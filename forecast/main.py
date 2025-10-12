"""
CBI-V14 Forecast API
Clean BigQuery ML implementation - no local ML libraries
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("forecast-api")

app = FastAPI(title="CBI-V14 Forecast API")

# CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# BigQuery configuration
PROJECT = os.environ.get("PROJECT_ID", "cbi-v14")
DATASET = os.environ.get("DATASET_ID", "forecasting_data_warehouse")
client = bigquery.Client(project=PROJECT)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CBI-V14 Forecast API",
        "status": "running",
        "architecture": "BigQuery ML (no local ML)",
        "version": "2.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "project": PROJECT,
        "dataset": DATASET
    }

@app.post("/forecast/run")
async def run_forecast():
    """
    Check forecast table status
    Models should be trained via BigQuery console, not this API
    """
    try:
        # Query existing forecast table
        query = f"""
        SELECT 
            COUNT(*) as forecast_rows,
            MAX(generated_at) as last_generated
        FROM `{PROJECT}.{DATASET}.soybean_oil_forecast`
        """
        
        result = client.query(query).to_dataframe()
        
        if result.iloc[0]['forecast_rows'] > 0:
            return {
                "status": "forecasts_available",
                "rows": int(result.iloc[0]['forecast_rows']),
                "last_generated": result.iloc[0]['last_generated'].isoformat(),
                "note": "Use GET /forecast/latest to retrieve predictions"
            }
        else:
            return {
                "status": "no_forecasts",
                "message": "Train BigQuery ML models first",
                "instructions": [
                    "Open BigQuery console",
                    "Run: CREATE MODEL forecasting_data_warehouse.zl_arima_v1 ...",
                    "Then: CREATE TABLE forecasting_data_warehouse.soybean_oil_forecast AS SELECT * FROM ML.FORECAST(...)",
                    "Finally: Call this endpoint again to verify"
                ]
            }
            
    except Exception as e:
        # Table doesn't exist yet
        return {
            "status": "not_ready",
            "message": "Forecast table not created yet",
            "error": str(e),
            "next_step": "Train BigQuery ML models via console"
        }

@app.get("/forecast/latest")
async def get_latest_forecast():
    """Get latest forecast results"""
    query = f"""
    SELECT date, predicted_close as forecast, lower_bound, upper_bound, generated_at
    FROM `{PROJECT}.{DATASET}.soybean_oil_forecast`
    ORDER BY date
    LIMIT 30
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if df.empty:
            return {
                "message": "No forecast available. Run POST /forecast/run first",
                "forecast": []
            }
        
        return {
            "model": "BigQuery-ARIMA",
            "forecast_days": len(df),
            "generated_at": df['generated_at'].iloc[0].isoformat(),
            "forecast": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/prices")
async def get_price_history(symbol: str = "ZL", days: int = 365):
    """Get historical price data for charts"""
    query = f"""
    SELECT
        DATE(time) as date,
        symbol,
        close,
        volume
    FROM `{PROJECT}.{DATASET}.soybean_oil_prices`
    WHERE symbol = '{symbol}'
        AND DATE(time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY time
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        return {
            "symbol": symbol,
            "days": days,
            "rows": len(df),
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/features")
async def get_feature_data(days: int = 90):
    """Get recent feature data for analysis"""
    query = f"""
    SELECT
        feature_date as date,
        zl_price as value,
        zl_open,
        zl_high,
        zl_low,
        zl_volume,
        zl_return_1d,
        zl_return_7d,
        zl_volatility_30d
    FROM `{PROJECT}.models.vw_master_feature_set_v1`
    WHERE feature_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY feature_date DESC
    """

    try:
        df = client.query(query).to_dataframe()

        return {
            "days": days,
            "rows": len(df),
            "features": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/training-snapshot")
async def get_training_snapshot(limit: int = 60):
    """Expose bounded neural training snapshot for the dashboard."""
    query = f"""
    SELECT
        timestamp,
        target_value,
        sma_7d,
        sma_30d,
        zl_volatility_30d,
        trend_direction
    FROM `{PROJECT}.models.zl_timesfm_training_v1`
    ORDER BY timestamp
    LIMIT {limit}
    """

    try:
        df = client.query(query).to_dataframe()
        return {
            "rows": len(df),
            "limit": limit,
            "data": df.to_dict("records")
        }
    except Exception as e:
        log.exception("Failed to fetch training snapshot")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast/baseline")
async def get_baseline_forecast():
    """Get baseline ARIMA forecast with historical data and confidence bands"""
    try:
        # Get historical data (last 90 days)
        historical_query = f"""
        SELECT 
            feature_date as date,
            zl_price as close,
            'historical' as type
        FROM `{PROJECT}.models.zl_price_training_base`
        WHERE feature_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        ORDER BY feature_date
        """
        
        # Get forecast data
        forecast_query = f"""
        SELECT 
            forecast_timestamp as date,
            forecast_value as close,
            prediction_interval_lower_bound as lower_bound,
            prediction_interval_upper_bound as upper_bound,
            'forecast' as type
        FROM `{PROJECT}.models.zl_forecast_baseline_v1`
        ORDER BY forecast_timestamp
        """
        
        historical_df = client.query(historical_query).to_dataframe()
        forecast_df = client.query(forecast_query).to_dataframe()
        
        # Get latest quote
        quote_query = f"""
        SELECT close, is_latest
        FROM `{PROJECT}.curated.vw_soybean_oil_quote`
        WHERE is_latest = true
        LIMIT 1
        """
        quote_df = client.query(quote_query).to_dataframe()
        
        return {
            "model": "ARIMA_PLUS_Baseline_v1",
            "generated_at": datetime.utcnow().isoformat(),
            "latest_price": float(quote_df.iloc[0]['close']) if not quote_df.empty else None,
            "historical": historical_df.to_dict('records'),
            "forecast": forecast_df.to_dict('records'),
            "total_points": len(historical_df) + len(forecast_df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)