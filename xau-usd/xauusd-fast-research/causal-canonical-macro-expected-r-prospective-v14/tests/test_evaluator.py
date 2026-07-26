from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from src.evaluator import (
    MACRO_FEATURES,
    build_macro_features,
    load_model,
    read_json,
    score_upstream,
    verify_config_hashes,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "config/macro_expected_r_prospective_v14.json")


def _macro_frame() -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-07-25T00:00:00Z",
        "2026-07-27T03:00:00Z",
        freq="5min",
        inclusive="left",
    )
    step = pd.Series(range(len(timestamps)), dtype=float)
    return pd.DataFrame(
        {
            "timestamp_ms": [
                int(timestamp.timestamp() * 1000) for timestamp in timestamps
            ],
            "dollaridxusd_mid_close": 100.0 + step * 0.01,
            "dollaridxusd_available": True,
            "ustbondtrusd_mid_close": 120.0 + step * 0.005,
            "ustbondtrusd_available": True,
        }
    )


def _evidence(end: str = "2026-07-27T03:00:00Z") -> dict:
    return {"snapshot_end_exclusive_utc": end}


def test_locked_inputs_and_model_are_loadable() -> None:
    verify_config_hashes(CONFIG)
    payload = load_model(CONFIG)
    assert payload["fit_rows"] == 3024
    assert len(payload["numeric_features"]) == 44
    assert payload["fit_selected_weight_fraction"] > 0.95
    assert payload["veto_quantile"] == 0.05


def test_macro_features_use_only_completed_hour_endpoints() -> None:
    cutoff = pd.Timestamp("2026-07-27T03:20:00Z")
    frame = _macro_frame()
    values, status = build_macro_features(cutoff, "LONG", frame, _evidence(), CONFIG)
    assert status == "PASS"
    assert set(values) == set(MACRO_FEATURES)
    endpoint = pd.Timestamp("2026-07-27T03:00:00Z")
    current_index = (
        frame["timestamp_ms"].searchsorted(
            int(endpoint.timestamp() * 1000), side="left"
        )
        - 1
    )
    previous = endpoint - pd.Timedelta(hours=1)
    previous_index = (
        frame["timestamp_ms"].searchsorted(
            int(previous.timestamp() * 1000), side="left"
        )
        - 1
    )
    dollar = frame["dollaridxusd_mid_close"]
    expected = -math.log(dollar.iloc[current_index] / dollar.iloc[previous_index])
    assert math.isclose(
        values["dir_inverse_dollar_return_1h"],
        expected,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert values["crossasset_coverage_fraction"] == 1.0
    assert values["crossasset_max_staleness_seconds"] == 1200.0


def test_macro_snapshot_must_cover_completed_endpoint() -> None:
    values, status = build_macro_features(
        pd.Timestamp("2026-07-27T03:20:00Z"),
        "SHORT",
        _macro_frame(),
        _evidence("2026-07-27T02:00:00Z"),
        CONFIG,
    )
    assert status == "AWAITING_MACRO_SNAPSHOT"
    assert all(values[name] is None for name in MACRO_FEATURES)


def test_upstream_xau_abstention_can_never_veto() -> None:
    payload = load_model(CONFIG)
    upstream = {
        "candidate_id": "C1",
        "candidate_fact_sha256": "a" * 64,
        "source_id": "R2_DOWNTREND",
        "specialist_id": "R2",
        "family_id": "R2_DOWNTREND",
        "scheduled_entry_time_utc": "2026-07-27T03:20:00Z",
        "direction": "SHORT",
        "feature_status": "ABSTAIN_STALE_XAU",
        "numeric_features": {
            name: None
            for name in payload["numeric_features"]
            if name not in MACRO_FEATURES
        },
        "python_predictions_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    row, reason = score_upstream(
        upstream,
        payload,
        _macro_frame(),
        _evidence(),
        CONFIG,
        pd.Timestamp("2026-07-27T03:30:00Z"),
    )
    assert reason is None
    assert row is not None
    assert row["selection_action"] == "MODEL_ABSTAIN_RETAIN_ALL"
    assert row["selected"] is True
    assert row["model_score"] is None
    assert row["broker_action_authorized"] is False
