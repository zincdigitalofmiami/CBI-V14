#!/usr/bin/env python3
"""
export_feature_importance.py
Export Vertex Model feature importance to BigQuery
Uses Vertex AI Python SDK to get model explanations
"""

import os, datetime, subprocess
import requests
from google.cloud import bigquery

PROJECT = os.getenv("PROJECT", "cbi-v14")
REGION  = os.getenv("REGION", "us-central1")
DATASET = os.getenv("DATASET", "predictions_uc1")
TABLE   = os.getenv("TABLE", "model_feature_importance")

MODEL_IDS = {
    "1W": "575258986094264320",
    "1M": "274643710967283712",
    "3M": "3157158578716934144",
    "6M": "3788577320223113216",
}

def ensure_table():
    client = bigquery.Client(project=PROJECT, location="us-central1")
    schema = [
        bigquery.SchemaField("horizon", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("prediction_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("feature", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("importance_abs", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("raw_contribution", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("model_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    table_ref = bigquery.Table(f"{PROJECT}.{DATASET}.{TABLE}", schema=schema)
    try:
        client.create_table(table_ref, exists_ok=True)
        print(f"✅ Table ensured: {PROJECT}.{DATASET}.{TABLE}")
    except Exception as e:
        print(f"Note: Table creation: {e}")
    return client

def get_model_feature_importance(model_id):
    """Get feature importance from Vertex AI model evaluations via REST API"""
    import requests
    
    TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
    
    # Use REST API to list evaluations
    url = f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{REGION}/models/{model_id}/evaluations"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"  API returned {response.status_code}: {response.text[:200]}")
            return {}
        
        evals = response.json().get("evaluations", [])
        if not evals:
            print(f"  No evaluations found for model {model_id}")
            return {}
        
        print(f"  Found {len(evals)} evaluations")
        agg = {}
        
        # Get feature attributions from each evaluation
        for eval_data in evals:
            eval_name = eval_data.get("name", "")
            if not eval_name:
                continue
            
            # Get full evaluation details
            eval_url = f"https://{REGION}-aiplatform.googleapis.com/v1/{eval_name}"
            eval_response = requests.get(eval_url, headers=headers, timeout=30)
            if eval_response.status_code == 200:
                eval_detail = eval_response.json()
                feats = extract_from_evaluation_response(eval_detail)
                if feats:
                    print(f"    Extracted {len(feats)} features from {eval_name}")
                    for f, p in feats.items():
                        agg[f] = max(agg.get(f, 0.0), p)
        
        return agg
        
    except Exception as e:
        print(f"  Error accessing evaluations: {e}")
        return {}

def extract_from_evaluation_response(eval_data):
    """Extract feature importance from evaluation response"""
    feats = {}
    if isinstance(eval_data, dict):
        mats = eval_data.get("modelExplanation", {}).get("meanAttributions", [])
        for ma in mats:
            fa = ma.get("featureAttributions", {})
            vals = [abs(v) for v in fa.values() if isinstance(v, (int, float))]
            denom = sum(vals) or 1.0
            for k, v in fa.items():
                if isinstance(v, (int, float)):
                    pct = abs(v) / denom * 100.0
                    feats[k] = max(feats.get(k, 0.0), pct)
    return feats

def main():
    client = ensure_table()
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []

    for horizon, mid in MODEL_IDS.items():
        print(f"\nProcessing {horizon} (model {mid})...")
        try:
            # Try to get feature importance from model
            feats = get_model_feature_importance(mid)
            
            if not feats:
                print(f"  ⚠️  No feature importance data available for {horizon}")
                print(f"     Feature importance requires model evaluations with explanations enabled")
                print(f"     This will be populated when evaluations are run")
                continue

            if feats:
                print(f"  Found {len(feats)} features")
                for f, p in sorted(feats.items(), key=lambda kv: -kv[1]):
                    rows.append({
                        "model_id": mid,
                        "horizon": horizon,
                        "feature": f,
                        "importance_pct": round(float(p), 6),
                        "computed_at": ts
                    })
        except Exception as ex:
            print(f"[WARN] {horizon}/{mid}: {ex}")
            import traceback
            traceback.print_exc()

    if rows:
        print(f"\nInserting {len(rows)} rows into {PROJECT}.{DATASET}.{TABLE}...")
        job = client.load_table_from_json(
            rows, f"{PROJECT}.{DATASET}.{TABLE}",
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"))
        job.result()
        print(f"✅ Inserted {len(rows)} rows")
    else:
        print("\n⚠️  No rows written.")
        print("   Feature importance data will be available after:")
        print("   1. Model evaluations are run with explanations enabled")
        print("   2. Evaluation results contain modelExplanation.meanAttributions")

if __name__ == "__main__":
    main()

