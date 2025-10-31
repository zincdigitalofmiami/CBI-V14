#!/usr/bin/env python3
"""
LOAD REAL HISTORICAL VIX DATA
The current VIX data is in 2025 (future/mock data)
We need REAL VIX data for 2020-2024
"""

import yfinance as yf
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta

client = bigquery.Client(project='cbi-v14')

def load_historical_vix():
    """Load REAL historical VIX data from Yahoo Finance"""
    
    print("LOADING REAL HISTORICAL VIX DATA")
    print("=" * 80)
    
    # Download VIX data (^VIX is the Yahoo Finance ticker)
    print("\n1. Downloading VIX from Yahoo Finance...")
    ticker = "^VIX"
    start_date = "2018-01-01"
    end_date = "2024-12-31"
    
    try:
        vix_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if vix_data.empty:
            print("  ❌ No data downloaded")
            return False
            
        print(f"  ✅ Downloaded {len(vix_data)} days of VIX data")
        print(f"  Date range: {vix_data.index[0].date()} to {vix_data.index[-1].date()}")
        print(f"  VIX range: {float(vix_data['Close'].min()):.2f} to {float(vix_data['Close'].max()):.2f}")
        
        # Prepare for BigQuery - handle multi-level columns
        vix_df = vix_data.reset_index()
        
        # If columns are multi-level, flatten them
        if isinstance(vix_df.columns, pd.MultiIndex):
            vix_df.columns = [col[0] if isinstance(col, tuple) else col for col in vix_df.columns]
        
        # Now rename the flattened columns
        vix_df = vix_df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high', 
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Select only needed columns
        vix_df = vix_df[['date', 'open', 'high', 'low', 'close', 'volume']]
        
        # Convert date to datetime
        vix_df['date'] = pd.to_datetime(vix_df['date'])
        
        print(f"\n2. Sample data:")
        print(vix_df.head())
        
        # Delete old future/mock data
        print("\n3. Deleting old mock/future VIX data...")
        delete_query = """
        DELETE FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        WHERE date >= '2025-01-01'
        """
        try:
            client.query(delete_query).result()
            print("  ✅ Deleted future/mock data")
        except Exception as e:
            print(f"  ⚠️ Could not delete old data: {e}")
        
        # Load to BigQuery
        print("\n4. Loading to BigQuery...")
        table_id = "cbi-v14.forecasting_data_warehouse.vix_daily"
        
        # Check what dates already exist
        check_query = """
        SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as rows
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        WHERE date < '2025-01-01'
        """
        result = client.query(check_query).result()
        for row in result:
            if row.rows > 0:
                print(f"  Existing data: {row.min_date} to {row.max_date} ({row.rows} rows)")
                # Filter to only new dates
                vix_df = vix_df[vix_df['date'] > pd.Timestamp(row.max_date)]
                print(f"  Adding {len(vix_df)} new rows")
        
        if len(vix_df) > 0:
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema=[
                    bigquery.SchemaField("date", "DATE"),
                    bigquery.SchemaField("open", "FLOAT64"),
                    bigquery.SchemaField("high", "FLOAT64"),
                    bigquery.SchemaField("low", "FLOAT64"),
                    bigquery.SchemaField("close", "FLOAT64"),
                    bigquery.SchemaField("volume", "FLOAT64"),
                ]
            )
            
            job = client.load_table_from_dataframe(vix_df, table_id, job_config=job_config)
            job.result()
            
            print(f"  ✅ Loaded {len(vix_df)} rows to BigQuery")
        else:
            print("  ℹ️ No new data to add")
        
        # Verify
        print("\n5. Verifying loaded data...")
        verify_query = """
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(*) as total_rows,
            MIN(close) as min_vix,
            MAX(close) as max_vix,
            AVG(close) as avg_vix
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        WHERE date BETWEEN '2020-01-01' AND '2024-12-31'
        """
        
        result = client.query(verify_query).result()
        for row in result:
            print(f"  Date range: {row.min_date} to {row.max_date}")
            print(f"  Total rows: {row.total_rows}")
            print(f"  VIX range: {row.min_vix:.2f} to {row.max_vix:.2f}")
            print(f"  Average VIX: {row.avg_vix:.2f}")
            
            if row.total_rows > 500:
                print("\n  ✅ Successfully loaded historical VIX data!")
                return True
            else:
                print("\n  ⚠️ Limited data loaded")
                return False
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def rebuild_vix_signal_with_real_data():
    """Rebuild VIX signal using the real historical data"""
    
    print("\n6. Rebuilding VIX signal with REAL data...")
    
    # Use the smart VIX calculation but with real historical data
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_vix_stress_signal` AS
    WITH vix_features AS (
        SELECT 
            date,
            close as vix_current,
            
            -- Moving averages
            AVG(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as vix_5d_ma,
            AVG(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as vix_20d_ma,
            AVG(close) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as vix_50d_ma,
            
            -- Rate of change
            (close - LAG(close, 1) OVER (ORDER BY date)) / NULLIF(LAG(close, 1) OVER (ORDER BY date), 0) as vix_1d_roc,
            (close - LAG(close, 5) OVER (ORDER BY date)) / NULLIF(LAG(close, 5) OVER (ORDER BY date), 0) as vix_5d_roc,
            
            -- Volatility of VIX
            STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as vix_20d_std,
            
            -- Historical percentile (within last 252 trading days)
            PERCENT_RANK() OVER (ORDER BY close) as vix_percentile_all,
            PERCENT_RANK() OVER (
                PARTITION BY CASE WHEN date >= DATE_SUB(CURRENT_DATE(), INTERVAL 252 DAY) THEN 1 ELSE 0 END
                ORDER BY close
            ) as vix_percentile_1y,
            
            -- Min/Max for normalization
            MIN(close) OVER (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as vix_52w_min,
            MAX(close) OVER (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as vix_52w_max
            
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        WHERE date BETWEEN '2018-01-01' AND '2024-12-31'  -- Use real historical data only
    )
    SELECT 
        date,
        vix_current,
        vix_20d_ma,
        
        -- Smart VIX signal combining multiple factors
        GREATEST(0, LEAST(1, 
            vix_percentile_all * 0.3 +  -- Historical position
            CASE 
                WHEN vix_current > 30 THEN 0.3
                WHEN vix_current > 25 THEN 0.2
                WHEN vix_current > 20 THEN 0.1
                ELSE 0
            END +
            CASE 
                WHEN vix_5d_roc > 0.2 THEN 0.2  -- Rapid increase
                WHEN vix_5d_roc > 0.1 THEN 0.1
                WHEN vix_5d_roc < -0.1 THEN -0.1
                ELSE 0
            END +
            CASE 
                WHEN vix_current > vix_20d_ma * 1.2 THEN 0.2  -- Above trend
                WHEN vix_current > vix_20d_ma THEN 0.1
                WHEN vix_current < vix_20d_ma * 0.8 THEN -0.1
                ELSE 0
            END
        )) as vix_signal,
        
        -- Additional features
        vix_percentile_all as vix_percentile,
        vix_5d_roc as vix_momentum,
        SAFE_DIVIDE(vix_current - vix_20d_ma, vix_20d_ma) as vix_trend_deviation,
        SAFE_DIVIDE(vix_current - vix_20d_ma, NULLIF(vix_20d_std, 0)) as vix_zscore,
        
        -- Regime
        CASE 
            WHEN vix_current > 40 THEN 'EXTREME'
            WHEN vix_current > 30 THEN 'CRISIS'
            WHEN vix_current > 25 THEN 'ELEVATED'
            WHEN vix_current > 20 THEN 'MODERATE'
            WHEN vix_current > 15 THEN 'NORMAL'
            ELSE 'LOW'
        END as vix_regime
        
    FROM vix_features
    WHERE date >= '2020-01-01'  -- Match our training data range
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        print("  ✅ Rebuilt VIX signal with real historical data")
        
        # Verify
        verify_query = """
        SELECT 
            COUNT(*) as rows,
            MIN(date) as min_date,
            MAX(date) as max_date,
            MIN(vix_signal) as min_signal,
            MAX(vix_signal) as max_signal,
            STDDEV(vix_signal) as std_signal
        FROM `cbi-v14.signals.vw_vix_stress_signal`
        WHERE date BETWEEN '2020-01-01' AND '2024-05-06'
        """
        
        result = client.query(verify_query).result()
        for row in result:
            print(f"\n  VIX signal stats for neural dataset period:")
            print(f"    Dates: {row.min_date} to {row.max_date} ({row.rows} rows)")
            print(f"    Signal range: {row.min_signal:.3f} to {row.max_signal:.3f}")
            print(f"    Signal std dev: {row.std_signal:.3f}")
            
            if row.std_signal > 0:
                print("\n  ✅ VIX signal now has real variance in the right date range!")
                return True
                
    except Exception as e:
        print(f"  ❌ Failed to rebuild: {e}")
    
    return False

def main():
    print("=" * 80)
    print("FIXING VIX DATA PROPERLY WITH REAL HISTORICAL DATA")
    print("=" * 80)
    
    # Load real VIX data
    loaded = load_historical_vix()
    
    if loaded:
        # Rebuild signal with real data
        rebuilt = rebuild_vix_signal_with_real_data()
        
        if rebuilt:
            print("\n" + "=" * 80)
            print("✅ SUCCESS! VIX NOW HAS REAL HISTORICAL DATA!")
            print("=" * 80)
            print("\nNext steps:")
            print("  1. Rebuild Big 8 aggregation")
            print("  2. Rebuild neural training dataset")
            print("  3. Train models")
            return True
    
    print("\n❌ Failed to fix VIX data")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
