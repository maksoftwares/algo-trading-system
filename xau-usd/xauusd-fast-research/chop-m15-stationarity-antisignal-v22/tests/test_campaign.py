from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    add_m15_stationarity_features,
    parameter_space,
    signal_mask_direction,
    simulate_trade,
)


def _load_v21():
    path = ROOT.parent / "chop-m15-stationarity-campaign-v21" / "src" / "campaign.py"
    spec = importlib.util.spec_from_file_location(
        "chop_m15_stationarity_v21_test_source", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V21 = _load_v21()


class _RegimeModule:
    @staticmethod
    def atr(frame: pd.DataFrame, period: int) -> pd.Series:
        del period
        return pd.Series(np.ones(len(frame)), index=frame.index)


def _m15_frame() -> pd.DataFrame:
    timestamps = pd.date_range("2023-01-01T00:15:00Z", periods=1000, freq="15min")
    close = 100.0 + np.sin(np.arange(1000) * np.pi / 8.0)
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "mid_open": close,
            "mid_high": close + 0.5,
            "mid_low": close - 0.5,
            "mid_close": close,
        }
    )


def _config() -> dict[str, object]:
    return {"features": {"state_atr_period": 14, "h1_atr_period": 14}}


def _signal_frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-01T09:00:00Z", periods=6, freq="5min")
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "timestamp_utc": starts + pd.Timedelta(minutes=5),
            "regime": ["TREND_UP", "CHOP", "CHOP", "CHOP", "TREND_DOWN", "CHOP"],
            "hour_utc_custom": 9,
            "risk_atr": 2.0,
            "spread_ratio": 1.0,
            "m15_state_age_m5": [0, 0, 1, 2, 0, 0],
            "z_192": [2.0] * 6,
            "phi_192": [0.8] * 6,
            "half_life_192": [10.0] * 6,
            "mean_slope_atr_192": [0.1] * 6,
            "return_3": [-0.2] * 6,
            "return_12": [-0.3] * 6,
            "tick_imbalance_15m": [-0.1] * 6,
        }
    )


def _ar1_params() -> dict[str, object]:
    return {
        "stationarity_window": 192,
        "z_abs_min": 1.25,
        "phi_min": 0.6,
        "phi_max": 0.97,
        "half_life_max": 36.0,
        "mean_slope_abs_max": 0.35,
        "m15_state_age_m5_max": 2,
        "m5_confirmation_window": 3,
        "m5_alignment_min": 0.03,
        "flow_alignment_min": 0.01,
        "session": "ALL",
        "geometry_id": "FAST",
    }


def test_stationarity_features_do_not_change_before_future_edit() -> None:
    frame = _m15_frame()
    before = add_m15_stationarity_features(frame, _config(), _RegimeModule)
    changed = frame.copy()
    changed.loc[950:, "mid_close"] += 50.0
    after = add_m15_stationarity_features(changed, _config(), _RegimeModule)
    pd.testing.assert_series_equal(
        before.loc[:949, "z_192"], after.loc[:949, "z_192"]
    )
    pd.testing.assert_series_equal(
        before.loc[:949, "variance_ratio_4_192"],
        after.loc[:949, "variance_ratio_4_192"],
    )


def test_stationarity_features_become_finite_after_warmup() -> None:
    result = add_m15_stationarity_features(_m15_frame(), _config(), _RegimeModule)
    assert np.isfinite(result.loc[900, "z_192"])
    assert np.isfinite(result.loc[900, "hurst_192"])
    assert np.isfinite(result.loc[900, "return_acf_1_192"])


def test_deterministic_design_has_1000_unique_rows() -> None:
    rows = parameter_space("CHOP_M15_AR1_STATIONARITY_CONTINUATION", 1000)
    assert len(rows) == 1000
    assert len({repr(sorted(row.items())) for row in rows}) == 1000


def test_ar1_signal_is_restricted_to_chop() -> None:
    mask, direction = signal_mask_direction(
        _signal_frame(), "CHOP_M15_AR1_STATIONARITY_CONTINUATION", _ar1_params()
    )
    assert mask.tolist() == [False, True, True, True, False, True]
    assert direction.loc[mask].eq(1).all()


def test_v22_is_exact_direction_inverse_of_v21() -> None:
    frame = _signal_frame()
    direct_mask, direct_direction = V21.signal_mask_direction(
        frame, "CHOP_M15_AR1_MEAN_REVERSION", _ar1_params()
    )
    inverse_mask, inverse_direction = signal_mask_direction(
        frame, "CHOP_M15_AR1_STATIONARITY_CONTINUATION", _ar1_params()
    )
    assert direct_mask.equals(inverse_mask)
    assert inverse_direction.equals(-direct_direction)


def test_future_state_does_not_change_prior_signals() -> None:
    frame = _signal_frame()
    before, _ = signal_mask_direction(
        frame, "CHOP_M15_AR1_STATIONARITY_CONTINUATION", _ar1_params()
    )
    changed = frame.copy()
    changed.loc[4:, "z_192"] = -2.0
    changed.loc[4:, "tick_imbalance_15m"] = 0.1
    after, _ = signal_mask_direction(
        changed, "CHOP_M15_AR1_STATIONARITY_CONTINUATION", _ar1_params()
    )
    assert before.loc[:3].equals(after.loc[:3])


def _arrays() -> dict[str, np.ndarray]:
    starts = pd.date_range("2024-01-02T10:00:00Z", periods=15, freq="5min")
    naive = starts.tz_localize(None).to_numpy()
    bid_high = np.full(15, 100.2)
    bid_low = np.full(15, 99.8)
    bid_high[1] = 102.0
    bid_low[1] = 98.8
    return {
        "starts": naive,
        "ends": naive + np.timedelta64(5, "m"),
        "atr": np.ones(15),
        "bid_open": np.full(15, 100.0),
        "bid_high": bid_high,
        "bid_low": bid_low,
        "bid_close": np.full(15, 100.0),
        "ask_open": np.full(15, 100.1),
        "ask_high": bid_high + 0.1,
        "ask_low": bid_low + 0.1,
        "ask_close": np.full(15, 100.1),
    }


def _execution() -> dict[str, float]:
    return {
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "extra_execution_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }


def test_m5_same_bar_collision_is_stop_first() -> None:
    geometry = {"stop_atr": 1.0, "target_r": 1.5, "hold_bars": 12}
    result = simulate_trade(
        _arrays(),
        0,
        1,
        geometry,
        _execution(),
        pd.Timestamp("2024-01-03T00:00:00Z"),
    )
    assert result is not None
    assert result["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert result["gross_r"] == -1.0


def test_noncontiguous_next_m5_bar_rejects_entry() -> None:
    arrays = _arrays()
    arrays["starts"] = arrays["starts"].copy()
    arrays["starts"][1] += np.timedelta64(5, "m")
    result = simulate_trade(
        arrays,
        0,
        1,
        {"stop_atr": 1.0, "target_r": 1.5, "hold_bars": 12},
        _execution(),
        pd.Timestamp("2024-01-03T00:00:00Z"),
    )
    assert result is None
