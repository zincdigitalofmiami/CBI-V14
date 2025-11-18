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
import numpy as np
from pathlib import Path
from datetime import datetime
import re

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
    CRITICAL: Filter to soybean contracts and aggregate to one row per date to avoid cartesian products.
    Since we're modeling ZL=F (soybean oil), we focus on soybean-related contracts.
    """
    
    print("Creating CFTC staging file (SOYBEAN CONTRACTS ONLY - ONE ROW PER DATE)...")
    
    # Load from existing staging file (raw files don't have proper date columns)
    existing_staging = DRIVE / "staging/cftc_commitments.parquet"
    if not existing_staging.exists():
        print(f"⚠️  CFTC staging file not found: {existing_staging}")
        print(f"   Note: Raw CFTC files need to be collected first")
        return None
    
    print(f"  Loading from existing staging file: {existing_staging.name}")
    df = pd.read_parquet(existing_staging)
    
    # Ensure date is date type
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    else:
        print(f"  ⚠️  No date column in staging file")
        return None
    
    # Filter to soybean-related contracts
    market_col = 'cftc_Market_and_Exchange_Names'
    if market_col in df.columns:
        # Find soybean contracts (SOYBEANS and SOYBEAN MEAL)
        soy_mask = df[market_col].str.contains('SOYBEAN', case=False, na=False)
        df = df[soy_mask].copy()
        print(f"  ✅ Filtered to soybean contracts: {len(df)} rows")
        
        if len(df) == 0:
            print("⚠️  No soybean contracts found after filtering")
            return None
        
        # Check if we have multiple contracts per date (SOYBEANS + SOYBEAN MEAL = 2 per date)
        dates_with_multiple = df.groupby('date').size()
        if (dates_with_multiple > 1).any():
            print(f"  ⚠️  Multiple contracts per date detected ({dates_with_multiple.max()} contracts). Aggregating...")
            
            # Group by date and aggregate
            # For position columns (long/short/open_interest), sum them
            # For other numeric columns, take mean
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            non_numeric_cols = [c for c in df.columns if c not in numeric_cols and c != 'date']
            
            agg_dict = {}
            for col in numeric_cols:
                col_lower = col.lower()
                if any(kw in col_lower for kw in ['position', 'long', 'short', 'open_interest', 'spread', 'swap']):
                    agg_dict[col] = 'sum'  # Sum positions
                else:
                    agg_dict[col] = 'mean'  # Average rates/prices/other metrics
            
            # For non-numeric columns, take first value
            for col in non_numeric_cols:
                if col != market_col:
                    agg_dict[col] = 'first'
            
            df = df.groupby('date').agg(agg_dict).reset_index()
            print(f"  ✅ Aggregated to one row per date: {len(df)} rows")
    
    # Ensure all columns are prefixed (should already be, but double-check)
    join_keys = ['date']
    columns_to_prefix = [c for c in df.columns if c not in join_keys and not c.startswith('cftc_')]
    if columns_to_prefix:
        rename_dict = {col: f'cftc_{col}' for col in columns_to_prefix}
        df = df.rename(columns=rename_dict)
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Verify one row per date
    if df['date'].duplicated().any():
        print(f"  ⚠️  WARNING: Still have duplicate dates after aggregation")
        dupes = df[df['date'].duplicated()]['date'].unique()
        print(f"  Duplicate dates: {dupes[:5]}")
    else:
        print(f"  ✅ Verified: One row per date ({len(df)} unique dates)")
    
    print(f"  ✅ Prefixed columns: {len([c for c in df.columns if c.startswith('cftc_')])}")
    print(f"  ✅ Join keys remain unprefixed: {join_keys}")
    
    staging_file = DRIVE / "staging/cftc_commitments.parquet"
    df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(df)} rows × {len(df.columns)} cols)")
    return df

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
                    df['date'] = pd.to_datetime(df['Date'], errors='coerce')
                elif 'year' in df.columns:
                    # USDA data often only has year - create Jan 1 date for each year
                    df['date'] = pd.to_datetime(df['year'].astype(str) + '-01-01', errors='coerce')
                    print(f"  ⚠️  No date column, using year column to create dates: {parquet_file.name}")
                else:
                    print(f"  ⚠️  No date/Date/year column in {parquet_file.name}")
                    continue
            else:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                # If date column is all null but year exists, use year instead
                if df['date'].isna().all() and 'year' in df.columns:
                    print(f"  ⚠️  Date column all null, using year column instead: {parquet_file.name}")
                    # Use first Monday of January (more likely to be a trading day than Jan 1)
                    # Jan 1 is often a holiday, so find first Monday
                    dates = []
                    for year in df['year']:
                        # Start with Jan 1 and find first Monday
                        base_date = pd.Timestamp(year=int(year), month=1, day=1)
                        # If Jan 1 is not Monday (0), find next Monday
                        days_until_monday = (7 - base_date.dayofweek) % 7
                        if days_until_monday == 0 and base_date.dayofweek != 0:
                            days_until_monday = 7
                        first_monday = base_date + pd.Timedelta(days=days_until_monday)
                        dates.append(first_monday)
                    df['date'] = pd.to_datetime(dates, errors='coerce')
            
            # Drop rows with NaT dates
            before_drop = len(df)
            df = df.dropna(subset=['date'])
            after_drop = len(df)
            if before_drop != after_drop:
                print(f"  ⚠️  Dropped {before_drop - after_drop} rows with null dates from {parquet_file.name}")
            
            if df.empty:
                print(f"  ⚠️  All rows had null dates: {parquet_file.name}")
                continue
            
            # Check for long-format USDA data (commodity_desc, statisticcat_desc, value)
            long_format_cols = {'commodity_desc', 'statisticcat_desc', 'value'}
            # Also support alternative naming
            long_format_cols_alt = {'commodity', 'statistic', 'value'}
            
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
            
            if long_format_cols.issubset(df.columns) or long_format_cols_alt.issubset(df.columns):
                def _clean_text(value: str) -> str:
                    value = str(value).lower().strip()
                    value = re.sub(r'[^a-z0-9]+', '_', value)
                    return value.strip('_')
                
                # Use actual column names (commodity_desc or commodity)
                commodity_col = 'commodity_desc' if 'commodity_desc' in df.columns else 'commodity'
                statistic_col = 'statisticcat_desc' if 'statisticcat_desc' in df.columns else 'statistic'
                
                df['pivot_column'] = (
                    df[commodity_col].apply(_clean_text) + "_" + df[statistic_col].apply(_clean_text)
                )
                
                df_wide = df.pivot_table(
                    index='date',
                    columns='pivot_column',
                    values='value',
                    aggfunc='first'
                ).reset_index()
                df_wide.columns.name = None
                feature_cols = []
                for col in df_wide.columns:
                    if col == 'date':
                        feature_cols.append('date')
                    else:
                        feature_cols.append(f"usda_{report_type}_{col}")
                df_wide.columns = feature_cols
                
                # Basic sanity check: if rows explode beyond expected, bail out
                original_dates = df['date'].nunique()
                if original_dates and len(df_wide) > (original_dates * 2):
                    raise ValueError(
                        f"Pivoted USDA data produced {len(df_wide)} rows (expected ~{original_dates}). Aborting to avoid cartesian product."
                    )
                
                df = df_wide.copy()
            
            # Prefix ALL columns with usda_{report_type}_ except date (skip if already prefixed)
            join_keys = ['date']
            columns_to_prefix = [
                c for c in df.columns
                if c not in join_keys and not c.startswith('usda_')
            ]
            
            # Create granular column names: usda_{report_type}_{field}
            rename_dict = {}
            for col in columns_to_prefix:
                # Clean column name (remove special chars, lowercase)
                clean_col = col.lower().replace(' ', '_').replace('-', '_')
                rename_dict[col] = f"usda_{report_type}_{clean_col}"
            
            if rename_dict:
                df = df.rename(columns=rename_dict)
            
            # Filter to 2000-2025
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
    # Filter out empty dataframes
    non_empty = [df for df in report_dataframes if not df.empty]
    if not non_empty:
        print("⚠️  All USDA dataframes are empty, skipping merge.")
        return None
    
    merged = non_empty[0].copy()
    merged_columns = set(merged.columns)
    for df in non_empty[1:]:
        # Keep only columns that are not already in merged (besides the join key)
        new_cols = ['date'] + [c for c in df.columns if c not in merged_columns and c != 'date']
        if len(new_cols) <= 1:
            continue  # nothing new to add
        df_subset = df[new_cols].copy()
        merged = merged.merge(df_subset, on='date', how='outer')
        merged_columns.update(new_cols)
    
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

def create_alpha_staging():
    """
    Combines all raw Alpha Vantage data into a single, prefixed, wide-format staging file.
    CRITICAL: Pivots to ONE ROW PER DATE to avoid cartesian products in joins.
    
    - Excludes treasury data (sourced from FRED instead)
    - Pivots symbol-specific data into wide columns (e.g., alpha_open_eurusd, alpha_rsi_14_spy)
    - Ensures final output has exactly one row per date
    """
    print("Creating Alpha Vantage staging file (PIVOTED TO ONE ROW PER DATE)...")
    
    alpha_dir = DRIVE / "raw/alpha_vantage"
    if not alpha_dir.exists():
        print(f"⚠️  Alpha Vantage raw data directory not found: {alpha_dir}")
        return None
    
    # Separate data by type for proper handling (store as tuples: (df, filename))
    forex_files = []
    technical_files = []
    commodity_files = []
    
    for parquet_file in alpha_dir.glob("*.parquet"):
        # Skip treasury files (FRED has these)
        if 'treasury' in parquet_file.name.lower():
            print(f"  ⏭️  Skipping treasury (sourced from FRED): {parquet_file.name}")
            continue
        
        # Skip ES intraday (needs separate aggregation)
        if 'es_intraday' in parquet_file.name.lower():
            print(f"  ⏭️  Skipping ES intraday (needs separate processing): {parquet_file.name}")
            continue
        
        try:
            df = pd.read_parquet(parquet_file)
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Categorize by file type (store filename too)
            if 'forex' in parquet_file.name.lower():
                forex_files.append((df, parquet_file.name))
                print(f"  Loaded forex: {parquet_file.name} ({len(df)} rows)")
            elif 'technicals' in parquet_file.name.lower():
                technical_files.append((df, parquet_file.name))
                print(f"  Loaded technicals: {parquet_file.name} ({len(df)} rows)")
            elif 'commodity' in parquet_file.name.lower():
                commodity_files.append((df, parquet_file.name))
                print(f"  Loaded commodity: {parquet_file.name} ({len(df)} rows)")
            else:
                print(f"  ⚠️  Unknown type: {parquet_file.name}")
        except Exception as e:
            print(f"  ⚠️  Error loading {parquet_file.name}: {e}")
    
    print(f"\n  Loaded: {len(forex_files)} forex, {len(technical_files)} technicals, {len(commodity_files)} commodities")
    
    if not (forex_files or technical_files or commodity_files):
        print("⚠️  No Alpha Vantage files found to stage.")
        return None
    
    # Start with an empty merged DataFrame
    merged_df = None
    
    # Process forex: Pivot each pair into its own columns
    if forex_files:
        print(f"\n  Processing {len(forex_files)} forex pairs...")
        for df, filename in forex_files:
            if df.empty or 'symbol' not in df.columns:
                continue
            
            symbol = df['symbol'].iloc[0].lower() if not df['symbol'].isna().all() else 'unknown'
            # Rename value columns to include symbol
            value_cols = [c for c in df.columns if c not in ['date', 'symbol']]
            rename_dict = {col: f"alpha_{col}_{symbol}" for col in value_cols}
            df_pivoted = df[['date'] + value_cols].rename(columns=rename_dict)
            
            # Merge into main DataFrame
            if merged_df is None:
                merged_df = df_pivoted
            else:
                merged_df = merged_df.merge(df_pivoted, on='date', how='outer')
    
    # Process technicals: Extract symbol from filename and include in column names
    if technical_files:
        print(f"\n  Processing {len(technical_files)} technical indicator files...")
        for df, filename in technical_files:
            if df.empty:
                continue
            
            # Extract symbol from filename: technicals_SPY.parquet -> SPY
            symbol = filename.replace('technicals_', '').replace('.parquet', '').lower()
            
            # Rename all value columns to include symbol
            value_cols = [c for c in df.columns if c != 'date']
            rename_dict = {col: f"alpha_{col}_{symbol}" for col in value_cols}
            df_pivoted = df.rename(columns=rename_dict)
            
            # Merge into main DataFrame
            if merged_df is None:
                merged_df = df_pivoted
            else:
                merged_df = merged_df.merge(df_pivoted, on='date', how='outer')
            
            print(f"    ✅ Pivoted {symbol.upper()}: {len(value_cols)} indicators")
    
    # Process commodities: Each is a separate price series (already unique names like price_wti)
    if commodity_files:
        print(f"\n  Processing {len(commodity_files)} commodity files...")
        for df, filename in commodity_files:
            if df.empty:
                continue
            
            # Commodities already have unique names (price_wti, price_brent, etc.)
            value_cols = [c for c in df.columns if c != 'date']
            rename_dict = {col: f"alpha_{col}" for col in value_cols}
            df_prefixed = df.rename(columns=rename_dict)
            
            # Merge into main DataFrame
            if merged_df is None:
                merged_df = df_prefixed
            else:
                merged_df = merged_df.merge(df_prefixed, on='date', how='outer')
    
    if merged_df is None:
        print("⚠️  No data to stage")
        return None
    
    # Sort by date
    merged_df = merged_df.sort_values('date').reset_index(drop=True)
    
    # Verify one row per date
    unique_dates = merged_df['date'].nunique()
    total_rows = len(merged_df)
    if total_rows != unique_dates:
        print(f"  ⚠️  WARNING: {total_rows} rows but {unique_dates} unique dates")
        dupes = merged_df.groupby('date').size()
        if (dupes > 1).any():
            print(f"  ⚠️  {(dupes > 1).sum()} dates have multiple rows - CARTESIAN PRODUCT RISK")
    else:
        print(f"  ✅ Verified: One row per date ({unique_dates} unique dates)")
    
    staging_file = DRIVE / "staging/alpha_vantage_features.parquet"
    merged_df.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged_df)} rows × {len(merged_df.columns)} cols)")
    
    return merged_df

def create_volatility_staging():
    """
    Creates volatility staging file from raw volatility data.
    - Loads raw volatility parquet files (VIX + realized vol)
    - Applies 'vol_' prefix to all columns except 'date'
    - Merges multiple files if present
    """
    print("Creating volatility staging file (VIX + realized vol)...")
    
    volatility_dir = DRIVE / "raw/volatility"
    if not volatility_dir.exists():
        print(f"⚠️  Volatility raw data directory not found: {volatility_dir}")
        return None
    
    # Find all volatility parquet files
    vol_files = list(volatility_dir.glob("volatility_*.parquet"))
    
    if not vol_files:
        print("⚠️  No volatility files found")
        return None
    
    # Load and combine all volatility files
    all_dfs = []
    for vol_file in vol_files:
        try:
            df = pd.read_parquet(vol_file)
            # Ensure date column exists and is date type
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            elif 'timestamp' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                df = df.drop(columns=['timestamp'])
            all_dfs.append(df)
            print(f"  ✅ Loaded {vol_file.name}: {len(df)} rows")
        except Exception as e:
            print(f"  ⚠️  Error loading {vol_file.name}: {e}")
            continue
    
    if not all_dfs:
        print("⚠️  No volatility data loaded")
        return None
    
    # Combine all dataframes (merge on date)
    merged = all_dfs[0].copy()
    for df in all_dfs[1:]:
        merged = merged.merge(df, on='date', how='outer', suffixes=('', '_dup'))
        # Remove duplicate columns
        merged = merged.loc[:, ~merged.columns.str.endswith('_dup')]
    
    # Prefix all columns except 'date' with 'vol_'
    join_keys = ['date']
    columns_to_prefix = [c for c in merged.columns if c not in join_keys]
    rename_dict = {col: f'vol_{col}' if not col.startswith('vol_') else col for col in columns_to_prefix}
    merged = merged.rename(columns=rename_dict)
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    staging_file = DRIVE / "staging/volatility_daily.parquet"
    merged.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged)} rows × {len(merged.columns)} cols)")
    return merged

def create_policy_trump_staging():
    """
    Creates policy/Trump staging file from raw policy data.
    - Loads raw policy_trump parquet files
    - Applies 'policy_trump_' prefix (already applied in collector, but ensure consistency)
    - Merges multiple files if present
    """
    print("Creating policy/Trump staging file...")
    
    policy_dir = DRIVE / "raw/policy_trump"
    if not policy_dir.exists():
        print(f"⚠️  Policy/Trump raw data directory not found: {policy_dir}")
        return None
    
    # Find all policy parquet files
    policy_files = list(policy_dir.glob("policy_trump_*.parquet"))
    
    if not policy_files:
        print("⚠️  No policy/Trump files found")
        return None
    
    # Load and combine all policy files
    all_dfs = []
    for policy_file in policy_files:
        try:
            df = pd.read_parquet(policy_file)
            # Ensure date column exists
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            elif 'timestamp' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
            all_dfs.append(df)
            print(f"  ✅ Loaded {policy_file.name}: {len(df)} rows")
        except Exception as e:
            print(f"  ⚠️  Error loading {policy_file.name}: {e}")
            continue
    
    if not all_dfs:
        print("⚠️  No policy/Trump data loaded")
        return None
    
    # Combine all dataframes (merge on date, outer join to keep all)
    merged = all_dfs[0].copy()
    for df in all_dfs[1:]:
        # Remove duplicate columns before merging
        cols_to_drop = [c for c in df.columns if c in merged.columns and c != 'date']
        df_clean = df.drop(columns=cols_to_drop) if cols_to_drop else df
        merged = merged.merge(df_clean, on='date', how='outer', suffixes=('', '_dup'))
        # Remove duplicate columns
        merged = merged.loc[:, ~merged.columns.str.endswith('_dup')]
    
    # Ensure all columns (except date/timestamp) have 'policy_trump_' prefix
    join_keys = ['date', 'timestamp']
    columns_to_prefix = [c for c in merged.columns if c not in join_keys and not c.startswith('policy_trump_')]
    if columns_to_prefix:
        rename_dict = {col: f'policy_trump_{col}' for col in columns_to_prefix}
        merged = merged.rename(columns=rename_dict)
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    staging_file = DRIVE / "staging/policy_trump_signals.parquet"
    merged.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged)} rows × {len(merged.columns)} cols)")
    return merged

def create_palm_staging():
    """
    Creates palm oil staging file from raw Barchart data.
    - Loads palm historical + daily files
    - Applies 'barchart_palm_' prefix (already applied, but ensure consistency)
    - Merges historical + daily data
    """
    print("Creating palm oil staging file (Barchart)...")
    
    barchart_dir = DRIVE / "raw/barchart"
    if not barchart_dir.exists():
        print(f"⚠️  Barchart raw data directory not found: {barchart_dir}")
        return None
    
    # Find palm files
    palm_files = list(barchart_dir.glob("*palm*.parquet"))
    
    if not palm_files:
        print("⚠️  No palm oil files found")
        return None
    
    # Load and combine palm files
    all_dfs = []
    for palm_file in palm_files:
        try:
            df = pd.read_parquet(palm_file)
            # Ensure date column exists
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            all_dfs.append(df)
            print(f"  ✅ Loaded {palm_file.name}: {len(df)} rows")
        except Exception as e:
            print(f"  ⚠️  Error loading {palm_file.name}: {e}")
            continue
    
    if not all_dfs:
        print("⚠️  No palm data loaded")
        return None
    
    # Combine all dataframes (merge on date, outer join)
    merged = all_dfs[0].copy()
    for df in all_dfs[1:]:
        # Remove duplicate columns before merging
        cols_to_drop = [c for c in df.columns if c in merged.columns and c != 'date']
        df_clean = df.drop(columns=cols_to_drop) if cols_to_drop else df
        merged = merged.merge(df_clean, on='date', how='outer', suffixes=('', '_dup'))
        # Remove duplicate columns
        merged = merged.loc[:, ~merged.columns.str.endswith('_dup')]
    
    # Ensure all columns (except date) have 'barchart_palm_' prefix
    join_keys = ['date']
    columns_to_prefix = [c for c in merged.columns if c not in join_keys and not c.startswith('barchart_palm_')]
    if columns_to_prefix:
        rename_dict = {col: f'barchart_palm_{col}' for col in columns_to_prefix}
        merged = merged.rename(columns=rename_dict)
    
    # Sort by date and remove duplicates
    merged = merged.sort_values('date').reset_index(drop=True)
    merged = merged.drop_duplicates(subset=['date'], keep='last')
    
    staging_file = DRIVE / "staging/barchart_palm_daily.parquet"
    merged.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(merged)} rows × {len(merged.columns)} cols)")
    return merged

def create_es_staging():
    """
    Creates ES futures staging file from Yahoo Finance data.
    - Loads es_daily_yahoo.parquet (25 years of ES data with technical indicators)
    - All columns already have 'es_' prefix (from collection script)
    - Ensures one row per date
    """
    print("Creating ES futures staging file (Yahoo Finance)...")
    
    alpha_dir = DRIVE / "raw/alpha_vantage"
    es_file = alpha_dir / "es_daily_yahoo.parquet"
    
    if not es_file.exists():
        print(f"⚠️  ES daily file not found: {es_file}")
        return None
    
    try:
        df = pd.read_parquet(es_file)
        
        # Ensure date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        else:
            print("⚠️  No date column found in ES data")
            return None
        
        # Ensure all columns (except date, symbol) have 'es_' prefix
        join_keys = ['date', 'symbol']
        columns_to_prefix = [
            c for c in df.columns 
            if c not in join_keys and not c.startswith('es_')
        ]
        if columns_to_prefix:
            rename_dict = {col: f'es_{col}' for col in columns_to_prefix}
            df = df.rename(columns=rename_dict)
        
        # Remove duplicates (keep last)
        df = df.drop_duplicates(subset=['date'], keep='last')
        df = df.sort_values('date').reset_index(drop=True)
        
        # Filter to 2000-2025
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= '2000-01-01') & (df['date'] <= '2025-12-31')].copy()
        df['date'] = df['date'].dt.date
        
        staging_file = DRIVE / "staging/es_futures_daily.parquet"
        df.to_parquet(staging_file, index=False)
        
        es_cols = [c for c in df.columns if c.startswith('es_')]
        print(f"✅ Created: {staging_file} ({len(df)} rows × {len(df.columns)} cols)")
        print(f"   ES columns: {len(es_cols)} (OHLCV + technical indicators)")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
        
    except Exception as e:
        print(f"⚠️  Error creating ES staging: {e}")
        return None

def main():
    """
    Main function to generate all staging files.
    """
    
    print("="*80)
    print("CREATING STAGING FILES - UNIQUE PER SOURCE")
    print("="*80)
    print("Yahoo = ZL=F ONLY (prices + indicators) | Alpha = Other symbols ONLY (no ZL data)")
    print("="*80)
    
    # Ensure staging directory exists
    staging_dir = DRIVE / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all staging files (each has unique requirements)
    create_yahoo_staging()        # ZL=F ONLY, KEEP ALL indicators (Alpha has NO ZL data - totally separate)
    create_fred_staging()         # Wide format with prefixes
    create_weather_staging()      # Granular wide format
    create_cftc_staging()         # Prefixed columns
    create_usda_staging()         # Granular wide format (one column per report/field)
    create_eia_staging()          # Granular wide format (one column per series ID)
    create_alpha_staging()        # Wide format with prefixes
    create_volatility_staging()   # VIX + realized vol with vol_ prefix
    create_policy_trump_staging() # Policy/Trump signals with policy_trump_ prefix
    create_palm_staging()         # Palm oil with barchart_palm_ prefix
    create_es_staging()           # ES futures with es_ prefix (25 years + technicals)
    
    print("\n" + "="*80)
    print("✅ STAGING FILES CREATED (CORRECTED)")
    print("="*80)
    print("Ready for join pipeline execution!")

if __name__ == "__main__":
    main()
