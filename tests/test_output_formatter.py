"""
Tests for the Output Formatter module.

Covers:
- Parsing of valid JSON response
- Fallback for malformed JSON
- Ranking order of output cards
- Edge cases (empty responses, missing fields)
"""

import json
import pytest

from app.models import RecommendationCard
from app.output_formatter import parse_llm_response, parse_with_fallback


@pytest.fixture
def valid_response():
    """A well-formed LLM JSON response."""
    return {
        "recommendations": [
            {
                "rank": 2,
                "name": "Dragon Wok",
                "cuisine": "Chinese, Thai",
                "rating": 4.1,
                "estimated_cost": "₹350 for two",
                "explanation": "Great Chinese food at an affordable price."
            },
            {
                "rank": 1,
                "name": "Spice Garden",
                "cuisine": "Indian, Mughlai",
                "rating": 4.3,
                "estimated_cost": "₹400 for two",
                "explanation": "Perfect match for Indian cuisine lovers."
            },
            {
                "rank": 3,
                "name": "Pasta Place",
                "cuisine": "Italian",
                "rating": 3.9,
                "estimated_cost": "₹500 for two",
                "explanation": "Good Italian option within budget."
            }
        ]
    }


@pytest.fixture
def valid_json_text(valid_response):
    """Valid JSON as a string."""
    return json.dumps(valid_response)


class TestParseLLMResponse:
    """Tests for parse_llm_response with already-parsed dict input."""

    def test_parses_valid_response(self, valid_response):
        cards = parse_llm_response(valid_response)
        assert len(cards) == 3

    def test_all_cards_are_recommendation_type(self, valid_response):
        cards = parse_llm_response(valid_response)
        assert all(isinstance(c, RecommendationCard) for c in cards)

    def test_sorted_by_rank(self, valid_response):
        cards = parse_llm_response(valid_response)
        ranks = [c.rank for c in cards]
        assert ranks == [1, 2, 3]

    def test_first_card_is_spice_garden(self, valid_response):
        cards = parse_llm_response(valid_response)
        assert cards[0].name == "Spice Garden"
        assert cards[0].rank == 1
        assert cards[0].rating == 4.3

    def test_empty_recommendations(self):
        cards = parse_llm_response({"recommendations": []})
        assert cards == []

    def test_missing_recommendations_key(self):
        cards = parse_llm_response({"data": []})
        assert cards == []

    def test_missing_fields_use_defaults(self):
        response = {
            "recommendations": [
                {"rank": 1, "name": "Test"}
            ]
        }
        cards = parse_llm_response(response)
        assert len(cards) == 1
        assert cards[0].cuisine == ""
        assert cards[0].rating == 0.0
        assert cards[0].estimated_cost == ""
        assert cards[0].explanation == ""


class TestParseWithFallback:
    """Tests for parse_with_fallback with raw text input."""

    def test_parses_clean_json(self, valid_json_text):
        cards = parse_with_fallback(valid_json_text)
        assert len(cards) == 3
        assert cards[0].rank == 1

    def test_parses_json_with_markdown_fences(self, valid_json_text):
        wrapped = f"```json\n{valid_json_text}\n```"
        cards = parse_with_fallback(wrapped)
        assert len(cards) == 3

    def test_parses_json_with_plain_fences(self, valid_json_text):
        wrapped = f"```\n{valid_json_text}\n```"
        cards = parse_with_fallback(wrapped)
        assert len(cards) == 3

    def test_handles_completely_invalid_text(self):
        cards = parse_with_fallback("I'm sorry, I can't help with that.")
        assert cards == []

    def test_handles_empty_string(self):
        cards = parse_with_fallback("")
        assert cards == []

    def test_ranking_order_preserved(self, valid_json_text):
        cards = parse_with_fallback(valid_json_text)
        for i, card in enumerate(cards):
            assert card.rank == i + 1
