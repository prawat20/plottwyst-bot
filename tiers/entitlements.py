from __future__ import annotations
"""
Single source of truth for tier feature flags.

Adding a Phase 3/4 feature = one new Feature entry + one value per tier.
Checking a feature anywhere = TierManager.get(guild_id, Feature.X).
"""
from enum import Enum
from typing import Any


class Feature(Enum):
    MAX_PLAYERS            = "max_players"            # int: max lobby size
    DAILY_GAME_LIMIT       = "daily_game_limit"       # int | None: server-level daily cap
    USER_DAILY_GAME_LIMIT  = "user_daily_game_limit"  # int | None: per-user daily cap
    DM_CLUES               = "dm_clues"               # bool: private per-player clues
    MURDERER_MODE          = "murderer_mode"           # bool: Phase 3
    ANALYTICS              = "analytics"               # bool: /stats & /leaderboard
    CUSTOM_SETTINGS        = "custom_settings"         # bool: Phase 4


TIERS: dict[str, dict[Feature, Any]] = {
    "free": {
        Feature.MAX_PLAYERS:           5,
        Feature.DAILY_GAME_LIMIT:      10,   # server: 10 games/day
        Feature.USER_DAILY_GAME_LIMIT: 3,    # user:   3 games/day
        Feature.DM_CLUES:              False,
        Feature.MURDERER_MODE:         False,
        Feature.ANALYTICS:             True,  # leaderboard is free
        Feature.CUSTOM_SETTINGS:       False,
    },
    "premium": {
        Feature.MAX_PLAYERS:           10,
        Feature.DAILY_GAME_LIMIT:      None,  # unlimited
        Feature.USER_DAILY_GAME_LIMIT: None,  # unlimited
        Feature.DM_CLUES:              True,
        Feature.MURDERER_MODE:         True,
        Feature.ANALYTICS:             True,
        Feature.CUSTOM_SETTINGS:       True,
    },
}
