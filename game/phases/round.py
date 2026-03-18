from __future__ import annotations
"""
Round phase: (Ready gate R1 only) → Discussion → Voting → Vote resolution → Clue reveal.

Each round is a self-contained coroutine.
Returns the outcome string: 'murderer_eliminated' | 'innocent_eliminated' | 'no_majority'
"""
import asyncio
import discord

import config
from game.state import GameState
from game import session_manager
from game.phases.reveal import CLUE_TYPE_EMOJI, CLUE_TYPE_LABEL


# ── Ready gate view ───────────────────────────────────────────────────────────

class ReadyView(discord.ui.View):
    """Host-controlled gate before Round 1 discussion. Auto-starts after 2 minutes."""

    def __init__(self, host_id: int, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.host_id = host_id
        self.ready   = asyncio.Event()

    @discord.ui.button(label="Start Discussion", style=discord.ButtonStyle.green, emoji="▶️")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message(
                "Only the game host can start discussion early.", ephemeral=True
            )
            return
        await interaction.response.edit_message(content="▶️ Discussion starting!", view=None)
        self.ready.set()
        self.stop()

    async def on_timeout(self) -> None:
        self.ready.set()


# ── Quick reference links ─────────────────────────────────────────────────────

def _ref_links(state: GameState) -> str:
    """Build a one-line quick-reference string with Discord jump links."""
    parts = []
    if "scene"    in state.ref_urls:
        parts.append(f"[📍 Crime Scene]({state.ref_urls['scene']})")
    if "suspects" in state.ref_urls:
        parts.append(f"[🕵️ Suspects]({state.ref_urls['suspects']})")
    if "clues"    in state.ref_urls:
        parts.append(f"[🔎 Opening Clues]({state.ref_urls['clues']})")
    return "  ·  ".join(parts)


async def _add_return_navigation(
    channel: discord.TextChannel,
    state: GameState,
    round_num: int,
    back_url: str,
) -> None:
    """
    Edit the old reveal messages (Crime Scene, Suspects, Clues) to append a
    'Return to Round N' field so players can jump back after browsing them.
    Replaces any stale return link from a previous round.
    """
    label = f"⬆️ Return to Round {round_num}"
    value = f"[Jump back to current discussion/voting]({back_url})"

    for key in ("scene", "suspects", "clues"):
        url = state.ref_urls.get(key)
        if not url:
            continue
        try:
            msg_id = int(url.split("/")[-1])
            msg    = await channel.fetch_message(msg_id)
            if not msg.embeds:
                continue
            old = msg.embeds[0]
            new_embed = discord.Embed(
                title       = old.title,
                description = old.description,
                color       = old.color,
            )
            for f in old.fields:
                if f.name.startswith("⬆️"):
                    continue   # drop any stale return link
                new_embed.add_field(name=f.name, value=f.value, inline=f.inline)
            if old.footer and old.footer.text:
                new_embed.set_footer(text=old.footer.text)
            new_embed.add_field(name=label, value=value, inline=False)
            await msg.edit(embed=new_embed)
        except Exception:
            pass   # best-effort — never block the game


# ── Timer helpers ─────────────────────────────────────────────────────────────

def _progress_bar(elapsed: int, total: int, length: int = 20) -> str:
    filled = int((elapsed / total) * length)
    return "█" * filled + "░" * (length - filled)


# ── Discussion phase ──────────────────────────────────────────────────────────

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
    duration = config.DISCUSSION_TIME_R1 if round_num == 1 else config.DISCUSSION_TIME_R2
    prompt   = _DISCUSSION_PROMPTS[min(round_num - 1, len(_DISCUSSION_PROMPTS) - 1)]

    # ── Ready gate (Round 1 only) ─────────────────────────────────────────────
    if round_num == 1:
        ready_view = ReadyView(host_id=state.creator_id, timeout=120.0)
        ready_msg  = await channel.send(
            f"📋 **Take a moment to read the case file!**\n"
            f"<@{state.creator_id}> — click **Start Discussion** when your team is ready.\n"
            f"*(Auto-starts in 2 minutes if no one clicks)*",
            view=ready_view,
        )
        try:
            await asyncio.wait_for(ready_view.ready.wait(), timeout=125.0)
        except asyncio.TimeoutError:
            pass
        ready_view.stop()
        try:
            await ready_msg.delete()
        except Exception:
            pass

    # ── Discussion embed ──────────────────────────────────────────────────────
    from bot.views.voting_view import CaseFileButton

    class DiscussionView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.vote_early = asyncio.Event()
            self.add_item(CaseFileButton())

        @discord.ui.button(label="Vote Now", style=discord.ButtonStyle.danger, emoji="🗳️", row=1)
        async def vote_now(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != state.creator_id:
                await interaction.response.send_message(
                    "Only the game host can end discussion early.", ephemeral=True
                )
                return
            button.disabled = True
            await interaction.response.edit_message(view=self)
            self.vote_early.set()

    ref = _ref_links(state)

    def build_embed(elapsed, total, remaining):
        bar = _progress_bar(elapsed, total)
        desc_parts = []
        if ref:
            desc_parts.append(f"🔗 **Quick Reference:** {ref}\n")
        desc_parts.append(
            f"**{len(state.remaining_suspects)} suspect{'s' if len(state.remaining_suspects) != 1 else ''} remain{'s' if len(state.remaining_suspects) == 1 else ''}.**\n"
            f"Talk it out — share theories, challenge alibis, cross-reference clues.\n\n"
            f"💡 *{prompt}*\n\n"
            f"`{bar}` **{remaining}s remaining**"
        )
        embed = discord.Embed(
            title=f"💬  ROUND {round_num} of {config.MAX_ROUNDS} — DISCUSSION",
            description="\n".join(desc_parts),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="📋 Case File button below — full evidence summary, only visible to you.")
        return embed

    disc_view = DiscussionView()
    msg = await channel.send(embed=build_embed(0, duration, duration), view=disc_view)

    # Edit old reveal messages so players can jump back from there
    await _add_return_navigation(channel, state, round_num, back_url=msg.jump_url)

    # Live countdown — wakes immediately if host clicks Vote Now
    elapsed = 0
    while elapsed < duration and not disc_view.vote_early.is_set():
        tick = min(10, duration - elapsed)
        try:
            await asyncio.wait_for(disc_view.vote_early.wait(), timeout=tick)
        except asyncio.TimeoutError:
            pass
        elapsed   = min(elapsed + tick, duration)
        remaining = duration - elapsed
        if disc_view.vote_early.is_set():
            break
        try:
            await msg.edit(
                embed=build_embed(elapsed, duration, remaining),
                view=disc_view,
            )
        except discord.errors.NotFound:
            break

    # Close discussion
    try:
        await msg.edit(
            embed=discord.Embed(
                title=f"💬  ROUND {round_num} — DISCUSSION CLOSED",
                description=(
                    "Time to vote.\n\n"
                    "**Who are you confident is NOT the murderer?**\n"
                    "Click their name to clear them from suspicion."
                ),
                color=discord.Color.greyple(),
            ),
            view=None,
        )
    except Exception:
        pass


# ── Voting phase ──────────────────────────────────────────────────────────────

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

    ref = _ref_links(state)

    def build_embed(elapsed=0, total=duration, remaining=duration):
        bar = _progress_bar(elapsed, total)
        desc_parts = []
        if ref:
            desc_parts.append(f"🔗 **Quick Reference:** {ref}\n")
        warning = (
            "Eliminated suspects cannot be named in the final guess — choose carefully.\n"
            if config.SILENT_ELIMINATION else
            "⚠️ Clear the actual murderer and nobody wins this round.\n"
        )
        desc_parts.append(
            "**Click a suspect you're confident is NOT the murderer.**\n"
            "The most-voted suspect is cleared from suspicion.\n"
            f"{warning}\n"
            f"`{bar}` **{remaining}s remaining**"
        )
        embed = discord.Embed(
            title=f"🗳️  ROUND {round_num} of {config.MAX_ROUNDS} — VOTE",
            description="\n".join(desc_parts),
            color=discord.Color.orange(),
        )
        embed.add_field(name="Suspect Board", value=_suspect_board(), inline=False)

        tally = state.vote_tally()
        if tally:
            tally_lines = [
                f"**{name}** — {count} vote{'s' if count != 1 else ''}"
                for name, count in sorted(tally.items(), key=lambda x: -x[1])
            ]
            embed.add_field(name="Live Votes", value="\n".join(tally_lines), inline=False)

        voted   = len(state.confirmed_votes)
        total_p = len(state.players)
        embed.set_footer(text=f"{voted}/{total_p} detective{'s' if total_p != 1 else ''} voted  ·  📋 Case File button for full details")
        return embed

    view = VotingView(state=state, timeout=float(duration))
    msg  = await channel.send(embed=build_embed(), view=view)

    # Edit old reveal messages so players can jump back from there
    await _add_return_navigation(channel, state, round_num, back_url=msg.jump_url)

    # Update every 10 seconds while timer runs
    elapsed = 0
    while elapsed < duration and not view.all_voted:
        await asyncio.sleep(min(10, duration - elapsed))
        elapsed = min(elapsed + 10, duration)
        fresh = await session_manager.load(state.channel_id)
        if fresh:
            state.votes              = fresh.votes
            state.confirmed_votes    = fresh.confirmed_votes
            state.players            = fresh.players
            state.remaining_suspects = fresh.remaining_suspects
            view.all_voted           = view._check_all_voted(state)
        remaining = duration - elapsed
        try:
            await msg.edit(embed=build_embed(elapsed, duration, remaining), view=view)
        except discord.errors.NotFound:
            break

    view.stop()

    fresh = await session_manager.load(state.channel_id)
    if fresh:
        state.votes           = fresh.votes
        state.confirmed_votes = fresh.confirmed_votes

    try:
        await msg.edit(embed=build_embed(duration, duration, 0), view=None)
    except discord.errors.NotFound:
        pass

    # ── Resolve ───────────────────────────────────────────────────────────────
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
        if config.SILENT_ELIMINATION:
            # Silent path — treat exactly like an innocent elimination.
            # Don't reveal guilt; the resolution phase will expose this later.
            state.remaining_suspects.remove(eliminated)
            state.murderer_eliminated_round = round_num
            remaining = len(state.remaining_suspects)
            await session_manager.save(state)
            result_embed = discord.Embed(
                title="✅  SUSPECT CLEARED",
                description=(
                    f"**{eliminated}** has been cleared from active questioning.\n\n"
                    f"**{remaining} suspect{'s' if remaining != 1 else ''} remain.** "
                    f"{'The investigation continues.' if remaining > 1 else 'One suspect remains.'}"
                ),
                color=discord.Color.green(),
            )
            await channel.send(embed=result_embed)
            return "innocent_eliminated"
        else:
            # Current behaviour — reveal immediately and end the game.
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


# ── Clue reveal ───────────────────────────────────────────────────────────────

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
