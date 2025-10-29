#!/usr/bin/env python3
"""
CBI-V14 CLEAN API - ACADEMIC RIGOR ONLY
Removed all bullshit simple math endpoints
Only keeping endpoints with HEAVY FUCKING DATA
"""

import os
import json
import io
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CBI-V14 Market Intelligence API",
    description="Academic-grade soybean oil forecasting with comprehensive intelligence",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# BigQuery client
PROJECT = "cbi-v14"
client = bigquery.Client(project=PROJECT)

# Import ONLY V4 model predictions router (all others DELETED to avoid confusion)
try:
    from v4_model_predictions import router as v4_router
    app.include_router(v4_router, tags=["V4 Enhanced Models"])
    logger.info("V4 model predictions router loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load V4 model predictions router: {e}")

# ============================================================================
# HEALTH CHECK
# ============================================================================
@app.get("/")
async def root():
    return {"message": "CBI-V14 Market Intelligence API", "status": "operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============================================================================
# MARKET INTELLIGENCE (ACADEMIC RIGOR)
# ============================================================================
@app.get("/api/v1/market/intelligence")
async def market_intelligence():
    """Get comprehensive market intelligence with real data"""
    try:
        # Get market intelligence from our comprehensive view
        query = f"""
        SELECT * FROM `{PROJECT}.api.vw_market_intelligence`
        ORDER BY date DESC
        LIMIT 1
        """
        df = client.query(query).to_dataframe()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No market intelligence data found.")
        
        latest_data = df.iloc[0].to_dict()
        
        # Ensure all expected fields are present with safe defaults
        default_values = {
            "zl_price": 0.0,
            "zl_forecast_1week": 0.0,
            "zl_forecast_1month": 0.0,
            "zl_forecast_3month": 0.0,
            "zl_forecast_6month": 0.0,
            "zl_forecast_12month": 0.0,
            "vix_current": 0.0,
            "vix_stress_ratio": 0.0,
            "vix_regime": "NORMAL",
            "palm_soy_spread": 0.0,
            "palm_soy_correlation": 0.0,
            "economic_sentiment": 0.0,
            "geopolitical_risk": 0.0,
            "trading_recommendation": "HOLD",
            "forecast_confidence": "MEDIUM",
            "bullish_probability_pct": 50.0,
            "primary_signal_driver": "N/A"
        }
        
        # Apply defaults and convert numpy types
        for key, default_val in default_values.items():
            if key in latest_data and pd.notna(latest_data[key]):
                if isinstance(latest_data[key], (np.floating, np.integer)):
                    latest_data[key] = default_val.__class__(latest_data[key])
            else:
                latest_data[key] = default_val
        
        return latest_data
    except Exception as e:
        logger.error(f"Error fetching market intelligence: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# ============================================================================
# COMPREHENSIVE SIGNAL UNIVERSE (847+ VARIABLES)
# ============================================================================
@app.get("/api/v1/signals/comprehensive")
async def comprehensive_signals():
    """Get all 847+ signals from comprehensive signal universe"""
    try:
        query = f"""
        SELECT * FROM `{PROJECT}.signals.vw_comprehensive_signal_universe`
        ORDER BY date DESC
        LIMIT 1
        """
        df = client.query(query).to_dataframe()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No comprehensive signal data found.")
        
        return df.to_dict('records')[0]
    except Exception as e:
        logger.error(f"Error fetching comprehensive signals: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# ============================================================================
# MARKET SIGNAL ENGINE (ACADEMIC RIGOR)
# ============================================================================
@app.get("/api/v1/signals/market-engine")
async def market_signal_engine():
    """Get signals from market signal engine with academic rigor"""
    try:
        # Import and use the market signal engine
        from market_signal_engine import MarketSignalEngine
        
        engine = MarketSignalEngine()
        forecast = engine.generate_market_forecast()
        
        return forecast
    except Exception as e:
        logger.error(f"Error running market signal engine: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# ============================================================================
# DATA ENDPOINTS (REAL DATA ONLY)
# ============================================================================
@app.get("/data/prices")
async def get_prices():
    """Get current commodity prices"""
    try:
        query = f"""
        SELECT 
            symbol,
            close as price,
            volume,
            DATE(time) as date
        FROM `{PROJECT}.forecasting_data_warehouse.soybean_oil_prices`
        WHERE DATE(time) = (SELECT MAX(DATE(time)) FROM `{PROJECT}.forecasting_data_warehouse.soybean_oil_prices`)
        """
        df = client.query(query).to_dataframe()
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/features")
async def get_features():
    """Get feature metadata for neural networks"""
    try:
        query = f"""
        SELECT * FROM `{PROJECT}.forecasting_data_warehouse.feature_metadata`
        ORDER BY feature_name
        """
        df = client.query(query).to_dataframe()
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADMIN ENDPOINTS - COMPLETE DATA UPLOAD SYSTEM
# ============================================================================
@app.post("/admin/upload-csv")
async def upload_csv(dataFile: UploadFile = File(...)):
    """Upload CSV data to BigQuery with automatic table detection"""
    if not dataFile.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    try:
        # Read CSV content
        content = await dataFile.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Auto-detect table based on filename
        filename_lower = dataFile.filename.lower()
        table_name = None
        
        # Map filename patterns to BigQuery tables
        if 'crude' in filename_lower or 'oil' in filename_lower or 'brent' in filename_lower or 'wti' in filename_lower:
            table_name = 'crude_oil_prices'
        elif 'soybean' in filename_lower and 'oil' in filename_lower:
            table_name = 'soybean_oil_prices'
        elif 'soybean' in filename_lower and 'oil' not in filename_lower:
            table_name = 'soybean_prices'
        elif 'corn' in filename_lower or 'maize' in filename_lower:
            table_name = 'corn_prices'
        elif 'wheat' in filename_lower:
            table_name = 'wheat_prices'
        elif 'cotton' in filename_lower:
            table_name = 'cotton_prices'
        elif 'rapeseed' in filename_lower:
            table_name = 'rapeseed_oil_prices'
        elif 'canola' in filename_lower:
            table_name = 'canola_oil_prices'
        elif 'palm' in filename_lower:
            table_name = 'palm_oil_prices'
        elif 'vix' in filename_lower:
            table_name = 'vix_daily'
        elif 'treasury' in filename_lower or 'bond' in filename_lower or 'yield' in filename_lower or 'note' in filename_lower or '10' in filename_lower or 'year' in filename_lower:
            table_name = 'treasury_prices'
        elif 'social' in filename_lower or 'sentiment' in filename_lower:
            table_name = 'social_sentiment'
        elif 'volatility' in filename_lower:
            table_name = 'volatility_data'
        else:
            raise HTTPException(status_code=400, detail=f"Cannot auto-detect table for filename: {dataFile.filename}. Supported keywords: crude, oil, brent, wti, soybean, corn, wheat, cotton, rapeseed, canola, palm, vix, treasury, bond, yield, note, 10, year, social, sentiment, volatility")
        
        # Standardize the dataframe
        df_standardized = standardize_price_dataframe(df, table_name)
        
        # Load to BigQuery
        table_id = f"{PROJECT}.forecasting_data_warehouse.{table_name}"
        
        # Get the actual table schema to match
        table_ref = client.get_table(table_id)
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            schema=table_ref.schema
        )
        
        job = client.load_table_from_dataframe(df_standardized, table_id, job_config=job_config)
        job.result()
        
        return {
            "message": "CSV uploaded successfully", 
            "filename": dataFile.filename,
            "table": table_name,
            "rows_loaded": len(df_standardized)
        }
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/upload")
async def upload_zip(dataFile: UploadFile = File(...)):
    """Upload ZIP archive with multiple CSV files"""
    if not dataFile.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")
    
    try:
        import zipfile
        import io
        
        # Read ZIP content
        content = await dataFile.read()
        
        results = []
        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
            for filename in zip_file.namelist():
                if filename.endswith('.csv'):
                    # Process each CSV in the ZIP
                    csv_content = zip_file.read(filename)
                    df = pd.read_csv(io.StringIO(csv_content.decode('utf-8')))
                    
                    # Auto-detect table
                    table_name = auto_detect_table_name(filename)
                    if table_name:
                        df_standardized = standardize_price_dataframe(df, table_name)
                        
                        # Load to BigQuery
                        table_id = f"{PROJECT}.forecasting_data_warehouse.{table_name}"
                        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
                        job = client.load_table_from_dataframe(df_standardized, table_id, job_config=job_config)
                        job.result()
                        
                        results.append({
                            "filename": filename,
                            "table": table_name,
                            "rows_loaded": len(df_standardized)
                        })
        
        return {
            "message": "ZIP uploaded successfully",
            "files_processed": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error uploading ZIP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def standardize_price_dataframe(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Standardize dataframe to match BigQuery schema"""
    # Create standardized dataframe
    result_df = pd.DataFrame()
    
    # Get the target table schema to determine column names
    table_id = f"{PROJECT}.forecasting_data_warehouse.{table_name}"
    table_ref = client.get_table(table_id)
    table_schema = {field.name: field.field_type for field in table_ref.schema}
    
    # Determine if we need date or time column
    needs_date = 'date' in table_schema
    needs_time = 'time' in table_schema
    
    # Time/Date column - try different common names
    time_col = None
    for col in ['time', 'Time', 'date', 'Date', 'timestamp']:
        if col in df.columns:
            time_col = col
            break
    
    if time_col:
        # Filter out footer lines that don't match date format
        df_clean = df[df[time_col].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}', na=False)]
        if len(df_clean) > 0:
            if needs_date:
                result_df['date'] = pd.to_datetime(df_clean[time_col]).dt.date.astype(str)
            if needs_time:
                result_df['time'] = pd.to_datetime(df_clean[time_col])
            df_to_use = df_clean  # Use cleaned dataframe for price columns
        else:
            if needs_date:
                result_df['date'] = pd.Timestamp.now().date().strftime('%Y-%m-%d')
            if needs_time:
                result_df['time'] = pd.Timestamp.now()
            df_to_use = df  # Fallback to original dataframe
    else:
        if needs_date:
            result_df['date'] = pd.Timestamp.now().date().strftime('%Y-%m-%d')
        if needs_time:
            result_df['time'] = pd.Timestamp.now()
        df_to_use = df
    
    # Price columns - determine if we need _price suffix
    needs_price_suffix = any('_price' in col for col in table_schema.keys())
    
    price_mapping = {
        'open': ['open', 'Open', 'OPEN'],
        'high': ['high', 'High', 'HIGH'],
        'low': ['low', 'Low', 'LOW'],
        'close': ['close', 'Close', 'CLOSE', 'last', 'Last', 'LAST', 'price', 'Price']
    }
    
    for target_col, possible_cols in price_mapping.items():
        found_col = None
        for col in possible_cols:
            if col in df_to_use.columns:
                found_col = col
                break
        
        if found_col:
            price_value = pd.to_numeric(df_to_use[found_col], errors='coerce')
            if needs_price_suffix:
                result_df[f'{target_col}_price'] = price_value
            else:
                result_df[target_col] = price_value
        else:
            if needs_price_suffix:
                result_df[f'{target_col}_price'] = None
            else:
                result_df[target_col] = None
    
    # Volume column
    volume_col = None
    for col in ['volume', 'Volume', 'VOLUME']:
        if col in df_to_use.columns:
            volume_col = col
            break
    
    if volume_col:
        result_df['volume'] = pd.to_numeric(df_to_use[volume_col], errors='coerce').astype('Int64')
    else:
        result_df['volume'] = None
    
    # Metadata columns
    result_df['symbol'] = table_name.upper().replace('_prices', '').replace('_daily', '')
    result_df['source_name'] = 'Admin_Upload'
    result_df['confidence_score'] = 1.0
    result_df['ingest_timestamp_utc'] = datetime.utcnow()
    result_df['provenance_uuid'] = f"admin_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Ensure all required columns are present with correct types
    for field in table_ref.schema:
        if field.name not in result_df.columns:
            if field.field_type == 'STRING':
                result_df[field.name] = ''
            elif field.field_type in ['FLOAT64', 'FLOAT']:
                result_df[field.name] = 0.0
            elif field.field_type in ['INT64', 'INTEGER']:
                result_df[field.name] = 0
            elif field.field_type == 'DATE':
                result_df[field.name] = pd.Timestamp.now().date().strftime('%Y-%m-%d')
            elif field.field_type == 'TIMESTAMP':
                result_df[field.name] = pd.Timestamp.now()
    
    # Reorder columns to match schema
    result_df = result_df[[field.name for field in table_ref.schema]]
    
    return result_df

def auto_detect_table_name(filename: str) -> str:
    """Auto-detect BigQuery table name from filename"""
    filename_lower = filename.lower()
    
    if 'crude' in filename_lower or 'oil' in filename_lower or 'brent' in filename_lower or 'wti' in filename_lower:
        return 'crude_oil_prices'
    elif 'soybean' in filename_lower and 'oil' in filename_lower:
        return 'soybean_oil_prices'
    elif 'soybean' in filename_lower and 'oil' not in filename_lower:
        return 'soybean_prices'
    elif 'corn' in filename_lower or 'maize' in filename_lower:
        return 'corn_prices'
    elif 'wheat' in filename_lower:
        return 'wheat_prices'
    elif 'cotton' in filename_lower:
        return 'cotton_prices'
    elif 'rapeseed' in filename_lower:
        return 'rapeseed_oil_prices'
    elif 'canola' in filename_lower:
        return 'canola_oil_prices'
    elif 'palm' in filename_lower:
        return 'palm_oil_prices'
    elif 'vix' in filename_lower:
        return 'vix_daily'
    elif 'treasury' in filename_lower or 'bond' in filename_lower or 'yield' in filename_lower or 'note' in filename_lower or '10' in filename_lower or 'year' in filename_lower:
        return 'treasury_prices'
    elif 'social' in filename_lower or 'sentiment' in filename_lower:
        return 'social_sentiment'
    elif 'volatility' in filename_lower:
        return 'volatility_data'
    else:
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
