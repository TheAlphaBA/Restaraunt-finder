# Evaluation Plan
## AI-Powered Restaurant Recommendation System (Zomato Use Case)

> **Reference:** [implementation-plan.md](./implementation-plan.md)

---

## Overview

This document defines the complete evaluation framework for the AI-Powered Restaurant Recommendation System. It covers **functional correctness**, **LLM output quality**, **data pipeline integrity**, **UI/UX validation**, **performance benchmarks**, and **deployment readiness** — mapped phase by phase to the implementation plan.

---

## Evaluation Goals

| Goal | Description |
|---|---|
| **Functional Correctness** | Every module performs its intended operation without errors |
| **Data Quality** | Preprocessing produces a clean, valid, filterable dataset |
| **Filter Accuracy** | Filter engine returns only restaurants matching user constraints |
| **LLM Output Quality** | Recommendations are relevant, ranked correctly, and well-explained |
| **Prompt Robustness** | Prompts consistently produce structured JSON across varied inputs |
| **UI Completeness** | All user flows work end-to-end without crashes or data loss |
| **Performance** | Response time is acceptable; system handles load gracefully |
| **Security & Safety** | No secrets leaked; inputs sanitized; LLM output validated |

---

## Evaluation Levels

```
Level 1 — Unit Tests         (module-by-module, isolated)
Level 2 — Integration Tests  (multi-module pipeline)
Level 3 — LLM Quality Evals  (prompt/output quality scoring)
Level 4 — UI/UX Tests        (manual + automated Streamlit checks)
Level 5 — Performance Tests  (latency, throughput, load)
Level 6 — Deployment Checks  (pre-launch readiness gate)
```

---

## Level 1 — Unit Tests

### 1.1 `models.py` — Data Model Validation

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-M-01 | Create valid `UserPreferences` | All valid fields | Object created | No exception raised |
| UT-M-02 | `UserPreferences` default extras | No extras passed | `extras = []` | `prefs.extras == []` |
| UT-M-03 | Create valid `RecommendationCard` | All fields provided | Object created | All fields accessible |
| UT-M-04 | `RecommendationCard` rank is int | `rank = "1"` (str) | Type error caught | `isinstance(card.rank, int)` |

---

### 1.2 `data_loader.py` — Dataset Loading

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-DL-01 | Load dataset successfully | Valid dataset name | Non-empty DataFrame | `len(df) > 0` |
| UT-DL-02 | Cache directory is created | Non-existent cache path | Directory created | `os.path.exists(cache_dir)` |
| UT-DL-03 | Network failure → retry | Mocked `ConnectionError` | Retries 3x then raises | `RuntimeError` raised after 3 attempts |
| UT-DL-04 | Fallback to local cache | Network down + cache exists | Returns cached DataFrame | `len(df) > 0` without network |
| UT-DL-05 | Dataset has expected columns | Real/mocked dataset | Required columns present | `{"name","location","rate","cuisines","approx_cost"} ⊆ df.columns` |

---

### 1.3 `preprocessor.py` — Data Cleaning

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-PP-01 | Duplicate rows removed | DataFrame with 2 identical rows | 1 row remaining | `len(df) == 1` |
| UT-PP-02 | Null rows dropped | Row with `rate = NaN` | Row removed | `df["rating"].isna().sum() == 0` |
| UT-PP-03 | Rating `"3.5/5"` parsed | `rate = "3.5/5"` | `rating = 3.5` | `df["rating"].iloc[0] == 3.5` |
| UT-PP-04 | Rating `"NEW"` → `None` | `rate = "NEW"` | Row dropped | Not present in output |
| UT-PP-05 | Rating `"-"` → `None` | `rate = "-"` | Row dropped | Not present in output |
| UT-PP-06 | Cost `"1,200"` → `1200` | `approx_cost = "1,200"` | `cost = 1200` | `df["cost"].iloc[0] == 1200` |
| UT-PP-07 | Cost `"₹800"` → `800` | `approx_cost = "₹800"` | `cost = 800` | `df["cost"].iloc[0] == 800` |
| UT-PP-08 | Cost `0` → row dropped | `approx_cost = "0"` | Row removed | Not present in output |
| UT-PP-09 | Location normalized to lowercase | `location = "BANGALORE"` | `location_norm = "bangalore"` | `df["location_norm"].iloc[0] == "bangalore"` |
| UT-PP-10 | Budget level encoded correctly | `cost = 250` | `budget_level = "low"` | `df["budget_level"].iloc[0] == "low"` |
| UT-PP-11 | Budget boundary value `cost=300` | `cost = 300` | `budget_level = "medium"` | `df["budget_level"].iloc[0] == "medium"` |
| UT-PP-12 | Rating out of range `> 5` → dropped | `rating = 5.5` | Row removed | Not present in output |
| UT-PP-13 | Empty DataFrame after cleaning | All rows null | `ValueError` raised | `ValueError: Preprocessed dataset is empty` |

