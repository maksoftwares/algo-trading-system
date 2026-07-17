from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.a3_meta_v1.a2_intraday_context_ranker import (
    A2IntradayContextRankerError,
    _build_macro_features,
    _feature_cutoff_timestamp,
    _fit_model,
    _segment,
    _select_daily,
    _stress_cost,
    _to_epoch_ms,
    _validate_contract,
    _validate_lifecycle_frames,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_a2_intraday_context_ranker_v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_is_fail_closed_and_preregistered() -> None:
    contract = _contract()
    _validate_contract(contract)
    assert not any(contract["authorization"].values())
    assert not contract["model"]["hyperparameter_search_authorized"]


def test_contract_rejects_model_or_causal_join_changes() -> None:
    changed_model = _contract()
    changed_model["model"]["max_iter"] += 1
    with pytest.raises(A2IntradayContextRankerError, match="model configuration"):
        _validate_contract(changed_model)
    changed_join = _contract()
    changed_join["causal_join"]["feature_cutoff_minutes_before_entry"] = 0
    with pytest.raises(A2IntradayContextRankerError, match="five minutes"):
        _validate_contract(changed_join)


def test_lifecycle_validator_requires_exact_pairing() -> None:
    contract = _contract()
    lock = contract["a2_source_lock"]
    lock["files"]["trades"]["rows"] = 2
    lock["files"]["deals"]["rows"] = 4
    lock["required_integrity"]["unique_position_ids"] = 2
    lock["required_integrity"]["successful_entry_orders"] = 2
    trades = pd.DataFrame(
        {
            "position_id": [1, 2],
            "entry_deal": [10, 20],
            "exit_deal": [12, 22],
            "direction": ["LONG", "SHORT"],
        }
    )
    orders = pd.DataFrame(
        {
            "deal_ticket": [10, 20],
            "order_ticket": [11, 21],
            "sl": [1.0, 2.0],
            "tp": [2.0, 3.0],
            "stop_distance_points": [100.0, 100.0],
        }
    )
    deals = pd.DataFrame(
        {
            "position_id": [1, 1, 2, 2],
            "entry_code": [0, 1, 0, 1],
            "deal_ticket": [10, 12, 20, 22],
            "direction": ["LONG", "LONG", "SHORT", "SHORT"],
        }
    )
    _validate_lifecycle_frames(trades, orders, deals, lock)
    deals.loc[3, "entry_code"] = 0
    with pytest.raises(A2IntradayContextRankerError, match="one entry and one exit"):
        _validate_lifecycle_frames(trades, orders, deals, lock)


def test_macro_features_are_causal_and_reject_gap_returns() -> None:
    rows = 400
    timestamp = np.arange(rows, dtype=np.int64) * 300_000
    frame = pd.DataFrame(
        {
            "timestamp_ms": timestamp,
            "dollaridxusd_mid_close": 100 + np.arange(rows) * 0.01,
            "dollaridxusd_available": True,
            "ustbondtrusd_mid_close": 200 + np.arange(rows) * 0.02,
            "ustbondtrusd_available": True,
        }
    )
    config = _contract()["intraday_macro_features"]
    baseline = _build_macro_features(frame, config)
    changed = frame.copy()
    changed.loc[350:, "dollaridxusd_mid_close"] *= 4
    rebuilt = _build_macro_features(changed, config)
    pd.testing.assert_frame_equal(baseline.iloc[:350], rebuilt.iloc[:350])
    gap = frame.copy()
    gap.loc[300, "timestamp_ms"] += 60_000
    gap_features = _build_macro_features(gap, config)
    assert pd.isna(gap_features.loc[300, "dollar_z_15m"])


def test_segment_purges_labels_that_exit_after_boundary() -> None:
    frame = pd.DataFrame(
        {
            "entry_time_utc": ["2020-12-31T10:00:00Z", "2020-12-31T11:00:00Z"],
            "exit_time_utc": ["2020-12-31T12:00:00Z", "2021-01-01T00:00:00Z"],
        }
    )
    result = _segment(frame, "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert len(result) == 1


def test_feature_cutoff_and_stress_cost_are_exact() -> None:
    timestamps = pd.Series(pd.to_datetime(["2020-01-01T10:05:00Z"], utc=True))
    cutoff = _feature_cutoff_timestamp(timestamps, 5)
    assert cutoff.iloc[0] == pd.Timestamp("2020-01-01T10:00:00Z")
    assert _to_epoch_ms(cutoff).iloc[0] == 1_577_872_800_000
    costs = _contract()["broker_cost_source_lock"]
    stress = _stress_cost(pd.Series([0.50, 1.00]), pd.Series([0.0, 2.0]), costs)
    np.testing.assert_allclose(stress.to_numpy(), [0.55, 1.0])


def test_daily_selection_caps_highest_scores_and_keeps_both_directions() -> None:
    frame = pd.DataFrame(
        {
            "position_id": list(range(8)),
            "entry_time_utc": ["2020-01-01T10:00:00Z"] * 6
            + ["2020-01-02T10:00:00Z"] * 2,
            "entry_time_ms": list(range(8)),
            "model_score": [0.1, 0.8, 0.9, 0.7, 0.6, 0.5, 0.3, 0.4],
            "direction": ["LONG", "SHORT"] * 4,
        }
    )
    selected = _select_daily(
        frame,
        0.0,
        {"maximum_selected_trades_per_utc_day": 4},
    )
    assert len(selected) == 6
    first_day = selected.loc[selected["entry_time_utc"].str[:10] == "2020-01-01"]
    assert sorted(first_day["model_score"], reverse=True) == [0.9, 0.8, 0.7, 0.6]
    assert set(selected["direction"]) == {"LONG", "SHORT"}


def test_model_predictions_are_deterministic() -> None:
    contract = _contract()
    features = contract["features"]
    rng = np.random.default_rng(17)
    frame = pd.DataFrame(rng.normal(size=(300, len(features))), columns=features)
    frame["stress_net_r"] = frame[features[0]] * 0.1 + rng.normal(size=300)
    first = _fit_model(frame, features, contract["model"]).predict(frame[features])
    second = _fit_model(frame, features, contract["model"]).predict(frame[features])
    np.testing.assert_array_equal(first, second)
