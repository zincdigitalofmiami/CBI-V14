#!/usr/bin/env python3
"""
Verification Protocol: Iteration Count Impact
Empirically verify whether 100 iterations truly gives better MAPE
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys

client = bigquery.Client()

def run_query(query, description):
    """Run a BigQuery query and return results"""
    print(f"\n{'='*80}")
    print(f"METHOD: {description}")
    print(f"{'='*80}")
    print(f"\nQuery:\n{query}\n")
    try:
        df = client.query(query).to_dataframe()
        print(f"\nResults ({len(df)} rows):")
        print(df.to_string())
        return df
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("VERIFICATION PROTOCOL: ITERATION COUNT IMPACT")
    print("="*80)
    
    # METHOD 1: Check existing model performance
    method1_query = """
    SELECT 
      iteration,
      loss as training_loss,
      eval_loss as evaluation_loss,
      ROUND(eval_loss / NULLIF(loss, 0), 2) as overfit_ratio,
      learning_rate
    FROM ML.TRAINING_INFO(MODEL `cbi-v14.models_v4.bqml_1w`)
    WHERE iteration IN (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
    ORDER BY iteration;
    """
    method1_df = run_query(method1_query, "Check Existing Model Performance (Training Info)")
    
    # METHOD 2: Calculate actual MAPE on recent predictions
    method2_query = """
    WITH predictions AS (
      SELECT 
        p.forecast_date,
        p.horizon,
        p.predicted_value,
        -- Get actual price from train_1w view
        t.zl_price_current as actual_price
      FROM `cbi-v14.predictions_uc1.production_forecasts` p
      LEFT JOIN `cbi-v14.models_v4.train_1w` t
        ON p.forecast_date = t.date
      WHERE p.forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    )
    SELECT 
      horizon,
      COUNT(*) as predictions_made,
      ROUND(AVG(ABS(predicted_value - actual_price) / NULLIF(actual_price, 0)) * 100, 2) as actual_mape,
      ROUND(MIN(ABS(predicted_value - actual_price) / NULLIF(actual_price, 0)) * 100, 2) as best_mape,
      ROUND(MAX(ABS(predicted_value - actual_price) / NULLIF(actual_price, 0)) * 100, 2) as worst_mape
    FROM predictions
    WHERE actual_price IS NOT NULL
    GROUP BY horizon
    ORDER BY horizon;
    """
    method2_df = run_query(method2_query, "Calculate Actual MAPE on Recent Predictions")
    
    # METHOD 3: Check validation set performance
    method3_query = """
    SELECT 
      '100 iterations' as model_version,
      *
    FROM ML.EVALUATE(
      MODEL `cbi-v14.models_v4.bqml_1w`,
      (SELECT * FROM `cbi-v14.models_v4.train_1w` 
       WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
         AND target_1w IS NOT NULL)
    );
    """
    method3_df = run_query(method3_query, "Check Validation Set Performance (Holdout Data)")
    
    # QUICK REALITY CHECK
    reality_check_query = """
    SELECT 
      model_name,
      horizon,
      forecast_date,
      predicted_value,
      49.56 as current_actual,
      ROUND(ABS(predicted_value - 49.56) / 49.56 * 100, 2) as real_mape_pct
    FROM `cbi-v14.predictions_uc1.production_forecasts`
    WHERE forecast_date = DATE('2025-11-04')
    ORDER BY horizon;
    """
    reality_check_df = run_query(reality_check_query, "Quick Reality Check (Nov 4 Predictions)")
    
    # ANALYSIS SUMMARY
    print(f"\n{'='*80}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*80}\n")
    
    if method1_df is not None and not method1_df.empty:
        print("\n🔍 METHOD 1 INSIGHTS:")
        print("- Look for overfit_ratio > 2.0 (indicates overfitting)")
        print("- Check if eval_loss starts increasing while training_loss decreases")
        max_overfit = method1_df['overfit_ratio'].max() if 'overfit_ratio' in method1_df.columns else None
        if max_overfit and max_overfit > 2.0:
            print(f"⚠️  WARNING: Max overfit ratio is {max_overfit:.2f} - overfitting detected!")
    
    if method2_df is not None and not method2_df.empty:
        print("\n🔍 METHOD 2 INSIGHTS:")
        print("- Compare actual_mape to stated 0.70-1.29% MAPE")
        print("- If actual_mape is much higher, the stated MAPE is likely from training data")
    
    if method3_df is not None and not method3_df.empty:
        print("\n🔍 METHOD 3 INSIGHTS:")
        print("- Validation set performance shows real-world accuracy")
        print("- Compare to training performance to detect overfitting")
    
    if reality_check_df is not None and not reality_check_df.empty:
        print("\n🔍 REALITY CHECK INSIGHTS:")
        print("- Compare predicted_value to actual $49.56")
        print("- The 3M prediction showing 10.8% error suggests overfitting")
        
        # Check for high errors
        high_errors = reality_check_df[reality_check_df['real_mape_pct'] > 5.0]
        if not high_errors.empty:
            print(f"\n⚠️  HIGH ERRORS DETECTED:")
            print(high_errors[['horizon', 'predicted_value', 'real_mape_pct']].to_string())
    
    print("\n" + "="*80)
    print("RECOMMENDATION:")
    print("="*80)
    print("""
    If overfit_ratio > 2.0 and eval_loss increases after iteration 40-50:
    → Reduce max_iterations to 40-50 with early_stop=TRUE
    
    If actual_mape >> stated MAPE (0.70-1.29%):
    → The stated MAPE is from training data (overfitted), not real performance
    
    If validation MAPE is much higher than training MAPE:
    → Model is overfitting, reduce iterations
    """)

if __name__ == "__main__":
    main()

