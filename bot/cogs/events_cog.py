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

        # Send a welcome message to the system channel (or first writable text channel)
        channel = guild.system_channel
        if channel is None:
            channel = next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                None,
            )
        if channel is None:
            return

        embed = discord.Embed(
            title="🔍  Plottwyst has arrived!",
            description=(
                "A murder has been committed — and your server is now equipped to solve it.\n\n"
                "Type `/lobby` in any channel to start your first murder mystery.\n"
                "Players join, the AI generates a unique case, and the investigation begins."
            ),
            color=discord.Color.dark_blue(),
        )
        embed.add_field(
            name="Getting Started",
            value=(
                "`/lobby` — Create a game lobby\n"
                "`/howtoplay` — Step-by-step new player guide\n"
                "`/commands` — See all available commands"
            ),
            inline=False,
        )
        embed.add_field(
            name="No server? No problem.",
            value="Join our [Community Server](https://discord.gg/z7BsnXzHz) to play instantly with other detectives.",
            inline=False,
        )
        embed.set_footer(text="plottwyst.app  ·  Every case is a new story.")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning("Could not send welcome message to guild %s — missing permissions", guild.id)

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
