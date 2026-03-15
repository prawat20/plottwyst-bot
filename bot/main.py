from __future__ import annotations
"""
Plottwyst Discord bot — entry point.

Run with:  python -m bot.main
"""
import asyncio
import logging
import discord
from discord.ext import commands

import config
from db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("plottwyst")

COGS = [
    "bot.cogs.game_cog",
    "bot.cogs.admin_cog",
    "bot.cogs.premium_cog",
    "bot.cogs.info_cog",
    "bot.cogs.events_cog",
]

intents = discord.Intents.default()
intents.message_content = True   # needed for potential future prefix commands


class PlottwystBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",   # fallback prefix (slash commands are primary)
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        # Initialise database tables
        await init_db()
        logger.info("Database initialised.")

        # Load cogs
        for cog in COGS:
            await self.load_extension(cog)
            logger.info("Loaded cog: %s", cog)

        # Sync slash commands globally
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self) -> None:
        logger.info("Plottwyst is online as %s (ID: %s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="mysteries unfold | /lobby",
            )
        )

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        logger.error("Command error: %s", error)


def main() -> None:
    if not config.DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set. Check your .env file.")
    if config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        logger.warning("GEMINI_API_KEY is not set — case generation will fail.")

    bot = PlottwystBot()
    asyncio.run(bot.start(config.DISCORD_TOKEN))


if __name__ == "__main__":
    main()
