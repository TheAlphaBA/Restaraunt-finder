# Architecture: AI-Powered Restaurant Recommendation System

> **Reference:** Based on [ProblemStatement.md](./ProblemStatement.md)

---

## 1. Overview

This document describes the end-to-end architecture of the **AI-Powered Restaurant Recommendation System** — a Zomato-inspired application that combines structured data filtering with LLM-driven natural language recommendations.

The system takes a user's preferences (location, budget, cuisine, rating), filters a real-world Zomato dataset, constructs an intelligent prompt, and uses an LLM to return ranked, human-readable restaurant recommendations.

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                             │
│              (CLI / Streamlit Web App / REST API)                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  User Preferences
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INPUT HANDLER MODULE                             │
│   Validates & normalizes: Location, Budget, Cuisine, Rating, Extras    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  Structured Query
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Hugging Face Dataset Loader                                    │  │
│   │  (ManikaSaini/zomato-restaurant-recommendation)                 │  │
│   └────────────────────────┬────────────────────────────────────────┘  │
│                            │  Raw Dataset                               │
│                            ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Data Preprocessing & Filtering Engine (Pandas)                 │  │
│   │  - Clean nulls, normalize fields                                │  │
│   │  - Filter by location, cuisine, budget, rating                  │  │
│   │  - Return top N candidates                                      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  Filtered Restaurant Records
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION LAYER                                │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Prompt Builder                                                 │  │
│   │  - Structures user query + filtered data into LLM prompt       │  │
│   │  - Includes context, ranking instructions, output format       │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  Constructed Prompt
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM RECOMMENDATION ENGINE                        │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  LLM API Client (OpenAI GPT / Google Gemini / LangChain)       │  │
│   │  - Sends prompt to LLM                                         │  │
│   │  - Receives ranked list with explanations                      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  LLM Response (JSON / Text)
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OUTPUT FORMATTER                                 │
│   Parses LLM response → structured recommendation cards                 │
│   Fields: Name, Cuisine, Rating, Cost, AI Explanation                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  Formatted Results
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (Results View)                    │
│               Displays top restaurant recommendations                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 User Interface Layer

| Sub-Component | Description |
|---|---|
| **Input Form** | Collects location, budget, cuisine, min rating, extras |
| **Results View** | Displays ranked restaurant cards with AI explanations |
| **Technology** | Streamlit (preferred) / CLI / Flask REST API |

**Responsibilities:**
- Accept and validate user inputs
- Send structured preferences to the Input Handler
- Display formatted recommendations returned from the Output Formatter

---

### 3.2 Input Handler Module

**Responsibilities:**
- Validate required fields (location, budget)
- Normalize budget strings → numeric ranges (`low` → ₹0–300, `medium` → ₹300–700, `high` → ₹700+)
- Normalize cuisine names (case-insensitive matching)
- Return a clean, typed `UserPreferences` object

**Key Fields:**
```python
@dataclass
class UserPreferences:
    location: str
    budget_level: str          # "low" | "medium" | "high"
    budget_range: tuple        # (min_cost, max_cost)
    cuisine: str
    min_rating: float
    extras: list[str]          # e.g., ["family-friendly", "quick service"]
```

---

### 3.3 Data Layer

#### 3.3.1 Dataset Loader

