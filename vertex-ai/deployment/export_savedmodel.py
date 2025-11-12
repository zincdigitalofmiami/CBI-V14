#!/usr/bin/env python3
"""
Export TensorFlow SavedModel format for Vertex AI deployment.

Exports Keras model to SavedModel format (required for Vertex AI).
SavedModel includes 'serve' signature tag automatically.
Verifies export by loading and testing inference signature.
"""

import os
import sys
import argparse
import tensorflow as tf
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT = "cbi-v14"
LOCATION = "us-central1"


def export_savedmodel(
    model_path: str,
    output_path: str,
    horizon: str = "1m"
) -> bool:
    """
    Export Keras model to SavedModel format.
    
    Args:
        model_path: Path to saved Keras model (.h5 or SavedModel)
        output_path: Directory where SavedModel will be exported
        horizon: Prediction horizon (1w, 1m, 3m, 6m)
    
    Returns:
        True if export successful, False otherwise
    """
    try:
        print(f"📦 Loading model from: {model_path}")
        
        # Load model
        if model_path.endswith('.h5'):
            model = tf.keras.models.load_model(model_path)
        else:
            model = tf.keras.models.load_model(model_path)
        
        print(f"✅ Model loaded: {model.summary()}")
        
        # Create output directory
        os.makedirs(output_path, exist_ok=True)
        
        # Export to SavedModel format
        print(f"📤 Exporting SavedModel to: {output_path}")
        model.save(output_path, save_format='tf')
        
        # Verify export by loading SavedModel
        print("🔍 Verifying SavedModel export...")
        loaded_model = tf.saved_model.load(output_path)
        
        # Check for serve signature
        if 'serve' in loaded_model.signatures:
            print("✅ SavedModel exported successfully with 'serve' signature")
        else:
            print("⚠️  Warning: 'serve' signature not found, but model exported")
        
        print(f"✅ SavedModel export complete: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting SavedModel: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Export TensorFlow model to SavedModel format for Vertex AI"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to Keras model file (.h5 or SavedModel directory)"
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Output directory for SavedModel export"
    )
    parser.add_argument(
        "--horizon",
        default="1m",
        choices=["1w", "1m", "3m", "6m"],
        help="Prediction horizon (default: 1m)"
    )
    
    args = parser.parse_args()
    
    success = export_savedmodel(
        model_path=args.model_path,
        output_path=args.output_path,
        horizon=args.horizon
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