---

### 1.4 `input_handler.py` — Input Validation

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-IH-01 | Valid inputs return `UserPreferences` | All valid fields | `UserPreferences` object | No exception |
| UT-IH-02 | Empty location raises error | `location = ""` | `ValueError` | Message: `"Location is required"` |
| UT-IH-03 | Whitespace-only location raises error | `location = "   "` | `ValueError` | Message: `"Location is required"` |
| UT-IH-04 | Invalid budget level raises error | `budget = "premium"` | `ValueError` | Message lists valid options |
| UT-IH-05 | Budget level case-insensitive | `budget = "MEDIUM"` | Normalized to `"medium"` | `prefs.budget_level == "medium"` |
| UT-IH-06 | Rating `< 0` raises error | `min_rating = -1` | `ValueError` | Message: `"Rating must be between 0 and 5"` |
| UT-IH-07 | Rating `> 5` raises error | `min_rating = 5.1` | `ValueError` | Message: `"Rating must be between 0 and 5"` |
| UT-IH-08 | Rating `= 0` is valid | `min_rating = 0` | `UserPreferences` created | `prefs.min_rating == 0.0` |
| UT-IH-09 | Rating `= 5` is valid | `min_rating = 5` | `UserPreferences` created | `prefs.min_rating == 5.0` |
| UT-IH-10 | `extras = None` normalized | `extras = None` | `extras = []` | `prefs.extras == []` |
| UT-IH-11 | Budget range mapped correctly | `budget = "low"` | `budget_range = (0, 300)` | `prefs.budget_range == (0, 300)` |
| UT-IH-12 | Location stripped and lowercased | `location = "  Bangalore  "` | `"bangalore"` | `prefs.location == "bangalore"` |

---

### 1.5 `filter_engine.py` — Restaurant Filtering

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-FE-01 | Location filter returns matching rows | `location = "bangalore"` | Only Bangalore rows | All rows contain `"bangalore"` in `location_norm` |
| UT-FE-02 | Location filter case-insensitive | `location = "Bangalore"` (already lowercased in handler) | Same as above | Results identical to UT-FE-01 |
| UT-FE-03 | Cuisine filter partial match | `cuisine = "indian"` | Rows where `cuisines_norm` contains `"indian"` | All rows contain `"indian"` |
| UT-FE-04 | Empty cuisine skips filter | `cuisine = ""` | All locations returned | No cuisine filtering applied |
| UT-FE-05 | Budget range filter inclusive boundaries | `budget_range = (300, 700)`, `cost = 300` | Row included | `cost=300` row present in results |
| UT-FE-06 | Budget range filter upper boundary | `budget_range = (300, 700)`, `cost = 700` | Row included | `cost=700` row present in results |
| UT-FE-07 | Budget filter excludes out-of-range | `budget_range = (300, 700)`, `cost = 800` | Row excluded | `cost=800` row not in results |
| UT-FE-08 | Min rating filter | `min_rating = 4.0` | Only rows with `rating >= 4.0` | `result["rating"].min() >= 4.0` |
| UT-FE-09 | Results sorted by rating descending | Mixed ratings | Highest rated first | `result["rating"].iloc[0] == result["rating"].max()` |
| UT-FE-10 | Results capped at `max_candidates` | 100 matching rows | ≤ 15 rows returned | `len(result) <= 15` |
| UT-FE-11 | Tie-break by votes when ratings equal | 20 rows all rated 4.9 | Top 15 by votes | Top row has highest `votes` |
| UT-FE-12 | Zero results → fallback activates | Impossible filter combo | `>= 1` result returned | Fallback returns top-rated rows |
| UT-FE-13 | Location with special chars `"(5th Block)"` | `location = "koramangala (5th block)"` | No regex error | Results returned or empty — no exception |
| UT-FE-14 | Regex-escaped location used | `location = "delhi+ncr"` | `re.escape()` applied | No `re.error` raised |

