import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.serve import app as app_module
from src.serve import load_model as lm

FEATURES = [0.1, 18.0, 2.3, 0.0, 0.5, 6.5, 65.0, 4.0, 1.0, 296.0, 15.0, 396.0, 5.0]


@pytest.fixture
def model_file(tmp_path):
    rng = np.random.RandomState(0)
    X = rng.rand(30, 13)
    y = X.sum(axis=1)
    scaler = StandardScaler().fit(X)
    model = Ridge().fit(scaler.transform(X), y)
    path = tmp_path / "model_20260101_000000.pkl"
    joblib.dump({"model": model, "scaler": scaler}, path)
    return path


@pytest.fixture(autouse=True)
def reset_state():
    lm._model = lm._scaler = lm._loaded_version = None
    app_module._total_requests = app_module._errors_400 = app_module._errors_500 = 0
    app_module._latencies = []
    yield


@pytest.fixture
def client(model_file, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(model_file))
    with TestClient(app_module.app) as c:
        yield c


@pytest.fixture
def client_no_model(monkeypatch):
    monkeypatch.setenv("MODEL_PATH", "/does/not/exist.pkl")
    with TestClient(app_module.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_when_model_loaded(client):
    assert client.get("/ready").json() == {"status": "ready"}


def test_ready_503_without_model(client_no_model):
    assert client_no_model.get("/ready").status_code == 503


def test_predict_ok(client):
    r = client.post("/predict", json={"features": FEATURES})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["prediction"], float)
    assert body["model_version"] == "model_20260101_000000"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"features": "abc"},
        {"features": [1, 2, 3]},
        {"features": ["a"] * 13},
        [1, 2, 3],
    ],
)
def test_predict_invalid_input_returns_400(client, payload):
    r = client.post("/predict", json=payload)
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_input"


def test_predict_invalid_input_message_names_the_field(client):
    body = client.post("/predict", json={"features": [1, 2, 3]}).json()
    assert body["error"] == "invalid_input"
    assert body["message"].startswith("features:")


@pytest.mark.parametrize("bad", ["1.5", None, True])
def test_predict_rejects_non_numbers(client, bad):
    r = client.post("/predict", json={"features": [bad] + FEATURES[1:]})
    assert r.status_code == 400


def test_predict_rejects_nan(client):
    r = client.post(
        "/predict",
        content=b'{"features": [NaN, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}',
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 400


def test_predict_ignores_extra_keys(client):
    r = client.post("/predict", json={"features": FEATURES, "note": "hi"})
    assert r.status_code == 200


def test_openapi_documents_schemas(client):
    spec = client.get("/openapi.json").json()
    assert "PredictRequest" in spec["components"]["schemas"]
    assert "ErrorResponse" in spec["components"]["schemas"]
    assert "400" in spec["paths"]["/predict"]["post"]["responses"]


def test_predict_invalid_json_returns_400(client):
    r = client.post("/predict", content=b"not json", headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert r.json()["message"] == "body must be valid JSON"


def test_predict_500_without_model(client_no_model):
    r = client_no_model.post("/predict", json={"features": FEATURES})
    assert r.status_code == 500


def test_metrics_counts_requests(client):
    client.post("/predict", json={"features": FEATURES})
    client.post("/predict", json={"features": [1]})
    m = client.get("/metrics").json()
    assert m["total_requests"] == 2
    assert m["errors_400"] == 1
    assert m["latency_avg_sec"] > 0


def test_reload_ok(client):
    r = client.get("/reload")
    assert r.status_code == 200
    assert r.json()["model_version"] == "model_20260101_000000"


def test_docs_available(client):
    assert client.get("/docs").status_code == 200
