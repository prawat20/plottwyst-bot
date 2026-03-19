"""
Tests for engine/prompts/system_prompt.py — build_prompt().

Covers all 12 arc × arc_position combinations and verifies:
- No exceptions raised
- Prompt is a non-empty string
- The active arc variant name appears in the prompt
- The arc position numbers are referenced correctly
- Round 3/4 clue instructions reference the arc correctly
"""
from __future__ import annotations
import pytest
from engine.prompts.system_prompt import build_prompt

_GENRE_CTX = {
    "genre": "Classic Whodunit",
    "era": "1920s",
    "venue": "Blackwood Manor",
    "murder_method_hint": "poison",
    "clue_flavour": "physical, testimonial, documentary",
}

_ARCS = ["A", "B", "C", "E"]
_POSITIONS = [1, 2, 3]

_ARC_NAMES = {
    "A": "PURE SYNTHESIS",
    "B": "INNOCENT MENTION",
    "C": "DOUBLE SUSPECT",
    "E": "FALSE WITNESS",
}


@pytest.mark.parametrize("arc", _ARCS)
@pytest.mark.parametrize("arc_position", _POSITIONS)
class TestBuildPromptAllCombinations:
    def test_returns_nonempty_string(self, arc, arc_position):
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        assert isinstance(prompt, str)
        assert len(prompt) > 500

    def test_arc_variant_name_present(self, arc, arc_position):
        """The prompt must name which variant is active."""
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        assert _ARC_NAMES[arc] in prompt

    def test_arc_position_referenced_in_rule_8(self, arc, arc_position):
        """Rule 8 must mention the non-arc positions as red-herring clues."""
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        prompt_lower = prompt.lower()
        non_arc = sorted(p for p in _POSITIONS if p != arc_position)
        for pos in non_arc:
            assert f"opening clue {pos}" in prompt_lower

    def test_rh_clue_slots_correct(self, arc, arc_position):
        """The two non-arc slots must be the lower (physical) and higher (timeline) positions."""
        non_arc = sorted(p for p in _POSITIONS if p != arc_position)
        rh1_pos, rh2_pos = non_arc[0], non_arc[1]
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        assert "physical" in prompt
        assert "timeline" in prompt
        # Both non-arc positions are referenced in the opening clue block rules
        assert f"Opening clue {rh1_pos}" in prompt or f"opening clue {rh1_pos}" in prompt
        assert f"Opening clue {rh2_pos}" in prompt or f"opening clue {rh2_pos}" in prompt

    def test_genre_context_embedded(self, arc, arc_position):
        """Genre, era, venue, and murder method must appear in the prompt."""
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        assert "Classic Whodunit" in prompt
        assert "1920s" in prompt
        assert "Blackwood Manor" in prompt
        assert "poison" in prompt

    def test_six_suspects_rule_present(self, arc, arc_position):
        """Rule 1 (exactly 6 suspects) must always be present."""
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        assert "6 suspects" in prompt or "Exactly 6" in prompt

    def test_round_3_4_instructions_present(self, arc, arc_position):
        """Round 3 and round 4 clue instructions must be present for every arc."""
        prompt = build_prompt(_GENRE_CTX, arc=arc, arc_position=arc_position)
        assert "Round 3" in prompt
        assert "Round 4" in prompt


class TestBuildPromptArcBSpecifics:
    """Arc B (Innocent Mention) has exoneration-specific language."""
    def test_exoneration_language(self):
        for pos in _POSITIONS:
            prompt = build_prompt(_GENRE_CTX, arc="B", arc_position=pos)
            assert "EXONERATION" in prompt or "exoneration" in prompt.lower()

    def test_r3_dismantles_arc_clue(self):
        """Arc B R3 must reference the arc position (the exoneration clue it dismantles)."""
        for pos in _POSITIONS:
            prompt = build_prompt(_GENRE_CTX, arc="B", arc_position=pos)
            assert f"opening clue {pos}" in prompt


class TestBuildPromptArcCSpecifics:
    """Arc C (Double Suspect) must introduce second suspect language."""
    def test_second_suspect_language(self):
        for pos in _POSITIONS:
            prompt = build_prompt(_GENRE_CTX, arc="C", arc_position=pos)
            assert "SECOND" in prompt or "second suspect" in prompt.lower()

    def test_emergence_clue_language(self):
        for pos in _POSITIONS:
            prompt = build_prompt(_GENRE_CTX, arc="C", arc_position=pos)
            assert "EMERGENCE" in prompt or "second strong suspect" in prompt.lower()


class TestBuildPromptArcESpecifics:
    """Arc E (False Witness) must contain witness/lying language."""
    def test_false_witness_language(self):
        for pos in _POSITIONS:
            prompt = build_prompt(_GENRE_CTX, arc="E", arc_position=pos)
            assert "FALSE WITNESS" in prompt or "WITNESS STATEMENT" in prompt

    def test_r3_dismantles_witness_statement(self):
        """Arc E R3 must reference the arc position (the false witness clue)."""
        for pos in _POSITIONS:
            prompt = build_prompt(_GENRE_CTX, arc="E", arc_position=pos)
            assert f"opening clue {pos}" in prompt
