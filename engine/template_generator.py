from __future__ import annotations
"""
Template-based case generator — zero AI, zero cost, effectively infinite stories.

How it works:
  Every element of a mystery (names, locations, methods, motives, clue text,
  alibi statements, solution narrative) is drawn from large randomised pools
  and assembled into a logically consistent case.

Combination space (conservative estimate):
  5 genres × 4 venues × 30 name combos × 6 motives × 5 methods ×
  5 twists × 5 clue chains × 6 trait × 6 location = 100,000+ unique games.

Players will not perceive repetition in normal play.
"""
import random
import string


# ── Name pools ───────────────────────────────────────────────────────────────

_FIRST_M = [
    "Arthur", "Edmund", "Victor", "Charles", "Henry", "Walter", "Roland",
    "Frank", "Tommy", "Sal", "Ray", "Mickey", "Dominic", "Leo", "Vince",
    "Marcus", "Julian", "Oliver", "Sebastian", "Dorian",
]
_FIRST_F = [
    "Eleanor", "Beatrice", "Constance", "Vivienne", "Harriet", "Adelaide",
    "Rose", "Vera", "Dottie", "Pearl", "Mabel", "Loretta", "Iris", "Clara",
    "Celeste", "Margot", "Isadora", "Edith", "Florence", "Lillian",
]
_LAST = [
    "Ashford", "Crane", "Weston", "Harlow", "Pendleton", "Voss", "Doyle",
    "Calloway", "Malone", "Ricci", "Benedetto", "Kowalski", "Lake", "Cross",
    "Sinclair", "Whitmore", "Blackwell", "Fairfax", "Morrow", "Sterling",
    "Hale", "Drake", "Finch", "Graves", "Marsh",
]

def _name(gender: str, exclude: list[str]) -> str:
    pool = _FIRST_M if gender == "M" else _FIRST_F
    used_lasts = {n.rsplit(" ", 1)[-1] for n in exclude if " " in n}
    avail_lasts = [l for l in _LAST if l not in used_lasts] or _LAST
    for _ in range(50):
        full = f"{random.choice(pool)} {random.choice(avail_lasts)}"
        if full not in exclude:
            return full
    return f"{random.choice(pool)} {random.choice(avail_lasts)}"


# ── Genre definitions ─────────────────────────────────────────────────────────