---

### 1.6 `prompt_builder.py` — Prompt Construction

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-PB-01 | Prompt contains location | `location = "bangalore"` | `"Bangalore"` in prompt | `"Bangalore" in user_prompt` |
| UT-PB-02 | Prompt contains budget level | `budget = "medium"` | `"Medium"` in prompt | `"Medium" in user_prompt` |
| UT-PB-03 | Prompt contains budget range | `budget_range = (300,700)` | `"₹300–₹700"` in prompt | Range string present |
| UT-PB-04 | Prompt contains cuisine | `cuisine = "italian"` | `"Italian"` in prompt | `"Italian" in user_prompt` |
| UT-PB-05 | Empty cuisine shows `"Any"` | `cuisine = ""` | `"Any"` in prompt | `"Any" in user_prompt` |
| UT-PB-06 | Extras included when provided | `extras = ["family-friendly"]` | `"family-friendly"` in prompt | Present in prompt |
| UT-PB-07 | Empty extras shows `"None"` | `extras = []` | `"None"` in prompt | `"None" in user_prompt` |
| UT-PB-08 | All candidate restaurants listed | 10-row DataFrame | 10 entries in prompt | Prompt contains all 10 entries |
| UT-PB-09 | Restaurant name with single quote | `name = "McDonald's"` | Name included safely | No prompt injection; no exception |
| UT-PB-10 | Empty candidates → returns `None` | Empty DataFrame | `(None, None)` returned | Caller handles gracefully |
| UT-PB-11 | System prompt contains JSON schema | Any valid input | JSON schema string present | `"recommendations"` in `system_prompt` |
| UT-PB-12 | Prompt NaN field shows `"N/A"` | Candidate with `cuisines = NaN` | `"Cuisine: N/A"` in prompt | `"N/A"` appears, not `"nan"` |

---

### 1.7 `llm_client.py` — LLM API Wrapper

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-LC-01 | Successful call returns dict | Valid prompts, mocked API | Parsed JSON dict | `isinstance(result, dict)` |
| UT-LC-02 | Retry on transient error | API fails twice then succeeds | Result returned | Result valid; 3 total attempts made |
| UT-LC-03 | Fail after 3 attempts | API fails 3 times | `RuntimeError` raised | Message: `"LLM call failed after 3 attempts"` |
| UT-LC-04 | Auth error → no retry | API returns 401 | Immediate `RuntimeError` | Only 1 attempt made |
| UT-LC-05 | Rate limit → exponential backoff | API returns 429 twice | Retried with delays | Sleep called with `1`, `2` seconds |
| UT-LC-06 | Empty response → retry | API returns `""` | Retry triggered | `ValueError` then retry; fallback activated |
| UT-LC-07 | Timeout respected | API hangs > 30s | `TimeoutError` raised | Within 32 seconds total |
| UT-LC-08 | Invalid API key raises clear error | `GEMINI_API_KEY = "bad"` | Auth error with message | `"Invalid API key"` in error |

---

### 1.8 `output_formatter.py` — Response Parsing

