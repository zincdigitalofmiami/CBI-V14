#!/usr/bin/env python3
"""
predict_single_horizon.py
Generate prediction for a single horizon (deploy → predict → undeploy)
"""

import json, math, pandas as pd, sys
from google.cloud import bigquery, aiplatform

PROJECT  = "cbi-v14"
LOCATION = "us-central1"
BQ = bigquery.Client(project=PROJECT, location=LOCATION)

MODELS = {
    "1W": "575258986094264320",
    "1M": "274643710967283712",
    "3M": "3157158578716934144",
    "6M": "3788577320223113216",
}

ENDPOINT_ID = "7286867078038945792"
MACHINE = "n1-standard-2"

def _sanitize_instance(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if obj is None:
        return None
    return obj

def load_predict_row():
    df = BQ.query("""
        SELECT * FROM `cbi-v14.models_v4.predict_frame_209` LIMIT 1
    """).to_dataframe()
    
    if df.empty:
        raise RuntimeError("predict_frame_209 is empty.")
    
    df = df.where(pd.notnull(df), None)
    row = json.loads(df.to_json(orient="records"))[0]
    row = {k: _sanitize_instance(v) for k, v in row.items()}
    
    # Validate targets are not NULL
    for target in ['target_1w', 'target_1m', 'target_3m', 'target_6m']:
        if row.get(target) is None:
            raise ValueError(f"{target} is NULL in predict_frame_209")
    
    return row

def deploy_predict_undeploy(horizon: str, model_id: str, instance: dict) -> float:
    aiplatform.init(project=PROJECT, location=LOCATION)
    endpoint = aiplatform.Endpoint(
        endpoint_name=f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )

    # Build full resource name for the Model
    model = aiplatform.Model(
        model_name=f"projects/{PROJECT}/locations/{LOCATION}/models/{model_id}"
    )

    display_name = f"temp_{horizon}_{model_id[-6:]}"
    
    # Deploy
    print(f"  📦 Deploying {horizon}...")
    endpoint.deploy(
        model=model,
        deployed_model_display_name=display_name,
        machine_type=MACHINE,
        min_replica_count=1,
        max_replica_count=1,
        traffic_split={"0": 100},
        sync=True,
    )
    print(f"  ✅ Deployed")

    # Predict
    try:
        print(f"  🔮 Predicting...")
        pred = endpoint.predict(instances=[instance])
        payload = pred.predictions[0]
        if isinstance(payload, dict) and "value" in payload:
            yhat = float(payload["value"])
        else:
            yhat = float(payload if isinstance(payload, (int, float)) else payload[0])
        print(f"  ✅ Prediction: {yhat:.4f}")
    finally:
        # Clean undeploy
        print(f"  🧹 Undeploying...")
        deployed = [m for m in endpoint.list_models() if m.display_name == display_name]
        if deployed:
            endpoint.undeploy(deployed_model_id=deployed[0].id)
        print(f"  ✅ Undeployed")

    return yhat

def write_prediction(horizon: str, yhat: float):
    BQ.query("""
        INSERT INTO `cbi-v14.predictions_uc1.monthly_vertex_predictions`
        (horizon, prediction_date, target_date, predicted_price,
         confidence_lower, confidence_upper, mape, model_id, model_name, created_at)
        SELECT
          @hz,
          CURRENT_DATE(),
          DATE_ADD((SELECT date FROM `cbi-v14.models_v4.predict_frame_209` LIMIT 1),
                   INTERVAL CASE @hz WHEN '1W' THEN 7 WHEN '1M' THEN 30 WHEN '3M' THEN 90 WHEN '6M' THEN 180 END DAY),
          @yhat,
          NULL, NULL, NULL,
          @mid,
          CONCAT('vertex_automl_', LOWER(@hz)),
          CURRENT_TIMESTAMP()
    """, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("hz", "STRING", horizon),
            bigquery.ScalarQueryParameter("yhat", "FLOAT64", yhat),
            bigquery.ScalarQueryParameter("mid", "STRING", MODELS[horizon]),
        ]
    )).result()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 predict_single_horizon.py <HORIZON>")
        print("  HORIZON: 1W, 1M, 3M, or 6M")
        sys.exit(1)
    
    horizon = sys.argv[1].upper()
    if horizon not in MODELS:
        print(f"Error: Invalid horizon {horizon}. Must be one of: {list(MODELS.keys())}")
        sys.exit(1)
    
    model_id = MODELS[horizon]
    
    print(f"🔮 Predicting {horizon} with model {model_id}")
    print("Loading predict row…")
    row = load_predict_row()
    print("✅ Loaded predict row")
    
    try:
        yhat = deploy_predict_undeploy(horizon, model_id, row)
        write_prediction(horizon, yhat)
        print(f"✅ Written to BigQuery: {yhat:.4f}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

