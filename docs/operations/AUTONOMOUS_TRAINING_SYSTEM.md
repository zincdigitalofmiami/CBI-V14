---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Autonomous Training System for Mac M4

## Overview

This is the complete autonomous training infrastructure for CBI-V14. It transforms your Mac M4 into a self-governing quant workstation that:

- ✅ Wakes itself every night at 23:59
- ✅ Runs complete training pipeline at 00:00 (midnight)
- ✅ Stays awake during training (no interruptions)
- ✅ Monitors its own health (hourly watchdog)
- ✅ Recovers from failures automatically
- ✅ Runs whether Cursor is alive or dead
- ✅ Survives reboots, sleep, and updates

**This system requires ZERO human intervention once installed.**

---

## Architecture

### Components

1. **Master Pipeline** (`scripts/run_nightly_pipeline.py`)
   - Orchestrates entire nightly workflow
   - Exports data → Audits → Training → Predictions → Upload → Evaluation
   - Logs everything, retries on failure
   - Exit codes and status tracking

2. **Watchdog** (`scripts/watchdog.py`)
   - Runs every hour
   - Checks for missed runs, failures, corrupted state
   - Triggers catch-up runs automatically
   - Alerts on persistent failures

3. **LaunchDaemons** (macOS native)
   - `com.cbi.nightly`: Triggers pipeline at midnight
   - `com.cbi.watchdog`: Runs watchdog hourly
   - Survives: sleep, reboots, logouts, updates

4. **Power Management**
   - Scheduled wake: 23:59 every night
   - caffeinate: Prevents sleep during training
   - OS-level, independent of applications

### Why LaunchDaemons (Not Cron)?

Cron has limitations on macOS:
- Doesn't survive sleep
- Unreliable after reboot
- Network changes can break it
- No guaranteed execution after wake

LaunchDaemons are native macOS schedulers:
- OS-level, not user-level
- Survive sleep, reboots, network changes
- Can wake the system (with power schedule)
- Apple-recommended for background tasks

---

## Installation

### Prerequisites

- macOS (M4 Mac recommended)
- Python 3.9+
- Google Cloud credentials configured
- sudo access (for LaunchDaemon installation)

### Automated Installation

```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
./scripts/setup/install_autonomous_system.sh
```

This will:
1. Validate prerequisites
2. Configure power management (wake schedule)
3. Create directories
4. Install LaunchDaemons
5. Make scripts executable
6. Run validation tests

### Manual Installation

If you prefer manual setup:

```bash
# 1. Configure wake schedule
sudo pmset schedule wakeorpoweron MTWRFSU 23:59:00

# 2. Install LaunchDaemons
sudo cp config/system/com.cbi.nightly.plist /Library/LaunchDaemons/
sudo cp config/system/com.cbi.watchdog.plist /Library/LaunchDaemons/

# 3. Set permissions
sudo chown root:wheel /Library/LaunchDaemons/com.cbi.*.plist
sudo chmod 644 /Library/LaunchDaemons/com.cbi.*.plist

# 4. Load daemons
sudo launchctl load /Library/LaunchDaemons/com.cbi.nightly.plist
sudo launchctl load /Library/LaunchDaemons/com.cbi.watchdog.plist

# 5. Verify
sudo launchctl list | grep com.cbi
```

---

## Validation

After installation, validate the system:

```bash
python3 scripts/setup/validate_system.py
```

This checks:
- Python environment and packages
- Required files and directories
- Power management configuration
- LaunchDaemon installation
- BigQuery connectivity
- Disk space
- Recent activity

---

## Operation

### Normal Operation

Once installed, the system runs automatically:

```
23:59 → Mac wakes (pmset schedule)
00:00 → Nightly pipeline starts (LaunchDaemon)
00:00-02:00 → Training runs (caffeinate keeps Mac awake)
Every hour → Watchdog checks health
```

### What the Nightly Pipeline Does

1. **Export Training Data** (15-30 min)
   - Pulls latest data from BigQuery
   - All 5 horizons: 1w, 1m, 3m, 6m, 12m
   - Saves to `TrainingData/exports/`

2. **Data Quality Checks** (2-5 min)
   - Validates data freshness
   - Checks for nulls, gaps, schema issues
   - Stops if critical errors found

3. **Train Models** (30-60 min)
   - LightGBM DART for each horizon
   - XGBoost DART for each horizon
   - Saves to `Models/local/horizon_{h}/`

4. **Generate Predictions** (5-10 min)
   - Uses best model per horizon
   - Creates predictions for latest date

