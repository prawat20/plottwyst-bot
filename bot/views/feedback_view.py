from __future__ import annotations
"""
Post-game feedback — two-step ephemeral flow, private to each player.

Step 1: Did the Plottwyst fool you?  (3 options)
Step 2: How was this case overall?   (4 options)
Result: "Thanks!" confirmation, both answers saved to game_feedback table.
"""
import discord
from db.session import AsyncSessionLocal
from db.repositories import feedback_repo


class FeedbackStartView(discord.ui.View):
    """Step 1 — Did the Plottwyst fool you?"""

    def __init__(self, game_id: str, guild_id: int):
        super().__init__(timeout=120)
        self.game_id  = game_id
        self.guild_id = guild_id

    @discord.ui.button(label="Yes, totally!", style=discord.ButtonStyle.primary, emoji="🎭")
    async def fooled_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._to_rating(interaction, "yes")

    @discord.ui.button(label="Almost got me", style=discord.ButtonStyle.secondary, emoji="😅")
    async def fooled_almost(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._to_rating(interaction, "almost")

    @discord.ui.button(label="Saw it coming", style=discord.ButtonStyle.secondary, emoji="🔍")
    async def fooled_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._to_rating(interaction, "no")

    async def _to_rating(self, interaction: discord.Interaction, plottwyst_answer: str):
        view = CaseRatingView(
            game_id=self.game_id,
            guild_id=self.guild_id,
            plottwyst_fooled=plottwyst_answer,
        )
        await interaction.response.edit_message(
            content="**How was this case overall?**",
            view=view,
        )


class CaseRatingView(discord.ui.View):
    """Step 2 — How was the case?"""

    def __init__(self, game_id: str, guild_id: int, plottwyst_fooled: str):
        super().__init__(timeout=120)
        self.game_id         = game_id
        self.guild_id        = guild_id
        self.plottwyst_fooled = plottwyst_fooled

    @discord.ui.button(label="Loved it", style=discord.ButtonStyle.success, emoji="🔥")
    async def rating_loved(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._save(interaction, "loved")

    @discord.ui.button(label="Good", style=discord.ButtonStyle.primary, emoji="👍")
    async def rating_good(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._save(interaction, "good")

    @discord.ui.button(label="Okay", style=discord.ButtonStyle.secondary, emoji="😐")
    async def rating_okay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._save(interaction, "okay")

    @discord.ui.button(label="Confused", style=discord.ButtonStyle.danger, emoji="😕")
    async def rating_confused(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._save(interaction, "confused")

    async def _save(self, interaction: discord.Interaction, rating: str):
        async with AsyncSessionLocal() as session:
            await feedback_repo.save_feedback(
                session,
                game_id=self.game_id,
                user_id=interaction.user.id,
                guild_id=self.guild_id,
                plottwyst_fooled=self.plottwyst_fooled,
                case_rating=rating,
            )
        await interaction.response.edit_message(
            content="✅  Thanks! Your feedback helps us improve Plottwyst. 🎭",
            view=None,
        )
