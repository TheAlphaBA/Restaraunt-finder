"""
Tests for the Prompt Builder module.

Covers:
- Prompt contains all user preference fields
- Restaurant list formatting
- Extras included in prompt when provided
"""

import pandas as pd
import pytest

from app.models import UserPreferences
from app.prompt_builder import build_prompt, format_restaurant_list, build_system_prompt


@pytest.fixture
def sample_prefs():
    """Sample user preferences for testing."""
    return UserPreferences(
        location="koramangala",
        budget_level="medium",
        budget_range=(300, 700),
        cuisine="indian",
        min_rating=3.5,
        extras=["family-friendly", "quick service"]
    )


@pytest.fixture
def sample_prefs_no_extras():
    """Sample user preferences without extras."""
    return UserPreferences(
        location="btm",
        budget_level="low",
        budget_range=(0, 300),
        cuisine="",
        min_rating=3.0
    )


@pytest.fixture
def sample_candidates():
    """Sample filtered restaurant DataFrame."""
    return pd.DataFrame({
        "name": ["Spice Garden", "Dragon Wok", "Pasta Place"],
        "cuisines": ["Indian, Mughlai", "Chinese, Thai", "Italian"],
        "rating": [4.3, 4.1, 3.9],
        "cost": [400, 350, 500],
        "location": ["Koramangala", "Koramangala", "Koramangala"],
        "rest_type": ["Casual Dining", "Quick Bites", "Cafe"]
    })


class TestBuildPrompt:
    """Tests for the build_prompt function."""

    def test_returns_tuple_of_two_strings(self, sample_prefs, sample_candidates):
        system, user = build_prompt(sample_prefs, sample_candidates)
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_contains_json_schema(self):
        system = build_system_prompt()
        assert "JSON" in system
        assert '"rank"' in system
        assert '"name"' in system
        assert '"cuisine"' in system
        assert '"rating"' in system
        assert '"estimated_cost"' in system
        assert '"explanation"' in system

    def test_user_prompt_contains_location(self, sample_prefs, sample_candidates):
        _, user = build_prompt(sample_prefs, sample_candidates)
        assert "Koramangala" in user  # .title() of "koramangala"

    def test_user_prompt_contains_budget(self, sample_prefs, sample_candidates):
        _, user = build_prompt(sample_prefs, sample_candidates)
        assert "Medium" in user
        assert "300" in user
        assert "700" in user

    def test_user_prompt_contains_cuisine(self, sample_prefs, sample_candidates):
        _, user = build_prompt(sample_prefs, sample_candidates)
        assert "Indian" in user

    def test_user_prompt_contains_min_rating(self, sample_prefs, sample_candidates):
        _, user = build_prompt(sample_prefs, sample_candidates)
        assert "3.5" in user

    def test_user_prompt_contains_extras(self, sample_prefs, sample_candidates):
        _, user = build_prompt(sample_prefs, sample_candidates)
        assert "family-friendly" in user
        assert "quick service" in user

    def test_user_prompt_no_extras_shows_none(self, sample_prefs_no_extras, sample_candidates):
        _, user = build_prompt(sample_prefs_no_extras, sample_candidates)
        assert "None" in user

    def test_user_prompt_empty_cuisine_shows_any(self, sample_prefs_no_extras, sample_candidates):
        _, user = build_prompt(sample_prefs_no_extras, sample_candidates)
        assert "Any" in user


class TestFormatRestaurantList:
    """Tests for restaurant list formatting."""

    def test_all_restaurants_included(self, sample_candidates):
        result = format_restaurant_list(sample_candidates)
        assert "Spice Garden" in result
        assert "Dragon Wok" in result
        assert "Pasta Place" in result

    def test_numbered_correctly(self, sample_candidates):
        result = format_restaurant_list(sample_candidates)
        assert result.startswith("1.")
        assert "2." in result
        assert "3." in result

    def test_includes_key_fields(self, sample_candidates):
        result = format_restaurant_list(sample_candidates)
        assert "Cuisine:" in result
        assert "Rating:" in result
        assert "Cost:" in result
        assert "Area:" in result

    def test_includes_rest_type(self, sample_candidates):
        result = format_restaurant_list(sample_candidates)
        assert "Type: Casual Dining" in result

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["name", "cuisines", "rating", "cost", "location"])
        result = format_restaurant_list(empty_df)
        assert result == ""
