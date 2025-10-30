#!/bin/bash
#
# PHASE 4: MONTHLY VERTEX AI PREDICTIONS
# Runs 1st of month at 2 AM
# Deploys endpoints → Gets predictions → Undeploys → Saves to BigQuery
#

set -e  # Exit on error

LOG_FILE="/Users/zincdigital/CBI-V14/logs/vertex_predictions.log"
ERROR_LOG="/Users/zincdigital/CBI-V14/logs/errors.log"
CONFIG_DIR="/Users/zincdigital/CBI-V14/config"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$ERROR_LOG"
}

log "================================================================================"
log "MONTHLY VERTEX AI PREDICTIONS - $(date)"
log "================================================================================"

# Check if today is 1st of month
DAY_OF_MONTH=$(date +%d)
if [ "$DAY_OF_MONTH" != "01" ] && [ "$FORCE_RUN" != "true" ]; then
    log "⚠️  Not 1st of month (day $DAY_OF_MONTH) - skipping"
    log "   To force run: FORCE_RUN=true $0"
    exit 0
fi

# Record start time
START_TIME=$(date +%s)

# Run Python script
log "🚀 Starting endpoint deployment..."
cd /Users/zincdigital/CBI-V14/automl

if python3 quick_endpoint_predictions.py >> "$LOG_FILE" 2>&1; then
    log "✅ Predictions complete"
    
    # Record end time and calculate cost
    END_TIME=$(date +%s)
    DURATION_MIN=$(( (END_TIME - START_TIME) / 60 ))
    
    log "⏱️  Total runtime: $DURATION_MIN minutes"
    log "💰 Estimated cost: \$$(python3 -c "print(f'{$DURATION_MIN * 0.14:.2f}')")"
    
    # Save run metadata
    cat > "$CONFIG_DIR/last_run.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "duration_minutes": $DURATION_MIN,
  "status": "success"
}
EOF
    
    log "✅ MONTHLY PREDICTIONS COMPLETE"
    exit 0
else
    error "❌ Predictions failed"
    
    cat > "$CONFIG_DIR/last_run.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "failed",
  "error": "See $ERROR_LOG"
}
EOF
    
    exit 1
fi

