#!/usr/bin/env python3
"""
Week 0 Day 2 Part 3: Create Prefixed BigQuery Tables
Creates new tables with proper source prefixing in parallel with existing legacy tables.
"""

import os
from google.cloud import bigquery
from typing import List, Dict
from datetime import datetime

# Configuration
PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

def create_yahoo_tables(client: bigquery.Client) -> List[str]:
    """Create Yahoo-prefixed tables (ZL primary source)."""
    tables_created = []
    
    # Yahoo Historical (with ZL and all other symbols)
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.yahoo_historical_prefixed (
        date DATE,
        symbol STRING,
        yahoo_open FLOAT64,
        yahoo_high FLOAT64,
        yahoo_low FLOAT64,
        yahoo_close FLOAT64,
        yahoo_volume INT64,
        yahoo_adj_close FLOAT64,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY symbol
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.yahoo_historical_prefixed")
    print("✓ Created yahoo_historical_prefixed")
    
    return tables_created

def create_alpha_tables(client: bigquery.Client) -> List[str]:
    """Create Alpha Vantage prefixed tables (everything except ZL)."""
    tables_created = []
    
    # ES Futures Intraday (11 timeframes)
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.alpha_es_intraday (
        date DATE,
        timestamp TIMESTAMP,
        symbol STRING,
        timeframe STRING,  -- 5min, 15min, 1hr, 4hr, 8hr, 1day, 3day, 7day, 30day, 3mo, 6mo
        alpha_open FLOAT64,
        alpha_high FLOAT64,
        alpha_low FLOAT64,
        alpha_close FLOAT64,
        alpha_volume INT64,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY symbol, timeframe
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.alpha_es_intraday")
    print("✓ Created alpha_es_intraday")
    
    # Commodities Daily (CORN, WHEAT, WTI, BRENT, etc.)
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.alpha_commodities_daily (
        date DATE,
        symbol STRING,
        alpha_open FLOAT64,
        alpha_high FLOAT64,
        alpha_low FLOAT64,
        alpha_close FLOAT64,
        alpha_volume INT64,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY symbol
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.alpha_commodities_daily")
    print("✓ Created alpha_commodities_daily")
    
    # FX Pairs Daily
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.alpha_fx_daily (
        date DATE,
        pair STRING,  -- USD/BRL, USD/CNY, USD/ARS, EUR/USD, USD/MYR
        alpha_open FLOAT64,
        alpha_high FLOAT64,
        alpha_low FLOAT64,
        alpha_close FLOAT64,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY pair
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.alpha_fx_daily")
    print("✓ Created alpha_fx_daily")
    
    # Technical Indicators (50+ indicators, wide format)
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.alpha_indicators_daily (
        date DATE,
        symbol STRING,
        
        -- Moving Averages
        alpha_sma_5 FLOAT64, alpha_sma_10 FLOAT64, alpha_sma_20 FLOAT64, 
        alpha_sma_50 FLOAT64, alpha_sma_100 FLOAT64, alpha_sma_200 FLOAT64,
        alpha_ema_5 FLOAT64, alpha_ema_10 FLOAT64, alpha_ema_20 FLOAT64,
        alpha_ema_50 FLOAT64, alpha_ema_100 FLOAT64, alpha_ema_200 FLOAT64,
        alpha_wma_10 FLOAT64, alpha_wma_20 FLOAT64,
        alpha_dema_20 FLOAT64, alpha_tema_20 FLOAT64,
        alpha_trima_20 FLOAT64, alpha_kama_20 FLOAT64,
        alpha_mama FLOAT64, alpha_fama FLOAT64,
        
        -- Momentum
        alpha_rsi_14 FLOAT64,
        alpha_macd_line FLOAT64, alpha_macd_signal FLOAT64, alpha_macd_hist FLOAT64,
        alpha_stoch_k FLOAT64, alpha_stoch_d FLOAT64,
        alpha_stochf_k FLOAT64, alpha_stochf_d FLOAT64,
        alpha_stochrsi_k FLOAT64, alpha_stochrsi_d FLOAT64,
        alpha_willr_14 FLOAT64, alpha_adx_14 FLOAT64,
        alpha_aroon_up FLOAT64, alpha_aroon_down FLOAT64, alpha_aroonosc FLOAT64,
        alpha_cci_20 FLOAT64, alpha_mom_10 FLOAT64, alpha_roc_10 FLOAT64,
        alpha_mfi_14 FLOAT64, alpha_trix_15 FLOAT64, alpha_ultosc FLOAT64,
        alpha_dx_14 FLOAT64, alpha_minus_di FLOAT64, alpha_plus_di FLOAT64,
        
        -- Volatility
        alpha_bbands_upper_20 FLOAT64, alpha_bbands_middle_20 FLOAT64, alpha_bbands_lower_20 FLOAT64,
        alpha_atr_14 FLOAT64, alpha_natr_14 FLOAT64, alpha_trange FLOAT64,
        
        -- Volume
        alpha_obv FLOAT64, alpha_ad FLOAT64, alpha_adosc FLOAT64, alpha_vwap FLOAT64,
        
        -- Pattern Recognition
        alpha_ht_trendline FLOAT64, alpha_ht_sine FLOAT64, alpha_ht_leadsine FLOAT64,
        alpha_ht_trendmode FLOAT64, alpha_ht_dcperiod FLOAT64, alpha_ht_dcphase FLOAT64,
        alpha_ht_phasor_inphase FLOAT64, alpha_ht_phasor_quad FLOAT64,
        
        -- Price Transform
        alpha_midpoint_14 FLOAT64, alpha_midprice_14 FLOAT64,
        alpha_sar FLOAT64, alpha_sarext FLOAT64,
        
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY symbol
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.alpha_indicators_daily")
    print("✓ Created alpha_indicators_daily")
    
    # News & Sentiment
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.alpha_news_sentiment (
        date DATE,
        published_at TIMESTAMP,
        title STRING,
        url STRING,
        alpha_sentiment_score FLOAT64,
        alpha_sentiment_label STRING,
        alpha_relevance_score FLOAT64,
        tickers ARRAY<STRING>,
        topics ARRAY<STRING>,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.alpha_news_sentiment")
    print("✓ Created alpha_news_sentiment")
    
    # Options Chains
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.alpha_options_snapshot (
        date DATE,
        snapshot_ts TIMESTAMP,
        underlier STRING,
        expiration DATE,
        strike FLOAT64,
        option_type STRING,  -- 'call' or 'put'
        alpha_bid FLOAT64,
        alpha_ask FLOAT64,
        alpha_last FLOAT64,
        alpha_volume INT64,
        alpha_open_interest INT64,
        alpha_iv FLOAT64,
        alpha_delta FLOAT64,
        alpha_gamma FLOAT64,
        alpha_theta FLOAT64,
        alpha_vega FLOAT64,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY underlier, expiration
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.alpha_options_snapshot")
    print("✓ Created alpha_options_snapshot")
    
    return tables_created

def create_fred_tables(client: bigquery.Client) -> List[str]:
    """Create FRED-prefixed tables (expanded 55-60 series)."""
    tables_created = []
    
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.fred_macro_expanded (
        date DATE,
        -- Interest Rates
        fred_dff FLOAT64, fred_dgs10 FLOAT64, fred_dgs2 FLOAT64, fred_dgs30 FLOAT64,
        fred_dgs5 FLOAT64, fred_dgs3mo FLOAT64, fred_dgs1 FLOAT64,
        fred_dfedtaru FLOAT64, fred_dfedtarl FLOAT64,
        
        -- Inflation
        fred_cpiaucsl FLOAT64, fred_cpilfesl FLOAT64, fred_pcepi FLOAT64,
        fred_dpccrv1q225sbea FLOAT64,
        
        -- PPI (Producer Price Index) - NEW
        fred_ppiaco FLOAT64, fred_ppicrm FLOAT64, fred_ppifis FLOAT64, fred_ppiidc FLOAT64,
        
        -- Employment
        fred_unrate FLOAT64, fred_payems FLOAT64, fred_civpart FLOAT64, fred_emratio FLOAT64,
        fred_icsa FLOAT64, fred_ccsa FLOAT64,  -- NEW: Initial/Continued claims
        
        -- GDP & Production
        fred_gdp FLOAT64, fred_gdpc1 FLOAT64, fred_indpro FLOAT64, fred_dgorder FLOAT64,
        fred_ism_mfg FLOAT64, fred_ism_services FLOAT64,  -- NEW: ISM indices
        
        -- Money Supply
        fred_m2sl FLOAT64, fred_m1sl FLOAT64, fred_bogmbase FLOAT64,
        
        -- Market Indicators
        fred_vixcls FLOAT64, fred_dtwexbgs FLOAT64, fred_dtwexemegs FLOAT64,
        
        -- Credit Spreads
        fred_baaffm FLOAT64, fred_t10y2y FLOAT64, fred_t10y3m FLOAT64,
        fred_tedrate FLOAT64,  -- NEW: TED spread
        
        -- Commodities
        fred_dcoilwtico FLOAT64, fred_goldpmgbd228nlbm FLOAT64,
        fred_dexcaus FLOAT64, fred_dexuseu FLOAT64,  -- NEW: More FX rates
        
        -- Consumer & Housing
        fred_houst FLOAT64, fred_umcsent FLOAT64, fred_csushpisa FLOAT64,  -- NEW: Case-Shiller
        fred_rsxfs FLOAT64, fred_pce FLOAT64,  -- NEW: Retail sales, PCE
        
        -- Additional Economic
        fred_cfnai FLOAT64, fred_bbi FLOAT64,  -- NEW: Chicago Fed Index, Book-to-Bill
        
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.fred_macro_expanded")
    print("✓ Created fred_macro_expanded")
    
    return tables_created

def create_weather_tables(client: bigquery.Client) -> List[str]:
    """Create weather tables (granular wide format)."""
    tables_created = []
    
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.weather_granular (
        date DATE,
        
        -- US key states (corn belt + wheat)
        weather_us_iowa_tavg_c FLOAT64, weather_us_iowa_prcp_mm FLOAT64,
        weather_us_illinois_tavg_c FLOAT64, weather_us_illinois_prcp_mm FLOAT64,
        weather_us_indiana_tavg_c FLOAT64, weather_us_indiana_prcp_mm FLOAT64,
        weather_us_minnesota_tavg_c FLOAT64, weather_us_minnesota_prcp_mm FLOAT64,
        weather_us_nebraska_tavg_c FLOAT64, weather_us_nebraska_prcp_mm FLOAT64,
        weather_us_kansas_tavg_c FLOAT64, weather_us_kansas_prcp_mm FLOAT64,
        weather_us_north_dakota_tavg_c FLOAT64, weather_us_north_dakota_prcp_mm FLOAT64,
        weather_us_south_dakota_tavg_c FLOAT64, weather_us_south_dakota_prcp_mm FLOAT64,
        
        -- Brazil key states (soy production)
        weather_br_mato_grosso_tavg_c FLOAT64, weather_br_mato_grosso_prcp_mm FLOAT64,
        weather_br_parana_tavg_c FLOAT64, weather_br_parana_prcp_mm FLOAT64,
        weather_br_rio_grande_do_sul_tavg_c FLOAT64, weather_br_rio_grande_do_sul_prcp_mm FLOAT64,
        weather_br_goias_tavg_c FLOAT64, weather_br_goias_prcp_mm FLOAT64,
        weather_br_mato_grosso_do_sul_tavg_c FLOAT64, weather_br_mato_grosso_do_sul_prcp_mm FLOAT64,
        
        -- Argentina key provinces (soy production)
        weather_ar_buenos_aires_tavg_c FLOAT64, weather_ar_buenos_aires_prcp_mm FLOAT64,
        weather_ar_cordoba_tavg_c FLOAT64, weather_ar_cordoba_prcp_mm FLOAT64,
        weather_ar_santa_fe_tavg_c FLOAT64, weather_ar_santa_fe_prcp_mm FLOAT64,
        weather_ar_entre_rios_tavg_c FLOAT64, weather_ar_entre_rios_prcp_mm FLOAT64,
        
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.weather_granular")
    print("✓ Created weather_granular")
    
    return tables_created

def create_cftc_tables(client: bigquery.Client) -> List[str]:
    """Create CFTC-prefixed tables."""
    tables_created = []
    
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.cftc_commitments (
        date DATE,
        symbol STRING,
        cftc_open_interest INT64,
        cftc_noncommercial_long INT64,
        cftc_noncommercial_short INT64,
        cftc_noncommercial_net INT64,
        cftc_commercial_long INT64,
        cftc_commercial_short INT64,
        cftc_commercial_net INT64,
        cftc_total_long INT64,
        cftc_total_short INT64,
        cftc_nonreportable_long INT64,
        cftc_nonreportable_short INT64,
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY symbol
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.cftc_commitments")
    print("✓ Created cftc_commitments")
    
    return tables_created

def create_usda_tables(client: bigquery.Client) -> List[str]:
    """Create USDA-prefixed tables (granular format)."""
    tables_created = []
    
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.usda_reports_granular (
        date DATE,
        
        -- WASDE World Production/Stocks
        usda_wasde_world_soyoil_prod FLOAT64,
        usda_wasde_world_soyoil_stocks FLOAT64,
        usda_wasde_world_soybean_prod FLOAT64,
        usda_wasde_world_soybean_stocks FLOAT64,
        usda_wasde_world_soymeal_prod FLOAT64,
        usda_wasde_world_corn_prod FLOAT64,
        usda_wasde_world_wheat_prod FLOAT64,
        
        -- WASDE US
        usda_wasde_us_soyoil_prod FLOAT64,
        usda_wasde_us_soyoil_stocks FLOAT64,
        usda_wasde_us_soybean_prod FLOAT64,
        usda_wasde_us_soybean_yield FLOAT64,
        usda_wasde_us_corn_prod FLOAT64,
        usda_wasde_us_corn_yield FLOAT64,
        
        -- Export Sales (weekly)
        usda_exports_soybeans_net_sales_total FLOAT64,
        usda_exports_soybeans_net_sales_china FLOAT64,
        usda_exports_soybeans_shipments FLOAT64,
        usda_exports_corn_net_sales_total FLOAT64,
        usda_exports_corn_shipments FLOAT64,
        usda_exports_wheat_net_sales_total FLOAT64,
        
        -- Crop Progress (weekly during season)
        usda_crop_progress_corn_planted_pct FLOAT64,
        usda_crop_progress_corn_emerged_pct FLOAT64,
        usda_crop_progress_corn_silking_pct FLOAT64,
        usda_crop_progress_corn_harvested_pct FLOAT64,
        usda_crop_progress_soybeans_planted_pct FLOAT64,
        usda_crop_progress_soybeans_blooming_pct FLOAT64,
        usda_crop_progress_soybeans_harvested_pct FLOAT64,
        
        -- NASS Quarterly Stocks
        usda_nass_corn_stocks FLOAT64,
        usda_nass_soybean_stocks FLOAT64,
        usda_nass_wheat_stocks FLOAT64,
        
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.usda_reports_granular")
    print("✓ Created usda_reports_granular")
    
    return tables_created

def create_eia_tables(client: bigquery.Client) -> List[str]:
    """Create EIA-prefixed tables (energy data)."""
    tables_created = []
    
    ddl = """
    CREATE TABLE IF NOT EXISTS forecasting_data_warehouse.eia_energy_granular (
        date DATE,
        
        -- Biofuel Production (weekly/monthly)
        eia_biodiesel_prod_total FLOAT64,
        eia_biodiesel_prod_padd1 FLOAT64,
        eia_biodiesel_prod_padd2 FLOAT64,
        eia_biodiesel_prod_padd3 FLOAT64,
        eia_ethanol_prod_total FLOAT64,
        eia_ethanol_stocks FLOAT64,
        
        -- RIN Prices (daily when available)
        eia_rin_price_d4 FLOAT64,
        eia_rin_price_d6 FLOAT64,
        eia_rin_price_d3 FLOAT64,
        
        -- Crude Oil & Products
        eia_crude_stocks FLOAT64,
        eia_crude_production FLOAT64,
        eia_gasoline_stocks FLOAT64,
        eia_distillate_stocks FLOAT64,
        eia_refinery_utilization FLOAT64,
        
        -- Natural Gas
        eia_ng_storage FLOAT64,
        eia_ng_production FLOAT64,
        
        ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("forecasting_data_warehouse.eia_energy_granular")
    print("✓ Created eia_energy_granular")
    
    return tables_created

def create_canonical_features_table(client: bigquery.Client) -> List[str]:
    """Create the canonical master features table that joins everything."""
    tables_created = []
    
    ddl = """
    CREATE TABLE IF NOT EXISTS features.master_features_canonical (
        date DATE,
        symbol STRING,
        
        -- Yahoo (primary for ZL)
        yahoo_open FLOAT64,
        yahoo_high FLOAT64,
        yahoo_low FLOAT64,
        yahoo_close FLOAT64,
        yahoo_volume INT64,
        
        -- Alpha Vantage prices (NULL for ZL)
        alpha_open FLOAT64,
        alpha_high FLOAT64,
        alpha_low FLOAT64,
        alpha_close FLOAT64,
        alpha_volume INT64,
        
        -- Alpha Vantage indicators (NULL for ZL, 50+ columns)
        alpha_rsi_14 FLOAT64,
        alpha_macd_line FLOAT64,
        alpha_macd_signal FLOAT64,
        alpha_macd_hist FLOAT64,
        -- ... (all 50+ indicators)
        
        -- FRED macro (55-60 columns)
        fred_dff FLOAT64,
        fred_dgs10 FLOAT64,
        fred_cpiaucsl FLOAT64,
        -- ... (all FRED series)
        
        -- Weather granular
        weather_us_iowa_tavg_c FLOAT64,
        weather_us_iowa_prcp_mm FLOAT64,
        -- ... (all weather columns)
        
        -- CFTC
        cftc_open_interest INT64,
        cftc_noncommercial_net INT64,
        -- ... (all CFTC columns)
        
        -- USDA
        usda_wasde_world_soyoil_prod FLOAT64,
        usda_exports_soybeans_net_sales_china FLOAT64,
        -- ... (all USDA columns)
        
        -- EIA
        eia_biodiesel_prod_total FLOAT64,
        eia_rin_price_d4 FLOAT64,
        -- ... (all EIA columns)
        
        -- Feature engineering results
        feature_rsi_divergence FLOAT64,
        feature_volume_surge FLOAT64,
        feature_weather_stress_index FLOAT64,
        -- ... (derived features)
        
        -- Metadata
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) PARTITION BY date
    CLUSTER BY symbol
    """
    client.query(ddl, location=LOCATION).result()
    tables_created.append("features.master_features_canonical")
    print("✓ Created master_features_canonical")
    
    return tables_created

def main():
    """Execute Week 0 Day 2 Part 3: Create all prefixed tables."""
    
    print("\n" + "="*60)
    print("Week 0 Day 2 Part 3: Create Prefixed BigQuery Tables")
    print("="*60)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    print(f"\n✓ Connected to project: {PROJECT_ID}")
    print(f"✓ Location: {LOCATION}")
    
    all_tables_created = []
    
    try:
        # Create tables by source
        print("\n1. Creating Yahoo tables...")
        all_tables_created.extend(create_yahoo_tables(client))
        
        print("\n2. Creating Alpha Vantage tables...")
        all_tables_created.extend(create_alpha_tables(client))
        
        print("\n3. Creating FRED tables...")
        all_tables_created.extend(create_fred_tables(client))
        
        print("\n4. Creating Weather tables...")
        all_tables_created.extend(create_weather_tables(client))
        
        print("\n5. Creating CFTC tables...")
        all_tables_created.extend(create_cftc_tables(client))
        
        print("\n6. Creating USDA tables...")
        all_tables_created.extend(create_usda_tables(client))
        
        print("\n7. Creating EIA tables...")
        all_tables_created.extend(create_eia_tables(client))
        
        print("\n8. Creating canonical features table...")
        all_tables_created.extend(create_canonical_features_table(client))
        
        # Summary
        print("\n" + "="*60)
        print(f"✓ SUCCESSFULLY CREATED {len(all_tables_created)} PREFIXED TABLES")
        print("="*60)
        
        print("\nTables created:")
        for table in all_tables_created:
            print(f"  - {table}")
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("1. Week 0 Day 3: Refactor 12 views to use prefixed tables")
        print("2. Week 0 Day 4: Backfill historical data into new tables")
        print("3. Week 1: Begin new data collection with proper prefixes")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    main()
