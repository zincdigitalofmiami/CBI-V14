#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
collect_neural_data_sources.py
Collect deep drivers data for neural model approach
Going beyond surface correlations to understand causality
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import requests
import logging
from typing import Dict, List
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeuralDataCollector:
    """Collect drivers behind the drivers"""
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.fred_api_key = self.get_fred_key()
        
    def get_fred_key(self):
        """Get FRED API key from secrets or environment"""
        # In production, get from Secret Manager
        # For now, check if we have it in existing data
        query = """
        SELECT DISTINCT source_name 
        FROM `cbi-v14.raw_intelligence.macro_economic_indicators`
        WHERE source_name LIKE '%FRED%'
        LIMIT 1
        """
        result = self.client.query(query).to_dataframe()
        # Placeholder - need actual key
        return "YOUR_FRED_API_KEY"
    
    # ============================================
    # DOLLAR DEEP DRIVERS
    # ============================================
    
    def collect_rate_differentials(self) -> pd.DataFrame:
        """Collect interest rate differentials that drive dollar"""
        
        logger.info("📊 Collecting rate differential data...")
        
        # FRED series for rate differentials
        fred_series = {
            'DGS10': 'US 10Y Treasury',
            'DGS2': 'US 2Y Treasury', 
            'DFEDTARU': 'Fed Funds Upper Target',
            'T10Y2Y': '10Y-2Y Spread',
            'T10YIE': '10Y Breakeven Inflation',
            'BAMLH0A0HYM2': 'High Yield Spread',
            'BAMLC0A0CM': 'Investment Grade Spread',
            'DFF': 'Fed Funds Effective',
            'SOFR': 'SOFR Rate',
            'DEXUSEU': 'EUR/USD Exchange Rate',
            'DEXJPUS': 'USD/JPY Exchange Rate'
        }
        
        data = []
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        for series_id, description in fred_series.items():
            try:
                params = {
                    'series_id': series_id,
                    'api_key': self.fred_api_key,
                    'file_type': 'json',
                    'observation_start': '2020-01-01',
                    'frequency': 'd'  # Daily
                }
                
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    observations = response.json()['observations']
                    for obs in observations:
                        if obs['value'] != '.':  # Skip missing
                            data.append({
                                'date': obs['date'],
                                'series': series_id,
                                'description': description,
                                'value': float(obs['value'])
                            })
                    logger.info(f"  ✓ {series_id}: {len(observations)} observations")
                    
            except Exception as e:
                logger.error(f"  ✗ Error fetching {series_id}: {e}")
        
        df = pd.DataFrame(data)
        
        # Pivot to wide format
        if not df.empty:
            df_pivot = df.pivot(index='date', columns='series', values='value')
            
