from __future__ import annotations
"""
Builds the Gemini prompt for a complete, unique murder mystery case.

Design goals (Mastermind difficulty — always):
- Opening clues 1 & 2 misdirect toward the red herring. Rounds 1–2 deepen that suspicion.
- Opening clue 3 is deliberately ambiguous — it nominally implicates the red herring but
  contains one specific detail that, on reflection, only the murderer could satisfy.
- Rounds 3–4 shift from misdirection to deduction via elimination constraints.
  Round 3 must specifically rule out the red herring, breaking the false certainty built
  in rounds 1–2. Combined with round 4, exactly one suspect remains.
- Two structural arcs:
    Variant A (Pure Synthesis): opening clue 3 is an ambiguity clue; rounds 3–4 are two
      independent elimination constraints that intersect at exactly one suspect.
    Variant B (Innocent Mention): opening clue 3 actively exonerates the murderer via
      physical evidence or a record; round 3 dismantles it; round 4 is a constraint clue.
- The red herring must fail at least one constraint clue in rounds 3–4.
- The solution should feel like "how did I miss that?" not "of course".
"""


def build_prompt(genre_ctx: dict) -> str:
    return f"""You are a master murder mystery writer. Generate a complete, original murder mystery case as a single JSON object. Every game must feel unique and surprising.

SETTING CONTEXT:
- Genre: {genre_ctx['genre']}
- Era: {genre_ctx['era']}
- Venue: {genre_ctx['venue']}
- Murder method: {genre_ctx['murder_method_hint']} — your case must use this method or a close era-appropriate variant. It must appear in the clues and solution.
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
    "background": "string — 2 sentences: who they were, their role in the setting",
    "secrets": "string — a secret they held that made enemies"
  }},
  "twist": "string — one unexpected complication that makes the case harder (e.g. alibi was fabricated by two people, victim was being blackmailed, a key record was altered). Must surface in at least one clue — it cannot exist only as a standalone field.",
  "murderer": "string — must match a suspect name exactly",
  "red_herring": "string — must match a different suspect name exactly",
  "suspects": [
    {{
      "name": "string — full name. All 6 suspect names must be unique — no two suspects share a first name or last name.",
      "gender": "M or F",
      "relation": "string — their specific relationship to the victim (e.g. estranged business partner, hired investigator, childhood friend turned rival). Describes the connection to the victim, not their profession.",
      "occupation": "string — their real-world profession (e.g. chemist, solicitor, retired colonel, seamstress, journalist). Must be a concrete profession with a plausible skill set — never a social role like fiancée or wife.",
      "motive": "string — specific, believable reason they might kill the victim",
      "trait": "string — one defining personality trait (e.g. methodical, paranoid, charming, volatile)",
      "last_seen": "string — specific location within the venue at time of murder",
      "alibi": "string — 2-sentence third-person alibi statement. Murderer's alibi is false but specific and convincing. Red herring's alibi is vague or unverifiable. Innocent suspects have solid, verifiable alibis with named witnesses or records."
    }}
  ],
  "clues": {{
    "opening": [
      {{"type": "physical",    "text": "string — physical evidence at the scene that strongly implicates the RED HERRING. Must not mention or implicate the murderer."}},
      {{"type": "timeline",    "text": "string — a time or movement detail that places the RED HERRING at or near the scene at a suspicious time. The murderer's movements are not mentioned."}},
      {{"type": "testimonial", "text": "string — see CLUE ARC VARIANTS in Rule 9 for what this must contain. This is the critical clue 3."}}
    ],
    "round_1": {{"type": "forensic",    "text": "string — forensic detail that deepens suspicion toward the RED HERRING. No evidence pointing to the murderer."}},
    "round_2": {{"type": "documentary", "text": "string — a document (letter, log, record, message) that appears to seal the RED HERRING's guilt. Misdirection peak — players should feel most certain here."}},
    "round_3": {{"type": "string — choose: physical | timeline | testimonial | forensic | documentary", "text": "string — see CLUE ARC VARIANTS in Rule 9."}},
    "round_4": {{"type": "string — choose: physical | timeline | testimonial | forensic | documentary", "text": "string — see CLUE ARC VARIANTS in Rule 9."}}
  }},
  "solution": "string — 4–5 sentence dramatic detective reveal. Must: (1) name the murderer and state their motive, (2) explain the murder method and how it connects to their occupation or profile, (3) show how the constraint clues narrow to the murderer specifically, (4) recontextualise opening clue 3 — explain the detail that was pointing at the murderer all along. Written as a compelling narrative reveal, not a technical checklist."
}}

RULES — follow all of these without exception:

1. Exactly 6 suspects. One is the murderer, one is the red herring, four are innocent. Do not add is_murderer or is_red_herring fields to suspects — these are set automatically.

2. The red herring must share the same last_seen location as the murderer — they were both there, only one killed.

3. The red herring must have a compelling, specific motive that players will find convincing right up until round 3.

4. All clue slots (opening ×3, round_1 through round_4) must be present, non-empty, and substantive.

5. The murder method must align with the murder_method_hint. It must appear in the clues and in the solution narrative.

6. The twist must surface in at least one clue. It cannot be a standalone detail disconnected from the evidence.

7. All 6 suspect names must be unique — no two suspects share a first or last name.

8. OPENING AND EARLY ROUNDS — mandatory structure for both arc variants:
   - Opening clues 1 & 2: Both strongly implicate the RED HERRING. The murderer is not mentioned.
   - Round 1: Forensic detail that deepens red herring suspicion.
   - Round 2: Documentary peak — appears to seal the red herring's guilt. Players should be most certain here.

9. CLUE ARC VARIANTS — choose exactly ONE:

   VARIANT A — PURE SYNTHESIS (default):
   - Opening clue 3: An AMBIGUITY CLUE — it nominally implicates the red herring (a witness account, an object, or a connection) but contains one specific embedded detail (a required skill, a particular access credential, a timing constraint, or specialist knowledge) that only the murderer possesses. At the opening, players read this as a third strike against the red herring. In the solution reveal, this clue recontextualises as the first real evidence pointing at the murderer.
   - Round 3: An ELIMINATION CONSTRAINT — a factual observation about the crime (e.g. required entry method, specific technical knowledge, a physical trait the killer must have had) that rules out most suspects and SPECIFICALLY rules out the red herring. This is the pivot point: the player's prime suspect is eliminated. No suspect is named. The constraint must be directly testable against each suspect's profile.
   - Round 4: A SECOND ELIMINATION CONSTRAINT of a different type. Combined with round 3, exactly one suspect satisfies both. No suspect is named.

   VARIANT B — INNOCENT MENTION:
   - Opening clue 3: An EXONERATION CLUE based on physical evidence or a record — NOT merely a witness — that appears to place the murderer elsewhere or prove they could not have acted (e.g. a time-stamped log, a physical object found in another location, a forensic result that seems to exonerate them). This makes the murderer the least likely suspect at the opening.
   - Round 3: A factual observation that dismantles the specific evidence from opening clue 3 (e.g. the log is shown to be automated, the physical object was planted, the forensic timing is off). Round 3 must also introduce one constraint detail the murderer satisfies. No suspect is named.
   - Round 4: A CONSTRAINT CLUE that, combined with the round 3 detail, narrows to exactly one suspect. No suspect is named.

10. CONSTRAINT CLUE DESIGN — elimination, not identification:
    Constraints must work by ruling suspects OUT, not by pointing directly at one suspect.
    GOOD: "The killer entered through the east corridor, accessible only to staff with a master key." Players eliminate everyone without a master key.
    BAD: "The killer had expert knowledge of poisons." Too directly identifies the chemist.
    Before writing round 3 and round 4, explicitly verify: does the RED HERRING fail at least one of these two constraints? If not, redesign the constraint or the red herring's profile until they do.

11. PROFILE–CLUE ALIGNMENT — mandatory pre-writing check:
    Before writing any clues: (a) write down both constraints you plan to use, (b) check every suspect's occupation, trait, last_seen, and alibi against each constraint, (c) confirm the murderer is the ONLY suspect who satisfies both constraints simultaneously, (d) confirm the red herring fails at least one, (e) if any other innocent suspect also satisfies both, change either the constraint or that suspect's profile before proceeding.

12. The murderer's alibi must be specific and convincing — the kind that makes them seem the least likely killer, not vague or obviously flimsy.

13. Round 3 and round 4 clues must NEVER name any suspect. They present facts about the crime, the method, or the evidence only.

14. The solution must be written as a compelling detective reveal — not a technical checklist. Explain what opening clue 3 really meant (the detail players should have caught), show how the constraints eliminate the red herring and all others, and state why the murderer's profile is the only one that fits. Do not use phrases like "round 3 showed" or "the constraint clue" — write it as an in-world revelation.

15. Keep all content appropriate for adult friend groups. No gore, no real-world groups targeted.

16. Every name, location, and detail must fit the era and genre provided.
"""
