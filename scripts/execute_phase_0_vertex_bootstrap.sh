#!/bin/bash
# Phase 0.5 & 0.6: Vertex AI One-Time Bootstrap
# Extract residual quantiles and feature importance from Vertex AI

set -e  # Exit on error

echo "============================================================"
echo "🚀 PHASE 0.5 & 0.6: VERTEX AI ONE-TIME BOOTSTRAP"
echo "============================================================"
echo ""
echo "⚠️  CRITICAL: This is the LAST time we use Vertex AI"
echo "✅ After this, BQML becomes the ONLY ongoing system"
echo ""
echo "Step 1: Extract Vertex Residual Quantiles (Phase 0.5)"
echo "Step 2: Import Vertex Feature Importance (Phase 0.6)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "============================================================"
echo "Phase 0.5: Extracting Vertex Residual Quantiles"
echo "============================================================"
python3 scripts/extract_vertex_residuals.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "Phase 0.6: Importing Vertex Feature Importance"
    echo "============================================================"
    python3 scripts/extract_vertex_feature_importance.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "============================================================"
        echo "✅ VERTEX AI BOOTSTRAP COMPLETE"
        echo "============================================================"
        echo "✅ Residual quantiles extracted"
        echo "✅ Feature importance imported"
        echo ""
        echo "⚠️  IMPORTANT: This was the LAST Vertex AI operation"
        echo "✅ BQML is now the ONLY ongoing system"
        echo "✅ No more Vertex AI dependencies"
        echo "============================================================"
    else
        echo ""
        echo "❌ Phase 0.6 failed - check errors above"
        exit 1
    fi
else
    echo ""
    echo "❌ Phase 0.5 failed - check errors above"
    exit 1
fi



