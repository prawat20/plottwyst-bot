from __future__ import annotations
"""
Post-game view — Play Again and Leaderboard buttons shown at the end of every game.

The view is posted by game_cog._run_game() after cleanup (session deleted).
It accepts _run_game as a callable so the game loop can be re-entered without
duplicating any logic.
"""
import asyncio
import discord

from game.state import GameState
from game import session_manager
from game.phases.lobby import add_player
from bot.views.lobby_view import LobbyView, build_lobby_embed
from db.session import AsyncSessionLocal
from db.repositories import user_repo
from tiers.manager import TierManager
from tiers.entitlements import Feature


class PostGameView(discord.ui.View):
    def __init__(self, guild_id: int, channel_id: int, game_id: str, run_game_fn):
        super().__init__(timeout=300)   # buttons live for 5 minutes
        self.guild_id     = guild_id
        self.channel_id   = channel_id
        self.game_id      = game_id
        self._run_game_fn = run_game_fn

    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    # ── Play Again ────────────────────────────────────────────────────────────

    @discord.ui.button(label="Play Again", style=discord.ButtonStyle.success, emoji="🎮")
    async def play_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This only works inside a server channel.", ephemeral=True
            )
            return

        # Guard: don't allow two games in the same channel
        if await session_manager.exists(self.channel_id):
            await interaction.response.send_message(
                "A game is already running in this channel. Wait for it to finish first.",
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            creator_id  = interaction.user.id
            can, reason = await TierManager.can_start_game(
                session, self.guild_id, creator_id=creator_id, channel_id=self.channel_id
            )
            if not can:
                await interaction.response.send_message(reason, ephemeral=True)
                return

            max_players = await TierManager.get(
                session, self.guild_id, Feature.MAX_PLAYERS, creator_id=creator_id
            )
            is_premium  = await TierManager.is_premium(
                session, self.guild_id, creator_id=creator_id
            )

        # Build new game state and open lobby
        state = GameState.new(
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            creator_id=interaction.user.id,
        )
        await add_player(state, interaction.user.id, interaction.user.display_name)

        lobby_view = LobbyView(state=state, max_players=max_players, is_premium=is_premium)
        await interaction.response.send_message(
            embed=build_lobby_embed(state, max_players, "random"), view=lobby_view
        )
        lobby_view.lobby_msg = await interaction.original_response()

        # Disable this post-game view so it can't be double-clicked
        self._disable_all()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        # Wait for the host to click Start (or the lobby to time out)
        await lobby_view.wait()

        if not lobby_view.started:
            await session_manager.delete(self.channel_id)
            try:
                await lobby_view.lobby_msg.edit(
                    embed=discord.Embed(
                        title="⏰  Lobby Expired",
                        description="The lobby timed out. Use `/lobby` to start a new game.",
                        color=discord.Color.red(),
                    ),
                    view=None,
                )
            except Exception:
                pass
            return

        # Hand off to the game loop (detached so Discord doesn't time out)
        asyncio.create_task(
            self._run_game_fn(interaction.channel, lobby_view.state, lobby_view.selected_genre_key)
        )

    # ── Rate this case ────────────────────────────────────────────────────────

    @discord.ui.button(label="Rate this case", style=discord.ButtonStyle.secondary, emoji="📝", row=1)
    async def rate_case(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.feedback_view import FeedbackStartView
        view = FeedbackStartView(game_id=self.game_id, guild_id=self.guild_id)
        await interaction.response.send_message(
            "**Did the Plottwyst fool you this time?**",
            view=view,
            ephemeral=True,
        )

    # ── Leaderboard ───────────────────────────────────────────────────────────

    @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This only works inside a server channel.", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            users = await user_repo.get_leaderboard(session, interaction.guild_id, limit=10)

        if not users:
            await interaction.response.send_message(
                "No games have been completed in this server yet.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆  Plottwyst Leaderboard",
            description="Top detectives ranked by wins, then accuracy.",
            color=discord.Color.gold(),
        )
        for i, user in enumerate(users, 1):
            member   = interaction.guild.get_member(user.user_id)
            name     = member.display_name if member else (user.display_name or "Unknown Detective")
            accuracy = (user.correct_guesses / user.games_played * 100) if user.games_played else 0
            embed.add_field(
                name=f"#{i}  {name}",
                value=f"**{user.games_won}** wins  ·  {user.games_played} games  ·  {accuracy:.0f}% accuracy",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)
