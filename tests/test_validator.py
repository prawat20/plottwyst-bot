"""
Tests for engine/validator.py — case structure and logical consistency checks.
"""
from __future__ import annotations
import copy
import pytest
from engine.validator import validate_case
from tests.conftest import make_valid_case


# ── happy path ────────────────────────────────────────────────────────────────

class TestValidCase:
    def test_valid_case_passes(self):
        case = make_valid_case()
        result = validate_case(case)
        assert result is case  # returns same dict in place

    def test_is_murderer_flag_set(self):
        case = make_valid_case()
        validate_case(case)
        for s in case["suspects"]:
            assert s["is_murderer"] == (s["name"] == case["murderer"])

    def test_is_red_herring_flag_set(self):
        case = make_valid_case()
        validate_case(case)
        for s in case["suspects"]:
            assert s["is_red_herring"] == (s["name"] == case["red_herring"])


# ── top-level required keys ───────────────────────────────────────────────────

class TestTopLevelKeys:
    @pytest.mark.parametrize("missing_key", [
        "setting", "victim", "plottwyst", "murderer", "red_herring",
        "suspects", "clues", "solution",
    ])
    def test_missing_top_level_key_raises(self, missing_key):
        case = make_valid_case()
        del case[missing_key]
        with pytest.raises(ValueError, match=missing_key):
            validate_case(case)

    def test_empty_solution_raises(self):
        case = make_valid_case()
        case["solution"] = ""
        with pytest.raises(ValueError, match="solution"):
            validate_case(case)


# ── setting / victim sub-keys ─────────────────────────────────────────────────

class TestSubKeys:
    @pytest.mark.parametrize("key", ["genre", "era", "venue", "atmosphere"])
    def test_missing_setting_key(self, key):
        case = make_valid_case()
        del case["setting"][key]
        with pytest.raises(ValueError):
            validate_case(case)

    @pytest.mark.parametrize("key", ["name", "gender", "background", "secrets"])
    def test_missing_victim_key(self, key):
        case = make_valid_case()
        del case["victim"][key]
        with pytest.raises(ValueError):
            validate_case(case)


# ── suspects ──────────────────────────────────────────────────────────────────

class TestSuspects:
    def test_wrong_suspect_count_raises(self):
        case = make_valid_case()
        case["suspects"] = case["suspects"][:5]  # only 5
        with pytest.raises(ValueError, match="6 suspects"):
            validate_case(case)

    def test_extra_suspects_raises(self):
        case = make_valid_case()
        extra = copy.deepcopy(case["suspects"][0])
        extra["name"] = "Extra Person"
        case["suspects"].append(extra)
        with pytest.raises(ValueError, match="6 suspects"):
            validate_case(case)

    def test_murderer_not_in_suspects_raises(self):
        case = make_valid_case()
        case["murderer"] = "Unknown Person"
        with pytest.raises(ValueError, match="murderer"):
            validate_case(case)

    def test_red_herring_not_in_suspects_raises(self):
        case = make_valid_case()
        case["red_herring"] = "Phantom Figure"
        with pytest.raises(ValueError, match="red_herring"):
            validate_case(case)

    def test_murderer_equals_red_herring_raises(self):
        case = make_valid_case()
        case["red_herring"] = case["murderer"]
        with pytest.raises(ValueError, match="same suspect"):
            validate_case(case)

    @pytest.mark.parametrize("key", [
        "name", "gender", "relation", "occupation", "motive", "trait", "last_seen", "alibi",
    ])
    def test_missing_suspect_field_raises(self, key):
        case = make_valid_case()
        del case["suspects"][0][key]
        with pytest.raises(ValueError):
            validate_case(case)

    def test_occupation_required(self):
        """Specifically guard against regression of the missing-occupation bug."""
        case = make_valid_case()
        for s in case["suspects"]:
            del s["occupation"]
        with pytest.raises(ValueError, match="occupation"):
            validate_case(case)


# ── clues ─────────────────────────────────────────────────────────────────────

class TestClues:
    @pytest.mark.parametrize("round_key", ["opening", "round_1", "round_2", "round_3", "round_4"])
    def test_missing_clue_key_raises(self, round_key):
        case = make_valid_case()
        del case["clues"][round_key]
        with pytest.raises(ValueError):
            validate_case(case)

    def test_wrong_opening_clue_count_raises(self):
        case = make_valid_case()
        case["clues"]["opening"] = case["clues"]["opening"][:2]  # only 2 instead of 3
        with pytest.raises(ValueError, match="3 opening clues"):
            validate_case(case)

    def test_opening_clue_missing_type_raises(self):
        case = make_valid_case()
        del case["clues"]["opening"][0]["type"]
        with pytest.raises(ValueError):
            validate_case(case)

    def test_opening_clue_missing_text_raises(self):
        case = make_valid_case()
        del case["clues"]["opening"][1]["text"]
        with pytest.raises(ValueError):
            validate_case(case)

    def test_round_clue_missing_type_raises(self):
        case = make_valid_case()
        del case["clues"]["round_2"]["type"]
        with pytest.raises(ValueError):
            validate_case(case)
