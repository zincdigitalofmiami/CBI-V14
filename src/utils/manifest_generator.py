#!/usr/bin/env python3
"""Generate manifests for Alpha Vantage data collection tracking"""

import json
import hashlib
from datetime import datetime
from pathlib import Path

class ManifestGenerator:
    """Track all Alpha data collection for reproducibility"""
    
    def __init__(self, manifest_dir="/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/alpha/manifests"):
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
    
    def create_manifest(self, collection_type, data):
        """Create manifest for a collection run"""
        
        manifest = {
            "collection_date": datetime.now().strftime("%Y-%m-%d"),
            "collection_ts": datetime.now().isoformat(),
            "collection_type": collection_type,  # 'daily', 'indicators', 'backfill'
            "data_summary": {
                "symbols_collected": data.get('symbols', []),
                "indicators_collected": data.get('indicators', []),
                "date_range": data.get('date_range', {}),
                "rows_collected": data.get('row_count', 0),
                "file_size_mb": data.get('file_size', 0) / 1024 / 1024 if data.get('file_size') else 0
            },
            "api_usage": {
                "calls_made": data.get('api_calls', 0),
                "rate_limit": "75/min",
                "errors": data.get('errors', [])
            },
            "data_quality": {
                "null_counts": data.get('null_counts', {}),
                "validation_passed": data.get('validation', True),
                "warnings": data.get('warnings', [])
            },
            "file_locations": {
                "local_raw": data.get('local_path'),
                "local_staging": data.get('staging_path'),
                "bq_table": data.get('bq_table')
            },
            "checksums": {
                "raw_data_hash": self._calculate_hash(data.get('local_path')) if data.get('local_path') else None,
                "staging_data_hash": self._calculate_hash(data.get('staging_path')) if data.get('staging_path') else None
            }
        }
        
        # Save manifest
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_file = self.manifest_dir / f"{collection_type}_{date_str}.json"
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Manifest saved: {manifest_file}")
        return manifest
    
    def _calculate_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        if not file_path or not Path(file_path).exists():
            return None
        
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

