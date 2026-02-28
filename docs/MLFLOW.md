# MLflow in This Project

MLflow is used for **experiment tracking** and **model registry** in this pipeline.

---

## What MLflow Does Here

- **Tracking:** Every training run logs parameters, metrics, and artifacts to the MLflow server.
- **Model Registry:** Trained models are registered with versions and stages (Staging, Production).
- **Reproducibility:** Each run has a unique `run_id`; artifacts are traceable to a specific run.

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Tracking Server** | Stores experiments, runs, params, metrics, and artifacts. Run with `mlflow server`. |
| **Experiment** | A named container for runs (e.g. `boston-housing`). |
| **Run** | One execution of training. Has `run_id`, params, metrics, artifacts. |
| **Params** | Inputs to the run (e.g. `random_state`, `data_path`). Logged at start. |
| **Metrics** | Values to compare (e.g. `mae`, `rmse`). Logged at end. |
| **Artifacts** | Files produced by a run (model `.pkl`, etc.). Stored in artifact store. |

---

## How to Run MLflow UI

```bash
python3 -m mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5001
```

Open http://127.0.0.1:5001 to view experiments, runs, and registered models.

---

## Integration with This Pipeline

- `src/train.py` sets `MLFLOW_TRACKING_URI` and logs each run.
- Models are saved to `models/` and also logged as MLflow artifacts.
- The inference service can load by `run_id` (from ConfigMap) or latest.
