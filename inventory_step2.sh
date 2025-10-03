#!/usr/bin/env bash
set -euo pipefail
OUT="${HOME}/inventory_step2_output.txt"
echo "=== START PIPELINE INVENTORY $(date -u) ===" > "${OUT}"

PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [[ -z "${PROJECT}" || "${PROJECT}" == "unset" ]]; then
  echo "ERROR: gcloud project not set. Run: gcloud config set project <PROJECT_ID>" | tee -a "${OUT}"
  exit 1
fi

echo -e "\n# PROJECT: ${PROJECT}\n" | tee -a "${OUT}"

echo -e "\n## Cloud Build triggers (possible CI pipelines)" | tee -a "${OUT}"
gcloud beta builds triggers list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no triggers or permission issue" | tee -a "${OUT}"

echo -e "\n## Cloud Build recent builds (last 50)" | tee -a "${OUT}"
gcloud builds list --project="${PROJECT}" --limit=50 --format=json 2>&1 | jq '.' || echo "cloud builds list failed" | tee -a "${OUT}"

echo -e "\n## Cloud Run services (managed) - all regions" | tee -a "${OUT}"
gcloud run services list --platform=managed --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no cloud run services or disabled" | tee -a "${OUT}"

echo -e "\n## Cloud Functions" | tee -a "${OUT}"
gcloud functions list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no functions or permission issue" | tee -a "${OUT}"

echo -e "\n## Dataflow jobs (recent)" | tee -a "${OUT}"
gcloud dataflow jobs list --project="${PROJECT}" --limit=50 --format=json 2>&1 | jq '.' || echo "no dataflow jobs or permission issue" | tee -a "${OUT}"

echo -e "\n## Composer environments (Airflow)" | tee -a "${OUT}"
gcloud composer environments list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no composer envs or permission issue" | tee -a "${OUT}"

echo -e "\n## Workflows (Cloud Workflows)" | tee -a "${OUT}"
gcloud workflows list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no workflows or permission issue" | tee -a "${OUT}"

echo -e "\n## Cloud Scheduler jobs" | tee -a "${OUT}"
gcloud scheduler jobs list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no scheduler jobs or permission issue" | tee -a "${OUT}"

echo -e "\n## Pub/Sub topics" | tee -a "${OUT}"
gcloud pubsub topics list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no pubsub topics or permission issue" | tee -a "${OUT}"

echo -e "\n## Pub/Sub subscriptions" | tee -a "${OUT}"
gcloud pubsub subscriptions list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no pubsub subscriptions or permission issue" | tee -a "${OUT}"

echo -e "\n## Artifact Registry repos" | tee -a "${OUT}"
gcloud artifacts repositories list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no artifact repos or permission issue" | tee -a "${OUT}"

echo -e "\n## Vertex AI: datasets, models, endpoints, pipeline jobs (us-central1)" | tee -a "${OUT}"
gcloud ai datasets list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' || echo "vertex datasets none/permission issue" | tee -a "${OUT}"
gcloud ai models list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' || echo "vertex models none/permission issue" | tee -a "${OUT}"
gcloud ai endpoints list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' || echo "vertex endpoints none/permission issue" | tee -a "${OUT}"
gcloud ai pipeline-jobs list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' || echo "vertex pipeline jobs none/permission issue" | tee -a "${OUT}"

echo -e "\n## GKE clusters (and kube workloads if credentials present)" | tee -a "${OUT}"
gcloud container clusters list --project="${PROJECT}" --format=json 2>&1 | jq '.' | tee -a "${OUT}" || echo "no GKE clusters or permission issue" | tee -a "${OUT}"

# if kubectl configured & context present, try to list namespaces (safe)
if kubectl version --client >/dev/null 2>&1; then
  echo -e "\n## kubectl: current-context and namespaces (if kubeconfig exists)" | tee -a "${OUT}"
  kubectl config current-context 2>&1 | tee -a "${OUT}" || true
  kubectl get namespaces -o json 2>&1 | jq '.' | tee -a "${OUT}" || true
fi

echo -e "\n## Dataproc clusters" | tee -a "${OUT}"
gcloud dataproc clusters list --project="${PROJECT}" --region=us-central1 --format=json 2>&1 | jq '.' || echo "no dataproc clusters or permission issue" | tee -a "${OUT}"

echo -e "\n## BigQuery Transfer configs (scheduled ingests from marketplace/APIs)" | tee -a "${OUT}"
gcloud bq transfers list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no bigquery transfer configs or permission issue" | tee -a "${OUT}"

echo -e "\n## Cloud Logging sinks" | tee -a "${OUT}"
gcloud logging sinks list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no sinks or permission issue" | tee -a "${OUT}"

echo -e "\n## Cloud Monitoring alert policies (possible pipeline alerts)" | tee -a "${OUT}"
gcloud monitoring policies list --project="${PROJECT}" --format=json 2>&1 | jq '.' || echo "no alert policies or permission issue" | tee -a "${OUT}"

echo -e "\n## Storage buckets & lifecycle (sanity check)" | tee -a "${OUT}"
gsutil ls -p "${PROJECT}" 2>&1 | tee -a "${OUT}" || echo "gsutil list may include other projects" | tee -a "${OUT}"

echo -e "\n## END PIPELINE INVENTORY $(date -u) ===" | tee -a "${OUT}"

echo -e "\nInventory saved to: ${OUT}"
