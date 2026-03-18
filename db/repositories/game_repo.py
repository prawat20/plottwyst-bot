from __future__ import annotations
"""Game record database operations."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Game, GamePlayer
from game.state import GameState, PlayerState


async def save_completed_game(
    session: AsyncSession,
    state: GameState,
    outcome: str,
) -> None:
    """Persist a finished game and all player records to the database."""
    correct_guess_count = sum(
        1 for p in state.players.values() if p.guessed_correctly
    )
    murderer_elim_round = state.round if outcome == "murderer_eliminated" else None

    game = Game(
        id                  = state.game_id,
        guild_id            = state.guild_id,
        channel_id          = state.channel_id,
        genre               = state.case.get("setting", {}).get("genre"),
        era                 = state.case.get("setting", {}).get("era"),
        setting             = state.case.get("setting", {}).get("venue"),
        mode                = state.mode,
        player_count        = len(state.players),
        rounds_played       = state.round,
        outcome             = outcome,
        correct_guess_count = correct_guess_count,
        murderer_elim_round = murderer_elim_round,
        started_at          = datetime.fromisoformat(state.created_at),
        ended_at            = datetime.now(timezone.utc),
    )
    session.add(game)

    for user_id, player in state.players.items():
        gp = GamePlayer(
            game_id           = state.game_id,
            user_id           = user_id,
            role              = player.role,
            guessed_correctly = player.guessed_correctly,
            final_guess       = player.final_guess,
            votes_cast        = player.votes_cast,
        )
        session.add(gp)

    await session.commit()
