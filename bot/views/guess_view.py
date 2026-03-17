from __future__ import annotations
"""Final guess UI — one button per remaining suspect, one guess per player."""
import discord
from game.state import GameState
from game import session_manager


class GuessView(discord.ui.View):
    def __init__(self, state: GameState, timeout: float):
        super().__init__(timeout=timeout)
        for i, suspect in enumerate(state.remaining_suspects):
            self.add_item(GuessButton(suspect, i))


class GuessButton(discord.ui.Button):
    def __init__(self, suspect_name: str, index: int):
        super().__init__(
            label=suspect_name[:80],  # Discord button label max 80 chars
            style=discord.ButtonStyle.danger,
            custom_id=f"guess_{index}",  # index-based to avoid 100-char custom_id limit
        )
        self.suspect_name = suspect_name

    async def callback(self, interaction: discord.Interaction):
        state = await session_manager.load(interaction.channel_id)
        if state is None or state.phase != "GUESS":
            await interaction.response.send_message("The guessing phase is not active.", ephemeral=True)
            return

        if interaction.user.id not in state.players:
            await interaction.response.send_message("You're not a player in this game.", ephemeral=True)
            return

        player = state.players[interaction.user.id]
        if player.has_guessed:
            await interaction.response.send_message("You've already made your guess.", ephemeral=True)
            return

        correct = self.suspect_name == state.murderer
        player.has_guessed       = True
        player.final_guess       = self.suspect_name
        player.guessed_correctly = correct

        if correct:
            state.winners.append(interaction.user.id)

        await session_manager.save(state)

        if correct:
            await interaction.response.send_message(
                f"🎉 **Correct!** You've identified the murderer — **{self.suspect_name}**!\n"
                f"Outstanding detective work. Wait for the full reveal.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ **Wrong guess.** {self.suspect_name} is not the murderer.\n"
                f"Wait for the full reveal to find out who did it.",
                ephemeral=True,
            )
