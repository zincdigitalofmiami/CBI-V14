#!/usr/bin/env python3
"""
Upload SavedModel to Vertex AI Model Registry.

Uploads TensorFlow SavedModel to Vertex AI Model Registry.
Model display name: CBI V14 Vertex – Neural {horizon}
Uses TensorFlow serving container image.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from google.cloud import aiplatform
from google.cloud.aiplatform import models

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT = "cbi-v14"
LOCATION = "us-central1"


def upload_to_vertex(
    savedmodel_path: str,
    model_display_name: str,
    description: Optional[str] = None
) -> Optional[str]:
    """
    Upload SavedModel to Vertex AI Model Registry.
    
    Args:
        savedmodel_path: Path to SavedModel directory
        model_display_name: Display name for the model in Vertex AI
        description: Optional description for the model
    
    Returns:
        Model resource name if successful, None otherwise
    """
    try:
        # Initialize Vertex AI
        aiplatform.init(project=PROJECT, location=LOCATION)
        
        print(f"📤 Uploading SavedModel from: {savedmodel_path}")
        print(f"📝 Model display name: {model_display_name}")
        
        # Verify SavedModel exists
        if not os.path.exists(savedmodel_path):
            print(f"❌ Error: SavedModel path does not exist: {savedmodel_path}")
            return None
        
        # Upload model to Vertex AI
        model = aiplatform.Model.upload(
            display_name=model_display_name,
            artifact_uri=savedmodel_path,
            serving_container_image_uri=(
                "us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-13:latest"
            ),
            description=description or f"Neural network model for {model_display_name}",
            sync=True
        )
        
        print(f"✅ Model uploaded successfully!")
        print(f"   Model ID: {model.resource_name}")
        print(f"   Model name: {model.display_name}")
        
        return model.resource_name
        
    except Exception as e:
        print(f"❌ Error uploading model to Vertex AI: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Upload SavedModel to Vertex AI Model Registry"
    )
    parser.add_argument(
        "--savedmodel-path",
        required=True,
        help="Path to SavedModel directory"
    )
    parser.add_argument(
        "--model-display-name",
        required=True,
        help="Display name for the model in Vertex AI"
    )
    parser.add_argument(
        "--description",
        help="Optional description for the model"
    )
    
    args = parser.parse_args()
    
    model_resource = upload_to_vertex(
        savedmodel_path=args.savedmodel_path,
        model_display_name=args.model_display_name,
        description=args.description
    )
    
    if model_resource:
        print(f"\n✅ Upload complete! Model resource: {model_resource}")
        sys.exit(0)
    else:
        print("\n❌ Upload failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()


