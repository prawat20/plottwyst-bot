from __future__ import annotations
"""
Pre-generated sample cases for local testing.

Set TEST_MODE=true in .env to use these instead of calling Gemini.
Each case is a fully validated dict matching the schema the game engine expects.
"""
import random

SAMPLE_CASES: list[dict] = [

    # ── Case 1: Victorian Gothic ─────────────────────────────────────────────
    {
        "setting": {
            "genre":      "Victorian gothic",
            "era":        "1880s",
            "venue":      "Ashford Manor",
            "atmosphere": (
                "A bitter November fog has swallowed the moors entirely, leaving Ashford Manor "
                "an island of candlelight in the dark. Lord Edmund Ashford is found slumped at "
                "his writing desk just after ten o'clock, a toppled tonic glass staining the "
                "Persian rug beneath him. The household physician is already on the premises."
            ),
        },
        "victim": {
            "name":       "Lord Edmund Ashford",
            "gender":     "M",
            "background": (
                "Lord of Ashford Manor and controlling shareholder of the Ashford & Sons "
                "shipping concern. Known for meticulous record-keeping and an appetite "
                "for uncovering financial impropriety."
            ),
            "secrets": (
                "He had recently discovered that one of his inner circle had committed fraud "
                "in the city of Exeter and was preparing to go to the constable on Friday."
            ),
        },
        "twist": (
            "The victim had been receiving small doses of poison for three weeks prior — "
            "the fatal dose tonight was merely the last in a carefully measured series."
        ),
        "murderer":    "Dr. Victor Crane",
        "red_herring": "Lady Helena Cross",
        "suspects": [
            {
                "name":         "Dr. Victor Crane",
                "gender":       "M",
                "relation":     "Personal physician to Lord Ashford for seven years",
                "motive":       "Lord Ashford had discovered Crane forged death certificates in Exeter to claim fraudulent life insurance payments, and threatened to expose him",
                "trait":        "Methodical and precise",
                "last_seen":    "Private Study",
                "alibi":        "I attended to His Lordship's constitution as I do every Tuesday evening. I administered his tonic, found him in good spirits, and departed by half past nine. Whatever happened after is entirely beyond my knowledge.",
                "is_murderer":   True,
                "is_red_herring": False,
            },
            {
                "name":         "Lady Helena Cross",
                "gender":       "F",
                "relation":     "Former romantic interest of Lord Ashford, now a distant acquaintance",
                "motive":       "Lord Ashford broke off their engagement fifteen years ago and married another, leaving Lady Helena in considerable financial hardship",
                "trait":        "Composed but watchful",
                "last_seen":    "Private Study",
                "alibi":        "Edmund invited me to discuss a private financial matter — he owed me a debt of honour from years past. We spoke briefly and I retired to the east sitting room before nine. I heard nothing unusual.",
                "is_murderer":   False,
                "is_red_herring": True,
            },
            {
                "name":         "Charles Ashford",
                "gender":       "M",
                "relation":     "Younger brother and sole heir to the Ashford estate",
                "motive":       "Stands to inherit the entire estate and shipping concern upon Edmund's death",
                "trait":        "Impulsive and easily agitated",
                "last_seen":    "Billiards Room",
                "alibi":        "I spent the entire evening at billiards with Pendleton — ask him. Edmund and I had our differences but I am not a murderer. This is outrageous.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
            {
                "name":         "Arthur Pendleton",
                "gender":       "M",
                "relation":     "Family solicitor managing the Ashford estate accounts",
                "motive":       "Lord Ashford had begun auditing the estate accounts and suspected Pendleton of redirecting small sums over several years",
                "trait":        "Nervously deferential",
                "last_seen":    "Billiards Room",
                "alibi":        "Charles and I played billiards from seven until the commotion started. I did not leave the room once. I am happy to swear to it.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
            {
                "name":         "Margaret Doyle",
                "gender":       "F",
                "relation":     "Head housekeeper, employed at Ashford Manor for twenty-two years",
                "motive":       "Lord Ashford had recently told her she would be retired at year's end, ending her only source of income and accommodation",
                "trait":        "Fiercely loyal but quietly resentful",
                "last_seen":    "Servants' Quarters",
                "alibi":        "I was below stairs the whole of the evening overseeing supper preparations and the clearing up after. Cook and two maids can confirm it. I would never harm His Lordship.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
            {
                "name":         "Eliza Voss",
                "gender":       "F",
                "relation":     "Governess to Lord Ashford's two young daughters",
                "motive":       "Lord Ashford had begun to suspect her credentials were forged and had written to her supposed alma mater for confirmation",
                "trait":        "Quietly intelligent, rarely volunteers information",
                "last_seen":    "Nursery",
                "alibi":        "The children were restless and I did not leave the nursery all evening. I read to them until they slept at half past eight and remained there until the household was roused.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
        ],
        "clues": {
            "opening": [
                {
                    "type": "physical",
                    "text": "Lord Ashford's nightly tonic glass was found overturned on the desk. A faint bitter residue coats the interior — the tonic itself is known to be sweet.",
                },
                {
                    "type": "timeline",
                    "text": "The parlour clock stopped at 10:04 PM when it was knocked from the mantel. The household physician signed the visitors' ledger at 9:47 PM.",
                },
                {
                    "type": "testimonial",
                    "text": "The parlour maid reports hearing a hushed but heated exchange from behind the closed door of the Private Study shortly before ten — two voices, one of them His Lordship's.",
                },
            ],
            "round_1": {
                "type": "forensic",
                "text": "A preliminary analysis of the tonic residue confirms the presence of arsenious oxide at a concentration far exceeding any medicinal application. Furthermore, traces suggest the compound was introduced gradually over several weeks, not in a single dose.",
            },
            "round_2": {
                "type": "documentary",
                "text": "A letter discovered beneath the blotter on Lord Ashford's desk, in his own hand: 'Crane — I know what transpired in Exeter. You have until Friday to present yourself to the constable, or I shall do it for you. — E.A.'",
            },
            "round_3": {
                "type": "testimonial",
                "text": "The coachman states that when Dr. Crane arrived at 9:40 PM he carried a small black leather case that was not his customary medical bag. When Crane departed just after ten, the case was no longer with him.",
            },
            "round_4": {
                "type": "physical",
                "text": "A phial of arsenious oxide wrapped in a linen handkerchief embroidered with the initials 'V.C.' was discovered by constables wedged behind a loose brick in the lower shelf of Dr. Crane's consulting room cupboard.",
            },
        },
        "solution": (
            "Dr. Victor Crane poisoned Lord Ashford by lacing his nightly tonic with arsenious oxide, "
            "administering small doses over three weeks before delivering the fatal quantity on the night "
            "of his final visit. His motive was self-preservation: Lord Ashford had uncovered Crane's "
            "fraudulent death-certificate scheme in Exeter and confronted him by letter. The phial bearing "
            "Crane's initials, the threatening letter in the bureau, the coachman's testimony about the "
            "unaccounted case, and the forensic confirmation of long-term arsenic exposure together form "
            "an airtight case against the physician."
        ),
        "_genre_ctx": {
            "genre":              "Victorian gothic",
            "era":                "1880s",
            "venue":              "Ashford Manor",
            "murder_method_hint": "arsenic poisoning disguised in a nightly tonic",
            "clue_flavour":       "telegrams, wax-sealed letters, gas lamps, servants' gossip, medical journals",
        },
        "clue_pool": [],   # populated at load time
    },

    # ── Case 2: 1920s Noir ───────────────────────────────────────────────────
    {
        "setting": {
            "genre":      "1920s noir",
            "era":        "1920s",
            "venue":      "The Blue Orchid — a speakeasy beneath Calloway's Laundry, Chicago",
            "atmosphere": (
                "Rain hammers the alley entrance and cigarette smoke hangs low over the bar. "
                "Just after midnight, the piano stops mid-song. Frank 'Lucky' Malone, the club's "
                "owner, is found face-down in his private booth — a single glass of rye at his "
                "elbow, a small red mark on the side of his neck."
            ),
        },
        "victim": {
            "name":       "Frank 'Lucky' Malone",
            "gender":     "M",
            "background": (
                "Owner of The Blue Orchid and a key distributor in the North Side bootlegging "
                "network. Charming on the surface, ruthless beneath — he kept two sets of books "
                "and knew exactly where every dollar went."
            ),
            "secrets": (
                "Malone had been quietly skimming from the North Side syndicate for eighteen months "
                "and was planning to disappear to Havana with the funds within the week."
            ),
        },
        "twist": (
            "The victim's private booth had been wiretapped — someone in the club had been "
            "feeding information to a rival syndicate for months, and Malone had just found out who."
        ),
        "murderer":    "Rose Calloway",
        "red_herring": "Tommy 'Two-Fingers' Ricci",
        "suspects": [
            {
                "name":         "Rose Calloway",
                "gender":       "F",
                "relation":     "Club bookkeeper and Malone's most trusted financial confidante",
                "motive":       "Malone discovered Rose had been feeding the rival Capone outfit with syndicate information via the wiretap, and told her she had until sunrise to leave Chicago or he'd have her killed",
                "trait":        "Ice-cool under pressure, speaks only when necessary",
                "last_seen":    "Back Office",
                "alibi":        "I was in the back office balancing the week's ledgers all night. The door was open — any of the bar staff could have seen me at my desk. I barely knew Frank was in his booth.",
                "is_murderer":   True,
                "is_red_herring": False,
            },
            {
                "name":         "Tommy 'Two-Fingers' Ricci",
                "gender":       "M",
                "relation":     "Head of security and Malone's personal enforcer",
                "motive":       "Malone had recently cut Tommy's cut of the distribution profits in half, and Tommy had been heard threatening to 'balance the books himself'",
                "trait":        "Hot-tempered, physically imposing",
                "last_seen":    "Back Office",
                "alibi":        "I was posted outside the back office all night keeping an eye on the cash room. Ask Sal — he was with me until at least half past twelve.",
                "is_murderer":   False,
                "is_red_herring": True,
            },
            {
                "name":         "Sal Benedetto",
                "gender":       "M",
                "relation":     "Bar manager and logistics coordinator for the bootleg deliveries",
                "motive":       "Malone had accused Sal of watering down the spirits and threatened to expose him to the syndicate",
                "trait":        "Jumpy and eager to please",
                "last_seen":    "Main Bar",
                "alibi":        "I was behind the bar the whole shift. Fifty people can put me there. I didn't go near Lucky's booth all night, I swear on my mother.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
            {
                "name":         "Vera Lake",
                "gender":       "F",
                "relation":     "The club's headline singer and Malone's on-again-off-again companion",
                "motive":       "Malone had told Vera he was done with her and planned to replace her with a younger act, ending both her income and her protection",
                "trait":        "Dramatically emotional, prone to outbursts",
                "last_seen":    "Dressing Room",
                "alibi":        "I finished my second set at midnight and went straight to my dressing room. I cried my eyes out over that rat — ask my dresser. I didn't touch him.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
            {
                "name":         "Detective Ray Kowalski",
                "gender":       "M",
                "relation":     "Chicago PD detective on Malone's payroll for protection",
                "motive":       "Malone had recently stopped the payments and threatened to expose Kowalski's arrangement to Internal Affairs",
                "trait":        "Calculating, always scanning the room",
                "last_seen":    "Main Bar",
                "alibi":        "I was at the bar nursing a Scotch from eleven until the body was found. I'm a police officer — you think I'd be stupid enough to kill a man in his own club?",
                "is_murderer":   False,
                "is_red_herring": False,
            },
            {
                "name":         "Mickey Doyle",
                "gender":       "M",
                "relation":     "Malone's personal driver and sometime errand-runner for the syndicate",
                "motive":       "Mickey had overheard Malone discussing plans to pin a recent warehouse theft on him as a fall guy",
                "trait":        "Nervous, talks too much when anxious",
                "last_seen":    "Main Bar",
                "alibi":        "I drove Mr. Malone here at ten, then sat at the bar waiting for him to need a ride. I never went near the back. I just drive the car, that's all I do.",
                "is_murderer":   False,
                "is_red_herring": False,
            },
        ],
        "clues": {
            "opening": [
                {
                    "type": "physical",
                    "text": "A small puncture mark, approximately two millimetres wide, was observed on the left side of the victim's neck — inconsistent with any natural cause of death.",
                },
                {
                    "type": "timeline",
                    "text": "The piano player confirms the music stopped abruptly at 12:08 AM when he heard something fall in the private booth. The last person seen entering the booth area before that was at 11:52 PM.",
                },
                {
                    "type": "testimonial",
                    "text": "Coat-check girl Dottie recalls a figure in a dark dress crossing from the direction of the back office toward the private booths at approximately ten minutes past midnight — moving quickly and not looking up.",
                },
            ],
            "round_1": {
                "type": "forensic",
                "text": "The coroner identifies the cause of death as cyanide poisoning administered by injection. The compound used — potassium cyanide in solution — requires both access to a chemistry source and the knowledge to prepare an injectable dose. It acts in under two minutes.",
            },
            "round_2": {
                "type": "documentary",
                "text": "A decoded ledger page found taped beneath the desk drawer in the back office shows two columns: one in Malone's shorthand, one in a different hand. The second column lists dates, names, and dollar amounts — all matching recent syndicate operations. The paper carries faint traces of a woman's hand cream.",
            },
            "round_3": {
                "type": "testimonial",
                "text": "Sal Benedetto, under pressure, admits he saw Rose Calloway leave the back office at 12:06 AM, cross the floor, and slip into the service corridor behind the private booths — an area she had no business being in. He said nothing earlier because he was scared.",
            },
            "round_4": {
                "type": "physical",
                "text": "A hollow hatpin with a glass vial still attached — containing residue consistent with cyanide solution — was found wedged beneath the cushion of the chair at the bookkeeper's desk in the back office, wrapped in a monogrammed handkerchief bearing the initials 'R.C.'",
            },
        },
        "solution": (
            "Rose Calloway killed Frank Malone with a cyanide-loaded hatpin slipped into his neck as she "
            "passed his booth just after midnight. Malone had discovered she was the club's wiretap leak — "
            "feeding intelligence to a rival outfit — and given her an ultimatum that would have meant her "
            "death at syndicate hands. Rose, a meticulous bookkeeper who had prepared the injectable dose "
            "in advance, chose to act first. The decoded ledger in her handwriting, the hatpin found at her "
            "desk, Sal's eyewitness account of her crossing to the booths, and the coroner's cyanide "
            "finding all point conclusively to Rose."
        ),
        "_genre_ctx": {
            "genre":              "1920s noir",
            "era":                "1920s",
            "venue":              "The Blue Orchid speakeasy, Chicago",
            "murder_method_hint": "cyanide dissolved in a glass of bootleg whiskey",
            "clue_flavour":       "matchbooks, cigarette stubs, telegrams, cash ledgers, jazz records, black-market receipts",
        },
        "clue_pool": [],   # populated at load time
    },

]


def load_sample_case() -> dict:
    """Pick a random sample case and populate the clue_pool."""
    case = random.choice(SAMPLE_CASES).copy()
    case["clue_pool"] = [
        case["clues"]["round_1"],
        case["clues"]["round_2"],
        case["clues"]["round_3"],
        case["clues"]["round_4"],
    ]
    return case