| Test ID | Test Description | Input | Expected Output | Pass Criteria |
|---|---|---|---|---|
| UT-OF-01 | Valid JSON parsed correctly | Well-formed JSON response | List of `RecommendationCard` | `len(cards) == 5` |
| UT-OF-02 | Cards sorted by rank | JSON with ranks out of order | Cards ordered `1, 2, 3, 4, 5` | `cards[0].rank == 1` |
| UT-OF-03 | Duplicate ranks re-indexed | Two cards with `rank = 1` | Ranks reassigned `1, 2, ...` | No duplicate ranks |
| UT-OF-04 | Missing rank defaults to index | `"rank"` key absent | Sequential rank assigned | `cards[0].rank == 1` |
| UT-OF-05 | String rank `"first"` → int fallback | `"rank": "first"` | `rank = 1` (by index) | No exception |
| UT-OF-06 | Plain text response → regex fallback | Non-JSON text response | Partial cards extracted | At least 1 card returned |
| UT-OF-07 | Truncated JSON → regex fallback | Incomplete JSON string | Fallback activated | No crash; partial result or empty list |
| UT-OF-08 | Missing `explanation` → default | `"explanation"` absent | `"No explanation available."` | Fallback text present |
| UT-OF-09 | LLM returns 7 items → capped at 5 | JSON with 7 recommendations | 5 cards returned | `len(cards) == 5` |
| UT-OF-10 | Hallucinated name filtered out | LLM name not in candidate list | Card removed | Only valid names in output |
| UT-OF-11 | Rating cast to float | `"rating": "4.3"` (string) | `rating = 4.3` (float) | `isinstance(card.rating, float)` |
| UT-OF-12 | Empty recommendations list | `{"recommendations": []}` | Empty list returned | `cards == []` |

---

## Level 2 — Integration Tests

### 2.1 Pipeline Integration Tests

| Test ID | Test Description | Modules Involved | Pass Criteria |
|---|---|---|---|
| IT-01 | Full pipeline: input → filter | `input_handler` + `filter_engine` | `len(candidates) > 0` for valid Bangalore Indian query |
| IT-02 | Full pipeline: filter → prompt | `filter_engine` + `prompt_builder` | Prompt contains candidate restaurants |
| IT-03 | Full pipeline: prompt → LLM → cards | `prompt_builder` + `llm_client` + `output_formatter` (mocked LLM) | Returns `List[RecommendationCard]` |
| IT-04 | End-to-end: user input → recommendation | All modules (mocked LLM) | ≥ 1 `RecommendationCard` returned |
| IT-05 | End-to-end with fallback: no filter results | All modules + fallback | System returns broadened results without crash |
| IT-06 | End-to-end with LLM failure | All modules + LLM mock raising error | Fallback top-rated filtered list returned |
| IT-07 | Config loaded correctly into all modules | `config.yaml` + all modules | Budget ranges, model name, max candidates all correct |

---

### 2.2 Data Pipeline Integration

| Test ID | Test Description | Pass Criteria |
|---|---|---|
| IT-D-01 | Load → preprocess produces valid DataFrame | `len(df) > 1000`; no nulls in key columns |
| IT-D-02 | Preprocessed data passes all assertions | `rating ∈ [0,5]`; `cost > 0`; `budget_level ∈ {low,medium,high}` |
| IT-D-03 | Filter on preprocessed data returns correct rows | Location + cuisine + budget + rating all satisfied |

---

## Level 3 — LLM Output Quality Evaluation

> This section defines how to measure the **quality** of LLM-generated recommendations beyond functional correctness.

---

### 3.1 Relevance Score

**Definition:** How well does each recommended restaurant match the user's stated preferences?

**Scoring Method:** Manual 1–5 scale per recommendation field:

| Dimension | Score 1 | Score 3 | Score 5 |
|---|---|---|---|
| **Location Match** | Wrong city entirely | Nearby area | Exact location match |
| **Cuisine Match** | Wrong cuisine | Partially matches | Exact cuisine match |
| **Budget Match** | Far outside range | ±₹150 off | Within specified range |
| **Rating Match** | Below min rating | At min rating | Significantly above min |
| **Explanation Quality** | Generic/empty | Partially specific | Highly personalized, specific |

