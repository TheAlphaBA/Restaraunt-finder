# Phase-Wise Implementation Plan
## AI-Powered Restaurant Recommendation System (Zomato Use Case)

> **References:**
> - [ProblemStatement.md](./ProblemStatement.md)
> - [architecture.md](./architecture.md)

---

## Overview

This document outlines the step-by-step, phase-wise plan to build the AI-Powered Restaurant Recommendation System. The project is broken into **6 phases**, progressing from environment setup to a fully functional, tested, and deployable application.

---

## Phase Summary

| Phase | Name | Duration | Key Output |
|---|---|---|---|
| **Phase 1** | Project Setup & Environment | Day 1 | Repo, virtualenv, config, folder structure |
| **Phase 2** | Data Ingestion & Preprocessing | Day 2–3 | Clean, filtered Pandas DataFrame |
| **Phase 3** | Input Handler & Filtering Engine | Day 4–5 | Working filter pipeline |
| **Phase 4** | LLM Integration & Prompt Engineering | Day 6–8 | LLM returning ranked JSON recommendations |
| **Phase 5** | UI Development (Streamlit) | Day 9–10 | Interactive web interface |
| **Phase 6** | Testing, Error Handling & Deployment | Day 11–13 | Tested, production-ready app |

---

## Phase 1 — Project Setup & Environment

**Goal:** Establish a clean, reproducible development environment and project scaffold.

**Duration:** Day 1

---

### 1.1 Repository & Folder Structure

Create the project directory following the architecture-defined structure:

```
restaurant-recommendation/
│
├── app/
│   ├── main.py
│   ├── input_handler.py
│   ├── data_loader.py
│   ├── preprocessor.py
│   ├── filter_engine.py
│   ├── prompt_builder.py
│   ├── llm_client.py
│   ├── output_formatter.py
│   └── models.py
│
├── config/
│   └── config.yaml
│
├── tests/
│   ├── test_filter_engine.py
│   ├── test_prompt_builder.py
│   └── test_output_formatter.py
│
├── Doc/
│   ├── ProblemStatement.txt
│   ├── ProblemStatement.md
│   ├── architecture.md
│   └── implementation-plan.md
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

### 1.2 Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install core dependencies
pip install datasets pandas numpy python-dotenv pyyaml streamlit pytest
pip install google-generativeai openai langchain
pip freeze > requirements.txt
```

---

### 1.3 Configuration Files

**`.env`** — Store all secrets (never commit):
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**`config/config.yaml`** — App-level settings:
```yaml
llm:
  provider: gemini              # or "openai"
  model: gemini-1.5-flash
  temperature: 0.4
  max_tokens: 1024

data:
  dataset_name: ManikaSaini/zomato-restaurant-recommendation
  max_candidates: 15            # Max restaurants to pass to LLM
  cache_dir: .cache/

budget_ranges:
  low:    [0, 300]
  medium: [300, 700]
  high:   [700, 9999]
```

**`.gitignore`:**
```
venv/
.env
.cache/
__pycache__/
*.pyc
```

---

### 1.4 Models Scaffold — `app/models.py`

Define core data classes used across all modules:

```python
from dataclasses import dataclass, field

@dataclass
class UserPreferences:
    location: str
    budget_level: str           # "low" | "medium" | "high"
    budget_range: tuple         # (min_cost, max_cost)
    cuisine: str
    min_rating: float
    extras: list[str] = field(default_factory=list)

@dataclass
class RecommendationCard:
    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
```

**✅ Phase 1 Deliverables:**
- [ ] Project folder created with all placeholder files
- [ ] Virtual environment set up with all dependencies installed
- [ ] `.env`, `config.yaml`, `.gitignore` configured
- [ ] `models.py` with `UserPreferences` and `RecommendationCard` dataclasses
- [ ] Git repository initialized with initial commit

---

## Phase 2 — Data Ingestion & Preprocessing

