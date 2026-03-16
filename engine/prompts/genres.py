from __future__ import annotations
"""
All available game genres and their era/setting options.

Each genre has a stable `key` used by the lobby Select and the generator.
`premium` = True means the genre is locked to premium servers.

Free  : random, victorian_gothic, noir_1920s
Premium: corporate, medieval, tropical
"""
import random


GENRES: list[dict] = [
    {
        "key":     "victorian_gothic",
        "premium": False,
        "genre":   "Victorian gothic",
        "era":     "1880s",
        "settings": [
            "a fog-shrouded English manor on the moors",
            "an exclusive London gentlemen's club",
            "a crumbling estate near the Scottish Highlands",
            "a grand Victorian townhouse on the edge of the city",
        ],
        "murder_methods": [
            "arsenic poisoning disguised in a nightly tonic",
            "a staged carriage accident on the estate grounds",
            "suffocation with a chloroform-soaked cloth",
            "a lethal dose of laudanum added to evening tea",
        ],
        "clue_flavour":       "telegrams, wax-sealed letters, gas lamps, servants' gossip, medical journals",
        "relationship_terms": ["lord", "lady", "butler", "governess", "solicitor", "physician"],
    },
    {
        "key":     "noir_1920s",
        "premium": False,
        "genre":   "1920s noir",
        "era":     "1920s",
        "settings": [
            "a smoky Chicago speakeasy behind a laundry front",
            "a luxury ocean liner mid-Atlantic crossing",
            "a Shanghai hotel during monsoon season",
            "a New Orleans jazz club on Bourbon Street",
        ],
        "murder_methods": [
            "a single .38 calibre bullet fired at close range",
            "cyanide dissolved in a glass of bootleg whiskey",
            "strangulation with a silk scarf",
            "a 'fall' from the hotel's top-floor balcony",
        ],
        "clue_flavour":       "matchbooks, cigarette stubs, telegrams, cash ledgers, jazz records, black-market receipts",
        "relationship_terms": ["detective", "dame", "bootlegger", "journalist", "senator", "mob boss"],
    },
    {
        "key":     "corporate",
        "premium": True,
        "genre":   "modern corporate thriller",
        "era":     "present day",
        "settings": [
            "a glass-and-steel tech startup in San Francisco",
            "a hedge fund's 40th-floor Manhattan office",
            "a pharmaceutical company's research campus",
            "a luxury private members' club in London",
        ],
        "murder_methods": [
            "a deliberately misconfigured insulin pump",
            "aconitine toxin in a protein shake",
            "a staged suicide with a forged note",
            "brake fluid drained from a company vehicle",
        ],
        "clue_flavour":       "Slack messages, CCTV logs, access card records, financial statements, deleted emails, server logs",
        "relationship_terms": ["CEO", "CFO", "senior partner", "board member", "whistleblower", "private equity investor"],
    },
    {
        "key":     "medieval",
        "premium": True,
        "genre":   "medieval mystery",
        "era":     "1340s",
        "settings": [
            "a fortified castle during a noble gathering",
            "a Benedictine monastery in the French countryside",
            "a prosperous merchant quarter of a walled city",
            "a royal court during a diplomatic summit",
        ],
        "murder_methods": [
            "hemlock mixed into the communal wine",
            "a crossbow bolt fired through a chapel window",
            "nightshade berries crushed into a feast dish",
            "a staged drowning in the castle's ornamental pond",
        ],
        "clue_flavour":       "wax seals, monks' journals, heraldic markings, blacksmith records, overheard confessions, blood on stone",
        "relationship_terms": ["knight", "noble", "abbot", "merchant", "herald", "court physician"],
    },
    {
        "key":     "tropical",
        "premium": True,
        "genre":   "tropical island",
        "era":     "present day",
        "settings": [
            "an ultra-exclusive private island resort",
            "a billionaire's superyacht anchored off the coast",
            "a remote research station on an uncharted atoll",
            "a luxury eco-lodge cut off by a tropical storm",
        ],
        "murder_methods": [
            "a rare reef toxin injected via a repurposed syringe",
            "a modified scuba regulator causing oxygen deprivation",
            "blunt force trauma disguised as a diving accident",
            "a sedative-laced cocktail followed by drowning",
        ],
        "clue_flavour":       "dive logs, satellite phone records, guest manifests, tide charts, resort CCTV, sunscreen-smeared fingerprints",
        "relationship_terms": ["resort owner", "marine biologist", "tech mogul", "celebrity", "security chief", "private chef"],
    },
]

# Displayed in the lobby Select menu — order matters for UX
GENRE_MENU: list[dict] = [
    {"key": "random",          "label": "Random — Surprise Me!",  "emoji": "🎲", "description": "A different era every game",             "premium": False},
    {"key": "victorian_gothic","label": "Victorian Gothic",        "emoji": "🏚️", "description": "1880s manor mystery",                   "premium": False},
    {"key": "noir_1920s",      "label": "1920s Noir",              "emoji": "🌆", "description": "Speakeasies and shadows",                "premium": False},
    {"key": "corporate",       "label": "Corporate Thriller",      "emoji": "🏢", "description": "Silicon Valley secrets",                 "premium": True},
    {"key": "medieval",        "label": "Medieval Mystery",        "emoji": "⚔️", "description": "Castles and conspiracies",               "premium": True},
    {"key": "tropical",        "label": "Tropical Island",         "emoji": "🌴", "description": "Paradise with a dark secret",            "premium": True},
]


def _build_genre_context(genre: dict) -> dict:
    return {
        "genre":              genre["genre"],
        "era":                genre["era"],
        "venue":              random.choice(genre["settings"]),
        "murder_method_hint": random.choice(genre["murder_methods"]),
        "clue_flavour":       genre["clue_flavour"],
    }


def pick_random_genre(premium_allowed: bool = True) -> dict:
    """Pick a random genre. Pass premium_allowed=False to restrict to free genres only."""
    pool  = GENRES if premium_allowed else [g for g in GENRES if not g["premium"]]
    return _build_genre_context(random.choice(pool))


def get_genre_by_key(key: str, premium_allowed: bool = True) -> dict:
    """Return a randomised genre context for the given key.
    Falls back to a random (tier-appropriate) genre if the key is unknown.
    """
    if key == "random":
        return pick_random_genre(premium_allowed=premium_allowed)
    genre_data = next((g for g in GENRES if g["key"] == key), None)
    if genre_data is None:
        return pick_random_genre(premium_allowed=premium_allowed)
    return _build_genre_context(genre_data)


def genre_display_name(key: str) -> str:
    """Human-readable name for a genre key, used in embeds."""
    entry = next((g for g in GENRE_MENU if g["key"] == key), None)
    if entry is None:
        return "Random"
    prefix = "⭐ " if entry["premium"] else ""
    return f"{entry['emoji']}  {prefix}{entry['label']}"
