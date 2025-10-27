"""
V3 Model Predictions API
Production-ready endpoints for the best performing models
WITH STATISTICAL VALIDATION LAYER
"""

from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

# Import forecast validator
try:
    from forecast_validator import validator
    VALIDATION_ENABLED = True
except ImportError:
    logger.warning("Forecast validator not available, running without validation")
    VALIDATION_ENABLED = False

# Configure logging
logger = logging.getLogger(__name__)

# Initialize BigQuery client
client = bigquery.Client(project="cbi-v14")

# Create router
router = APIRouter(prefix="/api/v3", tags=["V3 Model Predictions"])

# Best models for each horizon (UPDATED: Enriched models with news/social features)
BEST_MODELS = {
    "1w": {
        "model": "zl_boosted_tree_1w_v3_enriched",
        "mae": 1.23,
        "r2": 0.977,
        "type": "Boosted Tree (Enriched)",
        "mape": 2.46
    },
    "1m": {
        "model": "zl_boosted_tree_1m_v3_enriched",
        "mae": 0.99,
        "r2": 0.983,
        "type": "Boosted Tree (Enriched)",
        "mape": 1.98
    },
    "3m": {
        "model": "zl_boosted_tree_3m_v3_enriched",
        "mae": 1.20,
        "r2": 0.978,
        "type": "Boosted Tree (Enriched)",
        "mape": 2.40
    },
    "6m": {
        "model": "zl_boosted_tree_6m_v3_enriched",
        "mae": 1.25,
        "r2": 0.972,
        "type": "Boosted Tree (Enriched)",
        "mape": 2.49
    }
}

# Baseline models for comparison
BASELINE_MODELS = {
    "1w": "zl_linear_1w_v3",
    "1m": "zl_linear_1m_v3",
    "3m": "zl_linear_3m_v3",
    "6m": "zl_linear_6m_v3"
}

class PredictionResponse(BaseModel):
    horizon: str
    model_type: str
    model_name: str
    prediction: float
    current_price: float
    predicted_change: float
    predicted_change_pct: float
    confidence_metrics: Dict[str, float]
    timestamp: str
    validation_status: Optional[Dict[str, Any]] = None  # NEW: validation results

class ComparisonResponse(BaseModel):
    horizon: str
    current_price: float
    boosted_tree_prediction: float
    linear_baseline_prediction: float
    difference: float
    timestamp: str

@router.get("/forecast/{horizon}", response_model=PredictionResponse)
async def get_forecast(horizon: str):
    """
    Get forecast for specified horizon using the best performing model
    
    Horizons: 1w (1-week), 1m (1-month), 3m (3-month), 6m (6-month)
    """
    if horizon not in BEST_MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid horizon. Choose from: {list(BEST_MODELS.keys())}")
    
    model_info = BEST_MODELS[horizon]
    model_name = model_info["model"]
    
    try:
        # Get latest features from training dataset
        features_query = """
        SELECT *
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
        """
        features_df = client.query(features_query).to_dataframe()
        
        if features_df.empty:
            raise HTTPException(status_code=404, detail="No training data available")
        
        current_price = float(features_df['zl_price_current'].iloc[0])
        
        # Make prediction
        predict_query = f"""
        SELECT predicted_target_{horizon} as prediction
        FROM ML.PREDICT(
            MODEL `cbi-v14.models.{model_name}`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
        )
        """
        
        prediction_df = client.query(predict_query).to_dataframe()
        
        if prediction_df.empty:
            raise HTTPException(status_code=500, detail="Prediction failed")
        
        prediction = float(prediction_df['prediction'].iloc[0])
        
        # VALIDATE FORECAST STATISTICALLY
        validation_result = None
        if VALIDATION_ENABLED:
            validation_result = validator.validate_forecast(
                prediction=prediction,
                current_price=current_price,
                horizon=horizon,
                model_name=model_name
            )
            
            # Use corrected prediction if validation applied correction
            if validation_result['correction_applied']:
                logger.warning(f"Forecast corrected for {horizon}: {prediction:.2f} → {validation_result['corrected_prediction']:.2f}")
                prediction = validation_result['corrected_prediction']
        
        change = prediction - current_price
        change_pct = (change / current_price) * 100
        
        return PredictionResponse(
            horizon=horizon,
            model_type=model_info["type"],
            model_name=model_name,
            prediction=round(prediction, 2),
            current_price=round(current_price, 2),
            predicted_change=round(change, 2),
            predicted_change_pct=round(change_pct, 2),
            confidence_metrics={
                "mae": model_info["mae"],
                "r2": model_info["r2"],
                "mape": model_info.get("mape", None),
                "confidence_interval_width": model_info["mae"] * 2  # Approximate 95% CI
            },
            timestamp=datetime.now().isoformat(),
            validation_status={
                "enabled": VALIDATION_ENABLED,
                "is_valid": validation_result['is_valid'] if validation_result else True,
                "z_score": round(validation_result['z_score'], 2) if validation_result else None,
                "anomaly_type": validation_result['anomaly_type'] if validation_result else 'none',
                "correction_applied": validation_result['correction_applied'] if validation_result else False
            } if VALIDATION_ENABLED else None
        )
        
    except Exception as e:
        logger.error(f"Prediction error for {horizon}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare/{horizon}", response_model=ComparisonResponse)