**Goal:** Load the Zomato dataset from Hugging Face, clean it, normalize key fields, and produce a reliable Pandas DataFrame ready for filtering.

**Duration:** Day 2–3

---

### 2.1 Dataset Loader — `app/data_loader.py`

- Load dataset from Hugging Face using the `datasets` library
- Convert to Pandas DataFrame
- Cache locally to avoid repeated downloads

```python
from datasets import load_dataset
import pandas as pd
import os

def load_zomato_data(dataset_name: str, cache_dir: str) -> pd.DataFrame:
    os.makedirs(cache_dir, exist_ok=True)
    dataset = load_dataset(dataset_name, cache_dir=cache_dir)
    df = dataset["train"].to_pandas()
    return df
```

**Dataset Source:**
[ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

---

### 2.2 Data Exploration

Before preprocessing, explore the dataset:

```python
print(df.columns.tolist())     # Identify column names
print(df.dtypes)               # Inspect data types
print(df.isnull().sum())       # Count missing values
print(df["rate"].unique())     # Inspect rating format
print(df["approx_cost(for two people)"].unique())  # Inspect cost format
```

**Key columns to retain:**
- `name` — Restaurant name
- `location` — Area/neighbourhood
- `cuisines` — Cuisine types
- `approx_cost(for two people)` — Cost for two (INR)
- `rate` — Aggregate rating
- `rest_type` — Restaurant type (family, cafe, etc.)
- `votes` — Number of votes

---

### 2.3 Preprocessor — `app/preprocessor.py`

Apply the following cleaning steps in sequence:

| Step | Operation | Detail |
|---|---|---|
| **1. Drop duplicates** | `df.drop_duplicates()` | Remove exact duplicate rows |
| **2. Drop nulls** | Drop rows with missing `name`, `location`, `cuisines`, `rate`, `approx_cost` | Core fields required |
| **3. Parse rating** | `rate` column: remove `/5`, handle `NEW`, `-`, `nan` → `None` | Convert to `float` |
| **4. Parse cost** | `approx_cost` column: remove commas, cast to `int` | Normalize to numeric |
| **5. Normalize text** | Lowercase `location` and `cuisines` columns | Enable fuzzy matching |
| **6. Encode budget** | Map numeric cost → `low / medium / high` | Add `budget_level` column |
| **7. Reset index** | `df.reset_index(drop=True)` | Clean index after filtering |

```python
def preprocess(df: pd.DataFrame, budget_ranges: dict) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df.dropna(subset=["name", "location", "cuisines", "rate",
                            "approx_cost(for two people)"])
    df["rating"] = df["rate"].apply(parse_rating)
    df["cost"] = df["approx_cost(for two people)"].apply(parse_cost)
    df["location_norm"] = df["location"].str.lower().str.strip()
    df["cuisines_norm"] = df["cuisines"].str.lower().str.strip()
    df["budget_level"] = df["cost"].apply(
        lambda x: encode_budget(x, budget_ranges)
    )
    return df.reset_index(drop=True)
```

---

### 2.4 Validation

After preprocessing, validate the DataFrame:

```python
assert df["rating"].between(0, 5).all()
assert df["cost"].gt(0).all()
assert df["budget_level"].isin(["low", "medium", "high"]).all()
print(f"Cleaned dataset: {len(df)} records")
```

**✅ Phase 2 Deliverables:**
- [ ] `data_loader.py` — loads & caches dataset from Hugging Face
- [ ] `preprocessor.py` — all 7 cleaning steps implemented
- [ ] DataFrame validated with no nulls in key columns
- [ ] Budget level column populated correctly
- [ ] Data exploration notes documented

---

## Phase 3 — Input Handler & Filtering Engine

**Goal:** Accept and validate user preferences, then filter the preprocessed dataset to return the most relevant restaurant candidates.

**Duration:** Day 4–5

---

### 3.1 Input Handler — `app/input_handler.py`

Validate and normalize raw user inputs into a `UserPreferences` object:

```python
def build_user_preferences(
    location: str,
    budget_level: str,
    cuisine: str,
    min_rating: float,
    extras: list[str],
    budget_ranges: dict
) -> UserPreferences:
    # Validate
    if not location.strip():
        raise ValueError("Location is required.")
    if budget_level not in budget_ranges:
        raise ValueError(f"Budget must be one of: {list(budget_ranges.keys())}")
    if not 0 <= min_rating <= 5:
        raise ValueError("Rating must be between 0 and 5.")

    budget_range = tuple(budget_ranges[budget_level])

    return UserPreferences(
        location=location.strip().lower(),
        budget_level=budget_level,
        budget_range=budget_range,
        cuisine=cuisine.strip().lower(),
        min_rating=min_rating,
        extras=extras
    )
```

---

### 3.2 Filtering Engine — `app/filter_engine.py`

Apply sequential filters to the preprocessed DataFrame:

```python
def filter_restaurants(
    df: pd.DataFrame,
    prefs: UserPreferences,
    max_candidates: int = 15
) -> pd.DataFrame:

    result = df.copy()

    # Filter 1: Location (fuzzy substring match)
    result = result[result["location_norm"].str.contains(
        prefs.location, na=False
    )]

    # Filter 2: Cuisine (partial match)
    if prefs.cuisine:
        result = result[result["cuisines_norm"].str.contains(
            prefs.cuisine, na=False
        )]

    # Filter 3: Budget range
    min_cost, max_cost = prefs.budget_range
    result = result[result["cost"].between(min_cost, max_cost)]

    # Filter 4: Minimum rating
    result = result[result["rating"] >= prefs.min_rating]

    # Sort by rating descending, return top N
    result = result.sort_values("rating", ascending=False)
    return result.head(max_candidates)
```

**Filter Fallback Strategy:**

If strict filtering returns fewer than 3 results:
1. Relax cuisine filter → return top results by rating
2. Relax budget range by ±₹200
3. Return message advising user to broaden preferences

---

### 3.3 Unit Tests — `tests/test_filter_engine.py`

```python
def test_location_filter():
    ...  # assert only Bangalore results returned

def test_budget_filter():
    ...  # assert cost within range

def test_min_rating_filter():
    ...  # assert all results >= min_rating

def test_empty_results_fallback():
    ...  # assert graceful handling when no results
```

**✅ Phase 3 Deliverables:**
- [ ] `input_handler.py` — validates & returns `UserPreferences`
- [ ] `filter_engine.py` — all 4 filters + fallback logic
- [ ] End-to-end test: raw input → filtered DataFrame
- [ ] Unit tests passing for filter engine

---

## Phase 4 — LLM Integration & Prompt Engineering

**Goal:** Construct an optimized prompt from filtered restaurant data and user preferences, call the LLM via **Groq** (OpenAI-compatible API), and return structured ranked recommendations.

**Duration:** Day 6–8

**LLM Provider:** [Groq](https://groq.com/) — ultra-fast inference API with OpenAI-compatible endpoint.

**Supported Models (pick one):**
- `openai/gpt-oss-120b` — large-scale open-source GPT model
- `qwen/qwen3.6-27b` — Alibaba's Qwen 3.6 27B model

**API Details:**
- Base URL: `https://api.groq.com/openai/v1`
- Auth: `GROQ_API_KEY` in `.env`
- SDK: `openai` Python package (already installed) with custom `base_url`

---

### 4.1 Prompt Builder — `app/prompt_builder.py`

Build a system + user prompt from the `UserPreferences` and filtered DataFrame:

```python
def build_prompt(prefs: UserPreferences, candidates: pd.DataFrame) -> tuple:

    restaurant_list = "\n".join([
        f"{i+1}. Restaurant: {row['name']} | "
        f"Cuisine: {row['cuisines']} | "
        f"Rating: {row['rating']} | "
        f"Cost: ₹{row['cost']} for two | "
        f"Area: {row['location']}"
        for i, (_, row) in enumerate(candidates.iterrows())
    ])

    system_prompt = (
        "You are an expert restaurant recommendation assistant. "
        "Given a list of restaurants and user preferences, rank the top 5 "
        "restaurants that best match the user's needs. "
        "Return your response ONLY as valid JSON matching this schema: "
        '{"recommendations": [{"rank": int, "name": str, "cuisine": str, '
        '"rating": float, "estimated_cost": str, "explanation": str}]}'
    )

    user_prompt = f"""
User Preferences:
- Location: {prefs.location.title()}
- Budget: {prefs.budget_level.title()} (₹{prefs.budget_range[0]}–₹{prefs.budget_range[1]} for two)
- Cuisine: {prefs.cuisine.title() if prefs.cuisine else "Any"}
- Minimum Rating: {prefs.min_rating}
- Additional Preferences: {", ".join(prefs.extras) if prefs.extras else "None"}

Available Restaurants:
{restaurant_list}

Rank the top 5 restaurants and explain why each one fits the user's needs.
"""
    return system_prompt, user_prompt
```

---

### 4.2 LLM Client — `app/llm_client.py`

Use the **OpenAI Python SDK** with Groq's compatible endpoint:

```python
from openai import OpenAI
import time, json, os

def call_llm(system_prompt: str, user_prompt: str, config: dict) -> dict:
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=config["llm"]["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config["llm"]["temperature"],
                max_tokens=config["llm"]["max_tokens"]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)   # Exponential backoff
            else:
                raise RuntimeError(f"LLM call failed after 3 attempts: {e}")
```

---

### 4.3 Output Formatter — `app/output_formatter.py`

Parse LLM JSON response into `RecommendationCard` objects:

```python
import json, re
from app.models import RecommendationCard

def parse_llm_response(raw_response: dict) -> list[RecommendationCard]:
    cards = []
    for item in raw_response.get("recommendations", []):
        cards.append(RecommendationCard(
            rank=item.get("rank", 0),
            name=item.get("name", "Unknown"),
            cuisine=item.get("cuisine", ""),
            rating=float(item.get("rating", 0.0)),
            estimated_cost=item.get("estimated_cost", ""),
            explanation=item.get("explanation", "")
        ))
    return sorted(cards, key=lambda c: c.rank)

def parse_with_fallback(raw_text: str) -> list[RecommendationCard]:
    """Regex fallback if JSON is malformed."""
    try:
        data = json.loads(raw_text)
        return parse_llm_response(data)
    except json.JSONDecodeError:
        # Regex extraction fallback
        ...
```

---

### 4.4 Prompt Engineering Iterations

Test and iterate on prompt quality:

| Iteration | Change | Expected Improvement |
|---|---|---|
| v1 | Basic list of restaurants | Baseline results |
| v2 | Add user extras to prompt | Better personalization |
| v3 | Add JSON schema in system prompt | Consistent output format |
| v4 | Add ranking instruction & reasoning request | Better explanations |

**✅ Phase 4 Deliverables:**
- [ ] `prompt_builder.py` — constructs system + user prompts
- [ ] `llm_client.py` — Groq API wrapper (OpenAI-compatible) with retry + backoff
- [ ] `output_formatter.py` — JSON parser + regex fallback
- [ ] Prompt iterated to v4 with consistent JSON output
- [ ] Unit tests for prompt builder and output formatter
- [ ] End-to-end test: preferences → LLM → `RecommendationCard` list

---

## Phase 5 — UI Development (Streamlit)

**Goal:** Build an interactive, user-friendly Streamlit web interface that ties all components together.

**Duration:** Day 9–10

---

### 5.1 App Entry Point — `app/main.py`

```python
import streamlit as st
from app.input_handler import build_user_preferences
from app.data_loader import load_zomato_data
from app.preprocessor import preprocess
from app.filter_engine import filter_restaurants
from app.prompt_builder import build_prompt
from app.llm_client import call_llm
from app.output_formatter import parse_llm_response
import yaml, os
from dotenv import load_dotenv

load_dotenv()
with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

# Load & preprocess data once (cached)
@st.cache_data
def get_data():
    df_raw = load_zomato_data(config["data"]["dataset_name"],
                               config["data"]["cache_dir"])
    return preprocess(df_raw, config["budget_ranges"])

df = get_data()
```

---

### 5.2 UI Layout

```
┌──────────────────────────────────────────────────┐
│  🍽️  AI Restaurant Recommender                   │
│  Powered by Zomato Data + Google Gemini           │
├──────────────────────────────────────────────────┤
│  📍 Location:    [Text Input]                    │
│  💰 Budget:      [Selectbox: Low/Medium/High]    │
│  🍜 Cuisine:     [Text Input]                    │
│  ⭐ Min Rating:  [Slider: 0.0 – 5.0]            │
│  🏷️  Extras:     [Multiselect]                   │
│                                                  │
│  [ 🔍 Find Restaurants ]                         │
├──────────────────────────────────────────────────┤
│  Top Recommendations:                            │
│                                                  │
│  #1 🏆 Restaurant Name                           │
│  Cuisine | ⭐ 4.3 | ₹400 for two                │
│  "AI-generated explanation..."                   │
│  ─────────────────────────────────              │
│  #2 ...                                          │
└──────────────────────────────────────────────────┘
```

---

### 5.3 Streamlit Components

| UI Element | Streamlit Widget | Purpose |
|---|---|---|
| Location input | `st.text_input()` | Enter city/area |
| Budget selector | `st.selectbox()` | Choose low/medium/high |
| Cuisine input | `st.text_input()` | Enter cuisine type |
| Min rating slider | `st.slider(0.0, 5.0)` | Set minimum rating |
| Extras multiselect | `st.multiselect()` | Additional preferences |
| Submit button | `st.button()` | Trigger recommendation |
| Spinner | `st.spinner()` | Show loading state during LLM call |
| Results | `st.container()` + `st.markdown()` | Display recommendation cards |
| Error messages | `st.error()` / `st.warning()` | Show validation/API errors |

---

### 5.4 Recommendation Card Display

```python
for card in recommendations:
    with st.container():
        st.markdown(f"### #{card.rank} {card.name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Cuisine", card.cuisine)
        col2.metric("Rating", f"⭐ {card.rating}")
        col3.metric("Cost", card.estimated_cost)
        st.info(f"💬 {card.explanation}")
        st.divider()
```

---

### 5.5 Error & Edge Case Handling in UI

| Scenario | UI Behavior |
|---|---|
| Missing location | `st.error("Please enter a location")` |
| No restaurants found after filter | `st.warning("No restaurants found. Try broadening your preferences.")` |
| LLM API error | `st.error("Recommendation service unavailable. Showing top results by rating.")` |
| Empty LLM response | Fallback to displaying raw filtered results |

**✅ Phase 5 Deliverables:**
- [ ] `main.py` Streamlit app with all 5 input widgets
- [ ] Dataset loaded and cached with `@st.cache_data`
- [ ] Recommendation cards displayed with metrics + explanation
- [ ] All error states handled gracefully in the UI
- [ ] App runs locally with `streamlit run app/main.py`

---

## Phase 6 — Testing, Error Handling & Deployment

**Goal:** Write comprehensive tests, harden error handling, and prepare the app for deployment.

**Duration:** Day 11–13

---

### 6.1 Unit Tests

**`tests/test_filter_engine.py`:**
- Test location filter with valid and invalid inputs
- Test cuisine filter with partial/fuzzy match
- Test budget range boundaries
- Test min rating filter
- Test fallback when no results found

**`tests/test_prompt_builder.py`:**
- Test prompt contains all user preference fields
- Test restaurant list formatting
- Test extras included in prompt when provided

**`tests/test_output_formatter.py`:**
- Test parsing of valid JSON response
- Test fallback for malformed JSON
- Test ranking order of output cards

```bash
pytest tests/ -v --tb=short
```

---

### 6.2 Integration Tests

End-to-end test (with mocked LLM):

```python
def test_full_pipeline_integration(mock_llm):
    prefs = build_user_preferences("bangalore", "medium", "indian", 3.5, [])
    candidates = filter_restaurants(df, prefs)
    system_prompt, user_prompt = build_prompt(prefs, candidates)
    llm_response = mock_llm(system_prompt, user_prompt)
    cards = parse_llm_response(llm_response)
    assert len(cards) > 0
    assert all(isinstance(c, RecommendationCard) for c in cards)
```

---

### 6.3 Error Handling Hardening

| Layer | Error | Handling |
|---|---|---|
| Input Handler | Missing required field | `ValueError` with field-specific message |
| Data Loader | Network failure / dataset not found | Retry 3x; raise `RuntimeError` with instructions |
| Filter Engine | Zero results after all filters | Graceful fallback message |
| LLM Client | API rate limit / timeout | Exponential backoff (1s, 2s, 4s); 3 attempts |
| LLM Client | Auth failure (bad API key) | Immediate fail with clear key error message |
| Output Formatter | Malformed JSON | Regex fallback parser; log warning |
| UI | Any unhandled exception | `st.exception(e)` with user-friendly message |

---

### 6.4 Deployment

#### Option A — Local / Demo

```bash
streamlit run app/main.py
# Access at http://localhost:8501
```

#### Option B — Streamlit Cloud (Recommended for Sharing)

1. Push repository to GitHub (exclude `.env`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo
4. Set secrets in Streamlit Cloud dashboard:
   ```
   GEMINI_API_KEY = your_key_here
   ```
5. Deploy — public URL generated automatically

#### Option C — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.port=8501"]
```

```bash
docker build -t restaurant-recommender .
docker run -p 8501:8501 --env-file .env restaurant-recommender
```

---

### 6.5 README — Final Documentation

Include in `README.md`:
- Project overview and demo screenshot
- Setup instructions
- How to run locally
- How to configure API keys
- Architecture diagram reference
- Dataset link

---

**✅ Phase 6 Deliverables:**
- [x] All unit tests written and passing (`pytest`)
- [x] Integration test with mocked LLM
- [x] Error handling hardened across all layers
- [x] `README.md` with setup and usage instructions
- [x] Backend API deployed on Railway (`api/server.py` + Dockerfile)
- [x] Frontend UI deployed on Vercel (`frontend/` Next.js App)
- [x] Step-by-step deployment guide created in `Doc/deployment.md`

---

## Overall Progress Tracker

```
Phase 1: Project Setup            [ ] Day 1
Phase 2: Data Ingestion           [ ] Day 2–3
Phase 3: Input Handler & Filter   [ ] Day 4–5
Phase 4: LLM Integration          [ ] Day 6–8
Phase 5: Streamlit UI             [ ] Day 9–10
Phase 6: Testing & Deployment     [ ] Day 11–13
```

---

## Dependency Map

```
models.py
    │
    ├──► input_handler.py
    │         │
    │         ▼
    │    filter_engine.py ◄── data_loader.py
    │         │                    │
    │         ▼                    ▼
    │    prompt_builder.py   preprocessor.py
    │         │
    │         ▼
    │    llm_client.py
    │         │
    │         ▼
    └──► output_formatter.py
              │
              ▼
          main.py (Streamlit UI)
```

---

*Document generated from: [ProblemStatement.md](./ProblemStatement.md) · [architecture.md](./architecture.md)*
