import pandas as pd
from pathlib import Path

STAGING_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")
TARGET_FILE = STAGING_DIR / "es_daily_aggregated.parquet"

def find_duplicates(file_path):
    """Reads a parquet file and finds duplicate dates."""
    print(f"--- Analyzing {file_path.name} for duplicate dates ---")
    if not file_path.exists():
        print(f"ERROR: File not found at {file_path}")
        return

    df = pd.read_parquet(file_path)
    
    if 'date' not in df.columns:
        print("ERROR: No 'date' column in the DataFrame.")
        return

    duplicates = df[df.duplicated(subset=['date'], keep=False)]

    if duplicates.empty:
        print("✅ No duplicate dates found.")
    else:
        print(f"🚨 Found {len(duplicates)} rows with duplicate dates.")
        print("Duplicate rows:")
        print(duplicates.sort_values('date'))

if __name__ == "__main__":
    find_duplicates(TARGET_FILE)




