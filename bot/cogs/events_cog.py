from __future__ import annotations
"""
Events cog — tracks bot guild joins and removals.

on_guild_join  → records install, creates a server row for tier tracking
on_guild_remove → records removal for churn analytics
"""
import logging
import discord
from discord.ext import commands

from db.session import AsyncSessionLocal
from db.repositories import guild_event_repo, server_repo

logger = logging.getLogger(__name__)


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        logger.info(
            "Bot added to guild: %s (id=%s, members=%s)",
            guild.name, guild.id, guild.member_count,
        )
        async with AsyncSessionLocal() as session:
            await guild_event_repo.record(session, guild, "joined")
            # Ensure a server row exists so tier checks work immediately
            await server_repo.get_or_create(session, guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        logger.info(
            "Bot removed from guild: %s (id=%s)",
            guild.name, guild.id,
        )
        async with AsyncSessionLocal() as session:
            await guild_event_repo.record(session, guild, "left")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventsCog(bot))
