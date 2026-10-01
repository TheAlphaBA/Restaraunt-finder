"""
Input Handler — validates and normalizes raw user inputs into a UserPreferences object.

Validation rules:
- Location is required (non-empty string).
- Budget level must be a key in the configured budget_ranges dict.
- Minimum rating must be between 0.0 and 5.0.
- Cuisine and extras are optional; cuisine defaults to empty string (any).
"""

from app.models import UserPreferences


def build_user_preferences(
    location: str,
    budget_level: str,
    cuisine: str,
    min_rating: float,
    extras: list[str],
    budget_ranges: dict,
) -> UserPreferences:
    """Validate raw user inputs and build a UserPreferences object.

    Args:
        location: City or area name (e.g., "Bangalore", "Koramangala").
        budget_level: One of the keys in budget_ranges (e.g., "low", "medium", "high").
        cuisine: Desired cuisine type (e.g., "indian", "chinese"). Empty string means any.
        min_rating: Minimum acceptable aggregate rating (0.0–5.0).
        extras: Optional list of additional preferences (e.g., ["family-friendly"]).
        budget_ranges: Dict mapping budget level names to [min, max] cost ranges.
                       e.g., {"low": [0, 300], "medium": [300, 700], "high": [700, 9999]}

    Returns:
        A validated UserPreferences instance with normalized fields.

    Raises:
        ValueError: If any input fails validation.
    """
    # --- Validate location ---
    if not isinstance(location, str) or not location.strip():
        raise ValueError("Location is required and must be a non-empty string.")

    # --- Validate budget level ---
    if budget_level not in budget_ranges:
        valid_levels = list(budget_ranges.keys())
        raise ValueError(
            f"Budget must be one of: {valid_levels}. Got '{budget_level}'."
        )

    # --- Validate min_rating ---
    try:
        min_rating = float(min_rating)
    except (ValueError, TypeError):
        raise ValueError("Minimum rating must be a number between 0 and 5.")

    if not 0 <= min_rating <= 5:
        raise ValueError(
            f"Rating must be between 0 and 5. Got {min_rating}."
        )

    # --- Normalize & build ---
    budget_range = tuple(budget_ranges[budget_level])

    return UserPreferences(
        location=location.strip().lower(),
        budget_level=budget_level,
        budget_range=budget_range,
        cuisine=cuisine.strip().lower() if cuisine else "",
        min_rating=min_rating,
        extras=extras if extras else [],
    )
