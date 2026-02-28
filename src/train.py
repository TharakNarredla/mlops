import warnings
# Suppress sklearn internal RuntimeWarnings (matmul overflow/divide-by-zero) on some setups; model output is valid
warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os
import json

import mlflow

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
path_to_csv = os.path.join(project_root, "data", "train.csv")
path_to_models_dir = os.path.join(project_root, "models")
path_to_experiments_file = os.path.join(project_root, "experiments", "runs.json")

# MLflow: use env MLFLOW_TRACKING_URI or default to local server on 5001
if not os.environ.get("MLFLOW_TRACKING_URI"):
    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5001"

print("project root:", project_root)
print("CSV path:", path_to_csv)
df = pd.read_csv(path_to_csv)
df = df.dropna()
y = df["MEDV"]
X = df.drop(columns=["MEDV"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
model = Ridge(solver="lsqr")
model.fit(X_train_scaled, y_train)
y_pred = model.predict(X_test_scaled)
metric = mean_absolute_error(y_test, y_pred)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"model_{timestamp}.pkl"
path_to_save = os.path.join(path_to_models_dir, filename)
artifact = {"model": model, "scaler": scaler}
joblib.dump(artifact, path_to_save)
print("Model saved to:", path_to_save)

# --- MLflow: log run, params, metric, sklearn model; register model ---
mlflow.set_experiment("boston-housing")
with mlflow.start_run(run_name=f"run_{timestamp}") as run:
    mlflow.log_param("data_path", "data/train.csv")
    mlflow.log_param("random_state", 42)
    mlflow.log_param("test_size", 0.2)
    mlflow.log_param("solver", "lsqr")
    mlflow.log_metric("mae", metric)
    # Log sklearn model so Model Registry can version it (our inference still uses models/*.pkl)
    mlflow.sklearn.log_model(model, "model", registered_model_name="boston-housing")
    print("Logged to MLflow and registered model 'boston-housing'.")

# --- Experiment logging: append this run to runs.json (one JSON file, array of runs) ---
relative_model_path = os.path.relpath(path_to_save, project_root)
record = {
    "run_id": timestamp,
    "timestamp": timestamp,
    "data_path": "data/train.csv",
    "model_path": relative_model_path,
    "metric": metric,
}
if os.path.exists(path_to_experiments_file):
    with open(path_to_experiments_file, "r") as f:
        runs = json.load(f)
else:
    runs = []
runs.append(record)
with open(path_to_experiments_file, "w") as f:
    json.dump(runs, f, indent=2)
print("Logged to:", path_to_experiments_file)