GENRES: dict[str, dict] = {

    "victorian": {
        "label":  "Victorian gothic",
        "era":    "1880s",
        "venues": [
            "Thornfield Manor",
            "Blackmoor Estate",
            "Ashworth Hall",
            "Ravenswood House",
        ],
        "atmosphere_templates": [
            "A bitter {season} fog has swallowed the moors, leaving {venue} an island of candlelight in the dark. {victim_name} is found slumped at their writing desk just after ten o'clock, a toppled glass staining the Persian rug beneath.",
            "Gas lamps flicker against the {season} chill inside {venue} as the household gathers for the evening. {victim_name} is discovered face-down in the library — the fire still burning, a letter half-written on the desk.",
        ],
        "seasons": ["winter", "autumn", "spring"],
        "locations": ["Private Study", "Library", "Drawing Room", "Cellar", "Guest Suite", "Conservatory"],
        "relations": {
            "M": ["personal physician", "younger brother", "family solicitor", "business partner", "rival collector", "estranged cousin"],
            "F": ["governess", "widowed sister", "housekeeper", "fiancée", "former companion", "niece"],
        },
        "motives": {
            "personal physician":   ["victim discovered the physician had been forging prescriptions to supply laudanum to black-market dealers", "victim had cut the physician from his will after a botched treatment"],
            "younger brother":      ["stands to inherit the entire estate", "victim had discovered he had secretly sold family heirlooms"],
            "family solicitor":     ["victim had begun an audit that would expose years of embezzlement", "victim had found a forged codicil in the estate papers"],
            "business partner":     ["victim was preparing to dissolve the partnership and expose the suspect's fraudulent accounts", "victim had discovered the suspect was supplying stolen goods through their joint enterprise"],
            "rival collector":      ["victim had outbid them for a priceless artefact and was about to publish proof of the suspect's forged provenance", "a long-standing feud over the ownership of a contested estate"],
            "estranged cousin":     ["victim had blocked their inheritance claim through a contested will", "victim held documents proving the suspect's illegitimacy"],
            "governess":            ["victim had discovered her credentials were forged and written to her supposed institution for confirmation", "victim had witnessed her reading private correspondence and threatened dismissal"],
            "widowed sister":       ["victim had contested their late husband's estate, leaving her destitute", "victim had cut off her allowance after a family dispute"],
            "housekeeper":          ["victim had announced her retirement after twenty years of service, ending her only income and accommodation", "victim had accused her of stealing household silver"],
            "fiancée":              ["victim had broken off the engagement, leaving her socially ruined", "victim had discovered she was already secretly married"],
            "former companion":     ["victim had dismissed her without a reference after she refused to conceal the victim's own misconduct", "victim held letters that would expose a secret the suspect could not afford revealed"],
            "niece":                ["victim had changed the will to exclude her in favour of a charity", "victim had discovered she had been forging the victim's signature on cheques"],
        },
        "methods": [
            {"name": "arsenic poisoning", "instrument": "the nightly tonic", "residue": "arsenious compound", "cause": "arsenic poisoning", "preparation": "dissolved arsenious oxide into the tonic over several weeks"},
            {"name": "laudanum overdose", "instrument": "the evening tea", "residue": "opiate residue", "cause": "opiate overdose", "preparation": "introduced a concentrated laudanum solution into the tea service"},
            {"name": "strangulation", "instrument": "a silk cravat", "residue": "ligature marks", "cause": "asphyxiation", "preparation": "waited until the household retired before striking"},
            {"name": "blunt force trauma", "instrument": "a marble bookend", "residue": "traces of marble dust", "cause": "blunt force trauma to the skull", "preparation": "removed the bookend from the study shelf earlier that evening"},
        ],
        "twists": [
            "The victim had been receiving small doses of the poison for three weeks — tonight was merely the final, fatal dose.",
            "The victim had written a letter naming their killer but sealed it for delivery at a future date — it was intercepted.",
            "Two suspects were seen near the scene — one covered for the other, but their stories do not align on the timing.",
            "The victim was not killed where they were found — the body was moved after death to implicate someone else.",
            "The murder weapon was carefully cleaned and replaced in plain sight; only a residue trace betrays it.",
        ],
        "clue_chains": [
            {
                # ── Mastermind chain A ── red herring trail → pure synthesis (timing gap + professional object)
                "opening": [
                    ("physical",    "A calling card belonging to {red_herring_name} was found on the floor of the {murder_location}, as though dropped in haste during a hurried departure."),
                    ("timeline",    "The butler confirms he admitted {red_herring_name} to the house at {time_arrived} and heard raised voices shortly after from the direction of the {murder_location} — before the household fell quiet again."),
                    ("testimonial", "A housemaid states she observed {red_herring_name} leaving the {murder_location} with a flushed, agitated expression approximately ten minutes before the victim was discovered."),
                ],
                "round_1": ("forensic",     "The coroner confirms the cause of death as {cause}. The method required either specialist knowledge or a close personal acquaintance of the victim — someone whose presence would not have alarmed them. {red_herring_name}'s known background and prior access to the household make this a natural point of focus."),
                "round_2": ("documentary",  "A letter discovered behind the loose panel of the victim's writing desk — in a hand that matches samples of {red_herring_name}'s correspondence — reads: 'This cannot be allowed to continue. You have left me no choice.' It is undated, but the ink is recent."),
                # Constraint clues — no suspect named; players must cross-reference profiles
                "round_3": ("testimonial",  "A reconstruction of the evening narrows the window of opportunity to no more than twelve minutes. A careful review of staff accounts, the visitors' ledger, and the household's routine reveals precisely one person whose movements during this window cannot be independently verified by any witness present that night."),
                "round_4": ("physical",     "A faint impression preserved in the dust of the writing desk matches the base of a small hinged case — not a household item. Objects of this type are carried as a matter of professional habit by those in specific occupations, not as personal choice. Among all six suspects, exactly one holds a position that would account for such an object."),
            },
            {
                # ── Mastermind chain B ── deeper plant → pure synthesis (insider knowledge + material trace)
                "opening": [
                    ("physical",    "A torn fragment of fabric — matching the colour and weave of {red_herring_name}'s evening coat — was found clutched in the victim's right hand, as though torn free in a struggle."),
                    ("timeline",    "Two witnesses independently confirm they observed {red_herring_name} in the corridor outside the {murder_location} just before {time_of_death}, speaking in low, tense tones before moving away."),
                    ("testimonial", "A senior member of the household reports that {red_herring_name} and the victim quarrelled bitterly over supper — {red_herring_name} left the table early and was not seen in the drawing room for the rest of the evening."),
                ],
                "round_1": ("forensic",     "The residue recovered from the scene is confirmed as {residue} at a concentration consistent with {cause}. Whoever introduced it had both the access and the foreknowledge to do so — characteristics that have, thus far, pointed investigators toward {red_herring_name}."),
                "round_2": ("documentary",  "The victim's private accounts reveal a series of payments made to {red_herring_name} over the preceding months, each one annotated in the margin with the single word 'silence'. The final entry is dated three days before the murder."),
                # Constraint clues — no suspect named; players must cross-reference profiles
                "round_3": ("testimonial",  "It becomes clear the killer had prior knowledge of which preparation the victim took each evening — information recorded only in private correspondence, never shared beyond the victim's innermost circle of trust. When each suspect's established relationship with the victim is examined against this fact, the number who could have possessed this knowledge is very small."),
                "round_4": ("physical",     "A transfer of material is identified on the interior handle of the {murder_location} door — a substance not native to that room, traceable to an environment associated with a specific occupation or domestic station. Each suspect's daily surroundings, as established from their own statements, can be matched against this substance. Only one match holds."),
            },
            {
                # ── Innocent Mention chain ── murderer visually placed elsewhere → alibi dismantled → constraint synthesis
                "opening": [
                    ("physical",    "A calling card bearing {red_herring_name}'s name was found pressed beneath the victim's forearm at the desk — positioned as though placed deliberately within reach."),
                    ("timeline",    "The butler confirms {red_herring_name} was admitted to the house at {time_arrived} and was observed moving toward the {murder_location} shortly after entry, without explanation for the detour."),
                    ("testimonial", "A parlour maid states she passed {murderer_name} in the gallery corridor at the moment the household last heard the victim alive — an account that, on its face, places them well clear of the {murder_location} at the critical time."),
                ],
                "round_1": ("forensic",     "The coroner confirms cause of death as {cause}. The method required either specialist knowledge or a close personal acquaintance of the victim — someone whose presence would not have alarmed them. Attention continues to fall on {red_herring_name}, whose background fits the profile and whose movements remain insufficiently explained."),
                "round_2": ("documentary",  "A sealed letter in the victim's locked correspondence box — addressed to the family solicitor and dated two days prior — reads: 'Should anything befall me, look first to {red_herring_name}. They know precisely what I know.' The letter had not been sent."),
                # round_3 dismantles the clearing testimony from opening[2] without naming the murderer
                "round_3": ("testimonial",  "The parlour maid's account is revisited under closer examination. She concedes the gallery was unlit save for a single gas bracket that evening, and that she identified the figure by their coat rather than their face. The coat she describes — a dark wool with a double row of brass buttons — does not correspond to any garment that can be attributed to the person she named. No other witness can independently confirm who was in that corridor at that hour."),
                "round_4": ("physical",     "A faint impression preserved in the dust on the writing desk corresponds to the base of a small hinged case — not a household object. Such items are carried as a matter of professional habit by individuals in specific occupations, not as personal choice. Among all six suspects, exactly one holds a position that would account for the routine presence of such a case."),
                "solution_templates": [
                    "The murderer was {murderer_name} — not {red_herring_name}. The opening evidence established what appeared to be an alibi: a maid placed {murderer_name} in the gallery at the critical moment. Round 3 dismantled it — the witness admitted she identified only a coat in an unlit corridor, and the coat she described does not exist among {murderer_name}'s belongings. With the alibi gone, the professional object's impression at the desk sealed the case: only {murderer_name}'s occupation explains its presence there. Motive: {motive}. Method: {instrument}.",
                ],
            },
        ],
        "alibi_templates": {
            "murderer":    ["I attended to {victim_name} as is my custom and left before {time_of_death}. Whatever occurred after my departure is entirely beyond my knowledge.", "I was in the {alibi_location} the entire evening. Several members of the household can confirm it, if you care to ask them."],
            "red_herring": ["I had private business with {victim_name} earlier in the evening, yes — but we parted on civil terms and I retired to the {alibi_location} long before anything untoward occurred.", "I was near the {murder_location} at one point, I will not deny it — but I heard nothing and saw nothing of consequence."],
            "innocent":    [
                "I was in the {alibi_location} the whole of the evening. You may verify it with anyone present.",
                "I had no quarrel with {victim_name} that evening. We spoke briefly at supper and I did not see them again.",
                "I spent the evening with other members of the household in the {alibi_location}. I was not near the {murder_location} at any point.",
                "My movements that evening are entirely accounted for. I was in the {alibi_location} from dinner onwards and did not leave until after the alarm was raised.",
            ],
        },
        "solution_templates": [
            "The murderer was {murderer_name} — not {red_herring_name}, who the early evidence framed so carefully. Driven by {motive}, {murderer_name} introduced {residue} via {instrument}. The case breaks when two facts are read together: the twelve-minute gap in which only one person's movements are unverified, and the professional object whose impression was found at the desk — both fitting {murderer_name}'s position and no one else's simultaneously.",
            "It was {murderer_name} — not {red_herring_name}. The proof lies in synthesis, not accusation: the constraint of prior knowledge of the victim's private routine narrows the circle sharply, and the material trace on the {murder_location} door matches a single occupational environment. Only {murderer_name}'s profile satisfies both. Motive: {motive}. Method: {instrument} carrying {residue}.",
        ],
    },

    "noir": {
        "label":  "1920s noir",
        "era":    "1920s",
        "venues": [
            "The Blue Orchid — a speakeasy beneath Calloway's Laundry, Chicago",
            "The Silver Dagger Club, New Orleans",
            "The Pearl of the Orient Hotel, Shanghai",
            "The Midnight Lounge, Atlantic City",
        ],
        "atmosphere_templates": [
            "Rain hammers the alley entrance and cigarette smoke hangs low over the bar at {venue}. Just after midnight, {victim_name} is found face-down in their private booth — a glass of rye at their elbow and a small puncture mark on the side of the neck.",
            "The jazz stops mid-number inside {venue}. {victim_name}, the establishment's feared owner, is discovered slumped in their private office — the safe cracked open, the body still warm.",
        ],
        "seasons": ["winter", "autumn", "a rainy spring"],
        "locations": ["Back Office", "Private Booth", "Storage Room", "Rooftop", "Service Corridor", "Kitchen"],
        "relations": {
            "M": ["head of security", "bar manager", "club musician", "police contact on the payroll", "rival syndicate representative", "personal driver"],
            "F": ["bookkeeper", "headline singer", "hat-check girl", "journalist sniffing around the club", "wife of the victim", "silent business partner"],
        },
        "motives": {
            "head of security":                 ["victim had cut their share of the operation in half and threatened to replace them entirely", "victim had discovered they were skimming cash from the nightly take"],
            "bar manager":                      ["victim had accused them of watering down the spirits and threatened exposure to the syndicate", "victim had discovered they were selling information to a rival outfit"],
            "club musician":                    ["victim had refused to release them from an exploitative contract and threatened to blacklist them across the city", "victim had been extorting them over a past criminal record"],
            "police contact on the payroll":    ["victim had stopped protection payments and threatened to expose the arrangement to Internal Affairs", "victim possessed evidence of a crime the officer desperately needed buried"],
            "rival syndicate representative":   ["victim had recently stolen a distribution territory that belonged to the rival syndicate", "victim was planning to testify against the rival syndicate's leadership"],
            "personal driver":                  ["victim was planning to pin a warehouse robbery on them as a fall guy to appease the syndicate", "victim had discovered they were secretly working for a rival outfit"],
            "bookkeeper":                       ["victim had discovered they were feeding financial intelligence to a rival syndicate and gave them an ultimatum", "victim was planning to disappear with the funds the suspect had been carefully embezzling"],
            "headline singer":                  ["victim had cancelled their contract and planned to replace them with a younger act, ending both income and protection", "victim was blackmailing them over a secret from their past"],
            "hat-check girl":                   ["victim had witnessed them stealing from the coat-check proceeds and threatened to report it to the syndicate", "victim had rejected their advances in a manner that became a public humiliation"],
            "journalist sniffing around":       ["victim had discovered the journalist's identity as an undercover federal informant", "victim had threatened to expose the journalist's own criminal connections"],
            "wife of the victim":               ["victim was planning to disappear to another country with a mistress, leaving the suspect with nothing", "victim had been systematically draining a jointly held account without the suspect's knowledge"],
            "silent business partner":          ["victim was planning to dissolve the partnership and cut the suspect out entirely, despite equal investment", "victim had discovered the suspect's share of the business had been acquired with stolen syndicate money"],
        },
        "methods": [
            {"name": "cyanide injection", "instrument": "a hollow hatpin", "residue": "potassium cyanide solution", "cause": "cyanide poisoning by injection", "preparation": "prepared an injectable cyanide solution and concealed it in a hatpin worn as jewellery"},
            {"name": "poisoned drink", "instrument": "a glass of rye whiskey", "residue": "cyanide compound", "cause": "cyanide poisoning", "preparation": "slipped a lethal dose of cyanide into the victim's personal bottle behind the bar"},
            {"name": "shooting", "instrument": "a .38 revolver with a makeshift suppressor", "residue": "gunpowder residue", "cause": "a single gunshot wound", "preparation": "obtained a revolver through black-market channels two weeks prior"},
            {"name": "strangulation", "instrument": "a garrotte fashioned from piano wire", "residue": "ligature marks and piano wire fibres", "cause": "asphyxiation", "preparation": "cut a length of wire from the club piano during the afternoon and concealed it on their person"},
        ],
        "twists": [
            "The victim's private booth had been wiretapped — someone in the club had been feeding intelligence to a rival syndicate, and the victim had just found out who.",
            "The victim was planning to disappear to another country within the week, taking the syndicate's money with them — several people knew this and had motive to act first.",
            "A second person entered the room after the murder and disturbed the scene before leaving — their identity complicates the timeline.",
            "The murder weapon was planted on the most obvious suspect by the real killer, who anticipated investigators would stop looking after an arrest.",
            "The victim staged their own murder once before to escape debts — some suspects believed this was another fake, which delayed the alarm.",
        ],
        "clue_chains": [
            {
                # ── Mastermind chain A ── red herring frame → pure synthesis (timing gap + specialist supply)
                "opening": [
                    ("physical",    "A monogrammed handkerchief bearing {red_herring_name}'s known initials was found balled beneath the victim's table — stained with a substance that is not whiskey."),
                    ("timeline",    "The hat-check girl places {red_herring_name} moving toward the {murder_location} at approximately {time_arrived} and confirms they did not return through the main entrance that she could see."),
                    ("testimonial", "Two musicians seated near the stage independently recall seeing {red_herring_name} in close, heated conversation with the victim earlier that evening — voices low, gestures sharp, the kind of exchange that ends badly."),
                ],
                "round_1": ("forensic",     "The coroner confirms cause of death as {cause}. The method points to someone who had access to the victim's private area and knew their routine — a regular, or someone the victim trusted enough not to question. {red_herring_name} fits both criteria."),
                "round_2": ("documentary",  "A note recovered from inside the victim's breast pocket reads: 'I know what you did, {red_herring_name}. Thursday. Come alone.' The handwriting is the victim's own. The note was never sent."),
                # Constraint clues — no suspect named; players must cross-reference profiles
                "round_3": ("testimonial",  "The coroner places time of death within a window of eight minutes. A reconstruction of the club's movements that night — barback logs, service orders, stage cues, door counts — places every suspect except one in a traceable location during that period. One person's whereabouts during those eight minutes cannot be corroborated by any independent source."),
                "round_4": ("physical",     "The compound identified in the laboratory analysis is not obtainable through general channels — it requires either a registered account with a specialist supplier or a direct professional contact in a restricted field. An inquiry to the relevant supplier networks returns a single account consistent with the professional background of one of the six suspects."),
            },
            {
                # ── Mastermind chain B ── deeper plant → pure synthesis (insider knowledge + skill fluency)
                "opening": [
                    ("physical",    "The victim's personal glass was found displaced from its usual spot, moved to the table where {red_herring_name} typically sits. A fresh smear of fingerprints marks the base."),
                    ("timeline",    "The barback confirms {red_herring_name} was unattended behind the bar for several minutes around {time_arrived} — the same window during which the victim's private bottle could have been accessed."),
                    ("testimonial", "A regular patron overheard {red_herring_name} on the telephone earlier that afternoon, saying: 'It has to be tonight. After tonight, it's done.' The patron thought nothing of it at the time."),
                ],
                "round_1": ("forensic",     "Laboratory analysis of the residue in the victim's glass confirms {residue} at a lethal concentration — introduced into the supply before serving. The quantity required precision and foreknowledge. Those with established access to the private stock are already under scrutiny."),
                "round_2": ("documentary",  "A safe-deposit slip found in {red_herring_name}'s coat pocket — for a box opened that same afternoon at a nearby bank — is the kind of box used to retrieve items kept well away from scrutiny. The timing aligns precisely with the murder window."),
                # Constraint clues — no suspect named; players must cross-reference profiles
                "round_3": ("testimonial",  "The killer knew the victim would be in the private booth alone at that specific hour — a fact not on any public schedule, accessible only to those who managed the victim's personal arrangements. When each suspect's established role and access to this information is examined, the number who could have known narrows to two. One of those two has a verified alibi for the window in question."),
                "round_4": ("physical",     "The method of delivery required handling the instrument with practiced fluency — the kind that comes from professional exposure, not improvisation. The specific skill involved is not broadly held. Among the six suspects, one has a professional background that would account for this familiarity. The others demonstrably do not."),
            },
            {
                # ── Innocent Mention chain ── bartender clears murderer → tab records crack alibi → specialist synthesis
                "opening": [
                    ("physical",    "A monogrammed handkerchief bearing {red_herring_name}'s known initials was found balled beneath the victim's table — damp with a substance that is not whiskey."),
                    ("timeline",    "The hat-check girl places {red_herring_name} moving toward the {murder_location} at approximately {time_arrived} and cannot account for where they went from there."),
                    ("testimonial", "The bartender states {murderer_name} was seated at the main bar during the entire window — visible, ordering drinks, making conversation with staff — an account that appears to place them squarely in the clear at the time of the murder."),
                ],
                "round_1": ("forensic",     "The coroner confirms cause of death as {cause}. The method required close access and prior knowledge of the victim's private area — the kind that points to a regular, or someone the victim trusted. Suspicion continues to cluster around {red_herring_name}, whose movements in the critical window remain unaccounted for."),
                "round_2": ("documentary",  "A note recovered from inside the victim's breast pocket, written in the victim's own hand, reads: 'I know what you did, {red_herring_name}. Thursday. Come alone.' The note was never sent. The implication is that someone else found it first."),
                # round_3 dismantles the bar alibi from opening[2] without naming the murderer
                "round_3": ("testimonial",  "The bar tab ledger for that evening is recovered from the register. The final logged order attributed to the seat in question was placed fourteen minutes before the estimated time of death — not during it. The bartender, pressed on the precise timing, concedes he cannot confirm whether the person remained at the bar throughout the critical window or had stepped away. No other staff member can corroborate an unbroken presence there during that period."),
                "round_4": ("physical",     "The compound identified in laboratory analysis is not obtainable through general channels — it requires either a registered account with a specialist supplier or a direct professional contact in a restricted field. An inquiry to the relevant supplier networks returns a single account consistent with the professional background of one of the six suspects."),
                "solution_templates": [
                    "The killer was {murderer_name} — not {red_herring_name}. The bartender's opening statement appeared to provide an airtight alibi: {murderer_name} at the bar throughout. Round 3 cracked it — the tab ledger placed the last order fourteen minutes before the murder, and the bartender could not confirm a continuous presence during the window. With the alibi gone, the specialist supply network sealed it: only one suspect's professional credentials account for access to {residue}. Motive: {motive}. Method: {instrument}.",
                ],
            },
        ],
        "alibi_templates": {
            "murderer":    ["I was at my station the entire night. Anyone on that floor can tell you — I never went near the booth.", "I had nothing to do with it. I was in the {alibi_location} all evening, minding my own business like always."],
            "red_herring": ["Sure, I was near the {murder_location} — I won't lie about that. But I didn't go in. I heard something, got spooked, and walked the other way.", "I had words with {victim_name} earlier. It wasn't pretty. But I didn't touch them after that."],
            "innocent":    [
                "I was behind the {alibi_location} the whole shift. Fifty people can put me there.",
                "I've got nothing to hide. I was nowhere near that part of the club.",
                "I clocked in at nine and didn't leave my station until the whole place was locked down. You can check with anyone.",
                "Ask anyone who was working that night. I was in the {alibi_location} the whole time. I don't get involved in that kind of business.",
            ],
        },
        "solution_templates": [
            "The killer was {murderer_name} — not {red_herring_name}. Two constraints, read together, close the case: first, only one person has an eight-minute gap unaccounted for in any independent record; second, the specialist supply network returns a single account matching one suspect's professional history. {murderer_name} satisfies both. Motive: {motive}. Method: {instrument} carrying {residue}.",
            "The case against {red_herring_name} was built on surface evidence. The real answer required synthesis. The killer had to know the victim's private schedule — narrowing the field — and had to possess the professional fluency to execute the method without improvisation. Only {murderer_name}'s role and background satisfy both constraints simultaneously. Motive: {motive}.",
        ],
    },

    "corporate": {
        "label":  "modern corporate thriller",
        "era":    "present day",
        "venues": [
            "Axiom Technologies — a glass-and-steel campus in San Francisco",
            "Meridian Capital — a hedge fund's fortieth-floor Manhattan office",
            "Vantage Pharma — a pharmaceutical research campus outside Boston",
            "Sterling & Cross — a private equity firm in the City of London",
        ],
        "atmosphere_templates": [
            "The office at {venue} is empty except for the hum of servers and the glow of monitor screens. {victim_name}, the firm's {victim_role}, is found slumped at their standing desk just after 11 PM — an access-card log shows the building locked down thirty minutes earlier.",
            "Security cameras at {venue} went offline at 22:47. When they resumed at 23:12, {victim_name} was already dead in the executive boardroom, a single window left slightly ajar.",
        ],
        "seasons": ["late autumn", "winter", "early spring"],
        "locations": ["Server Room", "CEO Office", "Conference Room B", "Underground Parking", "Break Room", "Roof Terrace"],
        "relations": {
            "M": ["co-founder and CTO", "senior analyst", "head of compliance", "external auditor", "board member", "IT administrator"],
            "F": ["chief operating officer", "head of legal", "personal assistant", "senior data scientist", "investor relations director", "whistleblower"],
        },
        "motives": {
            "co-founder and CTO":           ["victim was about to force them out of the company and strip their equity stake ahead of an IPO", "victim had discovered they had been selling source code to a competitor"],
            "senior analyst":               ["victim had taken credit for their work and was about to fire them to cover it up", "victim had discovered they were running a side fund using firm capital without authorisation"],
            "head of compliance":           ["victim had ordered them to sign off on filings they knew to be fraudulent, and they had secretly refused and filed a complaint", "victim was about to expose their own past regulatory violation at a previous firm"],
            "external auditor":             ["victim had discovered the auditor had been issuing clean opinions in exchange for private consultancy fees", "victim was about to blow open a conflict of interest that would end the auditor's career"],
            "board member":                 ["victim was about to present findings to the full board that would remove the suspect from their position", "victim had discovered the board member had been illegally shorting the company's stock"],
            "IT administrator":             ["victim had discovered they had been accessing executive communications without authorisation", "victim was the only person who could link them to a data breach they had orchestrated and sold"],
            "chief operating officer":      ["victim was planning to replace them with an external hire and had already signed the offer letter", "victim had discovered they had been redirecting vendor payments to a personal account"],
            "head of legal":                ["victim had found evidence they had been running a parallel legal practice in breach of their employment contract", "victim was about to waive attorney-client privilege in a way that would expose the suspect's own misconduct"],
            "personal assistant":           ["victim had been systematically taking credit for the suspect's work and threatened to terminate them if they spoke up", "victim possessed compromising personal information and had been using it as leverage"],
            "senior data scientist":        ["victim had stolen their proprietary model and was about to patent it under the firm's name", "victim had discovered they had been selling user data to third parties"],
            "investor relations director":  ["victim had discovered they had been leaking non-public information to selected investors in exchange for personal kickbacks", "victim was about to restate earnings in a way that would expose the suspect's inflated projections"],
            "whistleblower":                ["victim had discovered the suspect's identity as the internal source and was about to expose them to the board", "victim had gathered enough evidence to reverse the whistleblower's previous complaint and implicate them instead"],
        },
        "methods": [
            {"name": "aconitine poisoning", "instrument": "a protein shake in the office fridge", "residue": "aconitine alkaloid", "cause": "aconitine poisoning", "preparation": "introduced aconitine extract into the victim's labelled protein shake in the communal fridge"},
            {"name": "staged fall", "instrument": "a deliberately slicked floor on the roof terrace", "residue": "silicone lubricant residue", "cause": "blunt force trauma consistent with a fall from height", "preparation": "applied a fast-drying silicone spray to the roof terrace surface the same afternoon"},
            {"name": "insulin overdose", "instrument": "a repurposed insulin pen", "residue": "insulin compound", "cause": "fatal hypoglycaemia by injection", "preparation": "obtained a high-dose insulin pen through a medical contact and modified it for rapid administration"},
            {"name": "electrocution", "instrument": "a modified charging cable at the victim's workstation", "residue": "arc flash residue on the cable", "cause": "electrocution via a tampered power cable", "preparation": "accessed the victim's workstation after hours and modified the charging cable the previous evening"},
        ],
        "twists": [
            "The victim had set an automated email to send if they did not cancel it by midnight — it has now been delivered, but its contents have been deleted from the recipient's inbox.",
            "Security camera footage for the relevant window was deleted remotely using administrator credentials — the same credentials two people in the building share.",
            "The victim had secretly been cooperating with a regulatory investigation and their death is highly convenient for several parties beyond the obvious suspects.",
            "A second copy of the incriminating data the victim had gathered was backed up to an offsite server — the killer does not know this yet.",
            "The victim made a phone call lasting four minutes at {time_arrived} — the recipient of that call has not come forward.",
        ],
        "clue_chains": [
            {
                # ── Mastermind chain A ── badge logs frame red herring → pure synthesis (digital gap + specialist access)
                "opening": [
                    ("physical",    "The victim's door access log shows {red_herring_name}'s badge used to enter the {murder_location} at {time_arrived} — a visit {red_herring_name} had not disclosed in their initial statement to security."),
                    ("timeline",    "CCTV in the lobby confirms {red_herring_name} was still in the building at {time_of_death}, despite claiming to have left before ten. Their keycard shows no outbound badge until twelve minutes after the estimated time of death."),
                    ("testimonial", "A colleague working late reports seeing {red_herring_name} pacing the corridor outside the {murder_location} that evening, checking their phone at regular intervals — looking, in the colleague's words, 'like someone waiting for something to be over'."),
                ],
                "round_1": ("forensic",     "Toxicology confirms {residue} in the victim's system at a lethal concentration. Procurement of this compound requires specialist channels or a professional contact — {red_herring_name}'s background includes a prior role at a research-adjacent supplier, a detail now drawing closer scrutiny."),
                "round_2": ("documentary",  "Recovered email threads show {red_herring_name} and the victim in increasingly hostile exchange in the seventy-two hours before the murder. The final message from {red_herring_name} reads: 'You've made your choice. Don't expect me to sit still for it.' Sent at 21:04 on the evening of the murder."),
                # Constraint clues — no suspect named; players must cross-reference profiles
                "round_3": ("testimonial",  "Digital forensics confirms the security footage deletion was performed using a personal access token — not a shared credential — tied to a specific system role. Three individuals in the building that evening held this level of access. Two have verified digital activity during the relevant window. The third has no verifiable system footprint for a period of eleven minutes."),
                "round_4": ("physical",     "The compound used requires specialist handling knowledge — storage temperature, concentration thresholds, administration method — not available in general reference materials. A review of each suspect's professional background and documented training identifies which of the six would have encountered this information as a matter of course in their field. The field is narrow."),
            },
            {
                # ── Mastermind chain B ── digital frame → pure synthesis (physical key + prior contact)
                "opening": [
                    ("physical",    "The victim's workstation shows a permissions override logged under {red_herring_name}'s credentials at {time_arrived} — granting temporary access to files the victim had been restricting from the wider team."),
                    ("timeline",    "Building access records show {red_herring_name} badge-accessed the executive floor three times in the two hours before the victim's death — once more than they acknowledged in their initial account to investigators."),
                    ("testimonial", "Two separate colleagues report that {red_herring_name} had been visibly under strain in the days before the murder, and had made comments suggesting they felt they were 'out of options' with the victim."),
                ],
                "round_1": ("forensic",     "Digital forensics confirms files were remotely wiped from the victim's machine within minutes of death, using administrator-level credentials. Those credentials are shared between two people in the building — {red_herring_name} is one of them. The other has not yet been publicly named."),
                "round_2": ("documentary",  "A burner device recovered near the {murder_location} shows encrypted messages sent to {red_herring_name}'s personal number over the forty-eight hours prior to the murder. The sender is masked, but the device's MAC address traces to a purchase made within a few streets of {red_herring_name}'s home address."),
                # Constraint clues — no suspect named; players must cross-reference profiles
                "round_3": ("testimonial",  "Physical access to the victim's private office that evening required a key issued to a limited and documented set of individuals — not duplicated, not reported missing. Building administration records confirm which roles were issued this key and who was present in the building that evening. The intersection of these two lists is small."),
                "round_4": ("physical",     "The supplier from whom the compound was obtained maintains transaction records. The relevant purchase is linked to a professional account opened under credentials consistent with one specific field of expertise. When each suspect's documented professional background is matched against the account's registration details, the attribution is unambiguous."),
            },
            {
                # ── Innocent Mention chain ── automated badge log creates alibi → forensics voids it → credential synthesis
                "opening": [
                    ("physical",    "The victim's workstation shows a permissions override logged under {red_herring_name}'s credentials at {time_arrived} — a visit {red_herring_name} had not disclosed in their initial account to building security."),
                    ("timeline",    "Building access records show {red_herring_name} badged into the executive floor twice in the ninety minutes before the victim's death — once more than they had acknowledged."),
                    ("testimonial", "The lobby access log records {murderer_name}'s badge swiped at the ground-floor entrance at {time_of_death} — a timestamp that, on its face, appears to place them in the lobby and away from the executive floor at the precise moment the victim died."),
                ],
                "round_1": ("forensic",     "Toxicology confirms {residue} in the victim's system at a lethal concentration. Procurement of this compound requires specialist channels or a professional contact. {red_herring_name}'s background continues to attract scrutiny, given a prior role at a research-adjacent supplier on record."),
                "round_2": ("documentary",  "Recovered email threads show {red_herring_name} and the victim in increasingly hostile exchange in the seventy-two hours before the murder. The final message, sent at 21:04 on the evening of the murder, reads: 'You've made your choice. Don't expect me to sit still for it.'"),
                # round_3 voids the lobby badge alibi from opening[2] without naming the murderer
                "round_3": ("testimonial",  "IT forensics examines the lobby badge entry logged at {time_of_death}. Analysis confirms it was generated by an automated credential poll — a scheduled system routine that runs independently of any physical card swipe. Lobby camera footage for the same ninety-second window shows the entrance area was unoccupied. The entry in the access log does not correspond to a real-time human presence in the lobby."),
                "round_4": ("physical",     "The compound used requires specialist handling knowledge — storage conditions, concentration thresholds, and administration method not available in general reference materials. A review of each suspect's professional background and documented training identifies which of the six would have encountered this information as a matter of course in their field. The field is narrow, and the match is unambiguous."),
                "solution_templates": [
                    "The killer was {murderer_name} — not {red_herring_name}. The lobby badge log appeared to provide a clean alibi: a timestamp placing {murderer_name} away from the executive floor at the moment of death. Round 3 nullified it — IT forensics proved the entry was an automated credential poll, and lobby cameras confirmed the entrance was empty. With the alibi voided, the specialist knowledge constraint closed the case: only {murderer_name}'s professional background accounts for handling {residue} at the required concentration. Motive: {motive}. Method: {instrument}.",
                ],
            },
        ],
        "alibi_templates": {
            "murderer":    ["I left the building at the time my access log shows. Whatever happened after that had nothing to do with me.", "I was in a call until eight, then I packed up and left. I can share my calendar and my Uber receipt."],
            "red_herring": ["I was in {murder_location} earlier that evening, yes — we had words. But I left and went straight to {alibi_location}. Check my badge history.", "I don't deny we had a difficult conversation. But I walked away. That's what you do."],
            "innocent":    [
                "I was at {alibi_location} all evening. My access log, my laptop activity, and the security footage will all confirm that.",
                "I had no reason to be anywhere near that part of the building. You can verify my location.",
                "I was working late at my desk all evening. You'll see my laptop was active on the network the entire time.",
                "I stayed in {alibi_location} for a call that ran until after eleven. I never went near the executive floor.",
            ],
        },
        "solution_templates": [
            "The killer was {murderer_name} — not {red_herring_name}. Two constraints solve it: only one of three people with high-level system access has an eleven-minute digital blackout during the window; and only one suspect's professional training would encompass handling {residue} as a matter of course. {murderer_name} is the only person who satisfies both. Motive: {motive}.",
            "The evidence against {red_herring_name} was circumstantial. The real answer required cross-referencing: the physical key to the victim's office was issued to a documented list, and the compound's procurement points to one specific professional background. Mapped against all six suspects, only {murderer_name} sits at the intersection. Motive: {motive}. Method: {instrument}.",
        ],
    },
}


