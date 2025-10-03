#!/usr/bin/env bash
set -euo pipefail
OUTFILE="${HOME}/inventory_step1_output.txt"
echo "=== START INVENTORY $(date -u) ===" > "${OUTFILE}"

echo -e "\n# PROJECT (gcloud config)" | tee -a "${OUTFILE}"
gcloud config get-value project 2>&1 | tee -a "${OUTFILE}"

PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [[ -z "${PROJECT}" || "${PROJECT}" == "unset" ]]; then
  echo "ERROR: gcloud project not set. Run: gcloud config set project <PROJECT_ID>" | tee -a "${OUTFILE}"
  exit 1
fi
echo -e "\n# PROJECT DESCRIPTION" | tee -a "${OUTFILE}"
gcloud projects describe "${PROJECT}" --format=json 2>&1 | tee -a "${OUTFILE}"

echo -e "\n# GSUTIL - list accessible buckets (may include buckets in other projects you can access)" | tee -a "${OUTFILE}"
gsutil ls 2>&1 | tee -a "${OUTFILE}"

echo -e "\n# BIGQUERY - datasets and sample tables" | tee -a "${OUTFILE}"
bq --project_id="${PROJECT}" ls --max_results=1000 2>&1 | tee -a "${OUTFILE}"
# list tables for each dataset (if any)
datasets=$(bq --project_id="${PROJECT}" ls --format=prettyjson | jq -r '.[].datasetReference.datasetId' 2>/dev/null || true)
if [[ -n "${datasets}" ]]; then
  for d in ${datasets}; do
    echo -e "\n## TABLES in dataset ${d}" | tee -a "${OUTFILE}"
    bq --project_id="${PROJECT}" ls --format=prettyjson "${PROJECT}:${d}" 2>&1 | tee -a "${OUTFILE}"
  done
fi

echo -e "\n# ENABLED APIS / SERVICES" | tee -a "${OUTFILE}"
gcloud services list --enabled --project="${PROJECT}" --format="table[box](config.name,config.title)" 2>&1 | tee -a "${OUTFILE}"

echo -e "\n# CLOUD RUN SERVICES (managed) - all regions" | tee -a "${OUTFILE}"
gcloud run services list --platform=managed --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# CLOUD FUNCTIONS" | tee -a "${OUTFILE}"
gcloud functions list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# DATAFLOW JOBS (recent)" | tee -a "${OUTFILE}"
gcloud dataflow jobs list --project="${PROJECT}" --limit=50 --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# CLOUD COMPOSER ENVS" | tee -a "${OUTFILE}"
gcloud composer environments list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# PUBSUB TOPICS" | tee -a "${OUTFILE}"
gcloud pubsub topics list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# ARTIFACT REGISTRY REPOS" | tee -a "${OUTFILE}"
gcloud artifacts repositories list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# VERTEX/AI - datasets and models (if gcloud ai components available)" | tee -a "${OUTFILE}"
gcloud ai datasets list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}" || echo "gcloud ai datasets list failed or not enabled; ignoring" | tee -a "${OUTFILE}"
gcloud ai models list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}" || echo "gcloud ai models list failed or not enabled; ignoring" | tee -a "${OUTFILE}"

echo -e "\n# SERVICE ACCOUNTS" | tee -a "${OUTFILE}"
gcloud iam service-accounts list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# IAM POLICY (project bindings)" | tee -a "${OUTFILE}"
gcloud projects get-iam-policy "${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# COMPUTE INSTANCES" | tee -a "${OUTFILE}"
gcloud compute instances list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# GKE CLUSTERS" | tee -a "${OUTFILE}"
gcloud container clusters list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUTFILE}"

echo -e "\n# NOTE: If some commands failed due to missing APIs or permissions, you'll see errors above." | tee -a "${OUTFILE}"

echo -e "\n=== END INVENTORY $(date -u) ===" | tee -a "${OUTFILE}"

echo -e "\nInventory complete. Output saved to: ${OUTFILE}"
