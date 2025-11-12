#!/usr/bin/env python3
"""
Complete workflow: Train locally with TensorFlow Metal, deploy to Vertex AI.

This script orchestrates the complete workflow:
1. Train model locally with TensorFlow Metal GPU
2. Export to SavedModel format
3. Upload to Vertex AI Model Registry
4. Deploy endpoint for predictions

Supports all 5 horizons: 1w, 1m, 3m, 6m, 12m
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import deployment functions
from export_savedmodel import export_savedmodel
from upload_to_vertex import upload_to_vertex
from create_endpoint import create_endpoint

PROJECT = "cbi-v14"
LOCATION = "us-central1"

# Default paths (can be overridden via environment variables)
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
CBI_V14_MODELS = os.getenv("CBI_V14_MODELS", f"{CBI_V14_REPO}/Models")
CBI_V14_LOGS = os.getenv("CBI_V14_LOGS", f"{CBI_V14_REPO}/Logs")


def train_local_deploy_vertex(
    horizon: str,
    model_path: Optional[str] = None,
    skip_training: bool = False,
    skip_export: bool = False,
    skip_upload: bool = False,
    skip_deploy: bool = False
) -> bool:
    """
    Complete workflow: Train locally, export, upload, deploy.
    
    Args:
        horizon: Prediction horizon (1w, 1m, 3m, 6m, 12m)
        model_path: Path to trained model (if skip_training=True)
        skip_training: Skip training step (use existing model)
        skip_export: Skip SavedModel export step
        skip_upload: Skip Vertex AI upload step
        skip_deploy: Skip endpoint deployment step
    
    Returns:
        True if all steps successful, False otherwise
    """
    print("="*80)
    print(f"🚀 COMPLETE WORKFLOW: Train Local → Deploy Vertex AI")
    print(f"   Horizon: {horizon.upper()}")
    print("="*80)
    print()
    
    # Step 1: Train model locally (if not skipped)
    if not skip_training:
        print("STEP 1: Training model locally with TensorFlow Metal...")
        print("⚠️  Training step not yet implemented")
        print("   Please train model separately and provide --model-path")
        print("   Or implement training logic here")
        print()
        
        if not model_path:
            print("❌ Error: No model path provided and training skipped")
            return False
    else:
        print("STEP 1: Skipping training (using existing model)")
        print()
    
    if not model_path:
        # Default model path
        model_path = f"{CBI_V14_MODELS}/local/{horizon}_model.h5"
    
    if not os.path.exists(model_path):
        print(f"❌ Error: Model not found at: {model_path}")
        return False
    
    print(f"✅ Using model: {model_path}")
    print()
    
    # Step 2: Export to SavedModel format
    if not skip_export:
        print("STEP 2: Exporting to SavedModel format...")
        savedmodel_path = f"{CBI_V14_MODELS}/vertex-ai/{horizon}_savedmodel"
        
        success = export_savedmodel(
            model_path=model_path,
            output_path=savedmodel_path,
            horizon=horizon
        )
        
        if not success:
            print("❌ SavedModel export failed!")
            return False
        
        print()
    else:
        print("STEP 2: Skipping SavedModel export")
        savedmodel_path = f"{CBI_V14_MODELS}/vertex-ai/{horizon}_savedmodel"
        print()
    
    # Step 3: Upload to Vertex AI Model Registry
    if not skip_upload:
        print("STEP 3: Uploading to Vertex AI Model Registry...")
        model_display_name = f"CBI V14 Vertex – Neural {horizon.upper()}"
        
        model_resource = upload_to_vertex(
            savedmodel_path=savedmodel_path,
            model_display_name=model_display_name,
            description=f"Neural network model trained locally for {horizon} horizon"
        )
        
        if not model_resource:
            print("❌ Vertex AI upload failed!")
            return False
        
        print()
    else:
        print("STEP 3: Skipping Vertex AI upload")
        print("⚠️  Cannot deploy endpoint without uploaded model")
        return False
    
    # Step 4: Deploy endpoint
    if not skip_deploy:
        print("STEP 4: Deploying endpoint...")
        endpoint_display_name = f"CBI V14 Vertex – Neural {horizon.upper()} Endpoint"
        
        endpoint_resource = create_endpoint(
            model_resource_name=model_resource,
            endpoint_display_name=endpoint_display_name,
            machine_type="n1-standard-4",
            min_replicas=1,
            max_replicas=3
        )
        
        if not endpoint_resource:
            print("❌ Endpoint deployment failed!")
            return False
        
        print()
    else:
        print("STEP 4: Skipping endpoint deployment")
        print()
    
    print("="*80)
    print("✅ COMPLETE WORKFLOW SUCCESSFUL!")
    print("="*80)
    print(f"   Model: {model_resource}")
    if not skip_deploy:
        print(f"   Endpoint: {endpoint_resource}")
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Complete workflow: Train locally, deploy to Vertex AI"
    )
    parser.add_argument(
        "--horizon",
        required=True,
        choices=["1w", "1m", "3m", "6m", "12m"],
        help="Prediction horizon"
    )
    parser.add_argument(
        "--model-path",
        help="Path to trained model (if training skipped)"
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Skip training step (use existing model)"
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Skip SavedModel export step"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip Vertex AI upload step"
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip endpoint deployment step"
    )
    
    args = parser.parse_args()
    
    success = train_local_deploy_vertex(
        horizon=args.horizon,
        model_path=args.model_path,
        skip_training=args.skip_training,
        skip_export=args.skip_export,
        skip_upload=args.skip_upload,
        skip_deploy=args.skip_deploy
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

