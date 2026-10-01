"""
Main entry point for the AI-Powered Restaurant Recommendation System.

Run with: streamlit run app/main.py
"""

import logging
import os
import sys

import streamlit as st
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `app.*` imports work when
# Streamlit is launched from the project root directory.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.data_loader import load_zomato_data          # noqa: E402
from app.filter_engine import filter_restaurants       # noqa: E402
from app.input_handler import build_user_preferences   # noqa: E402
from app.llm_client import call_llm                    # noqa: E402
from app.output_formatter import parse_llm_response    # noqa: E402
from app.preprocessor import preprocess                # noqa: E402
from app.prompt_builder import build_prompt            # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment & Config
# ---------------------------------------------------------------------------
load_dotenv()

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.yaml")
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Restaurant Recommender",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Gastronomic Discovery Engine (Lavender & Rose Theme)
# Adapted from Stitch-generated design system: DESIGN.md
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════════════ */
/*  TYPOGRAPHY — Poppins (headings & body) via Google Fonts               */
/* ═══════════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], [class*="st-"] {
    font-family: 'Poppins', sans-serif;
    color: #201828;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  BASE SURFACE                                                          */
/* ═══════════════════════════════════════════════════════════════════════ */
.stApp {
    background-color: #FFF7FF;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  HIDE DEFAULT STREAMLIT CHROME                                         */
/* ═══════════════════════════════════════════════════════════════════════ */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  HERO / HEADER — Lavender-to-Rose gradient banner                      */
/* ═══════════════════════════════════════════════════════════════════════ */
.hero-header {
    background: linear-gradient(135deg, #F3EFFE 0%, #FDE7F3 50%, #F7E9FF 100%);
    padding: 2.5rem 2.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px -2px rgba(107, 92, 138, 0.08);
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    right: -60px;
    top: -60px;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(252, 121, 189, 0.15), transparent 70%);
    pointer-events: none;
}
.hero-header h1 {
    background: linear-gradient(135deg, #9333EA 0%, #EC4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0 0 0.3rem;
    letter-spacing: -0.5px;
}
.hero-header p {
    color: #6B5C8A;
    font-size: 1.05rem;
    margin: 0;
    font-weight: 400;
    font-style: italic;
}
.hero-header .hero-badges {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 4px 14px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.85);
    color: #534471;
    box-shadow: 0 2px 8px rgba(107, 92, 138, 0.06);
    backdrop-filter: blur(4px);
}
.hero-badge .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
}
.hero-badge .dot-pink { background: #FC79BD; }
.hero-badge .dot-lavender { background: #D0BEF2; }

/* ═══════════════════════════════════════════════════════════════════════ */
/*  SIDEBAR — Soft Lavender tint                                          */
/* ═══════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FBF0FF 0%, #F7E9FF 40%, #F3EFFE 100%) !important;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    color: #534471;
    font-weight: 700;
}
section[data-testid="stSidebar"] label {
    color: #201828 !important;
    font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  INPUT FIELDS — Capsule-style with pink focus rings                    */
/* ═══════════════════════════════════════════════════════════════════════ */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 1.5px solid #E4D9F7 !important;
    background: #FFFFFF !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #F472B6 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(244, 114, 182, 0.15), 0 0 16px rgba(244, 114, 182, 0.1) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    border-radius: 12px !important;
    border: 1.5px solid #E4D9F7 !important;
}

/* Slider track gradient */
.stSlider > div > div > div > div {
    background: linear-gradient(90deg, #6B5C8A, #F472B6) !important;
}

/* Multiselect chips */
.stMultiSelect span[data-baseweb="tag"] {
    background-color: #6B5C8A !important;
    color: #FFFFFF !important;
    border-radius: 9999px !important;
    font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  PRIMARY BUTTON — Pink gradient pill with glow                         */
/* ═══════════════════════════════════════════════════════════════════════ */
.stButton > button, div.stFormSubmitButton > button {
    background: linear-gradient(90deg, #F472B6 0%, #E879A0 100%) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 9999px !important;
    border: none !important;
    padding: 0.65rem 1.75rem !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 14px rgba(244, 114, 182, 0.35) !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover, div.stFormSubmitButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 22px rgba(244, 114, 182, 0.45) !important;
    filter: brightness(1.05) !important;
}
.stButton > button:active, div.stFormSubmitButton > button:active {
    transform: scale(0.98) !important;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  FILTER SUMMARY PILLS                                                  */
/* ═══════════════════════════════════════════════════════════════════════ */
.filter-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    align-items: center;
}
.filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 5px 16px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
    background: #FFFFFF;
    color: #534471;
    border: 1px solid #E4D9F7;
    box-shadow: 0 2px 6px rgba(107, 92, 138, 0.05);
}
.filter-pill-accent {
    background: linear-gradient(135deg, #FFD8E7 0%, #EADDFF 100%);
    color: #534471;
    border: none;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  RECOMMENDATION CARD — Elevated lavender surface                       */
/* ═══════════════════════════════════════════════════════════════════════ */
.rec-card {
    background: #F7E9FF;
    border: 1px solid #E4D9F7;
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(107, 92, 138, 0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.rec-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 28px -4px rgba(107, 92, 138, 0.12),
                0 2px 6px -1px rgba(244, 114, 182, 0.15);
}

/* Rank badge — pink gradient pill */
.rec-card .card-rank {
    display: inline-block;
    background: linear-gradient(90deg, #F472B6 0%, #E879A0 100%);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 0.82rem;
    border-radius: 9999px;
    padding: 4px 16px;
    margin-bottom: 0.6rem;
    box-shadow: 0 2px 8px rgba(244, 114, 182, 0.25);
    letter-spacing: 0.02em;
}

/* Restaurant name */
.rec-card .card-name {
    font-size: 1.35rem;
    font-weight: 700;
    color: #534471;
    margin: 0.3rem 0 0.7rem;
    letter-spacing: -0.01em;
}

/* Metric row */
.rec-card .card-meta {
    display: flex;
    gap: 0;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    background: #FFFFFF;
    border-radius: 14px;
    padding: 0.8rem 1.2rem;
    box-shadow: 0 1px 4px rgba(107, 92, 138, 0.04);
}
.rec-card .card-meta .meta-item {
    flex: 1;
    min-width: 100px;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}
.rec-card .card-meta .meta-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #7A757F;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.rec-card .card-meta .meta-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #201828;
}
.rec-card .card-meta .meta-value.cost-value {
    color: #A43073;
    font-weight: 700;
}

/* AI explanation block */
.rec-card .card-explanation {
    background: #F1E3F9;
    border-left: 4px solid #6B5C8A;
    padding: 0.85rem 1.1rem;
    border-radius: 0 14px 14px 0;
    font-size: 0.9rem;
    color: #201828;
    line-height: 1.6;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}
.rec-card .card-explanation .ai-icon {
    font-size: 1rem;
    flex-shrink: 0;
    margin-top: 2px;
}
.rec-card .card-explanation .ai-label {
    font-weight: 700;
    color: #534471;
    font-size: 0.8rem;
    display: block;
    margin-bottom: 0.15rem;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  INFO / WARNING / ERROR — Themed alerts                                */
/* ═══════════════════════════════════════════════════════════════════════ */
.stAlert [data-baseweb="notification"] {
    border-radius: 14px !important;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  RESULTS HEADER BAR                                                    */
/* ═══════════════════════════════════════════════════════════════════════ */
.results-header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    background: #F7E9FF;
    border-radius: 16px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 8px rgba(107, 92, 138, 0.04);
}
.results-header h3 {
    margin: 0;
    color: #534471;
    font-weight: 700;
    font-size: 1.15rem;
}
.results-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 700;
    background: linear-gradient(90deg, #FFD8E7, #EADDFF);
    color: #534471;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  FALLBACK TABLE — Themed with lavender                                 */
/* ═══════════════════════════════════════════════════════════════════════ */
.fallback-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(107, 92, 138, 0.06);
}
.fallback-table th {
    background: linear-gradient(90deg, #6B5C8A, #534471);
    color: white;
    padding: 0.75rem 1rem;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: left;
    letter-spacing: 0.02em;
}
.fallback-table td {
    padding: 0.65rem 1rem;
    font-size: 0.88rem;
    border-bottom: 1px solid #E4D9F7;
    color: #201828;
}
.fallback-table tr:nth-child(even) td {
    background: #FBF0FF;
}
.fallback-table tr:hover td {
    background: #F3EFFE;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  LANDING FEATURE CARDS                                                 */
/* ═══════════════════════════════════════════════════════════════════════ */
.feature-card {
    text-align: center;
    padding: 2.5rem 1.5rem;
    background: #F7E9FF;
    border: 1px solid #E4D9F7;
    border-radius: 20px;
    box-shadow: 0 4px 16px rgba(107, 92, 138, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(107, 92, 138, 0.12);
}
.feature-card .icon {
    font-size: 2.8rem;
    margin-bottom: 0.75rem;
}
.feature-card h4 {
    margin: 0 0 0.5rem;
    color: #534471;
    font-weight: 700;
    font-size: 1.05rem;
}
.feature-card p {
    color: #6B5C8A;
    font-size: 0.88rem;
    line-height: 1.5;
    margin: 0;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  FOOTER                                                                */
/* ═══════════════════════════════════════════════════════════════════════ */
.app-footer {
    text-align: center;
    padding: 1.5rem 1rem;
    margin-top: 3rem;
    background: linear-gradient(135deg, #FBF0FF, #F7E9FF);
    border-radius: 16px 16px 0 0;
    border-top: 1px solid #E4D9F7;
}
.app-footer p {
    margin: 0;
    font-size: 0.82rem;
    color: #6B5C8A;
    font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  DATASET STATS BAR (sidebar)                                           */
/* ═══════════════════════════════════════════════════════════════════════ */
.dataset-stats {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 0.75rem 1rem;
    box-shadow: 0 2px 8px rgba(107, 92, 138, 0.05);
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.dataset-stats .stat-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #EADDFF, #FFD8E7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.dataset-stats .stat-text {
    font-size: 0.82rem;
    color: #201828;
    font-weight: 500;
}
.dataset-stats .stat-text strong {
    color: #534471;
}

/* ═══════════════════════════════════════════════════════════════════════ */
/*  ANIMATIONS                                                            */
/* ═══════════════════════════════════════════════════════════════════════ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.rec-card {
    animation: fadeInUp 0.4s ease forwards;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading & preprocessing Zomato dataset…")
def get_data():
    """Load and preprocess the Zomato dataset. Cached across reruns."""
    df_raw = load_zomato_data(
        config["data"]["dataset_name"],
        config["data"]["cache_dir"],
    )
    return preprocess(df_raw, config["budget_ranges"])


# Load data once
try:
    df = get_data()
except Exception as e:
    st.error(f"**Failed to load dataset:** {e}")
    st.info("Please check your network connection and try again.")
    st.stop()


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="hero-header">
    <h1>🍽️ AI Restaurant Recommender</h1>
    <p>Powered by Zomato Data + Groq LLM — discover your perfect meal in seconds</p>
    <div class="hero-badges">
        <span class="hero-badge"><span class="dot dot-pink"></span> Groq LLM Online</span>
        <span class="hero-badge"><span class="dot dot-lavender"></span> {len(df):,} Restaurants Loaded</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — user preference inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Search Preferences")
    st.caption("Tune the AI recommendation criteria")
    st.markdown("---")

    # 📍 Location
    available_locations = sorted(df["location_norm"].unique().tolist())
    location_input = st.text_input(
        "📍 Location / Area",
        placeholder="e.g. Koramangala, Indiranagar",
        help="Enter a city area or neighbourhood name",
        key="location_input",
    )

    # 💰 Budget
    budget_level = st.selectbox(
        "💰 Budget Level",
        options=list(config["budget_ranges"].keys()),
        format_func=lambda x: {
            "low": "💚 Low (< ₹300)",
            "medium": "💛 Medium (₹300 – ₹700)",
            "high": "❤️ High (₹700+)",
        }.get(x, x.title()),
        key="budget_level",
    )

    # 🍜 Cuisine
    cuisine_input = st.text_input(
        "🍜 Cuisine Preference",
        placeholder="e.g. Indian, Chinese, Italian (leave empty for any)",
        help="Partial match — 'indian' matches 'North Indian', 'South Indian', etc.",
        key="cuisine_input",
    )

    # ⭐ Min Rating
    min_rating = st.slider(
        "⭐ Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=3.5,
        step=0.1,
        key="min_rating",
    )

    # 🏷️ Extras
    extras = st.multiselect(
        "🏷️ Extras & Vibe",
        options=[
            "Family-friendly",
            "Quick service",
            "Romantic ambiance",
            "Outdoor seating",
            "Vegetarian-friendly",
            "Late-night dining",
            "Budget-friendly drinks",
            "Live music",
            "Rooftop seating",
            "Pet-friendly",
            "Craft beer",
        ],
        key="extras",
    )

    st.markdown("---")

    # 🔍 Submit button
    find_btn = st.button(
        "🔍  Find Restaurants",
        use_container_width=True,
        key="find_btn",
    )

    # Dataset stats
    st.markdown("---")
    st.markdown(f"""
    <div class="dataset-stats">
        <div class="stat-icon">📊</div>
        <div class="stat-text">
            <strong>{len(df):,}</strong> restaurants &nbsp;·&nbsp;
            <strong>{df['location_norm'].nunique()}</strong> areas
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main content area
# ---------------------------------------------------------------------------

def _display_recommendation_card(card, index: int):
    """Render a single recommendation card as styled HTML."""
    rank_emoji = {1: "🏆", 2: "🥈", 3: "🥉"}.get(card.rank, "🍽️")

    # Parse cost for display
    cost_display = card.estimated_cost if card.estimated_cost else "N/A"

    st.markdown(f"""
    <div class="rec-card" style="animation-delay: {index * 0.08}s;">
        <span class="card-rank">{rank_emoji} #{card.rank} Top Match</span>
        <div class="card-name">{card.name}</div>
        <div class="card-meta">
            <div class="meta-item">
                <span class="meta-label">🍜 Cuisine</span>
                <span class="meta-value">{card.cuisine}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">⭐ Rating</span>
                <span class="meta-value">{card.rating}/5.0</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">₹ Cost for Two</span>
                <span class="meta-value cost-value">{cost_display}</span>
            </div>
        </div>
        <div class="card-explanation">
            <span class="ai-icon">✨</span>
            <div>
                <span class="ai-label">Groq AI Insight</span>
                {card.explanation}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _display_fallback_table(candidates):
    """Show filtered results as a styled HTML table when LLM is unavailable."""
    rows_html = ""
    for i, (_, row) in enumerate(candidates.head(10).iterrows()):
        rows_html += (
            f"<tr>"
            f"<td><strong>{i+1}</strong></td>"
            f"<td><strong>{row['name']}</strong></td>"
            f"<td>{row.get('cuisines', 'N/A')}</td>"
            f"<td>⭐ {row['rating']}</td>"
            f"<td>₹{row['cost']}</td>"
            f"<td>{row.get('location', 'N/A')}</td>"
            f"</tr>"
        )
    st.markdown(f"""
    <table class="fallback-table">
        <thead>
            <tr>
                <th>#</th><th>Restaurant</th><th>Cuisine</th>
                <th>Rating</th><th>Cost (for two)</th><th>Area</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Handle the "Find Restaurants" action
# ---------------------------------------------------------------------------
if find_btn:
    # --- Validate location ---
    if not location_input or not location_input.strip():
        st.error("📍 **Please enter a location** to search for restaurants.")
        st.stop()

    # --- Build user preferences ---
    try:
        prefs = build_user_preferences(
            location=location_input,
            budget_level=budget_level,
            cuisine=cuisine_input,
            min_rating=min_rating,
            extras=extras,
            budget_ranges=config["budget_ranges"],
        )
    except ValueError as e:
        st.error(f"⚠️ **Invalid input:** {e}")
        st.stop()

    # --- Filter restaurants ---
    candidates = filter_restaurants(
        df, prefs,
        max_candidates=config["data"].get("max_candidates", 15),
    )

    if candidates.empty:
        st.warning(
            "🔍 **No restaurants found** matching your criteria. "
            "Try broadening your preferences — relax the cuisine, "
            "lower the minimum rating, or try a different area."
        )
        st.stop()

    # --- Show filter summary ---
    cuisine_pill = (
        f'<span class="filter-pill">🍜 {prefs.cuisine.title()}</span>'
        if prefs.cuisine else ''
    )
    extras_pill = (
        f'<span class="filter-pill">{len(prefs.extras)} Features</span>'
        if prefs.extras else ''
    )
    st.markdown(f"""
    <div class="filter-summary">
        <span class="filter-pill">📍 {prefs.location.title()}</span>
        <span class="filter-pill">💰 {prefs.budget_level.title()} (₹{prefs.budget_range[0]}–₹{prefs.budget_range[1]})</span>
        {cuisine_pill}
        <span class="filter-pill">⭐ ≥ {prefs.min_rating}</span>
        <span class="filter-pill-accent filter-pill">📋 {len(candidates)} candidates</span>
        {extras_pill}
    </div>
    """, unsafe_allow_html=True)

    # --- Call LLM for AI-ranked recommendations ---
    try:
        with st.spinner("✨ AI is ranking the best restaurants for you…"):
            system_prompt, user_prompt = build_prompt(prefs, candidates)
            llm_response = call_llm(system_prompt, user_prompt, config)
            recommendations = parse_llm_response(llm_response)

        if recommendations:
            st.markdown(f"""
            <div class="results-header">
                <h3>✨ Showing Top {len(recommendations)} AI-Matched Dining Gems</h3>
                <span class="results-badge">⚡ Synthesized by Groq LLM</span>
            </div>
            """, unsafe_allow_html=True)

            for i, card in enumerate(recommendations):
                _display_recommendation_card(card, i)
        else:
            # Empty LLM response — fallback to raw filtered results
            st.warning(
                "🤖 **AI returned no recommendations.** "
                "Showing top filtered results by rating instead."
            )
            _display_fallback_table(candidates)

    except (ValueError, RuntimeError) as e:
        # LLM API error — fallback to raw filtered results
        st.error(
            "🤖 **Recommendation service unavailable.** "
            "Showing top filtered results by rating instead."
        )
        logger.error(f"LLM call failed: {e}")
        _display_fallback_table(candidates)

else:
    # --- Landing state: show feature cards ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📍</div>
            <h4>Pick a Location</h4>
            <p>Enter an area like Koramangala, Indiranagar, or Jayanagar</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🎛️</div>
            <h4>Set Preferences</h4>
            <p>Choose your budget, cuisine, and minimum rating</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">✨</div>
            <h4>Get AI Picks</h4>
            <p>Our AI ranks & explains the best matches for you</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <p style='text-align:center; color:#6B5C8A; font-size:0.9rem; margin-top:2rem; font-weight:500;'>
    👈 Fill in your preferences in the sidebar and hit <strong>Find Restaurants</strong> to begin!
    </p>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="app-footer">
    <p>Built with ❤️ using Streamlit + Groq + Zomato Data</p>
</div>
""", unsafe_allow_html=True)
