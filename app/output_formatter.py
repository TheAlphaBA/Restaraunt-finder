"""
Output Formatter — parses LLM JSON response into RecommendationCard objects.

Includes:
- Primary JSON parser for well-formed LLM output
- Regex fallback parser for malformed JSON
"""

import json
import re
import logging
from typing import List

from app.models import RecommendationCard

logger = logging.getLogger(__name__)


def parse_llm_response(raw_response: dict) -> List[RecommendationCard]:
    """Parse a well-formed LLM JSON response into RecommendationCard objects.

    Args:
        raw_response: Parsed JSON dict with a "recommendations" key containing
                      a list of recommendation objects.

    Returns:
        List of RecommendationCard objects, sorted by rank.
    """
    cards = []
    recommendations = raw_response.get("recommendations", [])

    if not recommendations:
        logger.warning("LLM response contains no recommendations")
        return cards

    for item in recommendations:
        try:
            card = RecommendationCard(
                rank=int(item.get("rank", 0)),
                name=str(item.get("name", "Unknown")),
                cuisine=str(item.get("cuisine", "")),
                rating=float(item.get("rating", 0.0)),
                estimated_cost=str(item.get("estimated_cost", "")),
                explanation=str(item.get("explanation", ""))
            )
            cards.append(card)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed recommendation item: {e}")
            continue

    return sorted(cards, key=lambda c: c.rank)


def _extract_json_from_text(raw_text: str) -> dict:
    """Try to extract JSON from potentially malformed text.

    Handles common LLM quirks:
    - Markdown code fences (```json ... ```)
    - Trailing commas
    - Extra text before/after JSON

    Args:
        raw_text: Raw text that may contain JSON.

    Returns:
        Parsed JSON dict.

    Raises:
        json.JSONDecodeError: If no valid JSON can be extracted.
    """
    text = raw_text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


def _regex_fallback_parse(raw_text: str) -> List[RecommendationCard]:
    """Last-resort regex parser for completely malformed LLM output.

    Attempts to extract restaurant recommendations using pattern matching
    when JSON parsing fails entirely.

    Args:
        raw_text: Raw LLM response text.

    Returns:
        List of RecommendationCard objects extracted via regex.
    """
    cards = []

    # Pattern: look for numbered items with restaurant details
    pattern = re.compile(
        r'(?:^|\n)\s*#?(\d+)[.\)]\s*'          # rank
        r'(?:\*\*)?(.+?)(?:\*\*)?\s*\n'         # name
        r'.*?[Cc]uisine[:\s]+(.+?)\n'           # cuisine
        r'.*?[Rr]ating[:\s]+(\d+\.?\d*)',        # rating
        re.MULTILINE | re.DOTALL
    )

    for match in pattern.finditer(raw_text):
        try:
            cards.append(RecommendationCard(
                rank=int(match.group(1)),
                name=match.group(2).strip(),
                cuisine=match.group(3).strip(),
                rating=float(match.group(4)),
                estimated_cost="N/A",
                explanation="(Extracted from non-JSON response)"
            ))
        except (ValueError, IndexError):
            continue

    if cards:
        logger.info(f"Regex fallback extracted {len(cards)} recommendations")

    return sorted(cards, key=lambda c: c.rank)


def parse_with_fallback(raw_text: str) -> List[RecommendationCard]:
    """Parse LLM response text with JSON-first, regex-fallback strategy.

    Attempts:
    1. Direct JSON parsing
    2. JSON extraction from mixed text
    3. Regex pattern matching as last resort

    Args:
        raw_text: Raw text response from the LLM.

    Returns:
        List of RecommendationCard objects. May be empty if all parsing fails.
    """
    # Attempt 1: Parse as JSON
    try:
        data = _extract_json_from_text(raw_text)
        cards = parse_llm_response(data)
        if cards:
            return cards
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"JSON parsing failed: {e}")

    # Attempt 2: Regex fallback
    logger.warning("Falling back to regex extraction")
    cards = _regex_fallback_parse(raw_text)

    if not cards:
        logger.error("All parsing methods failed — no recommendations extracted")

    return cards
