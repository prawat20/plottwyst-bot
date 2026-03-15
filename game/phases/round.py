from __future__ import annotations
"""
Round phase: Discussion → Voting → Vote resolution → Clue reveal.

Each round is a self-contained coroutine.
Returns the outcome string: 'murderer_eliminated' | 'innocent_eliminated' | 'no_majority'
"""
import asyncio
import discord

import config
from game.state import GameState
from game import session_manager
from game.phases.reveal import CLUE_TYPE_EMOJI, CLUE_TYPE_LABEL


# ── Quick reference links ────────────────────────────────────────────────────

def _ref_links(state: GameState) -> str:
    """
    Build a one-line quick-reference string with Discord jump links to the key
    case messages posted during the reveal phase.  Returns an empty string if
    no refs are stored yet (shouldn't happen in normal play).
    """
    parts = []
    if "scene"    in state.ref_urls:
        parts.append(f"[📍 Crime Scene]({state.ref_urls['scene']})")
    if "suspects" in state.ref_urls:
        parts.append(f"[🕵️ Suspects]({state.ref_urls['suspects']})")
    if "clues"    in state.ref_urls:
        parts.append(f"[🔎 Opening Clues]({state.ref_urls['clues']})")
    return "  ·  ".join(parts)


# ── Timer helpers ────────────────────────────────────────────────────────────

def _progress_bar(elapsed: int, total: int, length: int = 20) -> str:
    filled = int((elapsed / total) * length)
    return "█" * filled + "░" * (length - filled)


async def _countdown(
    message: discord.Message,
    embed_builder,
    total: int,
    interval: int = 10,
) -> None:
    """Edit a Discord message every `interval` seconds with a live countdown."""
    elapsed = 0
    while elapsed < total:
        await asyncio.sleep(min(interval, total - elapsed))
        elapsed = min(elapsed + interval, total)
        remaining = total - elapsed
        await message.edit(embed=embed_builder(elapsed, total, remaining))


# ── Discussion phase ─────────────────────────────────────────────────────────

_DISCUSSION_PROMPTS = [
    "Where was each suspect when the crime occurred? Check their statements against the clues.",
    "Does the new evidence contradict anyone's alibi? Look for inconsistencies.",
    "Focus on motive — who had the most to gain from the victim's death?",
    "Trust the evidence. The clues have been pointing somewhere all along.",
]


async def run_discussion(
    channel: discord.TextChannel,
    state: GameState,
    round_num: int,
) -> None:
    duration = config.DISCUSSION_TIME
    prompt   = _DISCUSSION_PROMPTS[min(round_num - 1, len(_DISCUSSION_PROMPTS) - 1)]

    ref = _ref_links(state)

    def build_embed(elapsed, total, remaining):
        bar = _progress_bar(elapsed, total)
        embed = discord.Embed(
            title=f"💬  ROUND {round_num} of {config.MAX_ROUNDS} — DISCUSSION",
            description=(
                f"**{len(state.remaining_suspects)} suspect{'s' if len(state.remaining_suspects) != 1 else ''} remain.**\n"
                f"Talk it out — share theories, challenge alibis, cross-reference clues.\n\n"
                f"💡 *{prompt}*\n\n"
                f"`{bar}` **{remaining}s remaining**"
            ),
            color=discord.Color.blue(),
        )
        if ref:
            embed.add_field(name="Quick Reference", value=ref, inline=False)
        embed.set_footer(text="Voting opens automatically when the timer ends.")
        return embed

    msg = await channel.send(embed=build_embed(0, duration, duration))
    await _countdown(msg, build_embed, duration)
    await msg.edit(embed=discord.Embed(
        title=f"💬  ROUND {round_num} — DISCUSSION CLOSED",
        description=(
            "Time to vote.\n\n"
            "**Who are you confident is NOT the murderer?**\n"
            "Click their name to clear them from suspicion."
        ),
        color=discord.Color.greyple(),
    ))


# ── Voting phase ─────────────────────────────────────────────────────────────

