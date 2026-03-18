"""
End-to-end consistency tests — simulate every field access the game engine
makes on a case dict, for both template-generated and sample (Gemini-quality) cases.

Tests are grouped by game phase:
  1. reveal.py       — crime scene, suspect roster, opening clues
  2. suspect_view.py — paginated suspect profile viewer
  3. round.py        — voting board, clue reveal
  4. resolution.py   — scorecard, solution reveal, plottwyst, evidence recap
  5. validator.py    — full validate_case pass
  6. Cross-cutting   — structural uniqueness, Discord length limits

Covers both sources:
  - generate_template_case()  (template generator)
  - SAMPLE_CASES              (representative Gemini-quality cases)
"""
from __future__ import annotations
import pytest
from engine.template_generator import generate_template_case
from engine.sample_cases import SAMPLE_CASES, load_sample_case
from engine.validator import validate_case
from game.phases.reveal import CLUE_TYPE_EMOJI, CLUE_TYPE_LABEL


# ── Fixtures / helpers ────────────────────────────────────────────────────────

def _template_cases(n: int = 30) -> list[dict]:
    cases = [generate_template_case() for _ in range(n)]
    for c in cases:
        validate_case(c)   # normalise is_murderer / is_red_herring flags
    return cases


def _all_cases() -> list[dict]:
    """Return template cases + every sample case (via load path), all validated."""
    cases = _template_cases(30)
    for sc in SAMPLE_CASES:
        import copy
        c = copy.deepcopy(sc)
        # Populate clue_pool exactly as load_sample_case() does
        c["clue_pool"] = [
            c["clues"]["round_1"],
            c["clues"]["round_2"],
            c["clues"]["round_3"],
            c["clues"]["round_4"],
        ]
        validate_case(c)
        cases.append(c)
    return cases


ALL_CASES = _all_cases()


# ── Phase 1: reveal.py — crime scene ─────────────────────────────────────────

class TestRevealCrimeScene:
    """reveal.py lines: setting['atmosphere'], setting['venue'], setting['era'],
    setting['genre'], victim['name'], victim['background']"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_setting_fields_present_and_nonempty(self, case):
        s = case["setting"]
        for key in ("atmosphere", "venue", "era", "genre"):
            assert isinstance(s[key], str) and s[key].strip(), \
                f"setting['{key}'] is empty"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_victim_fields_present_and_nonempty(self, case):
        v = case["victim"]
        for key in ("name", "background"):
            assert isinstance(v[key], str) and v[key].strip(), \
                f"victim['{key}'] is empty"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_atmosphere_discord_length(self, case):
        # embed description cap is 4096 chars
        assert len(case["setting"]["atmosphere"]) <= 4096, \
            "atmosphere too long for Discord embed description"


# ── Phase 2: suspect_view.py — paginated profiles ────────────────────────────

class TestSuspectView:
    """suspect_view.py: s['name'], s['relation'], s['last_seen'], s['trait'],
    s['motive'], s['alibi'], s.get('occupation')"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_exactly_six_suspects(self, case):
        assert len(case["suspects"]) == 6

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_suspect_required_fields_nonempty(self, case):
        required = ("name", "relation", "last_seen", "trait", "motive", "alibi")
        for s in case["suspects"]:
            for key in required:
                assert isinstance(s[key], str) and s[key].strip(), \
                    f"suspect '{s.get('name', '?')}' has empty '{key}'"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_suspect_occupation_present(self, case):
        for s in case["suspects"]:
            assert "occupation" in s, \
                f"suspect '{s['name']}' missing 'occupation'"
            assert isinstance(s["occupation"], str) and s["occupation"].strip(), \
                f"suspect '{s['name']}' has empty 'occupation'"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_suspect_profile_discord_length(self, case):
        # suspect embed fields: profile_line + motive + alibi — each ≤ 1024
        for s in case["suspects"]:
            occupation = s.get("occupation", "")
            if occupation:
                profile_line = (
                    f"**Relation:** {s['relation']}  ·  **Occupation:** {occupation}"
                    f"  ·  **Last Seen:** {s['last_seen']}\n*{s['trait']}*"
                )
            else:
                profile_line = (
                    f"**Relation:** {s['relation']}  ·  **Last Seen:** {s['last_seen']}"
                    f"\n*{s['trait']}*"
                )
            assert len(profile_line) <= 1024, \
                f"profile_line for '{s['name']}' exceeds 1024 chars"
            assert len(s["motive"]) <= 1024, \
                f"motive for '{s['name']}' exceeds 1024 chars"
            alibi_display = f'*"{s["alibi"]}"*'
            assert len(alibi_display) <= 1024, \
                f"alibi display for '{s['name']}' exceeds 1024 chars"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_suspect_names_unique(self, case):
        names = [s["name"] for s in case["suspects"]]
        assert len(names) == len(set(names)), f"Duplicate suspect names: {names}"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_suspect_last_names_unique(self, case):
        last_names = [s["name"].rsplit(" ", 1)[-1] for s in case["suspects"]]
        assert len(last_names) == len(set(last_names)), \
            f"Duplicate last names: {last_names}"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_suspect_relations_unique(self, case):
        relations = [s["relation"] for s in case["suspects"]]
        assert len(relations) == len(set(relations)), \
            f"Duplicate relations: {relations}"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_innocent_alibis_unique(self, case):
        innocent_alibis = [
            s["alibi"] for s in case["suspects"]
            if not s["is_murderer"] and not s["is_red_herring"]
        ]
        assert len(innocent_alibis) == len(set(innocent_alibis)), \
            f"Duplicate innocent alibis: {innocent_alibis}"


