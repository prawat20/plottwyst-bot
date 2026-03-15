from __future__ import annotations
"""User stats database operations."""
from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User


async def get_or_create(session: AsyncSession, user_id: int, guild_id: int) -> User:
    result = await session.execute(
        select(User).where(User.user_id == user_id, User.guild_id == guild_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(user_id=user_id, guild_id=guild_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def check_daily_limit(
    session: AsyncSession,
    user_id: int,
    guild_id: int,
    limit: int,
) -> bool:
    """Returns True if this user can start another game today."""
    user = await get_or_create(session, user_id, guild_id)
    today = date.today()
    if user.games_date is None or user.games_date.date() < today:
        user.games_today = 0
        user.games_date  = datetime.utcnow()
        await session.commit()
    return user.games_today < limit


async def increment_games_today(
    session: AsyncSession,
    user_id: int,
    guild_id: int,
) -> None:
    """Increment this user's daily game counter, resetting if it's a new day."""
    user = await get_or_create(session, user_id, guild_id)
    today = date.today()
    if user.games_date is None or user.games_date.date() < today:
        user.games_today = 0
        user.games_date  = datetime.utcnow()
    user.games_today += 1
    await session.commit()


async def record_game_end(
    session: AsyncSession,
    user_id: int,
    guild_id: int,
    rounds_played: int,
    won: bool,
    guessed_correctly: bool,
    role: str = "detective",
    display_name: str | None = None,
) -> None:
    user = await get_or_create(session, user_id, guild_id)
    if display_name:
        user.display_name = display_name   # keep name fresh on every game
    user.games_played    += 1
    user.rounds_played   += rounds_played
    if won:
        user.games_won   += 1
    if guessed_correctly:
        user.correct_guesses += 1
    # Phase 3 stats
    if role == "murderer":
        user.murderer_games += 1
        if won:
            user.murderer_wins += 1
    await session.commit()


async def get_leaderboard(session: AsyncSession, guild_id: int, limit: int = 10) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.guild_id == guild_id)
        .order_by(User.games_won.desc(), User.correct_guesses.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_stats(session: AsyncSession, user_id: int, guild_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.user_id == user_id, User.guild_id == guild_id)
    )
    return result.scalar_one_or_none()
