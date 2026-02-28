"""
Model selection: env MODEL_PATH (full path to .pkl), or MODEL_RUN_ID (run_id from
runs.json), or default = latest (last run in runs.json). Load artifact and expose
model, scaler, and loaded version for the predict endpoint and rollback.
"""
import os
import json
import joblib

# In-memory state after load_model() is called
_model = None
_scaler = None
_loaded_version = None


def get_model_path():
    """
    Resolve which model to load. Priority:
    1. MODEL_PATH (env) = full path to .pkl
    2. MODEL_RUN_ID (env) = run_id → look up in runs.json, use that run's model_path
    3. default = latest = last run in runs.json

    Returns full path to the .pkl file, or None if not found.
    """
    # Project root: this file is at src/serve/load_model.py, so go up two levels
    this_file = os.path.abspath(__file__)
    serve_dir = os.path.dirname(this_file)
    src_dir = os.path.dirname(serve_dir)
    project_root = os.path.dirname(src_dir)

    path_to_runs = os.path.join(project_root, "experiments", "runs.json")

    # 1. Explicit full path
    model_path_env = os.environ.get("MODEL_PATH", "").strip()
    if model_path_env:
        if os.path.isfile(model_path_env):
            return model_path_env
        return None

    # 2. and 3. need runs.json
    if not os.path.isfile(path_to_runs):
        return None
    with open(path_to_runs, "r") as f:
        runs = json.load(f)
    if not runs:
        return None

    run_id_env = os.environ.get("MODEL_RUN_ID", "").strip()

    # 2. Specific run_id
    if run_id_env:
        for run in runs:
            if run.get("run_id") == run_id_env:
                rel_path = run.get("model_path")
                if not rel_path:
                    return None
                full_path = os.path.join(project_root, rel_path)
                if os.path.isfile(full_path):
                    return full_path
                return None
        return None

    # 3. Latest = last run
    last_run = runs[-1]
    rel_path = last_run.get("model_path")
    if not rel_path:
        return None
    full_path = os.path.join(project_root, rel_path)
    if os.path.isfile(full_path):
        return full_path
    return None


def get_model_path_latest():
    """
    Always resolve to the latest run in runs.json (ignore MODEL_PATH and MODEL_RUN_ID).
    Use for /reload?latest=1 so you can pick up a newly trained model without restarting.
    Returns full path to the .pkl file, or None if not found.
    """
    this_file = os.path.abspath(__file__)
    serve_dir = os.path.dirname(this_file)
    src_dir = os.path.dirname(serve_dir)
    project_root = os.path.dirname(src_dir)
    path_to_runs = os.path.join(project_root, "experiments", "runs.json")
    if not os.path.isfile(path_to_runs):
        return None
    with open(path_to_runs, "r") as f:
        runs = json.load(f)
    if not runs:
        return None
    last_run = runs[-1]
    rel_path = last_run.get("model_path")
    if not rel_path:
        return None
    full_path = os.path.join(project_root, rel_path)
    if os.path.isfile(full_path):
        return full_path
    return None


def load_model(force_latest=False):
    """
    Load the artifact at get_model_path() into memory. Sets _model, _scaler, _loaded_version.
    Call once at server startup (and on reload for rollback). On failure, all set to None.
    If force_latest=True, always load the latest run from runs.json (ignore MODEL_PATH/MODEL_RUN_ID).
    """
    global _model, _scaler, _loaded_version
    path = get_model_path_latest() if force_latest else get_model_path()
    if path is None:
        _model = None
        _scaler = None
        _loaded_version = None
        return
    try:
        artifact = joblib.load(path)
        if not isinstance(artifact, dict) or "model" not in artifact or "scaler" not in artifact:
            _model = None
            _scaler = None
            _loaded_version = None
            return
        _model = artifact["model"]
        _scaler = artifact["scaler"]
        # Version string from filename, e.g. model_20260206_175154.pkl -> 20260206_175154
        basename = os.path.basename(path)
        _loaded_version = basename.replace(".pkl", "") if basename.endswith(".pkl") else basename
    except Exception:
        _model = None
        _scaler = None
        _loaded_version = None


def get_model():
    """Return the loaded model, or None if not loaded."""
    return _model


def get_scaler():
    """Return the loaded scaler, or None if not loaded."""
    return _scaler


def get_loaded_version():
    """Return the loaded model version string (e.g. run_id from filename), or None. For API and rollback."""
    return _loaded_version
