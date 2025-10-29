#!/usr/bin/env python3
import sys
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

from google.cloud import bigquery

# Import validator
PROJECT_ROOT = '/Users/zincdigital/CBI-V14'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from forecast.forecast_validator import validator  # type: ignore

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'models_v4'
SOURCE_TABLE = 'training_dataset_super_enriched'
LOG_TABLE = f'{PROJECT_ID}.{DATASET_ID}.forecast_validation_logs'
ALERT_TABLE = f'{PROJECT_ID}.{DATASET_ID}.forecast_validation_alerts'

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


def ensure_tables():
    """Create log and alert tables if they don't exist (simple schemas)."""
    tables = {
        LOG_TABLE: [
            bigquery.SchemaField('timestamp', 'TIMESTAMP'),
            bigquery.SchemaField('date', 'DATE'),
            bigquery.SchemaField('current_price', 'FLOAT'),
            bigquery.SchemaField('forecast_1w', 'FLOAT'),
            bigquery.SchemaField('forecast_1m', 'FLOAT'),
            bigquery.SchemaField('forecast_3m', 'FLOAT'),
            bigquery.SchemaField('forecast_6m', 'FLOAT'),
            bigquery.SchemaField('z_1w', 'FLOAT'),
            bigquery.SchemaField('z_1m', 'FLOAT'),
            bigquery.SchemaField('z_3m', 'FLOAT'),
            bigquery.SchemaField('z_6m', 'FLOAT'),
            bigquery.SchemaField('cross_spread_pp', 'FLOAT'),
            bigquery.SchemaField('is_alert', 'BOOL'),
            bigquery.SchemaField('alert_reason', 'STRING'),
        ],
        ALERT_TABLE: [
            bigquery.SchemaField('timestamp', 'TIMESTAMP'),
            bigquery.SchemaField('date', 'DATE'),
            bigquery.SchemaField('current_price', 'FLOAT'),
            bigquery.SchemaField('forecast_1w', 'FLOAT'),
            bigquery.SchemaField('forecast_1m', 'FLOAT'),
            bigquery.SchemaField('forecast_3m', 'FLOAT'),
            bigquery.SchemaField('forecast_6m', 'FLOAT'),
            bigquery.SchemaField('z_1w', 'FLOAT'),
            bigquery.SchemaField('z_1m', 'FLOAT'),
            bigquery.SchemaField('z_3m', 'FLOAT'),
            bigquery.SchemaField('z_6m', 'FLOAT'),
            bigquery.SchemaField('cross_spread_pp', 'FLOAT'),
            bigquery.SchemaField('alert_reason', 'STRING'),
        ],
    }
    for table_fqn, schema in tables.items():
        try:
            client.get_table(table_fqn)
        except Exception:
            table = bigquery.Table(table_fqn, schema=schema)
            client.create_table(table)


