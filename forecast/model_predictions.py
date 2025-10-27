
# Add this to forecast/main.py or create new file forecast/model_predictions.py

from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
from datetime import datetime
from typing import Dict, Any
import pandas as pd

router = APIRouter()
client = bigquery.Client(project='cbi-v14')

# Production models - ONLY USE THESE
PRODUCTION_MODELS = {
    '1w': 'zl_boosted_tree_1w_production',  # MAE: 1.58, R²: 0.96
    '1m': 'zl_boosted_tree_1m_production',  # MAE: 1.42, R²: 0.97
    '3m': 'zl_boosted_tree_3m_production',  # MAE: 1.26, R²: 0.97
    '6m': 'zl_boosted_tree_6m_production',  # MAE: 1.19, R²: 0.98
}

@router.get("/api/forecast/{horizon}")
async def get_forecast(horizon: str) -> Dict[str, Any]:
    """
    Get soybean oil price forecast for specified horizon
    Horizons: 1w (1 week), 1m (1 month), 3m (3 months), 6m (6 months)
    """
    
    if horizon not in PRODUCTION_MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid horizon. Choose from: {list(PRODUCTION_MODELS.keys())}")
    
    model_name = PRODUCTION_MODELS[horizon]
    
    try:
        # Get latest features
        features_query = """
        SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
        FROM `cbi-v14.models.training_dataset_final_v1`
        ORDER BY date DESC
        LIMIT 1
        """
        
        # Get prediction
        predict_query = f"""
        SELECT 
            predicted_target_{horizon} as forecast
        FROM ML.PREDICT(
            MODEL `cbi-v14.models.{model_name}`,
            ({features_query})
        )
        """
        
        result = client.query(predict_query).to_dataframe()
        
        if result.empty:
            raise HTTPException(status_code=500, detail="No prediction returned")
        
        forecast_value = float(result['forecast'].iloc[0])
        
        # Get current price for comparison
        current_query = """
        SELECT zl_price_current 
        FROM `cbi-v14.models.training_dataset_final_v1`
        ORDER BY date DESC
        LIMIT 1
        """
        current_result = client.query(current_query).to_dataframe()
        current_price = float(current_result['zl_price_current'].iloc[0]) if not current_result.empty else None
        
        return {
            "horizon": horizon,
            "forecast": round(forecast_value, 2),
            "current_price": round(current_price, 2) if current_price else None,
            "change_percent": round(((forecast_value - current_price) / current_price * 100), 1) if current_price else None,
            "model": model_name,
            "model_mae": {
                "1w": 1.58,
                "1m": 1.42,
                "3m": 1.26,
                "6m": 1.19
            }.get(horizon),
            "model_r2": {
                "1w": 0.96,
                "1m": 0.97,
                "3m": 0.97,
                "6m": 0.98
            }.get(horizon),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/forecast/all")
async def get_all_forecasts() -> Dict[str, Any]:
    """
    Get all horizon forecasts at once
    """
    
    forecasts = {}
    current_price = None
    
    for horizon in PRODUCTION_MODELS.keys():
        try:
            result = await get_forecast(horizon)
            forecasts[horizon] = result
            if current_price is None:
                current_price = result.get('current_price')
        except:
            forecasts[horizon] = None
    
    return {
        "current_price": current_price,
        "forecasts": forecasts,
        "timestamp": datetime.utcnow().isoformat()
    }

# Add to main.py:
# from forecast.model_predictions import router as model_router
# app.include_router(model_router, tags=["Model Predictions"])
