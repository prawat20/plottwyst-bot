"""
GameState and PlayerState dataclasses.

These are serialised to Redis as JSON for persistence across bot restarts.
All fields are JSON-serialisable (no sets — use lists, no datetime objects
stored in Redis beyond ISO strings).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class PlayerState:
    user_id:           int
    display_name:      str
    role:              str  = "detective"   # Phase 3: 'murderer'
    has_guessed:       bool = False
    final_guess:       str | None = None
    guessed_correctly: bool | None = None
    votes_cast:        int = 0           # rounds this player confirmed a vote in
    dm_clues:          list[str] = field(default_factory=list)  # Phase 2 DM clues

    def to_dict(self) -> dict:
        return {
            "user_id":           self.user_id,
            "display_name":      self.display_name,
            "role":              self.role,
            "has_guessed":       self.has_guessed,
            "final_guess":       self.final_guess,
            "guessed_correctly": self.guessed_correctly,
            "votes_cast":        self.votes_cast,
            "dm_clues":          self.dm_clues,
        }

    @classmethod
    def from_dict(cls, d: dict) -> PlayerState:
        d = dict(d)
        d.setdefault("votes_cast", 0)   # backwards compat with sessions saved before this field
        return cls(**d)


@dataclass
class GameState:
    game_id:             str
    guild_id:            int
    channel_id:          int
    creator_id:          int
    phase:               str            # LOBBY | REVEAL | ROUND | VOTING | GUESS | RESOLUTION
    round:               int            # 0–4
    mode:                str            # 'standard' | 'murderer_among_players'
    players:             dict[int, PlayerState]
    case:                dict[str, Any] # Full Gemini-generated JSON
    remaining_suspects:  list[str]
    revealed_clues:      list[dict]     # Clues shown so far in channel
    clue_pool:           list[dict]     # Clues not yet revealed
    votes:               dict[int, str] # user_id -> suspect_name
    confirmed_votes:     list[int]      # user_ids who confirmed their vote
    winners:             list[int]      # user_ids who guessed correctly
    created_at:          str            # ISO datetime string
    ref_urls:            dict[str, str] # jump_url shortcuts: "scene", "suspects", "clues"

    # ── Convenience helpers ──────────────────────────────────────────────────

    @classmethod
    def new(cls, guild_id: int, channel_id: int, creator_id: int) -> GameState:
        return cls(
            game_id            = str(uuid.uuid4()),
            guild_id           = guild_id,
            channel_id         = channel_id,
            creator_id         = creator_id,
            phase              = "LOBBY",
            round              = 0,
            mode               = "standard",
            players            = {},
            case               = {},
            remaining_suspects = [],
            revealed_clues     = [],
            clue_pool          = [],
            votes              = {},
            confirmed_votes    = [],
            winners            = [],
            created_at         = datetime.now(timezone.utc).isoformat(),
            ref_urls           = {},
        )

    @property
    def murderer(self) -> str:
        return self.case.get("murderer", "")

    @property
    def all_players_guessed(self) -> bool:
        return all(p.has_guessed for p in self.players.values())

    def vote_tally(self) -> dict[str, int]:
        tally: dict[str, int] = {}
        for uid in self.confirmed_votes:
            suspect = self.votes.get(uid)
            if suspect:
                tally[suspect] = tally.get(suspect, 0) + 1
        return tally

    def majority_vote(self) -> str | None:
        """Return suspect name if they have a strict majority, else None."""
        tally = self.vote_tally()
        if not tally:
            return None
        top_suspect, top_votes = max(tally.items(), key=lambda x: x[1])
        if top_votes > len(self.players) / 2:
            return top_suspect
        return None

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "game_id":            self.game_id,
            "guild_id":           self.guild_id,
            "channel_id":         self.channel_id,
            "creator_id":         self.creator_id,
            "phase":              self.phase,
            "round":              self.round,
            "mode":               self.mode,
            "players":            {str(k): v.to_dict() for k, v in self.players.items()},
            "case":               self.case,
            "remaining_suspects": self.remaining_suspects,
            "revealed_clues":     self.revealed_clues,
            "clue_pool":          self.clue_pool,
            "votes":              {str(k): v for k, v in self.votes.items()},
            "confirmed_votes":    self.confirmed_votes,
            "winners":            self.winners,
            "created_at":         self.created_at,
            "ref_urls":           self.ref_urls,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GameState:
        return cls(
            game_id            = d["game_id"],
            guild_id           = d["guild_id"],
            channel_id         = d["channel_id"],
            creator_id         = d["creator_id"],
            phase              = d["phase"],
            round              = d["round"],
            mode               = d.get("mode", "standard"),
            players            = {
                int(k): PlayerState.from_dict(v)
                for k, v in d["players"].items()
            },
            case               = d["case"],
            remaining_suspects = d["remaining_suspects"],
            revealed_clues     = d["revealed_clues"],
            clue_pool          = d["clue_pool"],
            votes              = {int(k): v for k, v in d["votes"].items()},
            confirmed_votes    = d["confirmed_votes"],
            winners            = d["winners"],
            created_at         = d["created_at"],
            ref_urls           = d.get("ref_urls", {}),
        )