# ── Phase 3: reveal.py — opening clues ───────────────────────────────────────

class TestOpeningClues:
    """reveal.py: clues['opening'] — 3 clues, each with type + text"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_exactly_three_opening_clues(self, case):
        assert len(case["clues"]["opening"]) == 3

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_opening_clue_fields_nonempty(self, case):
        for i, clue in enumerate(case["clues"]["opening"]):
            assert isinstance(clue["type"], str) and clue["type"].strip(), \
                f"opening clue {i} has empty 'type'"
            assert isinstance(clue["text"], str) and clue["text"].strip(), \
                f"opening clue {i} has empty 'text'"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_opening_clue_text_discord_length(self, case):
        # clue text used as embed field value — ≤ 1024
        for i, clue in enumerate(case["clues"]["opening"]):
            assert len(clue["text"]) <= 1024, \
                f"opening clue {i} text exceeds 1024 chars"


# ── Phase 3: round.py — round clues & clue pool ──────────────────────────────

class TestRoundClues:
    """round.py reveal_next_clue: clue_pool items, each with type + text"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_clue_pool_has_four_items(self, case):
        assert len(case["clue_pool"]) == 4, \
            f"clue_pool has {len(case['clue_pool'])} items, expected 4"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_round_clues_match_clue_pool(self, case):
        """clue_pool must contain the same 4 round clues (may be same object or equal dict)."""
        expected = [
            case["clues"]["round_1"],
            case["clues"]["round_2"],
            case["clues"]["round_3"],
            case["clues"]["round_4"],
        ]
        assert case["clue_pool"] == expected, \
            "clue_pool does not match round_1..round_4 clues"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_round_clue_fields_nonempty(self, case):
        for key in ("round_1", "round_2", "round_3", "round_4"):
            clue = case["clues"][key]
            assert isinstance(clue["type"], str) and clue["type"].strip(), \
                f"{key} has empty 'type'"
            assert isinstance(clue["text"], str) and clue["text"].strip(), \
                f"{key} has empty 'text'"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_round_clue_text_discord_length(self, case):
        for key in ("round_1", "round_2", "round_3", "round_4"):
            clue = case["clues"][key]
            assert len(clue["text"]) <= 1024, \
                f"{key} text exceeds 1024 chars"


# ── Phase 4: resolution.py — solution + plottwyst ─────────────────────────────

