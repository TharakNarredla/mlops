import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from .load_model import get_loaded_version, get_model, get_scaler, load_model

_total_requests = 0
_errors_400 = 0
_errors_500 = 0
_latencies = []  # last N request durations (seconds); cap at 1000
_MAX_LATENCIES = 1000


@asynccontextmanager
async def lifespan(app):
    # Load the model once when the server starts
    load_model()
    yield


app = FastAPI(title="MLOps Inference API", lifespan=lifespan)


def _ensure_model():
    """Retry loading if the model was missing at startup (e.g. trained after the pod started)."""
    if get_model() is None:
        load_model()


def _validate_features(data):
    if data is None or not isinstance(data, dict):
        return False, "body must be JSON object"
    features = data.get("features")
    if features is None:
        return False, "missing 'features'"
    if not isinstance(features, list):
        return False, "features must be a list"
    if len(features) != 13:
        return False, "features must be exactly 13 numbers"
    try:
        arr = np.array(features, dtype=float)
    except (ValueError, TypeError):
        return False, "features must be numbers"
    if not np.isfinite(arr).all():
        return False, "features must be finite (no NaN/Inf)"
    return True, arr.reshape(1, -1)


def _predict(model, scaler, X):
    return float(model.predict(scaler.transform(X))[0])


@app.post("/predict")
async def predict(request: Request):
    global _total_requests, _errors_400, _errors_500, _latencies
    start_time = time.time()
    _total_requests += 1
    try:
        body = await request.json()
    except ValueError:
        body = None
    ok, payload = _validate_features(body)
    if not ok:
        _errors_400 += 1
        return JSONResponse({"error": "invalid_input", "message": payload}, status_code=400)

    _ensure_model()
    model = get_model()
    scaler = get_scaler()
    if model is None or scaler is None:
        _errors_500 += 1
        return JSONResponse(
            {"error": "prediction_failed", "message": "model not loaded"}, status_code=500
        )

    try:
        # sklearn is CPU-bound and blocking, so keep it off the event loop
        prediction = await run_in_threadpool(_predict, model, scaler, payload)
    except Exception as e:
        _errors_500 += 1
        return JSONResponse({"error": "prediction_failed", "message": str(e)}, status_code=500)

    _latencies.append(time.time() - start_time)
    if len(_latencies) > _MAX_LATENCIES:
        _latencies = _latencies[-_MAX_LATENCIES:]
    version = get_loaded_version() or "unknown"
    return {"prediction": prediction, "model_version": version}


@app.get("/metrics")
def metrics():
    if _latencies:
        avg_sec = sum(_latencies) / len(_latencies)
        min_sec = min(_latencies)
        max_sec = max(_latencies)
    else:
        avg_sec = min_sec = max_sec = 0.0
    return {
        "total_requests": _total_requests,
        "errors_400": _errors_400,
        "errors_500": _errors_500,
        "latency_avg_sec": round(avg_sec, 6),
        "latency_min_sec": round(min_sec, 6),
        "latency_max_sec": round(max_sec, 6),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    _ensure_model()
    if get_model() is not None and get_scaler() is not None:
        return {"status": "ready"}
    return JSONResponse({"status": "not_ready"}, status_code=503)


@app.get("/reload")
def reload(latest: str = ""):
    """
    Reload model from disk. By default uses same env (MODEL_PATH, MODEL_RUN_ID, or latest).
    Add ?latest=1 to force loading the latest run from runs.json (e.g. after training
    without restart).
    """
    force_latest = latest.strip().lower() in ("1", "true", "yes")
    load_model(force_latest=force_latest)
    version = get_loaded_version()
    if version is None:
        return JSONResponse(
            {"error": "reload_failed", "message": "model not loaded"}, status_code=500
        )
    return {"status": "ok", "model_version": version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
