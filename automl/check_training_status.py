#!/usr/bin/env python3
"""
Check current Vertex AI AutoML training status
"""

import logging
from google.cloud import aiplatform
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Vertex AI
project_id = "cbi-v14"
region = "us-central1"
aiplatform.init(project=project_id, location=region)

def check_training_status():
    """Check current AutoML training pipeline status."""
    
    logger.info("🔍 Checking Vertex AI AutoML training status...")
    
    try:
        # List all training pipelines from last 7 days
        from google.cloud.aiplatform_v1 import PipelineServiceClient
        from google.cloud.aiplatform_v1.types import ListTrainingPipelinesRequest
        
        client = PipelineServiceClient()
        parent = f"projects/{project_id}/locations/{region}"
        
        logger.info(f"Querying: {parent}")
        
        # Get training pipelines (use global for listing)
        global_parent = f"projects/{project_id}/locations/global"
        request = ListTrainingPipelinesRequest(parent=global_parent)
        response = client.list_training_pipelines(request=request)
        
        # Filter recent pipelines (last 30 days)
        recent_pipelines = []
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for pipeline in response:
            create_time = pipeline.create_time
            if create_time and create_time.timestamp() > cutoff_date.timestamp():
                recent_pipelines.append(pipeline)
        
        if not recent_pipelines:
            logger.info("❌ No recent training pipelines found (last 30 days)")
            logger.info("🔍 Checking for existing trained models...")
            
            # Check for existing models
            try:
                models = aiplatform.Model.list()
                cbi_models = [m for m in models if 'cbi' in m.display_name.lower() or 'soybean' in m.display_name.lower()]
                
                if cbi_models:
                    logger.info(f"📊 Found {len(cbi_models)} existing CBI models:")
                    for model in cbi_models:
                        logger.info(f"   - {model.display_name} (ID: {model.name.split('/')[-1]})")
                        logger.info(f"     Created: {model.create_time}")
                else:
                    logger.info("❌ No CBI models found")
            except Exception as e:
                logger.error(f"Error checking models: {e}")
                
            return
        
        logger.info(f"📊 Found {len(recent_pipelines)} recent training pipeline(s)")
        logger.info("\n" + "="*80)
        
        # Group by status
        running = []
        completed = []
        failed = []
        
        for pipeline in recent_pipelines:
            state_name = pipeline.state.name if pipeline.state else "UNKNOWN"
            
            if state_name in ["PIPELINE_STATE_RUNNING", "PIPELINE_STATE_PENDING"]:
                running.append(pipeline)
            elif state_name == "PIPELINE_STATE_SUCCEEDED":
                completed.append(pipeline)
            elif state_name in ["PIPELINE_STATE_FAILED", "PIPELINE_STATE_CANCELLED"]:
                failed.append(pipeline)
        
        # Display status
        logger.info(f"🟢 RUNNING: {len(running)}")
        logger.info(f"✅ COMPLETED: {len(completed)}")
        logger.info(f"❌ FAILED: {len(failed)}")
        
        # Show details for each pipeline
        for i, pipeline in enumerate(recent_pipelines, 1):
            pipeline_id = pipeline.name.split('/')[-1]
            display_name = pipeline.display_name or "Unknown"
            state_name = pipeline.state.name if pipeline.state else "UNKNOWN"
            create_time = pipeline.create_time.strftime('%Y-%m-%d %H:%M:%S') if pipeline.create_time else "Unknown"
            
            # Determine horizon from display name
            horizon = "Unknown"
            if "_1w_" in display_name.lower() or "1w" in display_name.lower():
                horizon = "1W"
            elif "_1m_" in display_name.lower() or "1m" in display_name.lower():
                horizon = "1M" 
            elif "_3m_" in display_name.lower() or "3m" in display_name.lower():
                horizon = "3M"
            elif "_6m_" in display_name.lower() or "6m" in display_name.lower():
                horizon = "6M"
            
            status_emoji = "🟢" if "RUNNING" in state_name or "PENDING" in state_name else "✅" if "SUCCEEDED" in state_name else "❌"
            
            logger.info(f"\n{i}. {status_emoji} {horizon} HORIZON:")
            logger.info(f"   Pipeline ID: {pipeline_id}")
            logger.info(f"   Display Name: {display_name}")
            logger.info(f"   State: {state_name}")
            logger.info(f"   Created: {create_time}")
            logger.info(f"   Console: https://console.cloud.google.com/ai/platform/locations/{region}/training/{pipeline_id}")
        
        # Training summary and next steps
        logger.info("\n" + "="*80)
        logger.info("📋 TRAINING SUMMARY:")
        
        horizons_running = set()
        horizons_completed = set()
        horizons_failed = set()
        
        for pipeline in recent_pipelines:
            display_name = pipeline.display_name or ""
            state_name = pipeline.state.name if pipeline.state else "UNKNOWN"
            
            if "_1w_" in display_name.lower() or "1w" in display_name.lower():
                horizon = "1W"
            elif "_1m_" in display_name.lower() or "1m" in display_name.lower():
                horizon = "1M"
            elif "_3m_" in display_name.lower() or "3m" in display_name.lower():
                horizon = "3M"
            elif "_6m_" in display_name.lower() or "6m" in display_name.lower():
                horizon = "6M"
            else:
                continue
            
            if "RUNNING" in state_name or "PENDING" in state_name:
                horizons_running.add(horizon)
            elif "SUCCEEDED" in state_name:
                horizons_completed.add(horizon)
            elif "FAILED" in state_name or "CANCELLED" in state_name:
                horizons_failed.add(horizon)
        
        logger.info(f"✅ COMPLETED: {', '.join(sorted(horizons_completed)) if horizons_completed else 'None'}")
        logger.info(f"🟢 RUNNING: {', '.join(sorted(horizons_running)) if horizons_running else 'None'}")
        logger.info(f"❌ FAILED: {', '.join(sorted(horizons_failed)) if horizons_failed else 'None'}")
        
        # Next steps recommendation
        all_horizons = {"1W", "1M", "3M", "6M"}
        not_started = all_horizons - horizons_running - horizons_completed - horizons_failed
        
        if not_started:
            logger.info(f"\n🎯 NEXT STEPS:")
            logger.info(f"   Need to start: {', '.join(sorted(not_started))}")
            
            if "6M" in horizons_completed:
                if "3M" not in horizons_running and "3M" not in horizons_completed:
                    logger.info(f"   ➡️  Launch 3M next (6M complete)")
                elif "1M" not in horizons_running and "1M" not in horizons_completed:
                    logger.info(f"   ➡️  Launch 1M next (after 3M)")
        else:
            logger.info(f"\n✅ All horizons have been started!")
        
        return {
            "running": list(horizons_running),
            "completed": list(horizons_completed),
            "failed": list(horizons_failed),
            "pipelines": recent_pipelines
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking training status: {str(e)}")
        return None

if __name__ == "__main__":
    status = check_training_status()
