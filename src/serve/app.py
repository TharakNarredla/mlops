from flask import Flask, request, jsonify
import numpy as np
import time
from .load_model import load_model, get_model, get_scaler, get_loaded_version

app = Flask(__name__)
_total_requests = 0
_errors_400 = 0
_errors_500 = 0
_latencies = []  # last N request durations (seconds); cap at 1000
_MAX_LATENCIES = 1000
@app.before_request
def before_first_request():
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
@app.route("/predict", methods=["POST"])
def predict():
    start_time = time.time()
    global _total_requests, _errors_400, _errors_500, _latencies
    ok, payload = _validate_features(request.get_json())
    if not ok:
        _total_requests += 1
        _errors_400 += 1
        return jsonify({"error": "invalid_input", "message": payload}), 400
    model = get_model()
    scaler = get_scaler()
    if model is None or scaler is None:
        _total_requests += 1
        _errors_500 += 1
        return jsonify({"error": "prediction_failed", "message": "model not loaded"}), 500

    try:
        X = payload
        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)
        prediction = float(pred[0])
    except Exception as e:
        _total_requests += 1
        _errors_500 += 1
        return jsonify({"error": "prediction_failed", "message": str(e)}), 500

    _total_requests += 1
    duration_sec = time.time() - start_time
    _latencies.append(duration_sec)
    if len(_latencies) > _MAX_LATENCIES:
        _latencies = _latencies[-_MAX_LATENCIES:]
    version = get_loaded_version() or "unknown"
    return jsonify({"prediction": prediction, "model_version": version}), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    if _latencies:
        avg_sec = sum(_latencies) / len(_latencies)
        min_sec = min(_latencies)
        max_sec = max(_latencies)
    else:
        avg_sec = min_sec = max_sec = 0.0
    return jsonify({
        "total_requests": _total_requests,
        "errors_400": _errors_400,
        "errors_500": _errors_500,
        "latency_avg_sec": round(avg_sec, 6),
        "latency_min_sec": round(min_sec, 6),
        "latency_max_sec": round(max_sec, 6),
    }), 200


@app.route("/reload", methods=["GET"])
def reload():
    """
    Reload model from disk. By default uses same env (MODEL_PATH, MODEL_RUN_ID, or latest).
    Add ?latest=1 to force loading the latest run from runs.json (e.g. after training without restart).
    """
    force_latest = request.args.get("latest", "").strip().lower() in ("1", "true", "yes")
    load_model(force_latest=force_latest)
    version = get_loaded_version()
    if version is None:
        return jsonify({"error": "reload_failed", "message": "model not loaded"}), 500
    return jsonify({"status": "ok", "model_version": version}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
