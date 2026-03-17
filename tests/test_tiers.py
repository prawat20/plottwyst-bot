"""
Tests for tiers/entitlements.py (pure data) and TierManager._is_dev_user.

TierManager.get / can_start_game depend on DB and are not tested here —
those need integration tests with a real async session.
"""
from __future__ import annotations
import pytest
from unittest.mock import patch
from tiers.entitlements import Feature, TIERS
from tiers.manager import TierManager


# ── TIERS table ───────────────────────────────────────────────────────────────

class TestTiersTable:
    def test_free_tier_has_player_cap(self):
        assert TIERS["free"][Feature.MAX_PLAYERS] == 5

    def test_premium_tier_has_larger_player_cap(self):
        assert TIERS["premium"][Feature.MAX_PLAYERS] > TIERS["free"][Feature.MAX_PLAYERS]

    def test_free_tier_has_daily_game_limit(self):
        assert TIERS["free"][Feature.DAILY_GAME_LIMIT] is not None
        assert TIERS["free"][Feature.DAILY_GAME_LIMIT] > 0

    def test_premium_tier_has_no_daily_game_limit(self):
        """None means unlimited."""
        assert TIERS["premium"][Feature.DAILY_GAME_LIMIT] is None

    def test_premium_tier_has_no_user_daily_limit(self):
        assert TIERS["premium"][Feature.USER_DAILY_GAME_LIMIT] is None

    def test_free_tier_dm_clues_disabled(self):
        assert TIERS["free"][Feature.DM_CLUES] is False

    def test_premium_tier_dm_clues_enabled(self):
        assert TIERS["premium"][Feature.DM_CLUES] is True

    def test_analytics_free_for_all(self):
        """Leaderboard is free — both tiers must have analytics enabled."""
        assert TIERS["free"][Feature.ANALYTICS] is True
        assert TIERS["premium"][Feature.ANALYTICS] is True

    def test_all_features_defined_in_both_tiers(self):
        for tier_name in ("free", "premium"):
            for feature in Feature:
                assert feature in TIERS[tier_name], (
                    f"Feature.{feature.name} missing from {tier_name} tier"
                )


# ── TierManager._is_dev_user ──────────────────────────────────────────────────

class TestIsDevUser:
    def test_unknown_user_is_not_dev(self):
        with patch("tiers.manager.config") as mock_cfg:
            mock_cfg.PREMIUM_USER_IDS = {111, 222}
            assert TierManager._is_dev_user(999) is False

    def test_listed_user_is_dev(self):
        with patch("tiers.manager.config") as mock_cfg:
            mock_cfg.PREMIUM_USER_IDS = {111, 222, 333}
            assert TierManager._is_dev_user(222) is True

    def test_empty_list_no_dev_users(self):
        with patch("tiers.manager.config") as mock_cfg:
            mock_cfg.PREMIUM_USER_IDS = set()
            assert TierManager._is_dev_user(12345) is False

    def test_zero_user_id_not_treated_as_dev(self):
        """0 is the default creator_id when not provided; must not grant dev access."""
        with patch("tiers.manager.config") as mock_cfg:
            mock_cfg.PREMIUM_USER_IDS = {111}
            assert TierManager._is_dev_user(0) is False
