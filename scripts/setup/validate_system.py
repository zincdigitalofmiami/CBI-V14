#!/usr/bin/env python3
"""
SYSTEM VALIDATION SCRIPT
Validates that the autonomous training system is properly configured.

Checks:
1. Power management settings
2. LaunchDaemon installation
3. Required files and directories
4. Python environment
5. BigQuery connectivity
6. Disk space

Run this after installation to verify everything is working.
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RESET = '\033[0m'

def colored(text: str, color: str) -> str:
    """Return colored text."""
    return f"{color}{text}{RESET}"

class SystemValidator:
    """Validates autonomous training system configuration."""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent.resolve()
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warning = 0
    
    def check(self, name: str, passed: bool, details: str = "", warning: bool = False):
        """Record a check result."""
        if passed:
            self.checks_passed += 1
            print(f"{colored('✅', GREEN)} {name}")
            if details:
                print(f"   {details}")
        elif warning:
            self.checks_warning += 1
            print(f"{colored('⚠️ ', YELLOW)} {name}")
            if details:
                print(f"   {details}")
        else:
            self.checks_failed += 1
            print(f"{colored('❌', RED)} {name}")
            if details:
                print(f"   {details}")
    
    def validate_python_environment(self):
        """Check Python version and required packages."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[1] Python Environment', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        # Python version
        python_version = sys.version.split()[0]
        major, minor = map(int, python_version.split('.')[:2])
        self.check(
            "Python version",
            major == 3 and minor >= 9,
            f"Version: {python_version} (requires 3.9+)"
        )
        
        # Required packages
        required_packages = [
            'pandas',
            'numpy',
            'polars',
            'lightgbm',
            'xgboost',
            'google.cloud.bigquery',
            'mlflow'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.check(f"Package: {package}", True)
            except ImportError:
                self.check(f"Package: {package}", False, "Not installed", warning=True)
    
    def validate_files_and_directories(self):
        """Check required files and directories exist."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[2] Files and Directories', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        required_files = [
            "scripts/run_nightly_pipeline.py",
            "scripts/watchdog.py",
            "scripts/export_training_data.py",
            "scripts/data_quality_checks.py",
            "scripts/upload_predictions.py",
            "src/training/baselines/tree_models.py",
            "src/prediction/generate_local_predictions.py"
        ]
        
        for file_path in required_files:
            full_path = self.repo_root / file_path
            exists = full_path.exists()
            executable = os.access(full_path, os.X_OK) if exists else False
            
            self.check(
                f"File: {file_path}",
                exists,
                f"Executable: {executable}" if exists else "Missing"
            )
        
        # Directories
        required_dirs = [
            "Logs/nightly",
            "TrainingData/exports",
            "Models/local",
        ]
        
        for dir_path in required_dirs:
            full_path = self.repo_root / dir_path
            self.check(f"Directory: {dir_path}", full_path.exists())
    
    def validate_power_management(self):
        """Check power management configuration."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[3] Power Management', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        # Check wake schedule
        try:
            result = subprocess.run(
                ['pmset', '-g', 'sched'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                schedule = result.stdout
                has_wake_schedule = 'wake' in schedule.lower() or 'poweron' in schedule.lower()
                
                self.check(
                    "Wake schedule configured",
                    has_wake_schedule,
                    schedule.strip() if has_wake_schedule else "No wake schedule found",
                    warning=not has_wake_schedule
                )
            else:
                self.check("Wake schedule", False, "Could not check pmset", warning=True)
                
        except Exception as e:
            self.check("Wake schedule", False, f"Error: {e}", warning=True)
        
        # Check current power settings
        try:
            result = subprocess.run(
                ['pmset', '-g'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.check("Power settings readable", True, "Use 'pmset -g' to view")
            else:
                self.check("Power settings", False, "Could not read", warning=True)
                
        except Exception as e:
            self.check("Power settings", False, f"Error: {e}", warning=True)
    
    def validate_launch_daemons(self):
        """Check LaunchDaemon installation."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[4] LaunchDaemons', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        daemons = [
            ('com.cbi.nightly', '/Library/LaunchDaemons/com.cbi.nightly.plist'),
            ('com.cbi.watchdog', '/Library/LaunchDaemons/com.cbi.watchdog.plist')
        ]
        
        for label, plist_path in daemons:
            # Check file exists
            exists = Path(plist_path).exists()
            self.check(f"Daemon file: {label}", exists, plist_path)
            
            if exists:
                # Check if loaded
                try:
                    result = subprocess.run(
                        ['sudo', 'launchctl', 'list'],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        loaded = label in result.stdout
                        self.check(
                            f"Daemon loaded: {label}",
                            True,
                            "Loaded and active" if loaded else "Not currently running (will start on schedule)",
                            warning=not loaded
                        )
                except Exception as e:
                    self.check(f"Daemon status: {label}", False, f"Error: {e}", warning=True)
    
    def validate_bigquery_connection(self):
        """Check BigQuery connectivity."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[5] BigQuery Connection', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        # Check credentials
        gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.check(
            "GOOGLE_APPLICATION_CREDENTIALS",
            gcp_creds is not None,
            f"Path: {gcp_creds}" if gcp_creds else "Not set",
            warning=gcp_creds is None
        )
        
        # Try to import and connect
        try:
            from google.cloud import bigquery
            
            project_id = os.getenv("PROJECT", "cbi-v14")
            client = bigquery.Client(project=project_id)
            
            # Try a simple query
            query = "SELECT 1 as test"
            result = client.query(query).result()
            
            self.check("BigQuery connectivity", True, f"Connected to project: {project_id}")
            
        except Exception as e:
            self.check("BigQuery connectivity", False, f"Error: {e}", warning=True)
    
    def validate_disk_space(self):
        """Check available disk space."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[6] Disk Space', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        try:
            result = subprocess.run(
                ['df', '-h', str(self.repo_root)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # Parse df output
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        size = parts[1]
                        used = parts[2]
                        avail = parts[3]
                        percent = parts[4]
                        
                        # Check if at least 10GB available
                        avail_value = avail.replace('Gi', '').replace('G', '')
                        try:
                            avail_gb = float(avail_value)
                            has_space = avail_gb >= 10
                            
                            self.check(
                                "Disk space",
                                has_space,
                                f"Available: {avail} (Total: {size}, Used: {used} {percent})",
                                warning=not has_space
                            )
                        except:
                            self.check("Disk space", True, f"Available: {avail}")
                    else:
                        self.check("Disk space", True, "Could not parse output", warning=True)
        except Exception as e:
            self.check("Disk space", False, f"Error: {e}", warning=True)
    
    def validate_logs(self):
        """Check recent logs."""
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('[7] Recent Activity', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        logs_dir = self.repo_root / "Logs" / "nightly"
        
        if not logs_dir.exists():
            self.check("Logs directory", False, "Directory does not exist")
            return
        
        # Check for status file
        status_file = logs_dir / "last_run_status.json"
        if status_file.exists():
            import json
            try:
                with open(status_file) as f:
                    status = json.load(f)
                
                last_run = datetime.fromisoformat(status.get('start_time', ''))
                age_hours = (datetime.now() - last_run).total_seconds() / 3600
                
                self.check(
                    "Last pipeline run",
                    True,
                    f"{age_hours:.1f} hours ago - {'SUCCESS' if status.get('success') else 'FAILED'}"
                )
            except Exception as e:
                self.check("Last pipeline run", False, f"Could not read status: {e}", warning=True)
        else:
            self.check("Last pipeline run", False, "Never run", warning=True)
        
        # Check for recent logs
        recent_logs = sorted(logs_dir.glob("nightly_pipeline_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if recent_logs:
            latest_log = recent_logs[0]
            age_hours = (datetime.now().timestamp() - latest_log.stat().st_mtime) / 3600
            
            self.check(
                "Recent log files",
                True,
                f"Latest: {latest_log.name} ({age_hours:.1f}h ago)"
            )
        else:
            self.check("Recent log files", False, "No logs found", warning=True)
    
    def run(self):
        """Run all validations."""
        print("")
        print(colored("="*80, BLUE))
        print(colored("🔍 AUTONOMOUS SYSTEM VALIDATION", BLUE))
        print(colored("="*80, BLUE))
        print(f"Repository: {self.repo_root}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.validate_python_environment()
        self.validate_files_and_directories()
        self.validate_power_management()
        self.validate_launch_daemons()
        self.validate_bigquery_connection()
        self.validate_disk_space()
        self.validate_logs()
        
        # Summary
        print(f"\n{colored('='*80, BLUE)}")
        print(f"{colored('VALIDATION SUMMARY', BLUE)}")
        print(f"{colored('='*80, BLUE)}\n")
        
        total_checks = self.checks_passed + self.checks_failed + self.checks_warning
        
        print(f"{colored('✅', GREEN)} Passed:   {self.checks_passed}/{total_checks}")
        print(f"{colored('⚠️ ', YELLOW)} Warnings: {self.checks_warning}/{total_checks}")
        print(f"{colored('❌', RED)} Failed:   {self.checks_failed}/{total_checks}")
        print()
        
        if self.checks_failed == 0 and self.checks_warning == 0:
            print(f"{colored('🎉 SYSTEM READY - All checks passed!', GREEN)}")
            print()
            return True
        elif self.checks_failed == 0:
            print(f"{colored('⚠️  SYSTEM MOSTLY READY - Review warnings', YELLOW)}")
            print()
            return True
        else:
            print(f"{colored('🚨 SYSTEM NOT READY - Fix errors before proceeding', RED)}")
            print()
            return False


def main():
    """Entry point."""
    validator = SystemValidator()
    success = validator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()







