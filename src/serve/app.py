import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .load_model import get_loaded_version, get_model, get_scaler, load_model
from .schemas import (
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    PredictRequest,
    PredictResponse,
    ReadyResponse,
    ReloadResponse,
)

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


@app.exception_handler(RequestValidationError)
async def invalid_input_handler(request: Request, exc: RequestValidationError):
    """Keep the original API contract: bad input -> 400 {"error": "invalid_input", ...}."""
    global _total_requests, _errors_400
    _total_requests += 1
    _errors_400 += 1
    first = exc.errors()[0]
    if first["type"] == "json_invalid":
        message = "body must be valid JSON"
    else:
        where = ".".join(str(p) for p in first["loc"] if p != "body")
        message = f"{where}: {first['msg']}" if where else first["msg"]
    return JSONResponse({"error": "invalid_input", "message": message}, status_code=400)


def _ensure_model():
    """Retry loading if the model was missing at startup (e.g. trained after the pod started)."""
    if get_model() is None:
        load_model()


def _predict(model, scaler, X):
    return float(model.predict(scaler.transform(X))[0])


@app.post(
    "/predict",
    response_model=PredictResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def predict(req: PredictRequest):
    global _total_requests, _errors_500, _latencies
    start_time = time.time()
    _total_requests += 1

    _ensure_model()
    model = get_model()
    scaler = get_scaler()
    if model is None or scaler is None:
        _errors_500 += 1
        return JSONResponse(
            {"error": "prediction_failed", "message": "model not loaded"}, status_code=500
        )

    X = np.array(req.features, dtype=float).reshape(1, -1)
    try:
        # sklearn is CPU-bound and blocking, so keep it off the event loop
        prediction = await run_in_threadpool(_predict, model, scaler, X)
    except Exception as e:
        _errors_500 += 1
        return JSONResponse({"error": "prediction_failed", "message": str(e)}, status_code=500)

    _latencies.append(time.time() - start_time)
    if len(_latencies) > _MAX_LATENCIES:
        _latencies = _latencies[-_MAX_LATENCIES:]
    return {"prediction": prediction, "model_version": get_loaded_version() or "unknown"}


@app.get("/metrics", response_model=MetricsResponse)
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


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.get("/ready", response_model=ReadyResponse, responses={503: {"model": ReadyResponse}})
def ready():
    _ensure_model()
    if get_model() is not None and get_scaler() is not None:
        return {"status": "ready"}
    return JSONResponse({"status": "not_ready"}, status_code=503)


@app.get(
    "/reload", response_model=ReloadResponse, responses={500: {"model": ErrorResponse}}
)
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