**Threshold:** Average relevance score ≥ **3.5 / 5** across 20 test queries.

---

### 3.2 Test Query Suite (20 Standardized Queries)

| QID | Location | Budget | Cuisine | Min Rating | Extras |
|---|---|---|---|---|---|
| Q-01 | Bangalore | Medium | Indian | 4.0 | family-friendly |
| Q-02 | Delhi | Low | Chinese | 3.5 | quick service |
| Q-03 | Mumbai | High | Italian | 4.5 | romantic |
| Q-04 | Bangalore | Low | Any | 3.0 | — |
| Q-05 | Chennai | Medium | South Indian | 4.0 | — |
| Q-06 | Hyderabad | High | Continental | 4.0 | fine dining |
| Q-07 | Delhi | Medium | Any | 4.0 | outdoor seating |
| Q-08 | Bangalore | High | Japanese | 4.5 | — |
| Q-09 | Mumbai | Low | Street Food | 3.5 | — |
| Q-10 | Pune | Medium | North Indian | 4.0 | family-friendly |
| Q-11 | Kolkata | Low | Bengali | 3.5 | — |
| Q-12 | Bangalore | Medium | Pizza | 4.0 | quick service |
| Q-13 | Delhi | High | Mughlai | 4.5 | — |
| Q-14 | Chennai | Low | Any | 3.0 | — |
| Q-15 | Bangalore | Low | Any | 0.0 | — |
| Q-16 | Mumbai | Medium | Seafood | 4.0 | waterfront |
| Q-17 | Hyderabad | Medium | Biryani | 4.0 | — |
| Q-18 | Delhi | Low | Fast Food | 3.0 | — |
| Q-19 | Bangalore | High | Any | 4.5 | rooftop |
| Q-20 | Mumbai | High | Multi-cuisine | 4.5 | buffet |

---

### 3.3 LLM Output Quality Metrics

| Metric | Definition | Measurement | Target |
|---|---|---|---|
| **JSON Parse Rate** | % of responses that parse as valid JSON | `successful_parses / total_calls × 100` | ≥ 90% |
| **Hallucination Rate** | % of recommended restaurants not in candidate list | `hallucinated_names / total_recommendations × 100` | ≤ 5% |
| **Rank Consistency** | % of times rank 1 is the highest-rated candidate | Manual check across 20 queries | ≥ 75% |
| **Explanation Specificity** | Avg word count of explanation (proxy for detail) | `mean(len(explanation.split()))` | ≥ 30 words |
| **Cuisine Accuracy** | % recommendations with correct cuisine | `correct_cuisine / total_recs × 100` | ≥ 85% |
| **Budget Compliance** | % recommendations within stated budget range | `within_budget / total_recs × 100` | ≥ 90% |
| **Response Latency** | Time from prompt sent to JSON parsed | `time.time()` before/after LLM call | ≤ 8 seconds (p95) |

---

### 3.4 Prompt Version Comparison

Track metrics across prompt versions to confirm improvements:

| Metric | Prompt v1 | Prompt v2 | Prompt v3 | Prompt v4 | Target |
|---|---|---|---|---|---|
| JSON Parse Rate | — | — | — | — | ≥ 90% |
| Hallucination Rate | — | — | — | — | ≤ 5% |
| Explanation Words (avg) | — | — | — | — | ≥ 30 |
| Budget Compliance | — | — | — | — | ≥ 90% |

> Fill in after running the 20-query test suite against each prompt version.

---

### 3.5 LLM Evaluation Commands

```python
# Run eval suite
results = []
for q in TEST_QUERIES:
    prefs = build_user_preferences(**q)
    candidates = filter_restaurants(df, prefs)
    system_p, user_p = build_prompt(prefs, candidates)
    raw = call_llm(system_p, user_p, config)
    cards = parse_llm_response(raw)
    results.append({
        "query": q,
        "cards": cards,
        "parse_success": len(cards) > 0,
        "hallucinated": [c for c in cards if c.name not in candidates["name"].values]
    })

# Summary
json_parse_rate = sum(r["parse_success"] for r in results) / len(results)
hallucination_rate = sum(len(r["hallucinated"]) for r in results) / (len(results) * 5)
print(f"JSON Parse Rate: {json_parse_rate:.0%}")
print(f"Hallucination Rate: {hallucination_rate:.0%}")
```

