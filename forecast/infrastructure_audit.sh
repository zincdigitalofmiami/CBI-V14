#!/bin/bash
# Complete Infrastructure Audit for final-cb-app
# Checks locations, naming, permissions, and configuration alignment

set -e
PROJECT="final-cb-app"
EXPECTED_REGION="us-central1"

echo "=================================="
echo "INFRASTRUCTURE AUDIT: $PROJECT"
echo "=================================="
echo "Expected Region: $EXPECTED_REGION"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error_count=0
warning_count=0

check_result() {
    local status=$1
    local message=$2
    local severity=${3:-"ERROR"}
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $message"
    elif [ "$severity" = "WARNING" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC}: $message"
        ((warning_count++))
    else
        echo -e "${RED}✗ FAIL${NC}: $message"
        ((error_count++))
    fi
}

echo "1. PROJECT CONFIGURATION"
echo "------------------------"
current_project=$(gcloud config get-value project 2>/dev/null)
if [ "$current_project" = "$PROJECT" ]; then
    check_result "PASS" "Project set correctly: $current_project"
else
    check_result "FAIL" "Wrong project: $current_project (expected: $PROJECT)"
fi

echo ""
echo "2. BIGQUERY DATASETS"
echo "-------------------"
bq_datasets=$(bq ls --format=json | jq -r '.[] | "\(.datasetReference.datasetId):\(.location)"')
echo "Found datasets:"
while IFS= read -r line; do
    dataset_id=$(echo $line | cut -d: -f1)
    location=$(echo $line | cut -d: -f2)
    echo "  $dataset_id in $location"
    
    if [ "$dataset_id" = "financial_market_data" ]; then
        if [ "$location" = "$EXPECTED_REGION" ]; then
            check_result "PASS" "financial_market_data dataset in correct region: $location"
        else
            check_result "FAIL" "financial_market_data dataset in wrong region: $location (expected: $EXPECTED_REGION)"
        fi
    fi
done <<< "$bq_datasets"

echo ""
echo "3. CLOUD STORAGE BUCKETS"
echo "-----------------------"
buckets=$(gsutil ls -L -b gs://*${PROJECT}* 2>/dev/null | grep -E "(gs://|Location constraint)" | paste - -)
if [ -z "$buckets" ]; then
    check_result "FAIL" "No project buckets found"
else
    echo "Found buckets:"
    echo "$buckets" | while read -r line; do
        bucket=$(echo $line | grep -o 'gs://[^[:space:]]*' | head -1)
        location=$(echo $line | grep -o 'Location constraint:[^[:space:]]*' | cut -d: -f2)
        
        if [ -n "$bucket" ] && [ -n "$location" ]; then
            echo "  $bucket in $location"
            
            # Check naming convention
            if [[ "$bucket" =~ ^gs://.*${PROJECT}.* ]]; then
                if [[ "$bucket" =~ _cloudbuild$ ]]; then
                    check_result "FAIL" "Bucket uses underscore instead of hyphen: $bucket"
                else
                    check_result "PASS" "Bucket naming follows convention: $bucket"
                fi
            else
                check_result "FAIL" "Bucket doesn't follow naming convention: $bucket"
            fi
            
            # Check location alignment
            if [ "$location" = "$EXPECTED_REGION" ]; then
                check_result "PASS" "Bucket in correct region: $bucket"
            elif [ "$location" = "US" ] && [[ "$bucket" =~ (cloudbuild|run-sources) ]]; then
                check_result "FAIL" "Build/source bucket should be in $EXPECTED_REGION, not multi-region US: $bucket"
            else
                check_result "FAIL" "Bucket in wrong location: $bucket ($location, expected: $EXPECTED_REGION)"
            fi
        fi
    done
fi

echo ""
echo "4. CLOUD RUN SERVICES"
echo "--------------------"
services=$(gcloud run services list --region=$EXPECTED_REGION --format="value(metadata.name,status.url)")
if [ -z "$services" ]; then
    check_result "FAIL" "No Cloud Run services found in $EXPECTED_REGION"
else
    echo "Found services in $EXPECTED_REGION:"
    echo "$services" | while IFS=$'\t' read -r name url; do
        echo "  $name: $url"
        
        # Check service account
        sa=$(gcloud run services describe $name --region=$EXPECTED_REGION --format="value(spec.template.spec.serviceAccountName)")
        if [ -n "$sa" ]; then
            check_result "PASS" "Service $name has service account: $sa"
            
            # Check BigQuery permissions
            roles=$(gcloud projects get-iam-policy $PROJECT --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:serviceAccount:$sa" | tail -n +2)
            if echo "$roles" | grep -q "roles/bigquery.jobUser"; then
                check_result "PASS" "Service account has bigquery.jobUser role"
            else
                check_result "FAIL" "Service account missing bigquery.jobUser role"
            fi
            
            if echo "$roles" | grep -q "roles/bigquery.dataEditor"; then
                check_result "PASS" "Service account has bigquery.dataEditor role"
            else
                check_result "FAIL" "Service account missing bigquery.dataEditor role"
            fi
        else
            check_result "FAIL" "Service $name has no service account configured"
        fi
    done
fi

echo ""
echo "5. BIGQUERY TABLES"
echo "-----------------"
tables=$(bq ls final-cb-app:financial_market_data --format=json 2>/dev/null | jq -r '.[].tableReference.tableId' 2>/dev/null)
if [ -n "$tables" ]; then
    echo "Found tables:"
    echo "$tables" | while read -r table; do
        echo "  $table"
        row_count=$(bq query --use_legacy_sql=false --format=csv --max_rows=1 "SELECT COUNT(*) FROM \`$PROJECT.financial_market_data.$table\`" 2>/dev/null | tail -1)
        if [ -n "$row_count" ] && [ "$row_count" -gt 0 ]; then
            check_result "PASS" "Table $table has data ($row_count rows)"
        else
            check_result "FAIL" "Table $table is empty or inaccessible"
        fi
    done
else
    check_result "FAIL" "No tables found in financial_market_data dataset"
fi

echo ""
echo "=================================="
echo "AUDIT SUMMARY"
echo "=================================="
echo -e "Errors: ${RED}$error_count${NC}"
echo -e "Warnings: ${YELLOW}$warning_count${NC}"

if [ $error_count -eq 0 ]; then
    echo -e "${GREEN}✓ INFRASTRUCTURE AUDIT PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ INFRASTRUCTURE AUDIT FAILED${NC}"
    echo ""
    echo "CRITICAL ISSUES TO FIX:"
    echo "1. Ensure all resources are in $EXPECTED_REGION"
    echo "2. Fix bucket naming conventions (use hyphens, not underscores)"
    echo "3. Grant proper BigQuery permissions to service accounts"
    echo "4. Verify all services can communicate"
    exit 1
fi
