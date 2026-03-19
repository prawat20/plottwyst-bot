from __future__ import annotations
"""Server (guild) database operations."""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Server


async def get_or_create(session: AsyncSession, guild_id: int) -> Server:
    result = await session.execute(select(Server).where(Server.guild_id == guild_id))
    server = result.scalar_one_or_none()
    if server is None:
        server = Server(guild_id=guild_id)
        session.add(server)
        await session.commit()
        await session.refresh(server)
    return server


async def get_tier(session: AsyncSession, guild_id: int) -> str:
    server = await get_or_create(session, guild_id)
    return server.tier


async def set_tier(session: AsyncSession, guild_id: int, tier: str) -> None:
    server = await get_or_create(session, guild_id)
    server.tier = tier
    if tier == "premium":
        server.premium_since = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()


async def check_daily_limit(session: AsyncSession, guild_id: int, limit: int) -> bool:
    """Returns True if the server can start another game today."""
    server = await get_or_create(session, guild_id)
    today  = datetime.now(timezone.utc).replace(tzinfo=None).date()
    if server.games_date is None or server.games_date.date() < today:
        server.games_today = 0
        server.games_date  = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.commit()
    return server.games_today < limit


async def increment_games_today(session: AsyncSession, guild_id: int) -> None:
    server = await get_or_create(session, guild_id)
    today  = datetime.now(timezone.utc).replace(tzinfo=None).date()
    if server.games_date is None or server.games_date.date() < today:
        server.games_today = 0
        server.games_date  = datetime.now(timezone.utc).replace(tzinfo=None)
    server.games_today += 1
    await session.commit()
