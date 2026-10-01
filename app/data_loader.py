"""
Data Loader — loads the Zomato dataset from Hugging Face and caches it locally.

Uses the `datasets` library to fetch the dataset and converts it to a
Pandas DataFrame. Caching ensures repeated runs don't re-download.
"""

import os
import pandas as pd
from datasets import load_dataset


def load_zomato_data(
    dataset_name: str,
    cache_dir: str,
    local_parquet: str = None,
) -> pd.DataFrame:
    """Load the Zomato restaurant dataset from a local pre-processed file or Hugging Face.

    Args:
        dataset_name: Hugging Face dataset identifier
                      (e.g., "ManikaSaini/zomato-restaurant-recommendation").
        cache_dir: Local directory path for caching the downloaded dataset.
        local_parquet: Optional path to a pre-packaged parquet file.

    Returns:
        Pandas DataFrame with restaurant records.

    Raises:
        RuntimeError: If the dataset cannot be loaded after retries.
    """
    if local_parquet and os.path.exists(local_parquet):
        try:
            df = pd.read_parquet(local_parquet)
            print(f"✅ Loaded pre-processed dataset from {local_parquet}: {len(df)} records")
            return df
        except Exception as e:
            print(f"⚠️  Could not read local parquet ({e}), falling back to Hugging Face download...")

    os.makedirs(cache_dir, exist_ok=True)

    for attempt in range(3):
        try:
            dataset = load_dataset(dataset_name, cache_dir=cache_dir)
            df = dataset["train"].to_pandas()
            print(f"✅ Dataset loaded from Hugging Face: {len(df)} records, {len(df.columns)} columns")
            return df
        except Exception as e:
            if attempt < 2:
                print(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying...")
            else:
                raise RuntimeError(
                    f"Failed to load dataset '{dataset_name}' after 3 attempts. "
                    f"Check your network connection and dataset name. Error: {e}"
                )
