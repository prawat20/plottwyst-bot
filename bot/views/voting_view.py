from __future__ import annotations
"""Voting UI — one button per remaining suspect, confirmation step, and Case File reference."""
import discord
from game.state import GameState
from game import session_manager
from game.phases.reveal import CLUE_TYPE_EMOJI


class VotingView(discord.ui.View):
    def __init__(self, state: GameState, timeout: float):
        super().__init__(timeout=timeout)
        self.state     = state
        self.all_voted = False

        # Suspect vote buttons (row 0 / 1 depending on count)
        for i, suspect in enumerate(state.remaining_suspects):
            self.add_item(SuspectVoteButton(suspect, i))

        # Case File reference button always on the last row
        self.add_item(CaseFileButton())

    def _check_all_voted(self, state: GameState) -> bool:
        return len(state.confirmed_votes) >= len(state.players)


# ── Vote buttons ──────────────────────────────────────────────────────────────

class SuspectVoteButton(discord.ui.Button):
    def __init__(self, suspect_name: str, index: int):
        super().__init__(
            label=suspect_name[:80],  # Discord button label max 80 chars
            style=discord.ButtonStyle.primary,
            custom_id=f"vote_{index}",  # index-based to avoid 100-char custom_id limit
        )
        self.suspect_name = suspect_name

    async def callback(self, interaction: discord.Interaction):
        state = await session_manager.load(interaction.channel_id)
        if state is None or state.phase != "VOTING":
            await interaction.response.send_message("Voting is not active.", ephemeral=True)
            return

        if interaction.user.id not in state.players:
            await interaction.response.send_message("You're not a player in this game.", ephemeral=True)
            return

        if interaction.user.id in state.confirmed_votes:
            await interaction.response.send_message("You've already cast your vote.", ephemeral=True)
            return

        # Don't save pending vote yet — only persist on confirmation to avoid race conditions
        view = ConfirmVoteView(state=state, suspect_name=self.suspect_name)
        await interaction.response.send_message(
            f"You're clearing **{self.suspect_name}** as innocent — removing them from suspicion.\n"
            f"⚠️ If they turn out to be the murderer, nobody wins this round.\n\n"
            f"Are you sure?",
            view=view,
            ephemeral=True,
        )


class ConfirmVoteView(discord.ui.View):
    def __init__(self, state: GameState, suspect_name: str):
        super().__init__(timeout=20)
        self.state        = state
        self.suspect_name = suspect_name

    @discord.ui.button(label="Yes, clear them", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = await session_manager.load(self.state.channel_id)
        if state is None or state.phase != "VOTING":
            await interaction.response.edit_message(content="Voting has ended.", view=None)
            return

        if interaction.user.id in state.confirmed_votes:
            await interaction.response.edit_message(content="You've already voted.", view=None)
            return

        state.votes[interaction.user.id] = self.suspect_name
        state.confirmed_votes.append(interaction.user.id)
        if interaction.user.id in state.players:
            state.players[interaction.user.id].votes_cast += 1
        await session_manager.save(state)

        await interaction.response.edit_message(
            content=f"✅ Vote locked in — you've cleared **{self.suspect_name}**.", view=None
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = await session_manager.load(self.state.channel_id)
        # Only remove pending vote if not already confirmed — never undo a confirmed vote
        if state and interaction.user.id in state.votes and interaction.user.id not in state.confirmed_votes:
            del state.votes[interaction.user.id]
            await session_manager.save(state)
        await interaction.response.edit_message(content="Vote cancelled.", view=None)


# ── Case File button ──────────────────────────────────────────────────────────

class CaseFileButton(discord.ui.Button):
    """
    Sends the player an ephemeral case digest — victim, all suspects with current
    status and motive, and every clue revealed so far. No scrolling needed.
    """
    def __init__(self):
        super().__init__(
            label="Case File",
            style=discord.ButtonStyle.secondary,
            emoji="📋",
            row=4,   # always on the bottom row, away from vote buttons
        )

    async def callback(self, interaction: discord.Interaction):
        state = await session_manager.load(interaction.channel_id)
        if state is None:
            await interaction.response.send_message(
                "Game state not found — it may have ended.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📂  Your Case File",
            description="Everything you know so far. Only you can see this.",
            color=discord.Color.dark_blue(),
        )

        # Victim
        victim = state.case.get("victim", {})
        embed.add_field(
            name="💀  Victim",
            value=f"**{victim.get('name', '—')}** — {victim.get('background', '—')}",
            inline=False,
        )

        # Suspects: status + truncated motive
        suspect_lines = []
        for s in state.case.get("suspects", []):
            status  = "🔴" if s["name"] in state.remaining_suspects else "✅ ~~"
            suffix  = "~~" if s["name"] not in state.remaining_suspects else ""
            motive  = s["motive"][:70] + ("…" if len(s["motive"]) > 70 else "")
            suspect_lines.append(f"{status}**{s['name']}**{suffix} — {motive}")

        if suspect_lines:
            embed.add_field(
                name=f"🕵️  Suspects  ({len(state.remaining_suspects)} active)",
                value="\n".join(suspect_lines),
                inline=False,
            )

        # All revealed clues
        if state.revealed_clues:
            clue_lines = []
            for i, clue in enumerate(state.revealed_clues, 1):
                emoji = CLUE_TYPE_EMOJI.get(clue["type"], "📌")
                text  = clue["text"][:90] + ("…" if len(clue["text"]) > 90 else "")
                clue_lines.append(f"{emoji} **{i}.** {text}")
            # Cap total to stay under 1024
            recap = "\n".join(clue_lines)
            if len(recap) > 1020:
                recap = recap[:1020] + "…"
            embed.add_field(
                name=f"🔎  Evidence  ({len(state.revealed_clues)} clues revealed)",
                value=recap,
                inline=False,
            )
        else:
            embed.add_field(name="🔎  Evidence", value="*No clues revealed yet.*", inline=False)

        embed.set_footer(text="📋 Case File  ·  Refreshes each time you click  ·  Only visible to you")
        await interaction.response.send_message(embed=embed, ephemeral=True)
