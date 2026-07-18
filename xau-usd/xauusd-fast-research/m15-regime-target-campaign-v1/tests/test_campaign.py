from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    execution_arrays,
    generate_manifest,
    prepare_features,
    signal_mask_direction,
    simulate_trade,
)


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "m15_regime_target_campaign_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _m15(rows: int = 192) -> pd.DataFrame:
    starts = pd.date_range("2024-01-02T00:00:00Z", periods=rows, freq="15min")
    close = pd.Series(2000.0 + np.sin(np.arange(rows) / 8.0), dtype=float)
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=15),
            "timestamp_utc": starts + pd.Timedelta(minutes=15),
            "bid_open": close - 0.06,
            "bid_high": close + 0.14,
            "bid_low": close - 0.26,
            "bid_close": close - 0.06,
            "ask_open": close + 0.06,
            "ask_high": close + 0.26,
            "ask_low": close - 0.14,
            "ask_close": close + 0.06,
            "mid_open": close,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "mid_close": close,
            "tick_count": 100,
        }
    )


class _Adaptive:
    @staticmethod
    def prepare_h4(frame: pd.DataFrame, settings: dict) -> pd.DataFrame:
        result = frame.copy()
        result["atr14"] = 1.0
        result["ema_fast"] = result["mid_close"].ewm(span=20, adjust=False).mean()
        result["ema_slow"] = result["mid_close"].ewm(span=80, adjust=False).mean()
        result["efficiency_ratio"] = 0.2
        result["range_atr"] = result["mid_high"] - result["mid_low"]
        return result


class _Regimes:
    @staticmethod
    def classify_h4(h4: pd.DataFrame, settings: dict) -> pd.DataFrame:
        return h4

    @staticmethod
    def attach_regime(frame: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        result["regime"] = "CHOP"
        result["ema_slope_atr_h4"] = 0.0
        return result


def test_manifest_is_complete_unique_and_contiguous() -> None:
    manifest = generate_manifest(_config()["selection"])
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(17120, 18120))
    assert manifest["variant_id"].is_unique
    assert manifest.groupby("regime_owner").size().to_dict() == {
        "CHOP": 500,
        "TRANSITION": 500,
    }


def test_future_price_changes_do_not_change_prior_intraday_features() -> None:
    original = _m15()
    altered = original.copy()
    price_columns = [
        "bid_open", "bid_high", "bid_low", "bid_close",
        "ask_open", "ask_high", "ask_low", "ask_close",
        "mid_open", "mid_high", "mid_low", "mid_close",
    ]
    altered.loc[144:, price_columns] += 500.0
    left = prepare_features(original, pd.DataFrame(), _config(), _Adaptive, _Regimes).iloc[:144]
    right = prepare_features(altered, pd.DataFrame(), _config(), _Adaptive, _Regimes).iloc[:144]
    columns = [
        "day_open", "anchored_vwap", "asian_high", "asian_low", "asian_mid",
        "prior_day_high", "prior_day_low", "last_resolved_regime",
        "transition_age_m15",
    ]
    pd.testing.assert_frame_equal(left[columns], right[columns])


def test_stop_wins_when_stop_and_target_share_a_bar() -> None:
    frame = _m15(4)
    frame["atr14"] = 1.0
    frame.loc[1, ["ask_open", "bid_open"]] = [100.0, 99.9]
    frame.loc[1, ["bid_low", "bid_high"]] = [98.0, 102.0]
    arrays = execution_arrays(frame)
    execution = _config()["execution"]
    outcome = simulate_trade(arrays, 0, 1, 101.0, 1.0, 1.0, execution)
    assert outcome is not None
    assert outcome["exit_reason"] == "STOP_AMBIGUOUS"
    assert outcome["exit_price"] == 99.0


def test_shock_is_never_eligible() -> None:
    frame = prepare_features(_m15(), pd.DataFrame(), _config(), _Adaptive, _Regimes)
    frame["regime"] = "UNSAFE_SHOCK"
    params = {
        "deviation_atr": 0.4,
        "body_min": 0.0,
        "require_confirmation": False,
        "minimum_day_bars": 16,
        "hour_window": "ALL",
        "stop_atr": 1.0,
        "hold_hours": 4,
        "target_r_min": 0.75,
        "target_r_max": 4.0,
    }
    mask, _, _ = signal_mask_direction(frame, "CHOP_SESSION_VWAP_TARGET", params)
    assert not mask.any()
