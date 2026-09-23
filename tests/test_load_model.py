import os
import sys

import joblib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "serve"))
import load_model as lm  # noqa: E402


@pytest.fixture(autouse=True)
def reset_module_state():
    """load_model keeps module-level globals; reset them between tests."""
    lm._model = None
    lm._scaler = None
    lm._loaded_version = None
    yield
    lm._model = None
    lm._scaler = None
    lm._loaded_version = None


def test_get_model_path_uses_explicit_model_path(tmp_path, monkeypatch):
    fake_model = tmp_path / "somewhere.pkl"
    fake_model.write_bytes(b"x")
    monkeypatch.setenv("MODEL_PATH", str(fake_model))

    assert lm.get_model_path() == str(fake_model)


def test_get_model_path_missing_explicit_path_returns_none(monkeypatch):
    monkeypatch.setenv("MODEL_PATH", "/does/not/exist.pkl")

    assert lm.get_model_path() is None


def test_load_model_missing_file_leaves_state_none(monkeypatch):
    monkeypatch.setenv("MODEL_PATH", "/does/not/exist.pkl")

    lm.load_model()

    assert lm.get_model() is None
    assert lm.get_scaler() is None
    assert lm.get_loaded_version() is None


def test_load_model_valid_artifact_sets_state(tmp_path, monkeypatch):
    model_path = tmp_path / "model_20260101_000000.pkl"
    joblib.dump({"model": "m", "scaler": "s"}, model_path)
    monkeypatch.setenv("MODEL_PATH", str(model_path))

    lm.load_model()

    assert lm.get_model() == "m"
    assert lm.get_scaler() == "s"
    assert lm.get_loaded_version() == "model_20260101_000000"


def test_load_model_bad_artifact_shape_leaves_state_none(tmp_path, monkeypatch):
    bad_path = tmp_path / "bad.pkl"
    joblib.dump({"only_model": "m"}, bad_path)
    monkeypatch.setenv("MODEL_PATH", str(bad_path))

    lm.load_model()

    assert lm.get_model() is None
