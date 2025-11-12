#!/bin/bash

# Script to clean up unused Vercel deployments
# Keeps only the latest production deployment for each project

set -e

echo "🧹 Cleaning up unused Vercel deployments..."
echo ""

# Function to get deployment ID from URL
get_deployment_id() {
    local url=$1
    vercel inspect "$url" 2>&1 | grep -E "^\s+id\s+" | awk '{print $2}' | head -1
}

# Function to get all deployment URLs (handles pagination)
get_all_deployments() {
    local project_name=$1
    local all_deployments=""
    local next_token=""
    local page=1
    
    while true; do
        local cmd_output
        if [ -z "$next_token" ]; then
            cmd_output=$(vercel ls "$project_name" 2>&1)
        else
            cmd_output=$(vercel ls "$project_name" --next "$next_token" 2>&1)
        fi
        
        # Extract URLs from this page
        local page_deployments=$(echo "$cmd_output" | grep -oE 'https://[^[:space:]]+' | sort -u)
        if [ -n "$page_deployments" ]; then
            if [ -z "$all_deployments" ]; then
                all_deployments="$page_deployments"
            else
                all_deployments="$all_deployments"$'\n'"$page_deployments"
            fi
        fi
        
        # Check if there's a next page
        if echo "$cmd_output" | grep -q "To display the next page"; then
            next_token=$(echo "$cmd_output" | grep "To display the next page" | grep -oE '[0-9]+' | head -1)
            page=$((page + 1))
            echo "   📄 Fetched page $page..." >&2
        else
            break
        fi
    done
    
    # Return unique sorted deployments (only URLs)
    echo "$all_deployments" | grep -E "^https://" | sort -u
}

# Function to cleanup deployments for a project
cleanup_project() {
    local project_name=$1
    shift
    local keep_urls=("$@")  # Additional URLs to keep
    
    echo "📦 Processing project: $project_name"
    echo "   🔍 Fetching all deployments (this may take a moment)..."
    
    # Get all deployment URLs (handles pagination)
    local deployments=$(get_all_deployments "$project_name")
    
    if [ -z "$deployments" ]; then
        echo "   No deployments found"
        return
    fi
    
    # Get the first (most recent) deployment as the one to keep
    local first_deployment=$(echo "$deployments" | head -1)
    
    # Build list of deployment IDs to keep
    local keep_ids=""
    
    # Add the first (most recent) deployment
    echo "   🔍 Getting deployment ID for: $first_deployment"
    local first_id=$(get_deployment_id "$first_deployment")
    if [ -n "$first_id" ]; then
        keep_ids="$first_id"
        echo "   ✅ Keeping deployment: $first_deployment (ID: $first_id)"
    fi
    
    # Add any additional URLs to keep
    for keep_url in "${keep_urls[@]}"; do
        # Remove trailing slash if present
        keep_url="${keep_url%/}"
        echo "   🔍 Getting deployment ID for: $keep_url"
        local keep_id=$(get_deployment_id "$keep_url")
        if [ -n "$keep_id" ]; then
            if [ -z "$keep_ids" ]; then
                keep_ids="$keep_id"
            else
                keep_ids="$keep_ids"$'\n'"$keep_id"
            fi
            echo "   ✅ Keeping deployment: $keep_url (ID: $keep_id)"
        else
            echo "   ⚠️  Could not get deployment ID for: $keep_url"
        fi
    done
    
    if [ -z "$keep_ids" ]; then
        echo "   ⚠️  No deployments to keep, skipping..."
        return
    fi
    
    echo ""
    
    # Count total deployments
    local total=$(echo "$deployments" | wc -l | tr -d ' ')
    local keep_count=$(echo "$keep_ids" | grep -v "^$" | wc -l | tr -d ' ')
    local to_delete=$((total - keep_count))
    
    echo "   📊 Found $total deployments, keeping $keep_count, will delete $to_delete old ones"
    echo ""
    
    # Delete all other deployments
    local count=0
    for deployment in $deployments; do
        local dep_id=$(get_deployment_id "$deployment")
        
        if [ -z "$dep_id" ]; then
            echo "   ⚠️  Skipping $deployment (could not get ID)"
            continue
        fi
        
        # Check if this deployment should be kept
        if echo "$keep_ids" | grep -q "^$dep_id$"; then
            continue
        fi
        
        count=$((count + 1))
        echo "   🗑️  [$count/$to_delete] Deleting: $deployment (ID: $dep_id)"
        vercel rm "$dep_id" --yes 2>&1 | grep -v "Vercel CLI" || true
    done
    
    echo "   ✅ Cleanup complete for $project_name"
    echo ""
}

# Cleanup all projects
echo "Starting cleanup for all projects..."
echo ""

# Keep specific deployments as requested
cleanup_project "cbi-dashboard" "https://cbi-dashboard-1qjx7qban-zincdigitalofmiamis-projects.vercel.app"
cleanup_project "dashboard-nextjs"
cleanup_project "summit-bi-intel" "https://summit-bi-intel-j4jm2d8ep-zincdigitalofmiamis-projects.vercel.app"

echo "🎉 All cleanup complete!"

