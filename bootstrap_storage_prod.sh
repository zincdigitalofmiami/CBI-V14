#!/usr/bin/env bash
set -euo pipefail
PROJECT="cbi-v14"
PROC_BUCKET="forecasting-app-processed-data-bucket"
REGION="us-central1"

echo "=== STORAGE HARDEN (prod) $(date -u) ==="

if gsutil ls -p "${PROJECT}" "gs://${PROC_BUCKET}" >/dev/null 2>&1; then
  echo "✓ Exists: gs://${PROC_BUCKET}"
else
  echo "-> Creating: gs://${PROC_BUCKET} in ${REGION}"
  gsutil mb -p "${PROJECT}" -l "${REGION}" -c STANDARD "gs://${PROC_BUCKET}"
fi

echo "-> Enforce uniform bucket-level access"
gsutil uniformbucketlevelaccess set on "gs://${PROC_BUCKET}"

echo "-> Enable object versioning"
gsutil versioning set on "gs://${PROC_BUCKET}"

echo "-> Set labels"
gsutil label ch -l env:prod -l app:forecasting -l owner:zinc "gs://${PROC_BUCKET}"

echo "-> Apply lifecycle: delete noncurrent versions after 30d, current after 365d (adjust later if needed)"
cat > /tmp/proc_lifecycle.json <<JSON
{
  "rule": [
    {"action":{"type":"Delete"},"condition":{"isLive": false, "age": 30}},
    {"action":{"type":"Delete"},"condition":{"age": 365}}
  ]
}
JSON
gsutil lifecycle set /tmp/proc_lifecycle.json "gs://${PROC_BUCKET}"

echo -e "\n# Verify"
gsutil ls -L -b "gs://${PROC_BUCKET}" | sed -n '1,240p'
echo -e "\n=== DONE STORAGE HARDEN ==="
