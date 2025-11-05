# automl/predict_all_horizons_fixed.py

import json, math, pandas as pd

from google.cloud import bigquery

from google.cloud import aiplatform

PROJECT  = "cbi-v14"
LOCATION = "us-central1"
BQ = bigquery.Client(project=PROJECT, location=LOCATION)

# Vertex model numeric IDs you already confirmed
MODELS = {
    "1W": "575258986094264320",
    "1M": "274643710967283712",
    "3M": "3157158578716934144",
    "6M": "3788577320223113216",
}

# Reuse your clean endpoint (currently with 0 models)
ENDPOINT_ID = "7286867078038945792"
MACHINE     = "n1-standard-2"

def _sanitize_instance(obj):
    # Vertex needs JSON-serializable, no NaN/NaT
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
    
    # Replace NaN with None
    df = df.where(pd.notnull(df), None)
    row = json.loads(df.to_json(orient="records"))[0]
    row = {k: _sanitize_instance(v) for k, v in row.items()}
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
    endpoint.deploy(
        model=model,
        deployed_model_display_name=display_name,
        machine_type=MACHINE,
        min_replica_count=1,
        max_replica_count=1,
        traffic_split={"0": 100},
        sync=True,
    )

    # Predict
    try:
        pred = endpoint.predict(instances=[instance])
        # AutoML Tabular usually returns [{"value": <float>, ...}]
        payload = pred.predictions[0]
        if isinstance(payload, dict) and "value" in payload:
            yhat = float(payload["value"])
        else:
            # Fallback if it's a bare float/list
            yhat = float(payload if isinstance(payload, (int, float)) else payload[0])
    finally:
        # Clean undeploy by locating the deployed model id we just added
        deployed = [m for m in endpoint.list_models() if m.display_name == display_name]
        if deployed:
            endpoint.undeploy(deployed_model_id=deployed[0].id)

    return yhat

def write_prediction(horizon: str, yhat: float):
    # Compute target_date from the predict frame's "date"
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
    print("Loading predict row…")
    row = load_predict_row()
    print("✅ Loaded predict row")

    results = {}
    for hz, mid in MODELS.items():
        print(f"🔮 Predicting {hz} with model {mid} …")
        try:
            yhat = deploy_predict_undeploy(hz, mid, row)
            write_prediction(hz, yhat)
            results[hz] = yhat
            print(f"  ✅ {hz}: {yhat:.4f}")
        except Exception as e:
            results[hz] = None
            print(f"  ❌ {hz} failed: {e}")

    print("\n==================================================")
    print("✅ Processing complete:")
    for hz in ["1W","1M","3M","6M"]:
        print(f"  {hz}: {results[hz]}")

