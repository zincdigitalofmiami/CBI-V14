#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
MASTER NIGHTLY PIPELINE ORCHESTRATOR
Runs the complete CBI-V14 training pipeline every night at midnight.

This script is called by the macOS LaunchDaemon and orchestrates:
1. Data export from BigQuery
2. Pre-flight audits
3. Model training (all horizons)
4. Prediction generation
5. BigQuery upload
6. Evaluation (MAPE + Sharpe)
7. Logging and error recovery

This script is designed to run autonomously, every night, without human intervention.
"""
import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import time

# Environment setup
REPO_ROOT = Path(__file__).parent.parent.resolve()
LOGS_DIR = REPO_ROOT / "Logs" / "nightly"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for this run
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_LOG = LOGS_DIR / f"nightly_pipeline_{RUN_TIMESTAMP}.log"
RUN_STATUS_FILE = LOGS_DIR / "last_run_status.json"

# Python executable (use current environment)
PYTHON = sys.executable

# Horizons to train
HORIZONS = ["1w", "1m", "3m", "6m", "12m"]


class PipelineLogger:
    """Dual logger: file + stdout"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """Log message to both file and stdout."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        # Print to stdout
        print(log_line)
        
        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(log_line + "\n")
    
    def info(self, message: str):
        self.log(message, "INFO")
    
    def warning(self, message: str):
        self.log(message, "WARN")
    
    def error(self, message: str):
        self.log(message, "ERROR")
    
    def success(self, message: str):
        self.log(message, "SUCCESS")


class PipelineStage:
    """Individual pipeline stage with timing and error tracking."""
    
    def __init__(self, name: str, logger: PipelineLogger):
        self.name = name
        self.logger = logger
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error_message = None
        self.retries = 0
        self.max_retries = 1
    
    def run(self, command: List[str], critical: bool = True) -> bool:
        """
        Run a command as a pipeline stage.
        
        Args:
            command: Command to run as list
            critical: If True, pipeline stops on failure. If False, continues.
        
        Returns:
            True if successful, False otherwise
        """
        self.start_time = datetime.now()
        
        self.logger.info("="*80)
        self.logger.info(f"STAGE: {self.name}")
        self.logger.info("="*80)
        self.logger.info(f"Command: {' '.join(command)}")
        self.logger.info("")
        
        while self.retries <= self.max_retries:
            try:
                result = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour max per stage
                )
                
                # Log output
                if result.stdout:
                    self.logger.info(result.stdout)
                
                if result.returncode == 0:
                    self.success = True
                    self.end_time = datetime.now()
                    duration = (self.end_time - self.start_time).total_seconds()
                    self.logger.success(f"✅ {self.name} completed in {duration:.1f}s")
                    return True
                else:
                    # Command failed
                    self.error_message = result.stderr if result.stderr else "Unknown error"
                    self.logger.error(f"❌ {self.name} failed (exit code {result.returncode})")
                    self.logger.error(f"Error: {self.error_message}")
                    
                    if self.retries < self.max_retries:
                        self.retries += 1
                        self.logger.warning(f"🔄 Retrying ({self.retries}/{self.max_retries})...")
                        time.sleep(5)
                        continue
                    else:
                        self.end_time = datetime.now()
                        if critical:
                            self.logger.error(f"🚨 CRITICAL FAILURE - Pipeline stopped")
                            return False
                        else:
                            self.logger.warning(f"⚠️  Non-critical failure - continuing")
                            return False
                            
            except subprocess.TimeoutExpired:
                self.error_message = "Command timed out (>1 hour)"
                self.logger.error(f"❌ {self.name} timed out")
                
                if self.retries < self.max_retries:
                    self.retries += 1
                    self.logger.warning(f"🔄 Retrying ({self.retries}/{self.max_retries})...")
                    time.sleep(5)
                    continue
                else:
                    self.end_time = datetime.now()
                    return False
                    
            except Exception as e:
                self.error_message = str(e)
                self.logger.error(f"❌ {self.name} exception: {e}")
                self.logger.error(traceback.format_exc())
                self.end_time = datetime.now()
                return False
        
        return False
    
    def to_dict(self) -> Dict:
        """Export stage status to dict."""
        return {
            "name": self.name,
            "success": self.success,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            "error": self.error_message,
            "retries": self.retries
        }