5. **Upload to BigQuery** (5-10 min)
   - Uploads predictions to `predictions` dataset
   - Creates/updates views for dashboard

6. **Evaluation** (5 min)
   - MAPE calculation
   - Sharpe ratio calculation
   - Logs metrics

**Total duration: ~1-2 hours**

### What the Watchdog Does

Every hour:

1. Check if last run completed successfully
2. Check if last run was >26 hours ago (missed)
3. If failure or missed → trigger new run
4. If persistent failures (>2) → alert for human intervention
5. Log status

---

## Monitoring

### Check System Status

```bash
# View LaunchDaemon status
sudo launchctl list | grep com.cbi

# View power schedule
pmset -g sched

# View power settings
pmset -g

# Check last run status
cat Logs/nightly/last_run_status.json | python3 -m json.tool
```

### View Logs

```bash
# Latest pipeline run
tail -f Logs/nightly/nightly_pipeline_$(ls -t Logs/nightly/nightly_pipeline_* | head -1 | xargs basename)

# Watchdog log
tail -f Logs/nightly/watchdog.log

# LaunchDaemon output
cat Logs/nightly/daemon_stdout.log
cat Logs/nightly/daemon_stderr.log
```

### Check Recent Activity

```bash
# List recent pipeline runs
ls -lht Logs/nightly/nightly_pipeline_*.log | head -5

# Check success/failure
grep -l "COMPLETED SUCCESSFULLY" Logs/nightly/nightly_pipeline_*.log | wc -l
grep -l "CRITICAL FAILURE" Logs/nightly/nightly_pipeline_*.log | wc -l
```

---

## Management

### Manual Pipeline Run

Test the pipeline manually:

```bash
python3 scripts/run_nightly_pipeline.py
```

This runs the complete pipeline immediately (useful for testing).

### Stop/Start Daemons

```bash
# Stop nightly pipeline
sudo launchctl unload /Library/LaunchDaemons/com.cbi.nightly.plist

# Stop watchdog
sudo launchctl unload /Library/LaunchDaemons/com.cbi.watchdog.plist

# Start nightly pipeline
sudo launchctl load /Library/LaunchDaemons/com.cbi.nightly.plist

# Start watchdog
sudo launchctl load /Library/LaunchDaemons/com.cbi.watchdog.plist
```

### Modify Schedule

To change the nightly run time, edit the plist:

```bash
sudo nano /Library/LaunchDaemons/com.cbi.nightly.plist
```

Find:
```xml
<key>StartCalendarInterval</key>
<dict>
  <key>Hour</key>
  <integer>0</integer>  <!-- Change this -->
  <key>Minute</key>
  <integer>0</integer>  <!-- And this -->
</dict>
```

Then reload:
```bash
sudo launchctl unload /Library/LaunchDaemons/com.cbi.nightly.plist
sudo launchctl load /Library/LaunchDaemons/com.cbi.nightly.plist
```

### Update Wake Schedule

```bash
# Wake at different time
sudo pmset schedule wakeorpoweron MTWRFSU 23:30:00

# Verify
pmset -g sched
```

---

## Troubleshooting

### Pipeline Not Running

**Symptom:** Last run is >24 hours old

**Check:**
```bash
# Is daemon loaded?
sudo launchctl list | grep com.cbi.nightly

# Are there errors in logs?
cat Logs/nightly/daemon_stderr.log

# Test manual run
python3 scripts/run_nightly_pipeline.py
```

**Fix:**
```bash
# Reload daemon
sudo launchctl unload /Library/LaunchDaemons/com.cbi.nightly.plist
sudo launchctl load /Library/LaunchDaemons/com.cbi.nightly.plist
```

### Mac Not Waking

**Symptom:** Pipeline runs only when Mac is already on

**Check:**
```bash
pmset -g sched
```

**Fix:**
```bash
# Re-set wake schedule
sudo pmset schedule wakeorpoweron MTWRFSU 23:59:00

# Verify
pmset -g sched
```

### Training Interrupted by Sleep

**Symptom:** Logs show incomplete runs, Mac went to sleep mid-training

**Check:**
```bash
# View power settings
pmset -g

# Check if caffeinate is in daemon
grep caffeinate /Library/LaunchDaemons/com.cbi.nightly.plist
```

**Fix:**
- Ensure the daemon uses `caffeinate` (it should by default)
- Check energy saver settings: System Preferences → Battery → Prevent sleeping when display is off

### BigQuery Upload Failing

**Symptom:** Pipeline succeeds but no predictions in BigQuery

