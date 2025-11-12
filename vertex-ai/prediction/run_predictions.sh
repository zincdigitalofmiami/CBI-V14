#!/bin/bash
# =========================
# STRICT SINGLE-FLIGHT PREDICT PIPELINE
# =========================

set -euo pipefail

# --- normalize/validate horizon arg ---
HORIZ_RAW="${1:-}"
if [[ -z "$HORIZ_RAW" ]]; then 
  echo "Usage: run_all_predictions_safe.sh <1W|1M|3M|6M>"
  exit 2
fi

HORIZ="$(echo "$HORIZ_RAW" | tr '[:lower:]' '[:upper:]')"
case "$HORIZ" in 
  1W|1M|3M|6M) 
    ;;
  *) 
    echo "Invalid horizon: $HORIZ"
    exit 2
    ;;
esac
LABEL="$HORIZ"

PROJECT="cbi-v14"
REGION="us-central1"
EP="7286867078038945792"
BQ_DATASET="predictions_uc1"
BQ_TABLE="monthly_vertex_predictions"
BQ_LOCATION="us-central1"

MODEL_1W="575258986094264320"
MODEL_1M="274643710967283712"
MODEL_3M="3157158578716934144"
MODEL_6M="3788577320223113216"

ensure_endpoint_idle() {
  # wait until: no pending ops on this endpoint (but allow deployed models to exist)
  echo ">> checking endpoint for pending operations..."
  TOKEN=$(gcloud auth print-access-token 2>/dev/null || echo "")
  if [[ -n "$TOKEN" ]]; then
    OPS=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJECT/locations/$REGION/operations?filter=metadata.target:%22projects/$PROJECT/locations/$REGION/endpoints/$EP%22%20AND%20done:false" \
      2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("operations",[])))' 2>/dev/null || echo "0")
    if [[ "$OPS" == "0" ]]; then
      echo ">> endpoint has no pending operations"
      return 0
    fi
    echo ">> waiting for $OPS pending operation(s) to complete..."
    sleep 10
  else
    echo ">> skipped operation check (no auth token)"
  fi
}

deploy_wait() {
  local MODEL_ID="$1"
  local DISPLAY="$2"
  
  # If a model is already deployed, skip redeploy
  ALREADY="$(gcloud ai endpoints describe "$EP" --region="$REGION" \
            --format='value(deployedModels[].id)' 2>&1 | grep -E '^[0-9]+$' | head -n1)"
  if [[ -n "$ALREADY" ]]; then
    echo ">> endpoint already has a deployed model (id=$ALREADY); skipping deploy step"
    return 0
  fi
  
  # start deploy
  echo "   - deploying model $MODEL_ID..."
  gcloud ai endpoints deploy-model "$EP" --region="$REGION" \
      --model="$MODEL_ID" \
      --display-name="$DISPLAY" \
      --machine-type="n1-standard-2" \
      --min-replica-count=1 --max-replica-count=1 \
      --quiet 2>&1 || {
    echo "ERROR: Deploy command failed"
    return 1
  }
  
  # verify deploy succeeded (idempotent)
  sleep 5  # brief wait for endpoint state to update
  DMID="$(gcloud ai endpoints describe "$EP" --region="$REGION" \
          --format='value(deployedModels[].id)' 2>&1 | grep -E '^[0-9]+$' | head -n1)"
  if [[ -n "$DMID" ]]; then
    echo "   - deploy OK (deployed_model_id=$DMID)"
  else
    echo "ERROR: no deployed model found on endpoint after deploy"
    return 1
  fi
}

undeploy_all() {
  # Only undeploy temporary models created by this script
  local ids
  ids=$(gcloud ai endpoints describe "$EP" --region="$REGION" \
        --format='value(deployedModels[?starts_with(displayName,"temp_")].id)' 2>&1 | grep -E '^[0-9]+$' || echo "")
  if [[ -n "$ids" ]]; then
    for id in $ids; do
      echo "   - undeploying temp model $id"
      gcloud ai endpoints undeploy-model "$EP" --region="$REGION" \
        --deployed-model-id="$id" --quiet 2>&1 || true
    done
  else
    echo "   - no temp_* models to undeploy"
  fi
}

verify_bq_row() {
  local H=$1
  bq --location="$BQ_LOCATION" query --use_legacy_sql=false --format=prettyjson \
"SELECT horizon, prediction_date, target_date, predicted_price, model_name, created_at
   FROM \`$PROJECT.$BQ_DATASET.$BQ_TABLE\`
  WHERE horizon=UPPER('$H')
  ORDER BY created_at DESC
  LIMIT 1" 2>&1 | head -20
}

run_horizon() {
  local H="$1"
  local MID="$2"
  # H and LABEL are already normalized to uppercase at script start

  echo ""
  echo "================== ${LABEL} =================="

  ensure_endpoint_idle  # Only check for pending ops, don't undeploy existing models
  echo ">> deploy ${LABEL}…"
  deploy_wait "$MID" "temp_${H}_$(date +%H%M%S)"

  echo ">> predict ${LABEL}…"
  python3 automl/predict_single_horizon.py "$H"

  echo ">> verify BigQuery write (${LABEL})…"
  verify_bq_row "$H"

  echo ">> explain ${LABEL}…"
  python3 automl/explain_single_horizon.py "$H" --endpoint="$EP" || true
  # (non-fatal: if explanations unsupported, we still finish predictions)

  echo ">> undeploy ${LABEL}…"
  undeploy_all  # Only undeploys temp_* models
  ensure_endpoint_idle  # Verify undeploy completed
  echo "============= ${LABEL} DONE ============="
}

# preflight: table exists and region is correct
echo "Project: $(gcloud config get-value project) | Region: $REGION | Endpoint: $EP"
echo "Processing horizon: $LABEL"
if ! bq --location="$BQ_LOCATION" show "$PROJECT:$BQ_DATASET.$BQ_TABLE" >/dev/null 2>&1; then
  echo "ERROR: BigQuery table $PROJECT.$BQ_DATASET.$BQ_TABLE not found in $BQ_LOCATION"
  exit 1
fi
echo ">> BigQuery table verified: $PROJECT.$BQ_DATASET.$BQ_TABLE"

# Run single horizon (as specified by command-line arg)
MODEL_ID=""
case "$LABEL" in
  1W) MODEL_ID="$MODEL_1W" ;;
  1M) MODEL_ID="$MODEL_1M" ;;
  3M) MODEL_ID="$MODEL_3M" ;;
  6M) MODEL_ID="$MODEL_6M" ;;
esac

if [[ -z "$MODEL_ID" ]]; then
  echo "ERROR: No model ID found for horizon $LABEL"
  exit 1
fi

run_horizon "$HORIZ" "$MODEL_ID"

echo ""
echo "Horizon $LABEL processed. Summary:"
bq --location="$BQ_LOCATION" query --use_legacy_sql=false \
"SELECT horizon, prediction_date, target_date, predicted_price, model_name, created_at
 FROM \`$PROJECT.$BQ_DATASET.$BQ_TABLE\`
 WHERE horizon='$LABEL'
 ORDER BY created_at DESC
 LIMIT 1"
