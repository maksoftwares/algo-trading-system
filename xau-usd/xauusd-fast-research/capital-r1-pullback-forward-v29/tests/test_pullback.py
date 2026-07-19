from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pullback import (  # noqa: E402
    PullbackSettings,
    candidate_id,
    candidates_from_evaluations,
    completed_index,
    mt5_atr,
    prepare_indicator_frame,
)


def bars(rows: int = 20, frequency: str = "15min") -> pd.DataFrame:
    close = np.arange(rows, dtype=float) + 100.0
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=rows, freq=frequency, tz="UTC"),
            "open": close - 0.25,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
        }
    )


def test_mt5_atr_is_simple_true_range_average() -> None:
    frame = bars()
    observed = mt5_atr(frame, 14)
    # Every true range is 2.0, so native iATR is exactly 2.0 after warm-up.
    assert np.isnan(observed[13])
    assert observed[14] == pytest.approx(2.0)
    assert observed[-1] == pytest.approx(2.0)


def test_completed_index_mirrors_native_shift_one() -> None:
    frame = prepare_indicator_frame(bars(), PullbackSettings())
    assert completed_index(frame, "2026-01-01T00:15:00Z") == 0
    assert completed_index(frame, "2026-01-01T00:29:59Z") == 0
    assert completed_index(frame, "2026-01-01T00:30:00Z") == 1


def test_candidate_export_never_grants_authority() -> None:
    evaluations = pd.DataFrame(
        [
            {
                "decision_time_utc": pd.Timestamp("2026-07-20T09:15:00Z"),
                "raw_signal": True,
                "direction": "LONG",
                "signal_reason": "R1_H1_EMA_PULLBACK_LONG_M15",
                "regime": "UPTREND",
                "guard_action": "ORDER_SEND_OK",
                "guard_reason": "pass",
                "stop_points": 500.0,
                "break_distance_atr": 0.2,
                "estimated_cost_r": 0.02,
                "spread_points": 10.0,
            }
        ]
    )
    result = candidates_from_evaluations(evaluations, "a" * 64)
    assert len(result) == 1
    assert not result.loc[0, "trade_permission"]
    assert not result.loc[0, "broker_action_allowed"]
    assert not result.loc[0, "python_execution_authorized"]
    assert result.loc[0, "spread_points"] == 10.0


def test_candidate_id_is_version_and_dependency_bound() -> None:
    decision = "2026-07-20T09:15:00Z"
    first = candidate_id(decision, "a" * 64)
    assert first == candidate_id(decision, "a" * 64)
    assert first != candidate_id(decision, "b" * 64)


def test_unknown_setting_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown pullback settings"):
        PullbackSettings.from_mapping({"not_a_setting": 1})
