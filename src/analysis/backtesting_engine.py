#!/usr/bin/env python3
"""
Backtesting Engine for Procurement Strategy Validation

This script validates procurement strategies by simulating historical decisions
based on model predictions and comparing outcomes against actual prices.

Purpose: Validate BUY/WAIT/MONITOR signals and measure strategy performance.
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from google.cloud import bigquery
import warnings

warnings.filterwarnings("ignore")

def get_repo_root():
    """Find the repository root by looking for a marker file."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "QUICK_REFERENCE.txt").exists():
            return parent
    raise FileNotFoundError("Repository root not found.")

def load_historical_predictions(client: bigquery.Client, start_date: str, end_date: str):
    """Load historical predictions from BigQuery."""
    query = f"""
    SELECT 
        prediction_date,
        horizon,
        predicted_price,
        confidence_lower,
        confidence_upper,
        model_used,
        DATE_ADD(prediction_date, 
            CASE horizon
                WHEN '1W' THEN INTERVAL 7 DAY
                WHEN '1M' THEN INTERVAL 30 DAY
                WHEN '3M' THEN INTERVAL 90 DAY
                WHEN '6M' THEN INTERVAL 180 DAY
                ELSE INTERVAL 30 DAY
            END
        ) as target_date
    FROM `cbi-v14.predictions.daily_forecasts`
    WHERE prediction_date >= '{start_date}'
      AND prediction_date <= '{end_date}'
      AND horizon = '1M'  -- Focus on 1M horizon for procurement
    ORDER BY prediction_date
    """
    return client.query(query).to_dataframe()

def load_actual_prices(client: bigquery.Client, start_date: str, end_date: str):
    """Load actual soybean oil prices."""
    query = f"""
    SELECT 
        DATE(time) as date,
        close as actual_price
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
      AND DATE(time) >= '{start_date}'
      AND DATE(time) <= '{end_date}'
    ORDER BY date
    """
    return client.query(query).to_dataframe()

def generate_procurement_signal(row, strategy='conservative'):
    """
    Generate procurement signal based on prediction and strategy.
    
    Strategies:
    - 'conservative': Only BUY when strong confidence and price below prediction
    - 'aggressive': BUY when price is below prediction, even with lower confidence
    - 'risk_averse': BUY only when price is significantly below prediction
    """
    predicted = row['predicted_price']
    actual = row['actual_price']
    confidence_lower = row.get('confidence_lower', predicted * 0.95)
    confidence_upper = row.get('confidence_upper', predicted * 1.05)
    
    price_diff_pct = ((predicted - actual) / actual) * 100
    
    if strategy == 'conservative':
        if price_diff_pct > 2 and actual < confidence_lower:
            return 'BUY'
        elif price_diff_pct < -2 or actual > confidence_upper:
            return 'WAIT'
        else:
            return 'MONITOR'
    
    elif strategy == 'aggressive':
        if price_diff_pct > 1:
            return 'BUY'
        elif price_diff_pct < -3:
            return 'WAIT'
        else:
            return 'MONITOR'
    
    elif strategy == 'risk_averse':
        if price_diff_pct > 3 and actual < confidence_lower * 0.98:
            return 'BUY'
        elif price_diff_pct < -1:
            return 'WAIT'
        else:
            return 'MONITOR'
    
    return 'MONITOR'

