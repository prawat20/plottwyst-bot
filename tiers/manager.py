from __future__ import annotations
"""TierManager: resolves feature values for a guild at runtime."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from tiers.entitlements import Feature, TIERS
from db.repositories import server_repo
import config


class TierManager:
    @staticmethod
    def _is_dev_user(user_id: int) -> bool:
        """True if this user is in the PREMIUM_USER_IDS override list."""
        return user_id in config.PREMIUM_USER_IDS

    @staticmethod
    async def get(session: AsyncSession, guild_id: int, feature: Feature, creator_id: int = 0) -> Any:
        """Return the feature value for this guild's current tier.
        Dev users always receive premium feature values.
        """
        if TierManager._is_dev_user(creator_id):
            return TIERS["premium"][feature]
        tier = await server_repo.get_tier(session, guild_id)
        return TIERS.get(tier, TIERS["free"])[feature]

    @staticmethod
    async def is_premium(session: AsyncSession, guild_id: int, creator_id: int = 0) -> bool:
        if TierManager._is_dev_user(creator_id):
            return True
        tier = await server_repo.get_tier(session, guild_id)
        return tier == "premium"

    @staticmethod
    async def can_start_game(
        session: AsyncSession,
        guild_id: int,
        creator_id: int = 0,
        channel_id: int = 0,
    ) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        reason is empty string when allowed.
        Dev users bypass all limits.
        Limit hits are logged for upsell analytics.
        """
        from db.repositories import limit_hit_repo

        if TierManager._is_dev_user(creator_id):
            return True, ""

        limit = await TierManager.get(session, guild_id, Feature.DAILY_GAME_LIMIT)
        if limit is None:
            return True, ""

        allowed = await server_repo.check_daily_limit(session, guild_id, limit)
        if not allowed:
            # Log the hit for upsell tracking
            await limit_hit_repo.record(
                session    = session,
                guild_id   = guild_id,
                user_id    = creator_id,
                channel_id = channel_id,
                limit_type = "daily_game_limit",
            )
            return False, (
                f"Your server has reached its **{limit} games/day** limit. "
                "Upgrade to premium for unlimited games."
            )
        return True, ""
