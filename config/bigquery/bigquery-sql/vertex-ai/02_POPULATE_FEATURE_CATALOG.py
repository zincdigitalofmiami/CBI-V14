import pandas as pd
from google.cloud import bigquery
import re

def get_feature_metadata():
    """Fetches the current feature metadata catalog from BigQuery."""
    client = bigquery.Client(project='cbi-v14')
    query = "SELECT * FROM `cbi-v14.models_v4.feature_metadata_catalog` ORDER BY ordinal_position"
    df = client.query(query).to_dataframe()
    return df

def categorize_features(df):
    """
    Applies a comprehensive set of rules to automatically categorize features
    into factor groups and feature types.
    """
    categorized_df = df.copy()

    # Define categorization rules (extensible)
    # Format: (regex_pattern, factor_group, feature_type)
    rules = [
        # Targets
        (r'^target_', 'TARGET', 'TARGET'),
        
        # Prices
        (r'_price_current$', 'PRICE', 'PRICE_ABSOLUTE'),
        (r'_close$', 'PRICE', 'PRICE_ABSOLUTE'),
        (r'_open$', 'PRICE', 'PRICE_ABSOLUTE'),
        (r'_high$', 'PRICE', 'PRICE_ABSOLUTE'),
        (r'_low$', 'PRICE', 'PRICE_ABSOLUTE'),
        
        # Lags
        (r'_lag\d+$', 'LAGGED_FEATURE', 'LAG'),
        
        # Volatility
        (r'vix', 'VOLATILITY', 'INDEX'),
        (r'atr', 'VOLATILITY', 'TECHNICAL_INDICATOR'),
        (r'bb_', 'VOLATILITY', 'TECHNICAL_INDICATOR'),

        # Momentum
        (r'rsi', 'MOMENTUM', 'TECHNICAL_INDICATOR'),
        (r'macd', 'MOMENTUM', 'TECHNICAL_INDICATOR'),
        (r'roc', 'MOMENTUM', 'TECHNICAL_INDICATOR'),
        (r'momentum', 'MOMENTUM', 'TECHNICAL_INDICATOR'),

        # Trend
        (r'ma_\d+d', 'TREND', 'TECHNICAL_INDICATOR'),

        # Volume
        (r'_volume', 'VOLUME', 'VOLUME'),

        # Monetary Policy
        (r'dxy', 'MONETARY_POLICY', 'INDEX'),
        (r'fed_funds', 'MONETARY_POLICY', 'RATE'),
        (r'yield', 'MONETARY_POLICY', 'RATE'),

        # Positioning
        (r'cftc', 'POSITIONING', 'SENTIMENT'),

        # Substitution Effects (Inflation)
        (r'_spread$', 'SUBSTITUTION_EFFECT', 'PRICE_SPREAD'),
        (r'palm_oil', 'SUBSTITUTION_EFFECT', 'PRICE_ABSOLUTE'),
        (r'rapeseed_oil', 'SUBSTITUTION_EFFECT', 'PRICE_ABSOLUTE'),
        (r'cpi', 'INFLATION', 'INDEX'),
        (r'ppi', 'INFLATION', 'INDEX'),

        # Neural Scores
        (r'_neural_score$', 'NEURAL_FACTOR', 'PROPRIETARY_SCORE'),
        
        # Other Economic
        (r'gdp', 'GROWTH', 'ECONOMIC_INDICATOR'),
        (r'unemployment', 'GROWTH', 'ECONOMIC_INDICATOR'),
    ]

    # Apply rules
    for index, row in categorized_df.iterrows():
        col_name = row['column_name']
        for pattern, factor, f_type in rules:
            if re.search(pattern, col_name, re.IGNORECASE):
                categorized_df.loc[index, 'factor_group'] = factor
                categorized_df.loc[index, 'feature_type'] = f_type
                break # Stop after first match

    return categorized_df

def upload_categorized_features(df):
    """Uploads the updated dataframe back to BigQuery, overwriting the table."""
    client = bigquery.Client(project='cbi-v14')
    table_id = 'cbi-v14.models_v4.feature_metadata_catalog'
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"✅ Successfully uploaded {len(df)} categorized features to {table_id}")

def main():
    """Main execution function."""
    print("Step 1: Fetching existing feature metadata...")
    metadata_df = get_feature_metadata()
    
    print("Step 2: Applying categorization rules...")
    categorized_df = categorize_features(metadata_df)
    
    # Report on categorization coverage
    total_features = len(categorized_df)
    categorized_count = categorized_df['factor_group'].notna().sum()
    coverage = (categorized_count / total_features) * 100
    
    print("\n--- Categorization Report ---")
    print(f"Total Features: {total_features}")
    print(f"Automatically Categorized: {categorized_count} ({coverage:.1f}%)")
    print(f"Remaining to Categorize Manually: {total_features - categorized_count}")
    print("-----------------------------\n")

    print("Step 3: Uploading updated metadata to BigQuery...")
    upload_categorized_features(categorized_df)

if __name__ == "__main__":
    main()
