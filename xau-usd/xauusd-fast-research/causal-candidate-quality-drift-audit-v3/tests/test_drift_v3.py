from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.drift import (  # noqa: E402
    decomposition_table,
    numeric_psi,
    weighted_mean,
    weighted_quantile,
)


CONFIG = json.loads(
    (ROOT / "config" / "drift_audit_v3.json").read_text(encoding="utf-8")
)


def test_weighted_statistics_and_identical_psi() -> None:
    values = np.array([0.0, 1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 2.0, 2.0])
    assert weighted_mean(values, weights) == 11.0 / 6.0
    assert np.all(np.diff(weighted_quantile(values, weights, [0.1, 0.5, 0.9])) >= 0)
    assert numeric_psi(values, values, weights, weights, bins=4, epsilon=1e-6) == 0.0


def test_decomposition_identity() -> None:
    frame = pd.DataFrame(
        {
            "model_lane": ["L", "L", "L", "L"],
            "period": ["REFERENCE", "REFERENCE", "CURRENT", "CURRENT"],
            "selected": [True, True, True, True],
            "event_eval_weight": [1.0, 1.0, 1.0, 3.0],
            "stress_net_r": [1.0, -1.0, 0.5, -0.5],
            "regime": ["A", "B", "A", "B"],
            "session_utc": ["S", "S", "S", "S"],
            "direction": ["LONG", "SHORT", "LONG", "SHORT"],
            "action_availability": ["X", "Y", "X", "Y"],
            "chosen_action": ["X", "Y", "X", "Y"],
        }
    )
    config = {
        "expected": {"lanes": ["L"]},
        "decomposition_dimensions": ["regime"],
    }
    result = decomposition_table(frame, config)
    total = result.loc[result["category"].eq("__TOTAL__")].iloc[0]
    assert np.isclose(
        total["composition_effect_r"] + total["within_stratum_effect_r"],
        total["total_effect_r"],
    )
    assert np.isclose(
        total["current_mean_r"] - total["reference_mean_r"], total["total_effect_r"]
    )


def test_runtime_authorization_is_disabled() -> None:
    authorization = CONFIG["authorization"]
    assert authorization["research_only"] is True
    assert all(
        not value for key, value in authorization.items() if key != "research_only"
    )


def test_completed_output_invariants() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    result_path = output / CONFIG["outputs"]["result_json"]
    if not result_path.is_file():
        return
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["decision"] == "F2026_DRIFT_AUDIT_COMPLETE_NO_RUNTIME_AUTHORIZATION"
    replayed = pd.read_parquet(output / CONFIG["outputs"]["replayed_events"])
    assert not replayed.duplicated(["period", "model_lane", "event_id"]).any()
    assert set(replayed["period"]) == {"REFERENCE", "CURRENT"}
    assert set(replayed["model_lane"]) == set(CONFIG["expected"]["lanes"])
