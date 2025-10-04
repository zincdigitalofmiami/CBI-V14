"""
CBI-V14 Forecast API
Clean BigQuery ML implementation - no local ML libraries
"""

from fastapi import FastAPI, HTTPException
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
    FROM `{PROJECT}.{DATASET}.soybean_prices`
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
        date,
        value,
        sma_5,
        sma_20,
        argentina_precip,
        us_precip
    FROM `{PROJECT}.{DATASET}.soy_oil_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY date DESC
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)