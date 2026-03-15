from __future__ import annotations
"""
Case generator — calls Gemini and returns a validated case dict.

Retries up to MAX_RETRIES times on malformed JSON or validation failure.
Raises RuntimeError if all retries are exhausted.
"""
import json
import logging
from google import genai
from google.genai import types

import config
from engine.prompts.genres import pick_random_genre
from engine.prompts.system_prompt import build_prompt
from engine.validator import validate_case
from engine.sample_cases import load_sample_case
from engine.template_generator import generate_template_case

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

# Initialise Gemini client once at import time.
# If the key is the placeholder string, generation will fail gracefully.
_client = genai.Client(api_key=config.GEMINI_API_KEY)

_generation_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    temperature=1.0,        # High creativity for unique stories
    max_output_tokens=4096,
)


async def generate_case(genre_override: dict | None = None) -> dict:
    """
    Generate and validate a complete murder mystery case.

    Args:
        genre_override: Optional genre context dict (for future custom settings).
                        If None, picks a random genre.

    Returns:
        Validated case dict ready for game injection.

    Raises:
        RuntimeError: If all retries fail.
    """
    if config.TEST_MODE:
        logger.info("TEST_MODE enabled — generating template case (no Gemini call)")
        return generate_template_case()

    genre_ctx = genre_override or pick_random_genre()
    prompt    = build_prompt(genre_ctx)

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await _client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=_generation_config,
            )
            raw_text = response.text.strip()

            # Strip markdown code fences if Gemini wraps the JSON
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            case = json.loads(raw_text)
            case = validate_case(case)

            # Attach genre context so game phases can reference it
            case["_genre_ctx"] = genre_ctx

            # Build a flat clue pool for round reveals
            case["clue_pool"] = [
                case["clues"]["round_1"],
                case["clues"]["round_2"],
                case["clues"]["round_3"],
                case["clues"]["round_4"],
            ]

            logger.info("Case generated successfully on attempt %d", attempt)
            return case

        except Exception as e:
            error_str = str(e)
            # 429 = quota exhausted — retrying immediately won't help
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.error("Gemini quota exhausted: %s", e)
                raise RuntimeError("quota_exhausted")
            last_error = e
            logger.warning("Case generation attempt %d failed: %s", attempt, e)

    raise RuntimeError(
        f"Failed to generate a valid case after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )
