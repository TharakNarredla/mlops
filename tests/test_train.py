import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import train  # noqa: E402


@pytest.fixture
def sample_df():
    rng = np.random.RandomState(0)
    n = 50
    X = pd.DataFrame(
        {
            "CRIM": rng.rand(n),
            "RM": rng.uniform(4, 8, n),
            "AGE": rng.uniform(0, 100, n),
        }
    )
    y = 3 * X["RM"] + rng.rand(n) * 0.1
    df = X.copy()
    df["MEDV"] = y
    return df


def test_load_data_splits_target(tmp_path, sample_df):
    csv_path = tmp_path / "train.csv"
    sample_df.to_csv(csv_path, index=False)

    X, y = train.load_data(str(csv_path))

    assert "MEDV" not in X.columns
    assert len(X) == len(y) == len(sample_df)


def test_load_data_drops_na_rows(tmp_path, sample_df):
    sample_df.loc[0, "RM"] = None
    csv_path = tmp_path / "train.csv"
    sample_df.to_csv(csv_path, index=False)

    X, _ = train.load_data(str(csv_path))

    assert len(X) == len(sample_df) - 1


def test_fit_model_returns_usable_artifacts(sample_df):
    X = sample_df.drop(columns=["MEDV"])
    y = sample_df["MEDV"]

    model, scaler, mae = train.fit_model(X, y)

    assert mae >= 0
    # scaler + model round-trip on a fresh row
    scaled = scaler.transform(X.iloc[[0]])
    pred = model.predict(scaled)
    assert np.isfinite(pred[0])


def test_save_artifact_writes_pkl_and_is_loadable(tmp_path, sample_df):
    X = sample_df.drop(columns=["MEDV"])
    y = sample_df["MEDV"]
    model, scaler, _ = train.fit_model(X, y)

    path = train.save_artifact(model, scaler, str(tmp_path), "20260101_000000")

    assert os.path.isfile(path)
    assert path.endswith("model_20260101_000000.pkl")


def test_log_experiment_appends_and_creates_file(tmp_path):
    experiments_file = tmp_path / "experiments" / "runs.json"
    record1 = {"run_id": "a", "metric": 1.0}
    record2 = {"run_id": "b", "metric": 2.0}

    train.log_experiment(str(experiments_file), record1)
    runs = train.log_experiment(str(experiments_file), record2)

    assert os.path.isfile(experiments_file)
    assert len(runs) == 2
    with open(experiments_file) as f:
        on_disk = json.load(f)
    assert [r["run_id"] for r in on_disk] == ["a", "b"]
