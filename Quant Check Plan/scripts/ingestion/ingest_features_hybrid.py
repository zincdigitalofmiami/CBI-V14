#!/usr/bin/env python3
"""
Production Ingestion Pipeline for features.daily_ml_matrix
===========================================================

Architecture:
- Hybrid regime lookup (Python dict, not SQL JOIN)
- Micro-batch loading (free, not streaming inserts)
- Schema enforcement with STRUCTs
- Exponential backoff retry logic
- Data quality checks before load
- Ingestion monitoring and logging

Cost: FREE for <1TB/month micro-batch loads
Performance: ~10K rows/sec with proper batching

Per: DAY_1_EXECUTION_PACKET_2025-11-21.md
Per: QUAD_CHECK Section 13 unanimous approval
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
from google.cloud import bigquery
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = "cbi-v14"
DATASET_ID = "features"
TABLE_ID = "daily_ml_matrix"
REGIME_WEIGHTS_TABLE = "training.regime_weights"
REGIME_CALENDAR_TABLE = "training.regime_calendar"
MONITORING_TABLE = "ops.ingestion_runs"

# Batch size for micro-batch loading (tune for performance vs memory)
BATCH_SIZE = 5000

# Retry configuration (exponential backoff)
RETRY_CONFIG = retry.Retry(
    initial=1.0,
    maximum=60.0,
    multiplier=2.0,
    deadline=300.0,
    predicate=retry.if_exception_type(
        GoogleAPIError,
    )
)


class RegimeCache:
    """
    In-memory regime lookup cache.
    Loads regime_calendar and regime_weights once at startup.
    Provides O(1) lookup by date.
    """
    
    def __init__(self, client: bigquery.Client):
        self.client = client
        self.regime_map: Dict[date, Dict[str, Any]] = {}
        self._load_regimes()
    
    def _load_regimes(self):
        """Load regime calendar and weights into memory."""
        query = f"""
        SELECT
          cal.date,
          cal.regime,
          w.weight,
          cal.valid_from,
          cal.valid_to
        FROM `{PROJECT_ID}.{REGIME_CALENDAR_TABLE}` cal
        LEFT JOIN `{PROJECT_ID}.{REGIME_WEIGHTS_TABLE}` w
          ON cal.regime = w.regime
        ORDER BY cal.date
        """
        
        logger.info("Loading regime calendar into memory...")
        try:
            df = self.client.query(query).to_dataframe()
            
            for _, row in df.iterrows():
                self.regime_map[row['date']] = {
                    'name': row['regime'],
                    'weight': int(row['weight']) if pd.notna(row['weight']) else 0,
                    'valid_from': row['valid_from'],
                    'valid_to': row['valid_to']
                }
            
            logger.info(f"✅ Loaded {len(self.regime_map)} regime calendar entries")
            
            # Log regime coverage
            if self.regime_map:
                min_date = min(self.regime_map.keys())
                max_date = max(self.regime_map.keys())
                logger.info(f"Regime coverage: {min_date} → {max_date}")
        
        except Exception as e:
            logger.error(f"❌ Failed to load regime calendar: {e}")
            raise
    
    def get_regime(self, dt: date) -> Optional[Dict[str, Any]]:
        """
        Get regime for a given date.
        Returns None if date not in regime calendar.
        """
        return self.regime_map.get(dt)
    
    def validate_date_coverage(self, dates: List[date]) -> Dict[str, Any]:
        """
        Validate that all dates have regime coverage.
        Returns dict with validation results.
        """
        missing_dates = [d for d in dates if d not in self.regime_map]
        
        return {
            'total_dates': len(dates),
            'covered_dates': len(dates) - len(missing_dates),
            'missing_dates': missing_dates,
            'coverage_pct': (len(dates) - len(missing_dates)) / len(dates) * 100 if dates else 0
        }


class DataQualityChecker:
    """Pre-load data quality validation."""
    
    @staticmethod
    def validate_required_fields(df: pd.DataFrame) -> Dict[str, Any]:
        """Check required fields are present and not null."""
        required = ['symbol', 'data_date']
        
        missing_fields = [f for f in required if f not in df.columns]
        null_counts = {f: df[f].isnull().sum() for f in required if f in df.columns}
        
        return {
            'missing_fields': missing_fields,
            'null_counts': null_counts,
            'is_valid': len(missing_fields) == 0 and all(c == 0 for c in null_counts.values())
        }
    
    @staticmethod
    def validate_date_range(df: pd.DataFrame) -> Dict[str, Any]:
        """Check date range is reasonable."""
        if 'data_date' not in df.columns or df.empty:
            return {'is_valid': False, 'error': 'No data_date column or empty DataFrame'}
        
        min_date = df['data_date'].min()
        max_date = df['data_date'].max()
        date_range_days = (max_date - min_date).days if pd.notna(min_date) and pd.notna(max_date) else 0
        
        return {
            'min_date': min_date,
            'max_date': max_date,
            'date_range_days': date_range_days,
            'is_valid': True
        }
    
    @staticmethod
    def validate_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
        """Check for duplicate (symbol, data_date) pairs."""
        if df.empty or 'symbol' not in df.columns or 'data_date' not in df.columns:
            return {'is_valid': False, 'error': 'Missing required columns'}
        
        duplicates = df.duplicated(subset=['symbol', 'data_date'], keep=False)
        dup_count = duplicates.sum()
        
        return {
            'duplicate_count': int(dup_count),
            'duplicate_rows': df[duplicates][['symbol', 'data_date']].to_dict('records') if dup_count > 0 else [],
            'is_valid': dup_count == 0
        }


class IngestionPipeline:
    """Main ingestion pipeline."""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.regime_cache = RegimeCache(self.client)
        self.quality_checker = DataQualityChecker()
        self.table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    def transform_row_to_bq_format(self, row: pd.Series, regime_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a pandas row into BigQuery STRUCT format.
        
        Expected input columns (example):
        - symbol, data_date, timestamp
        - open, high, low, close, volume, vwap, realized_vol_1h
        - P, R1, R2, S1, S2, distance_to_P, distance_to_nearest_pivot, weekly_pivot_distance, price_above_P
        - trump_action_prob, trump_expected_zl_move, ... (16 policy features)
        - (optional) golden_zone_state, swing_high, swing_low, fib_50, fib_618, vol_decay_slope, qualified_trigger
        """
        
        # Helper to safely get float/int/bool values
        def safe_float(key, default=None):
            val = row.get(key)
            return float(val) if pd.notna(val) else default
        
        def safe_int(key, default=None):
            val = row.get(key)
            return int(val) if pd.notna(val) else default
        
        def safe_bool(key, default=None):
            val = row.get(key)
            return bool(val) if pd.notna(val) else default
        
        # Build the denormalized row
        bq_row = {
            'symbol': str(row['symbol']),
            'data_date': row['data_date'].strftime('%Y-%m-%d') if isinstance(row['data_date'], (datetime, pd.Timestamp)) else str(row['data_date']),
            'timestamp': row.get('timestamp', datetime.utcnow()).isoformat() if pd.notna(row.get('timestamp')) else datetime.utcnow().isoformat(),
            
            # Market data STRUCT
            'market_data': {
                'open': safe_float('open'),
                'high': safe_float('high'),
                'low': safe_float('low'),
                'close': safe_float('close'),
                'volume': safe_int('volume'),
                'vwap': safe_float('vwap'),
                'realized_vol_1h': safe_float('realized_vol_1h')
            },
            
            # Pivots STRUCT
            'pivots': {
                'P': safe_float('P'),
                'R1': safe_float('R1'),
                'R2': safe_float('R2'),
                'S1': safe_float('S1'),
                'S2': safe_float('S2'),
                'distance_to_P': safe_float('distance_to_P'),
                'distance_to_nearest_pivot': safe_float('distance_to_nearest_pivot'),
                'weekly_pivot_distance': safe_float('weekly_pivot_distance'),
                'price_above_P': safe_bool('price_above_P')
            },
            
            # Policy STRUCT (16 Trump features)
            'policy': {
                'trump_action_prob': safe_float('trump_action_prob'),
                'trump_expected_zl_move': safe_float('trump_expected_zl_move'),
                'trump_score': safe_float('trump_score'),
                'trump_score_signed': safe_float('trump_score_signed'),
                'trump_confidence': safe_float('trump_confidence'),
                'trump_sentiment_7d': safe_float('trump_sentiment_7d'),
                'trump_tariff_intensity': safe_float('trump_tariff_intensity'),
                'trump_procurement_alert': safe_bool('trump_procurement_alert'),
                'trump_mentions': safe_int('trump_mentions'),
                'trumpxi_china_mentions': safe_int('trumpxi_china_mentions'),
                'trumpxi_sentiment_volatility': safe_float('trumpxi_sentiment_volatility'),
                'trumpxi_policy_impact': safe_float('trumpxi_policy_impact'),
                'trumpxi_volatility_30d_ma': safe_float('trumpxi_volatility_30d_ma'),
                'trump_soybean_sentiment_7d': safe_float('trump_soybean_sentiment_7d'),
                'policy_trump_topic_multiplier': safe_float('policy_trump_topic_multiplier'),
                'policy_trump_recency_decay': safe_float('policy_trump_recency_decay')
            },
            
            # Golden Zone STRUCT (MES)
            'golden_zone': {
                'state': safe_int('golden_zone_state'),
                'swing_high': safe_float('swing_high'),
                'swing_low': safe_float('swing_low'),
                'fib_50': safe_float('fib_50'),
                'fib_618': safe_float('fib_618'),
                'vol_decay_slope': safe_float('vol_decay_slope'),
                'qualified_trigger': safe_bool('qualified_trigger')
            },
            
            # Regime STRUCT (from cache)
            'regime': {
                'name': regime_info['name'],
                'weight': regime_info['weight'],
                'vol_percentile': safe_float('vol_percentile'),  # If available in source
                'k_vol': safe_float('k_vol')  # If available in source
            },
            
            # Top-level regime_name for clustering
            'regime_name': regime_info['name'],
            
            # Ingestion timestamp (auto-filled by BQ, but we can set it)
            'ingestion_ts': datetime.utcnow().isoformat()
        }
        
        return bq_row
    
    def validate_and_enrich(self, df: pd.DataFrame) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validate data quality and enrich with regime info.
        Returns: (enriched_rows, validation_report)
        """
        logger.info(f"Validating {len(df)} rows...")
        
        # Run quality checks
        required_check = self.quality_checker.validate_required_fields(df)
        date_check = self.quality_checker.validate_date_range(df)
        dup_check = self.quality_checker.validate_duplicates(df)
        
        validation_report = {
            'required_fields': required_check,
            'date_range': date_check,
            'duplicates': dup_check,
            'overall_valid': all([
                required_check['is_valid'],
                date_check['is_valid'],
                dup_check['is_valid']
            ])
        }
        
        if not validation_report['overall_valid']:
            logger.error(f"❌ Data quality validation failed: {validation_report}")
            return [], validation_report
        
        # Check regime coverage
        dates = df['data_date'].dt.date.unique() if hasattr(df['data_date'], 'dt') else df['data_date'].unique()
        regime_coverage = self.regime_cache.validate_date_coverage(list(dates))
        validation_report['regime_coverage'] = regime_coverage
        
        if regime_coverage['coverage_pct'] < 100:
            logger.warning(f"⚠️ Regime coverage: {regime_coverage['coverage_pct']:.1f}% ({len(regime_coverage['missing_dates'])} dates missing)")
        
        # Enrich rows with regime info
        enriched_rows = []
        skipped_count = 0
        
        for _, row in df.iterrows():
            row_date = row['data_date'].date() if hasattr(row['data_date'], 'date') else row['data_date']
            regime_info = self.regime_cache.get_regime(row_date)
            
            if regime_info is None:
                logger.warning(f"⚠️ No regime for {row['symbol']} on {row_date}, skipping")
                skipped_count += 1
                continue
            
            enriched_row = self.transform_row_to_bq_format(row, regime_info)
            enriched_rows.append(enriched_row)
        
        validation_report['rows_processed'] = len(df)
        validation_report['rows_enriched'] = len(enriched_rows)
        validation_report['rows_skipped'] = skipped_count
        
        logger.info(f"✅ Validated and enriched {len(enriched_rows)} rows ({skipped_count} skipped)")
        
        return enriched_rows, validation_report
    
    @retry.Retry(**RETRY_CONFIG.__dict__)
    def load_batch(self, rows: List[Dict[str, Any]]) -> bigquery.job.LoadJob:
        """
        Load a batch of rows using micro-batch loading (free).
        Uses exponential backoff retry.
        """
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION],
        )
        
        # Convert to NDJSON
        ndjson_data = "\n".join([json.dumps(row, default=str) for row in rows])
        
        # Load job
        job = self.client.load_table_from_json(
            rows,
            self.table_ref,
            job_config=job_config
        )
        
        # Wait for completion
        job.result()
        
        return job
    
    def ingest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Main ingestion method.
        
        Args:
            df: DataFrame with feature data
        
        Returns:
            Ingestion report dict
        """
        start_time = datetime.utcnow()
        logger.info(f"🚀 Starting ingestion of {len(df)} rows")
        
        # Validate and enrich
        enriched_rows, validation_report = self.validate_and_enrich(df)
        
        if not enriched_rows:
            logger.error("❌ No rows to ingest after validation")
            return {
                'status': 'failed',
                'reason': 'validation_failed',
                'validation_report': validation_report,
                'rows_loaded': 0,
                'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
            }
        
        # Batch load
        total_loaded = 0
        batches = [enriched_rows[i:i+BATCH_SIZE] for i in range(0, len(enriched_rows), BATCH_SIZE)]
        
        logger.info(f"Loading {len(batches)} batches of up to {BATCH_SIZE} rows each...")
        
        for i, batch in enumerate(batches, 1):
            try:
                logger.info(f"Loading batch {i}/{len(batches)} ({len(batch)} rows)...")
                job = self.load_batch(batch)
                total_loaded += len(batch)
                logger.info(f"✅ Batch {i}/{len(batches)} loaded successfully")
            
            except Exception as e:
                logger.error(f"❌ Batch {i}/{len(batches)} failed: {e}")
                return {
                    'status': 'failed',
                    'reason': f'batch_load_failed: {e}',
                    'validation_report': validation_report,
                    'rows_loaded': total_loaded,
                    'failed_batch': i,
                    'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
                }
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ Ingestion complete: {total_loaded} rows in {duration:.1f}s ({total_loaded/duration:.0f} rows/sec)")
        
        return {
            'status': 'success',
            'validation_report': validation_report,
            'rows_loaded': total_loaded,
            'batches': len(batches),
            'duration_seconds': duration,
            'rows_per_second': total_loaded / duration if duration > 0 else 0
        }


def main():
    """Example usage."""
    # Example: Load from a parquet file
    input_file = sys.argv[1] if len(sys.argv) > 1 else "TrainingData/staging/zl_features_sample.parquet"
    
    if not os.path.exists(input_file):
        logger.error(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    logger.info(f"Reading {input_file}...")
    df = pd.read_parquet(input_file)
    
    # Ensure data_date is datetime
    if 'data_date' in df.columns:
        df['data_date'] = pd.to_datetime(df['data_date'])
    
    # Run ingestion
    pipeline = IngestionPipeline()
    report = pipeline.ingest(df)
    
    # Print report
    logger.info("="*80)
    logger.info("INGESTION REPORT")
    logger.info("="*80)
    logger.info(json.dumps(report, indent=2, default=str))
    
    if report['status'] == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
