import json
import os
import warnings
from datetime import datetime

import joblib
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Suppress sklearn internal RuntimeWarnings (matmul overflow/divide-by-zero) on some setups;
# model output is valid
warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)


def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.dropna()
    y = df["MEDV"]
    X = df.drop(columns=["MEDV"])
    return X, y


def fit_model(X, y, random_state=42, test_size=0.2, solver="lsqr"):
    """Split, scale, fit a Ridge model. Returns (model, scaler, mae)."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    model = Ridge(solver=solver)
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    return model, scaler, mae


def save_artifact(model, scaler, models_dir, timestamp):
    os.makedirs(models_dir, exist_ok=True)
    filename = f"model_{timestamp}.pkl"
    path_to_save = os.path.join(models_dir, filename)
    joblib.dump({"model": model, "scaler": scaler}, path_to_save)
    return path_to_save


def log_experiment(experiments_file, record):
    os.makedirs(os.path.dirname(experiments_file), exist_ok=True)
    if os.path.exists(experiments_file):
        with open(experiments_file, "r") as f:
            runs = json.load(f)
    else:
        runs = []
    runs.append(record)
    with open(experiments_file, "w") as f:
        json.dump(runs, f, indent=2)
    return runs


def log_to_mlflow(model, mae, timestamp, params):
    import mlflow

    if not os.environ.get("MLFLOW_TRACKING_URI"):
        os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5001"
    mlflow.set_experiment("boston-housing")
    with mlflow.start_run(run_name=f"run_{timestamp}"):
        for key, value in params.items():
            mlflow.log_param(key, value)
        mlflow.log_metric("mae", mae)
        mlflow.sklearn.log_model(model, "model", registered_model_name="boston-housing")


def main():
    path_to_csv = os.path.join(project_root, "data", "train.csv")
    path_to_models_dir = os.path.join(project_root, "models")
    path_to_experiments_file = os.path.join(project_root, "experiments", "runs.json")

    print("project root:", project_root)
    print("CSV path:", path_to_csv)

    X, y = load_data(path_to_csv)
    model, scaler, mae = fit_model(X, y)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_to_save = save_artifact(model, scaler, path_to_models_dir, timestamp)
    print("Model saved to:", path_to_save)

    params = {
        "data_path": "data/train.csv",
        "random_state": 42,
        "test_size": 0.2,
        "solver": "lsqr",
    }
    try:
        log_to_mlflow(model, mae, timestamp, params)
        print("Logged to MLflow and registered model 'boston-housing'.")
    except Exception as e:
        print("MLflow logging skipped (tracking server unavailable?):", e)

    relative_model_path = os.path.relpath(path_to_save, project_root)
    record = {
        "run_id": timestamp,
        "timestamp": timestamp,
        "data_path": "data/train.csv",
        "model_path": relative_model_path,
        "metric": mae,
    }
    log_experiment(path_to_experiments_file, record)
    print("Logged to:", path_to_experiments_file)


if __name__ == "__main__":
    main()