- **Source:** [Hugging Face — ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- **Library:** `datasets` (Hugging Face)
- **Strategy:** Load once at startup, cache locally to avoid repeated downloads

```python
from datasets import load_dataset
dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
df = dataset["train"].to_pandas()
```

#### 3.3.2 Data Preprocessing

| Step | Operation |
|---|---|
| Drop nulls | Remove rows with missing name, location, cuisine, cost, or rating |
| Normalize text | Lowercase location & cuisine for fuzzy matching |
| Parse cost | Convert cost-for-two strings to numeric values |
| Parse rating | Convert rating to float; handle `NEW` or `-` as `None` |
| Encode budget | Map numeric cost to `low / medium / high` category |

#### 3.3.3 Filtering Engine

Filters dataset by:
1. **Location** — substring/fuzzy match on restaurant city/area
2. **Cuisine** — matches against cuisine type column
3. **Budget** — filters by `approx_cost` within the user's budget range
4. **Min Rating** — filters rows where `rating >= min_rating`

Returns top **N candidates** (default: 10–15) sorted by rating descending.

---

### 3.4 Integration Layer — Prompt Builder

The Prompt Builder is the critical bridge between structured data and the LLM.

**Prompt Structure:**

```
System:
  You are a restaurant recommendation assistant. Given a list of restaurants
  and a user's preferences, rank the top 5 restaurants and explain why each
  one is a good match. Return results in JSON format.

User:
  User Preferences:
  - Location: {location}
  - Budget: {budget_level} (approx ₹{budget_range} for two)
  - Cuisine: {cuisine}
  - Minimum Rating: {min_rating}
  - Additional Preferences: {extras}

  Available Restaurants:
  {formatted_restaurant_list}

  Please rank the top 5 restaurants and provide:
  1. Restaurant Name
  2. Cuisine
  3. Rating
  4. Estimated Cost
  5. A 2-3 sentence explanation of why this restaurant fits the user's needs.
```

**Formatted Restaurant List Example:**
```
1. Restaurant: Spice Garden | Cuisine: Indian | Rating: 4.3 | Cost: ₹400 | Area: Koramangala, Bangalore
2. Restaurant: Dragon Wok | Cuisine: Chinese | Rating: 4.1 | Cost: ₹350 | Area: Indiranagar, Bangalore
...
```

---

### 3.5 LLM Recommendation Engine

| Attribute | Detail |
|---|---|
| **Primary LLM** | Google Gemini (`gemini-1.5-flash` / `gemini-pro`) |
| **Alternative** | OpenAI `gpt-4o` / `gpt-3.5-turbo` |
| **Framework** | LangChain (optional — for prompt chaining & memory) |
| **Output Format** | Structured JSON |
| **Temperature** | `0.4` (balanced: creative but consistent) |
| **Max Tokens** | `1024` |

**Expected LLM JSON Output:**
```json
{
  "recommendations": [
    {
      "rank": 1,
      "name": "Spice Garden",
      "cuisine": "Indian",
      "rating": 4.3,
      "estimated_cost": "₹400 for two",
      "explanation": "Spice Garden perfectly matches your preference for Indian cuisine in Koramangala within a medium budget. With a high rating of 4.3 and known for family-friendly ambiance, it's an excellent choice."
    },
    ...
  ]
}
```

---

### 3.6 Output Formatter

- Parses LLM JSON response
- Falls back to regex parsing if JSON is malformed
- Maps each entry to a `RecommendationCard` object
- Passes structured list to the UI layer for rendering

```python
@dataclass
class RecommendationCard:
    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
```

---

## 4. Data Flow Summary

```
User Input
    │
    ▼
Input Handler (validate & normalize)
    │
    ▼
Data Loader (load Zomato dataset from HuggingFace)
    │
    ▼
Preprocessing (clean, normalize)
    │
    ▼
Filtering Engine (location + cuisine + budget + rating)
    │
    ▼
Prompt Builder (structured prompt with filtered data)
    │
    ▼
LLM API Call (Gemini / OpenAI)
    │
    ▼
Output Formatter (parse JSON response)
    │
    ▼
UI Display (recommendation cards)
```

---

## 5. Project Folder Structure

```
restaurant-recommendation/
│
├── app/
│   ├── main.py                  # Entry point (Streamlit / CLI)
│   ├── input_handler.py         # User input validation & normalization
│   ├── data_loader.py           # Hugging Face dataset loader & caching
│   ├── preprocessor.py          # Data cleaning & normalization
│   ├── filter_engine.py         # Restaurant filtering logic
│   ├── prompt_builder.py        # LLM prompt construction
│   ├── llm_client.py            # LLM API wrapper (Gemini / OpenAI)
│   ├── output_formatter.py      # Parse & structure LLM response
│   └── models.py                # Dataclasses: UserPreferences, RecommendationCard
│
├── config/
│   └── config.yaml              # API keys, model settings, budget thresholds
│
├── tests/
│   ├── test_filter_engine.py
│   ├── test_prompt_builder.py
│   └── test_output_formatter.py
│
├── Doc/
│   ├── ProblemStatement.txt
│   ├── ProblemStatement.md
│   └── architecture.md          # This file
│
├── requirements.txt
├── .env                         # API keys (never commit)
└── README.md
```

---

## 6. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core development language |
| **Data Loading** | `datasets` (Hugging Face) | Load Zomato dataset |
| **Data Processing** | `pandas`, `numpy` | Clean, filter, transform data |
| **LLM Integration** | Google Gemini API / OpenAI API | Generate recommendations |
| **LLM Framework** | LangChain *(optional)* | Prompt chaining, memory, retries |
| **UI** | Streamlit | Interactive web interface |
| **Config** | `python-dotenv`, `PyYAML` | Manage API keys & settings |
| **Testing** | `pytest` | Unit & integration tests |

---

## 7. Key Design Decisions

### 7.1 Why Pre-filter before LLM?
Sending the entire dataset to the LLM would exceed token limits and increase cost. Pre-filtering to 10–15 relevant candidates keeps the prompt concise and focused.

### 7.2 Why Structured JSON Output from LLM?
Requesting JSON output makes parsing reliable and deterministic. It avoids brittle string parsing and integrates cleanly into the UI layer.

### 7.3 Why Streamlit for UI?
Streamlit provides rapid development of interactive data apps in pure Python — no frontend knowledge needed. It's ideal for ML/AI prototypes.

### 7.4 Budget Normalization
Since budgets in the dataset are numeric (cost-for-two in INR), and user input is categorical (`low/medium/high`), a mapping layer ensures consistent filtering without exposing raw numbers in the UI.

---

## 8. Error Handling Strategy

| Scenario | Handling |
|---|---|
| No restaurants match filters | Return message: "No results found, try broadening your preferences" |
| LLM API failure / timeout | Retry up to 3 times with exponential backoff; fallback to top-rated filtered list |
| Malformed LLM JSON response | Regex fallback parser; log warning |
| Dataset load failure | Use locally cached version if available |
| Invalid user input | Validate at input handler; return field-specific error messages |

---

## 9. Future Enhancements

| Enhancement | Description |
|---|---|
| **User Feedback Loop** | Thumbs up/down on recommendations to fine-tune future prompts |
| **Conversation Memory** | Multi-turn chat using LangChain memory for iterative refinement |
| **Map Integration** | Display restaurant locations on an interactive map (Folium / Google Maps) |
| **Semantic Search** | Use embeddings (FAISS / Pinecone) for similarity-based restaurant lookup |
| **Personalization** | Save user history and preferences for returning users |
| **Multi-city Expansion** | Extend beyond Zomato dataset to other food delivery APIs |

---

*Document generated based on: [ProblemStatement.md](./ProblemStatement.md)*
