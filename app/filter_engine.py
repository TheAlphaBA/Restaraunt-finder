"""
Filter Engine — applies sequential filters to the preprocessed DataFrame
based on user preferences.

Filter pipeline:
1. Location (fuzzy substring match on location_norm)
2. Cuisine (partial match on cuisines_norm, optional)
3. Budget range (cost between min and max)
4. Minimum rating (rating >= threshold)

Fallback strategy (when strict filtering returns < 3 results):
1. Relax cuisine filter → return top results by rating in the location
2. Relax budget range by ±₹200
3. Return whatever is available with a flag indicating relaxed filters
"""

import pandas as pd

from app.models import UserPreferences


def filter_restaurants(
    df: pd.DataFrame,
    prefs: UserPreferences,
    max_candidates: int = 15,
) -> pd.DataFrame:
    """Apply sequential filters to the preprocessed DataFrame.

    Args:
        df: Preprocessed Zomato DataFrame (must contain location_norm,
            cuisines_norm, cost, rating columns).
        prefs: Validated UserPreferences object.
        max_candidates: Maximum number of restaurant candidates to return.

    Returns:
        Filtered DataFrame sorted by rating descending, limited to
        max_candidates rows. May be empty if no restaurants match even
        after fallback relaxation.
    """
    result = df.copy()

    # --- Filter 1: Location (fuzzy substring match) ---
    result = result[
        result["location_norm"].str.contains(prefs.location, na=False)
    ]

    if result.empty:
        return result.head(0)  # No point continuing if location yields nothing

    # --- Filter 2: Cuisine (partial match, optional) ---
    if prefs.cuisine:
        cuisine_filtered = result[
            result["cuisines_norm"].str.contains(prefs.cuisine, na=False)
        ]
    else:
        cuisine_filtered = result

    # --- Filter 3: Budget range ---
    min_cost, max_cost = prefs.budget_range
    budget_filtered = cuisine_filtered[
        cuisine_filtered["cost"].between(min_cost, max_cost)
    ]

    # --- Filter 4: Minimum rating ---
    rating_filtered = budget_filtered[
        budget_filtered["rating"] >= prefs.min_rating
    ]

    # --- Sort by rating descending ---
    strict_result = rating_filtered.sort_values("rating", ascending=False)

    # --- Fallback strategy if strict filtering returns fewer than 3 results ---
    if len(strict_result) >= 3:
        return strict_result.head(max_candidates)

    # Fallback 1: Relax cuisine filter (keep location + budget + rating)
    fallback_1 = result[
        result["cost"].between(min_cost, max_cost)
        & (result["rating"] >= prefs.min_rating)
    ].sort_values("rating", ascending=False)

    if len(fallback_1) >= 3:
        return fallback_1.head(max_candidates)

    # Fallback 2: Relax budget range by ±₹200 (keep location + rating)
    relaxed_min = max(0, min_cost - 200)
    relaxed_max = max_cost + 200
    fallback_2 = result[
        result["cost"].between(relaxed_min, relaxed_max)
        & (result["rating"] >= prefs.min_rating)
    ].sort_values("rating", ascending=False)

    if len(fallback_2) >= 3:
        return fallback_2.head(max_candidates)

    # Fallback 3: Return top results by rating in the location only
    fallback_3 = result.sort_values("rating", ascending=False)
    return fallback_3.head(max_candidates)
