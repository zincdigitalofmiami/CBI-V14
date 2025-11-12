#!/usr/bin/env python3
"""
FORECAST VALIDATION LAYER
Statistical plausibility checks to prevent extreme anomalies from reaching production
"""

from google.cloud import bigquery
from datetime import datetime
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

class ForecastValidator:
    """Validates forecasts against historical distribution to catch anomalies"""
    
    def __init__(self, historical_lookback_years: int = 5):
        self.lookback_years = historical_lookback_years
        self._historical_stats_cache = {}
    
    def get_historical_statistics(self, horizon_days: int) -> Dict[str, float]:
        """Get mean and std of historical price changes for given horizon"""
        
        cache_key = f"stats_{horizon_days}d"
        
        if cache_key in self._historical_stats_cache:
            return self._historical_stats_cache[cache_key]
        
        query = f"""
        WITH historical_changes AS (
            SELECT 
                (LEAD(zl_price_current, {horizon_days}) OVER(ORDER BY PARSE_DATE('%Y-%m-%d', date)) - zl_price_current) / 
                zl_price_current * 100 AS pct_change
            FROM `cbi-v14.models.training_dataset`
            WHERE PARSE_DATE('%Y-%m-%d', date) >= DATE_SUB(CURRENT_DATE(), INTERVAL {self.lookback_years} YEAR)
        )
        SELECT
            AVG(pct_change) AS mean_change,
            STDDEV(pct_change) AS std_change,
            MIN(pct_change) AS min_change,
            MAX(pct_change) AS max_change,
            APPROX_QUANTILES(pct_change, 100)[OFFSET(25)] AS q25,
            APPROX_QUANTILES(pct_change, 100)[OFFSET(50)] AS q50,
            APPROX_QUANTILES(pct_change, 100)[OFFSET(75)] AS q75
        FROM historical_changes
        WHERE pct_change IS NOT NULL
        """
        
        try:
            result = client.query(query).to_dataframe().iloc[0]
            
            stats = {
                'mean_change': float(result['mean_change']),
                'std_change': float(result['std_change']),
                'min_change': float(result['min_change']),
                'max_change': float(result['max_change']),
                'q25': float(result['q25']),
                'q50': float(result['q50']),
                'q75': float(result['q75'])
            }
            
            self._historical_stats_cache[cache_key] = stats
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching historical statistics: {e}")
            return {
                'mean_change': 0.0,
                'std_change': 5.0,  # Default to 5% std
                'min_change': -20.0,
                'max_change': 20.0,
                'q25': -3.0,
                'q50': 0.0,
                'q75': 3.0
            }
    
    def validate_forecast(
        self, 
        prediction: float, 
        current_price: float,
        horizon: str,
        model_name: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Validate if forecast is statistically plausible
        
        Returns:
            dict with:
                - is_valid: bool
                - original_prediction: float
                - corrected_prediction: float (if correction applied)
                - z_score: float
                - anomaly_type: str ('none', 'extreme_bearish', 'extreme_bullish')
                - correction_applied: bool
                - validation_message: str
        """
        
        # Map horizon to days
        horizon_map = {'1w': 7, '1m': 30, '3m': 90, '6m': 180}
        horizon_days = horizon_map.get(horizon, 30)
        
        # Get historical statistics
        stats = self.get_historical_statistics(horizon_days)
        
        # Calculate forecast percent change
        pct_change = (prediction - current_price) / current_price * 100
        
        # Calculate z-score
        z_score = (pct_change - stats['mean_change']) / stats['std_change']
        
        # Determine if anomalous
        is_extreme = abs(z_score) > 3.0
        is_very_extreme = abs(z_score) > 4.0
        
        # Determine anomaly type
        if z_score < -3.0:
            anomaly_type = 'extreme_bearish'
        elif z_score > 3.0:
            anomaly_type = 'extreme_bullish'
        else:
            anomaly_type = 'none'
        
        # Apply correction if needed (cap at 3σ)
        correction_applied = False
        corrected_prediction = prediction
        
        if is_very_extreme:
            # Apply hard cap at 3σ for forecasts beyond 4σ
            max_deviation_pct = stats['mean_change'] + (3.0 * stats['std_change'] * (1 if z_score > 0 else -1))
            corrected_prediction = current_price * (1 + max_deviation_pct / 100)
            correction_applied = True
            
            validation_message = (
                f"⚠️ FORECAST CORRECTED: {model_name} {horizon} forecast "
                f"({pct_change:+.2f}%) was {abs(z_score):.1f}σ from historical mean. "
                f"Corrected to {max_deviation_pct:+.2f}% (3σ limit)."
            )
            logger.warning(validation_message)
            
        elif is_extreme:
            # Flag but don't correct for 3-4σ deviations
            validation_message = (
                f"⚠️ FORECAST WARNING: {model_name} {horizon} forecast "
                f"({pct_change:+.2f}%) is {abs(z_score):.1f}σ from historical mean. "
                f"Proceeding without correction, but monitoring required."
            )
            logger.warning(validation_message)
            
        else:
            validation_message = (
                f"✅ FORECAST VALIDATED: {model_name} {horizon} forecast "
                f"({pct_change:+.2f}%) is {abs(z_score):.1f}σ from historical mean. "
                f"Within acceptable range."
            )
            logger.info(validation_message)
        
        return {
            'is_valid': not is_very_extreme,
            'original_prediction': prediction,
            'corrected_prediction': corrected_prediction,
            'original_pct_change': pct_change,
            'corrected_pct_change': (corrected_prediction - current_price) / current_price * 100,
            'z_score': z_score,
            'anomaly_type': anomaly_type,
            'correction_applied': correction_applied,
            'validation_message': validation_message,
            'historical_stats': stats,
            'model_name': model_name,
            'horizon': horizon,
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_all_horizons(
        self, 
        forecasts: Dict[str, float], 
        current_price: float,
        model_name: str = "unknown"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate all forecast horizons at once
        
        Args:
            forecasts: dict like {'1w': 50.5, '1m': 51.0, '3m': 48.0, '6m': 42.0}
            current_price: current ZL price
            model_name: name of model generating forecasts
        
        Returns:
            dict of validation results per horizon
        """
        
        results = {}
        
        for horizon, prediction in forecasts.items():
            results[horizon] = self.validate_forecast(
                prediction=prediction,
                current_price=current_price,
                horizon=horizon,
                model_name=model_name
            )
        
        # Check for cross-horizon consistency
        # (e.g., 1w should not predict +10% while 6m predicts -15%)
        pct_changes = [r['corrected_pct_change'] for r in results.values()]
        
        if max(pct_changes) - min(pct_changes) > 25:
            logger.warning(
                f"⚠️ CROSS-HORIZON INCONSISTENCY: Forecasts range from "
                f"{min(pct_changes):+.2f}% to {max(pct_changes):+.2f}% "
                f"(spread: {max(pct_changes) - min(pct_changes):.2f}pp)"
            )
        
        return results


# Singleton instance
validator = ForecastValidator(historical_lookback_years=5)


def validate_forecast_simple(
    prediction: float, 
    current_price: float, 
    horizon: str,
    model_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Simple wrapper for one-off forecast validation
    
    Example:
        result = validate_forecast_simple(42.0, 50.0, '6m', 'zl_boosted_tree_6m_v3')
        if result['correction_applied']:
            use_price = result['corrected_prediction']
        else:
            use_price = result['original_prediction']
    """
    return validator.validate_forecast(prediction, current_price, horizon, model_name)


if __name__ == "__main__":
    print("=" * 80)
    print("🔬 FORECAST VALIDATOR - TESTING")
    print("=" * 80)
    print()
    
    # Test case 1: Normal forecast (should pass)
    print("TEST 1: Normal forecast (+2%)")
    result1 = validate_forecast_simple(51.0, 50.0, '6m', 'test_normal')
    print(f"Result: {result1['validation_message']}")
    print()
    
    # Test case 2: Extreme bearish forecast (should correct)
    print("TEST 2: Extreme bearish forecast (-15.87%, the old V3 bug)")
    result2 = validate_forecast_simple(42.10, 50.04, '6m', 'test_extreme_bearish')
    print(f"Result: {result2['validation_message']}")
    print(f"Original: ${result2['original_prediction']:.2f} ({result2['original_pct_change']:+.2f}%)")
    print(f"Corrected: ${result2['corrected_prediction']:.2f} ({result2['corrected_pct_change']:+.2f}%)")
    print(f"Z-score: {result2['z_score']:.2f}")
    print()
    
    # Test case 3: Validate all horizons
    print("TEST 3: Validate all horizons")
    forecasts = {
        '1w': 50.5,
        '1m': 51.0,
        '3m': 49.0,
        '6m': 50.5
    }
    results = validator.validate_all_horizons(forecasts, 50.0, 'test_ensemble')
    for horizon, result in results.items():
        print(f"{horizon}: {result['corrected_pct_change']:+.2f}% (z={result['z_score']:.2f}, valid={result['is_valid']})")
    
    print()
    print("✅ Validation layer ready for production use")

