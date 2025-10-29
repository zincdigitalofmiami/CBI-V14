#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from typing import Dict
import sys

from google.cloud import bigquery

# Ensure project root is on path to import validator
PROJECT_ROOT = '/Users/zincdigital/CBI-V14'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from forecast.forecast_validator import validator  # type: ignore

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'models_v4'
SOURCE_TABLE = 'training_dataset_super_enriched'

MODELS = {
    '1w': 'baseline_boosted_tree_1w_v14_FINAL',
    '1m': 'baseline_boosted_tree_1m_v14_FINAL',
    '3m': 'baseline_boosted_tree_3m_v14_FINAL',
    '6m': 'baseline_boosted_tree_6m_v14_FINAL',
}

EXCLUDE_BASE = [
    'date',
    'econ_gdp_growth',
    'econ_unemployment_rate',
    'treasury_10y_yield',
    'news_article_count',
    'news_avg_score',
]

OTHER_TARGETS = ['target_1w', 'target_1m', 'target_3m', 'target_6m']

client = bigquery.Client(project=PROJECT_ID)


def get_latest_date_and_price() -> Dict[str, str]:
    q = f"""
    SELECT
      MAX(date) AS max_date,
      ANY_VALUE(zl_price_current) AS current_price
    FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`
    WHERE date = (SELECT MAX(date) FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`)
    """
    row = client.query(q).to_dataframe().iloc[0]
    # Ensure JSON-serializable types
    latest_date_str = str(row['max_date'])
    return {'date': latest_date_str, 'current_price': float(row['current_price'])}


def predict_for_date(date_str: str, horizon_key: str) -> float:
    target = {
        '1w': 'target_1w',
        '1m': 'target_1m',
        '3m': 'target_3m',
        '6m': 'target_6m',
    }[horizon_key]

    exclude_cols = EXCLUDE_BASE + [t for t in OTHER_TARGETS if t != target]
    except_clause = ', '.join(exclude_cols)

    model_name = MODELS[horizon_key]

    q = f"""
    WITH input_row AS (
      SELECT * EXCEPT({except_clause})
      FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`
      WHERE date = '{date_str}' AND {target} IS NOT NULL
      LIMIT 1
    )
    SELECT predicted_{target} AS yhat
    FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`, TABLE input_row)
    """
    df = client.query(q).to_dataframe()
    if df.empty:
        # Fall back to selecting without target not null filter
        q2 = f"""
        WITH input_row AS (
          SELECT * EXCEPT({except_clause})
          FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`
          WHERE date = '{date_str}'
          LIMIT 1
        )
        SELECT predicted_{target} AS yhat
        FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`, TABLE input_row)
        """
        df = client.query(q2).to_dataframe()
    if df.empty:
        raise RuntimeError(f"No prediction returned for {model_name} on {date_str}")
    return float(df['yhat'].iloc[0])


def main():
    meta = get_latest_date_and_price()
    latest_date = meta['date']
    current_price = meta['current_price']

    forecasts: Dict[str, float] = {}
    for hk in ['1w', '1m', '3m', '6m']:
        yhat = predict_for_date(latest_date, hk)
        forecasts[hk] = yhat

    # Validate
    results = validator.validate_all_horizons(forecasts, current_price, model_name='baseline_boosted_tree_v14_final')

    report = {
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'latest_date': latest_date,
        'current_price': current_price,
        'forecasts': forecasts,
        'validation': results,
    }

    print(json.dumps(report, indent=2))
    with open('forecast_validation_results.json', 'w') as f:
        json.dump(report, f, indent=2)


if __name__ == '__main__':
    main()
