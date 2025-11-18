#!/usr/bin/env python3
"""
NIGHTLY PIPELINE WATCHDOG
Monitors the nightly training pipeline and recovers from failures.

Runs every hour to:
1. Check if last run completed successfully
2. Check if last run was >24 hours ago (missed run)
3. Retry failed runs
4. Alert on persistent failures

This is a fail-safe that ensures training never stops, even if:
- Mac was asleep
- Pipeline crashed
- System rebooted
- Disk was full
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# Environment setup
REPO_ROOT = Path(__file__).parent.parent.resolve()
LOGS_DIR = REPO_ROOT / "Logs" / "nightly"
WATCHDOG_LOG = LOGS_DIR / "watchdog.log"
STATUS_FILE = LOGS_DIR / "last_run_status.json"
PIPELINE_SCRIPT = REPO_ROOT / "scripts" / "run_nightly_pipeline.py"

# Python executable
PYTHON = sys.executable

# Configuration
MAX_AGE_HOURS = 26  # If last run is >26 hours old, trigger new run
MAX_RETRIES = 2     # Maximum automatic retries before human intervention


class Watchdog:
    """Pipeline health monitor and recovery system."""
    
    def __init__(self):
        self.now = datetime.now()
        self.log_file = WATCHDOG_LOG
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to watchdog log."""
        timestamp = self.now.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        print(log_line)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_line + "\n")
        except Exception as e:
            print(f"⚠️  Could not write to log: {e}")
    
    def check_health(self) -> dict:
        """
        Check pipeline health and return status.
        
        Returns:
            dict with keys: healthy, reason, action_needed
        """
        # Check if status file exists
        if not STATUS_FILE.exists():
            self.log("⚠️  No status file found - pipeline never run", "WARN")
            return {
                "healthy": False,
                "reason": "never_run",
                "action_needed": "run_pipeline"
            }
        
        # Load status
        try:
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)
        except Exception as e:
            self.log(f"❌ Could not read status file: {e}", "ERROR")
            return {
                "healthy": False,
                "reason": "status_file_corrupt",
                "action_needed": "run_pipeline"
            }
        
        # Parse timestamps
        try:
            last_run_time = datetime.fromisoformat(status['start_time'])
            age_hours = (self.now - last_run_time).total_seconds() / 3600
        except Exception as e:
            self.log(f"❌ Could not parse timestamp: {e}", "ERROR")
            return {
                "healthy": False,
                "reason": "timestamp_error",
                "action_needed": "run_pipeline"
            }
        
        # Check age
        if age_hours > MAX_AGE_HOURS:
            self.log(f"⚠️  Last run was {age_hours:.1f} hours ago (>24h)", "WARN")
            return {
                "healthy": False,
                "reason": "missed_run",
                "action_needed": "run_pipeline",
                "age_hours": age_hours
            }
        
        # Check success
        if not status.get('success', False):
            self.log(f"❌ Last run failed at stage: {status.get('failed_stage', 'unknown')}", "ERROR")
            
            # Count recent failures
            failure_count = self._count_recent_failures()
            
            if failure_count >= MAX_RETRIES:
                self.log(f"🚨 {failure_count} consecutive failures - HUMAN INTERVENTION NEEDED", "ERROR")
                return {
                    "healthy": False,
                    "reason": "persistent_failure",
                    "action_needed": "alert",
                    "failure_count": failure_count
                }
            else:
                self.log(f"⚠️  Failure #{failure_count} - will retry", "WARN")
                return {
                    "healthy": False,
                    "reason": "recent_failure",
                    "action_needed": "retry_pipeline",
                    "failure_count": failure_count
                }
        
        # All good
        self.log(f"✅ Pipeline healthy - last run {age_hours:.1f}h ago", "INFO")
        return {
            "healthy": True,
            "reason": "success",
            "action_needed": "none",
            "age_hours": age_hours
        }
    
    def _count_recent_failures(self) -> int:
        """Count consecutive failures in recent run history."""
        # Look for recent run logs
        if not LOGS_DIR.exists():
            return 0
        
        # Get all nightly pipeline logs, sorted by time (newest first)
        log_files = sorted(
            LOGS_DIR.glob("nightly_pipeline_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        failure_count = 0
        
        # Check last N runs
        for log_file in log_files[:5]:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                if "COMPLETED SUCCESSFULLY" in content:
                    # Success found - stop counting
                    break
                elif "CRITICAL FAILURE" in content or "PIPELINE EXCEPTION" in content:
                    failure_count += 1
            except Exception:
                pass
        
        return failure_count
    
    def trigger_pipeline(self):
        """Trigger a new pipeline run."""
        self.log("🔄 Triggering pipeline run...", "INFO")
        
        try:
            # Run pipeline (detached - don't wait for completion)
            subprocess.Popen(
                [PYTHON, str(PIPELINE_SCRIPT)],
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            self.log("✅ Pipeline triggered successfully", "INFO")
            return True
            
        except Exception as e:
            self.log(f"❌ Could not trigger pipeline: {e}", "ERROR")
            return False
    
    def send_alert(self, health_status: dict):
        """Send alert for persistent failures."""
        self.log("="*80, "ERROR")
        self.log("🚨 ALERT: PIPELINE REQUIRES HUMAN INTERVENTION", "ERROR")
        self.log("="*80, "ERROR")
        self.log(f"Reason: {health_status['reason']}", "ERROR")
        self.log(f"Failure count: {health_status.get('failure_count', 'unknown')}", "ERROR")
        self.log("", "ERROR")
        self.log("Actions:", "ERROR")
        self.log("1. Check logs in: Logs/nightly/", "ERROR")
        self.log("2. Review last_run_status.json", "ERROR")
        self.log("3. Manually run: python scripts/run_nightly_pipeline.py", "ERROR")
        self.log("4. Check disk space, BigQuery connection, and system resources", "ERROR")
        self.log("="*80, "ERROR")
        
        # TODO: Send email/Slack notification
        # For now, just log prominently
    
    def run(self):
        """Main watchdog check."""
        self.log("="*80)
        self.log("🐕 WATCHDOG CHECK")
        self.log("="*80)
        
        # Check health
        health = self.check_health()
        
        # Take action
        if health["action_needed"] == "run_pipeline":
            self.log(f"Action: Triggering pipeline (reason: {health['reason']})")
            self.trigger_pipeline()
            
        elif health["action_needed"] == "retry_pipeline":
            self.log(f"Action: Retrying pipeline (attempt #{health['failure_count'] + 1})")
            self.trigger_pipeline()
            
        elif health["action_needed"] == "alert":
            self.send_alert(health)
            
        elif health["action_needed"] == "none":
            self.log("Action: None - system healthy")
        
        self.log("="*80)
        self.log("")


def main():
    """Entry point for watchdog."""
    watchdog = Watchdog()
    watchdog.run()
    sys.exit(0)


if __name__ == "__main__":
    main()



