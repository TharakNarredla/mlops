"""
Retrain script: reads experiments/runs.json, checks if we should retrain
(time-based: retrain if last run was >= RETRAIN_AFTER_DAYS ago), and if so
runs src/train.py from project root.
"""
import json
import os
import subprocess
from datetime import datetime

# --- Project root (same pattern as train.py) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
path_to_runs = os.path.join(project_root, "experiments", "runs.json")

# --- Load runs and get last run ---
if not os.path.exists(path_to_runs):
    last_run = None
else:
    with open(path_to_runs, "r") as f:
        runs = json.load(f)
    if not runs:
        last_run = None
    else:
        last_run = runs[-1]

# --- Days since last run ---
if last_run is None:
    days_since = None
else:
    ts = last_run["timestamp"]
    date_str = ts[:8]
    last_run_date = datetime.strptime(date_str, "%Y%m%d").date()
    today = datetime.now().date()
    days_since = (today - last_run_date).days

# --- Rule: retrain if no previous run or last run >= N days ago ---
RETRAIN_AFTER_DAYS = 0
if last_run is None:
    should_retrain = True
elif days_since >= RETRAIN_AFTER_DAYS:
    should_retrain = True
else:
    should_retrain = False

# --- Act: run train.py or say no retrain needed ---
if should_retrain:
    print("Triggering training...")
    subprocess.run(["python3", "src/train.py"], cwd=project_root)
    print("Training finished.")
else:
    print(f"No retrain needed (last run was {days_since} day(s) ago).")