# ── Plottwyst templates (framing mechanism descriptions) ──────────────────────

_PLOTTWYST_TEMPLATES = [
    "{murderer_name} deliberately positioned {red_herring_name} near the scene and ensured their presence would be noted — exploiting an existing tension between {red_herring_name} and {victim_name} to divert suspicion from themselves.",
    "{murderer_name} planted personal items belonging to {red_herring_name} near the body, knowing {red_herring_name}'s known grievance with {victim_name} would make them the obvious suspect.",
    "By ensuring {red_herring_name} was seen near the {murder_location} that evening, {murderer_name} constructed a frame that investigators were intended to follow — while the true method and motive pointed elsewhere.",
    "The evidence trail leading to {red_herring_name} was no accident. {murderer_name} exploited a pre-existing conflict to manufacture suspicion, keeping the real motive and method hidden in plain sight.",
    "{murderer_name} knew that {red_herring_name}'s history with {victim_name} would speak for itself — and made certain that history was the first thing investigators would find.",
]

_PLOTTWYST_HINTS = [
    " Investigators note that several of the key pieces pointing to {red_herring_name} are curiously well-positioned — as though arranged for discovery rather than left in the chaos of a genuine crime.",
    " The pattern of evidence, taken together, is consistent with a calculated attempt to direct scrutiny away from its true source.",
    " The manner in which this evidence was arranged suggests deliberate placement rather than coincidence — each item positioned where it would be found, and found quickly.",
]


