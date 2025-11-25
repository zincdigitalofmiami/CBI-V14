#!/usr/bin/env python3
"""
DEPRECATED - MARKED FOR DELETION IN PHASE 1

This file contains broken postgres references from CBI-V13 project.
Will be replaced with proper BigQuery ingestion scripts in Phase 1.

DO NOT USE THIS FILE - IT WILL FAIL
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# POSTGRES REFERENCES REMOVED - FILE MARKED FOR REWRITE IN PHASE 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatasetProfile:
    """Profile of a dataset for intelligent routing"""
    name: str
    data_type: str  # 'market', 'macro', 'crisis', 'fed'
    time_column: str
    key_columns: List[str]
    target_table: str
    frequency: str  # 'daily', 'monthly', 'irregular'
    date_format: str


class IntelligentDataIngestor:
    """
    Intelligent data ingestion pipeline that can:
    - Parse different CSV formats automatically
    - Understand data types and meanings
    - Route data to appropriate database tables
    - Handle time series alignment
    - Validate data quality
    """

    def __init__(self):
        self.engine = get_engine()
        self.profiles = {}
        self.ingested_datasets = {}

    def ingest_file(self, file_path: str) -> bool:
        """
        Intelligently ingest a data file

        1. Analyze file structure
        2. Identify data type and meaning
        3. Create appropriate database schema
        4. Load and validate data
        5. Route to correct tables
        """
        logger.info(f"🔍 Analyzing file: {file_path}")

        try:
            # Step 1: Load and analyze file
            df = pd.read_csv(file_path)
            logger.info(f"📊 Loaded {len(df)} rows, {len(df.columns)} columns")

            # Step 2: Profile the dataset
            profile = self._profile_dataset(df, file_path)
            logger.info(f"🧠 Identified as: {profile.data_type} data, frequency: {profile.frequency}")

            # Step 3: Prepare data for ingestion
            df_clean = self._prepare_data(df, profile)
            logger.info(f"🧹 Cleaned to {len(df_clean)} rows")

            # Step 4: Create/update database schema
            self._ensure_schema(profile)

            # Step 5: Ingest data
            rows_ingested = self._ingest_data(df_clean, profile)
            logger.info(f"✅ Ingested {rows_ingested} rows to {profile.target_table}")

            # Store profile for future reference
            self.profiles[profile.name] = profile
            self.ingested_datasets[profile.name] = {
                'rows': rows_ingested,
                'columns': list(df_clean.columns),
                'date_range': f"{df_clean[profile.time_column].min()} to {df_clean[profile.time_column].max()}"
            }

            return True

        except Exception as e:
            logger.error(f"❌ Failed to ingest {file_path}: {e}")
            return False

    def _profile_dataset(self, df: pd.DataFrame, file_path: str) -> DatasetProfile:
        """
        Intelligently profile a dataset to understand its structure and meaning
        """
        file_name = Path(file_path).stem.lower()
        columns = [col.lower() for col in df.columns]

        # Detect time column
        time_column = None
        for col in df.columns:
            if col.lower() in ['date', 'time', 'timestamp', 'ds']:
                time_column = col
                break

        if not time_column:
            raise ValueError("No time column found in dataset")

        # Convert time column to datetime
        df[time_column] = pd.to_datetime(df[time_column])

        # Determine data type based on file name and columns
        if 'crisis' in file_name or 'crisis_label' in columns:
            return DatasetProfile(
                name=file_name,
                data_type='crisis',
                time_column=time_column,
                key_columns=['equity_return', 'bond_yield', 'volatility_index', 'gdp_growth', 'inflation', 'crisis_label'],
                target_table='features.financial_crisis',
                frequency=self._detect_frequency(df[time_column]),
                date_format='%Y-%m-%d'
            )

        elif 'fedfunds' in file_name or 'fed' in file_name:
            return DatasetProfile(
                name=file_name,
                data_type='fed',
                time_column=time_column,
                key_columns=['close', 'ema', 'macd', 'signal_line'],
                target_table='features.fed_rates',
                frequency=self._detect_frequency(df[time_column]),
                date_format='%Y-%m-%d'
            )

        elif 'economics' in file_name or 'finance' in file_name:
            return DatasetProfile(
                name=file_name,
                data_type='comprehensive',
                time_column=time_column,
                key_columns=['gdp_growth', 'inflation_rate', 'unemployment_rate', 'interest_rate', 'crude_oil_price', 'gold_price'],
                target_table='features.macro_comprehensive',
                frequency=self._detect_frequency(df[time_column]),
                date_format='%Y-%m-%d'
            )

        else:
            # Generic market data
            return DatasetProfile(
                name=file_name,
                data_type='market',
                time_column=time_column,
                key_columns=list(df.select_dtypes(include=[np.number]).columns)[:10],
                target_table='curated.market_data_generic',
                frequency=self._detect_frequency(df[time_column]),
                date_format='%Y-%m-%d'
            )

    def _detect_frequency(self, time_series: pd.Series) -> str:
        """Detect the frequency of the time series"""
        if len(time_series) < 2:
            return 'irregular'

        diffs = time_series.sort_values().diff().dropna()
        median_diff = diffs.median()

        if median_diff <= pd.Timedelta(days=1):
            return 'daily'
        elif median_diff <= pd.Timedelta(days=7):
            return 'weekly'
        elif median_diff <= pd.Timedelta(days=31):
            return 'monthly'
        else:
            return 'irregular'

    def _prepare_data(self, df: pd.DataFrame, profile: DatasetProfile) -> pd.DataFrame:
        """
        Prepare data for ingestion based on profile
        """
        df_clean = df.copy()

        # Standardize time column
        df_clean[profile.time_column] = pd.to_datetime(df_clean[profile.time_column])

        # Sort by time
        df_clean = df_clean.sort_values(profile.time_column)

        # Remove duplicates
        df_clean = df_clean.drop_duplicates(subset=[profile.time_column])

        # Standardize column names (lowercase, underscore)
        new_columns = {}
        for col in df_clean.columns:
            new_col = col.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', '_pct')
            new_columns[col] = new_col
        df_clean = df_clean.rename(columns=new_columns)

        # Update profile with new column names
        profile.time_column = new_columns.get(profile.time_column, profile.time_column).lower()
        profile.key_columns = [new_columns.get(col, col).lower() for col in profile.key_columns if new_columns.get(col, col).lower() in df_clean.columns]

        return df_clean

    def _ensure_schema(self, profile: DatasetProfile):
        """
        Create database table schema based on dataset profile
        """
        schema_name, table_name = profile.target_table.split('.')

        with self.engine.begin() as conn:
            # Create schema if not exists
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

            # Create table based on data type
            if profile.data_type == 'crisis':
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {profile.target_table} (
                        ds DATE PRIMARY KEY,
                        equity_return DECIMAL,
                        bond_yield DECIMAL,
                        fx_rate_change DECIMAL,
                        volatility_index DECIMAL,
                        gdp_growth DECIMAL,
                        inflation DECIMAL,
                        crisis_label INTEGER
                    )
                """))

            elif profile.data_type == 'fed':
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {profile.target_table} (
                        ds DATE PRIMARY KEY,
                        fed_rate DECIMAL,
                        ema DECIMAL,
                        macd DECIMAL,
                        signal_line DECIMAL,
                        histogram DECIMAL,
                        cross_signal TEXT
                    )
                """))

            elif profile.data_type == 'comprehensive':
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {profile.target_table} (
                        ds DATE PRIMARY KEY,
                        stock_index TEXT,
                        open_price DECIMAL,
                        close_price DECIMAL,
                        daily_high DECIMAL,
                        daily_low DECIMAL,
                        trading_volume BIGINT,
                        gdp_growth_pct DECIMAL,
                        inflation_rate_pct DECIMAL,
                        unemployment_rate_pct DECIMAL,
                        interest_rate_pct DECIMAL,
                        consumer_confidence_index DECIMAL,
                        government_debt_billion_usd DECIMAL,
                        corporate_profits_billion_usd DECIMAL,
                        forex_usd_eur DECIMAL,
                        forex_usd_jpy DECIMAL,
                        crude_oil_price_usd_per_barrel DECIMAL,
                        gold_price_usd_per_ounce DECIMAL,
                        real_estate_index DECIMAL,
                        retail_sales_billion_usd DECIMAL,
                        bankruptcy_rate_pct DECIMAL,
                        mergers_acquisitions_deals INTEGER,
                        venture_capital_funding_billion_usd DECIMAL,
                        consumer_spending_billion_usd DECIMAL
                    )
                """))

    def _ingest_data(self, df: pd.DataFrame, profile: DatasetProfile) -> int:
        """
        Ingest cleaned data into the appropriate table
        """
        rows_inserted = 0

        with self.engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    if profile.data_type == 'crisis':
                        conn.execute(text(f"""
                            INSERT INTO {profile.target_table}
                            (ds, equity_return, bond_yield, fx_rate_change, volatility_index, gdp_growth, inflation, crisis_label)
                            VALUES (:ds, :equity_return, :bond_yield, :fx_rate_change, :volatility_index, :gdp_growth, :inflation, :crisis_label)
                            ON CONFLICT (ds) DO UPDATE SET
                                equity_return = EXCLUDED.equity_return,
                                bond_yield = EXCLUDED.bond_yield,
                                fx_rate_change = EXCLUDED.fx_rate_change,
                                volatility_index = EXCLUDED.volatility_index,
                                gdp_growth = EXCLUDED.gdp_growth,
                                inflation = EXCLUDED.inflation,
                                crisis_label = EXCLUDED.crisis_label
                        """), {
                            'ds': row[profile.time_column].date(),
                            'equity_return': float(row.get('equity_return', 0)) if pd.notna(row.get('equity_return')) else None,
                            'bond_yield': float(row.get('bond_yield', 0)) if pd.notna(row.get('bond_yield')) else None,
                            'fx_rate_change': float(row.get('fx_rate_change', 0)) if pd.notna(row.get('fx_rate_change')) else None,
                            'volatility_index': float(row.get('volatility_index', 0)) if pd.notna(row.get('volatility_index')) else None,
                            'gdp_growth': float(row.get('gdp_growth', 0)) if pd.notna(row.get('gdp_growth')) else None,
                            'inflation': float(row.get('inflation', 0)) if pd.notna(row.get('inflation')) else None,
                            'crisis_label': int(row.get('crisis_label', 0)) if pd.notna(row.get('crisis_label')) else 0
                        })

                    elif profile.data_type == 'fed':
                        conn.execute(text(f"""
                            INSERT INTO {profile.target_table}
                            (ds, fed_rate, ema, macd, signal_line, histogram, cross_signal)
                            VALUES (:ds, :fed_rate, :ema, :macd, :signal_line, :histogram, :cross_signal)
                            ON CONFLICT (ds) DO UPDATE SET
                                fed_rate = EXCLUDED.fed_rate,
                                ema = EXCLUDED.ema,
                                macd = EXCLUDED.macd,
                                signal_line = EXCLUDED.signal_line,
                                histogram = EXCLUDED.histogram,
                                cross_signal = EXCLUDED.cross_signal
                        """), {
                            'ds': row[profile.time_column].date(),
                            'fed_rate': float(row.get('close', 0)) if pd.notna(row.get('close')) else None,
                            'ema': float(row.get('ema', 0)) if pd.notna(row.get('ema')) else None,
                            'macd': float(row.get('macd', 0)) if pd.notna(row.get('macd')) else None,
                            'signal_line': float(row.get('signal_line', 0)) if pd.notna(row.get('signal_line')) else None,
                            'histogram': float(row.get('histogram', 0)) if pd.notna(row.get('histogram')) else None,
                            'cross_signal': str(row.get('cross', '')) if pd.notna(row.get('cross')) else None
                        })

                    elif profile.data_type == 'comprehensive':
                        conn.execute(text(f"""
                            INSERT INTO {profile.target_table}
                            (ds, stock_index, open_price, close_price, daily_high, daily_low, trading_volume,
                             gdp_growth_pct, inflation_rate_pct, unemployment_rate_pct, interest_rate_pct,
                             consumer_confidence_index, government_debt_billion_usd, corporate_profits_billion_usd,
                             forex_usd_eur, forex_usd_jpy, crude_oil_price_usd_per_barrel, gold_price_usd_per_ounce,
                             real_estate_index, retail_sales_billion_usd, bankruptcy_rate_pct,
                             mergers_acquisitions_deals, venture_capital_funding_billion_usd, consumer_spending_billion_usd)
                            VALUES (:ds, :stock_index, :open_price, :close_price, :daily_high, :daily_low, :trading_volume,
                                   :gdp_growth_pct, :inflation_rate_pct, :unemployment_rate_pct, :interest_rate_pct,
                                   :consumer_confidence_index, :government_debt_billion_usd, :corporate_profits_billion_usd,
                                   :forex_usd_eur, :forex_usd_jpy, :crude_oil_price_usd_per_barrel, :gold_price_usd_per_ounce,
                                   :real_estate_index, :retail_sales_billion_usd, :bankruptcy_rate_pct,
                                   :mergers_acquisitions_deals, :venture_capital_funding_billion_usd, :consumer_spending_billion_usd)
                            ON CONFLICT (ds) DO UPDATE SET
                                stock_index = EXCLUDED.stock_index,
                                open_price = EXCLUDED.open_price,
                                close_price = EXCLUDED.close_price,
                                daily_high = EXCLUDED.daily_high,
                                daily_low = EXCLUDED.daily_low,
                                trading_volume = EXCLUDED.trading_volume,
                                gdp_growth_pct = EXCLUDED.gdp_growth_pct,
                                inflation_rate_pct = EXCLUDED.inflation_rate_pct,
                                unemployment_rate_pct = EXCLUDED.unemployment_rate_pct,
                                interest_rate_pct = EXCLUDED.interest_rate_pct,
                                consumer_confidence_index = EXCLUDED.consumer_confidence_index,
                                government_debt_billion_usd = EXCLUDED.government_debt_billion_usd,
                                corporate_profits_billion_usd = EXCLUDED.corporate_profits_billion_usd,
                                forex_usd_eur = EXCLUDED.forex_usd_eur,
                                forex_usd_jpy = EXCLUDED.forex_usd_jpy,
                                crude_oil_price_usd_per_barrel = EXCLUDED.crude_oil_price_usd_per_barrel,
                                gold_price_usd_per_ounce = EXCLUDED.gold_price_usd_per_ounce,
                                real_estate_index = EXCLUDED.real_estate_index,
                                retail_sales_billion_usd = EXCLUDED.retail_sales_billion_usd,
                                bankruptcy_rate_pct = EXCLUDED.bankruptcy_rate_pct,
                                mergers_acquisitions_deals = EXCLUDED.mergers_acquisitions_deals,
                                venture_capital_funding_billion_usd = EXCLUDED.venture_capital_funding_billion_usd,
                                consumer_spending_billion_usd = EXCLUDED.consumer_spending_billion_usd
                        """), {
                            'ds': row[profile.time_column].date(),
                            'stock_index': str(row.get('stock_index', '')),
                            'open_price': float(row.get('open_price', 0)) if pd.notna(row.get('open_price')) else None,
                            'close_price': float(row.get('close_price', 0)) if pd.notna(row.get('close_price')) else None,
                            'daily_high': float(row.get('daily_high', 0)) if pd.notna(row.get('daily_high')) else None,
                            'daily_low': float(row.get('daily_low', 0)) if pd.notna(row.get('daily_low')) else None,
                            'trading_volume': int(row.get('trading_volume', 0)) if pd.notna(row.get('trading_volume')) else None,
                            'gdp_growth_pct': float(row.get('gdp_growth__pct_', 0)) if pd.notna(row.get('gdp_growth__pct_')) else None,
                            'inflation_rate_pct': float(row.get('inflation_rate__pct_', 0)) if pd.notna(row.get('inflation_rate__pct_')) else None,
                            'unemployment_rate_pct': float(row.get('unemployment_rate__pct_', 0)) if pd.notna(row.get('unemployment_rate__pct_')) else None,
                            'interest_rate_pct': float(row.get('interest_rate__pct_', 0)) if pd.notna(row.get('interest_rate__pct_')) else None,
                            'consumer_confidence_index': float(row.get('consumer_confidence_index', 0)) if pd.notna(row.get('consumer_confidence_index')) else None,
                            'government_debt_billion_usd': float(row.get('government_debt__billion_usd_', 0)) if pd.notna(row.get('government_debt__billion_usd_')) else None,
                            'corporate_profits_billion_usd': float(row.get('corporate_profits__billion_usd_', 0)) if pd.notna(row.get('corporate_profits__billion_usd_')) else None,
                            'forex_usd_eur': float(row.get('forex_usd_eur', 0)) if pd.notna(row.get('forex_usd_eur')) else None,
                            'forex_usd_jpy': float(row.get('forex_usd_jpy', 0)) if pd.notna(row.get('forex_usd_jpy')) else None,
                            'crude_oil_price_usd_per_barrel': float(row.get('crude_oil_price__usd_per_barrel_', 0)) if pd.notna(row.get('crude_oil_price__usd_per_barrel_')) else None,
                            'gold_price_usd_per_ounce': float(row.get('gold_price__usd_per_ounce_', 0)) if pd.notna(row.get('gold_price__usd_per_ounce_')) else None,
                            'real_estate_index': float(row.get('real_estate_index', 0)) if pd.notna(row.get('real_estate_index')) else None,
                            'retail_sales_billion_usd': float(row.get('retail_sales__billion_usd_', 0)) if pd.notna(row.get('retail_sales__billion_usd_')) else None,
                            'bankruptcy_rate_pct': float(row.get('bankruptcy_rate__pct_', 0)) if pd.notna(row.get('bankruptcy_rate__pct_')) else None,
                            'mergers_acquisitions_deals': int(row.get('mergers___acquisitions_deals', 0)) if pd.notna(row.get('mergers___acquisitions_deals')) else None,
                            'venture_capital_funding_billion_usd': float(row.get('venture_capital_funding__billion_usd_', 0)) if pd.notna(row.get('venture_capital_funding__billion_usd_')) else None,
                            'consumer_spending_billion_usd': float(row.get('consumer_spending__billion_usd_', 0)) if pd.notna(row.get('consumer_spending__billion_usd_')) else None
                        })

                    rows_inserted += 1

                except Exception as e:
                    logger.warning(f"Failed to insert row for {row[profile.time_column]}: {e}")
                    continue

        return rows_inserted

    def get_ingestion_summary(self) -> Dict[str, Any]:
        """Get summary of all ingested datasets"""
        return {
            'datasets_ingested': len(self.ingested_datasets),
            'datasets': self.ingested_datasets,
            'profiles': {name: {
                'data_type': profile.data_type,
                'target_table': profile.target_table,
                'frequency': profile.frequency
            } for name, profile in self.profiles.items()}
        }


