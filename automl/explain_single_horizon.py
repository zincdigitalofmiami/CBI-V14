#!/usr/bin/env python3
"""
explain_single_horizon.py

Explain for a single horizon:
- Loads the same 209-col predict frame row you use for predict
- Calls Vertex online explain() via endpoint (model must be deployed)
- Writes top-K attributions into cbi-v14.predictions_uc1.model_feature_importance

Usage: python3 explain_single_horizon.py <horizon> [--endpoint=ENDPOINT_ID]
"""

import os, sys, json, math, datetime as dt, argparse
from google.cloud import aiplatform, bigquery

PROJECT = os.environ.get("PROJECT", "cbi-v14")
REGION  = os.environ.get("GCP_REGION", "us-central1")
PRED_DS = os.environ.get("PRED_DS", "predictions_uc1")
FEAT_TBL = f"{PROJECT}.{PRED_DS}.model_feature_importance"
ENDPOINT_ID = os.environ.get("ENDPOINT_ID", "7286867078038945792")

MODEL_IDS = {
    "1W": "575258986094264320",
    "1M": "274643710967283712",
    "3M": "3157158578716934144",
    "6M": "3788577320223113216",
}

parser = argparse.ArgumentParser(description="Extract feature importance for a horizon")
parser.add_argument("horizon", type=str, help="Horizon (1w, 1m, 3m, 6m)")
parser.add_argument("--endpoint", type=str, default=ENDPOINT_ID, help="Endpoint ID")
args = parser.parse_args()

HORIZ = args.horizon.upper()

if HORIZ not in MODEL_IDS:
    print(f"❌ Invalid horizon: {HORIZ}. Must be one of: {list(MODEL_IDS.keys())}", file=sys.stderr)
    sys.exit(1)

MODEL_ID = MODEL_IDS[HORIZ]

# ---- load predict frame (209-col, correct order) ----
bq = bigquery.Client(project=PROJECT, location=REGION)

# Try to get columns from contract view, fallback to direct table inspection
try:
    contract_sql = """
    SELECT column_name
    FROM `cbi-v14.models_v4._contract_209`
    ORDER BY ordinal_position
    """
    cols = [r[0] for r in bq.query(contract_sql).result()]
except Exception:
    # Fallback: get columns from training_dataset_super_enriched
    schema_sql = """
    SELECT column_name
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'training_dataset_super_enriched'
      AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m')
    ORDER BY ordinal_position
    """
    cols = [r[0] for r in bq.query(schema_sql).result()]

if not cols:
    print("❌ Could not determine column order", file=sys.stderr)
    sys.exit(1)

row_sql = f"""
SELECT {",".join("`"+c+"`" for c in cols)}
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
LIMIT 1
"""

row_df = bq.query(row_sql).to_dataframe()
if row_df.shape[0] != 1:
    print(f"❌ predict-frame empty or multiple rows: {row_df.shape[0]}", file=sys.stderr)
    sys.exit(1)

# Sanitize instance for Vertex AI
instance = {}
for col in cols:
    val = row_df.iloc[0][col]
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        instance[col] = None
    else:
        instance[col] = val

# ---- call online explain() via endpoint ----
aiplatform.init(project=PROJECT, location=REGION)
endpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{PROJECT}/locations/{REGION}/endpoints/{args.endpoint}"
)

# --- ensure endpoint has a deployed model (max 3 minutes) ---
import time

print(f"Checking endpoint {args.endpoint} for deployed models...")
deadline = time.time() + 180  # 3 minutes max wait
while time.time() < deadline:
    ep = endpoint.gca_resource
    if getattr(ep, "deployed_models", None) and len(ep.deployed_models) > 0:
        print(f"  Found {len(ep.deployed_models)} deployed model(s) on endpoint")
        break
    time.sleep(5)
else:
    print("⚠️  No deployed model found on endpoint; skipping explain (non-fatal).", file=sys.stderr)
    sys.exit(0)

# Some AutoML Tabular models return explanations via endpoint.explain()
# If not supported, this will raise. We catch and exit cleanly.
try:
    print(f"Calling explain() for {HORIZ} via endpoint {args.endpoint}...")
    resp = endpoint.explain(instances=[instance], parameters=None)
except Exception as e:
    print(f"⚠️  Explain not supported for {HORIZ}: {e}", file=sys.stderr)
    print(f"   Skipping explain for {HORIZ}. Predictions still written.", file=sys.stderr)
    sys.exit(0)

# resp.predictions[0] → prediction dict
# resp.explanations[0].attributions[0].feature_attributions → {feature: weight}
if not resp.explanations or not resp.explanations[0].attributions:
    print(f"⚠️  No attributions returned for {HORIZ}", file=sys.stderr)
    sys.exit(0)

atts = resp.explanations[0].attributions[0]
feat_attr = atts.feature_attributions or {}

if not feat_attr:
    print(f"⚠️  Empty feature attributions for {HORIZ}", file=sys.stderr)
    sys.exit(0)

# Normalize importance by absolute value, take top-K
K = 15
pairs = [(f, abs(v)) for f, v in feat_attr.items() if v is not None]
pairs.sort(key=lambda x: x[1], reverse=True)
top = pairs[:K]

print(f"  Extracted {len(top)} top features")

# Prepare rows for BQ
prediction_date = dt.date.today()
now_ts = dt.datetime.now(dt.timezone.utc)

# Ensure table exists (idempotent)
schema = [
    bigquery.SchemaField("horizon", "STRING", "REQUIRED"),
    bigquery.SchemaField("prediction_date", "DATE", "REQUIRED"),
    bigquery.SchemaField("feature", "STRING", "REQUIRED"),
    bigquery.SchemaField("importance_abs", "FLOAT64", "REQUIRED"),
    bigquery.SchemaField("raw_contribution", "FLOAT64", "NULLABLE"),
    bigquery.SchemaField("model_id", "STRING", "REQUIRED"),
    bigquery.SchemaField("created_at", "TIMESTAMP", "REQUIRED"),
]

try:
    bq.get_table(FEAT_TBL)
except Exception:
    bq.create_table(bigquery.Table(FEAT_TBL, schema=schema))
    print(f"  Created table: {FEAT_TBL}")

rows = [{
    "horizon": HORIZ,
    "prediction_date": prediction_date,
    "feature": f,
    "importance_abs": float(w) if w is not None else 0.0,
    "raw_contribution": float(feat_attr.get(f)) if feat_attr.get(f) is not None else None,
    "model_id": str(MODEL_ID),
    "created_at": now_ts,
} for f, w in top]

errors = bq.insert_rows_json(FEAT_TBL, rows)
if errors:
    print("❌ BQ insert errors:", errors, file=sys.stderr)
    sys.exit(1)

print(f"✅ {HORIZ}: wrote {len(rows)} feature rows into {FEAT_TBL}")

