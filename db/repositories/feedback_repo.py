from __future__ import annotations
"""Feedback record database operations."""
import uuid as _uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import GameFeedback


async def save_feedback(
    session: AsyncSession,
    game_id: str,
    user_id: int,
    guild_id: int,
    plottwyst_fooled: str | None = None,
    case_rating: str | None = None,
) -> None:
    """
    Upsert a feedback record for (game_id, user_id).
    Calling this twice (once per question) merges both answers into one row.
    """
    gid = _uuid.UUID(game_id)
    result = await session.execute(
        select(GameFeedback).where(
            GameFeedback.game_id == gid,
            GameFeedback.user_id == user_id,
        )
    )
    fb = result.scalar_one_or_none()

    if fb is None:
        fb = GameFeedback(game_id=gid, user_id=user_id, guild_id=guild_id)
        session.add(fb)

    if plottwyst_fooled is not None:
        fb.plottwyst_fooled = plottwyst_fooled
    if case_rating is not None:
        fb.case_rating = case_rating

    await session.commit()
