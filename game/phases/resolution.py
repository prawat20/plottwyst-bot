from __future__ import annotations
"""
Resolution phase — final guess, winner reveal, and case solution.
"""
import asyncio
import logging
import discord

import config
from game.state import GameState

# Round ordinals for readable reveal messages
_ORDINAL = {1: "Round 1", 2: "Round 2", 3: "Round 3", 4: "Round 4"}
from game import session_manager
from game.phases.round import _progress_bar
from game.phases.reveal import CLUE_TYPE_EMOJI

logger = logging.getLogger(__name__)


async def run_final_guess(channel: discord.TextChannel, state: GameState) -> None:
    """Post the final guess UI and wait for all players or the timer."""
    from bot.views.guess_view import GuessView

    state.phase = "GUESS"
    await session_manager.save(state)

    duration        = config.GUESS_TIME
    remaining_count = len(state.remaining_suspects)

    def build_embed(elapsed=0, total=duration, remaining=duration):
        bar = _progress_bar(elapsed, total)
        guessed     = sum(1 for p in state.players.values() if p.has_guessed)
        total_p     = len(state.players)
        embed = discord.Embed(
            title="🎯  FINAL GUESS — Name the Murderer",
            description=(
                "The investigation is over. Now comes the moment of truth.\n\n"
                f"**{remaining_count} suspect{'s remain' if remaining_count != 1 else ' remains'}.** "
                f"Each detective gets **one guess** — make it count.\n\n"
                f"Your answer is private. The full reveal comes after everyone guesses "
                f"or the timer expires.\n\n"
                f"`{bar}` **{remaining}s remaining**"
            ),
            color=discord.Color.dark_purple(),
        )
        embed.add_field(
            name="Remaining Suspects",
            value="\n".join(f"🔹 {s}" for s in state.remaining_suspects),
            inline=False,
        )
        embed.set_footer(text=f"{guessed}/{total_p} detective{'s' if total_p != 1 else ''} guessed  ·  Answers are sealed until the reveal")
        return embed

    view = GuessView(state=state, timeout=float(duration))
    msg  = await channel.send(embed=build_embed(), view=view)

    # Live countdown
    elapsed = 0
    while elapsed < duration and not state.all_players_guessed:
        await asyncio.sleep(min(10, duration - elapsed))
        elapsed = min(elapsed + 10, duration)
        fresh = await session_manager.load(state.channel_id)
        if fresh:
            state.players = fresh.players
            state.winners = fresh.winners
        remaining = duration - elapsed
        try:
            await msg.edit(embed=build_embed(elapsed, duration, remaining), view=view)
        except discord.errors.NotFound:
            break

    # Final reload to capture any guesses made during the last polling interval
    fresh = await session_manager.load(state.channel_id)
    if fresh:
        state.players = fresh.players
        state.winners = fresh.winners

    view.stop()
    try:
        await msg.edit(embed=build_embed(duration, duration, 0), view=None)
    except discord.errors.NotFound:
        pass


