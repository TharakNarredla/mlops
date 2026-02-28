# Pipeline Architecture

This document describes the end-to-end flow of the MLOps pipeline.

---

## High-Level Flow

```
Data → Training → MLflow → Artifacts → Docker → Kubernetes → API Serving
```

---

## Components

### Data
- **Location:** `data/train.csv`
- **Format:** Boston Housing–style regression (13 features, target MEDV)
- Training and logging use a fixed data path for reproducibility.

### Training
- **Scripts:** `train.py` (main training), `retrain.py` (retrain decision logic)
- **Output:** Model artifacts in `models/`, run metadata in `experiments/runs.json`
- **Reproducibility:** Fixed `random_state`, StandardScaler, deterministic paths

### MLflow
- Experiment tracking and model registry
- Each run logs params, metrics, and artifacts
- See `docs/MLFLOW.md` for details

### Artifacts
- **models/:** One `.pkl` per run (model + scaler)
- **experiments/runs.json:** Run metadata for version resolution

### Docker
- **Dockerfile.inference:** Local run with volume mounts for `models/` and `experiments/`
- **Dockerfile.inference.k8s:** Production-style image with artifacts baked in

### Kubernetes
- **Deployment:** Runs the inference container
- **Service:** Exposes the API
- **ConfigMap:** `MODEL_RUN_ID` for version selection and rollback

### API Serving
- **Endpoints:** `POST /predict`, `GET /metrics`, `GET /reload`
- Version-aware: loads model by `run_id` or latest
- See `docs/api.md` for the API contract

---

## Rollback

Change `MODEL_RUN_ID` in the ConfigMap and run `kubectl rollout restart deployment/mlops-inference` to serve a different model version without redeploying code.
