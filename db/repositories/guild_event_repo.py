from __future__ import annotations
"""Guild install/remove event tracking."""
import discord
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import GuildEvent


async def record(
    session: AsyncSession,
    guild: discord.Guild,
    event_type: str,
) -> None:
    """Log a 'joined' or 'left' event for a guild."""
    session.add(GuildEvent(
        guild_id     = guild.id,
        guild_name   = guild.name,
        member_count = guild.member_count,
        event_type   = event_type,
    ))
    await session.commit()


async def get_recent(session: AsyncSession, limit: int = 20) -> list[GuildEvent]:
    """Return the most recent guild events, newest first."""
    result = await session.execute(
        select(GuildEvent)
        .order_by(GuildEvent.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_totals(session: AsyncSession) -> tuple[int, int]:
    """Return (total_joined, total_left) counts."""
    joined = await session.execute(
        select(func.count()).where(GuildEvent.event_type == "joined")
    )
    left = await session.execute(
        select(func.count()).where(GuildEvent.event_type == "left")
    )
    return joined.scalar() or 0, left.scalar() or 0
