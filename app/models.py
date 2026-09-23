"""
Core data models for the Restaurant Recommendation System.

Defines the shared dataclasses used across all modules:
- UserPreferences: Encapsulates validated user input
- RecommendationCard: Represents a single restaurant recommendation from the LLM
"""

from dataclasses import dataclass, field


@dataclass
class UserPreferences:
    """Structured representation of a user's restaurant search criteria.

    Attributes:
        location: Normalized (lowercase, stripped) city or area name.
        budget_level: One of "low", "medium", or "high".
        budget_range: Numeric (min_cost, max_cost) tuple derived from budget_level.
        cuisine: Normalized cuisine type (e.g., "indian", "chinese"). Empty string means any.
        min_rating: Minimum acceptable aggregate rating (0.0–5.0).
        extras: Optional list of additional preferences (e.g., ["family-friendly", "quick service"]).
    """
    location: str
    budget_level: str           # "low" | "medium" | "high"
    budget_range: tuple         # (min_cost, max_cost)
    cuisine: str
    min_rating: float
    extras: list[str] = field(default_factory=list)


@dataclass
class RecommendationCard:
    """A single restaurant recommendation returned by the LLM.

    Attributes:
        rank: Position in the ranked list (1 = best match).
        name: Restaurant name.
        cuisine: Cuisine type(s).
        rating: Aggregate rating (0.0–5.0).
        estimated_cost: Human-readable cost string (e.g., "₹400 for two").
        explanation: AI-generated explanation of why this restaurant fits the user's needs.
    """
    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
