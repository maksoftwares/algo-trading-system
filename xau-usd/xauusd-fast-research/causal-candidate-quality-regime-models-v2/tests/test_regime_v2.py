from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from regime_model import fit_model, predict
from regime_runner import availability_table


PACKAGE = Path(__file__).resolve().parents[1]


def _contract() -> dict:
    return json.loads(
        (PACKAGE / "config" / "regime_models_v2.json").read_text(encoding="utf-8")
    )


def test_feature_contract_excludes_identity_outcome_and_comex() -> None:
    features = _contract()["features"]
    assert len(features) == 22
    assert "family_id" not in features
    assert "stress_net_r" not in features
    assert "decision_time" not in features
    assert not any(name.startswith("gc_") for name in features)


def test_availability_is_count_based_and_fail_closed() -> None:
    rows = []
    for assignment, count in (("FIT", 90), ("CALIBRATION", 8), ("TEST", 15)):
        rows.extend(
            {
                "family_id": "R1_UPTREND",
                "fold_id": "F2025",
                "assignment": assignment,
            }
            for _ in range(count)
        )
    contract = _contract()
    contract["population"]["families"] = ["R1_UPTREND", "R2_DOWNTREND"]
    result = availability_table(pd.DataFrame(rows), contract)
    indexed = result.set_index(["family_id", "fold_id"])
    assert bool(indexed.at[("R1_UPTREND", "F2025"), "trainable"])
    assert not bool(indexed.at[("R2_DOWNTREND", "F2025"), "trainable"])


def test_regime_model_fits_only_supplied_numeric_features() -> None:
    rng = np.random.default_rng(7)
    features = ["a", "b"]
    frame = pd.DataFrame(
        {
            "a": np.r_[rng.normal(-1, 0.2, 50), rng.normal(1, 0.2, 50)],
            "b": rng.normal(size=100),
            "stress_net_r_positive": [0] * 50 + [1] * 50,
            "structural_weight": np.ones(100),
            "family_id": ["constant"] * 100,
        }
    )
    model = fit_model(
        frame,
        features=features,
        parameters={"C": 0.05, "solver": "lbfgs", "max_iter": 2000, "random_state": 1},
    )
    probability = predict(model, frame, features)
    assert probability[:50].mean() < probability[50:].mean()
