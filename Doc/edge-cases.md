# Edge Cases & Corner Scenarios
## AI-Powered Restaurant Recommendation System (Zomato Use Case)

> **Reference:** [implementation-plan.md](./implementation-plan.md)

---

## Overview

This document catalogs all known edge cases, corner scenarios, and failure conditions across every layer of the system. Each case includes the **trigger condition**, **expected behavior**, **recommended handling**, and **test hint** to guide implementation and testing.

---

## Table of Contents

1. [Phase 1 — Project Setup & Config](#phase-1--project-setup--config)
2. [Phase 2 — Data Ingestion & Preprocessing](#phase-2--data-ingestion--preprocessing)
3. [Phase 3 — Input Handler](#phase-3--input-handler)
4. [Phase 3 — Filtering Engine](#phase-3--filtering-engine)
5. [Phase 4 — Prompt Builder](#phase-4--prompt-builder)
6. [Phase 4 — LLM Client](#phase-4--llm-client)
7. [Phase 4 — Output Formatter](#phase-4--output-formatter)
8. [Phase 5 — Streamlit UI](#phase-5--streamlit-ui)
9. [Phase 6 — Testing & Deployment](#phase-6--testing--deployment)
10. [Cross-Cutting Concerns](#cross-cutting-concerns)

---

## Phase 1 — Project Setup & Config

### EC-1.1: Missing `.env` File

| Field | Detail |
|---|---|
| **Trigger** | App starts without a `.env` file or `GEMINI_API_KEY` not set |
| **Impact** | LLM client silently gets `None` as API key; fails at runtime |
| **Expected Behavior** | App should fail fast at startup with a clear error message |
| **Recommended Handling** | Add startup check: `if not os.getenv("GEMINI_API_KEY"): raise EnvironmentError(...)` |
| **Test Hint** | `monkeypatch.delenv("GEMINI_API_KEY")` → assert `EnvironmentError` |

---

### EC-1.2: Malformed `config.yaml`

| Field | Detail |
|---|---|
| **Trigger** | `config.yaml` has invalid YAML syntax or missing required keys (`llm`, `data`, `budget_ranges`) |
| **Impact** | `KeyError` or `yaml.YAMLError` at startup |
| **Expected Behavior** | Fail fast with descriptive config validation error |
| **Recommended Handling** | Validate config schema after loading; list all missing keys in one error |
| **Test Hint** | Pass a dict with missing `llm` key → assert `KeyError` |

---

### EC-1.3: `budget_ranges` Keys Missing or Misspelled

| Field | Detail |
|---|---|
| **Trigger** | `config.yaml` has `budget_ranges.med` instead of `budget_ranges.medium` |
| **Impact** | User selecting "medium" causes `KeyError` in input handler |
| **Expected Behavior** | Startup validation catches it before any request is made |
| **Recommended Handling** | Assert all three keys (`low`, `medium`, `high`) exist at app init |
| **Test Hint** | Load config with `{"low": [...], "high": [...]}` (missing medium) → assert startup error |

---

### EC-1.4: Python Version Incompatibility

| Field | Detail |
|---|---|
| **Trigger** | Running on Python < 3.10 (type hints like `list[str]` fail) |
| **Impact** | `TypeError` at import of `models.py` |
| **Expected Behavior** | Clear error pointing to Python version requirement |
| **Recommended Handling** | Add version check in `main.py`; document requirement in `README.md` |
| **Test Hint** | Document in CI to test on Python 3.10+ only |

---

## Phase 2 — Data Ingestion & Preprocessing

### EC-2.1: Hugging Face Dataset Unavailable (Network Failure)

| Field | Detail |
|---|---|
| **Trigger** | No internet access or HuggingFace is down during first load |
| **Impact** | `ConnectionError` or `requests.exceptions.Timeout` |
| **Expected Behavior** | Attempt 3 retries; fall back to local cache if available |
| **Recommended Handling** | Wrap `load_dataset()` in try/except; check `.cache/` for existing files |
| **Test Hint** | Mock `load_dataset` to raise `ConnectionError` → assert fallback to cache |

---

### EC-2.2: Dataset Schema Changes

| Field | Detail |
|---|---|
| **Trigger** | HuggingFace dataset is updated and column names change (e.g., `rate` → `rating`) |
| **Impact** | `KeyError` in preprocessor when accessing expected columns |
| **Expected Behavior** | Validation step catches missing columns and raises descriptive error |
| **Recommended Handling** | After loading, assert required columns exist: `assert "rate" in df.columns` |
| **Test Hint** | Pass DataFrame with renamed columns → assert `AssertionError` with column name |

---

### EC-2.3: Rating Column has Non-Numeric Values

| Field | Detail |
|---|---|
| **Trigger** | `rate` column contains `"NEW"`, `"-"`, `"3.5/5"`, `"4.1 /5"`, or `NaN` |
| **Impact** | `ValueError` or silent `NaN` propagation if not handled |
| **Expected Behavior** | `parse_rating()` handles all known formats; unknown formats → `None` |
| **Recommended Handling** | Strip `/5`, strip whitespace, handle `NEW`/`-` → `None`, catch `ValueError` → `None` |
| **Test Hint** | `parse_rating("NEW")` → `None`; `parse_rating("3.5/5")` → `3.5`; `parse_rating("-")` → `None` |

---

### EC-2.4: Cost Column Contains Commas or Currency Symbols

| Field | Detail |
|---|---|
| **Trigger** | `approx_cost` has values like `"1,200"`, `"₹800"`, `"500.0"` |
| **Impact** | `int()` conversion fails with `ValueError` |
| **Expected Behavior** | `parse_cost()` strips commas, currency symbols, and converts to int |
| **Recommended Handling** | `re.sub(r"[^\d]", "", str(val))` before `int()` conversion |
| **Test Hint** | `parse_cost("1,200")` → `1200`; `parse_cost("₹800")` → `800`; `parse_cost("")` → `None` |

---

### EC-2.5: All Rows Dropped After Preprocessing

| Field | Detail |
|---|---|
| **Trigger** | Dataset has too many null values in required columns; all rows dropped |
| **Impact** | Empty DataFrame reaches filter engine → zero results for any query |
| **Expected Behavior** | Raise a clear error after preprocessing if DataFrame is empty |
| **Recommended Handling** | `if df.empty: raise ValueError("Preprocessed dataset is empty. Check source data.")` |
| **Test Hint** | Pass DataFrame with all nulls in `rate` column → assert `ValueError` |

---

### EC-2.6: Duplicate Restaurant Entries

| Field | Detail |
|---|---|
| **Trigger** | Same restaurant listed multiple times with slightly different data (e.g., different votes count) |
| **Impact** | Same restaurant recommended multiple times in top-N candidates |
| **Expected Behavior** | Deduplication retains the row with the highest vote count or latest entry |
| **Recommended Handling** | Use `df.drop_duplicates(subset=["name", "location"])` keeping last |
| **Test Hint** | Insert 2 rows with same name+location → assert only 1 remains after preprocessing |

---

### EC-2.7: Cost Value of Zero

| Field | Detail |
|---|---|
| **Trigger** | `approx_cost` parses to `0` (e.g., empty string or `"0"`) |
| **Impact** | `cost > 0` assertion fails; row passes budget filter incorrectly |
| **Expected Behavior** | Rows with cost = 0 are dropped as invalid |
| **Recommended Handling** | Drop rows where `df["cost"] <= 0` after parsing |
| **Test Hint** | Pass row with cost `"0"` → assert it is excluded from cleaned DataFrame |

---

### EC-2.8: Rating Out of Expected Range

| Field | Detail |
|---|---|
| **Trigger** | Parsed rating value exceeds 5.0 or is negative (data corruption) |
| **Impact** | Invalid rows pass min_rating filter; incorrect recommendations |
| **Expected Behavior** | Clamp or drop ratings outside [0, 5] range |
| **Recommended Handling** | `df = df[df["rating"].between(0, 5, inclusive="both")]` |
| **Test Hint** | Insert row with `rating=5.5` → assert it is excluded after validation |

---

## Phase 3 — Input Handler

### EC-3.1: Empty Location String

| Field | Detail |
|---|---|
| **Trigger** | User submits empty string `""` or only whitespace `"   "` as location |
| **Impact** | Filter returns entire dataset or `str.contains("")` matches everything |
| **Expected Behavior** | Raise `ValueError("Location is required.")` before filtering |
| **Recommended Handling** | `if not location.strip(): raise ValueError(...)` |
| **Test Hint** | `build_user_preferences("", "medium", "indian", 3.5, [])` → assert `ValueError` |

---

### EC-3.2: Location with Special Regex Characters

| Field | Detail |
|---|---|
| **Trigger** | User enters `"Koramangala (5th Block)"` or `"Delhi+NCR"` |
| **Impact** | `str.contains()` with `regex=True` raises `re.error` for unescaped special chars |
| **Expected Behavior** | Location is treated as a literal string, not a regex pattern |
| **Recommended Handling** | Use `str.contains(re.escape(location), na=False)` in filter engine |
| **Test Hint** | Filter with location `"Delhi (NCR)"` → assert no regex exception raised |

---

### EC-3.3: Invalid Budget Level

| Field | Detail |
|---|---|
| **Trigger** | User passes `"MEDIUM"` (uppercase) or `"mid"` (unrecognized alias) |
| **Impact** | `KeyError` in `budget_ranges[budget_level]` |
| **Expected Behavior** | Normalize to lowercase before validation; reject unknown values |
| **Recommended Handling** | `budget_level = budget_level.strip().lower()` before lookup |
| **Test Hint** | `build_user_preferences("Delhi", "MEDIUM", ...)` → normalizes to `"medium"` |

---

### EC-3.4: Rating Out of [0, 5] Range

| Field | Detail |
|---|---|
| **Trigger** | User enters `min_rating = -1` or `min_rating = 6` |
| **Impact** | No results (if > 5) or all results returned (if < 0) |
| **Expected Behavior** | `ValueError("Rating must be between 0 and 5.")` |
| **Recommended Handling** | `if not 0 <= min_rating <= 5: raise ValueError(...)` |
| **Test Hint** | `min_rating=5.1` → `ValueError`; `min_rating=0` → valid |

---

### EC-3.5: Cuisine Left Blank

| Field | Detail |
|---|---|
| **Trigger** | User leaves cuisine field empty to search for any cuisine |
| **Impact** | Cuisine filter is skipped — correct behavior, but must be intentional |
| **Expected Behavior** | Empty cuisine string → cuisine filter is skipped entirely |
| **Recommended Handling** | `if prefs.cuisine:` guard in filter engine (already planned) |
| **Test Hint** | `cuisine=""` → filter engine skips cuisine check, returns results of any cuisine |

---

### EC-3.6: Extras List is `None` instead of Empty List

| Field | Detail |
|---|---|
| **Trigger** | UI passes `extras=None` when no extras are selected |
| **Impact** | `", ".join(None)` raises `TypeError` in prompt builder |
| **Expected Behavior** | `None` extras normalized to `[]` in input handler |
| **Recommended Handling** | `extras = extras or []` in `build_user_preferences()` |
| **Test Hint** | Pass `extras=None` → `UserPreferences.extras == []` |

---

### EC-3.7: Very Long User Input Strings

| Field | Detail |
|---|---|
| **Trigger** | User pastes a 1000-character string in location or cuisine field |
| **Impact** | Prompt size explodes; potential token limit breach |
| **Expected Behavior** | Truncate input to max N characters with a warning |
| **Recommended Handling** | `location = location[:100]`; show `st.warning()` if truncated |
| **Test Hint** | Input 200-char location → assert stored as first 100 chars |

---

## Phase 3 — Filtering Engine

### EC-3.8: Location Matches Zero Restaurants

| Field | Detail |
|---|---|
| **Trigger** | User enters a valid city not present in the dataset (e.g., `"Mysuru"`) |
| **Impact** | Empty DataFrame after location filter |
| **Expected Behavior** | Return empty result with a helpful message suggesting nearby cities |
| **Recommended Handling** | If `len(result) == 0` after location filter, return `[]` with `"no_location_match"` flag |
| **Test Hint** | Filter with `location="atlantis"` → assert empty result + message |

---

### EC-3.9: All Filters Together Yield Zero Results

| Field | Detail |
|---|---|
| **Trigger** | Strict combination of location + cuisine + budget + rating leaves 0 rows |
| **Impact** | Prompt builder receives empty DataFrame; LLM prompt has no restaurants |
| **Expected Behavior** | Progressive filter relaxation: drop cuisine → relax budget → relax rating |
| **Recommended Handling** | Tiered fallback: try each relaxation step, stop when ≥ 3 results found |
| **Test Hint** | Set impossible combination → assert fallback activates and returns ≥ 1 result |

---

### EC-3.10: More than `max_candidates` Equally Rated Restaurants

| Field | Detail |
|---|---|
| **Trigger** | 50+ restaurants all have the same top rating (e.g., 4.9) |
| **Impact** | `head(15)` selection is arbitrary; no secondary sort criterion |
| **Expected Behavior** | Secondary sort by `votes` descending for tie-breaking |
| **Recommended Handling** | `df.sort_values(["rating", "votes"], ascending=[False, False]).head(max_candidates)` |
| **Test Hint** | DataFrame with 20 rows all rated 4.9 → assert top 15 are those with highest votes |

---

### EC-3.11: Budget Range Boundary Values

| Field | Detail |
|---|---|
| **Trigger** | Restaurant cost is exactly at a boundary (e.g., cost = ₹300 for `medium` range [300, 700]) |
| **Impact** | `between()` may be exclusive; boundary restaurant excluded incorrectly |
| **Expected Behavior** | Boundary values should be inclusive on both ends |
| **Recommended Handling** | Use `df["cost"].between(min_cost, max_cost, inclusive="both")` |
| **Test Hint** | Restaurant with `cost=300` and `budget="medium"` → assert included in results |

---

### EC-3.12: Dataset Entirely in One City

| Field | Detail |
|---|---|
| **Trigger** | Dataset only contains restaurants from Bangalore; user searches for Delhi |
| **Impact** | Location filter returns empty |
| **Expected Behavior** | Inform user the dataset does not cover their city |
| **Recommended Handling** | After filter, check result length; return message: `"Dataset covers: {unique_cities}"` |
| **Test Hint** | Mock dataset with only `"bangalore"` → filter for `"delhi"` → assert descriptive message |

---

## Phase 4 — Prompt Builder

### EC-4.1: Empty Candidates DataFrame Passed to Prompt Builder

| Field | Detail |
|---|---|
| **Trigger** | Filter engine returns an empty DataFrame (all fallbacks exhausted) |
| **Impact** | Restaurant list in prompt is empty; LLM hallucinates restaurants |
| **Expected Behavior** | Do not call prompt builder with empty candidates; return early |
| **Recommended Handling** | Guard: `if candidates.empty: return None, None` → handle in caller |
| **Test Hint** | `build_prompt(prefs, pd.DataFrame())` → assert returns `None, None` |

---

### EC-4.2: Restaurant Name Contains Special Characters or Quotes

| Field | Detail |
|---|---|
| **Trigger** | Restaurant name like `"McDonald's"` or `"Café \"Bella\""` |
| **Impact** | JSON prompt injection — LLM may misinterpret quotes and break JSON output |
| **Expected Behavior** | Sanitize restaurant name before embedding in prompt |
| **Recommended Handling** | Escape or strip problematic characters; use f-string carefully |
| **Test Hint** | Build prompt with restaurant named `"Mama's & Papa's"` → assert prompt is clean string |

---

### EC-4.3: Prompt Exceeds LLM Token Limit

| Field | Detail |
|---|---|
| **Trigger** | 15 candidates × long restaurant entries + user prefs exceed model's context window |
| **Impact** | LLM API returns `400 Bad Request: context length exceeded` |
| **Expected Behavior** | Reduce max candidates or truncate restaurant descriptions |
| **Recommended Handling** | Estimate token count before sending; reduce `max_candidates` if > 800 tokens |
| **Test Hint** | Generate prompt with 15 very long restaurant entries → assert token count check triggers |

---

### EC-4.4: All Candidates Have Missing Fields

| Field | Detail |
|---|---|
| **Trigger** | Candidate DataFrame rows have `NaN` for `cuisines`, `cost`, or `rating` |
| **Impact** | Prompt contains `"Cuisine: nan"` which confuses the LLM |
| **Expected Behavior** | Replace `NaN` values with `"N/A"` in prompt formatting |
| **Recommended Handling** | `row.get("cuisines", "N/A") or "N/A"` in the prompt list comprehension |
| **Test Hint** | Pass candidate with `cuisines=NaN` → assert prompt shows `"Cuisine: N/A"` |

---

### EC-4.5: No Extras Provided — Prompt Formatting

| Field | Detail |
|---|---|
| **Trigger** | `prefs.extras` is an empty list |
| **Impact** | Prompt shows `"Additional Preferences: "` — empty, looks broken |
| **Expected Behavior** | Show `"Additional Preferences: None"` when extras is empty |
| **Recommended Handling** | `", ".join(prefs.extras) if prefs.extras else "None"` (already in plan, verify) |
| **Test Hint** | Build prompt with `extras=[]` → assert `"None"` appears, not an empty field |

---

## Phase 4 — LLM Client

### EC-4.6: API Key Invalid or Expired

| Field | Detail |
|---|---|
| **Trigger** | `GEMINI_API_KEY` is set but incorrect or revoked |
| **Impact** | API returns `401 Unauthorized` or `403 Forbidden` |
| **Expected Behavior** | Fail immediately (no retry); show clear error: `"Invalid API key"` |
| **Recommended Handling** | Catch auth exceptions separately; do NOT retry on auth failures |
| **Test Hint** | Mock API to return 401 → assert no retry, immediate clear error raised |

---

### EC-4.7: API Rate Limit Exceeded

| Field | Detail |
|---|---|
| **Trigger** | Too many requests in quick succession; API returns `429 Too Many Requests` |
| **Impact** | LLM call fails; user sees error |
| **Expected Behavior** | Retry with exponential backoff (1s → 2s → 4s); show spinner during wait |
| **Recommended Handling** | Detect `429` specifically; use `time.sleep(2 ** attempt)` |
| **Test Hint** | Mock API to return 429 twice then succeed → assert final result is valid |

---

### EC-4.8: LLM API Timeout

| Field | Detail |
|---|---|
| **Trigger** | LLM takes > 30 seconds to respond (network issue or model overload) |
| **Impact** | `requests.Timeout` or hanging Streamlit session |
| **Expected Behavior** | Set explicit timeout on API call; retry up to 3 times |
| **Recommended Handling** | Set `request_options={"timeout": 30}` on API call |
| **Test Hint** | Mock API to sleep 35 seconds → assert `TimeoutError` raised after 30s |

---

### EC-4.9: LLM Returns Empty Response

| Field | Detail |
|---|---|
| **Trigger** | LLM API returns HTTP 200 but `response.text` is empty or `""` |
| **Impact** | `json.loads("")` raises `JSONDecodeError` |
| **Expected Behavior** | Treat empty response as failure; retry once; then use fallback |
| **Recommended Handling** | `if not response.text.strip(): raise ValueError("LLM returned empty response")` |
| **Test Hint** | Mock API to return empty string → assert fallback to sorted filtered list |

---

### EC-4.10: LLM Returns Partial Response (Truncated)

| Field | Detail |
|---|---|
| **Trigger** | `max_tokens=1024` is too low; LLM truncates mid-JSON |
| **Impact** | `json.loads()` fails with `JSONDecodeError` on incomplete JSON |
| **Expected Behavior** | Regex fallback attempts to extract partial data |
| **Recommended Handling** | Increase `max_tokens`; use regex fallback for partial results |
| **Test Hint** | Pass truncated JSON string `'{"recommendations": [{"rank": 1, "name": "X"'` → regex fallback activates |

---

### EC-4.11: LLM Hallucinates Restaurant Names Not in Candidates

| Field | Detail |
|---|---|
| **Trigger** | LLM invents a restaurant `"Golden Dragon Palace"` not in the filtered list |
| **Impact** | User is shown a non-existent restaurant |
| **Expected Behavior** | Cross-validate LLM response names against candidate list |
| **Recommended Handling** | After parsing, filter cards: `[c for c in cards if c.name in candidate_names]` |
| **Test Hint** | LLM response includes name not in candidates → assert that card is removed |

---

### EC-4.12: LLM Returns More or Fewer than 5 Recommendations

| Field | Detail |
|---|---|
| **Trigger** | LLM returns 3 or 7 items instead of exactly 5 |
| **Impact** | UI displays inconsistent number of cards |
| **Expected Behavior** | Accept and display whatever count is returned (1–5); cap at 5 |
| **Recommended Handling** | `cards[:5]` after parsing; log a warning if fewer than 3 returned |
| **Test Hint** | LLM response with 7 items → assert only 5 displayed |

---

## Phase 4 — Output Formatter

### EC-4.13: LLM Returns Plain Text Instead of JSON

| Field | Detail |
|---|---|
| **Trigger** | LLM ignores JSON instruction and returns narrative text |
| **Impact** | `json.loads()` fails; no structured output available |
| **Expected Behavior** | Regex fallback extracts restaurant names and explanations from text |
| **Recommended Handling** | `parse_with_fallback()` uses regex patterns to find numbered list items |
| **Test Hint** | Pass plain-text LLM response → assert at least restaurant names extracted |

---

### EC-4.14: Rank Field is Missing or Non-Integer

| Field | Detail |
|---|---|
| **Trigger** | LLM response has `"rank": "first"` or `"rank": null` |
| **Impact** | `int()` conversion fails; sorting breaks |
| **Expected Behavior** | Default to index position if rank is missing/invalid |
| **Recommended Handling** | `rank = int(item.get("rank", i+1))` with try/except fallback to `i+1` |
| **Test Hint** | JSON with `"rank": "first"` → assert falls back to sequential index |

---

### EC-4.15: Duplicate Ranks in LLM Response

| Field | Detail |
|---|---|
| **Trigger** | LLM assigns rank `1` to two different restaurants |
| **Impact** | Sorting is non-deterministic; user confused about top pick |
| **Expected Behavior** | Re-assign sequential ranks based on list order after sorting |
| **Recommended Handling** | After `sorted()`, re-index: `for i, card in enumerate(cards): card.rank = i+1` |
| **Test Hint** | Two items with `rank=1` → assert output has ranks 1, 2 without duplicates |

---

## Phase 5 — Streamlit UI

### EC-5.1: User Clicks "Find Restaurants" with No Input

| Field | Detail |
|---|---|
| **Trigger** | User clicks button without filling in location or budget |
| **Impact** | Validation error thrown without friendly message |
| **Expected Behavior** | Show inline `st.error()` messages per field; do not trigger search |
| **Recommended Handling** | Validate before calling `build_user_preferences()`; use `st.stop()` on error |
| **Test Hint** | Manual test: submit empty form → assert error message visible, no spinner shown |

---

### EC-5.2: Dataset Reload Failure on App Restart

| Field | Detail |
|---|---|
| **Trigger** | Streamlit `@st.cache_data` cache is cleared; dataset re-load fails on network error |
| **Impact** | App crashes at startup with unhandled exception |
| **Expected Behavior** | Show `st.error("Failed to load dataset. Please refresh.")` with retry option |
| **Recommended Handling** | Wrap `get_data()` in try/except; show error state in UI, not traceback |
| **Test Hint** | Simulate network error in `load_zomato_data` mock → assert Streamlit shows error message |

---

### EC-5.3: User Submits Multiple Rapid Requests

| Field | Detail |
|---|---|
| **Trigger** | User clicks "Find Restaurants" button multiple times quickly |
| **Impact** | Multiple concurrent LLM API calls; race condition on results |
| **Expected Behavior** | Disable submit button during loading; show spinner |
| **Recommended Handling** | Use `st.session_state.loading = True` to disable button while request is in-flight |
| **Test Hint** | Manual test: click button twice rapidly → assert only one spinner shown |

---

### EC-5.4: LLM Takes Too Long — UI Appears Frozen

| Field | Detail |
|---|---|
| **Trigger** | LLM API responds slowly (> 10 seconds) |
| **Impact** | User sees blank spinner with no feedback on progress |
| **Expected Behavior** | Show progress message during wait (e.g., `"Asking AI for recommendations..."`) |
| **Recommended Handling** | Use `st.spinner("Finding the best restaurants for you...")` wrapping LLM call |
| **Test Hint** | Mock slow LLM → assert spinner text is visible |

---

### EC-5.5: Recommendation Cards Have Missing Fields

| Field | Detail |
|---|---|
| **Trigger** | `RecommendationCard.explanation` is empty string or `None` |
| **Impact** | `st.info("")` renders empty blue box |
| **Expected Behavior** | Show fallback message `"No explanation available."` |
| **Recommended Handling** | `card.explanation or "No explanation available."` in display |
| **Test Hint** | Render card with `explanation=""` → assert fallback text appears |

---

### EC-5.6: Non-ASCII Characters in Restaurant Names

| Field | Detail |
|---|---|
| **Trigger** | Restaurant name contains Devanagari, Chinese, or Arabic script (e.g., `"दिल्ली दरबार"`) |
| **Impact** | Streamlit renders fine, but markdown header `### #1 दिल्ली दरबार` may display oddly |
| **Expected Behavior** | Render Unicode characters correctly in the UI |
| **Recommended Handling** | Ensure `st.markdown()` handles UTF-8; set `charset=utf-8` in app config |
| **Test Hint** | Render card with Hindi restaurant name → assert no encoding error |

---

### EC-5.7: Mobile / Narrow Viewport Layout

| Field | Detail |
|---|---|
| **Trigger** | User opens app on a small screen (mobile browser) |
| **Impact** | `st.columns(3)` layout becomes very cramped; metrics unreadable |
| **Expected Behavior** | Layout degrades gracefully; text remains readable |
| **Recommended Handling** | Test with Streamlit's responsive layout; consider single-column fallback |
| **Test Hint** | Manual test at 375px viewport → assert metrics are still legible |

---

## Phase 6 — Testing & Deployment

### EC-6.1: Tests Run Against Live HuggingFace API

| Field | Detail |
|---|---|
| **Trigger** | Unit tests call `load_dataset()` without mocking → slow CI, network-dependent |
| **Impact** | CI pipeline is flaky; tests fail on network issues |
| **Expected Behavior** | All data loading mocked in unit/integration tests |
| **Recommended Handling** | Use `pytest-mock` to mock `load_dataset`; use fixture DataFrames |
| **Test Hint** | `@patch("app.data_loader.load_dataset")` → supply fixture DataFrame |

---

### EC-6.2: Secrets Accidentally Committed to Git

| Field | Detail |
|---|---|
| **Trigger** | Developer commits `.env` file or hardcodes API key in source code |
| **Impact** | API key exposed publicly; security breach |
| **Expected Behavior** | `.gitignore` prevents `.env` from being committed |
| **Recommended Handling** | Add pre-commit hook to scan for API key patterns; use `git-secrets` |
| **Test Hint** | Run `git status` → assert `.env` shows as untracked, not staged |

---

### EC-6.3: Docker Container Missing Environment Variables

| Field | Detail |
|---|---|
| **Trigger** | Docker container started without `--env-file .env` flag |
| **Impact** | App starts but LLM calls fail silently with `None` API key |
| **Expected Behavior** | Container startup fails fast with missing env var error |
| **Recommended Handling** | Add `ENV_CHECK` script in Dockerfile `ENTRYPOINT` to verify required vars |
| **Test Hint** | Start container without `--env-file` → assert container exits with code 1 + error log |

---

### EC-6.4: Streamlit Cloud Secrets Not Configured

| Field | Detail |
|---|---|
| **Trigger** | App deployed to Streamlit Cloud without setting `GEMINI_API_KEY` in secrets |
| **Impact** | App loads but crashes on first recommendation request |
| **Expected Behavior** | Startup check fails with visible error before first user interaction |
| **Recommended Handling** | Check secrets at import time; show `st.error("API key not configured")` on load |
| **Test Hint** | Deploy with missing secret → assert error shown on homepage, not on button click |

---

### EC-6.5: `requirements.txt` Version Conflicts

| Field | Detail |
|---|---|
| **Trigger** | `langchain` or `google-generativeai` updates break API compatibility |
| **Impact** | `AttributeError` or `ImportError` in production |
| **Expected Behavior** | Pin exact versions in `requirements.txt` |
| **Recommended Handling** | Use `pip freeze > requirements.txt`; test upgrade in isolated branch |
| **Test Hint** | CI test that runs `pip install -r requirements.txt` → assert no install errors |

---

## Cross-Cutting Concerns

### EC-X.1: Concurrent Users on Shared Deployment

| Field | Detail |
|---|---|
| **Trigger** | Multiple users submit requests at the same time on Streamlit Cloud |
| **Impact** | LLM API rate limit hit faster; shared cache state confusion |
| **Expected Behavior** | Each user session is isolated; dataset cache is shared read-only |
| **Recommended Handling** | Keep `@st.cache_data` for dataset; keep session state per user |
| **Test Hint** | Load test with 5 concurrent Streamlit sessions → assert no shared state bleed |

---

### EC-X.2: Unicode Encoding in Dataset

| Field | Detail |
|---|---|
| **Trigger** | Location or cuisine names contain special characters (e.g., `"Café"`, `"Città"`) |
| **Impact** | `.str.lower()` or `.str.contains()` may fail on certain pandas versions |
| **Expected Behavior** | Unicode-safe string operations throughout |
| **Recommended Handling** | Ensure Python `str` (not bytes) throughout; test with non-ASCII restaurant entries |
| **Test Hint** | Add row with `location="Café District"` → assert filter works correctly |

---

### EC-X.3: System Locale Differences

| Field | Detail |
|---|---|
| **Trigger** | App deployed on a server with a non-UTF-8 locale |
| **Impact** | `UnicodeDecodeError` when reading/writing files or processing dataset |
| **Expected Behavior** | Explicit UTF-8 encoding enforced everywhere |
| **Recommended Handling** | `open(file, encoding="utf-8")`; set `PYTHONIOENCODING=utf-8` in deployment env |
| **Test Hint** | Run in `LANG=C` locale → assert no encoding errors |

---

### EC-X.4: Logging & Observability Gaps

| Field | Detail |
|---|---|
| **Trigger** | An error occurs in production with no logging; impossible to debug |
| **Impact** | No visibility into which step failed or why |
| **Expected Behavior** | Structured logging at each pipeline step with log levels |
| **Recommended Handling** | Use Python `logging` module; log at INFO for normal flow, ERROR for failures |
| **Test Hint** | Trigger a known error → assert log file contains relevant error message |

---

## Edge Case Test Matrix Summary

| ID | Component | Category | Severity | Handled In |
|---|---|---|---|---|
| EC-1.1 | Config | Missing secret | 🔴 Critical | `main.py` startup |
| EC-1.2 | Config | YAML malformed | 🔴 Critical | Config loader |
| EC-2.1 | Data Loader | Network failure | 🔴 Critical | `data_loader.py` |
| EC-2.2 | Dataset | Schema change | 🔴 Critical | `preprocessor.py` |
| EC-2.3 | Preprocessor | Rating parse | 🟠 High | `parse_rating()` |
| EC-2.4 | Preprocessor | Cost parse | 🟠 High | `parse_cost()` |
| EC-2.5 | Preprocessor | Empty DataFrame | 🔴 Critical | `preprocessor.py` |
| EC-2.6 | Preprocessor | Duplicates | 🟡 Medium | `preprocessor.py` |
| EC-3.1 | Input Handler | Empty location | 🔴 Critical | `input_handler.py` |
| EC-3.2 | Input Handler | Regex injection | 🟠 High | `filter_engine.py` |
| EC-3.3 | Input Handler | Budget casing | 🟡 Medium | `input_handler.py` |
| EC-3.8 | Filter Engine | No results | 🔴 Critical | `filter_engine.py` |
| EC-3.9 | Filter Engine | All filters fail | 🔴 Critical | Fallback logic |
| EC-3.10 | Filter Engine | Tie-breaking | 🟡 Medium | Sort by votes |
| EC-4.1 | Prompt Builder | Empty candidates | 🔴 Critical | Guard clause |
| EC-4.3 | Prompt Builder | Token limit | 🟠 High | Token estimator |
| EC-4.6 | LLM Client | Invalid API key | 🔴 Critical | Auth error handler |
| EC-4.7 | LLM Client | Rate limit | 🟠 High | Retry logic |
| EC-4.9 | LLM Client | Empty response | 🟠 High | Retry + fallback |
| EC-4.11 | LLM Client | Hallucination | 🟠 High | Name validation |
| EC-4.13 | Output Formatter | Plain text response | 🟠 High | Regex fallback |
| EC-4.15 | Output Formatter | Duplicate ranks | 🟡 Medium | Re-index cards |
| EC-5.1 | UI | Empty form submit | 🟠 High | Validation guard |
| EC-5.3 | UI | Rapid re-submit | 🟡 Medium | Session state lock |
| EC-6.2 | Security | Committed secrets | 🔴 Critical | `.gitignore` + hooks |
| EC-X.1 | Concurrency | Multiple users | 🟡 Medium | Session isolation |

---

*Severity Key: 🔴 Critical — blocks core function | 🟠 High — degrades experience | 🟡 Medium — minor impact*

---

*Document generated from: [implementation-plan.md](./implementation-plan.md)*
