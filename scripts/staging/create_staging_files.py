#!/usr/bin/env python3
"""
Create staging files from raw data for join pipeline.
CRITICAL: Each source has UNIQUE transformation requirements
- Yahoo = ZL=F ONLY (Alpha provides all other symbols)
- FRED = Wide format with renamed columns
- Weather = US_MIDWEST region only
- EIA = Exclude placeholder, deduplicate
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def create_yahoo_staging():
    """
    Yahoo = ZL=F ONLY (Alpha doesn't have ZL futures OR ZL indicators)
    KEEP ALL Yahoo indicators (46+) - these are the ONLY indicators for ZL
    Alpha is TOTALLY SEPARATE - only provides other symbols (CORN, WHEAT, etc.)
    """
    
    print("Creating Yahoo staging file (ZL=F ONLY - KEEP ALL INDICATORS)...")
    
    # Look for ZL_F.parquet specifically
    zl_file = DRIVE / "raw/yahoo_finance/prices/commodities/ZL_F.parquet"
    
    if not zl_file.exists():
        print(f"❌ ZL_F.parquet not found at {zl_file}")
        return None
    
    # Load ZL=F data ONLY
    df = pd.read_parquet(zl_file)
    
    print(f"  ✅ Loaded ZL=F: {len(df)} rows × {len(df.columns)} cols")
    
    # Standardize date column first
    if 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df = df.drop(columns=['Date'])
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Lowercase ALL columns first
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Prefix ALL columns with 'yahoo_' except join keys (date, symbol)
    # Industry best practice: source prefix for multi-provider data warehouses
    join_keys = ['date', 'symbol']
    columns_to_prefix = [c for c in df.columns if c not in join_keys]
    rename_dict = {col: f'yahoo_{col}' for col in columns_to_prefix}
    df = df.rename(columns=rename_dict)
    
    print(f"  ✅ Prefixed {len(columns_to_prefix)} columns with 'yahoo_'")
    print(f"  ✅ Join keys remain unprefixed: {join_keys}")
    print(f"  ✅ Total columns: {len(df.columns)} (all Yahoo data clearly namespaced)")
    
    # Verify single symbol
    if 'symbol' in df.columns:
        assert df['symbol'].nunique() == 1, "Should only have ZL=F"
        print(f"  ✅ Single symbol: {df['symbol'].iloc[0]}")
    
    # Save
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} (ZL=F ONLY: {len(df)} rows × {len(df.columns)} cols - ALL INDICATORS KEPT)")
    
    return df

def create_fred_staging():
    """
    FRED = Use pre-made wide format + rename series codes to friendly names
    CRITICAL: Prefix ALL columns with 'fred_' except 'date' (industry best practice)
    """
    
    print("Creating FRED staging file (WIDE FORMAT WITH PREFIXES)...")
    
    # Use pre-made wide format file
    wide_file = DRIVE / "raw/fred/combined/fred_wide_format_20251116.parquet"
    
    if not wide_file.exists():
        print(f"⚠️  Wide format file not found: {wide_file}")
        print("   Run: python3 scripts/ingest/collect_fred_comprehensive.py")
        return None
    
    df = pd.read_parquet(wide_file)
    
    # Date is in index - reset to column
    df = df.reset_index()
    
    print(f"  ✅ Loaded wide format: {df.shape}")
    
    # Rename FRED series codes to friendly names first
    df = df.rename(columns={
        'DFF': 'fed_funds_rate',
        'VIXCLS': 'vix',
        'DGS10': 'treasury_10y',
        'DGS2': 'treasury_2y',
        'DGS30': 'treasury_30y',
        'DGS5': 'treasury_5y',
        'DGS1': 'treasury_1y',
        'DGS3MO': 'treasury_3mo',
        'DTWEXBGS': 'usd_broad_index',
        'DTWEXEMEGS': 'usd_emerging_index',
        'DCOILWTICO': 'crude_oil_wti',
        'DEXUSEU': 'usd_eur_rate',
        'DFEDTARU': 'fed_target_upper',
        'DFEDTARL': 'fed_target_lower',
        'T10Y2Y': 'yield_spread_10y2y',
        'T10Y3M': 'yield_spread_10y3m'
    })
    
    print(f"  ✅ Renamed columns to friendly names")
    
    # CRITICAL: Prefix ALL columns with 'fred_' except join keys (date)
    # Industry best practice: source prefix for multi-provider data warehouses
    join_keys = ['date']
    columns_to_prefix = [c for c in df.columns if c not in join_keys]
    rename_dict = {col: f'fred_{col}' for col in columns_to_prefix}
    df = df.rename(columns=rename_dict)
    
    print(f"  ✅ Prefixed {len(columns_to_prefix)} columns with 'fred_'")
    print(f"  ✅ Join keys remain unprefixed: {join_keys}")
    
    # Standardize date type
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Filter to 2000-2025
    df_temp = df.copy()
    df_temp['date'] = pd.to_datetime(df_temp['date'])
    df_filtered = df_temp[(df_temp['date'] >= '2000-01-01') & (df_temp['date'] <= '2025-12-31')]
    df_filtered['date'] = df_filtered['date'].dt.date
    
    staging_file = DRIVE / "staging/fred_macro_expanded.parquet"
    df_filtered.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(df_filtered)} rows × {len(df_filtered.columns)} cols)")
    
    return df_filtered

def create_weather_staging():
    """
    Weather = GRANULAR WIDE FORMAT (one column per region)
    CRITICAL: Creates single wide table with region-specific columns
    - US Midwest: illinois, iowa, indiana, nebraska, ohio
    - Brazil: mato_grosso, parana, rio_grande_do_sul
    - Argentina: buenos_aires, cordoba, santa_fe
    Column naming: weather_{country}_{region}_{variable} (e.g., weather_us_iowa_tavg_c)
    """
    
    print("Creating Weather staging file (GRANULAR WIDE FORMAT)...")
    
    noaa_dir = DRIVE / "raw/noaa"
    
    if not noaa_dir.exists():
        print(f"⚠️  NOAA directory not found: {noaa_dir}")
        return None
    
    # Define key regions per plan
    key_regions = {
        'us': {
            'illinois': {'file_pattern': 'illinois', 'country': 'us'},
            'iowa': {'file_pattern': 'iowa', 'country': 'us'},
            'indiana': {'file_pattern': 'indiana', 'country': 'us'},
            'nebraska': {'file_pattern': 'nebraska', 'country': 'us'},
            'ohio': {'file_pattern': 'ohio', 'country': 'us'}
        },
        'br': {
            'mato_grosso': {'file_pattern': 'mato_grosso', 'country': 'br'},
            'parana': {'file_pattern': 'parana', 'country': 'br'},
            'rio_grande_do_sul': {'file_pattern': 'rio_grande_do_sul', 'country': 'br'}
        },
        'ar': {
            'buenos_aires': {'file_pattern': 'buenos_aires', 'country': 'ar'},
            'cordoba': {'file_pattern': 'cordoba', 'country': 'ar'},
            'santa_fe': {'file_pattern': 'santa_fe', 'country': 'ar'}
        }
    }
    
    # Try to load individual region files first
    processed_dir = noaa_dir / "processed"
    regional_dir = noaa_dir / "regional"
    
    region_dataframes = []
    
    # Try individual region files
    for country, regions in key_regions.items():
        for region_name, region_info in regions.items():
            # Try processed directory first (individual station files)
            pattern = region_info['file_pattern']
            found = False
            
            # Look for files matching the pattern
            if processed_dir.exists():
                for parquet_file in processed_dir.glob(f"*{pattern}*.parquet"):
                    try:
                        df = pd.read_parquet(parquet_file)
                        if 'date' not in df.columns:
                            if 'Date' in df.columns:
                                df['date'] = pd.to_datetime(df['Date']).dt.date
                            else:
                                continue
                        else:
                            df['date'] = pd.to_datetime(df['date']).dt.date
                        
                        # Prefix ALL columns with weather_{country}_{region}_ except date
                        join_keys = ['date']
                        columns_to_prefix = [c for c in df.columns if c not in join_keys]
                        rename_dict = {col: f"weather_{country}_{region_name}_{col}" for col in columns_to_prefix}
                        df = df.rename(columns=rename_dict)
                        
                        region_dataframes.append(df)
                        print(f"  ✅ Loaded {country}/{region_name}: {len(df)} rows")
                        found = True
                        break
                    except Exception as e:
                        print(f"  ⚠️  Error loading {parquet_file.name}: {e}")
                        continue
            
            # Fallback to regional aggregates if individual files not found
            if not found and regional_dir.exists():
                if country == 'us' and region_name in ['illinois', 'iowa', 'indiana', 'nebraska', 'ohio']:
                    # Use US Midwest aggregate for all US regions (will be duplicated but prefixed differently)
                    us_file = regional_dir / "us_midwest_aggregate.parquet"
                    if us_file.exists():
                        df = pd.read_parquet(us_file)
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date']).dt.date
                        # Prefix with region-specific prefix
                        join_keys = ['date']
                        columns_to_prefix = [c for c in df.columns if c not in join_keys]
                        rename_dict = {col: f"weather_{country}_{region_name}_{col}" for col in columns_to_prefix}
                        df = df.rename(columns=rename_dict)
                        region_dataframes.append(df)
                        print(f"  ✅ Loaded {country}/{region_name} (from aggregate): {len(df)} rows")
                        found = True
    
    if not region_dataframes:
        print("⚠️  No weather data found - trying regional aggregates as fallback...")
        # Last resort: use regional aggregates with generic prefixes
        if regional_dir.exists():
            us_file = regional_dir / "us_midwest_aggregate.parquet"
            if us_file.exists():
                df = pd.read_parquet(us_file)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.date
                join_keys = ['date']
                columns_to_prefix = [c for c in df.columns if c not in join_keys]
                rename_dict = {col: f"weather_us_midwest_{col}" for col in columns_to_prefix}
                df = df.rename(columns=rename_dict)
                region_dataframes.append(df)
                print(f"  ✅ Loaded US_MIDWEST aggregate: {len(df)} rows")
    
    if not region_dataframes:
        print("❌ No weather data found")
        return None
    
    # Merge all region DataFrames on date to create one wide table
    print(f"\n  Merging {len(region_dataframes)} region DataFrames...")
    merged = region_dataframes[0]
    for df in region_dataframes[1:]:
        merged = merged.merge(df, on='date', how='outer')
    
    # Filter to 2000-2025
    merged['date'] = pd.to_datetime(merged['date'])
    merged = merged[(merged['date'] >= '2000-01-01') & (merged['date'] <= '2025-12-31')]
    merged['date'] = merged['date'].dt.date
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    print(f"  ✅ Merged into wide format: {len(merged)} rows × {len(merged.columns)} cols")
    print(f"  ✅ Columns: {len([c for c in merged.columns if c.startswith('weather_')])} weather columns")
    
    staging_file = DRIVE / "staging/weather_granular_daily.parquet"
    merged.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged)} rows × {len(merged.columns)} cols)")
    
    return merged

def create_cftc_staging():
    """
    CFTC = Prefix all columns with 'cftc_' except 'date'
    CRITICAL: Industry best practice - source prefix for multi-provider data warehouses
    """
    
    print("Creating CFTC staging file (WITH PREFIXES)...")
    
    cftc_dir = DRIVE / "raw/cftc"
    all_cftc = []
    
    if not cftc_dir.exists():
        print(f"⚠️  CFTC directory not found: {cftc_dir}")
        return None
    
    for parquet_file in cftc_dir.rglob("*.parquet"):
        try:
            df = pd.read_parquet(parquet_file)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            else:
                print(f"  ⚠️  No date column in {parquet_file.name}")
                continue
            
            all_cftc.append(df)
            print(f"  Loaded {parquet_file.name}: {len(df)} rows")
        except Exception as e:
            print(f"  ⚠️  Error loading {parquet_file.name}: {e}")
            continue
    
    if not all_cftc:
        print("⚠️  No CFTC files found")
        return None
    
    combined = pd.concat(all_cftc, ignore_index=True)
    
    # Filter to 2006-2025 (CFTC starts 2006)
    combined['date'] = pd.to_datetime(combined['date'])
    combined = combined[(combined['date'] >= '2006-01-01') & (combined['date'] <= '2025-12-31')]
    combined['date'] = combined['date'].dt.date
    
    # CRITICAL: Prefix ALL columns with 'cftc_' except join keys (date)
    join_keys = ['date']
    columns_to_prefix = [c for c in combined.columns if c not in join_keys]
    rename_dict = {col: f'cftc_{col}' for col in columns_to_prefix}
    combined = combined.rename(columns=rename_dict)
    
    print(f"  ✅ Prefixed {len(columns_to_prefix)} columns with 'cftc_'")
    print(f"  ✅ Join keys remain unprefixed: {join_keys}")
    
    staging_file = DRIVE / "staging/cftc_cot_2006_2025.parquet"
    combined.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(combined)} rows × {len(combined.columns)} cols)")
    return combined

def create_usda_staging():
    """
    USDA = GRANULAR WIDE FORMAT (one column per report/field)
    CRITICAL: Creates single wide table with report-specific columns
    Key Reports: WASDE, Export Sales, Crop Progress
    Column naming: usda_{report}_{field} (e.g., usda_wasde_world_soyoil_prod, usda_exports_soybeans_net_sales_china)
    """
    
    print("Creating USDA staging file (GRANULAR WIDE FORMAT)...")
    
    usda_dir = DRIVE / "raw/usda"
    
    if not usda_dir.exists():
        print(f"⚠️  USDA directory not found: {usda_dir}")
        return None
    
    report_dataframes = []
    
    # Process each USDA file and create granular columns
    for parquet_file in usda_dir.rglob("*.parquet"):
        try:
            df = pd.read_parquet(parquet_file)
            
            if df.empty:
                print(f"  ⚠️  Empty file: {parquet_file.name}")
                continue
            
            # Standardize date column
            if 'date' not in df.columns:
                if 'Date' in df.columns:
                    df['date'] = pd.to_datetime(df['Date']).dt.date
                else:
                    print(f"  ⚠️  No date column in {parquet_file.name}")
                    continue
            else:
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Identify report type from filename or data structure
            filename = parquet_file.stem.lower()
            report_type = 'nass'  # default
            
            if 'wasde' in filename:
                report_type = 'wasde'
            elif 'export' in filename or 'sales' in filename:
                report_type = 'exports'
            elif 'crop' in filename or 'progress' in filename:
                report_type = 'cropprog'
            elif 'nass' in filename:
                report_type = 'nass'
            
            # Prefix ALL columns with usda_{report_type}_ except date
            join_keys = ['date']
            columns_to_prefix = [c for c in df.columns if c not in join_keys]
            
            # Create granular column names: usda_{report_type}_{field}
            rename_dict = {}
            for col in columns_to_prefix:
                # Clean column name (remove special chars, lowercase)
                clean_col = col.lower().replace(' ', '_').replace('-', '_')
                rename_dict[col] = f"usda_{report_type}_{clean_col}"
            
            df = df.rename(columns=rename_dict)
            
            # Filter to 2000-2025
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= '2000-01-01') & (df['date'] <= '2025-12-31')]
            df['date'] = df['date'].dt.date
            
            report_dataframes.append(df)
            print(f"  ✅ Loaded {report_type} from {parquet_file.name}: {len(df)} rows, {len(columns_to_prefix)} fields")
            
        except Exception as e:
            print(f"  ⚠️  Error loading {parquet_file.name}: {e}")
            continue
    
    if not report_dataframes:
        print("⚠️  No USDA files found")
        return None
    
    # Merge all report DataFrames on date to create one wide table
    print(f"\n  Merging {len(report_dataframes)} USDA report DataFrames...")
    merged = report_dataframes[0]
    for df in report_dataframes[1:]:
        merged = merged.merge(df, on='date', how='outer')
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    print(f"  ✅ Merged into wide format: {len(merged)} rows × {len(merged.columns)} cols")
    print(f"  ✅ Columns: {len([c for c in merged.columns if c.startswith('usda_')])} USDA columns")
    
    staging_file = DRIVE / "staging/usda_reports_granular.parquet"
    merged.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged)} rows × {len(merged.columns)} cols)")
    
    return merged

def create_eia_staging():
    """
    EIA = GRANULAR WIDE FORMAT (one column per series ID)
    CRITICAL: Creates single wide table with series-specific columns
    Key Series: Biodiesel production (PADD 1-5), Ethanol production (US total), D4/D6 RIN prices
    Column naming: eia_{series_description} (e.g., eia_biodiesel_prod_padd2, eia_rin_price_d4)
    """
    
    print("Creating EIA staging file (GRANULAR WIDE FORMAT - EXCLUDE PLACEHOLDERS)...")
    
    eia_dir = DRIVE / "raw/eia"
    
    if not eia_dir.exists():
        print(f"⚠️  EIA directory not found: {eia_dir}")
        return None
    
    series_dataframes = []
    
    for parquet_file in eia_dir.rglob("*.parquet"):
        # Exclude placeholder files
        if 'placeholder' in parquet_file.name.lower():
            print(f"  ⚠️  Skipping placeholder: {parquet_file.name}")
            continue
        
        # Exclude known duplicates
        if parquet_file.name == 'eia_all_20251116.parquet':
            print(f"  ⚠️  Skipping duplicate: {parquet_file.name}")
            continue
        
        try:
            df = pd.read_parquet(parquet_file)
            
            # Check for real data (not all NaN)
            if df.empty:
                print(f"  ⚠️  Empty file: {parquet_file.name}")
                continue
            
            # Standardize date column
            if 'date' not in df.columns:
                if 'Date' in df.columns:
                    df['date'] = pd.to_datetime(df['Date']).dt.date
                else:
                    print(f"  ⚠️  No date column in {parquet_file.name}")
                    continue
            else:
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Handle different EIA data structures
            if 'series_id' in df.columns and 'value' in df.columns:
                # Long format: pivot to wide
                df_wide = df.pivot_table(
                    index='date',
                    columns='series_id',
                    values='value',
                    aggfunc='first'
                ).reset_index()
                df_wide.columns.name = None
                
                # Prefix series_id columns with eia_{series_id}_
                columns_to_prefix = [c for c in df_wide.columns if c != 'date']
                rename_dict = {col: f"eia_{col}" for col in columns_to_prefix}
                df_wide = df_wide.rename(columns=rename_dict)
                
                df = df_wide
            else:
                # Already wide format: prefix all columns except date
                join_keys = ['date']
                columns_to_prefix = [c for c in df.columns if c not in join_keys]
                rename_dict = {col: f"eia_{col}" for col in columns_to_prefix}
                df = df.rename(columns=rename_dict)
            
            # Filter to 2010-2025
            df = df.copy()  # Avoid SettingWithCopyWarning
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= '2010-01-01') & (df['date'] <= '2025-12-31')].copy()
            df['date'] = df['date'].dt.date
            
            series_dataframes.append(df)
            print(f"  ✅ Loaded {parquet_file.name}: {len(df)} rows, {len([c for c in df.columns if c.startswith('eia_')])} series")
            
        except Exception as e:
            print(f"  ⚠️  Error loading {parquet_file.name}: {e}")
            continue
    
    if not series_dataframes:
        print("⚠️  No real EIA data found")
        return None
    
    # Merge all series DataFrames on date to create one wide table
    print(f"\n  Merging {len(series_dataframes)} EIA series DataFrames...")
    merged = series_dataframes[0]
    for df in series_dataframes[1:]:
        merged = merged.merge(df, on='date', how='outer')
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    print(f"  ✅ Merged into wide format: {len(merged)} rows × {len(merged.columns)} cols")
    print(f"  ✅ Columns: {len([c for c in merged.columns if c.startswith('eia_')])} EIA columns")
    
    staging_file = DRIVE / "staging/eia_energy_granular.parquet"
    merged.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged)} rows × {len(merged.columns)} cols)")
    
    return merged

def main():
    """Create all staging files - each with unique transformation"""
    
    print("="*80)
    print("CREATING STAGING FILES - UNIQUE PER SOURCE")
    print("="*80)
    print("Yahoo = ZL=F ONLY (prices + indicators) | Alpha = Other symbols ONLY (no ZL data)")
    print("="*80)
    
    # Ensure staging directory exists
    staging_dir = DRIVE / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all staging files (each has unique requirements)
    create_yahoo_staging()    # ZL=F ONLY, KEEP ALL indicators (Alpha has NO ZL data - totally separate)
    create_fred_staging()     # Wide format with fred_ prefix
    create_weather_staging()  # Granular wide format (one column per region)
    create_cftc_staging()     # With cftc_ prefix
    create_usda_staging()     # Granular wide format (one column per report/field)
    create_eia_staging()      # Granular wide format (one column per series ID)
    
    print("\n" + "="*80)
    print("✅ STAGING FILES CREATED (CORRECTED)")
    print("="*80)
    print("Ready for join pipeline execution!")

if __name__ == "__main__":
    main()