---

## Level 4 — UI / UX Evaluation

### 4.1 Functional UI Test Cases

| Test ID | Test Description | Steps | Expected Result | Pass Criteria |
|---|---|---|---|---|
| UI-01 | Happy path: valid inputs → recommendations shown | Fill all fields → click Find | 5 cards displayed | All 5 cards visible with name, rating, cost, explanation |
| UI-02 | Empty location → error shown | Leave location blank → click Find | Error message | `st.error()` visible; no spinner triggered |
| UI-03 | Invalid rating slider behavior | Drag slider to 5.0 → submit | Recommendations for 5-star restaurants | Returns results or "no match" message |
| UI-04 | Dataset loads on startup | Open app | No error on first load | No crash; input form visible immediately |
| UI-05 | Spinner shown during LLM call | Submit valid form | Spinner appears | `"Finding restaurants..."` text visible during wait |
| UI-06 | LLM error → fallback shown | Mock LLM failure → submit | Fallback message | `st.error()` or fallback results shown; no traceback |
| UI-07 | No results → helpful message | Search for impossible combo | Warning displayed | `st.warning()` with suggestions |
| UI-08 | Extras multiselect works | Select 2 extras → submit | Extras in prompt | Verified via LLM prompt log |
| UI-09 | Results refresh on new search | First search → change input → search again | New results shown | Previous cards replaced, not appended |
| UI-10 | Budget selectbox covers all options | Open selectbox | Low, Medium, High visible | All 3 options present |

---

### 4.2 UI Accessibility & UX Checks

| Check | Standard | Pass Criteria |
|---|---|---|
| All inputs labeled | WCAG 2.1 AA | Labels visible above each widget |
| Error messages are readable | Contrast ratio ≥ 4.5:1 | Streamlit default colors pass |
| Submit button is clearly identified | UX best practice | Button text is descriptive (`"Find Restaurants"`) |
| Recommendation cards are scannable | UX best practice | Name, cuisine, rating, cost visible at a glance |
| Mobile layout usable | Responsive | No horizontal scroll at 375px viewport |

---

### 4.3 UI Load & Cache Evaluation

| Test ID | Description | Pass Criteria |
|---|---|---|
| UI-C-01 | Dataset loads only once per session | `@st.cache_data` confirmed active | Second form submit is faster than first |
| UI-C-02 | Cache survives app restart | Restart Streamlit → dataset reloaded from cache | No HuggingFace network call on restart |
| UI-C-03 | Session state isolated between users | Two browser tabs simulating two users | Each tab shows its own results |

---

## Level 5 — Performance Evaluation

### 5.1 Latency Benchmarks

| Stage | Measurement Method | Target (p50) | Target (p95) |
|---|---|---|---|
| Dataset load (first time) | `time.time()` around `load_dataset()` | ≤ 15s | ≤ 30s |
| Dataset load (cached) | `time.time()` around `load_dataset()` | ≤ 1s | ≤ 3s |
| Preprocessing | `time.time()` around `preprocess()` | ≤ 2s | ≤ 5s |
| Filter engine | `time.time()` around `filter_restaurants()` | ≤ 100ms | ≤ 500ms |
| Prompt build | `time.time()` around `build_prompt()` | ≤ 10ms | ≤ 50ms |
| LLM API call | `time.time()` around `call_llm()` | ≤ 4s | ≤ 8s |
| Output parsing | `time.time()` around `parse_llm_response()` | ≤ 5ms | ≤ 20ms |
| **Total end-to-end** | From button click to cards displayed | **≤ 8s** | **≤ 15s** |

---

### 5.2 Load Testing

