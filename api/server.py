"""
FastAPI backend for the AI Restaurant Recommendation System.
Wraps existing Streamlit backend modules as REST API endpoints.

Run with: uvicorn api.server:app --reload --port 8000
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import yaml

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `app.*` imports work.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.data_loader import load_zomato_data
from app.filter_engine import filter_restaurants
from app.input_handler import build_user_preferences
from app.llm_client import call_llm
from app.output_formatter import parse_llm_response
from app.preprocessor import preprocess
from app.prompt_builder import build_prompt

# ---------------------------------------------------------------------------
# Environment & Config
# ---------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.yaml")
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

# ---------------------------------------------------------------------------
# In-memory dataset cache
# ---------------------------------------------------------------------------
dataset_cache: dict = {}


# ---------------------------------------------------------------------------
# Lifespan — load dataset on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load and preprocess the Zomato dataset on server startup."""
    logger.info("Loading Zomato dataset on startup...")
    try:
        parquet_path = config["data"].get("local_parquet")
        if parquet_path and not os.path.isabs(parquet_path):
            parquet_path = os.path.join(PROJECT_ROOT, parquet_path)

        raw_df = load_zomato_data(
            config["data"]["dataset_name"],
            config["data"]["cache_dir"],
            local_parquet=parquet_path,
        )
        if "location_norm" in raw_df.columns and "budget_level" in raw_df.columns:
            dataset_cache["df"] = raw_df
        else:
            dataset_cache["df"] = preprocess(raw_df, config["budget_ranges"])

        logger.info(f"Dataset ready: {len(dataset_cache['df'])} restaurants loaded")
    except Exception as e:
        logger.error(f"Failed to load dataset on startup: {e}")
    yield
    # Shutdown: nothing to clean up
    logger.info("Server shutting down")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Restaurant Recommender API",
    version="1.0.0",
    description="Backend API for restaurant recommendations powered by Groq LLM",
    lifespan=lifespan,
)

# CORS — allow Vercel frontend, preview domains, and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Models (Pydantic)
# ---------------------------------------------------------------------------
class RecommendationRequest(BaseModel):
    """User preferences for restaurant search."""
    location: str = Field(..., min_length=1, description="City area or neighbourhood name")
    cuisine: str = Field(default="", description="Cuisine type (empty = any)")
    budget_level: str = Field(default="medium", description="One of: low, medium, high")
    min_rating: float = Field(default=3.5, ge=0.0, le=5.0, description="Minimum rating (0-5)")
    extras: list[str] = Field(default_factory=list, description="Additional preferences")


class RestaurantCardResponse(BaseModel):
    """A single restaurant recommendation."""
    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str


class RecommendationResponse(BaseModel):
    """Full recommendation response."""
    recommendations: list[RestaurantCardResponse]
    candidates_found: int
    filters_applied: dict


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment monitoring."""
    return {
        "status": "healthy",
        "dataset_loaded": "df" in dataset_cache,
        "restaurant_count": len(dataset_cache.get("df", [])),
    }


@app.get("/api/locations")
async def get_locations():
    """Return unique location values for the frontend dropdown."""
    df = dataset_cache.get("df")
    if df is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded yet")

    locations = sorted(df["location"].dropna().unique().tolist())
    return {"locations": locations, "count": len(locations)}


@app.get("/api/cuisines")
async def get_cuisines():
    """Return unique cuisine values for the frontend dropdown."""
    df = dataset_cache.get("df")
    if df is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded yet")

    all_cuisines = set()
    for val in df["cuisines"].dropna():
        for c in str(val).split(","):
            c = c.strip()
            if c:
                all_cuisines.add(c)
    return {"cuisines": sorted(all_cuisines), "count": len(all_cuisines)}


@app.get("/api/budget-levels")
async def get_budget_levels():
    """Return available budget levels and their ranges."""
    return {"budget_levels": config["budget_ranges"]}


@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend(req: RecommendationRequest):
    """Main recommendation endpoint — filters data + calls Groq LLM.

    Pipeline:
    1. Validate user preferences via input_handler
    2. Filter restaurants via filter_engine
    3. Build prompt via prompt_builder
    4. Call LLM via llm_client
    5. Parse response via output_formatter
    """
    df = dataset_cache.get("df")
    if df is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded yet")

    # --- 1. Validate & build user preferences ---
    try:
        prefs = build_user_preferences(
            location=req.location,
            budget_level=req.budget_level,
            cuisine=req.cuisine,
            min_rating=req.min_rating,
            extras=req.extras,
            budget_ranges=config["budget_ranges"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- 2. Filter restaurants ---
    candidates = filter_restaurants(
        df, prefs,
        max_candidates=config["data"].get("max_candidates", 15),
    )
    candidates_count = len(candidates)

    if candidates_count == 0:
        return RecommendationResponse(
            recommendations=[],
            candidates_found=0,
            filters_applied={
                "location": prefs.location,
                "budget_level": prefs.budget_level,
                "cuisine": prefs.cuisine or "any",
                "min_rating": prefs.min_rating,
            },
        )

    # --- 3. Build prompt ---
    system_prompt, user_prompt = build_prompt(prefs, candidates)

    # --- 4. Call LLM ---
    try:
        llm_response = call_llm(system_prompt, user_prompt, config)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=f"LLM service error: {e}")

    # --- 5. Parse response ---
    cards = parse_llm_response(llm_response)

    return RecommendationResponse(
        recommendations=[
            RestaurantCardResponse(
                rank=card.rank,
                name=card.name,
                cuisine=card.cuisine,
                rating=card.rating,
                estimated_cost=card.estimated_cost,
                explanation=card.explanation,
            )
            for card in cards
        ],
        candidates_found=candidates_count,
        filters_applied={
            "location": prefs.location,
            "budget_level": prefs.budget_level,
            "cuisine": prefs.cuisine or "any",
            "min_rating": prefs.min_rating,
        },
    )
