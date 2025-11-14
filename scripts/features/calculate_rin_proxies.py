#!/usr/bin/env python3
"""
Calculate RIN proxy features from biofuel component prices
Since actual RIN prices aren't available on Yahoo, we calculate economic proxies
that capture the same market signals.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_biofuel_data():
    """Load all biofuel component data from cache and BigQuery"""
    logger.info("Loading biofuel component data...")
    
    # Load the combined biofuel data from cache
    biofuel_df = pd.read_csv('/Users/zincdigital/CBI-V14/cache/yahoo_finance_biofuel/all_biofuel_components.csv')
    biofuel_df['Date'] = pd.to_datetime(biofuel_df['Date'], utc=True)
    
    # Pivot to get one row per date with all symbols as columns
    pivot_df = biofuel_df.pivot_table(
        index='Date',
        columns='symbol',
        values='Close',
        aggfunc='first'
    )
    
    # Load existing commodity data from BigQuery
    logger.info("Loading commodity data from BigQuery...")
    client = bigquery.Client(project='cbi-v14')
    
    query = """
    SELECT 
      date,
      symbol,
      close
    FROM `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr`
    WHERE symbol IN ('ZL=F', 'ZC=F', 'ZS=F', 'CL=F', 'ZM=F')
    ORDER BY date, symbol
    """
    
    commodities_df = client.query(query).to_dataframe()
    commodities_df['date'] = pd.to_datetime(commodities_df['date'])
    
    # Pivot commodities
    commodities = commodities_df.pivot_table(
        index='date',
        columns='symbol',
        values='close',
        aggfunc='first'
    )
    
    # Rename columns for clarity
    commodities.columns = [col.replace('=F', '') for col in commodities.columns]
    pivot_df.columns = [col.replace('=F', '') for col in pivot_df.columns]
    
    # Align on date index
    pivot_df.index = pivot_df.index.tz_localize(None)
    
    # Merge all data
    all_data = pd.concat([commodities, pivot_df], axis=1, join='outer')
    all_data = all_data.reset_index()
    all_data.rename(columns={'index': 'date', 'Date': 'date'}, inplace=True)
    
    logger.info(f"Loaded data for {len(all_data)} dates")
    logger.info(f"Columns: {list(all_data.columns)}")
    return all_data

def calculate_rin_proxies(df):
    """Calculate RIN proxy features from component prices"""
    logger.info("Calculating RIN proxy features...")
    
    # Convert cents/gallon to dollars for consistency
    # HO, RB are in $/gallon already, but check scale
    
    # 1. Biodiesel spread (D4 RIN proxy)
    # When biodiesel is profitable, D4 RINs are cheap
    # When spread is negative, D4 RINs are expensive
    # Formula: Soybean Oil price - (Heating Oil price * 1.2 conversion factor)
    if 'HO' in df.columns and 'ZL' in df.columns:
        df['biodiesel_spread'] = df['ZL'] - (df['HO'] * 12)  # HO in $/gal, ZL in $/cwt
    else:
        df['biodiesel_spread'] = None
    
    # 2. Ethanol spread (D6 RIN proxy)
    # Gasoline value - Corn cost (in energy-equivalent terms)
    # Formula: (Gasoline * 42 gal/barrel) - (Corn * 2.8 bushels/barrel ethanol)
    if 'RB' in df.columns and 'ZC' in df.columns:
        df['ethanol_spread'] = (df['RB'] * 42) - (df['ZC'] / 100 * 2.8)  # ZC in cents/bushel
    else:
        df['ethanol_spread'] = None
    
    # 3. Biofuel crack spread
    # Similar to refinery crack but for biofuels
    # Formula: Oil value (11 lbs/bushel) - Bean cost
    if 'ZL' in df.columns and 'ZS' in df.columns:
        df['biofuel_crack'] = (df['ZL'] * 7.35) - (df['ZS'] / 100 * 11)  # ZS in cents/bushel
    else:
        df['biofuel_crack'] = None
    
    # 4. Natural gas impact (ethanol production cost)
    if 'NG' in df.columns:
        df['nat_gas_impact'] = df['NG']
    else:
        df['nat_gas_impact'] = None
    
    # 5. Sugar-ethanol arbitrage (Brazil dynamics)
    if 'SB' in df.columns and 'ZC' in df.columns:
        df['sugar_ethanol_spread'] = df['SB'] - (df['ZC'] / 100 * 0.5)
    else:
        df['sugar_ethanol_spread'] = None
    
    # 6. Clean energy momentum (regulatory sentiment)
    if 'ICLN' in df.columns:
        df['clean_energy_momentum_30d'] = df['ICLN'].pct_change(periods=30, fill_method=None) * 100
        df['clean_energy_momentum_7d'] = df['ICLN'].pct_change(periods=7, fill_method=None) * 100
    else:
        df['clean_energy_momentum_30d'] = None
        df['clean_energy_momentum_7d'] = None
    
    # 7. Advanced biofuel indicators
    if 'biodiesel_spread' in df.columns and 'ZL' in df.columns:
        df['biodiesel_margin'] = df['biodiesel_spread'] / df['ZL'] * 100  # As % of soy oil price
    else:
        df['biodiesel_margin'] = None
        
    if 'ethanol_spread' in df.columns and 'RB' in df.columns:
        df['ethanol_margin'] = df['ethanol_spread'] / df['RB'] * 100  # As % of gasoline price
    else:
        df['ethanol_margin'] = None
    
    # 8. Cross-commodity ratios
    if 'CL' in df.columns and 'RB' in df.columns:
        df['oil_to_gas_ratio'] = df['CL'] / df['RB']  # Crude to gasoline
    else:
        df['oil_to_gas_ratio'] = None
        
    if 'ZS' in df.columns and 'ZC' in df.columns:
        df['soy_to_corn_ratio'] = df['ZS'] / df['ZC']  # Soybean to corn (both in cents)
    else:
        df['soy_to_corn_ratio'] = None
    
    # 9. Moving averages for stability
    if 'biodiesel_spread' in df.columns and df['biodiesel_spread'].notna().any():
        df['biodiesel_spread_ma30'] = df['biodiesel_spread'].rolling(window=30).mean()
    else:
        df['biodiesel_spread_ma30'] = None
        
    if 'ethanol_spread' in df.columns and df['ethanol_spread'].notna().any():
        df['ethanol_spread_ma30'] = df['ethanol_spread'].rolling(window=30).mean()
    else:
        df['ethanol_spread_ma30'] = None
    
    # 10. Volatility measures
    if 'biodiesel_spread' in df.columns and df['biodiesel_spread'].notna().any():
        df['biodiesel_spread_vol'] = df['biodiesel_spread'].rolling(window=20).std()
    else:
        df['biodiesel_spread_vol'] = None
        
    if 'ethanol_spread' in df.columns and df['ethanol_spread'].notna().any():
        df['ethanol_spread_vol'] = df['ethanol_spread'].rolling(window=20).std()
    else:
        df['ethanol_spread_vol'] = None
    
    # Count non-null features
    feature_cols = ['biodiesel_spread', 'ethanol_spread', 'biofuel_crack', 
                   'nat_gas_impact', 'sugar_ethanol_spread', 
                   'clean_energy_momentum_30d', 'clean_energy_momentum_7d',
                   'biodiesel_margin', 'ethanol_margin', 'oil_to_gas_ratio', 
                   'soy_to_corn_ratio', 'biodiesel_spread_ma30', 'ethanol_spread_ma30',
                   'biodiesel_spread_vol', 'ethanol_spread_vol']
    
    non_null_count = sum(1 for col in feature_cols if col in df.columns and df[col].notna().any())
    logger.info(f"Calculated {non_null_count} RIN proxy features with data")
    
    return df

def save_to_bigquery(df):
    """Save RIN proxy features to BigQuery"""
    logger.info("Saving to BigQuery...")
    
    client = bigquery.Client(project='cbi-v14')
    
    # Prepare data
    df_to_save = df[['date'] + [col for col in df.columns if 'spread' in col or 'margin' in col or 
                                 'momentum' in col or 'crack' in col or 'impact' in col or 
                                 'ratio' in col or '_vol' in col or '_ma' in col]]
    
    # Remove rows with all NaN values
    df_to_save = df_to_save.dropna(how='all', subset=[col for col in df_to_save.columns if col != 'date'])
    
    # Table ID
    table_id = 'cbi-v14.yahoo_finance_comprehensive.rin_proxy_features'
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )
    
    # Load to BigQuery
    job = client.load_table_from_dataframe(df_to_save, table_id, job_config=job_config)
    job.result()
    
    logger.info(f"✅ Saved {len(df_to_save)} rows to {table_id}")
    
    # Show sample
    print("\nSample of RIN proxy features (latest 5 dates):")
    print(df_to_save[['date', 'biodiesel_spread', 'ethanol_spread', 'biofuel_crack', 
                      'clean_energy_momentum_30d']].tail())
    
    return df_to_save

def create_update_sql():
    """Create SQL to update production tables with RIN proxies"""
    
    sql = """
