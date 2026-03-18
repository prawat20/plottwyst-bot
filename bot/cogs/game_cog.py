from __future__ import annotations
"""
Game cog — handles /lobby and orchestrates the full game loop.
"""
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands

from game.state import GameState
from game import session_manager
from game.phases import lobby as lobby_phase
from game.phases import reveal as reveal_phase
from game.phases import round as round_phase
from game.phases import resolution as res_phase
from engine.generator import generate_case
from tiers.manager import TierManager
from tiers.entitlements import Feature
from db.session import AsyncSessionLocal
from db.repositories import server_repo, user_repo, game_repo
from bot.views.lobby_view import LobbyView, build_lobby_embed

import config

logger = logging.getLogger(__name__)


class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /lobby ───────────────────────────────────────────────────────────────

    @app_commands.command(name="lobby", description="Create a new Plottwyst murder mystery lobby.")
    async def lobby(self, interaction: discord.Interaction) -> None:
        channel_id = interaction.channel_id
        guild_id   = interaction.guild_id

        # Only allow in guild channels
        if guild_id is None:
            await interaction.response.send_message("Plottwyst must be played in a server channel.", ephemeral=True)
            return

        # Block if a game is already running in this channel
        if await session_manager.exists(channel_id):
            await interaction.response.send_message(
                "A game is already running in this channel. "
                "Wait for it to finish, then use `/lobby` to start a new one.",
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            # Tier checks (creator_id allows dev users to bypass limits)
            creator_id = interaction.user.id
            can, reason = await TierManager.can_start_game(
                session, guild_id, creator_id=creator_id, channel_id=channel_id
            )
            if not can:
                await interaction.response.send_message(reason, ephemeral=True)
                return

            max_players = await TierManager.get(session, guild_id, Feature.MAX_PLAYERS, creator_id=creator_id)
            is_premium  = await TierManager.is_premium(session, guild_id, creator_id=creator_id)

            # Create state and persist
            state = GameState.new(guild_id=guild_id, channel_id=channel_id, creator_id=interaction.user.id)
            await lobby_phase.add_player(state, interaction.user.id, interaction.user.display_name)

            view = LobbyView(state=state, max_players=max_players, is_premium=is_premium)
            await interaction.response.send_message(
                embed=build_lobby_embed(state, max_players, "random"), view=view
            )
            view.lobby_msg = await interaction.original_response()

            # Wait for host to click Start (view.stop() called inside the button)
            await view.wait()

            # If timed out without start
            if not view.started:
                await session_manager.delete(channel_id)
                try:
                    await view.lobby_msg.edit(
                        embed=discord.Embed(
                            title="⏰  Lobby Expired",
                            description="The lobby timed out. Use `/lobby` to create a new game.",
                            color=discord.Color.red(),
                        ),
                        view=None,
                    )
                except Exception:
                    pass
                return

        # ── Game loop ─────────────────────────────────────────────────────────
        # Detach from the interaction handler so Discord never times out.
        # _run_game drives itself via channel.send() — no interaction token needed.
        asyncio.create_task(self._run_game(interaction.channel, view.state, view.selected_genre_key))

    # ── Main game loop ────────────────────────────────────────────────────────

    async def _run_game(
        self,
        channel: discord.TextChannel,
        state: GameState,
        genre_key: str = "random",
    ) -> None:
        from engine.prompts.genres import get_genre_by_key

        # Increment daily counters and resolve genre with correct tier context.
        # Done before generate_case so limits are locked in before the API call.
        async with AsyncSessionLocal() as session:
            is_premium     = await TierManager.is_premium(session, state.guild_id, creator_id=state.creator_id)
            genre_override = get_genre_by_key(genre_key, premium_allowed=is_premium)
            await server_repo.increment_games_today(session, state.guild_id)
            for uid in state.players:
                await user_repo.increment_games_today(session, uid, state.guild_id)

        final_outcome = "abandoned"   # safe default if anything throws before resolution
        try:
            # Generate case — typing indicator shows players something is happening
            async with channel.typing():
                case = await generate_case(genre_override=genre_override)
            state.case = case
            await session_manager.save(state)

            if case.get("_fallback"):
                await channel.send(
                    "📦  *The AI story generator is taking a break — playing a classic case from our archives.*"
                )

            # Reveal phase
            await reveal_phase.run_reveal(channel, state)
            await asyncio.sleep(2)

            # 4 rounds
            game_over = False
            for round_num in range(1, config.MAX_ROUNDS + 1):
                state.round = round_num
                await session_manager.save(state)

                await round_phase.run_discussion(channel, state, round_num)
                outcome = await round_phase.run_voting(channel, state, round_num)
                await asyncio.sleep(1)

                if outcome == "murderer_eliminated" and not config.SILENT_ELIMINATION:
                    game_over = True
                    break

                await round_phase.reveal_next_clue(channel, state)
                await asyncio.sleep(2)

            if not game_over:
                # Final guess phase
                await res_phase.run_final_guess(channel, state)
                # Final reload to capture any guesses made in the last polling interval
                fresh = await session_manager.load(state.channel_id)
                if fresh:
                    state.players = fresh.players
                    state.winners = fresh.winners

            final_outcome = await res_phase.run_resolution(
                channel, state, murderer_eliminated=game_over
            )

        except Exception as e:
            logger.exception("Game loop error: %s", e)
            await channel.send(
                embed=discord.Embed(
                    title="⚠️  Something Went Wrong",
                    description=(
                        "An unexpected error stopped the game.\n\n"
                        "Use `/lobby` to start a fresh case — your stats won't be affected."
                    ),
                    color=discord.Color.red(),
                )
            )
            final_outcome = "abandoned"

        finally:
            # Persist stats and clean up
            await self._save_stats(state, final_outcome)
            await session_manager.delete(state.channel_id)

        # ── Post-game UI (shown after session is fully cleaned up) ────────────
        if final_outcome != "abandoned":
            from bot.views.post_game_view import PostGameView
            post_view = PostGameView(
                guild_id=state.guild_id,
                channel_id=state.channel_id,
                game_id=state.game_id,
                run_game_fn=self._run_game,
            )
            await channel.send(
                embed=discord.Embed(
                    title="🕵️  Ready for Another Case?",
                    description=(
                        "Great investigation! Start a new lobby or check the leaderboard "
                        "to see how your team stacks up."
                    ),
                    color=discord.Color.dark_blue(),
                ),
                view=post_view,
            )

    async def _save_stats(self, state: GameState, outcome: str) -> None:
        async with AsyncSessionLocal() as session:
            try:
                await game_repo.save_completed_game(session, state, outcome)

                # Don't touch user stats for abandoned games — the error message
                # tells players their stats won't be affected, and crashing mid-game
                # shouldn't count against anyone's record.
                if outcome != "abandoned":
                    for user_id, player in state.players.items():
                        won = user_id in state.winners
                        await user_repo.record_game_end(
                            session=session,
                            user_id=user_id,
                            guild_id=state.guild_id,
                            rounds_played=state.round,
                            won=won,
                            guessed_correctly=bool(player.guessed_correctly),
                            role=player.role,
                            display_name=player.display_name,
                        )
            except Exception as e:
                logger.error("Failed to save stats: %s", e)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GameCog(bot))