# REMOVED:             # Calculate synthetic spreads # NO FAKE DATA
            if 'DGS10' in df_pivot.columns and 'DGS2' in df_pivot.columns:
                df_pivot['yield_curve'] = df_pivot['DGS10'] - df_pivot['DGS2']
                
            if 'DGS10' in df_pivot.columns and 'T10YIE' in df_pivot.columns:
                df_pivot['real_10y_yield'] = df_pivot['DGS10'] - df_pivot['T10YIE']
            
            # Rate momentum
            if 'DFF' in df_pivot.columns:
                df_pivot['fed_funds_3m_change'] = df_pivot['DFF'].diff(periods=63)  # ~3 months
                df_pivot['fed_funds_momentum'] = df_pivot['DFF'].rolling(window=5).mean()
            
            logger.info(f"✅ Collected {len(df_pivot)} days of rate data")
            return df_pivot.reset_index()
        
        return pd.DataFrame()
    
    def collect_risk_sentiment_indicators(self) -> pd.DataFrame:
        """Collect risk on/off indicators"""
        
        logger.info("📊 Collecting risk sentiment indicators...")
        
        # Get from existing data
        query = """
        WITH risk_indicators AS (
          SELECT 
            date,
            vix_level,
            vix_level - LAG(vix_level, 1) OVER (ORDER BY date) as vix_1d_change,
            vix_level - LAG(vix_level, 5) OVER (ORDER BY date) as vix_5d_change,
            
            -- Term structure
            CASE 
              WHEN vix_level > 30 THEN 'extreme_fear'
              WHEN vix_level > 20 THEN 'fear'
              WHEN vix_level < 15 THEN 'greed'
              ELSE 'neutral'
            END as vix_regime,
            
            -- Correlation breakdowns
            CORR(zl_price_current, crude_price) OVER (
              ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as commodity_correlation_20d,
            
            CORR(zl_price_current, corn_price) OVER (
              ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as ag_correlation_20d,
            
            -- Safe haven flows
            gold_price,
            gold_price - LAG(gold_price, 1) OVER (ORDER BY date) as gold_1d_change
            
          FROM `cbi-v14.models_v4.production_training_data_1m`
          WHERE date >= '2020-01-01'
        )
        SELECT * FROM risk_indicators
        ORDER BY date
        """
        
        df = self.client.query(query).to_dataframe()
        logger.info(f"✅ Collected {len(df)} days of risk sentiment data")
        return df
    
    def collect_capital_flows(self) -> pd.DataFrame:
        """Collect capital flow proxies"""
        
        logger.info("📊 Collecting capital flow indicators...")
        
        # Use trade data as proxy for flows
        query = """
        WITH flow_proxies AS (
          SELECT 
            date,
            
            -- Trade flows
            china_soybean_imports_mt,
            china_imports_from_us_mt,
            china_soybean_imports_mt * zl_price_current as china_trade_value,
            
            -- Currency movements indicate flows
            usd_cny_rate,
            usd_cny_rate - LAG(usd_cny_rate, 1) OVER (ORDER BY date) as cny_daily_change,
            usd_cny_rate - LAG(usd_cny_rate, 30) OVER (ORDER BY date) as cny_monthly_change,
            
            usd_brl_rate,
            usd_brl_rate - LAG(usd_brl_rate, 1) OVER (ORDER BY date) as brl_daily_change,
            
            -- Positioning
            cftc_managed_net,
            cftc_commercial_net,
            cftc_managed_net - LAG(cftc_managed_net, 1) OVER (ORDER BY date) as spec_flow
            
          FROM `cbi-v14.models_v4.production_training_data_1m`
          WHERE date >= '2020-01-01'
        )
        SELECT * FROM flow_proxies
        ORDER BY date
        """
        
        df = self.client.query(query).to_dataframe()
        logger.info(f"✅ Collected {len(df)} days of flow proxy data")
        return df
    
    # ============================================
    # FED DEEP DRIVERS
    # ============================================
    
    def collect_employment_dynamics(self) -> pd.DataFrame:
        """Collect deep employment indicators"""
        
        logger.info("📊 Collecting employment dynamics...")
        
        # FRED employment series
        employment_series = {
            'PAYEMS': 'Nonfarm Payrolls',
            'UNRATE': 'Unemployment Rate',
            'CIVPART': 'Participation Rate',
            'CES0500000003': 'Average Hourly Earnings',
            'JTSQUL': 'Quits Rate',
            'JTSJOL': 'Job Openings',
            'ICSA': 'Initial Claims',
            'CCSA': 'Continuing Claims',
            'ECIALLCIV': 'Employment Cost Index'
        }
        
        # Similar to rate collection
        # (Implement similar to collect_rate_differentials)
        
        # For now, use proxy from existing data
        query = """
        SELECT 
          date,
          economic_indicators_employment_rate,
          economic_indicators_employment_rate - LAG(economic_indicators_employment_rate, 1) 
            OVER (ORDER BY date) as employment_1m_change,
          economic_indicators_employment_rate - LAG(economic_indicators_employment_rate, 3) 
            OVER (ORDER BY date) as employment_3m_change,
          economic_indicators_employment_rate - LAG(economic_indicators_employment_rate, 12) 
            OVER (ORDER BY date) as employment_12m_change
        FROM `cbi-v14.models_v4.production_training_data_1m`
        WHERE date >= '2020-01-01'
        ORDER BY date
        """
        
        df = self.client.query(query).to_dataframe()
        logger.info(f"✅ Collected {len(df)} days of employment data")
        return df
    
    def collect_inflation_components(self) -> pd.DataFrame:
        """Collect detailed inflation drivers"""
        
        logger.info("📊 Collecting inflation components...")
        
        query = """
        WITH inflation_detail AS (
          SELECT 
            date,
            
            -- Core inflation
            cpi_yoy,
            cpi_yoy - LAG(cpi_yoy, 1) OVER (ORDER BY date) as cpi_momentum,
            cpi_yoy - LAG(cpi_yoy, 3) OVER (ORDER BY date) as cpi_3m_momentum,
            
            -- Commodity inflation
            (crude_price - LAG(crude_price, 252) OVER (ORDER BY date)) 
              / NULLIF(LAG(crude_price, 252) OVER (ORDER BY date), 0) * 100 as oil_inflation_yoy,
            
            (corn_price - LAG(corn_price, 252) OVER (ORDER BY date))
              / NULLIF(LAG(corn_price, 252) OVER (ORDER BY date), 0) * 100 as food_inflation_yoy,
            
            -- Inflation expectations (term structure proxy)
            treasury_10y_yield - treasury_2y_yield as term_premium,
            treasury_10y_yield - fed_funds_rate as long_short_spread,
            
            -- Volatility as supply chain stress
            volatility_30d as supply_chain_proxy
            
          FROM `cbi-v14.models_v4.production_training_data_1m`
          WHERE date >= '2020-01-01'
        )
        SELECT * FROM inflation_detail
        ORDER BY date
        """
        
        df = self.client.query(query).to_dataframe()
        logger.info(f"✅ Collected {len(df)} days of inflation data")
        return df
    
    # ============================================
    # CRUSH MARGIN DEEP DRIVERS
    # ============================================
    
    def collect_processing_dynamics(self) -> pd.DataFrame:
        """Collect crush processing drivers"""
        
        logger.info("📊 Collecting processing dynamics...")
        
        query = """
        WITH processing AS (
          SELECT 
            date,
            
            -- Core crush metrics
            crush_margin,
            crush_margin_30d_ma,
            crush_margin_7d_ma,
            
            -- Components
            oil_price_per_cwt,
            meal_price_per_ton,
            bean_price_per_bushel,
            
            -- Spreads
            oil_price_per_cwt - bean_price_per_bushel as oil_bean_spread,
            meal_price_per_ton - bean_price_per_bushel as meal_bean_spread,
            
            -- Efficiency metrics
            crush_margin / NULLIF(bean_price_per_bushel, 0) as margin_efficiency,
            crush_margin / NULLIF(crush_margin_30d_ma, 0) as margin_momentum,
            
            -- Volatility
            STDDEV(crush_margin) OVER (
              ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as margin_volatility_20d
            
          FROM `cbi-v14.models_v4.production_training_data_1m`
          WHERE date >= '2020-01-01'
        )
        SELECT * FROM processing
        ORDER BY date
        """
        
        df = self.client.query(query).to_dataframe()
        logger.info(f"✅ Collected {len(df)} days of processing data")
        return df
    
    def collect_demand_drivers(self) -> pd.DataFrame:
        """Collect meal and oil demand indicators"""
        
        logger.info("📊 Collecting demand drivers...")
        
        query = """
        WITH demand AS (
          SELECT 
            date,
            
            -- Biofuel demand
            feature_biofuel_cascade,
            feature_biofuel_ethanol,
            rin_d4_price,
            rin_d5_price,
            rin_d6_price,
            
            -- Feed demand (livestock proxy via China)
            china_soybean_imports_mt,
            china_soybean_imports_mt - LAG(china_soybean_imports_mt, 1) 
              OVER (ORDER BY date) as china_import_momentum,
            
            -- Oil substitution
            palm_price,
            palm_price - zl_price_current as palm_soy_spread,
            
            -- Energy ratios
            crude_price,
            crude_price / NULLIF(zl_price_current, 0) as crude_soy_ratio,
            
            -- Seasonal patterns
            EXTRACT(MONTH FROM date) as month,
            CASE 
              WHEN EXTRACT(MONTH FROM date) IN (9, 10, 11) THEN 1  -- Harvest
              ELSE 0
            END as harvest_season
            
          FROM `cbi-v14.models_v4.production_training_data_1m`
          WHERE date >= '2020-01-01'
        )
        SELECT * FROM demand
        ORDER BY date
        """
        
        df = self.client.query(query).to_dataframe()
        logger.info(f"✅ Collected {len(df)} days of demand data")
        return df
    
    # ============================================
    # COMBINE AND STORE
    # ============================================
    
    def combine_neural_features(self) -> pd.DataFrame:
        """Combine all neural drivers into single dataset"""
        
        logger.info("🔄 Combining neural features...")
        
        # Collect all components
        rate_diff = self.collect_rate_differentials()
        risk_sent = self.collect_risk_sentiment_indicators()
        cap_flows = self.collect_capital_flows()
        employment = self.collect_employment_dynamics()
        inflation = self.collect_inflation_components()
        processing = self.collect_processing_dynamics()
        demand = self.collect_demand_drivers()
        
        # Merge all on date
        dfs = [rate_diff, risk_sent, cap_flows, employment, inflation, processing, demand]
        
        # Start with first non-empty dataframe
        combined = None
        for df in dfs:
            if not df.empty:
                if combined is None:
                    combined = df
                else:
                    combined = pd.merge(combined, df, on='date', how='outer')
        
        if combined is not None:
            # Sort by date
            combined = combined.sort_values('date')
            
            # Forward fill missing values
            combined = combined.fillna(method='ffill')
            
            logger.info(f"✅ Combined {len(combined)} rows with {len(combined.columns)} features")
            return combined
        
        return pd.DataFrame()
    
    def store_to_bigquery(self, df: pd.DataFrame, table_name: str):
        """Store neural features to BigQuery"""
        
        if df.empty:
            logger.warning("No data to store")
            return
        
        table_id = f"cbi-v14.models_v4.{table_name}"
        
        # Configure job
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            schema_update_options=["ALLOW_FIELD_ADDITION"]
        )
        
        # Load to BigQuery
        job = self.client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()
        
        logger.info(f"✅ Stored {len(df)} rows to {table_id}")
    
    def calculate_neural_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate composite neural scores"""
        
        logger.info("🧮 Calculating neural scores...")
        
        # Dollar neural score
        dollar_features = ['yield_curve', 'real_10y_yield', 'fed_funds_momentum', 
                          'vix_regime', 'cny_monthly_change']
        
        for feature in dollar_features:
            if feature in df.columns:
                # Normalize to 0-1
                df[f'{feature}_norm'] = (df[feature] - df[feature].min()) / \
                                        (df[feature].max() - df[feature].min())
        
        # Calculate composite scores
        if all(f'{f}_norm' in df.columns for f in dollar_features):
            df['dollar_neural_score'] = df[[f'{f}_norm' for f in dollar_features]].mean(axis=1)
        
        return df

def main():
    """Run neural data collection"""
    
    print("="*60)
    print("🧠 NEURAL DATA COLLECTION")
    print("="*60)
    
    collector = NeuralDataCollector()
    
    # Combine all features
    neural_df = collector.combine_neural_features()
    
    if not neural_df.empty:
        # Calculate scores
        neural_df = collector.calculate_neural_scores(neural_df)
        
        # Store to BigQuery
        collector.store_to_bigquery(neural_df, "neural_drivers_raw")
        
        print("✅ Neural data collection complete!")
        print(f"   Total features: {len(neural_df.columns)}")
        print(f"   Date range: {neural_df['date'].min()} to {neural_df['date'].max()}")
    else:
        print("❌ No data collected")

if __name__ == "__main__":
    main()






