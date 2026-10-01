"""
Tests for the Filter Engine and Input Handler modules (Phase 3).

Covers:
- Input handler: validation, normalization, edge cases
- Location filter with valid and invalid inputs
- Cuisine filter with partial match
- Budget range boundaries
- Min rating filter
- Fallback when few/no results found
- End-to-end: raw input → filtered DataFrame
"""

import pytest
import pandas as pd

from app.models import UserPreferences
from app.input_handler import build_user_preferences
from app.filter_engine import filter_restaurants


# ---------------------------------------------------------------------------
# Fixtures: shared test data
# ---------------------------------------------------------------------------

BUDGET_RANGES = {
    "low": [0, 300],
    "medium": [300, 700],
    "high": [700, 9999],
}


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a small preprocessed DataFrame that mimics the real pipeline output."""
    data = {
        "name": [
            "Tandoori Palace",
            "Noodle Box",
            "Curry Corner",
            "The Pizza Hub",
            "Biryani House",
            "Sushi Lane",
            "Dosa Camp",
            "Burger Point",
        ],
        "location": [
            "Koramangala",
            "Indiranagar",
            "Koramangala",
            "Koramangala",
            "Jayanagar",
            "Koramangala",
            "Koramangala",
            "MG Road",
        ],
        "cuisines": [
            "North Indian, Mughlai",
            "Chinese, Thai",
            "South Indian, North Indian",
            "Italian, Pizza",
            "Biryani, North Indian",
            "Japanese, Sushi",
            "South Indian",
            "American, Burger",
        ],
        "location_norm": [
            "koramangala",
            "indiranagar",
            "koramangala",
            "koramangala",
            "jayanagar",
            "koramangala",
            "koramangala",
            "mg road",
        ],
        "cuisines_norm": [
            "north indian, mughlai",
            "chinese, thai",
            "south indian, north indian",
            "italian, pizza",
            "biryani, north indian",
            "japanese, sushi",
            "south indian",
            "american, burger",
        ],
        "cost": [500, 600, 350, 450, 400, 900, 200, 300],
        "rating": [4.2, 4.5, 3.8, 4.0, 4.3, 4.7, 3.5, 3.2],
        "budget_level": [
            "medium", "medium", "medium", "medium",
            "medium", "high", "low", "low",
        ],
    }
    return pd.DataFrame(data)


# ===========================================================================
# INPUT HANDLER TESTS
# ===========================================================================


class TestBuildUserPreferences:
    """Tests for the build_user_preferences function."""

    def test_valid_inputs(self):
        """Happy path — all inputs valid."""
        prefs = build_user_preferences(
            location="Koramangala",
            budget_level="medium",
            cuisine="Indian",
            min_rating=3.5,
            extras=["family-friendly"],
            budget_ranges=BUDGET_RANGES,
        )
        assert prefs.location == "koramangala"
        assert prefs.budget_level == "medium"
        assert prefs.budget_range == (300, 700)
        assert prefs.cuisine == "indian"
        assert prefs.min_rating == 3.5
        assert prefs.extras == ["family-friendly"]

    def test_location_normalised_to_lowercase(self):
        prefs = build_user_preferences(
            "  INDIRANAGAR  ", "low", "chinese", 0.0, [], BUDGET_RANGES,
        )
        assert prefs.location == "indiranagar"

    def test_empty_location_raises(self):
        with pytest.raises(ValueError, match="Location is required"):
            build_user_preferences("", "low", "indian", 3.0, [], BUDGET_RANGES)

    def test_whitespace_only_location_raises(self):
        with pytest.raises(ValueError, match="Location is required"):
            build_user_preferences("   ", "low", "indian", 3.0, [], BUDGET_RANGES)

    def test_invalid_budget_level_raises(self):
        with pytest.raises(ValueError, match="Budget must be one of"):
            build_user_preferences(
                "Bangalore", "ultra", "indian", 3.0, [], BUDGET_RANGES,
            )

    def test_rating_below_zero_raises(self):
        with pytest.raises(ValueError, match="Rating must be between 0 and 5"):
            build_user_preferences(
                "Bangalore", "low", "indian", -1.0, [], BUDGET_RANGES,
            )

    def test_rating_above_five_raises(self):
        with pytest.raises(ValueError, match="Rating must be between 0 and 5"):
            build_user_preferences(
                "Bangalore", "low", "indian", 5.5, [], BUDGET_RANGES,
            )

    def test_empty_cuisine_defaults_to_empty_string(self):
        prefs = build_user_preferences(
            "Bangalore", "low", "", 3.0, [], BUDGET_RANGES,
        )
        assert prefs.cuisine == ""

    def test_none_cuisine_defaults_to_empty_string(self):
        prefs = build_user_preferences(
            "Bangalore", "low", None, 3.0, [], BUDGET_RANGES,
        )
        assert prefs.cuisine == ""

    def test_extras_defaults_to_empty_list(self):
        prefs = build_user_preferences(
            "Bangalore", "low", "indian", 3.0, None, BUDGET_RANGES,
        )
        assert prefs.extras == []

    def test_boundary_rating_zero(self):
        prefs = build_user_preferences(
            "Bangalore", "low", "", 0.0, [], BUDGET_RANGES,
        )
        assert prefs.min_rating == 0.0

    def test_boundary_rating_five(self):
        prefs = build_user_preferences(
            "Bangalore", "low", "", 5.0, [], BUDGET_RANGES,
        )
        assert prefs.min_rating == 5.0


# ===========================================================================
# FILTER ENGINE TESTS
# ===========================================================================


class TestLocationFilter:
    """Tests that the location filter works correctly."""

    def test_returns_only_matching_location(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(300, 700),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        assert all(
            "koramangala" in loc
            for loc in result["location_norm"]
        )

    def test_excludes_non_matching_location(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(300, 700),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        assert "indiranagar" not in result["location_norm"].values
        assert "jayanagar" not in result["location_norm"].values

    def test_invalid_location_returns_empty(self, sample_df):
        prefs = UserPreferences(
            location="nonexistentplace",
            budget_level="medium",
            budget_range=(300, 700),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        assert result.empty


class TestCuisineFilter:
    """Tests for cuisine partial matching."""

    def test_partial_cuisine_match(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="indian",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        assert all(
            "indian" in c for c in result["cuisines_norm"]
        )

    def test_empty_cuisine_returns_all_in_location(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        # Should include all Koramangala restaurants
        koramangala_count = len(
            sample_df[sample_df["location_norm"] == "koramangala"]
        )
        assert len(result) == koramangala_count


class TestBudgetFilter:
    """Tests for budget range filtering."""

    def test_medium_budget_range(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(300, 700),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        # All costs must be within range (or fallback may apply)
        # With enough results in range, strict filter should apply
        for cost in result["cost"]:
            assert 300 <= cost <= 700

    def test_low_budget_includes_cheap_options(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="low",
            budget_range=(0, 300),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        # Dosa Camp (₹200) should be included
        assert "Dosa Camp" in result["name"].values


class TestMinRatingFilter:
    """Tests for minimum rating filtering."""

    def test_all_results_meet_min_rating(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="",
            min_rating=4.0,
        )
        result = filter_restaurants(sample_df, prefs)
        assert all(result["rating"] >= 4.0)

    def test_high_min_rating_narrows_results(self, sample_df):
        prefs_low = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="",
            min_rating=0.0,
        )
        prefs_high = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="",
            min_rating=4.5,
        )
        result_low = filter_restaurants(sample_df, prefs_low)
        result_high = filter_restaurants(sample_df, prefs_high)
        assert len(result_high) <= len(result_low)


class TestSortingAndMaxCandidates:
    """Tests that results are sorted and capped correctly."""

    def test_results_sorted_by_rating_descending(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        ratings = result["rating"].tolist()
        assert ratings == sorted(ratings, reverse=True)

    def test_max_candidates_limit(self, sample_df):
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(0, 9999),
            cuisine="",
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs, max_candidates=2)
        assert len(result) <= 2


class TestFallbackStrategy:
    """Tests that fallback logic kicks in when strict filtering is too narrow."""

    def test_cuisine_relaxation_on_few_results(self, sample_df):
        """When a niche cuisine + location yields < 3, fallback relaxes cuisine."""
        prefs = UserPreferences(
            location="koramangala",
            budget_level="medium",
            budget_range=(300, 700),
            cuisine="japanese",  # Only Sushi Lane (₹900, outside budget)
            min_rating=0.0,
        )
        result = filter_restaurants(sample_df, prefs)
        # Strict filter would give 0 results (japanese + medium budget in
        # koramangala). Fallback 1 relaxes cuisine → should return medium
        # budget restaurants in koramangala.
        assert len(result) >= 3

    def test_budget_relaxation(self):
        """When location + budget yields < 3, budget range is relaxed by ±200."""
        data = {
            "name": ["A", "B", "C", "D"],
            "location_norm": ["area1", "area1", "area1", "area1"],
            "cuisines_norm": ["x", "x", "x", "x"],
            "cost": [250, 260, 270, 400],
            "rating": [4.0, 4.1, 4.2, 3.5],
            "budget_level": ["low", "low", "low", "medium"],
        }
        df = pd.DataFrame(data)
        prefs = UserPreferences(
            location="area1",
            budget_level="medium",
            budget_range=(300, 400),
            cuisine="",
            min_rating=3.0,
        )
        result = filter_restaurants(df, prefs)
        # Strict budget (300–400) yields only D (1 result).
        # Fallback 2 relaxes to (100–600) → picks up A, B, C, D.
        assert len(result) >= 3

    def test_total_fallback_returns_top_by_rating(self):
        """When nothing matches budget or relaxed budget, return top by rating."""
        data = {
            "name": ["A", "B", "C"],
            "location_norm": ["area1", "area1", "area1"],
            "cuisines_norm": ["x", "y", "z"],
            "cost": [5000, 5500, 6000],
            "rating": [4.5, 4.0, 3.5],
            "budget_level": ["high", "high", "high"],
        }
        df = pd.DataFrame(data)
        prefs = UserPreferences(
            location="area1",
            budget_level="low",
            budget_range=(0, 300),
            cuisine="abc",  # matches nothing
            min_rating=4.8,  # too high for any
        )
        result = filter_restaurants(df, prefs)
        # All strict + fallback 1 + fallback 2 fail on rating.
        # Fallback 3 returns top by rating in location regardless.
        assert len(result) == 3
        assert result.iloc[0]["name"] == "A"  # highest rating


# ===========================================================================
# END-TO-END TEST: raw input → UserPreferences → filtered DataFrame
# ===========================================================================


class TestEndToEnd:
    """Integration test: raw user input through to filtered results."""

    def test_full_pipeline(self, sample_df):
        """Raw input → build_user_preferences → filter_restaurants → results."""
        prefs = build_user_preferences(
            location="Koramangala",
            budget_level="medium",
            cuisine="Indian",
            min_rating=3.5,
            extras=["family-friendly"],
            budget_ranges=BUDGET_RANGES,
        )

        result = filter_restaurants(sample_df, prefs, max_candidates=5)

        # Must return a non-empty DataFrame
        assert not result.empty

        # All results should be in Koramangala
        assert all("koramangala" in loc for loc in result["location_norm"])

        # All results should have rating >= 3.5
        assert all(result["rating"] >= 3.5)

        # Results should be sorted by rating descending
        ratings = result["rating"].tolist()
        assert ratings == sorted(ratings, reverse=True)

        # At most 5 candidates
        assert len(result) <= 5

    def test_pipeline_no_matching_location(self, sample_df):
        """Pipeline gracefully returns empty when location has no matches."""
        prefs = build_user_preferences(
            location="Mumbai",
            budget_level="medium",
            cuisine="Indian",
            min_rating=3.0,
            extras=[],
            budget_ranges=BUDGET_RANGES,
        )
        result = filter_restaurants(sample_df, prefs)
        assert result.empty
