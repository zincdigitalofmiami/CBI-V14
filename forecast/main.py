from fastapi import FastAPI
from fastapi.responses import JSONResponse
from google.cloud import bigquery
import numpy as np
import pandas as pd
import os, datetime as dt, logging
import pmdarima as pm

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("forecast-worker")
 
PROJECT = os.environ.get("PROJECT","cbi-v14")
DATASET = os.environ.get("DATASET","forecasting_data_warehouse")
SRC_TABLE = f"{PROJECT}.{DATASET}.soy_oil_features" # Use the rich features view
DST_TABLE = f"{PROJECT}.{DATASET}.soybean_oil_forecast"
 
app = FastAPI()
 
@app.get("/health")
def health():
    return {"ok": True, "ts": dt.datetime.utcnow().isoformat()}
 
def run_forecast(df: pd.DataFrame, steps=30) -> pd.DataFrame:
    """
    Runs a multivariate SARIMAX forecast.
    - `value` is the target variable to forecast.
    - All other numeric columns are used as exogenous features.
    """
    if df is None or df.empty:
        return pd.DataFrame()
 
    df = df.sort_values("date").set_index("date")
 
    # Separate target variable (endog) from features (exog)
    endog = df["value"]
    exog_cols = [col for col in df.columns if col != 'value' and pd.api.types.is_numeric_dtype(df[col])]
    exog = df[exog_cols]
    exog = df[exog_cols].copy()

    # Explicitly convert feature columns to numeric, coercing errors. This prevents dtype-related model failures.
    for col in exog_cols:
        exog[col] = pd.to_numeric(exog[col], errors='coerce')

    # Forward-fill and then back-fill to handle missing feature data robustly
    exog = exog.fillna(method='ffill').fillna(method='bfill')
 
    # Combine and drop any remaining rows where the target is still null
    full_df = pd.concat([endog, exog], axis=1).dropna()
    if len(full_df) < 20: # Require more data for a multivariate model
        log.warning("Not enough data for forecast after cleaning: %d rows", len(full_df))
        return pd.DataFrame()

    endog = full_df["value"]
    exog = full_df[exog_cols]
 
    # Use auto_arima to find the best model parameters automatically based on the data.
    # This is a crucial step for a robust, real-world forecasting system.
    model = pm.auto_arima(
        y=endog,
        X=exog,
        start_p=1, start_q=1,
        test='adf',       # Use ADF test to find the optimal 'd' for stationarity
        max_p=3, max_q=3, # Max non-seasonal order
        m=7,              # Weekly seasonality
        d=None,           # Let model determine 'd'
        seasonal=True,    # Enable seasonality
        start_P=0,
        D=1,              # Enforce seasonal differencing
        trace=False,      # Do not print status on every step
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True     # Use stepwise algorithm to find best model faster
    )
 
    # For forecasting, assume future exogenous variables hold their last known value
    # The data must be a DataFrame with the same columns as the training 'exog' data.
    # For forecasting, assume future exogenous variables hold their last known value.
    last_exog_values = exog.iloc[-1:]
    future_exog_list = [last_exog_values] * steps
    future_exog = pd.concat(future_exog_list)
    future_exog.index = pd.date_range(start=endog.index.max() + pd.Timedelta(days=1), periods=steps)
    fc, conf_int = model.predict(n_periods=steps, X=future_exog, return_conf_int=True)
    last = endog.index.max()
    dates = pd.date_range(start=last + pd.Timedelta(days=1), periods=steps, freq="D")
    out = pd.DataFrame({
        "date": dates,
        "forecast": fc,
        "forecast_lower": conf_int[:, 0],
        "forecast_upper": conf_int[:, 1],
        "created_at": dt.datetime.utcnow()
    })
    return out

@app.post("/forecast/run")
def run():
    try:
        bq = bigquery.Client(project=PROJECT)
        # Query all relevant features from the view to power the SARIMAX model.
        # Using a longer lookback period (1 year) for better model stability.
        q = f"""
        SELECT
            Date AS date,
            oil_price AS value,
            crush_spread,
            us_avg_temp,
            us_avg_precip,
            brazil_avg_temp,
            brazil_avg_precip,
            argentina_avg_temp,
            argentina_avg_precip,
            sentiment_score,
            soy_volatility,
            us_crush,
            china_imports
        FROM `{SRC_TABLE}`
        WHERE Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
          AND oil_price IS NOT NULL
        ORDER BY Date
        """
        df = bq.query(q).to_dataframe()
        log.info("source rows=%d", len(df))
        out = run_forecast(df, steps=30)
        if out.empty:
            return {"skipped": "not_enough_data"}
        
        # Define schema to include new confidence interval columns
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            schema=[
                bigquery.SchemaField("date", "TIMESTAMP"),
                bigquery.SchemaField("forecast", "FLOAT64"),
                bigquery.SchemaField("forecast_lower", "FLOAT64"),
                bigquery.SchemaField("forecast_upper", "FLOAT64"),
                bigquery.SchemaField("created_at", "TIMESTAMP"),
            ],
        )
        job = bq.load_table_from_dataframe(
            out, DST_TABLE, job_config=job_config
        )
        job.result()
        return {"rows_written": int(out.shape[0]), "table": DST_TABLE}
    except Exception as e:
        log.exception("Forecast failed")
        return JSONResponse(status_code=500, content={"error": str(e)})