def main():
    """Main ingestion process"""
    ingestor = IntelligentDataIngestor()

    # Files to ingest
    files = [
        '/Users/zincdigital/Downloads/Financial_Crisis.csv',
        '/Users/zincdigital/Downloads/FRED_FEDFUNDS, 1D (1).csv',
        '/Users/zincdigital/Downloads/finance_economics_dataset.csv'
    ]

    print("🚀 INTELLIGENT DATA INGESTION - CBI-V14")
    print("=" * 50)
    print("🚫 NO FAKE DATA - Processing only real data files")
    print("")

    success_count = 0
    for file_path in files:
        if Path(file_path).exists():
            if ingestor.ingest_file(file_path):
                success_count += 1
        else:
            logger.warning(f"File not found: {file_path}")

    # Summary
    summary = ingestor.get_ingestion_summary()
    print("\n📊 INGESTION SUMMARY:")
    print(f"✅ Successfully ingested: {success_count}/{len(files)} files")

    for name, data in summary['datasets'].items():
        print(f"  📈 {name}: {data['rows']} rows, range: {data['date_range']}")

    if success_count > 0:
        print(f"\n🎯 READY: {success_count} real datasets ingested and available for CBI-V14")
    else:
        print("\n❌ No datasets were successfully ingested")

if __name__ == "__main__":
    main()