from __future__ import annotations
"""
Builds the Gemini prompt for a complete, unique murder mystery case.

Design goals (Mastermind difficulty — always):
- Opening clues 1 & 2 misdirect toward the red herring. Round 1-2 deepen that suspicion.
- Two structural arcs are available — AI chooses either:
    Variant A (Pure Synthesis): opening clue 3 also implicates red herring; rounds 3-4
      are two independent constraint clues that intersect at exactly one suspect.
    Variant B (Innocent Mention): opening clue 3 appears to CLEAR the murderer (apparent
      alibi); round 3 quietly dismantles that clearing detail; round 4 is a constraint clue.
- No single clue ever names or conclusively points to the murderer alone.
- The solution should feel like "how did I miss that?" not "of course".
"""


def build_prompt(genre_ctx: dict) -> str:
    return f"""You are a master murder mystery writer. Generate a complete, original murder mystery case as a single JSON object. Every game must feel unique and surprising.

SETTING CONTEXT:
- Genre: {genre_ctx['genre']}
- Era: {genre_ctx['era']}
- Venue: {genre_ctx['venue']}
- Murder method inspiration: {genre_ctx['murder_method_hint']}
- Evidence flavour (use these types): {genre_ctx['clue_flavour']}

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
    "background": "string — 2 sentences: who they were, their role in the setting",
    "secrets": "string — 1 sentence: a secret they held that made enemies"
  }},
  "twist": "string — one unexpected complication that makes the case harder (e.g. alibi was fabricated by two people, victim was being blackmailed, security logs were deleted)",
  "murderer": "string — must match a suspect name exactly",
  "red_herring": "string — must match a different suspect name exactly",
  "suspects": [
    {{
      "name": "string — full name (6 suspects total, not the victim)",
      "gender": "M or F",
      "relation": "string — their relationship to the victim (e.g. business partner, estranged brother, hired investigator — be specific and era-appropriate. Do NOT use relationship statuses like fiancée, wife, husband as the sole descriptor — include their actual occupation or role)",
      "occupation": "string — their real-world job or skill set (e.g. chemist, solicitor, retired colonel, seamstress, journalist). Must be a concrete profession with a plausible tool set and area of expertise — not a social role.",
      "motive": "string — specific, believable reason they might kill the victim",
      "trait": "string — one defining personality trait (e.g. methodical, paranoid, charming, volatile)",
      "last_seen": "string — specific location within the venue at time of murder",
      "alibi": "string — 2-sentence alibi statement in their own voice. Murderer's alibi is false. Red herring's alibi is vague. Innocents tell the truth.",
      "is_murderer": false,
      "is_red_herring": false
    }}
  ],
  "clues": {{
    "opening": [
      {{"type": "physical",    "text": "string — physical evidence at the scene pointing toward the RED HERRING (an object of theirs, their location, something tied to them) — must NOT implicate the murderer"}},
      {{"type": "timeline",    "text": "string — time/movement detail that places the RED HERRING at or near the scene at a suspicious time — the murderer's movements are not mentioned"}},
      {{"type": "testimonial", "text": "string — a witness account that incriminates the RED HERRING (they were seen, overheard, or reported near the scene or in conflict with the victim)"}}
    ],
    "round_1": {{"type": "forensic",     "text": "string — forensic detail that deepens suspicion toward the RED HERRING (method, access, or background that fits them) — no evidence pointing to the murderer"}},
    "round_2": {{"type": "documentary",  "text": "string — a document (letter, log, record, message) that appears to seal the RED HERRING's guilt — misdirection peak; players should feel most certain here"}},
    "round_3": {{"type": "testimonial",  "text": "string — see CLUE ARC VARIANTS below for what this must contain"}},
    "round_4": {{"type": "physical",     "text": "string — see CLUE ARC VARIANTS below for what this must contain"}}
  }},
  "solution": "string — 3-4 sentence narrative explanation. Name the murderer, explain their motive, describe how they did it, and show how the clues prove it. Should feel like the detective's final reveal."
}}

RULES — you must follow all of these:
1. Exactly 6 suspects. One is the murderer, one is the red herring, four are innocent.
2. Set is_murderer=true only on the murderer. Set is_red_herring=true only on the red herring.
3. Red herring must share the same last_seen location as the murderer (they were both there — only one killed).
4. Red herring must have a compelling, specific motive — one that players will find convincing right up until round 3 or 4.
5. All clue slots (opening x3, round_1 through round_4) must be present and non-empty.
6. MASTERMIND CLUE STRUCTURE — mandatory regardless of arc variant chosen:
   - Opening clues 1 & 2: Both implicate the RED HERRING strongly.
   - Round 1: Forensic detail that deepens red herring suspicion.
   - Round 2: Documentary peak — a document that appears to seal the red herring's guilt. Players should feel most certain here.
7. CLUE ARC VARIANTS — choose exactly ONE of the following for opening clue 3, round 3, and round 4:

   VARIANT A — PURE SYNTHESIS (default):
   - Opening clue 3: A third piece of testimony or physical evidence that further implicates the RED HERRING. The murderer is not mentioned.
   - Round 3: A CONSTRAINT CLUE — a factual observation about the crime (timing gap, insider knowledge, access credential) that rules out most suspects when cross-referenced against their profiles. NO suspect is named.
   - Round 4: A SECOND CONSTRAINT CLUE of a different type. Combined with round 3, exactly ONE suspect satisfies both constraints simultaneously. NO suspect is named.

   VARIANT B — INNOCENT MENTION:
   - Opening clue 3: A testimonial that appears to CLEAR THE MURDERER — a witness places them elsewhere, a log appears to exonerate them, a colleague confirms their alibi. This makes the murderer seem like the least likely suspect at the opening.
   - Round 3: A factual observation that dismantles the specific clearing detail from opening clue 3 — the witness recants a detail, the log is shown to be automated, the alibi is shown to be unverifiable. NO suspect is named in round 3. The discrediting is presented as a fact about the evidence, not an accusation.
   - Round 4: A CONSTRAINT CLUE — a specialist skill, physical trace, or access credential that narrows to exactly one suspect when mapped against all profiles. NO suspect is named.

8. The murderer's suspect profile MUST contain specific, verifiable details (in occupation, trait, last_seen, or alibi) that satisfy the round 3 and round 4 constraints uniquely. No other suspect satisfies both simultaneously. BEFORE writing any clues, mentally verify: does the murderer's occupation or a specific attribute in their profile directly support the constraint you plan to use? If not, change either the murderer's profile or the constraint until they align. Never write a constraint clue that references a skill, tool, or knowledge area not present in the murderer's profile.
9. The murderer's alibi must sound solid regardless of arc variant chosen.
10. Round 3 and round 4 clues must NEVER name any suspect. They are factual observations about the crime or the evidence, not accusations.
11. The solution paragraph must explicitly state: (a) what the round 3 mechanism is and how it maps to the murderer's profile, (b) what the round 4 constraint is and which attribute satisfies it, (c) why no other suspect satisfies both.
12. Keep all content appropriate for adult friend groups. No gore, no real-world groups targeted.
13. Every name, location, and detail must fit the era and genre.
"""
