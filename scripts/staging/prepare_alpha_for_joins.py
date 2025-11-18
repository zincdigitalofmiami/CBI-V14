#!/usr/bin/env python3
"""
Prepare Alpha Vantage data for joining with existing pipeline.
Converts from raw Alpha format to join-ready wide format.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def prepare_alpha_indicators():
    """
    Convert 50+ indicators from separate files to wide format.
    CRITICAL: Must handle 550 API calls worth of data efficiently.
    NO PLACEHOLDERS ALLOWED!
    """
    
    print("="*80)
    print("PREPARING ALPHA INDICATORS FOR JOINS - WITH VALIDATION")
    print("="*80)
    
    # Import validator
    import sys
    sys.path.insert(0, str(DRIVE.parent / "src"))
    from utils.data_validation import AlphaDataValidator
    validator = AlphaDataValidator()
    
    # Step 1: Read all indicator files for each symbol
    indicators_dir = DRIVE / "raw/alpha/indicators/daily"
    staging_dir = DRIVE / "staging/alpha/daily"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    all_symbols_data = []
    
    for symbol in ['CORN', 'WHEAT', 'WTI', 'BRENT', 'NATURAL_GAS', 'COTTON', 'SUGAR', 'COFFEE', 'COPPER', 'ALUMINUM']:
        print(f"\nProcessing {symbol}...")
        
        # Read symbol's indicator file (has all 50+ indicators as columns)
        indicator_file = indicators_dir / f"{symbol}_indicators.parquet"
        if not indicator_file.exists():
            print(f"  ⚠️  Missing indicators for {symbol}")
            continue
        
        df = pd.read_parquet(indicator_file)
        df['symbol'] = symbol
        
        # Ensure date column is consistent
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
        elif 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date']).dt.date
        
        # CRITICAL: Validate before adding to collection
        validator.validate_dataframe(df, 'indicators', symbol)
        
        all_symbols_data.append(df)
        print(f"  ✅ Loaded {len(df)} days, {len(df.columns)} indicators")
    
    # Step 2: Combine all symbols
    combined = pd.concat(all_symbols_data, ignore_index=True)
    print(f"\n✅ Combined: {len(combined)} total rows, {combined['symbol'].nunique()} symbols")
    
    # Step 3: Pivot if needed (if data is in long format)
    # If already wide (each indicator is a column), skip this
    if 'indicator_name' in combined.columns:  # Long format
        print("\nPivoting from long to wide format...")
        combined_wide = combined.pivot_table(
            index=['date', 'symbol'],
            columns='indicator_name',
            values='indicator_value',
            aggfunc='first'
        ).reset_index()
    else:  # Already wide
        combined_wide = combined
        print("\nAlready in wide format")
    
    # Step 3.5: Prefix ALL columns with 'alpha_' except join keys (date, symbol)
    # Industry best practice: source prefix for multi-provider data warehouses
    join_keys = ['date', 'symbol']
    columns_to_prefix = [c for c in combined_wide.columns if c not in join_keys]
    rename_dict = {col: f'alpha_{col}' for col in columns_to_prefix}
    combined_wide = combined_wide.rename(columns=rename_dict)
    print(f"\n✅ Prefixed {len(columns_to_prefix)} indicator columns with 'alpha_'")
    print(f"   Join keys remain unprefixed: {join_keys}")
    
    # Step 4: Validate combined data before saving
    print("\n🔍 Validating combined indicators before saving...")
    validator.validate_dataframe(combined_wide, 'indicators', 'ALL_SYMBOLS')
    
    # Step 5: Save to staging
    output_file = staging_dir / "alpha_indicators_wide.parquet"
    combined_wide.to_parquet(output_file, index=False)
    print(f"\n✅ Saved to staging: {output_file}")
    print(f"   Shape: {combined_wide.shape}")
    
    return combined_wide

def prepare_alpha_prices():
    """Prepare Alpha price data for joining"""
    
    print("\n" + "="*80)
    print("PREPARING ALPHA PRICES")
    print("="*80)
    
    # Import validator
    import sys
    sys.path.insert(0, str(DRIVE.parent / "src"))
    from utils.data_validation import AlphaDataValidator
    validator = AlphaDataValidator()
    
    prices_dir = DRIVE / "raw/alpha/prices/commodities"
    staging_dir = DRIVE / "staging/alpha/daily"
    
    all_prices = []
    
    for price_file in prices_dir.glob("*.parquet"):
        df = pd.read_parquet(price_file)
        symbol = price_file.stem.replace("_daily", "")
        df['symbol'] = symbol
        
        # Standardize date column
        if 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date']).dt.date
        
        # Keep only OHLCV columns
        keep_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        df = df[[c for c in keep_cols if c in df.columns]]
        
        # Prefix price columns with 'alpha_' except join keys
        join_keys = ['date', 'symbol']
        price_cols_to_prefix = [c for c in df.columns if c not in join_keys]
        rename_dict = {col: f'alpha_{col}' for col in price_cols_to_prefix}
        df = df.rename(columns=rename_dict)
        
        # CRITICAL: Validate each symbol's prices
        validator.validate_dataframe(df, 'daily', symbol)
        
        all_prices.append(df)
        print(f"  {symbol}: {len(df)} days (prices prefixed with 'alpha_')")
    
    combined_prices = pd.concat(all_prices, ignore_index=True)
    
    print(f"\n✅ All price columns prefixed with 'alpha_' (except join keys)")
    
    # Validate combined prices before saving
    print("\n🔍 Validating combined prices before saving...")
    validator.validate_dataframe(combined_prices, 'daily', 'ALL_SYMBOLS')
    
    # Save
    output_file = staging_dir / "alpha_prices_combined.parquet"
    combined_prices.to_parquet(output_file, index=False)
    print(f"\n✅ Saved prices: {output_file}")
    
    return combined_prices

def create_join_ready_file():
    """
    Merge prices + indicators into single join-ready file.
    This is what join_spec.yaml will reference.
    """
    
    print("\n" + "="*80)
    print("CREATING JOIN-READY ALPHA FILE")
    print("="*80)
    
    staging_dir = DRIVE / "staging/alpha/daily"
    
    # Read prepared files
    prices = pd.read_parquet(staging_dir / "alpha_prices_combined.parquet")
    indicators = pd.read_parquet(staging_dir / "alpha_indicators_wide.parquet")
    
    # Merge on date + symbol
    merged = prices.merge(
        indicators,
        on=['date', 'symbol'],
        how='outer'
    )
    
    print(f"Merged shape: {merged.shape}")
    print(f"Columns: {merged.shape[1]} total")
    print(f"  - Price columns: 5 (OHLCV)")
    print(f"  - Indicator columns: {merged.shape[1] - 7} (50+ indicators)")
    
    # CRITICAL: Validate merged data before saving
    import sys
    sys.path.insert(0, str(DRIVE.parent / "src"))
    from utils.data_validation import AlphaDataValidator
    validator = AlphaDataValidator()
    print("\n🔍 Validating final join-ready file before saving...")
    validator.validate_dataframe(merged, 'daily', 'ALPHA_COMPLETE')
    
    # Save final join-ready file
    output_file = staging_dir / "alpha_complete_ready_for_join.parquet"
    merged.to_parquet(output_file, index=False)
    
    print(f"\n✅ Join-ready file created: {output_file}")
    print(f"   This is what join_spec.yaml will use!")
    
    return merged

def main():
    """Run complete staging pipeline"""
    
    # 1. Prepare indicators (wide format)
    indicators_df = prepare_alpha_indicators()
    
    # 2. Prepare prices
    prices_df = prepare_alpha_prices()
    
    # 3. Create join-ready file
    final_df = create_join_ready_file()
    
    print("\n" + "="*80)
    print("STAGING PIPELINE COMPLETE")
    print("="*80)
    print(f"Final dataset: {final_df.shape}")
    print(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    print(f"Symbols: {sorted(final_df['symbol'].unique())}")
    print("\nReady for joining with join_spec.yaml!")

if __name__ == "__main__":
    main()

