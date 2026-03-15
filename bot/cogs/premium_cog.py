from __future__ import annotations
"""
Premium cog — Phase 4 placeholder.

/premium info  → shows what premium includes
/premium activate <key>  → activate premium (key system to be built in Phase 4)
"""
import discord
from discord import app_commands
from discord.ext import commands
from tiers.entitlements import TIERS, Feature
from db.session import AsyncSessionLocal
from db.repositories import limit_hit_repo


class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    premium_group = app_commands.Group(name="premium", description="Premium tier management.")

    @premium_group.command(name="info", description="See what Plottwyst Premium includes.")
    async def info(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id:
            async with AsyncSessionLocal() as session:
                await limit_hit_repo.record(
                    session    = session,
                    guild_id   = interaction.guild_id,
                    user_id    = interaction.user.id,
                    channel_id = interaction.channel_id,
                    limit_type = "premium_info_view",
                )
        free    = TIERS["free"]
        premium = TIERS["premium"]

        embed = discord.Embed(
            title="⭐  Plottwyst Premium",
            description=(
                "Upgrade your server for the full detective experience — "
                "more players, unlimited games, and exclusive modes coming soon."
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(
            name="🆓  Free",
            value=(
                f"✅ Up to **{free[Feature.MAX_PLAYERS]} players** per game\n"
                f"✅ **{free[Feature.DAILY_GAME_LIMIT]} games/day** per server\n"
                f"✅ **{free[Feature.USER_DAILY_GAME_LIMIT]} games/day** per player\n"
                f"✅ Leaderboard & personal stats\n"
                f"✅ AI-generated mysteries\n"
                f"❌ Private DM clues\n"
                f"❌ Murderer Among Players mode\n"
                f"❌ Custom game settings"
            ),
            inline=True,
        )
        embed.add_field(
            name="⭐  Premium",
            value=(
                f"✅ Up to **{premium[Feature.MAX_PLAYERS]} players** per game\n"
                f"✅ **Unlimited** games per server\n"
                f"✅ **Unlimited** games per player\n"
                f"✅ Leaderboard & personal stats\n"
                f"✅ AI-generated mysteries\n"
                f"✅ Private DM clues *(coming soon)*\n"
                f"✅ Murderer Among Players *(coming soon)*\n"
                f"✅ Custom game settings *(coming soon)*"
            ),
            inline=True,
        )
        embed.set_footer(text="Premium activation coming soon — stay tuned!")
        await interaction.response.send_message(embed=embed)

    @premium_group.command(name="activate", description="Activate a premium key for this server.")
    async def activate(self, interaction: discord.Interaction, key: str) -> None:
        if interaction.guild_id:
            async with AsyncSessionLocal() as session:
                await limit_hit_repo.record(
                    session    = session,
                    guild_id   = interaction.guild_id,
                    user_id    = interaction.user.id,
                    channel_id = interaction.channel_id,
                    limit_type = "premium_activate_attempt",
                )
        # Phase 4: validate key against payment provider, set server tier
        await interaction.response.send_message(
            "Premium activation is coming soon! Join our community for early access.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PremiumCog(bot))
