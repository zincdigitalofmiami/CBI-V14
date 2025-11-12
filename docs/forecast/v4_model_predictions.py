"""
V4 Model Predictions API - Enhanced Forecasting with Model Selection
Complete isolation from V3 endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from google.cloud import bigquery
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize BigQuery client
client = bigquery.Client(project="cbi-v14")

# Create router with V4 prefix
router = APIRouter(prefix="/api/v4", tags=["V4 Enhanced Models"])

# Model registry - will be populated as models complete training
AVAILABLE_MODELS = {
    "1w": {
        "boosted_v3": "cbi-v14.models.zl_boosted_tree_1w_v3",  # Fallback to proven V3
        "dnn_v4": "cbi-v14.models_v4.zl_dnn_1w_v4",
        #"arima_v4": "cbi-v14.models_v4.zl_arima_1w_v4",  # DELETED - failed model
        #"automl_v4": "cbi-v14.models_v4.zl_automl_1w_v4",  # Will be available after training
    },
    "1m": {
        "boosted_v3": "cbi-v14.models.zl_boosted_tree_1m_v3",
        "dnn_v4": "cbi-v14.models_v4.zl_dnn_1m_v4",
        #"arima_v4": "cbi-v14.models_v4.zl_arima_1m_v4",  # DELETED - failed model
        #"automl_v4": "cbi-v14.models_v4.zl_automl_1m_v4",
    },
    "3m": {
        "boosted_v3": "cbi-v14.models.zl_boosted_tree_3m_v3",
        "dnn_v3": "cbi-v14.models.zl_dnn_3m_production",  # V3 DNN actually works for 3m/6m
        #"arima_v4": "cbi-v14.models_v4.zl_arima_3m_v4",  # DELETED - failed model
        #"automl_v4": "cbi-v14.models_v4.zl_automl_3m_v4",
    },
    "6m": {
        "boosted_v3": "cbi-v14.models.zl_boosted_tree_6m_v3",
        "dnn_v3": "cbi-v14.models.zl_dnn_6m_production",
        #"arima_v4": "cbi-v14.models_v4.zl_arima_6m_v4",  # DELETED - failed model
        #"automl_v4": "cbi-v14.models_v4.zl_automl_6m_v4",
    }
}

class ForecastResponse(BaseModel):
    horizon: str
    model_type: str
    model_name: str
    prediction: float
    current_price: float
    predicted_change: float
    predicted_change_pct: float
    confidence_metrics: Optional[Dict[str, float]] = None
    timestamp: str

class ForwardCurvePoint(BaseModel):
    day_number: int
    target_date: str
    forward_price: float
    days_from_now: int

class ModelComparisonResponse(BaseModel):
    horizon: str
    current_price: float
    models: Dict[str, Dict]
    timestamp: str

@router.get("/forecast/{horizon}", response_model=ForecastResponse)
async def get_v4_forecast(
    horizon: str,
    model_type: str = Query("boosted_v3", description="Model type: boosted_v3, dnn_v4, arima_v4, automl_v4, ensemble_v4")
):
    """
    Get V4 forecast with model selection
    
    **CRITICAL:** V3 models remain default and untouched
    
    **Available Models:**
    - `boosted_v3`: Production V3 Boosted Tree (default, proven)
    - `dnn_v4`: Fixed DNN with normalization (1w, 1m only)
    - `automl_v4`: AutoML model (available after training completes)
    - `ensemble_v4`: Weighted ensemble (available after AutoML completes)
    
    Note: `arima_v4` models were deleted (failed training)
    """
    if horizon not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid horizon '{horizon}'. Choose from: {list(AVAILABLE_MODELS.keys())}"
        )
    
    if model_type not in AVAILABLE_MODELS[horizon]:
        available = list(AVAILABLE_MODELS[horizon].keys())
        raise HTTPException(
            status_code=400,
            detail=f"Model type '{model_type}' not available for horizon '{horizon}'. Available: {available}"
        )
    
    model_path = AVAILABLE_MODELS[horizon][model_type]
    
    try:
        # Get current price
        current_price_query = """
        SELECT zl_price_current
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
        """
        current_price = float(client.query(current_price_query).to_dataframe()['zl_price_current'].iloc[0])
        
        # Make prediction
        target_col = f"target_{horizon}"
        predict_query = f"""
        SELECT predicted_{target_col} as prediction
        FROM ML.PREDICT(
            MODEL `{model_path}`,
            (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
        )
        """
        
        prediction = float(client.query(predict_query).to_dataframe()['prediction'].iloc[0])
        
        change = prediction - current_price
        change_pct = (change / current_price) * 100
        
        # Try to get confidence metrics (not available for ARIMA)
        confidence_metrics = None
        try:
            eval_query = f"""
            SELECT mean_absolute_error, r2_score
            FROM ML.EVALUATE(MODEL `{model_path}`)
            LIMIT 1
            """
            eval_df = client.query(eval_query).to_dataframe()
            confidence_metrics = {
                "mae": float(eval_df['mean_absolute_error'].iloc[0]),
                "r2": float(eval_df['r2_score'].iloc[0]),
                "mape_percent": (float(eval_df['mean_absolute_error'].iloc[0]) / 50.0) * 100
            }
        except:
            logger.info(f"Confidence metrics not available for {model_path}")
        
        return ForecastResponse(
            horizon=horizon,
            model_type=model_type,
            model_name=model_path.split('.')[-1],
            prediction=round(prediction, 2),
            current_price=round(current_price, 2),
            predicted_change=round(change, 2),
            predicted_change_pct=round(change_pct, 2),
            confidence_metrics=confidence_metrics,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"V4 forecast error for {horizon}/{model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forward-curve", response_model=List[ForwardCurvePoint])
async def get_forward_curve(days: int = Query(180, ge=0, le=180)):
    """
    Get continuous forward curve with daily price forecasts
    
    **Returns:** Linear interpolation between V3 model forecasts (0-180 days)
    """
    try:
        query = f"""
        SELECT 
            day_number,
            CAST(target_date AS STRING) as target_date,
            forward_price,
            days_from_now
        FROM `cbi-v14.models_v4.forward_curve_v3`
        WHERE day_number <= {days}
        ORDER BY day_number
        """
        
        df = client.query(query).to_dataframe()
        
        return [
            ForwardCurvePoint(
                day_number=int(row['day_number']),
                target_date=row['target_date'],
                forward_price=float(row['forward_price']),
                days_from_now=int(row['days_from_now'])
            )
            for _, row in df.iterrows()
        ]
        
    except Exception as e:
        logger.error(f"Forward curve error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-comparison/{horizon}", response_model=ModelComparisonResponse)
async def compare_models(horizon: str):
    """
    Compare all available models for a given horizon
    
    **Returns:** Predictions from all available model types
    """
    if horizon not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid horizon. Choose from: {list(AVAILABLE_MODELS.keys())}"
        )
    
    try:
        # Get current price
        current_price_query = """
        SELECT zl_price_current
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
        """
        current_price = float(client.query(current_price_query).to_dataframe()['zl_price_current'].iloc[0])
        
        models_results = {}
        
        for model_type, model_path in AVAILABLE_MODELS[horizon].items():
            try:
                forecast = await get_v4_forecast(horizon, model_type)
                models_results[model_type] = {
                    "prediction": forecast.prediction,
                    "change_pct": forecast.predicted_change_pct,
                    "confidence": forecast.confidence_metrics
                }
            except Exception as e:
                logger.warning(f"Could not get forecast for {model_type}: {str(e)}")
                models_results[model_type] = {"error": str(e)}
        
        return ModelComparisonResponse(
            horizon=horizon,
            current_price=current_price,
            models=models_results,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Model comparison error for {horizon}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def v4_health_check():
    """
    Check V4 API health and model availability
    """
    try:
        # Count available models
        total_models = sum(len(models) for models in AVAILABLE_MODELS.values())
        
        # Check if forward curve exists
        curve_check = """
        SELECT COUNT(*) as count
        FROM `cbi-v14.models_v4.forward_curve_v3`
        """
        curve_count = int(client.query(curve_check).to_dataframe()['count'].iloc[0])
        
        return {
            "status": "healthy",
            "version": "v4",
            "available_horizons": list(AVAILABLE_MODELS.keys()),
            "total_model_configurations": total_models,
            "forward_curve_points": curve_count,
            "automl_status": "training" if "automl_v4" not in AVAILABLE_MODELS["1w"] else "available",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/model-registry")
async def get_model_registry():
    """
    Get complete V4 model registry with availability status
    """
    return {
        "v4_models": AVAILABLE_MODELS,
        "notes": {
            "automl_status": "Training in background (~4 hours remaining)",
            "ensemble_status": "Pending AutoML completion",
            "v3_fallback": "All endpoints default to proven V3 Boosted Tree models"
        },
        "performance_targets": {
            "mape_goal": "< 2.0%",
            "v3_baseline": {"1w": "3.4%", "1m": "5.6%", "3m": "7.4%", "6m": "8.2%"}
        }
    }

