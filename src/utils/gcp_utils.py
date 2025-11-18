#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBI-V14 - Google Cloud Platform (GCP) Utilities
================================================

Helper functions for interacting with GCP services, primarily for
configuration and authentication.
"""
import os
import json
from pathlib import Path

def get_gcp_project_id() -> str:
    """
    Retrieves the GCP Project ID from the environment or a config file.

    Order of precedence:
    1. `GCP_PROJECT_ID` environment variable.
    2. The `project_id` key from the standard gcloud ADC file.
    3. The `project_id` key from our project's specific key file.

    Returns:
        The GCP Project ID string, or an empty string if not found.
    """
    # 1. Check environment variable
    if os.getenv('GCP_PROJECT_ID'):
        return os.getenv('GCP_PROJECT_ID')

    # 2. Check standard gcloud ADC file
    try:
        adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        if adc_path.exists():
            with open(adc_path, 'r') as f:
                creds = json.load(f)
                if 'project_id' in creds:
                    return creds['project_id']
    except Exception:
        pass # Ignore errors here, just a fallback

    # 3. Check project-specific key file
    try:
        project_key_path = Path(__file__).parent.parent.parent / "config" / "terraform" / "cbi-v14-gcp-key.json"
        if project_key_path.exists():
            with open(project_key_path, 'r') as f:
                keyfile = json.load(f)
                if 'project_id' in keyfile:
                    return keyfile['project_id']
    except Exception:
        pass # Final fallback
        
    # As a final, hardcoded fallback for this specific project
    return "cbi-v14"
