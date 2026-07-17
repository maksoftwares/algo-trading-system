from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "volatility.py"
SPEC = importlib.util.spec_from_file_location(
    "cftc_options_volatility_routing_v2_tests", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
VOLATILITY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VOLATILITY
SPEC.loader.exec_module(VOLATILITY)


def _config() -> dict:
    return {
        "features": {
            "h1_atr_period": 3,
            "positioning_z_lookbacks": [3],
            "maximum_positioning_staleness_days": 14,
            "atr_baseline_bars": 12,
            "atr_baseline_minimum_bars": 6,
        }
    }


def _positioning() -> pd.DataFrame:
    reports = pd.date_range("2023-01-03T00:00:00Z", periods=9, freq="7D")
    option_oi = np.array(
        [100.0, 112.0, 125.0, 141.0, 150.0, 177.0, 205.0, 218.0, 260.0]
    )
    frame = pd.DataFrame(
        {
            "report_date": reports,
            "available_utc": reports + pd.Timedelta(days=6),
            "open_interest_all_combined": 1000.0 + option_oi,
            "open_interest_all_futures": np.full(len(reports), 1000.0),
            "options_open_interest_delta_equivalent": option_oi,
        }
    )
    sequence = np.arange(len(reports), dtype=float)
    for category, multiplier in (
        ("producer", -1.0),
        ("swap", -0.5),
        ("managed_money", 1.0),
        ("other_reportable", 0.25),
        ("nonreportable", 0.1),
    ):
        options_net = multiplier * (10.0 + sequence)
        futures_net = multiplier * (20.0 + sequence)
        frame[f"{category}_options_net"] = options_net
        frame[f"{category}_futures_net"] = futures_net
        frame[f"{category}_combined_net"] = options_net + futures_net
        frame[f"{category}_options_long"] = 40.0 + sequence + np.maximum(options_net, 0.0)
        frame[f"{category}_options_short"] = 40.0 + sequence + np.maximum(-options_net, 0.0)
    for category in ("swap", "managed_money", "other_reportable"):
        frame[f"{category}_options_spread"] = 5.0 + sequence
    return frame


def _h1() -> pd.DataFrame:
    starts = pd.date_range("2023-01-01T00:00:00Z", periods=1800, freq="1h")
    mid = 1800.0 + np.arange(len(starts), dtype=float) * 0.02
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


def _policy_frame(rows: int = 96) -> pd.DataFrame:
    ends = pd.date_range("2020-01-01T01:00:00Z", periods=rows, freq="1h")
    cycle = np.resize(np.array([-2.0, -1.0, 1.0, 2.0]), rows)
    frame = pd.DataFrame(
        {
            "bar_end_utc": ends,
            "hour_utc": ends.hour,
            "atr14": np.ones(rows),
            "atr_ratio_causal": np.ones(rows),
            "body_atr": cycle,
            "mid_close": 100.0 + cycle,
        }
    )
    for bars in (3, 6, 12, 24):
        frame[f"impulse_{bars}_atr"] = cycle
    for bars in (6, 12, 24, 48):
        frame[f"prior_high_{bars}"] = np.full(rows, 100.5)
        frame[f"prior_low_{bars}"] = np.full(rows, 99.5)
    for prefix in (
        "options_oi_growth_z",
        "mm_spread_build_z",
        "swap_spread_build_z",
        "gross_activity_level_z",
    ):
        for lookback in (52, 104, 156):
            frame[f"{prefix}_{lookback}"] = cycle
    return frame


def test_weekly_activity_is_computed_before_hourly_asof_join() -> None:
    positioning = _positioning()
    result = VOLATILITY.prepare_features(_h1(), positioning, _config())
    option_change = np.log(positioning["options_open_interest_delta_equivalent"]).diff()
    report_index = 5
    expected = (
        option_change.iloc[report_index] - option_change.iloc[2:5].mean()
    ) / option_change.iloc[2:5].std(ddof=0)
    available = positioning.loc[report_index, "available_utc"]
    at_release = result.loc[result["bar_end_utc"].eq(available)].iloc[0]
    twelve_hours_later = result.loc[
        result["bar_end_utc"].eq(available + pd.Timedelta(hours=12))
    ].iloc[0]
    assert np.isclose(at_release["options_oi_growth_z_3"], expected)
    assert np.isclose(twelve_hours_later["options_oi_growth_z_3"], expected)
    assert at_release["activity_available_utc"] == available


def test_activity_asof_join_never_exposes_future_report() -> None:
    positioning = _positioning()
    result = VOLATILITY.prepare_features(_h1(), positioning, _config())
    observed = result["activity_available_utc"].notna()
    assert (
        result.loc[observed, "activity_available_utc"]
        <= result.loc[observed, "bar_end_utc"]
    ).all()


def test_manifest_registers_attempts_9094_through_10093() -> None:
    manifest = VOLATILITY.generate_manifest(
        _policy_frame(),
        pd.Timestamp("2020-01-01T00:00:00Z"),
        pd.Timestamp("2020-02-01T00:00:00Z"),
        attempts_before=9093,
        policies_per_mechanic=200,
        minimum_raw_signals=0,
    )
    assert len(manifest) == 1000
    assert manifest["attempt_no"].min() == 9094
    assert manifest["attempt_no"].max() == 10093
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()


def test_price_structure_supplies_direction() -> None:
    frame = _policy_frame(4)
    breakout = {
        "lookback": 52,
        "activity_threshold_z": 0.5,
        "session": "ALL",
        "channel_bars": 6,
        "breakout_buffer_atr": 0.0,
        "compression_max": 99.0,
    }
    mask, direction = VOLATILITY.signal_mask_direction(
        frame, "OPTIONS_OI_EXPANSION_BREAKOUT", breakout
    )
    assert direction.tolist() == [-1, -1, 1, 1]
    assert mask.tolist() == [False, False, True, True]

    reversal = {
        "lookback": 52,
        "activity_threshold_z": 0.5,
        "session": "ALL",
        "impulse_hours": 3,
        "impulse_min_atr": 0.25,
        "confirmation_min_atr": 0.1,
    }
    frame["options_oi_growth_z_52"] = -2.0
    frame["body_atr"] = -frame["impulse_3_atr"]
    mask, direction = VOLATILITY.signal_mask_direction(
        frame, "OPTIONS_OI_CONTRACTION_REVERSAL", reversal
    )
    assert direction.tolist() == [1, 1, -1, -1]
    assert mask.all()