async def run_voting(
    channel: discord.TextChannel,
    state: GameState,
    round_num: int,
) -> str:
    """
    Posts voting buttons, waits for the timer, resolves votes.
    Returns: 'murderer_eliminated' | 'innocent_eliminated' | 'no_majority'
    """
    from bot.views.voting_view import VotingView

    state.votes           = {}
    state.confirmed_votes = []
    state.phase           = "VOTING"
    await session_manager.save(state)

    duration = config.VOTING_TIME

    ref = _ref_links(state)

    # Build the static suspect board for this round (cleared suspects already removed)
    all_suspects = [s["name"] for s in state.case["suspects"]] if state.case else state.remaining_suspects

    def _suspect_board() -> str:
        lines = []
        for name in all_suspects:
            if name in state.remaining_suspects:
                lines.append(f"🔴  {name}")
            else:
                lines.append(f"✅  {name}  — cleared")
        return "\n".join(lines)

    def build_embed(elapsed=0, total=duration, remaining=duration):
        bar = _progress_bar(elapsed, total)
        embed = discord.Embed(
            title=f"🗳️  ROUND {round_num} of {config.MAX_ROUNDS} — VOTE",
            description=(
                "**Click a suspect you're confident is NOT the murderer.**\n"
                "The most-voted suspect is cleared from suspicion.\n"
                "⚠️ Clear the actual murderer and nobody wins this round.\n\n"
                f"`{bar}` **{remaining}s remaining**"
            ),
            color=discord.Color.orange(),
        )
        # Suspect status board
        embed.add_field(name="Suspect Board", value=_suspect_board(), inline=False)

        # Live vote tally
        tally = state.vote_tally()
        if tally:
            tally_lines = [
                f"**{name}** — {count} vote{'s' if count != 1 else ''}"
                for name, count in sorted(tally.items(), key=lambda x: -x[1])
            ]
            embed.add_field(name="Live Votes", value="\n".join(tally_lines), inline=False)

        if ref:
            embed.add_field(name="Quick Reference", value=ref, inline=False)

        voted   = len(state.confirmed_votes)
        total_p = len(state.players)
        embed.set_footer(text=f"{voted}/{total_p} detective{'s' if total_p != 1 else ''} voted  ·  📋 Case File button for full details")
        return embed

    view = VotingView(state=state, timeout=float(duration))
    msg  = await channel.send(embed=build_embed(), view=view)

    # Update every 10 seconds while timer runs
    elapsed = 0
    while elapsed < duration and not view.all_voted:
        await asyncio.sleep(min(10, duration - elapsed))
        elapsed = min(elapsed + 10, duration)
        # Reload state to capture button clicks
        fresh = await session_manager.load(state.channel_id)
        if fresh:
            state.votes           = fresh.votes
            state.confirmed_votes = fresh.confirmed_votes
            view.all_voted        = view._check_all_voted(state)
        remaining = duration - elapsed
        try:
            await msg.edit(embed=build_embed(elapsed, duration, remaining), view=view)
        except discord.errors.NotFound:
            break

    view.stop()

    # Reload final state
    fresh = await session_manager.load(state.channel_id)
    if fresh:
        state.votes           = fresh.votes
        state.confirmed_votes = fresh.confirmed_votes

    # Disable buttons
    try:
        await msg.edit(embed=build_embed(duration, duration, 0), view=None)
    except discord.errors.NotFound:
        pass

    # ── Resolve ──────────────────────────────────────────────────────────────
    eliminated = state.majority_vote()
    if eliminated is None:
        tally = state.vote_tally()
        if tally:
            tally_text = "\n".join(
                f"**{name}** — {count} vote{'s' if count != 1 else ''}"
                for name, count in sorted(tally.items(), key=lambda x: -x[1])
            )
        else:
            tally_text = "*No votes cast.*"
        result_embed = discord.Embed(
            title="🟡  NO MAJORITY — No One Eliminated",
            description=(
                "The detectives couldn't reach a consensus this round.\n"
                "No suspect has been cleared. Study the next clue carefully.\n\n"
                f"**Final vote count:**\n{tally_text}"
            ),
            color=discord.Color.yellow(),
        )
        await channel.send(embed=result_embed)
        return "no_majority"

    if eliminated == state.murderer:
        result_embed = discord.Embed(
            title="💀  THE MURDERER WAS CLEARED — Round Forfeit",
            description=(
                f"The detectives cleared **{eliminated}**... who was the murderer all along.\n\n"
                "The killer slips through your fingers. Nobody wins this round.\n"
                "The investigation continues — don't make the same mistake again."
            ),
            color=discord.Color.dark_red(),
        )
        await channel.send(embed=result_embed)
        state.remaining_suspects.remove(eliminated)
        await session_manager.save(state)
        return "murderer_eliminated"

    # Innocent eliminated
    state.remaining_suspects.remove(eliminated)
    remaining = len(state.remaining_suspects)
    await session_manager.save(state)
    result_embed = discord.Embed(
        title="✅  SUSPECT CLEARED",
        description=(
            f"**{eliminated}** has been eliminated from suspicion — they were innocent.\n\n"
            f"**{remaining} suspect{'s' if remaining != 1 else ''} remain.** "
            f"{'One of them is the murderer.' if remaining > 1 else 'The murderer is the last one standing.'}"
        ),
        color=discord.Color.green(),
    )
    await channel.send(embed=result_embed)
    return "innocent_eliminated"


# ── Clue reveal ──────────────────────────────────────────────────────────────

async def reveal_next_clue(channel: discord.TextChannel, state: GameState) -> None:
    if not state.clue_pool:
        return

    clue = state.clue_pool.pop(0)
    state.revealed_clues.append(clue)
    await session_manager.save(state)

    emoji      = CLUE_TYPE_EMOJI.get(clue["type"], "📌")
    type_label = CLUE_TYPE_LABEL.get(clue["type"], clue["type"].upper())
    total_seen = len(state.revealed_clues)
    embed = discord.Embed(
        title=f"{emoji}  NEW EVIDENCE  —  {type_label}",
        description=clue["text"],
        color=discord.Color.teal(),
    )
    embed.set_footer(text=f"Clue {total_seen} of {total_seen + len(state.clue_pool)} total  ·  Discuss before the next round begins")
    await channel.send(embed=embed)
