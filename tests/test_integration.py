import pytest
import pandas as pd

from app.models import UserPreferences, RecommendationCard
from app.input_handler import build_user_preferences
from app.filter_engine import filter_restaurants
from app.prompt_builder import build_prompt
from app.output_formatter import parse_llm_response

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Spice Garden", "Dragon Wok", "Truffles"],
        "location": ["Koramangala", "Koramangala", "Koramangala"],
        "location_norm": ["koramangala", "koramangala", "koramangala"],
        "cuisines": ["North Indian", "Chinese", "American, Burger"],
        "cuisines_norm": ["north indian", "chinese", "american, burger"],
        "cost": [600, 400, 800],
        "rating": [4.3, 4.0, 4.5],
        "budget_level": ["medium", "medium", "high"],
        "rest_type": ["Casual Dining", "Quick Bites", "Cafe"]
    })

@pytest.fixture
def mock_llm_response():
    return {
        "recommendations": [
            {
                "rank": 1,
                "name": "Spice Garden",
                "cuisine": "North Indian",
                "rating": 4.3,
                "estimated_cost": "₹600 for two",
                "explanation": "Perfect match for Indian cuisine in Koramangala."
            }
        ]
    }

def test_full_pipeline_integration(sample_df, mock_llm_response):
    """End-to-end integration test of the logic pipeline with a mocked LLM."""
    budget_ranges = {
        "low": [0, 300],
        "medium": [300, 700],
        "high": [700, 9999]
    }
    
    # 1. User Input Handling
    prefs = build_user_preferences(
        location="koramangala", 
        budget_level="medium", 
        cuisine="indian", 
        min_rating=3.5, 
        extras=[], 
        budget_ranges=budget_ranges
    )
    
    # 2. Filter Engine
    candidates = filter_restaurants(sample_df, prefs)
    assert not candidates.empty
    
    # 3. Prompt Building
    system_prompt, user_prompt = build_prompt(prefs, candidates)
    assert "Koramangala" in user_prompt
    assert "Spice Garden" in user_prompt
    
    # 4. LLM response parsing (Mocked)
    cards = parse_llm_response(mock_llm_response)
    
    # Assertions
    assert len(cards) == 1
    assert all(isinstance(c, RecommendationCard) for c in cards)
    assert cards[0].name == "Spice Garden"
    assert cards[0].rank == 1
