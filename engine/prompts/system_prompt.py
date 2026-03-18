from __future__ import annotations
"""
Builds the Gemini prompt for a complete, unique murder mystery case.

Design goals (Mastermind difficulty — always):
- Opening clues 1 & 2 misdirect toward the red herring. Rounds 1–2 deepen that suspicion.
  By the end of round 2 the red herring must be the obvious, dominant suspect.
- Opening clue 3 is an ambiguity clue — nominally implicates the red herring but contains
  one embedded detail that only the murderer could satisfy.
- Rounds 3–4 shift from misdirection to deduction via elimination constraints.
  Round 3 narrows to 2–3 suspects AND specifically eliminates the red herring.
  Round 4 narrows to exactly 1.
- The plottwyst (framing mechanism) is woven into one mid-game clue, revealed fully at the end.
- No single clue implicating the murderer is conclusive on its own.
- The solution should feel like "how did I miss that?" not "of course".
"""


def build_prompt(genre_ctx: dict) -> str:
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
      {{"type": "physical",    "text": "string — a specific physical object or forensic trace at a named location that strongly implicates the RED HERRING. References a real object (not vague). Does not mention or implicate the murderer."}},
      {{"type": "timeline",    "text": "string — a specific time, movement, or access record placing the RED HERRING at or near the scene. The murderer's movements are not mentioned."}},
      {{"type": "testimonial", "text": "string — see CLUE ARC VARIANTS in Rule 9. This is the critical ambiguity clue."}}
    ],
    "round_1": {{"type": "forensic",    "text": "string — specific forensic detail (trace, method, biological evidence) deepening suspicion toward the RED HERRING. No evidence implicating the murderer."}},
    "round_2": {{"type": "documentary", "text": "string — a specific document (named letter, dated log, signed record) appearing to seal the RED HERRING's guilt. Players should be most certain here."}},
    "round_3": {{"type": "string — choose: physical | timeline | testimonial | forensic | documentary", "text": "string — see CLUE ARC VARIANTS in Rule 9."}},
    "round_4": {{"type": "string — choose: physical | timeline | testimonial | forensic | documentary", "text": "string — see CLUE ARC VARIANTS in Rule 9."}}
  }},
  "solution": "string — 4–5 sentence dramatic detective reveal. Must: (1) name the murderer and state their motive, (2) explain the murder method and its connection to their occupation, (3) show how the constraint clues eliminate everyone else, (4) recontextualise opening clue 3 — explain what that detail was really pointing at, (5) explain how the plottwyst (framing of the red herring) was constructed. Written as a compelling in-world narrative, not a technical checklist. Never use phrases like 'round 3 showed' or 'the constraint clue'."
}}

RULES — follow all of these without exception:

1. Exactly 6 suspects. One murderer, one red herring, four innocent. Do not add is_murderer or is_red_herring fields — these are set automatically.

2. The red herring must share the same last_seen location as the murderer — they were both there, only one killed.

3. The red herring must have a compelling, specific motive — one players find convincing right up until round 3.

4. All clue slots (opening ×3, round_1 through round_4) must be present, non-empty, and substantive.

5. The murder method must align with the murder_method_hint. It must appear in the clues and solution.

6. The plottwyst must surface as a subtle detail in one of the round 1–4 clues. It cannot exist only in the plottwyst field — players must have had the chance to notice it during play.

7. All 6 suspect names must be unique — no two suspects share a first or last name.

8. OPENING AND EARLY ROUNDS — mandatory for both arc variants:
   - Opening clues 1 & 2: Both strongly implicate the RED HERRING. The murderer is not mentioned.
   - Round 1: Forensic detail deepening red herring suspicion.
   - Round 2: Documentary peak — appears to seal red herring's guilt. Misdirection maximum.

9. CLUE ARC VARIANTS — choose exactly ONE:

   VARIANT A — PURE SYNTHESIS (default):
   - Opening clue 3: An AMBIGUITY CLUE — nominally implicates the red herring but contains one specific embedded detail (a required skill, access credential, timing constraint, or specialist knowledge) that only the murderer possesses. Players read it as a third strike against the red herring at the opening; in the solution, it recontextualises as the first real evidence of the murderer.
   - Round 3: An ELIMINATION CONSTRAINT that rules out most suspects INCLUDING the red herring specifically. Must narrow the field to 2–3 suspects — not just 1, not "most". No suspect is named. This is the pivot: the player's prime suspect is eliminated.
   - Round 4: A SECOND ELIMINATION CONSTRAINT of a different type. Combined with round 3, exactly one suspect satisfies both. No suspect is named.

   VARIANT B — INNOCENT MENTION:
   - Opening clue 3: An EXONERATION CLUE based on physical evidence or a record (not merely a witness) that appears to place the murderer elsewhere or prove they could not have acted. Makes the murderer the least likely suspect at the opening.
   - Round 3: Dismantles the specific evidence from clue 3 (the log is automated, the object was planted, the timing is wrong). Must also introduce one constraint detail the murderer satisfies. No suspect named.
   - Round 4: A CONSTRAINT CLUE that, combined with the round 3 detail, narrows to exactly one suspect. No suspect named.

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

18. NO SINGLE-CLUE DEDUCTION — no clue that implicates the murderer should be conclusive on its own. Every piece of evidence pointing toward the murderer must require combination with at least one other clue to become conclusive.

19. Round 3 and round 4 clues must NEVER name any suspect. Facts about the crime, the method, or the evidence only.

20. Content appropriate for adult friend groups. No gore, no real-world groups targeted.

21. Every name, location, and detail must fit the era and genre provided.
"""
