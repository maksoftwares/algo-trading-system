from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from step_3_features import (  # noqa: E402
    CompletedAtrReference,
    _aggregate_hour_to_m5,
    _window,
    _xau_feature_status,
    deterministic_features,
)


def test_raw_window_is_open_left_closed_right() -> None:
    cutoff = 10_000
    times = np.array([4_999, 5_000, 5_001, 10_000, 10_001], dtype=np.int64)
    bids = np.arange(5, dtype=float)
    asks = bids + 1.0
    selected, selected_bids, _ = _window(
        times, bids, asks, cutoff_ms=cutoff, width_ms=5_000
    )
    assert selected.tolist() == [5_001, 10_000]
    assert selected_bids.tolist() == [2.0, 3.0]


def test_completed_atr_never_reads_forming_bar() -> None:
    frame = pd.DataFrame(
        {
            "timestamp_ms": [0, 300_000, 600_000],
            "atr": [1.0, 2.0, 999.0],
        }
    )
    reference = CompletedAtrReference(frame)
    assert reference.at_cutoff(900_000) == 999.0
    assert reference.at_cutoff(899_999) == 2.0


def test_m5_aggregation_uses_only_observed_mid_quotes() -> None:
    frame = _aggregate_hour_to_m5(
        np.array([0, 1_000, 300_000], dtype=np.int64),
        np.array([99.0, 101.0, 102.0]),
        np.array([101.0, 103.0, 104.0]),
    )
    assert frame["timestamp_ms"].tolist() == [0, 300_000]
    assert frame["mid_high"].tolist() == [102.0, 103.0]
    assert frame["mid_close"].tolist() == [102.0, 103.0]


def test_deterministic_features_match_locked_ordered_names() -> None:
    contract = json.loads(
        (
            PACKAGE_ROOT / "config" / "step_2b_dataset_feature_contract_v1.json"
        ).read_text()
    )
    row = {
        "family_id": "R4_CHOP",
        "direction": "SHORT",
        "decision_time": pd.Timestamp("2025-01-06T12:30:00Z"),
        "stop_mode": "ATR",
        "target_mode": "R_MULTIPLE",
        "planned_stop_price": 3.0,
        "stop_floor_price": np.nan,
        "target_r": 2.0,
        "label_observation_cap_minutes": 720.0,
        "maximum_hold_mode": "FIXED",
    }
    features = deterministic_features(
        row, mechanic_mapping=contract["broad_mechanic_mapping"], atr=1.5
    )
    expected = contract["feature_contract"]["ordered_blocks"][0]["features"]
    assert list(features) == expected
    assert features["direction_sign"] == -1.0
    assert features["planned_stop_atr"] == 2.0


def test_xau_status_fails_closed_for_any_missing_mandatory_value() -> None:
    assert _xau_feature_status({"available": 1.0, "missing": None}, 0.0) == (
        "ABSTAIN_MISSING_MANDATORY_XAU"
    )
    assert _xau_feature_status({"available": 1.0}, 301.0) == "ABSTAIN_STALE_XAU"
    assert _xau_feature_status({"available": 1.0}, 300.0) == "PASS"