-- Update production_training_data_1m with RIN proxy features
-- These replace the NULL RIN columns with calculated proxies

UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  -- Use biodiesel spread as D4 RIN proxy
  rin_d4_price = COALESCE(r.biodiesel_spread, 0),
  
  -- Use ethanol spread as D6 RIN proxy  
  rin_d6_price = COALESCE(r.ethanol_spread, 0),
  
  -- Use average of spreads as D5 RIN proxy (advanced biofuel)
  rin_d5_price = COALESCE((r.biodiesel_spread + r.ethanol_spread) / 2, 0),
  
  -- Use biofuel crack for RFS mandate proxies
  rfs_mandate_biodiesel = COALESCE(r.biofuel_crack, 0),
  rfs_mandate_advanced = COALESCE(r.biodiesel_margin, 0),
  rfs_mandate_total = COALESCE(r.ethanol_margin, 0)
  
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features` r
WHERE t.date = r.date;

-- Verify the update
SELECT 
  COUNT(*) as total_rows,
  COUNT(rin_d4_price) as d4_filled,
  COUNT(rin_d6_price) as d6_filled,
  AVG(rin_d4_price) as avg_d4_proxy,
  AVG(rin_d6_price) as avg_d6_proxy
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date >= '2020-01-01';
"""
    
    with open('/Users/zincdigital/CBI-V14/bigquery-sql/UPDATE_RIN_PROXIES.sql', 'w') as f:
        f.write(sql)
    
    logger.info("✅ Created UPDATE_RIN_PROXIES.sql")
    return sql

def main():
    """Main execution"""
    print("=" * 70)
    print("RIN PROXY FEATURE CALCULATION")
    print("=" * 70)
    
    # Load data
    df = load_biofuel_data()
    
    # Calculate proxies
    df = calculate_rin_proxies(df)
    
    # Save to BigQuery
    saved_df = save_to_bigquery(df)
    
    # Create update SQL
    create_update_sql()
    
    print("\n" + "=" * 70)
    print("✅ RIN PROXY FEATURES READY!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run UPDATE_RIN_PROXIES.sql to populate production table")
    print("2. Retrain bqml_1m_v2 with filled RIN columns")
    print("3. Expected: Capture biofuel signal (-0.601 correlation)")
    print("\nProxy features created:")
    print("  • biodiesel_spread (D4 RIN proxy)")
    print("  • ethanol_spread (D6 RIN proxy)")
    print("  • biofuel_crack (processing economics)")
    print("  • clean_energy_momentum (regulatory sentiment)")
    print("  • Plus 11 additional derived features")

if __name__ == "__main__":
    main()
