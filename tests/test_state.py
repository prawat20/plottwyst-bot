"""
Tests for GameState / PlayerState pure logic:
  - vote_tally (only confirmed votes count)
  - majority_vote (strict majority required)
  - all_players_guessed property
  - serialisation round-trip
"""
from __future__ import annotations
import pytest
from tests.conftest import make_state
from game.state import GameState, PlayerState


# ── vote_tally ────────────────────────────────────────────────────────────────

class TestVoteTally:
    def test_empty_returns_empty(self):
        state = make_state(3)
        assert state.vote_tally() == {}

    def test_pending_vote_not_counted(self):
        """A vote in state.votes that is NOT in confirmed_votes must not appear in tally."""
        state = make_state(3)
        uid = list(state.players.keys())[0]
        state.votes[uid] = "Victor Crane"
        # deliberately NOT appending to confirmed_votes
        assert state.vote_tally() == {}

    def test_confirmed_vote_counted(self):
        state = make_state(3)
        uid = list(state.players.keys())[0]
        state.votes[uid] = "Victor Crane"
        state.confirmed_votes.append(uid)
        assert state.vote_tally() == {"Victor Crane": 1}

    def test_multiple_votes_same_suspect(self):
        state = make_state(3)
        uids = list(state.players.keys())
        for uid in uids[:2]:
            state.votes[uid] = "Lady Ash"
            state.confirmed_votes.append(uid)
        assert state.vote_tally() == {"Lady Ash": 2}

    def test_split_votes(self):
        state = make_state(4)
        uids = list(state.players.keys())
        state.votes[uids[0]] = "Victor Crane"
        state.votes[uids[1]] = "Lady Ash"
        state.confirmed_votes.extend([uids[0], uids[1]])
        tally = state.vote_tally()
        assert tally == {"Victor Crane": 1, "Lady Ash": 1}

    def test_confirmed_vote_for_missing_suspect_ignored(self):
        """Edge case: uid is confirmed but has no entry in votes dict."""
        state = make_state(2)
        uid = list(state.players.keys())[0]
        state.confirmed_votes.append(uid)
        # uid not in state.votes at all
        assert state.vote_tally() == {}


# ── majority_vote ─────────────────────────────────────────────────────────────

class TestMajorityVote:
    def test_no_votes_returns_none(self):
        state = make_state(3)
        assert state.majority_vote() is None

    def test_single_player_votes_self(self):
        """With 1 player, 1 vote > 0.5 → majority."""
        state = make_state(1)
        uid = list(state.players.keys())[0]
        state.votes[uid] = "Victor Crane"
        state.confirmed_votes.append(uid)
        assert state.majority_vote() == "Victor Crane"

    def test_exactly_half_is_not_majority(self):
        """2 players, 1 vote: 1 > 2/2 = 1 is False → no majority."""
        state = make_state(2)
        uid = list(state.players.keys())[0]
        state.votes[uid] = "Victor Crane"
        state.confirmed_votes.append(uid)
        assert state.majority_vote() is None

    def test_two_of_three_is_majority(self):
        """3 players, 2 votes for same suspect: 2 > 1.5 → majority."""
        state = make_state(3)
        uids = list(state.players.keys())
        for uid in uids[:2]:
            state.votes[uid] = "Victor Crane"
            state.confirmed_votes.append(uid)
        assert state.majority_vote() == "Victor Crane"

    def test_one_of_three_is_not_majority(self):
        state = make_state(3)
        uid = list(state.players.keys())[0]
        state.votes[uid] = "Victor Crane"
        state.confirmed_votes.append(uid)
        assert state.majority_vote() is None

    def test_tie_returns_none(self):
        """2 votes each for two suspects with 4 players: 2 > 2 is False."""
        state = make_state(4)
        uids = list(state.players.keys())
        state.votes[uids[0]] = "Victor Crane"
        state.votes[uids[1]] = "Victor Crane"
        state.votes[uids[2]] = "Lady Ash"
        state.votes[uids[3]] = "Lady Ash"
        state.confirmed_votes.extend(uids)
        assert state.majority_vote() is None

    def test_three_of_four_is_majority(self):
        state = make_state(4)
        uids = list(state.players.keys())
        for uid in uids[:3]:
            state.votes[uid] = "Dr. Finch"
            state.confirmed_votes.append(uid)
        assert state.majority_vote() == "Dr. Finch"

    def test_only_top_suspect_returned(self):
        """Returns the suspect with most confirmed votes, not a random one."""
        state = make_state(5)
        uids = list(state.players.keys())
        # 3 for Crane, 1 for Ash, 1 for Finch
        for uid in uids[:3]:
            state.votes[uid] = "Victor Crane"
            state.confirmed_votes.append(uid)
        state.votes[uids[3]] = "Lady Ash"
        state.confirmed_votes.append(uids[3])
        # 3 > 2.5 → strict majority
        assert state.majority_vote() == "Victor Crane"


