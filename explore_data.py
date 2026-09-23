"""
Phase 2 — Data Exploration & Validation Script

Loads the Zomato dataset, explores its structure, preprocesses it,
and validates the result. Outputs exploration notes.
"""

import sys
sys.path.insert(0, ".")

import yaml
from app.data_loader import load_zomato_data
from app.preprocessor import preprocess, validate

# Load config
with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

# ── Step 1: Load raw data ──────────────────────────────
print("=" * 60)
print("STEP 1: Loading dataset from Hugging Face")
print("=" * 60)
df_raw = load_zomato_data(
    config["data"]["dataset_name"],
    config["data"]["cache_dir"]
)

# ── Step 2: Explore raw data ──────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Data Exploration")
print("=" * 60)

print("\n📋 Columns:")
print(df_raw.columns.tolist())

print("\n📋 Data Types:")
print(df_raw.dtypes)

print("\n📋 Missing Values:")
print(df_raw.isnull().sum())

print("\n📋 Shape:", df_raw.shape)

print("\n📋 Sample 'rate' values:")
if "rate" in df_raw.columns:
    print(df_raw["rate"].unique()[:20])

print("\n📋 Sample 'approx_cost(for two people)' values:")
if "approx_cost(for two people)" in df_raw.columns:
    print(df_raw["approx_cost(for two people)"].unique()[:20])

print("\n📋 Sample locations (first 15 unique):")
if "location" in df_raw.columns:
    print(df_raw["location"].unique()[:15])

print("\n📋 Sample cuisines (first 15 unique):")
if "cuisines" in df_raw.columns:
    print(df_raw["cuisines"].unique()[:15])

# ── Step 3: Preprocess ─────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Preprocessing")
print("=" * 60)
df_clean = preprocess(df_raw, config["budget_ranges"])

# ── Step 4: Validate ───────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Validation")
print("=" * 60)
validate(df_clean)

# ── Step 5: Post-processing summary ───────────────────
print("\n" + "=" * 60)
print("STEP 5: Post-Processing Summary")
print("=" * 60)
print(f"\nCleaned columns: {df_clean.columns.tolist()}")
print(f"\nRating range: {df_clean['rating'].min()} – {df_clean['rating'].max()}")
print(f"Cost range: ₹{df_clean['cost'].min()} – ₹{df_clean['cost'].max()}")
print(f"\nBudget level distribution:")
print(df_clean["budget_level"].value_counts())
print(f"\nTop 10 locations:")
print(df_clean["location_norm"].value_counts().head(10))
print(f"\nSample cleaned data (first 3 rows):")
print(df_clean[["name", "location_norm", "cuisines_norm", "rating", "cost", "budget_level"]].head(3).to_string())
print("\n✅ Phase 2 complete — data is ready for filtering!")
