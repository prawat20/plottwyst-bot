from __future__ import annotations
"""
Redis-backed session manager.

One GameState per Discord channel, keyed by channel_id.
Game state survives bot restarts via Redis persistence.
TTL auto-cleans abandoned games after GAME_STATE_TTL seconds.
"""
import json
import redis.asyncio as aioredis
from game.state import GameState
import config

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(config.REDIS_URL, decode_responses=True)
    return _redis


def _key(channel_id: int) -> str:
    return f"plottwyst:game:{channel_id}"


async def save(state: GameState) -> None:
    r = await get_redis()
    await r.set(_key(state.channel_id), json.dumps(state.to_dict()), ex=config.GAME_STATE_TTL)


async def load(channel_id: int) -> GameState | None:
    r = await get_redis()
    data = await r.get(_key(channel_id))
    if data is None:
        return None
    return GameState.from_dict(json.loads(data))


async def delete(channel_id: int) -> None:
    r = await get_redis()
    await r.delete(_key(channel_id))


async def exists(channel_id: int) -> bool:
    r = await get_redis()
    return bool(await r.exists(_key(channel_id)))