async def run_resolution(
    channel: discord.TextChannel,
    state: GameState,
    murderer_eliminated: bool = False,
) -> str:
    """
    Announce winners and reveal the full solution.

    murderer_eliminated=True  →  the killer was voted out mid-game;
                                  skip the guess scorecard entirely and
                                  show a Plottwyst-framed defeat instead.

    Returns the outcome string for DB recording.
    """
    state.phase = "RESOLUTION"
    await session_manager.save(state)

    murderer_name = state.murderer
    winners       = [state.players[uid] for uid in state.winners if uid in state.players]

    silent_elimination = (
        config.SILENT_ELIMINATION
        and state.murderer_eliminated_round is not None
    )

    if murderer_eliminated:
        # ── Classic mode: early defeat, Plottwyst claimed the case ───────────
        # No scorecard — nobody ever got a chance to guess.
        defeat_embed = discord.Embed(
            title="🎭  THE PLOTTWYST CLAIMED ANOTHER CASE",
            description=(
                f"**{murderer_name}** was voted out in Round {state.round} — "
                f"the killer escaped before the investigation could run its course.\n\n"
                "No detective had the chance to name the killer. "
                "The misdirection held from the very first clue.\n\n"
                "*The full truth is about to be revealed.*"
            ),
            color=discord.Color.dark_red(),
        )
        await channel.send(embed=defeat_embed)
        outcome = "murderer_eliminated"

    elif silent_elimination:
        # ── Silent elimination mode: murderer was cleared during voting ───────
        # No scorecard — murderer wasn't in the final guess list.
        elim_round = _ORDINAL.get(state.murderer_eliminated_round, f"Round {state.murderer_eliminated_round}")
        defeat_embed = discord.Embed(
            title="🎭  THE KILLER WALKED FREE",
            description=(
                f"The investigation ran its full course — but the murderer was never on the final list.\n\n"
                f"Your team cleared **{murderer_name}** from suspicion in **{elim_round}**. "
                f"They walked free while the investigation focused elsewhere.\n\n"
                "*The full truth is about to be revealed.*"
            ),
            color=discord.Color.dark_red(),
        )
        await channel.send(embed=defeat_embed)
        outcome = "murderer_eliminated"

    else:
        # ── Dramatic sequential scorecard reveal ──────────────────────────────
        suspense_embed = discord.Embed(
            title="🔍  UNSEALING THE DETECTIVE REPORTS...",
            description="*The verdicts are being revealed one by one...*",
            color=discord.Color.dark_purple(),
        )
        scorecard_msg = await channel.send(embed=suspense_embed)
        await asyncio.sleep(2)

        scorecard_lines: list[str] = []
        for player in state.players.values():
            if player.has_guessed:
                icon  = "✅" if player.guessed_correctly else "❌"
                guess = player.final_guess or "—"
                scorecard_lines.append(f"{icon}  **{player.display_name}** — guessed *{guess}*")
            else:
                scorecard_lines.append(f"⏭️  **{player.display_name}** — did not guess in time")

            reveal_embed = discord.Embed(
                title="🔍  UNSEALING THE DETECTIVE REPORTS...",
                description="\n".join(scorecard_lines),
                color=discord.Color.dark_purple(),
            )
            reveal_embed.set_footer(text="The full solution is about to be revealed…")
            try:
                await scorecard_msg.edit(embed=reveal_embed)
            except discord.errors.NotFound:
                scorecard_msg = await channel.send(embed=reveal_embed)
            await asyncio.sleep(2)

        await asyncio.sleep(1)

        # ── Winner announcement ───────────────────────────────────────────────
        if winners:
            winner_lines = "\n".join(f"🏆  **{p.display_name}**" for p in winners)
            losers = [p for p in state.players.values() if p.user_id not in state.winners]
            loser_note = (
                f"\n\n*{', '.join(p.display_name for p in losers)} — so close. Better luck next case.*"
                if losers else ""
            )
            result_embed = discord.Embed(
                title="🎉  CASE CLOSED — You Saw Through the Plottwyst",
                description=(
                    f"The following detective{'s' if len(winners) != 1 else ''} cracked the case:\n\n"
                    f"{winner_lines}"
                    f"{loser_note}\n\n"
                    "Outstanding work. The murderer has been brought to justice."
                ),
                color=discord.Color.gold(),
            )
            outcome = "solved"
        else:
            result_embed = discord.Embed(
                title="🎭  THE PLOTTWYST WORKED",
                description=(
                    "The misdirection held. No detective correctly identified the killer.\n\n"
                    "The murderer walks free. The truth can no longer stay hidden — "
                    "it is about to be revealed."
                ),
                color=discord.Color.dark_grey(),
            )
            outcome = "unsolved"

        await channel.send(embed=result_embed)

    await asyncio.sleep(3)

    # ── Suspense beat before the truth ───────────────────────────────────────
    await channel.send(embed=discord.Embed(
        description="*The case file is being unsealed...*",
        color=discord.Color.dark_grey(),
    ))
    await asyncio.sleep(2)

    # ── Full solution reveal — split across two embeds to respect Discord limits ──
    #
    # Discord hard limits (enforced server-side, cause HTTP 400 if exceeded):
    #   • embed description : 4 096 chars
    #   • embed field value  : 1 024 chars
    #   • total embed chars  : 6 000 chars  (title + desc + footer + all field names/values)
    #
    # Strategy:
    #   Embed A — narrative only  (title + description, no fields)
    #   Embed B — structured data (motive / trait / location / red herring / evidence recap)
    # This gives the narrative up to ~3 900 chars and each detail field its own budget.

    murderer_profile = next(
        (s for s in state.case["suspects"] if s["name"] == murderer_name), None
    )
    if murderer_profile is None:
        logger.warning("Murderer '%s' not found in suspects list — case data may be corrupted", murderer_name)
        murderer_profile = {}

    def _cap(text: str, limit: int) -> str:
        """Hard-cap a string to `limit` chars, appending … if truncated."""
        return text if len(text) <= limit else text[: limit - 1] + "…"

    # ── Embed A: narrative ───────────────────────────────────────────────────
    # Budget:  title ≤ 256 + description ≤ 4 096 + footer ≤ 2 048  → total well under 6 000
    title_a  = "🔓  THE TRUTH REVEALED"
    prefix   = f"**The murderer was {murderer_name}.**\n\n"
    max_narr = 4096 - len(prefix) - 1   # reserve 1 char for safety
    narrative = _cap(state.case["solution"], max_narr)

    embed_a = discord.Embed(
        title=title_a,
        description=prefix + narrative,
        color=discord.Color.dark_red(),
    )
    embed_a.set_footer(text="Plottwyst  ·  Every case is a new story.")
    await channel.send(embed=embed_a)
    await asyncio.sleep(1)

    # ── Embed B: case details ────────────────────────────────────────────────
    # Each field value is individually capped; total stays well under 6 000.
    embed_b = discord.Embed(
        title="📁  Case Details",
        color=discord.Color.dark_grey(),
    )

    motive_text    = _cap(murderer_profile.get("motive",    "—"), 512)
    trait_text     = _cap(murderer_profile.get("trait",     "—"), 256)
    last_seen_text = _cap(murderer_profile.get("last_seen", "—"), 256)

    embed_b.add_field(name="Motive",    value=motive_text,    inline=True)
    embed_b.add_field(name="Trait",     value=trait_text,     inline=True)
    embed_b.add_field(name="Last Seen", value=last_seen_text, inline=True)

    plottwyst_text = state.case.get("plottwyst", "")
    red_herring    = state.case.get("red_herring", "")
    if plottwyst_text or red_herring:
        if plottwyst_text:
            rh_text = plottwyst_text
        else:
            # Fallback for cases generated before the plottwyst field was introduced
            rh_text = (
                f"**{red_herring}** was cast into suspicion by design — motive, opportunity, "
                f"and seemingly damning evidence all aligned against them. "
                f"The real killer was never where the evidence pointed."
            )
        embed_b.add_field(
            name="🎭  The Plottwyst",
            value=_cap(rh_text, 512),
            inline=False,
        )

    # Evidence recap: all revealed clues + any unrevealed clues still in the pool
    # (clue_pool is non-empty only when the murderer was eliminated early)
    clue_lines = []
    for i, clue in enumerate(state.revealed_clues, 1):
        emoji = CLUE_TYPE_EMOJI.get(clue["type"], "📌")
        clue_lines.append(f"{emoji} **{i}.** {_cap(clue['text'], 95)}")

    if state.clue_pool:
        # Calculate which round number each remaining pool clue belongs to
        rounds_already_revealed = max(0, len(state.revealed_clues) - 3)  # 3 opening clues
        clue_lines.append("*— Clues you never reached —*")
        for i, clue in enumerate(state.clue_pool):
            round_num  = rounds_already_revealed + i + 1
            total_idx  = len(state.revealed_clues) + i + 1
            emoji      = CLUE_TYPE_EMOJI.get(clue["type"], "📌")
            clue_lines.append(f"{emoji} **{total_idx}.** *{_cap(clue['text'], 95)}* *(Round {round_num})*")

    if clue_lines:
        revealed_count   = len(state.revealed_clues)
        unrevealed_count = len(state.clue_pool)
        field_name = (
            f"🔎  Evidence  ({revealed_count} revealed · {unrevealed_count} unrevealed)"
            if unrevealed_count else
            f"🔎  Evidence  ({revealed_count} clues)"
        )
        recap = _cap("\n".join(clue_lines), 1020)
        embed_b.add_field(name=field_name, value=recap, inline=False)

    embed_b.set_footer(text="Use /stats to see your record  ·  /leaderboard for server rankings")
    await channel.send(embed=embed_b)

    return outcome
