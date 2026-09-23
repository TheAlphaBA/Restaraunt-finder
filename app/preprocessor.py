"""
Preprocessor — cleans, normalizes, and transforms the raw Zomato DataFrame.

Applies 7 sequential cleaning steps:
1. Drop duplicate rows
2. Drop rows with missing core fields
3. Parse rating (handle "NEW", "-", "/5" suffix)
4. Parse cost (remove commas, cast to int)
5. Normalize text (lowercase location and cuisines)
6. Encode budget level (map numeric cost → low/medium/high)
7. Reset index
"""

from typing import Optional

import pandas as pd


def parse_rating(value) -> Optional[float]:
    """Convert raw rating string to float.

    Handles formats like "4.1/5", "NEW", "-", NaN.

    Args:
        value: Raw rating value from the dataset.

    Returns:
        Parsed float rating (0.0–5.0), or None if unparseable.
    """
    if pd.isna(value):
        return None

    value = str(value).strip()

    # Handle known non-numeric values
    if value.upper() in ("NEW", "-", "", "NAN"):
        return None

    # Remove "/5" suffix if present
    value = value.replace("/5", "").strip()

    try:
        rating = float(value)
        if 0.0 <= rating <= 5.0:
            return rating
        return None
    except (ValueError, TypeError):
        return None


def parse_cost(value) -> Optional[int]:
    """Convert raw cost string to integer.

    Handles formats like "400", "1,200", etc.

    Args:
        value: Raw cost value from the dataset.

    Returns:
        Parsed integer cost, or None if unparseable.
    """
    if pd.isna(value):
        return None

    value = str(value).strip().replace(",", "")

    try:
        cost = int(float(value))
        return cost if cost > 0 else None
    except (ValueError, TypeError):
        return None


def encode_budget(cost: int, budget_ranges: dict) -> Optional[str]:
    """Map a numeric cost to a budget level category.

    Args:
        cost: Numeric cost value (cost for two in INR).
        budget_ranges: Dict mapping level names to [min, max] ranges.
                       e.g., {"low": [0, 300], "medium": [300, 700], "high": [700, 9999]}

    Returns:
        Budget level string ("low", "medium", or "high"), or None if no range matches.
    """
    if cost is None:
        return None

    for level, (min_cost, max_cost) in budget_ranges.items():
        if min_cost <= cost <= max_cost:
            return level

    return None


def preprocess(df: pd.DataFrame, budget_ranges: dict) -> pd.DataFrame:
    """Apply all 7 cleaning steps to the raw Zomato DataFrame.

    Args:
        df: Raw DataFrame from the dataset loader.
        budget_ranges: Dict mapping budget level names to [min, max] cost ranges.

    Returns:
        Cleaned DataFrame with parsed rating, cost, normalized text,
        and budget_level columns. No nulls in core fields.
    """
    print(f"📊 Raw dataset: {len(df)} records")

    # Step 1: Drop duplicate rows
    df = df.drop_duplicates()
    print(f"   Step 1 — Drop duplicates: {len(df)} records")

    # Step 2: Drop rows with missing core fields
    core_fields = ["name", "location", "cuisines", "rate",
                   "approx_cost(for two people)"]
    # Only drop on columns that exist in the dataframe
    existing_core = [col for col in core_fields if col in df.columns]
    df = df.dropna(subset=existing_core)
    print(f"   Step 2 — Drop nulls in core fields: {len(df)} records")

    # Step 3: Parse rating
    if "rate" in df.columns:
        df = df.copy()
        df["rating"] = df["rate"].apply(parse_rating)
        # Drop rows where rating couldn't be parsed
        df = df.dropna(subset=["rating"])
        df["rating"] = df["rating"].astype(float)
        print(f"   Step 3 — Parse rating: {len(df)} records")

    # Step 4: Parse cost
    if "approx_cost(for two people)" in df.columns:
        df["cost"] = df["approx_cost(for two people)"].apply(parse_cost)
        # Drop rows where cost couldn't be parsed
        df = df.dropna(subset=["cost"])
        df["cost"] = df["cost"].astype(int)
        print(f"   Step 4 — Parse cost: {len(df)} records")

    # Step 5: Normalize text fields
    if "location" in df.columns:
        df["location_norm"] = df["location"].str.lower().str.strip()
    if "cuisines" in df.columns:
        df["cuisines_norm"] = df["cuisines"].str.lower().str.strip()
    print(f"   Step 5 — Normalize text: done")

    # Step 6: Encode budget level
    df["budget_level"] = df["cost"].apply(
        lambda x: encode_budget(x, budget_ranges)
    )
    # Drop rows that don't fall into any budget range
    df = df.dropna(subset=["budget_level"])
    print(f"   Step 6 — Encode budget: {len(df)} records")

    # Step 7: Reset index
    df = df.reset_index(drop=True)
    print(f"   Step 7 — Reset index: done")
    print(f"✅ Cleaned dataset: {len(df)} records")

    return df


def validate(df: pd.DataFrame) -> bool:
    """Validate the preprocessed DataFrame.

    Checks that:
    - All ratings are between 0 and 5
    - All costs are positive
    - All budget levels are valid

    Args:
        df: Preprocessed DataFrame.

    Returns:
        True if all validations pass.

    Raises:
        AssertionError: If any validation fails.
    """
    assert df["rating"].between(0, 5).all(), \
        "Found ratings outside 0–5 range"
    assert df["cost"].gt(0).all(), \
        "Found non-positive cost values"
    assert df["budget_level"].isin(["low", "medium", "high"]).all(), \
        "Found invalid budget levels"
    assert df["location_norm"].notna().all(), \
        "Found null location_norm values"
    assert df["cuisines_norm"].notna().all(), \
        "Found null cuisines_norm values"

    print("✅ All validations passed")
    return True