def get_latest_date_and_price() -> Dict[str, Any]:
    q = f"""
    SELECT
      MAX(date) AS max_date,
      ANY_VALUE(zl_price_current) AS current_price
    FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`
    WHERE date = (SELECT MAX(date) FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`)
    """
    row = client.query(q).to_dataframe().iloc[0]
    return {'date': str(row['max_date']), 'current_price': float(row['current_price'])}


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
      WHERE date = '{date_str}'
      LIMIT 1
    )
    SELECT predicted_{target} AS yhat
    FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`, TABLE input_row)
    """
    df = client.query(q).to_dataframe()
    if df.empty:
        raise RuntimeError(f"No prediction returned for {model_name} on {date_str}")
    return float(df['yhat'].iloc[0])


def send_email_alert(subject: str, body: str) -> None:
    to_addr = os.getenv('ALERT_EMAIL_TO')
    from_addr = os.getenv('ALERT_EMAIL_FROM', 'alerts@cbi-v14.local')

    if not to_addr:
        print("Email alerts not configured (ALERT_EMAIL_TO missing). Skipping email.")
        return

    # Prefer SendGrid if available
    sg_key = os.getenv('SENDGRID_API_KEY')
    if sg_key:
        try:
            import requests
            resp = requests.post(
                'https://api.sendgrid.com/v3/mail/send',
                headers={
                    'Authorization': f'Bearer {sg_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'personalizations': [{'to': [{'email': to_addr}]}],
                    'from': {'email': from_addr},
                    'subject': subject,
                    'content': [{'type': 'text/plain', 'value': body}]
                }
            )
            if resp.status_code >= 400:
                print(f"SendGrid error: {resp.status_code} {resp.text}")
            return
        except Exception as e:
            print(f"SendGrid exception: {e}")
            # fall through to SMTP

    # SMTP fallback
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    if not host or not user or not pwd:
        print("SMTP not configured (SMTP_HOST/USER/PASS missing). Skipping email.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate(localtime=True)

    with smtplib.SMTP(host, port) as s:
        if use_tls:
            s.starttls()
        s.login(user, pwd)
        s.sendmail(from_addr, [to_addr], msg.as_string())


def main():
    ensure_tables()
    meta = get_latest_date_and_price()
    latest_date = meta['date']
    current_price = meta['current_price']

    forecasts: Dict[str, float] = {}
    for hk in ['1w', '1m', '3m', '6m']:
        forecasts[hk] = predict_for_date(latest_date, hk)

    results = validator.validate_all_horizons(forecasts, current_price, model_name='baseline_boosted_tree_v14_final')

    z = {h: float(results[h]['z_score']) for h in results}
    pct = [results[h]['corrected_pct_change'] for h in results]
    cross_spread = float(max(pct) - min(pct))

    alert_reasons = []
    for h in ['1w', '1m', '3m', '6m']:
        if abs(z[h]) > 3.0:
            alert_reasons.append(f'{h} | {z[h]:.2f}σ')
    if cross_spread > 25.0:
        alert_reasons.append(f'cross_spread {cross_spread:.2f}pp')

    is_alert = len(alert_reasons) > 0
    reason_str = '; '.join(alert_reasons) if is_alert else ''

    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    log_row = [{
        'timestamp': timestamp,
        'date': latest_date,
        'current_price': current_price,
        'forecast_1w': forecasts['1w'],
        'forecast_1m': forecasts['1m'],
        'forecast_3m': forecasts['3m'],
        'forecast_6m': forecasts['6m'],
        'z_1w': z['1w'],
        'z_1m': z['1m'],
        'z_3m': z['3m'],
        'z_6m': z['6m'],
        'cross_spread_pp': cross_spread,
        'is_alert': is_alert,
        'alert_reason': reason_str,
    }]

    client.insert_rows_json(LOG_TABLE, log_row)

    if is_alert:
        client.insert_rows_json(ALERT_TABLE, log_row)
        # Prepare email body
        body = (
            f"Forecast Validation Alert\n"
            f"Timestamp: {timestamp}\n"
            f"Date: {latest_date}\n"
            f"Current Price: {current_price:.4f}\n\n"
            f"Forecasts:\n"
            f"  1W: {forecasts['1w']:.4f} (z={z['1w']:.2f})\n"
            f"  1M: {forecasts['1m']:.4f} (z={z['1m']:.2f})\n"
            f"  3M: {forecasts['3m']:.4f} (z={z['3m']:.2f})\n"
            f"  6M: {forecasts['6m']:.4f} (z={z['6m']:.2f})\n\n"
            f"Cross-horizon spread: {cross_spread:.2f} pp\n"
            f"Reasons: {reason_str}\n"
        )
        send_email_alert(subject='CBI-V14 Forecast Alert', body=body)

    report = {
        'timestamp': timestamp,
        'latest_date': latest_date,
        'current_price': current_price,
        'forecasts': forecasts,
        'z_scores': z,
        'cross_spread_pp': cross_spread,
        'is_alert': is_alert,
        'alert_reason': reason_str,
    }
    with open('monitor_last.json', 'w') as f:
        json.dump(report, f, indent=2)

    if is_alert:
        print(f"ALERT: {reason_str}")
        sys.exit(2)
    else:
        print("Monitor OK: no alerts")


if __name__ == '__main__':
    main()
