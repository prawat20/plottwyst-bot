from __future__ import annotations
"""
Builds the Gemini prompt for a complete, unique murder mystery case.

Design goals (Mastermind difficulty — always):
- Two opening clues misdirect toward the red herring. Rounds 1–2 deepen that suspicion.
  By the end of round 2 the red herring must be the obvious, dominant suspect.
- One opening clue is the ARC CLUE — its position (1, 2, or 3) is randomised each game.
- Rounds 3–4 shift from misdirection to deduction via arc-specific resolution.
- The plottwyst (framing mechanism) is woven into one mid-game clue, revealed fully at the end.
- No single clue implicating the murderer is conclusive on its own.
- The solution should feel like "how did I miss that?" not "of course".

Arc variants:
  A — PURE SYNTHESIS    : arc clue has a hidden detail only the murderer satisfies
  B — INNOCENT MENTION  : arc clue appears to clear the murderer (exoneration)
  C — DOUBLE SUSPECT    : arc clue introduces a second strong suspect alongside the red herring
  E — FALSE WITNESS     : arc clue is a named witness statement that is lying or mistaken
"""


def build_prompt(genre_ctx: dict, arc: str = "A", arc_position: int = 3) -> str:
    # ── Pre-compute all dynamic parts ─────────────────────────────────────────
    non_arc   = sorted(p for p in [1, 2, 3] if p != arc_position)
    rh1_pos   = non_arc[0]   # lower non-arc position → physical clue
    rh2_pos   = non_arc[1]   # higher non-arc position → timeline clue

    arc_name = {
        "A": "PURE SYNTHESIS",
        "B": "INNOCENT MENTION",
        "C": "DOUBLE SUSPECT",
        "E": "FALSE WITNESS",
    }[arc]

    arc_type_hint = {
        "A": "physical | timeline | testimonial | forensic | documentary",
        "B": "physical | documentary",
        "C": "testimonial | physical",
        "E": "testimonial",
    }[arc]

    arc_clue_instruction = {
        "A": (
            "An AMBIGUITY CLUE — nominally implicates the red herring but contains one specific "
            "embedded detail (a required skill, access credential, timing constraint, or specialist "
            "knowledge) that only the murderer possesses. Players read it as a strike against the "
            "red herring; in the solution it recontextualises as the first real evidence of the murderer."
        ),
        "B": (
            "An EXONERATION CLUE based on physical evidence or a verifiable record (not merely a "
            "witness statement) that appears to place the murderer elsewhere or prove they could not "
            "have acted. Makes the murderer the least likely suspect when this clue is first read."
        ),
        "C": (
            "An EMERGENCE CLUE that introduces a SECOND strong suspect entirely distinct from the "
            "red herring — a piece of evidence, a record, or a physical object that ties a different "
            "named suspect to the victim with compelling weight. After this clue players have two "
            "strong candidates, not one. Both will be eliminated by constraint clues in rounds 3–4."
        ),
        "E": (
            "A WITNESS STATEMENT attributed to one of the named suspects that places the RED HERRING "
            "at the scene, in possession of the murder weapon, or in a damning exchange with the "
            "victim. The statement is specific, attributed by name, and reads as a decisive strike "
            "against the red herring — but the witness is lying or mistaken for reasons revealed in round 3."
        ),
    }[arc]

    arc_r3_r4 = {
        "A": (
            f"   - Round 3: An ELIMINATION CONSTRAINT that rules out most suspects INCLUDING the "
            f"red herring specifically. Must narrow the field to 2–3 suspects — not just 1, not "
            f"\"most\". No suspect is named. This is the pivot: the player's prime suspect is eliminated.\n"
            f"   - Round 4: A SECOND ELIMINATION CONSTRAINT of a different type. Combined with "
            f"round 3, exactly one suspect satisfies both. No suspect is named."
        ),
        "B": (
            f"   - Round 3: Dismantles the specific evidence from opening clue {arc_position} "
            f"(the log is automated, the object was planted, the timing is wrong). Must also "
            f"introduce one constraint detail the murderer satisfies. No suspect named.\n"
            f"   - Round 4: A CONSTRAINT CLUE that, combined with the round 3 detail, narrows "
            f"to exactly one suspect. No suspect named."
        ),
        "C": (
            f"   - Round 3: An ELIMINATION CONSTRAINT that rules out BOTH the red herring AND "
            f"the second suspect introduced in opening clue {arc_position}, each failing for a "
            f"different specific reason (one lacks the required access, the other fails on timing "
            f"or method). Must still leave 2–3 suspects in play. No suspect named.\n"
            f"   - Round 4: A SECOND ELIMINATION CONSTRAINT of a different type. Combined with "
            f"round 3, exactly one suspect satisfies both. No suspect is named."
        ),
        "E": (
            f"   - Round 3: Dismantles the witness statement from opening clue {arc_position} — "
            f"reveals it contains a provable impossibility (a timing conflict with a verifiable "
            f"record, a physical constraint the witness couldn't have observed, or a named document "
            f"directly contradicting their account). Also introduces one elimination constraint. "
            f"No suspect named.\n"
            f"   - Round 4: A CONSTRAINT CLUE that, combined with the round 3 detail, narrows "
            f"to exactly one suspect. No suspect named."
        ),
    }[arc]

    solution_arc_note = {
        "A": (
            f"recontextualise opening clue {arc_position} — explain what the embedded ambiguity "
            f"detail was really pointing at and why players almost certainly misread it"
        ),
        "B": (
            f"recontextualise opening clue {arc_position} — show how the exoneration evidence "
            f"was false and what specific detail in round 3 exposed it"
        ),
        "C": (
            f"recontextualise opening clue {arc_position} — explain why the second suspect was "
            f"a false lead and how the two separate constraints eliminated both them and the red herring"
        ),
        "E": (
            f"recontextualise opening clue {arc_position} — reveal that the witness was lying or "
            f"mistaken, expose their real motive for the false statement, and show what the "
            f"round 3 impossibility actually proved"
        ),
    }[arc]

    # ── Opening clue JSON schema entries ──────────────────────────────────────
    # rh1_pos and rh2_pos get standard red-herring clues (physical, timeline).
    # arc_position gets the arc-specific clue.
    _rh_physical = (
        '{"type": "physical",  "text": "string — a specific physical object or forensic trace at a '
        'named location that strongly implicates the RED HERRING. References a real object (not vague). '
        'Does not mention or implicate the murderer."}'
    )
    _rh_timeline = (
        '{"type": "timeline",  "text": "string — a specific time, movement, or access record placing '
        'the RED HERRING at or near the scene. The murderer\'s movements are not mentioned."}'
    )
    _arc_clue = (
        f'{{"type": "{arc_type_hint}", "text": "string — opening clue {arc_position} (ARC CLUE): '
        f'{arc_clue_instruction}"}}'
    )

    slots = {rh1_pos: _rh_physical, rh2_pos: _rh_timeline, arc_position: _arc_clue}
    opening_block = "\n      ".join(slots[p] for p in [1, 2, 3])

    # ── Build and return the full prompt ──────────────────────────────────────
    return f"""You are a master murder mystery writer. Generate a complete, original murder mystery case as a single JSON object. Every game must feel unique and surprising.

SETTING CONTEXT:
- Genre: {genre_ctx['genre']}
- Era: {genre_ctx['era']}
- Venue: {genre_ctx['venue']}
- Murder method: {genre_ctx['murder_method_hint']} — use this method or a close era-appropriate variant. It must appear in the clues and solution.
- Evidence flavour (draw from these types): {genre_ctx['clue_flavour']}

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no commentary:

{{
  "setting": {{
    "genre": "string",
    "era": "string",
    "venue": "string — specific name of the location",
    "atmosphere": "string — 2-sentence vivid description of the scene when the body is found"
  }},
  "victim": {{
    "name": "string — full name",
    "gender": "M or F",
    "background": "string — 2–3 sentences: who they were, their role in the setting, and what they were planning or had done in the hours before their death that made someone feel threatened",
    "secrets": "string — a secret they held that made enemies"
  }},
  "plottwyst": "string — 2–3 sentences describing exactly how the murderer engineered the misdirection toward the red herring: what physical action they took (planted evidence, exploited an existing grievance, manipulated a record), why it was convincing, and what specific detail in the evidence trail reveals the fabrication in hindsight. This must be hinted at as a subtle detail in one round 1–4 clue — players can notice it but probably won't understand it until the final reveal.",
  "murderer": "string — must match a suspect name exactly",
  "red_herring": "string — must match a different suspect name exactly",
  "suspects": [
    {{
      "name": "string — full name. All 6 names must be unique — no two suspects share a first or last name.",
      "gender": "M or F",
      "relation": "string — their specific relationship to the victim (e.g. estranged business partner, hired investigator, childhood friend turned rival). Describes connection to the victim, not their job.",
      "occupation": "string — their real-world profession (e.g. chemist, solicitor, retired colonel, seamstress, journalist). A concrete profession with a plausible skill set — never a social role like fiancée or wife.",
      "motive": "string — specific, believable reason they might kill the victim",
      "trait": "string — one defining personality trait (e.g. methodical, paranoid, charming, volatile)",
      "last_seen": "string — specific named location within the venue at time of murder",
      "alibi": "string — 2-sentence third-person alibi. See alibi rules in Rule 16."
    }}
  ],
  "clues": {{
    "opening": [
      {opening_block}
    ],
    "round_1": {{"type": "forensic",    "text": "string — specific forensic detail (trace, method, biological evidence) deepening suspicion toward the RED HERRING. No evidence implicating the murderer."}},
    "round_2": {{"type": "documentary", "text": "string — a specific document (named letter, dated log, signed record) appearing to seal the RED HERRING's guilt. Players should be most certain here."}},
    "round_3": {{"type": "string — choose: physical | timeline | testimonial | forensic | documentary", "text": "string — see CLUE ARC in Rule 9."}},
    "round_4": {{"type": "string — choose: physical | timeline | testimonial | forensic | documentary", "text": "string — see CLUE ARC in Rule 9."}}
  }},
  "solution": "string — 4–5 sentence dramatic detective reveal. Must: (1) name the murderer and state their motive, (2) explain the murder method and its connection to their occupation, (3) show how the constraint clues eliminate everyone else, (4) {solution_arc_note}, (5) explain how the plottwyst (framing of the red herring) was constructed. Written as a compelling in-world narrative, not a technical checklist. Never use phrases like 'round 3 showed' or 'the constraint clue'."
}}

RULES — follow all of these without exception:

1. Exactly 6 suspects. One murderer, one red herring, four innocent. Do not add is_murderer or is_red_herring fields — these are set automatically.

2. The red herring must share the same last_seen location as the murderer — they were both there, only one killed.

3. The red herring must have a compelling, specific motive — one players find convincing right up until round 3.

4. All clue slots (opening ×3, round_1 through round_4) must be present, non-empty, and substantive.

5. The murder method must align with the murder_method_hint. It must appear in the clues and solution.

6. The plottwyst must surface as a subtle detail in one of the round 1–4 clues. It cannot exist only in the plottwyst field — players must have had the chance to notice it during play.

7. All 6 suspect names must be unique — no two suspects share a first or last name.

8. OPENING AND EARLY ROUNDS:
   - Opening clue {rh1_pos} and opening clue {rh2_pos}: Both strongly implicate the RED HERRING. The murderer is not mentioned.
   - Opening clue {arc_position}: the ARC CLUE — see Rule 9 exactly.
   - Round 1: Forensic detail deepening red herring suspicion.
   - Round 2: Documentary peak — appears to seal red herring's guilt. Misdirection maximum.

9. CLUE ARC — you MUST use VARIANT {arc} ({arc_name}) exactly as specified:

   - Opening clue {arc_position}: {arc_clue_instruction}
{arc_r3_r4}

10. CONSTRAINT CLUE DESIGN — elimination, not identification:
    Constraints must rule suspects OUT, not point directly at one person.
    GOOD: "The east corridor required a staff master key — only certain roles held one." Players eliminate everyone without a key.
    BAD: "The killer had expert knowledge of poisons." Too directly identifies the chemist.
    Round 3 must narrow to 2–3 suspects. Round 4 must cut to 1. This two-stage narrowing is harder to solve than a single elimination.
    The RED HERRING must fail at least one of the two constraint clues. Verify this explicitly before writing.

11. PROFILE–CLUE ALIGNMENT — mandatory pre-writing check:
    Before writing any clues: (a) list both constraints, (b) check every suspect against each, (c) confirm only the murderer satisfies both, (d) confirm the red herring fails at least one, (e) if any innocent satisfies both, change the constraint or that suspect's profile.

12. RED HERRING DOMINANCE — at the end of round 2, a rational player should be MORE confident about the red herring than about any other suspect. The red herring must have: the strongest apparent motive, clearest opportunity, and most incriminating physical evidence. The murderer should appear to be a secondary suspect or borderline innocent at this stage.

13. ALIBI NETWORK — alibis must form a cross-referencing web, not isolated statements:
    - At least two innocent suspects' alibis must reference each other by name ("She was with Mr. X in the drawing room — Mr. X can confirm").
    - The murderer's false alibi must contain one subtle internal detail that contradicts another suspect's statement when the two are compared carefully. Players who cross-reference will catch the inconsistency.
    - The red herring's alibi is vague or unverifiable — no named witness, no record.
    - Each of the four innocent suspects conceals one minor unrelated secret (an affair, a debt, a small theft, an embarrassment) that makes them evasive about a specific detail in their alibi. They are innocent of the murder but not of everything.

14. VICTIM AS ACTIVE AGENT — the victim must have been actively doing something in the hours before their death that made the murderer feel threatened: scheduling a meeting, sending a message, preparing to make an announcement, or retrieving a document. This must surface in at least one clue.

15. PHYSICAL ANCHORING — every clue must reference a specific named object, a specific named location within the venue, or a specific person. Vague observations are not allowed.
    GOOD: "A torn corner of a telegram was found wedged beneath the escritoire in the east study."
    BAD: "Signs of a struggle were found near the scene."

16. ALIBI FORMAT — alibi field rules:
    - All alibis are written in third-person prose (never first-person).
    - Murderer's alibi: false, specific, and convincing — sounds like the least suspicious account.
    - Red herring's alibi: vague, unverifiable, no named corroboration.
    - Innocent suspects: solid alibis with named witnesses or records — but each innocent is evasive about one specific detail due to their unrelated secret.

17. ANTI-ARCHETYPE — vary which type of suspect is the murderer. Do not default to the most sinister-sounding occupation (chemist, retired colonel, solicitor). The murderer may be the journalist, the maid, the socialite, the accountant — whoever serves the story. Experienced players should not be able to predict the murderer from their occupation alone.

18. NO SINGLE-CLUE DEDUCTION — no clue that implicating the murderer should be conclusive on its own. Every piece of evidence pointing toward the murderer must require combination with at least one other clue to become conclusive.

19. Round 3 and round 4 clues must NEVER name any suspect. Facts about the crime, the method, or the evidence only.

20. Content appropriate for adult friend groups. No gore, no real-world groups targeted.

21. Every name, location, and detail must fit the era and genre provided.
"""