**Check:**
```bash
# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(); print('OK')"

# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
```

**Fix:**
```bash
# Set credentials in daemon plist
sudo nano /Library/LaunchDaemons/com.cbi.nightly.plist

# Add to EnvironmentVariables dict:
<key>GOOGLE_APPLICATION_CREDENTIALS</key>
<string>/path/to/credentials.json</string>
```

### Watchdog Not Recovering

**Symptom:** Failures persist, watchdog doesn't trigger retry

**Check:**
```bash
# Is watchdog running?
sudo launchctl list | grep com.cbi.watchdog

# Check watchdog log
tail -20 Logs/nightly/watchdog.log
```

**Fix:**
```bash
# Reload watchdog
sudo launchctl unload /Library/LaunchDaemons/com.cbi.watchdog.plist
sudo launchctl load /Library/LaunchDaemons/com.cbi.watchdog.plist
```

### Disk Space Full

**Symptom:** Pipeline fails with "No space left"

**Check:**
```bash
df -h .
du -sh Models/ TrainingData/ Logs/
```

**Fix:**
```bash
# Clean old logs (keep last 30 days)
find Logs/nightly -name "*.log" -mtime +30 -delete

# Clean old models (keep last 7 days)
find Models/local -name "*.bin" -mtime +7 -delete

# Clean old training exports (regenerated nightly)
rm -f TrainingData/exports/*.parquet
```

---

## Uninstallation

To completely remove the autonomous system:

```bash
# 1. Unload daemons
sudo launchctl unload /Library/LaunchDaemons/com.cbi.nightly.plist
sudo launchctl unload /Library/LaunchDaemons/com.cbi.watchdog.plist

# 2. Remove daemon files
sudo rm /Library/LaunchDaemons/com.cbi.nightly.plist
sudo rm /Library/LaunchDaemons/com.cbi.watchdog.plist

# 3. Remove wake schedule
sudo pmset schedule cancelall

# 4. (Optional) Remove logs
rm -rf Logs/nightly
```

---

## Advanced Configuration

### Run Multiple Times Per Day

Edit the plist to include multiple intervals:

```xml
<key>StartCalendarInterval</key>
<array>
  <dict>
    <key>Hour</key>
    <integer>0</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <dict>
    <key>Hour</key>
    <integer>12</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
</array>
```

### Custom Python Environment

If using a virtual environment:

```xml
<key>ProgramArguments</key>
<array>
  <string>/usr/bin/caffeinate</string>
  <string>-dims</string>
  <string>/path/to/venv/bin/python3</string>
  <string>/Users/kirkmusick/Documents/GitHub/CBI-V14/scripts/run_nightly_pipeline.py</string>
</array>
```

### Email Alerts on Failure

Modify `watchdog.py` to send emails:

```python
def send_alert(self, health_status: dict):
    # Add email sending logic here
    import smtplib
    # ... implementation
```

---

## FAQ

**Q: Will this work if my Mac is on battery?**
A: Yes, but battery settings may prevent wake. Best to keep plugged in.

**Q: What if I'm traveling and Mac is closed/unplugged?**
A: Watchdog will detect missed run and trigger catch-up when next awake.

**Q: Can I run this on an external drive?**
A: Yes, but ensure the drive is always mounted.

**Q: Will this interfere with other work?**
A: No - runs at midnight and uses only available resources (8-10 threads).

**Q: How much disk space needed?**
A: ~10-20GB for models, data, and logs (auto-cleans old files).

**Q: What if BigQuery is down?**
A: Pipeline fails gracefully, watchdog retries on next hour.

---

## Status Dashboard

You can monitor the system status programmatically:

```python
import json
from pathlib import Path

status_file = Path("Logs/nightly/last_run_status.json")

if status_file.exists():
    with open(status_file) as f:
        status = json.load(f)
    
    print(f"Last run: {status['start_time']}")
    print(f"Success: {status['success']}")
    print(f"Stages: {len(status['stages'])}")
    
    for stage in status['stages']:
        print(f"  {stage['name']}: {'✅' if stage['success'] else '❌'}")
```

---

## Support

**Logs:** `Logs/nightly/`
**Status:** `Logs/nightly/last_run_status.json`
**Validation:** `python3 scripts/setup/validate_system.py`

For issues, check logs first, then run validation script.

---

## Summary

Once installed, your Mac M4 is a fully autonomous quant training system:

✅ Self-waking
✅ Self-training  
✅ Self-monitoring  
✅ Self-healing  
✅ Self-logging  

**No human intervention required.**

Welcome to the future of autonomous ML operations.







