from __future__ import annotations
"""
Redis-backed session manager.

One GameState per Discord channel, keyed by channel_id.
Game state survives bot restarts via Redis persistence.
TTL auto-cleans abandoned games after GAME_STATE_TTL seconds.
"""
import asyncio
import json
import logging
import redis.asyncio as aioredis
from game.state import GameState
import config

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(config.REDIS_URL, decode_responses=True)
    return _redis


def _key(channel_id: int) -> str:
    return f"plottwyst:game:{channel_id}"


async def _with_retry(coro_fn, *args, retries: int = 3, **kwargs):
    """Run a Redis operation with reconnection retries on failure."""
    global _redis
    for attempt in range(retries):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as e:
            logger.warning("Redis operation failed (attempt %d/%d): %s", attempt + 1, retries, e)
            _redis = None  # force reconnect on next get_redis() call
            if attempt < retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
    logger.error("Redis operation failed after %d attempts", retries)
    return None


async def save(state: GameState) -> None:
    async def _save():
        r = await get_redis()
        await r.set(_key(state.channel_id), json.dumps(state.to_dict()), ex=config.GAME_STATE_TTL)
    await _with_retry(_save)


async def load(channel_id: int) -> GameState | None:
    async def _load():
        r = await get_redis()
        data = await r.get(_key(channel_id))
        if data is None:
            return None
        return GameState.from_dict(json.loads(data))
    return await _with_retry(_load)


async def delete(channel_id: int) -> None:
    async def _delete():
        r = await get_redis()
        await r.delete(_key(channel_id))
    await _with_retry(_delete)


async def exists(channel_id: int) -> bool:
    async def _exists():
        r = await get_redis()
        return bool(await r.exists(_key(channel_id)))
    result = await _with_retry(_exists)
    return result if result is not None else False