# ── Assembly engine ───────────────────────────────────────────────────────────

def _fill(template: str, ctx: dict) -> str:
    """Safe template fill — leaves unknown keys as-is rather than crashing."""
    try:
        return template.format(**ctx)
    except KeyError:
        # Fill what we can, leave the rest
        result = template
        for k, v in ctx.items():
            result = result.replace("{" + k + "}", str(v))
        return result


def generate_template_case(genre_key: str | None = None) -> dict:
    """
    Generate one complete, randomised murder mystery case from templates.
    No API calls. Instant. Effectively infinite combinations.
    """
    if genre_key is None or genre_key not in GENRES:
        genre_key = random.choice(list(GENRES.keys()))

    g   = GENRES[genre_key]
    cfg = g

    # ── Setting ──────────────────────────────────────────────────────────────
    venue       = random.choice(g["venues"])
    season      = random.choice(g["seasons"])
    all_locs    = g["locations"]

    # ── Names & roles ────────────────────────────────────────────────────────
    used_names: list[str] = []

    victim_gender = random.choice(["M", "F"])
    victim_name   = _name(victim_gender, used_names)
    used_names.append(victim_name)

    # ── Suspects ─────────────────────────────────────────────────────────────
    traits = [
        "methodical and precise",
        "hot-tempered and impulsive",
        "charming and disarming",
        "deeply secretive",
        "coldly calculating",
        "visibly desperate",
    ]
    shuffled_traits = random.sample(traits, len(traits))
    shuffled_locs   = random.sample(all_locs, len(all_locs))

    suspects_raw = []
    used_relations: dict[str, list[str]] = {"M": [], "F": []}
    for i in range(6):
        gender   = random.choice(["M", "F"])
        name     = _name(gender, used_names)
        used_names.append(name)
        avail_rels = [r for r in g["relations"][gender] if r not in used_relations[gender]]
        if not avail_rels:
            avail_rels = g["relations"][gender]
        relation = random.choice(avail_rels)
        used_relations[gender].append(relation)
        motives  = g["motives"].get(relation, ["an undisclosed personal grievance against the victim"])
        motive   = random.choice(motives)
        trait    = shuffled_traits[i]
        location = shuffled_locs[i % len(shuffled_locs)]
        suspects_raw.append({
            "name": name, "gender": gender, "relation": relation,
            "motive": motive, "trait": trait, "location": location,
        })

    # ── Assign roles ──────────────────────────────────────────────────────────
    murderer_idx    = random.randrange(6)
    rh_candidates   = [i for i in range(6) if i != murderer_idx]
    red_herring_idx = random.choice(rh_candidates)

    murderer    = suspects_raw[murderer_idx]
    red_herring = suspects_raw[red_herring_idx]

    # Red herring shares murderer's location (same place, only one killed)
    red_herring["location"] = murderer["location"]

    murder_location   = murderer["location"]
    murderer_location = murderer["location"]   # where murderer was last seen

    # ── Method & timing ──────────────────────────────────────────────────────
    method        = random.choice(g["methods"])
    twist         = random.choice(g["twists"])
    clue_chain    = random.choice(g["clue_chains"])
    time_of_death = f"{random.randint(21, 23)}:{random.choice(['04','12','18','27','33','41','52'])} PM"
    time_arrived  = f"{random.randint(20, 22)}:{random.choice(['15','22','38','44','51','57'])} PM"
    gap           = random.randint(8, 22)
    weeks         = random.randint(2, 4)

    # Alibi locations for innocents (not murder location)
    safe_locs = [l for l in all_locs if l != murder_location]

    # ── Build alibi statements ────────────────────────────────────────────────
    alibi_tmpls = g["alibi_templates"]

    # Pre-shuffle innocent alibi pool so each innocent gets a distinct template
    _innocent_raw = alibi_tmpls["innocent"]
    if len(_innocent_raw) >= 4:
        _innocent_pool = random.sample(_innocent_raw, 4)
    else:
        extended = _innocent_raw * ((4 // len(_innocent_raw)) + 1)
        random.shuffle(extended)
        _innocent_pool = extended[:4]
    _innocent_iter = iter(_innocent_pool)

    def build_alibi(role: str, alibi_loc: str) -> str:
        if role == "innocent":
            tmpl = next(_innocent_iter)
        else:
            tmpl = random.choice(alibi_tmpls[role])
        return _fill(tmpl, {
            "victim_name":     victim_name,
            "murderer_name":   murderer["name"],
            "murder_location": murder_location,
            "alibi_location":  alibi_loc,
            "time_of_death":   time_of_death,
            "time_arrived":    time_arrived,
        })

    # ── Assemble suspect profiles ─────────────────────────────────────────────
    suspects_out = []
    for i, s in enumerate(suspects_raw):
        if i == murderer_idx:
            role_key  = "murderer"
            is_m, is_rh = True, False
        elif i == red_herring_idx:
            role_key  = "red_herring"
            is_m, is_rh = False, True
        else:
            role_key  = "innocent"
            is_m, is_rh = False, False

        alibi_loc = murder_location if role_key in ("murderer", "red_herring") else random.choice(safe_locs)
        alibi     = build_alibi(role_key, alibi_loc)

        suspects_out.append({
            "name":           s["name"],
            "gender":         s["gender"],
            "relation":       s["relation"],
            "occupation":     s["relation"],  # template relations are already occupation-based
            "motive":         s["motive"],
            "trait":          s["trait"],
            "last_seen":      s["location"],
            "alibi":          alibi,
            "is_murderer":    is_m,
            "is_red_herring": is_rh,
        })

    # ── Build clues ───────────────────────────────────────────────────────────
    ctx = {
        "victim_name":        victim_name,
        "murderer_name":      murderer["name"],
        "red_herring_name":   red_herring["name"],
        "murder_location":    murder_location,
        "murderer_location":  murderer_location,
        "murderer_relation":  murderer["relation"],
        "murderer_occupation": murderer["relation"],
        "instrument":         method["instrument"],
        "residue":            method["residue"],
        "cause":              method["cause"],
        "motive":             murderer["motive"],
        "venue":              venue,
        "time_of_death":      time_of_death,
        "time_arrived":       time_arrived,
        "gap":                str(gap),
        "weeks":              str(weeks),
        "season":             season,
    }

    def build_clue(tmpl_tuple: tuple) -> dict:
        clue_type, tmpl = tmpl_tuple
        return {"type": clue_type, "text": _fill(tmpl, ctx)}

    opening_clues = [build_clue(t) for t in clue_chain["opening"]]
    round_clues   = {k: build_clue(clue_chain[k]) for k in ["round_1", "round_2", "round_3", "round_4"]}

    # Weave plottwyst hint into round_2 to surface the framing mid-game
    hint = _fill(random.choice(_PLOTTWYST_HINTS), ctx)
    round_clues["round_2"]["text"] += hint

    # ── Scene & solution ──────────────────────────────────────────────────────
    atm_tmpl     = random.choice(g["atmosphere_templates"])
    victim_role  = suspects_out[0]["relation"] if False else random.choice(g["relations"][victim_gender])
    atmosphere   = _fill(atm_tmpl, {**ctx, "victim_role": victim_role})

    plottwyst = _fill(random.choice(_PLOTTWYST_TEMPLATES), ctx)

    sol_tmpls = clue_chain.get("solution_templates", g["solution_templates"])
    sol_tmpl  = random.choice(sol_tmpls)
    solution = _fill(sol_tmpl, ctx)

    clue_pool = [round_clues["round_1"], round_clues["round_2"],
                 round_clues["round_3"], round_clues["round_4"]]

    return {
        "setting": {
            "genre":      g["label"],
            "era":        g["era"],
            "venue":      venue,
            "atmosphere": atmosphere,
        },
        "victim": {
            "name":       victim_name,
            "gender":     victim_gender,
            "background": f"A prominent figure at {venue}, known for sharp instincts and a habit of keeping records others would prefer to see destroyed.",
            "secrets":    f"Had recently uncovered information about {murderer['name']} that posed an existential threat.",
        },
        "plottwyst":   plottwyst,
        "murderer":    murderer["name"],
        "red_herring": red_herring["name"],
        "suspects":    suspects_out,
        "clues": {
            "opening": opening_clues,
            **round_clues,
        },
        "solution":   solution,
        "clue_pool":  clue_pool,
        "_genre_ctx": {
            "genre":              g["label"],
            "era":                g["era"],
            "venue":              venue,
            "murder_method_hint": method["name"],
            "clue_flavour":       "",
        },
    }
