from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "session.py"
SPEC = importlib.util.spec_from_file_location(
    "calendar_session_specialists_v1_tests", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
SESSION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SESSION
SPEC.loader.exec_module(SESSION)


def _config() -> dict:
    return {"features": {"h1_atr_period": 3}}


def _h1(rows: int = 240) -> pd.DataFrame:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="1h")
    wave = np.sin(np.arange(rows, dtype=float) / 8.0)
    mid = 2000.0 + np.arange(rows, dtype=float) * 0.05 + wave
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(hours=1),
            "mid_open": mid,
            "mid_high": mid + 1.0,
            "mid_low": mid - 1.0,
            "mid_close": mid + 0.2,
        }
    )


def _policy_frame(rows: int = 240) -> pd.DataFrame:
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=rows, freq="1h")
    ends = starts + pd.Timedelta(hours=1)
    cycle = np.resize(np.array([-2.0, -1.0, 1.0, 2.0]), rows)
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": ends,
            "hour_utc": ends.hour,
            "weekday": ends.weekday,
            "report_date": ends.floor("D"),
            "available_utc": ends,
            "atr14": np.ones(rows),
            "body_atr": cycle,
        }
    )
    for hours in (3, 6, 12, 24):
        frame[f"impulse_{hours}_atr"] = cycle
    for hours in (6, 12, 24, 48):
        frame[f"range_position_{hours}"] = np.resize(
            np.array([0.05, 0.95, 0.5, 0.10]), rows
        )
        frame[f"range_span_atr_{hours}"] = 2.0
    return frame


def test_future_prices_cannot_change_an_earlier_decision() -> None:
    original = _h1()
    changed = original.copy()
    changed.loc[changed.index > 100, ["mid_open", "mid_high", "mid_low", "mid_close"]] += 500.0
    first = SESSION.prepare_features(original, _config())
    second = SESSION.prepare_features(changed, _config())
    columns = [
        "atr14",
        "impulse_3_atr",
        "impulse_24_atr",
        "range_position_48",
        "range_span_atr_48",
    ]
    pd.testing.assert_series_equal(first.loc[100, columns], second.loc[100, columns])


def test_registered_mechanics_supply_fixed_directions() -> None:
    frame = _policy_frame(24)
    frame["hour_utc"] = np.resize(np.array([0, 6, 12, 18]), len(frame))
    frame["weekday"] = 0
    frame["impulse_6_atr"] = np.resize(np.array([-2.0, -1.0, 1.0, 2.0]), len(frame))

    carry_params = {"decision_hour": 0, "fixed_direction": -1, "weekday_set": "ALL"}
    mask, direction = SESSION.signal_mask_direction(
        frame, "UTC_HOUR_DIRECTIONAL_CARRY", carry_params
    )
    assert direction.eq(-1).all()
    assert mask.tolist()[:4] == [True, False, False, False]

    impulse_params = {
        "decision_hour": 6,
        "impulse_hours": 6,
        "impulse_min_atr": 0.5,
        "weekday_set": "ALL",
    }
    continuation_mask, continuation = SESSION.signal_mask_direction(
        frame, "PRIOR_SESSION_CONTINUATION", impulse_params
    )
    reversal_mask, reversal = SESSION.signal_mask_direction(
        frame, "PRIOR_SESSION_REVERSAL", impulse_params
    )
    assert continuation.iloc[1] == -1
    assert reversal.iloc[1] == 1
    assert continuation_mask.iloc[1]
    assert reversal_mask.iloc[1]

    range_params = {
        "decision_hour": 12,
        "range_hours": 12,
        "edge_fraction": 0.10,
        "range_min_atr": 1.0,
        "weekday_set": "ALL",
    }
    frame.loc[2, "range_position_12"] = 0.05
    range_mask, range_direction = SESSION.signal_mask_direction(
        frame, "SESSION_RANGE_EXTREME_REVERSION", range_params
    )
    assert range_mask.iloc[2]
    assert range_direction.iloc[2] == 1


def test_manifest_registers_attempts_10094_through_11093() -> None:
    manifest = SESSION.generate_manifest(
        _policy_frame(),
        pd.Timestamp("2020-01-01T00:00:00Z"),
        pd.Timestamp("2020-02-01T00:00:00Z"),
        attempts_before=10093,
        policies_per_mechanic=200,
        minimum_raw_signals=0,
    )
    assert len(manifest) == 1000
    assert manifest["attempt_no"].min() == 10094
    assert manifest["attempt_no"].max() == 11093
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()


def test_significance_blocks_include_zero_trade_days() -> None:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=10, freq="1D")
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(hours=1),
            "report_date": starts,
        }
    )
    trades = pd.DataFrame(
        {
            "report_date": [starts[0]],
            "stress_net_r": [1.0],
        }
    )
    value = SESSION.BASE._weekly_pvalue(
        trades,
        frame,
        pd.Timestamp("2024-01-01T00:00:00Z"),
        pd.Timestamp("2024-01-11T00:00:00Z"),
    )
    assert 0.0 < value < 0.5