| Scenario | Concurrent Users | Expected Behavior | Pass Criteria |
|---|---|---|---|
| Light load | 1 user | Normal response | E2E latency ≤ 8s |
| Moderate load | 5 users | Slightly slower | E2E latency ≤ 15s; no crashes |
| Heavy load | 10 users | Rate limiting possible | Retry logic handles 429; no data corruption |

**Load test command (using `locust` or manual multi-tab):**
```bash
locust -f locustfile.py --headless -u 10 -r 2 --run-time 60s
```

---

### 5.3 Memory Usage

| Metric | Target |
|---|---|
| DataFrame in memory | ≤ 200 MB |
| Streamlit session state | ≤ 10 MB per session |
| Peak memory during LLM call | ≤ 300 MB total |

```bash
# Monitor memory
python -m memory_profiler app/main.py
```

---

## Level 6 — Deployment Readiness Checklist

### 6.1 Pre-Deployment Gate

| Check | Criterion | Status |
|---|---|---|
| All unit tests pass | `pytest tests/ -v` exits with code 0 | ☐ |
| All integration tests pass | `pytest tests/integration/` exits with code 0 | ☐ |
| LLM JSON parse rate ≥ 90% | Measured over 20-query suite | ☐ |
| Hallucination rate ≤ 5% | Measured over 20-query suite | ☐ |
| E2E latency ≤ 8s (p50) | Measured with stopwatch / locust | ☐ |
| `.env` not committed | `git ls-files .env` returns empty | ☐ |
| All required env vars documented | `README.md` lists all secrets | ☐ |
| `requirements.txt` is pinned | All packages have `==` version | ☐ |
| App runs with `streamlit run app/main.py` | No import errors on clean venv | ☐ |
| App handles all edge cases gracefully | Manual test of EC-3.1, EC-4.6, EC-3.9 | ☐ |
| Streamlit Cloud secrets configured | `GEMINI_API_KEY` set in dashboard | ☐ |
| `README.md` complete | Setup + usage + architecture link included | ☐ |

---

### 6.2 Smoke Test (Post-Deployment)

After deploying to Streamlit Cloud or Docker, run this quick smoke test:

| Step | Action | Expected |
|---|---|---|
| 1 | Open the deployed URL | Homepage loads without error |
| 2 | Submit: `Bangalore, Medium, Indian, 4.0` | 5 restaurant cards returned |
| 3 | Submit: `Delhi, Low, Any, 3.5` | 5 restaurant cards returned |
| 4 | Submit empty location | Error message shown |
| 5 | Submit: `Atlantis, Low, Any, 0.0` (city not in dataset) | "No results" message shown |
| 6 | Check response time | Within 15 seconds |

---

## Evaluation Summary Dashboard

After running all evaluation levels, populate this summary:

| Level | Total Tests | Passed | Failed | Pass Rate | Status |
|---|---|---|---|---|---|
| L1 — Unit Tests | 67 | — | — | — | ☐ |
| L2 — Integration Tests | 10 | — | — | — | ☐ |
| L3 — LLM Quality (20 queries) | 20 | — | — | — | ☐ |
| L4 — UI Tests | 13 | — | — | — | ☐ |
| L5 — Performance | 5 | — | — | — | ☐ |
| L6 — Deployment Readiness | 12 | — | — | — | ☐ |
| **Total** | **127** | — | — | **Target: ≥ 95%** | ☐ |

---

## Running All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all unit + integration tests
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

# Run LLM quality eval suite
python scripts/run_llm_eval.py

# Check code quality
flake8 app/ --max-line-length=100
black app/ --check

# Run load test (optional)
locust -f locustfile.py --headless -u 5 -r 1 --run-time 30s
```

---

## Evaluation Sign-Off

| Evaluator | Role | Date | Signature |
|---|---|---|---|
| | Developer | | |
| | Reviewer | | |
| | QA Lead | | |

> **Release approved when:** All Level 1–4 tests pass, LLM JSON parse rate ≥ 90%, hallucination rate ≤ 5%, and Level 6 deployment checklist is fully checked off.

---

*Document generated from: [implementation-plan.md](./implementation-plan.md)*