class TestResolution:
    """resolution.py: solution, plottwyst, red_herring, murderer profile fields"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_solution_nonempty(self, case):
        assert isinstance(case["solution"], str) and case["solution"].strip()

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_solution_discord_length(self, case):
        prefix = f"**The murderer was {case['murderer']}.**\n\n"
        full = prefix + case["solution"]
        assert len(full) <= 4096, "solution + prefix exceeds embed description limit"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_plottwyst_nonempty(self, case):
        assert isinstance(case.get("plottwyst"), str) and case["plottwyst"].strip(), \
            "plottwyst is missing or empty"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_plottwyst_discord_length(self, case):
        # shown in embed field value — capped at 512 in resolution.py, but check raw
        assert len(case.get("plottwyst", "")) <= 1024, \
            "plottwyst exceeds 1024 chars before Discord cap"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_murderer_profile_accessible(self, case):
        """resolution.py does: next(s for s in suspects if s['name'] == murderer_name)"""
        murderer_name = case["murderer"]
        profile = next((s for s in case["suspects"] if s["name"] == murderer_name), None)
        assert profile is not None, f"murderer '{murderer_name}' not found in suspects"
        # Fields accessed: motive, trait, last_seen
        for key in ("motive", "trait", "last_seen"):
            assert key in profile and profile[key], \
                f"murderer profile missing '{key}'"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_red_herring_in_suspects(self, case):
        names = [s["name"] for s in case["suspects"]]
        assert case["red_herring"] in names, \
            f"red_herring '{case['red_herring']}' not in suspects"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_murderer_ne_red_herring(self, case):
        assert case["murderer"] != case["red_herring"], \
            "murderer and red_herring are the same person"


# ── Phase 5: game flow flags ──────────────────────────────────────────────────

class TestFlags:
    """is_murderer / is_red_herring flags set correctly after validate_case"""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_exactly_one_murderer_flag(self, case):
        murderers = [s for s in case["suspects"] if s["is_murderer"]]
        assert len(murderers) == 1, f"Expected 1 murderer flag, got {len(murderers)}"
        assert murderers[0]["name"] == case["murderer"]

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_exactly_one_red_herring_flag(self, case):
        rhs = [s for s in case["suspects"] if s["is_red_herring"]]
        assert len(rhs) == 1, f"Expected 1 red_herring flag, got {len(rhs)}"
        assert rhs[0]["name"] == case["red_herring"]

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_four_innocent_suspects(self, case):
        innocents = [s for s in case["suspects"] if not s["is_murderer"] and not s["is_red_herring"]]
        assert len(innocents) == 4


# ── Phase 6: clue type values ─────────────────────────────────────────────────

_KNOWN_TYPES = set(CLUE_TYPE_EMOJI.keys())


class TestClueTypes:
    """All clue types should be recognised so the correct emoji is shown."""

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_opening_clue_types_known(self, case):
        for i, clue in enumerate(case["clues"]["opening"]):
            assert clue["type"] in _KNOWN_TYPES, \
                f"opening clue {i} has unknown type '{clue['type']}'"

    @pytest.mark.parametrize("case", ALL_CASES)
    def test_round_clue_types_known(self, case):
        for key in ("round_1", "round_2", "round_3", "round_4"):
            clue = case["clues"][key]
            assert clue["type"] in _KNOWN_TYPES, \
                f"{key} has unknown type '{clue['type']}'"


# ── Structural uniqueness (template only) ─────────────────────────────────────

_TEMPLATE_CASES = _template_cases(50)


class TestTemplateUniqueness:
    """Run on 50 template cases to catch systematic duplication bugs."""

    @pytest.mark.parametrize("case", _TEMPLATE_CASES)
    def test_no_duplicate_last_names(self, case):
        last_names = [s["name"].rsplit(" ", 1)[-1] for s in case["suspects"]]
        assert len(last_names) == len(set(last_names)), \
            f"Duplicate last names: {last_names}"

    @pytest.mark.parametrize("case", _TEMPLATE_CASES)
    def test_no_duplicate_relations(self, case):
        relations = [s["relation"] for s in case["suspects"]]
        assert len(relations) == len(set(relations)), \
            f"Duplicate relations: {relations}"

    @pytest.mark.parametrize("case", _TEMPLATE_CASES)
    def test_innocent_alibis_not_all_same(self, case):
        alibis = [
            s["alibi"] for s in case["suspects"]
            if not s["is_murderer"] and not s["is_red_herring"]
        ]
        # At minimum the 4 innocent alibis must not all be identical
        assert len(set(alibis)) > 1, "All innocent alibis are identical"

    @pytest.mark.parametrize("case", _TEMPLATE_CASES)
    def test_plottwyst_mentions_murderer_or_red_herring(self, case):
        plottwyst = case.get("plottwyst", "")
        murderer_first = case["murderer"].split()[0]
        rh_first = case["red_herring"].split()[0]
        assert murderer_first in plottwyst or rh_first in plottwyst, \
            f"plottwyst doesn't mention murderer or red herring:\n{plottwyst}"

    @pytest.mark.parametrize("case", _TEMPLATE_CASES)
    def test_round2_contains_plottwyst_hint(self, case):
        """round_2 should have the framing hint appended."""
        r2_text = case["clues"]["round_2"]["text"]
        hint_phrases = [
            "deliberate placement",
            "calculated attempt",
            "arranged for discovery",
        ]
        assert any(phrase in r2_text for phrase in hint_phrases), \
            f"round_2 missing plottwyst hint:\n{r2_text}"
