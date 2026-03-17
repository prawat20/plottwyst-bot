"""Shared test fixtures and helpers."""
from __future__ import annotations
from game.state import GameState, PlayerState


def make_state(
    num_players: int = 3,
    suspects: list[str] | None = None,
    murderer: str = "Victor Crane",
) -> GameState:
    """Return a minimal GameState ready for voting/guess testing."""
    state = GameState.new(guild_id=1, channel_id=100, creator_id=1001)
    state.phase = "VOTING"

    if suspects is None:
        suspects = ["Victor Crane", "Lady Ash", "Dr. Finch", "Rose Mott", "Col. Ward", "Ivy Stone"]

    state.case = {
        "murderer": murderer,
        "red_herring": "Lady Ash",
        "suspects": [
            {
                "name": n,
                "gender": "unknown",
                "relation": "guest",
                "occupation": "unknown",
                "motive": "greed",
                "trait": "nervous",
                "last_seen": "library",
                "alibi": "was reading",
                "is_murderer": (n == murderer),
                "is_red_herring": (n == "Lady Ash"),
            }
            for n in suspects
        ],
        "victim": {"name": "Lord Grey", "gender": "male", "background": "wealthy lord", "secrets": "many"},
        "setting": {"genre": "classic", "era": "1920s", "venue": "manor", "atmosphere": "tense"},
        "twist": "None",
        "solution": "Victor did it.",
        "clues": {
            "opening": [
                {"type": "physical", "text": "A broken cane."},
                {"type": "testimony", "text": "Someone heard shouting."},
                {"type": "behavioral", "text": "Victor avoided eye contact."},
            ],
            "round_1": {"type": "physical", "text": "Muddy boots near the study."},
            "round_2": {"type": "document", "text": "A torn letter."},
            "round_3": {"type": "testimony", "text": "Alibi crumbles."},
            "round_4": {"type": "behavioral", "text": "Victor left early."},
        },
    }

    state.remaining_suspects = list(suspects)

    for i in range(1, num_players + 1):
        uid = 2000 + i
        state.players[uid] = PlayerState(user_id=uid, display_name=f"Player{i}")

    return state


def make_valid_case() -> dict:
    """Return a structurally valid case dict."""
    suspects = [
        {
            "name": "Victor Crane",
            "gender": "male",
            "relation": "butler",
            "occupation": "butler",
            "motive": "inheritance",
            "trait": "devious",
            "last_seen": "study",
            "alibi": "was polishing silver",
        },
        {
            "name": "Lady Ash",
            "gender": "female",
            "relation": "cousin",
            "occupation": "socialite",
            "motive": "jealousy",
            "trait": "flirtatious",
            "last_seen": "garden",
            "alibi": "was reading",
        },
        {
            "name": "Dr. Finch",
            "gender": "male",
            "relation": "physician",
            "occupation": "doctor",
            "motive": "blackmail",
            "trait": "secretive",
            "last_seen": "library",
            "alibi": "treating a patient",
        },
        {
            "name": "Rose Mott",
            "gender": "female",
            "relation": "maid",
            "occupation": "maid",
            "motive": "revenge",
            "trait": "quiet",
            "last_seen": "kitchen",
            "alibi": "preparing dinner",
        },
        {
            "name": "Col. Ward",
            "gender": "male",
            "relation": "army friend",
            "occupation": "retired colonel",
            "motive": "old debt",
            "trait": "gruff",
            "last_seen": "billiards room",
            "alibi": "playing billiards",
        },
        {
            "name": "Ivy Stone",
            "gender": "female",
            "relation": "niece",
            "occupation": "journalist",
            "motive": "story",
            "trait": "nosy",
            "last_seen": "parlour",
            "alibi": "writing notes",
        },
    ]
    return {
        "setting": {"genre": "classic", "era": "1920s", "venue": "manor", "atmosphere": "tense"},
        "victim": {"name": "Lord Grey", "gender": "male", "background": "wealthy lord", "secrets": "many"},
        "twist": "The victim faked his death once before.",
        "murderer": "Victor Crane",
        "red_herring": "Lady Ash",
        "suspects": suspects,
        "clues": {
            "opening": [
                {"type": "physical", "text": "A broken cane near the fireplace."},
                {"type": "testimony", "text": "A maid heard shouting at midnight."},
                {"type": "behavioral", "text": "Victor avoided eye contact at dinner."},
            ],
            "round_1": {"type": "physical", "text": "Muddy boots found by the study door."},
            "round_2": {"type": "document", "text": "A torn letter addressed to the victim."},
            "round_3": {"type": "testimony", "text": "Victor's alibi fell apart under questioning."},
            "round_4": {"type": "behavioral", "text": "Victor was seen leaving through the back exit."},
        },
        "solution": "Victor Crane poisoned Lord Grey to claim the inheritance.",
    }