async def compare_models(horizon: str):
    """
    Compare Boosted Tree prediction with Linear baseline for a given horizon
    """
    if horizon not in BEST_MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid horizon. Choose from: {list(BEST_MODELS.keys())}")
    
    try:
        # Get current price
        features_query = """
        SELECT zl_price_current
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
        """
        features_df = client.query(features_query).to_dataframe()
        current_price = float(features_df['zl_price_current'].iloc[0])
        
        # Get Boosted Tree prediction
        boosted_model = BEST_MODELS[horizon]["model"]
        boosted_query = f"""
        SELECT predicted_target_{horizon} as prediction
        FROM ML.PREDICT(
            MODEL `cbi-v14.models.{boosted_model}`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
        )
        """
        boosted_pred = float(client.query(boosted_query).to_dataframe()['prediction'].iloc[0])
        
        # Get Linear baseline prediction
        linear_model = BASELINE_MODELS[horizon]
        linear_query = f"""
        SELECT predicted_target_{horizon} as prediction
        FROM ML.PREDICT(
            MODEL `cbi-v14.models.{linear_model}`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
        )
        """
        linear_pred = float(client.query(linear_query).to_dataframe()['prediction'].iloc[0])
        
        return ComparisonResponse(
            horizon=horizon,
            current_price=round(current_price, 2),
            boosted_tree_prediction=round(boosted_pred, 2),
            linear_baseline_prediction=round(linear_pred, 2),
            difference=round(boosted_pred - linear_pred, 2),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Comparison error for {horizon}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast/all", response_model=List[PredictionResponse])
async def get_all_forecasts():
    """
    Get forecasts for all horizons using the best models
    """
    results = []
    
    for horizon in ["1w", "1m", "3m", "6m"]:
        try:
            forecast = await get_forecast(horizon)
            results.append(forecast)
        except Exception as e:
            logger.error(f"Error getting forecast for {horizon}: {str(e)}")
    
    return results

@router.get("/model-info")
async def get_model_info():
    """
    Get information about all V3 models and their performance
    """
    return {
        "best_models": BEST_MODELS,
        "baseline_models": BASELINE_MODELS,
        "summary": {
            "total_models": 8,
            "model_types": ["Boosted Tree", "Linear"],
            "horizons": ["1w", "1m", "3m", "6m"],
            "best_overall": "zl_boosted_tree_1w_v3",
            "best_mae": 1.72
        },
        "recommendations": {
            "production": "Use Boosted Tree models for all horizons",
            "monitoring": "Compare against Linear baselines to detect anomalies",
            "confidence": {
                "1w": "High (R² = 0.956)",
                "1m": "High (R² = 0.892)",
                "3m": "Good (R² = 0.796)",
                "6m": "Moderate (R² = 0.647)"
            }
        }
    }

@router.get("/health")
async def health_check():
    """
    Check if models are accessible and working
    """
    try:
        # Check if we can access the models
        for horizon, model_info in BEST_MODELS.items():
            model_name = model_info["model"]
            check_query = f"SELECT 1 FROM `cbi-v14.models.INFORMATION_SCHEMA.MODELS` WHERE model_name = '{model_name}'"
            client.query(check_query).result()
        
        return {
            "status": "healthy",
            "models_available": len(BEST_MODELS),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
