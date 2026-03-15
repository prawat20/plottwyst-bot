from __future__ import annotations
"""Async SQLAlchemy session factory and table initialiser."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from db.models import Base
import config

engine = create_async_engine(config.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Create all tables if they don't exist, then apply any column-level
    migrations that create_all won't handle on existing tables.
    Each ALTER is wrapped in IF NOT EXISTS so it's safe to run every startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Column migrations — add new columns to existing tables safely
        migrations = [
            "ALTER TABLE users      ADD COLUMN IF NOT EXISTS display_name  VARCHAR(100)",
            "ALTER TABLE limit_hits ADD COLUMN IF NOT EXISTS channel_id    BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE users      ADD COLUMN IF NOT EXISTS games_today   INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users      ADD COLUMN IF NOT EXISTS games_date    TIMESTAMP",
            """
            CREATE TABLE IF NOT EXISTS guild_events (
                id           SERIAL PRIMARY KEY,
                guild_id     BIGINT        NOT NULL,
                guild_name   VARCHAR(100),
                member_count INTEGER,
                event_type   VARCHAR(20)   NOT NULL,
                created_at   TIMESTAMP     NOT NULL DEFAULT NOW()
            )
            """,
        ]
        for sql in migrations:
            await conn.execute(__import__("sqlalchemy").text(sql))


async def get_session() -> AsyncSession:
    """Yield a session — use as async context manager."""
    async with AsyncSessionLocal() as session:
        yield session