def simulate_procurement_strategy(predictions_df: pd.DataFrame, actuals_df: pd.DataFrame, 
                                  strategy: str = 'conservative'):
    """
    Simulate procurement decisions and calculate performance metrics.
    """
    # Merge predictions with actuals
    merged = predictions_df.merge(
        actuals_df,
        left_on='target_date',
        right_on='date',
        how='inner'
    )
    
    if merged.empty:
        print("⚠️  No matching dates between predictions and actuals")
        return None
    
    # Generate signals
    merged['signal'] = merged.apply(
        lambda row: generate_procurement_signal(row, strategy),
        axis=1
    )
    
    # Simulate procurement decisions
    results = []
    inventory_level = 0  # Track procurement inventory
    total_cost = 0
    total_quantity = 0
    
    for _, row in merged.iterrows():
        signal = row['signal']
        actual_price = row['actual_price']
        predicted_price = row['predicted_price']
        target_date = row['target_date']
        
        # Simulate procurement decision
        if signal == 'BUY':
            # Buy 100 units (normalized)
            quantity = 100
            cost = actual_price * quantity
            inventory_level += quantity
            total_cost += cost
            total_quantity += quantity
            decision = 'PURCHASED'
        elif signal == 'WAIT':
            decision = 'DEFERRED'
            quantity = 0
            cost = 0
        else:  # MONITOR
            decision = 'MONITORED'
            quantity = 0
            cost = 0
        
        results.append({
            'date': target_date,
            'prediction_date': row['prediction_date'],
            'predicted_price': predicted_price,
            'actual_price': actual_price,
            'signal': signal,
            'decision': decision,
            'quantity': quantity,
            'cost': cost,
            'price_error': predicted_price - actual_price,
            'price_error_pct': ((predicted_price - actual_price) / actual_price) * 100
        })
    
    results_df = pd.DataFrame(results)
    
    # Calculate performance metrics
    buy_decisions = results_df[results_df['signal'] == 'BUY']
    
    if len(buy_decisions) == 0:
        print("⚠️  No BUY signals generated")
        return None
    
    avg_purchase_price = buy_decisions['actual_price'].mean()
    avg_predicted_price = buy_decisions['predicted_price'].mean()
    
    # Calculate savings vs always buying at average price
    always_buy_price = merged['actual_price'].mean()
    savings_vs_always_buy = (always_buy_price - avg_purchase_price) * total_quantity
    
    # Calculate accuracy metrics
    mae = results_df['price_error'].abs().mean()
    mape = (results_df['price_error_pct'].abs()).mean()
    rmse = np.sqrt((results_df['price_error'] ** 2).mean())
    
    # Calculate signal accuracy
    correct_signals = 0
    for _, row in buy_decisions.iterrows():
        # Signal is correct if we bought below predicted price
        if row['actual_price'] < row['predicted_price']:
            correct_signals += 1
    
    signal_accuracy = (correct_signals / len(buy_decisions)) * 100 if len(buy_decisions) > 0 else 0
    
    return {
        'strategy': strategy,
        'total_decisions': len(results_df),
        'buy_signals': len(buy_decisions),
        'wait_signals': len(results_df[results_df['signal'] == 'WAIT']),
        'monitor_signals': len(results_df[results_df['signal'] == 'MONITOR']),
        'avg_purchase_price': avg_purchase_price,
        'avg_predicted_price': avg_purchase_price,
        'always_buy_price': always_buy_price,
        'savings_vs_always_buy': savings_vs_always_buy,
        'total_quantity_purchased': total_quantity,
        'mae': mae,
        'mape': mape,
        'rmse': rmse,
        'signal_accuracy': signal_accuracy,
        'results': results_df
    }

def run_backtest(start_date: str, end_date: str, strategies: list = ['conservative', 'aggressive', 'risk_averse']):
    """Run backtest for specified date range and strategies."""
    print("=" * 80)
    print("🔬 PROCUREMENT STRATEGY BACKTESTING ENGINE")
    print("=" * 80)
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Strategies: {', '.join(strategies)}")
    print()
    
    client = bigquery.Client(project='cbi-v14')
    
    # Load data
    print("Loading historical predictions...")
    predictions_df = load_historical_predictions(client, start_date, end_date)
    print(f"✅ Loaded {len(predictions_df)} predictions")
    
    print("Loading actual prices...")
    actuals_df = load_actual_prices(client, start_date, end_date)
    print(f"✅ Loaded {len(actuals_df)} actual prices")
    
    if predictions_df.empty or actuals_df.empty:
        print("❌ Insufficient data for backtesting")
        return None
    
    # Run backtests for each strategy
    all_results = {}
    for strategy in strategies:
        print(f"\n--- Running backtest for {strategy} strategy ---")
        results = simulate_procurement_strategy(predictions_df, actuals_df, strategy)
        if results:
            all_results[strategy] = results
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("📊 BACKTEST RESULTS SUMMARY")
    print("=" * 80)
    
    summary_data = []
    for strategy, results in all_results.items():
        summary_data.append({
            'Strategy': strategy,
            'Buy Signals': results['buy_signals'],
            'Avg Purchase Price': f"${results['avg_purchase_price']:.2f}",
            'Savings vs Always Buy': f"${results['savings_vs_always_buy']:.2f}",
            'MAE': f"${results['mae']:.2f}",
            'MAPE': f"{results['mape']:.2f}%",
            'Signal Accuracy': f"{results['signal_accuracy']:.1f}%"
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    # Save detailed results
    repo_root = get_repo_root()
    output_dir = repo_root / "docs/analysis/backtesting"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for strategy, results in all_results.items():
        output_path = output_dir / f"backtest_{strategy}_{timestamp}.csv"
        results['results'].to_csv(output_path, index=False)
        print(f"\n✅ Detailed results saved to {output_path}")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Backtest procurement strategies.")
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date for backtest (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date for backtest (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--strategies",
        nargs='+',
        default=['conservative', 'aggressive', 'risk_averse'],
        help="Strategies to test (conservative, aggressive, risk_averse)"
    )
    
    args = parser.parse_args()
    
    run_backtest(args.start_date, args.end_date, args.strategies)

if __name__ == "__main__":
    main()

