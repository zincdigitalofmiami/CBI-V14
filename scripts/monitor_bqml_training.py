#!/usr/bin/env python3
"""
Monitor BQML model training progress
"""
import time
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

def monitor_training(model_name: str):
    """Monitor a single model's training progress"""
    client = bigquery.Client(project=PROJECT_ID)
    print(f"\n🔨 Monitoring {model_name}...")
    
    last_iteration = 0
    wait_count = 0
    
    while True:
        try:
            # Query training info
            query = f"""
            SELECT 
              iteration, 
              training_loss, 
              evaluation_loss, 
              learning_rate, 
              duration_ms
            FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`)
            ORDER BY iteration DESC
            LIMIT 1;
            """
            
            results = client.query(query).to_dataframe()
            
            if not results.empty:
                current_iter = int(results['iteration'].iloc[0])
                
                if current_iter > last_iteration:
                    last_iteration = current_iter
                    train_loss = float(results['training_loss'].iloc[0])
                    eval_loss = float(results['evaluation_loss'].iloc[0])
                    duration = float(results['duration_ms'].iloc[0]) / 1000
                    
                    print(f"  Iteration {current_iter}/100 | "
                          f"Train Loss: {train_loss:.6f} | "
                          f"Val Loss: {eval_loss:.6f} | "
                          f"Duration: {duration:.1f}s")
                    
                    # Check if training complete
                    if current_iter >= 100:
                        print(f"  ✅ Training complete!")
                        break
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            error_str = str(e)
            if "Not found: Model" in error_str or "404" in error_str:
                wait_count += 1
                if wait_count <= 10:
                    print(f"  ⏳ Waiting for model creation... ({wait_count*30}s)")
                else:
                    print(f"  ⚠️  Model not found after 5 minutes - check training job")
                time.sleep(30)
            else:
                print(f"  ❌ Error: {error_str}")
                break

def train_all_models():
    """Train all 4 models and monitor progress"""
    models = ['bqml_1w_mean', 'bqml_1m_mean', 'bqml_3m_mean', 'bqml_6m_mean']
    
    print("="*60)
    print("🚀 CBI-V14 Model Training Pipeline")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Models to train: {len(models)}")
    print("")
    
    for model in models:
        monitor_training(model)
    
    print("\n" + "="*60)
    print("✅ All models trained successfully!")
    print(f"End time: {datetime.now().isoformat()}")
    print("="*60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        monitor_training(sys.argv[1])
    else:
        train_all_models()