# ── all_players_guessed ───────────────────────────────────────────────────────

class TestAllPlayersGuessed:
    def test_false_when_none_guessed(self):
        state = make_state(3)
        assert state.all_players_guessed is False

    def test_false_when_some_guessed(self):
        state = make_state(3)
        uids = list(state.players.keys())
        state.players[uids[0]].has_guessed = True
        assert state.all_players_guessed is False

    def test_true_when_all_guessed(self):
        state = make_state(3)
        for p in state.players.values():
            p.has_guessed = True
        assert state.all_players_guessed is True

    def test_true_with_single_player(self):
        state = make_state(1)
        for p in state.players.values():
            p.has_guessed = True
        assert state.all_players_guessed is True

    def test_empty_players_is_trivially_true(self):
        """all() of empty iterable is True — document this edge case explicitly."""
        state = make_state(0)
        assert state.all_players_guessed is True


# ── murderer property ─────────────────────────────────────────────────────────

class TestMurdererProperty:
    def test_returns_murderer_name(self):
        state = make_state()
        assert state.murderer == "Victor Crane"

    def test_empty_case_returns_empty_string(self):
        state = GameState.new(guild_id=1, channel_id=1, creator_id=1)
        assert state.murderer == ""


# ── serialisation round-trip ──────────────────────────────────────────────────

class TestSerialisation:
    def test_gamestate_round_trip(self):
        state = make_state(3)
        uid = list(state.players.keys())[0]
        state.votes[uid] = "Victor Crane"
        state.confirmed_votes.append(uid)
        state.winners.append(uid)

        restored = GameState.from_dict(state.to_dict())

        assert restored.game_id == state.game_id
        assert restored.murderer == state.murderer
        assert restored.confirmed_votes == state.confirmed_votes
        assert restored.winners == state.winners
        assert restored.votes == state.votes
        # Players survive the round-trip
        assert set(restored.players.keys()) == set(state.players.keys())

    def test_player_state_round_trip(self):
        p = PlayerState(
            user_id=42,
            display_name="Alice",
            has_guessed=True,
            final_guess="Victor Crane",
            guessed_correctly=True,
            votes_cast=2,
        )
        restored = PlayerState.from_dict(p.to_dict())
        assert restored.user_id == 42
        assert restored.has_guessed is True
        assert restored.guessed_correctly is True
        assert restored.votes_cast == 2

    def test_player_state_backwards_compat_missing_votes_cast(self):
        """Old sessions saved before votes_cast field must still load."""
        d = {
            "user_id": 1,
            "display_name": "Bob",
            "role": "detective",
            "has_guessed": False,
            "final_guess": None,
            "guessed_correctly": None,
            "dm_clues": [],
            # votes_cast deliberately absent
        }
        p = PlayerState.from_dict(d)
        assert p.votes_cast == 0

    def test_int_keys_restored_from_string_keys(self):
        """to_dict serialises player/vote keys as strings; from_dict must restore ints."""
        state = make_state(2)
        uids = list(state.players.keys())
        state.votes[uids[0]] = "Lady Ash"
        state.confirmed_votes.append(uids[0])

        restored = GameState.from_dict(state.to_dict())
        assert all(isinstance(k, int) for k in restored.players.keys())
        assert all(isinstance(k, int) for k in restored.votes.keys())
