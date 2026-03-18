from __future__ import annotations
"""Limit hit tracking — upsell analytics."""
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import LimitHit, User


async def record(
    session: AsyncSession,
    guild_id: int,
    user_id: int,
    channel_id: int,
    limit_type: str = "daily_game_limit",
) -> None:
    """Log one limit hit event."""
    session.add(LimitHit(
        guild_id   = guild_id,
        user_id    = user_id,
        channel_id = channel_id,
        limit_type = limit_type,
    ))
    await session.commit()


async def get_top_servers(session: AsyncSession, limit: int = 10) -> list[dict]:
    """
    Returns the servers hitting limits most often — ranked upsell candidates.
    Each row: {guild_id, hits, unique_users, last_hit}
    """
    result = await session.execute(
        select(
            LimitHit.guild_id,
            func.count(LimitHit.id).label("hits"),
            func.count(func.distinct(LimitHit.user_id)).label("unique_users"),
            func.max(LimitHit.hit_at).label("last_hit"),
        )
        .group_by(LimitHit.guild_id)
        .order_by(desc("hits"))
        .limit(limit)
    )
    return [
        {
            "guild_id":     row.guild_id,
            "hits":         row.hits,
            "unique_users": row.unique_users,
            "last_hit":     row.last_hit,
        }
        for row in result.all()
    ]


async def get_top_users(session: AsyncSession, limit: int = 10) -> list[dict]:
    """
    Returns individual users hitting limits most often across all servers.
    Each row: {user_id, guild_id, hits, last_hit, display_name}
    display_name is pulled from the users table (cached from past games).
    """
    result = await session.execute(
        select(
            LimitHit.user_id,
            LimitHit.guild_id,
            func.count(LimitHit.id).label("hits"),
            func.max(LimitHit.hit_at).label("last_hit"),
            User.display_name,
        )
        .outerjoin(
            User,
            (User.user_id == LimitHit.user_id) & (User.guild_id == LimitHit.guild_id),
        )
        .group_by(LimitHit.user_id, LimitHit.guild_id, User.display_name)
        .order_by(desc("hits"))
        .limit(limit)
    )
    return [
        {
            "user_id":      row.user_id,
            "guild_id":     row.guild_id,
            "hits":         row.hits,
            "last_hit":     row.last_hit,
            "display_name": row.display_name,
        }
        for row in result.all()
    ]