class NightlyPipeline:
    """Complete nightly training pipeline orchestrator."""
    
    def __init__(self):
        self.logger = PipelineLogger(RUN_LOG)
        self.stages = []
        self.start_time = datetime.now()
        self.end_time = None
        self.overall_success = False
        
    def run(self):
        """Run the complete pipeline."""
        self.logger.info("="*80)
        self.logger.info("🌙 CBI-V14 NIGHTLY TRAINING PIPELINE")
        self.logger.info("="*80)
        self.logger.info(f"Run ID: {RUN_TIMESTAMP}")
        self.logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Repository: {REPO_ROOT}")
        self.logger.info(f"Python: {PYTHON}")
        self.logger.info("")
        
        try:
            # Stage 1: Export training data
            if not self._export_training_data():
                self._save_status(success=False, failed_stage="export")
                return False
            
            # Stage 2: Data quality checks
            if not self._run_data_quality_checks():
                self._save_status(success=False, failed_stage="quality_checks")
                return False
            
            # Stage 3: Train models (all horizons)
            if not self._train_all_models():
                self._save_status(success=False, failed_stage="training")
                return False
            
            # Stage 4: Generate predictions
            if not self._generate_predictions():
                self._save_status(success=False, failed_stage="predictions")
                return False
            
            # Stage 5: Upload to BigQuery
            if not self._upload_predictions():
                self._save_status(success=False, failed_stage="upload")
                return False
            
            # Stage 6: Evaluation (non-critical)
            self._run_evaluations()
            
            # Complete
            self.end_time = datetime.now()
            self.overall_success = True
            self._save_status(success=True)
            
            self.logger.info("")
            self.logger.info("="*80)
            self.logger.success("🎉 NIGHTLY PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("="*80)
            total_duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"Total duration: {total_duration/60:.1f} minutes")
            self.logger.info("")
            
            return True
            
        except Exception as e:
            self.end_time = datetime.now()
            self.logger.error(f"🚨 PIPELINE EXCEPTION: {e}")
            self.logger.error(traceback.format_exc())
            self._save_status(success=False, failed_stage="exception", error=str(e))
            return False
    
    def _export_training_data(self) -> bool:
        """Export all training data from BigQuery."""
        stage = PipelineStage("Export Training Data", self.logger)
        
        command = [
            PYTHON,
            str(REPO_ROOT / "scripts" / "export_training_data.py"),
            "--horizon", "all",
            "--surface", "prod"
        ]
        
        success = stage.run(command, critical=True)
        self.stages.append(stage)
        return success
    
    def _run_data_quality_checks(self) -> bool:
        """Run comprehensive data quality audit."""
        stage = PipelineStage("Data Quality Checks", self.logger)
        
        command = [
            PYTHON,
            str(REPO_ROOT / "scripts" / "data_quality_checks.py"),
            "--horizon", "all"
        ]
        
        success = stage.run(command, critical=True)
        self.stages.append(stage)
        return success
    
    def _train_all_models(self) -> bool:
        """Train models for all horizons."""
        self.logger.info("")
        self.logger.info("="*80)
        self.logger.info("🌳 TRAINING MODELS - ALL HORIZONS")
        self.logger.info("="*80)
        self.logger.info("")
        
        all_success = True
        
        for horizon in HORIZONS:
            # Train tree models (LightGBM + XGBoost)
            stage = PipelineStage(f"Train Tree Models ({horizon})", self.logger)
            
            command = [
                PYTHON,
                str(REPO_ROOT / "src" / "training" / "baselines" / "tree_models.py"),
                "--horizon", horizon,
                "--surface", "prod"
            ]
            
            success = stage.run(command, critical=False)
            self.stages.append(stage)
            
            if not success:
                self.logger.warning(f"⚠️  Training failed for {horizon}, continuing with next horizon")
                all_success = False
        
        # At least some models must succeed
        successful_trainings = sum(1 for s in self.stages[-len(HORIZONS):] if s.success)
        
        if successful_trainings == 0:
            self.logger.error("❌ All training runs failed - cannot continue")
            return False
        elif successful_trainings < len(HORIZONS):
            self.logger.warning(f"⚠️  Only {successful_trainings}/{len(HORIZONS)} horizons trained successfully")
        else:
            self.logger.success(f"✅ All {len(HORIZONS)} horizons trained successfully")
        
        return True
    
    def _generate_predictions(self) -> bool:
        """Generate predictions using trained models."""
        stage = PipelineStage("Generate Predictions", self.logger)
        
        command = [
            PYTHON,
            str(REPO_ROOT / "src" / "prediction" / "generate_local_predictions.py"),
            "--horizon", "all"
        ]
        
        success = stage.run(command, critical=True)
        self.stages.append(stage)
        return success
    
    def _upload_predictions(self) -> bool:
        """Upload predictions to BigQuery."""
        stage = PipelineStage("Upload Predictions to BigQuery", self.logger)
        
        command = [
            PYTHON,
            str(REPO_ROOT / "scripts" / "upload_predictions.py")
        ]
        
        success = stage.run(command, critical=True)
        self.stages.append(stage)
        return success
    
    def _run_evaluations(self):
        """Run evaluation metrics (non-critical)."""
        self.logger.info("")
        self.logger.info("="*80)
        self.logger.info("📊 RUNNING EVALUATIONS")
        self.logger.info("="*80)
        self.logger.info("")
        
# REMOVED:         # Note: These scripts don't exist yet, so we'll create placeholders # NO FAKE DATA
        # that log warnings but don't fail
        
        self.logger.warning("⚠️  Evaluation scripts not yet implemented")
        self.logger.info("   - MAPE evaluation: TODO")
        self.logger.info("   - Sharpe evaluation: TODO")
        self.logger.info("")
    
    def _save_status(self, success: bool, failed_stage: str = None, error: str = None):
        """Save pipeline run status to JSON file."""
        status = {
            "run_id": RUN_TIMESTAMP,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else datetime.now().isoformat(),
            "success": success,
            "failed_stage": failed_stage,
            "error": error,
            "stages": [s.to_dict() for s in self.stages]
        }
        
        try:
            with open(RUN_STATUS_FILE, 'w') as f:
                json.dump(status, f, indent=2)
            
            self.logger.info(f"📝 Status saved to: {RUN_STATUS_FILE}")
        except Exception as e:
            self.logger.error(f"⚠️  Could not save status file: {e}")


def main():
    """Entry point for nightly pipeline."""
    pipeline = NightlyPipeline()
    success = pipeline.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()







