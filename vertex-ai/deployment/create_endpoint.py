#!/usr/bin/env python3
"""
Deploy model to Vertex AI endpoint for predictions.

Deploys model to Vertex AI endpoint for online predictions.
Endpoint display name: CBI V14 Vertex – Neural {horizon} Endpoint
Machine type: n1-standard-4 (configurable)
Min/max replicas: 1-3 (auto-scaling)
"""

import os
import sys
import argparse
from pathlib import Path
from google.cloud import aiplatform

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT = "cbi-v14"
LOCATION = "us-central1"


def create_endpoint(
    model_resource_name: str,
    endpoint_display_name: str,
    machine_type: str = "n1-standard-4",
    min_replicas: int = 1,
    max_replicas: int = 3
) -> str:
    """
    Deploy model to Vertex AI endpoint.
    
    Args:
        model_resource_name: Full resource name of the model (projects/.../models/...)
        endpoint_display_name: Display name for the endpoint
        machine_type: Machine type for deployment (default: n1-standard-4)
        min_replicas: Minimum number of replicas (default: 1)
        max_replicas: Maximum number of replicas (default: 3)
    
    Returns:
        Endpoint resource name if successful, None otherwise
    """
    try:
        # Initialize Vertex AI
        aiplatform.init(project=PROJECT, location=LOCATION)
        
        print(f"🚀 Creating endpoint: {endpoint_display_name}")
        print(f"📦 Model: {model_resource_name}")
        print(f"💻 Machine type: {machine_type}")
        print(f"📊 Replicas: {min_replicas}-{max_replicas}")
        
        # Get model
        model = aiplatform.Model(model_resource_name)
        print(f"✅ Model loaded: {model.display_name}")
        
        # Create or get endpoint
        endpoints = aiplatform.Endpoint.list(
            filter=f'display_name="{endpoint_display_name}"'
        )
        
        if endpoints:
            endpoint = endpoints[0]
            print(f"✅ Using existing endpoint: {endpoint.display_name}")
        else:
            endpoint = aiplatform.Endpoint.create(display_name=endpoint_display_name)
            print(f"✅ Created new endpoint: {endpoint.display_name}")
        
        # Deploy model to endpoint
        print(f"📤 Deploying model to endpoint...")
        endpoint.deploy(
            model=model,
            deployed_model_display_name=f"{endpoint_display_name}_model",
            machine_type=machine_type,
            min_replica_count=min_replicas,
            max_replica_count=max_replicas,
            sync=True
        )
        
        print(f"✅ Model deployed successfully!")
        print(f"   Endpoint: {endpoint.resource_name}")
        print(f"   Endpoint ID: {endpoint.name}")
        
        return endpoint.resource_name
        
    except Exception as e:
        print(f"❌ Error deploying model to endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Deploy model to Vertex AI endpoint"
    )
    parser.add_argument(
        "--model-resource-name",
        required=True,
        help="Full resource name of the model (projects/.../models/...)"
    )
    parser.add_argument(
        "--endpoint-display-name",
        required=True,
        help="Display name for the endpoint"
    )
    parser.add_argument(
        "--machine-type",
        default="n1-standard-4",
        help="Machine type for deployment (default: n1-standard-4)"
    )
    parser.add_argument(
        "--min-replicas",
        type=int,
        default=1,
        help="Minimum number of replicas (default: 1)"
    )
    parser.add_argument(
        "--max-replicas",
        type=int,
        default=3,
        help="Maximum number of replicas (default: 3)"
    )
    
    args = parser.parse_args()
    
    endpoint_resource = create_endpoint(
        model_resource_name=args.model_resource_name,
        endpoint_display_name=args.endpoint_display_name,
        machine_type=args.machine_type,
        min_replicas=args.min_replicas,
        max_replicas=args.max_replicas
    )
    
    if endpoint_resource:
        print(f"\n✅ Deployment complete! Endpoint: {endpoint_resource}")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()


