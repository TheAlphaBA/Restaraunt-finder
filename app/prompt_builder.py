"""
Prompt Builder — constructs system + user prompts from user preferences
and filtered restaurant candidates for the LLM.

Builds a structured prompt (v4) that includes:
- System instruction with JSON output schema
- User preferences context
- Formatted restaurant candidate list
- Ranking and reasoning instructions
"""

from typing import Tuple

import pandas as pd

from app.models import UserPreferences


def format_restaurant_list(candidates: pd.DataFrame) -> str:
    """Format the filtered restaurant DataFrame into a numbered text list.

    Args:
        candidates: Filtered DataFrame with restaurant data.

    Returns:
        Formatted string listing each restaurant with key details.
    """
    lines = []
    for i, (_, row) in enumerate(candidates.iterrows()):
        line = (
            f"{i+1}. Restaurant: {row['name']} | "
            f"Cuisine: {row['cuisines']} | "
            f"Rating: {row['rating']} | "
            f"Cost: ₹{row['cost']} for two | "
            f"Area: {row['location']}"
        )
        # Include restaurant type if available
        if "rest_type" in row and pd.notna(row.get("rest_type")):
            line += f" | Type: {row['rest_type']}"
        lines.append(line)

    return "\n".join(lines)


def build_system_prompt() -> str:
    """Build the system prompt with JSON output schema and ranking instructions.

    Returns:
        System prompt string.
    """
    return (
        "You are an expert restaurant recommendation assistant. "
        "Given a list of restaurants and user preferences, rank the top 5 "
        "restaurants that best match the user's needs.\n\n"
        "For each restaurant, provide a 2-3 sentence explanation of why it "
        "fits the user's preferences, considering location, cuisine match, "
        "budget fit, rating quality, and any additional preferences.\n\n"
        "Return your response ONLY as valid JSON matching this exact schema "
        "(no markdown, no code fences, no extra text):\n"
        '{"recommendations": [\n'
        '  {\n'
        '    "rank": 1,\n'
        '    "name": "Restaurant Name",\n'
        '    "cuisine": "Cuisine Type",\n'
        '    "rating": 4.5,\n'
        '    "estimated_cost": "₹X for two",\n'
        '    "explanation": "Why this restaurant is a good match..."\n'
        '  }\n'
        ']}'
    )


def build_user_prompt(prefs: UserPreferences, candidates: pd.DataFrame) -> str:
    """Build the user prompt from preferences and filtered candidates.

    Args:
        prefs: Validated user preferences.
        candidates: Filtered restaurant DataFrame.

    Returns:
        User prompt string.
    """
    restaurant_list = format_restaurant_list(candidates)

    return (
        f"User Preferences:\n"
        f"- Location: {prefs.location.title()}\n"
        f"- Budget: {prefs.budget_level.title()} "
        f"(₹{prefs.budget_range[0]}–₹{prefs.budget_range[1]} for two)\n"
        f"- Cuisine: {prefs.cuisine.title() if prefs.cuisine else 'Any'}\n"
        f"- Minimum Rating: {prefs.min_rating}\n"
        f"- Additional Preferences: "
        f"{', '.join(prefs.extras) if prefs.extras else 'None'}\n\n"
        f"Available Restaurants:\n"
        f"{restaurant_list}\n\n"
        f"Rank the top 5 restaurants and explain why each one fits the user's needs."
    )


def build_prompt(prefs: UserPreferences, candidates: pd.DataFrame) -> Tuple[str, str]:
    """Build complete system + user prompts for the LLM.

    Args:
        prefs: Validated user preferences.
        candidates: Filtered restaurant DataFrame.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(prefs, candidates)
    return system_prompt, user_prompt
