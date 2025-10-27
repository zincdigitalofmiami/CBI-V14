#!/usr/bin/env python3
"""
DASHBOARD PREPARATION RUNNER
Orchestrates the complete dashboard data preparation process.
Extracts REAL metadata from V4 models and stores for dashboard consumption.
"""

import sys
import logging
from datetime import datetime
from prediction_metadata_extractor import PredictionMetadataExtractor
from dashboard_data_pipeline import DashboardDataPipeline
from google.cloud import bigquery
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Complete dashboard preparation workflow
    """
    print("="*80)
    print("DASHBOARD PREPARATION - V4 MODEL METADATA EXTRACTION")
    print("="*80)
    print(f"Started: {datetime.now()}")
    print()
    
    try:
        # Initialize components
        logger.info("Initializing metadata extractor and dashboard pipeline")
        extractor = PredictionMetadataExtractor()
        pipeline = DashboardDataPipeline()
        
        # Initialize dashboard infrastructure
        logger.info("Setting up dashboard infrastructure")
        pipeline.initialize_dashboard_infrastructure()
        
        # Get latest input data
        logger.info("Retrieving latest input data")
        client = bigquery.Client(project='cbi-v14')
        
        query = """
        SELECT *
        FROM `cbi-v14.models.training_dataset`
        WHERE PARSE_DATE('%Y-%m-%d', date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        ORDER BY PARSE_DATE('%Y-%m-%d', date) DESC
        LIMIT 1
        """
        
        latest_data = client.query(query).to_dataframe()
        
        if latest_data.empty:
            logger.error("No recent data available for prediction")
            print("❌ ERROR: No recent data found")
            return 1
            
        input_date = latest_data['date'].iloc[0]
        logger.info(f"Using input data from: {input_date}")
        
        # Extract complete metadata from V4 models
        logger.info("Extracting prediction metadata from V4 models")
        metadata = extractor.generate_prediction_with_metadata(latest_data)
        
        # Store metadata in dashboard tables
        logger.info("Storing metadata in dashboard tables")
        pipeline.store_prediction_metadata(metadata)
        
        # Test dashboard queries
        logger.info("Testing dashboard queries")
        pipeline.test_dashboard_queries()
        
        # Display results
        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        
        print(f"Input Date: {input_date}")
        print(f"Regime: {metadata['regime']['regime']} (VIX: {metadata['regime']['vix_current']:.2f})")
        
        print(f"\nPredictions:")
        for horizon in ['1w', '1m', '3m', '6m']:
            pred = metadata['predictions'].get(horizon)
            if pred:
                intervals = metadata['confidence_intervals'].get(horizon, {})
                if intervals:
                    print(f"  {horizon}: ${pred:.2f} [{intervals['lower_68']:.2f}, {intervals['upper_68']:.2f}] (68% CI)")
                else:
                    print(f"  {horizon}: ${pred:.2f}")
            else:
                print(f"  {horizon}: ERROR")
                
        print(f"\nRecent Performance (90 days):")
        for horizon in ['1w', '1m', '3m', '6m']:
            acc = metadata['historical_accuracy'].get(horizon, {})
            if acc:
                print(f"  {horizon}: MAPE {acc['mape']:.2f}%, Dir Acc {acc['directional_accuracy']:.1f}% (n={acc['prediction_count']})")
            else:
                print(f"  {horizon}: No accuracy data")
                
        print(f"\nFeature Importance (Top 3):")
        for horizon in ['1w', '1m', '3m', '6m']:
            importance = metadata['feature_importance'].get(horizon, [])
            if importance and len(importance) > 0:
                top_features = [f for f in importance[:3] if f.get('weight') is not None]
                if top_features:
                    feature_names = [f['feature'] for f in top_features]
                    print(f"  {horizon}: {', '.join(feature_names)}")
                else:
                    print(f"  {horizon}: Feature list available (no weights)")
            else:
                print(f"  {horizon}: No feature data")
                
        print("\n" + "="*60)
        print("DASHBOARD DATA READY")
        print("="*60)
        print("Tables populated:")
        print("  ✅ cbi-v14.dashboard.prediction_history")
        print("  ✅ cbi-v14.dashboard.regime_history")
        print("  ✅ cbi-v14.dashboard.performance_metrics")
        print()
        print("Dashboard can now query real V4 model data:")
        print("  • Latest predictions with confidence intervals")
        print("  • Historical accuracy metrics by regime")
        print("  • Feature importance tracking")
        print("  • Regime detection timeline")
        print("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Dashboard preparation failed: {e}")
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
