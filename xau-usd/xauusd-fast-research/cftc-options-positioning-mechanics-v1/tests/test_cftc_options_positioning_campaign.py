from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "campaign.py"
SPEC = importlib.util.spec_from_file_location("cftc_options_campaign_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)


def _config() -> dict:
    return {
        "features": {
            "h1_atr_period": 3,
            "positioning_z_lookbacks": [3, 4, 5],
            "maximum_positioning_staleness_days": 14,
        }
    }


def _positioning(rows: int = 12) -> pd.DataFrame:
    reports = pd.date_range("2023-01-03T00:00:00Z", periods=rows, freq="7D")
    values = np.arange(rows, dtype=float)
    frame = pd.DataFrame(
        {
            "report_date": reports,
            "available_utc": reports + pd.Timedelta(days=6),
            "open_interest_all_combined": 1200.0 + values,
            "open_interest_all_futures": 1000.0 + values,
            "options_open_interest_delta_equivalent": np.full(rows, 200.0),
        }
    )
    for category, multiplier in (
        ("producer", -1.0),
        ("swap", -0.5),
        ("managed_money", 1.0),
        ("other_reportable", 0.25),
        ("nonreportable", 0.1),
    ):
        frame[f"{category}_options_net"] = multiplier * (10.0 + values)
        frame[f"{category}_futures_net"] = multiplier * (20.0 + values)
        frame[f"{category}_combined_net"] = (
            frame[f"{category}_options_net"] + frame[f"{category}_futures_net"]
        )
    return frame


def _h1(rows: int = 240) -> pd.DataFrame:
    starts = pd.date_range("2023-01-01T00:00:00Z", periods=rows, freq="1h")
    mid = 1800.0 + np.arange(rows, dtype=float) * 0.2
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


def _policy_frame(rows: int = 500) -> pd.DataFrame:
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=rows, freq="1h")
    cycle = np.tile(np.array([-2.0, -1.0, 1.0, 2.0]), rows // 4 + 1)[:rows]
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(hours=1),
            "hour_utc": (starts + pd.Timedelta(hours=1)).hour,
            "atr14": np.ones(rows),
            "body_atr": cycle,
            "prior_body_atr": np.roll(cycle, 1),
            "return_6h_atr": cycle,
            "managed_money_options_net_share": cycle * 0.01,
            "producer_options_net_share": -cycle * 0.01,
        }
    )
    prefixes = (
        "mm_options_flow_z",
        "mm_options_level_z",
        "producer_mm_divergence_z",
        "swap_options_flow_z",
        "options_futures_dislocation_z",
    )
    for prefix in prefixes:
        for lookback in (52, 104, 156):
            frame[f"{prefix}_{lookback}"] = cycle
    return frame


def test_positioning_zscore_excludes_current_observation() -> None:
    positioning = _positioning(12)
    prepared = CAMPAIGN.prepare_positioning(positioning, _config())
    share = positioning["managed_money_options_net"] / positioning[
        "options_open_interest_delta_equivalent"
    ]
    expected = (share.iloc[5] - share.iloc[2:5].mean()) / share.iloc[2:5].std(ddof=0)
    assert np.isclose(prepared.loc[5, "mm_options_level_z_3"], expected)


def test_asof_join_never_exposes_future_report() -> None:
    result = CAMPAIGN.prepare_features(_h1(), _positioning(), _config())
    before = result.loc[result["bar_end_utc"] < pd.Timestamp("2023-01-09T00:00:00Z")]
    assert before["report_date"].isna().all()
    after = result.loc[
        result["bar_end_utc"].eq(pd.Timestamp("2023-01-09T00:00:00Z"))
    ].iloc[0]
    assert after["report_date"] == pd.Timestamp("2023-01-03T00:00:00Z")


def test_manifest_registers_exactly_one_thousand_attempts() -> None:
    frame = _policy_frame()
    manifest = CAMPAIGN.generate_manifest(
        frame,
        pd.Timestamp("2020-01-01T00:00:00Z"),
        pd.Timestamp("2020-02-01T00:00:00Z"),
        8093,
        200,
        0,
    )
    assert len(manifest) == 1000
    assert manifest["attempt_no"].min() == 8094
    assert manifest["attempt_no"].max() == 9093
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()


def test_mechanic_direction_mappings_are_fixed() -> None:
    frame = _policy_frame(8)
    params = {
        "lookback": 52,
        "threshold_z": 0.5,
        "price_filter": "NONE",
        "price_min_atr": 0.0,
        "crowd_extension_atr_min": 0.0,
        "require_opposite_option_sides": False,
        "session": "ALL",
        "stop_atr": 1.0,
        "target_r": 1.5,
        "hold_hours": 4,
    }
    _, continuation = CAMPAIGN.signal_mask_direction(
        frame, "MM_OPTIONS_FLOW_CONTINUATION", params
    )
    _, crowding = CAMPAIGN.signal_mask_direction(
        frame, "MM_OPTIONS_CROWDING_REVERSAL", params
    )
    _, swap = CAMPAIGN.signal_mask_direction(
        frame, "SWAP_OPTIONS_HEDGE_PRESSURE", params
    )
    assert continuation.iloc[0] == -1
    assert crowding.iloc[0] == 1
    assert swap.iloc[0] == 1


def test_bh_adjustment_is_monotone_in_rank() -> None:
    adjusted = CAMPAIGN.benjamini_hochberg(pd.Series([0.001, 0.02, 0.5]))
    assert adjusted.tolist() == [0.003, 0.03, 0.5]


def test_closed_drawdown_includes_initial_equity_peak() -> None:
    assert CAMPAIGN.closed_drawdown(pd.Series([-2.0, 3.0])) == 2.0


def test_execution_uses_long_ask_and_stop_first_on_ambiguous_bar() -> None:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=60, freq="5min")
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "bid_open": np.full(60, 100.0),
            "bid_high": np.full(60, 102.0),
            "bid_low": np.full(60, 99.0),
            "bid_close": np.full(60, 100.0),
            "ask_open": np.full(60, 100.2),
            "ask_high": np.full(60, 102.2),
            "ask_low": np.full(60, 99.2),
            "ask_close": np.full(60, 100.2),
        }
    )
    outcome = CAMPAIGN.simulate_trade(
        CAMPAIGN.execution_arrays(frame),
        starts[0],
        1.0,
        1,
        {"stop_atr": 1.0, "target_r": 1.5, "hold_hours": 4},
        {
            "maximum_entry_spread_r": 0.5,
            "maximum_research_risk_usd": 50.0,
            "current_account_risk_usd": 8.0,
            "ounces_at_lot_size": 1.0,
            "extra_execution_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        },
        pd.Timestamp("2024-01-02T00:00:00Z"),
    )
    assert outcome is not None
    assert outcome["entry_price"] == 100.2
    assert outcome["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert outcome["net_r"] == -1.0
