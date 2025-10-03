#!/usr/bin/env bash
set -euo pipefail
PROJECT=cbi-v14
OUTDIR="$HOME/v13_check"
mkdir -p "${OUTDIR}"

echo "=== START v13 CHECK $(date -u) ===" > "${OUTDIR}/run.log"

echo -e "\n# Artifact Registry repos (project=${PROJECT})" | tee -a "${OUTDIR}/run.log"
gcloud artifacts repositories list --project="${PROJECT}" --format="table(name,format,location)" 2>&1 | tee -a "${OUTDIR}/run.log"

REPO_PATH="us-central1-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy"

echo -e "\n# Listing docker images in repo: ${REPO_PATH} (if it exists)" | tee -a "${OUTDIR}/run.log"
gcloud artifacts docker images list "${REPO_PATH}" --project="${PROJECT}" --include-tags --format=json > "${OUTDIR}/ar_images.json" 2>/dev/null || echo "No images or repo not present" >> "${OUTDIR}/run.log"

echo -e "\n# Filter Artifact Registry images that mention 'cbi-v13'" | tee -a "${OUTDIR}/run.log"
if [[ -s "${OUTDIR}/ar_images.json" ]]; then
  jq '.[] | {name: .name, tags: .tags}' "${OUTDIR}/ar_images.json" | jq -s '.' > "${OUTDIR}/ar_images_compact.json"
  jq '.[] | select(.name|test("cbi-v13"))' "${OUTDIR}/ar_images.json" > "${OUTDIR}/ar_v13.json" || true
  if [[ -s "${OUTDIR}/ar_v13.json" ]]; then
    echo "Found Artifact Registry images referencing cbi-v13:" | tee -a "${OUTDIR}/run.log"
    jq -r '.[] | "- \(.name) (tags: \(.tags // [] | join(",")))"' "${OUTDIR}/ar_v13.json" | tee -a "${OUTDIR}/run.log"
  else
    echo "No Artifact Registry images containing 'cbi-v13' found." | tee -a "${OUTDIR}/run.log"
  fi
else
  echo "No repository images file created; repo may not exist or access denied." | tee -a "${OUTDIR}/run.log"
fi

echo -e "\n# Cloud Run services and the container images they reference" | tee -a "${OUTDIR}/run.log"
gcloud run services list --platform=managed --project="${PROJECT}" --format=json > "${OUTDIR}/run_services.json" 2>&1 || true
jq -r '.[] | {name: .metadata.name, image: .spec.template.spec.containers[0].image} ' "${OUTDIR}/run_services.json" | tee "${OUTDIR}/run_services_images.txt" || true
echo -e "\nPrinted Cloud Run services -> images (also saved to ${OUTDIR}/run_services_images.txt)" | tee -a "${OUTDIR}/run.log"

echo -e "\n# Cross-check: which Cloud Run services currently reference an image with 'cbi-v13' in its URL?" | tee -a "${OUTDIR}/run.log"
jq -r '.[] | select(.spec.template.spec.containers[0].image|test("cbi-v13")) | {name:.metadata.name, image:.spec.template.spec.containers[0].image}' "${OUTDIR}/run_services.json" > "${OUTDIR}/run_services_using_v13.json" || true
if [[ -s "${OUTDIR}/run_services_using_v13.json" ]]; then
  echo "Services using cbi-v13 images:" | tee -a "${OUTDIR}/run.log"
  jq -r '.[] | "- \(.name): \(.image)"' "${OUTDIR}/run_services_using_v13.json" | tee -a "${OUTDIR}/run.log"
else
  echo "No Cloud Run services currently reference cbi-v13 images." | tee -a "${OUTDIR}/run.log"
fi

echo -e "\n=== END v13 CHECK $(date -u) ===" | tee -a "${OUTDIR}/run.log"

# print the most relevant summaries to the terminal for quick paste
echo -e "\n--- SUMMARY ---"
echo "Artifact Repo: ${REPO_PATH}"
if [[ -s "${OUTDIR}/ar_v13.json" ]]; then
  echo "Artifact images referencing cbi-v13 (first 20 lines):"
  jq -r '.[] | "- \(.name) (tags: \(.tags // [] | join(",")))"' "${OUTDIR}/ar_v13.json" | sed -n '1,20p'
else
  echo "No Artifact images with 'cbi-v13' found."
fi

echo -e "\nCloud Run services -> image (first 200 chars per line):"
sed -n '1,200p' "${OUTDIR}/run_services_images.txt" | sed -n '1,200p'

if [[ -s "${OUTDIR}/run_services_using_v13.json" ]]; then
  echo -e "\nServices actively using cbi-v13 images:"
  jq -r '.[] | "- \(.name): \(.image)"' "${OUTDIR}/run_services_using_v13.json"
else
  echo -e "\nNo Cloud Run services are actively using cbi-v13 images."
fi

echo -e "\nFiles saved under: ${OUTDIR} (ar_images.json, ar_v13.json, run_services.json, run_services_images.txt, run_services_using_v13.json, run.log)"
