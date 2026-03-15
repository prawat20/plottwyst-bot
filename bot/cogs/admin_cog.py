from __future__ import annotations
"""
Admin cog — /stats and /leaderboard.
Both are free features (analytics=True for all tiers).
"""
import discord
from discord import app_commands
from discord.ext import commands

from db.session import AsyncSessionLocal
from db.repositories import user_repo, limit_hit_repo, guild_event_repo
import config


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="stats", description="View your Plottwyst stats for this server.")
    async def stats(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            user = await user_repo.get_stats(session, interaction.user.id, interaction.guild_id)

        if user is None or user.games_played == 0:
            await interaction.response.send_message(
                "You haven't played any games yet. Use `/lobby` to start one!", ephemeral=True
            )
            return

        win_rate = (user.games_won / user.games_played * 100) if user.games_played else 0
        accuracy = (user.correct_guesses / user.games_played * 100) if user.games_played else 0

        embed = discord.Embed(
            title=f"🕵️  {interaction.user.display_name}'s Detective Record",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Games Played",    value=str(user.games_played),    inline=True)
        embed.add_field(name="Games Won",        value=str(user.games_won),        inline=True)
        embed.add_field(name="Win Rate",         value=f"{win_rate:.1f}%",         inline=True)
        embed.add_field(name="Rounds Played",    value=str(user.rounds_played),    inline=True)
        embed.add_field(name="Correct Guesses",  value=str(user.correct_guesses),  inline=True)
        embed.add_field(name="Guess Accuracy",   value=f"{accuracy:.1f}%",         inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Top detectives in this server.")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            users = await user_repo.get_leaderboard(session, interaction.guild_id, limit=10)

        if not users:
            await interaction.response.send_message(
                "No games played yet. Use `/lobby` to start the first one!", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆  Plottwyst Leaderboard",
            description="Top detectives ranked by wins, then accuracy.",
            color=discord.Color.gold(),
        )
        for i, user in enumerate(users, 1):
            member = interaction.guild.get_member(user.user_id)
            name   = member.display_name if member else (user.display_name or "Unknown Player")
            accuracy = (user.correct_guesses / user.games_played * 100) if user.games_played else 0
            embed.add_field(
                name=f"#{i}  {name}",
                value=f"**{user.games_won}** wins  ·  {user.games_played} games  ·  {accuracy:.0f}% accuracy",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)


    @app_commands.command(
        name="leads",
        description="[Owner only] Servers and users hitting the free tier limit — upsell targets.",
    )
    async def leads(self, interaction: discord.Interaction) -> None:
        # Only accessible to dev/owner users
        if interaction.user.id not in config.PREMIUM_USER_IDS:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            top_servers = await limit_hit_repo.get_top_servers(session, limit=10)
            top_users   = await limit_hit_repo.get_top_users(session, limit=10)

        if not top_servers:
            await interaction.followup.send("No limit hits recorded yet.", ephemeral=True)
            return

        # ── Top servers embed ─────────────────────────────────────────────────
        servers_embed = discord.Embed(
            title="📈  Free Tier Limit Hits — Top Servers",
            description="Servers most frequently blocked by the daily game limit.",
            color=discord.Color.orange(),
        )
        for row in top_servers:
            last = row["last_hit"].strftime("%Y-%m-%d %H:%M") if row["last_hit"] else "—"
            servers_embed.add_field(
                name=f"Server `{row['guild_id']}`",
                value=(
                    f"**{row['hits']}** hits  ·  "
                    f"**{row['unique_users']}** unique users  ·  "
                    f"Last: {last}"
                ),
                inline=False,
            )

        # ── Top users embed ───────────────────────────────────────────────────
        users_embed = discord.Embed(
            title="👤  Free Tier Limit Hits — Top Users",
            description="Individual users blocked most often (prime upsell targets).",
            color=discord.Color.red(),
        )
        for row in top_users:
            last = row["last_hit"].strftime("%Y-%m-%d %H:%M") if row["last_hit"] else "—"
            member = None
            guild  = self.bot.get_guild(row["guild_id"])
            if guild:
                member = guild.get_member(row["user_id"])
            name = member.display_name if member else (f"Unknown User")
            users_embed.add_field(
                name=name,
                value=(
                    f"**{row['hits']}** hits  ·  "
                    f"Server `{row['guild_id']}`  ·  "
                    f"Last: {last}"
                ),
                inline=False,
            )

        await interaction.followup.send(embeds=[servers_embed, users_embed], ephemeral=True)


    @app_commands.command(
        name="installs",
        description="[Owner only] Bot install and removal history.",
    )
    async def installs(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in config.PREMIUM_USER_IDS:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            events        = await guild_event_repo.get_recent(session, limit=20)
            total_joined, total_left = await guild_event_repo.get_totals(session)

        active = total_joined - total_left

        embed = discord.Embed(
            title="📊  Bot Installs",
            description=(
                f"**{total_joined}** total installs  ·  "
                f"**{total_left}** removals  ·  "
                f"**{active}** currently active servers"
            ),
            color=discord.Color.green(),
        )

        if events:
            lines = []
            for e in events:
                icon = "✅" if e.event_type == "joined" else "❌"
                ts   = e.created_at.strftime("%Y-%m-%d %H:%M") if e.created_at else "—"
                name = e.guild_name or f"id:{e.guild_id}"
                lines.append(f"{icon} **{name}** · {e.member_count or '?'} members · {ts}")
            embed.add_field(
                name="Recent Events",
                value="\n".join(lines[:20]),
                inline=False,
            )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
