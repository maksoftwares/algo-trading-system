from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m5_microstructure_campaign_test_module", ROOT / "src" / "campaign.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(ROOT / "src" / "campaign.py")
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)


def _raw_frame(rows: int = 8) -> pd.DataFrame:
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=rows, freq="5min")
    mid = 100.0 + np.arange(rows) * 0.1
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "bid_open": mid - 0.1,
            "bid_high": mid + 0.4,
            "bid_low": mid - 0.4,
            "bid_close": mid,
            "ask_open": mid + 0.1,
            "ask_high": mid + 0.6,
            "ask_low": mid - 0.2,
            "ask_close": mid + 0.2,
            "mid_open": mid,
            "mid_high": mid + 0.5,
            "mid_low": mid - 0.5,
            "mid_close": mid + 0.1,
            "tick_signed_move": np.ones(rows),
            "tick_realized_variance": np.ones(rows),
            "tick_spread_last": np.ones(rows),
            "tick_book_imbalance_mean": np.full(rows, 0.3),
            "tick_imbalance_5m": np.full(rows, 0.1),
            "tick_imbalance_15m": np.full(rows, 0.08),
            "price_efficiency_5m": np.full(rows, 0.6),
            "quote_intensity_ratio": np.full(rows, 1.2),
        }
    )


def test_manifest_has_exactly_one_thousand_unique_attempts() -> None:
    manifest = CAMPAIGN.generate_manifest(6093, 200)
    assert len(manifest) == 1000
    assert manifest["attempt_no"].min() == 6094
    assert manifest["attempt_no"].max() == 7093
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()


def test_spread_and_variance_baselines_exclude_current_bar() -> None:
    frame = _raw_frame(6)
    frame.loc[4, "tick_spread_last"] = 10.0
    frame.loc[4, "tick_realized_variance"] = 8.0
    config = {"features": {"atr_period": 2, "baseline_bars": 3, "baseline_minimum_bars": 2}}
    prepared = CAMPAIGN.prepare_features(frame, config)
    assert prepared.loc[4, "spread_ratio"] == 10.0
    assert prepared.loc[4, "variance_ratio"] == 8.0


def test_flow_continuation_uses_completed_pressure_direction() -> None:
    frame = _raw_frame(20)
    config = {"features": {"atr_period": 2, "baseline_bars": 3, "baseline_minimum_bars": 2}}
    prepared = CAMPAIGN.prepare_features(frame, config)
    params = {
        "imbalance_window": "15m",
        "imbalance_min": 0.05,
        "book_min": 0.1,
        "intensity_min": 1.0,
        "efficiency_min": 0.3,
        "spread_ratio_max": 1.2,
        "require_body_alignment": True,
        "require_trend_alignment": False,
        "session": "ALL",
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        prepared, "FLOW_CONTINUATION", params
    )
    assert bool(mask.iloc[-1])
    assert int(direction.iloc[-1]) == 1


def test_all_mechanics_tolerate_warmup_nans() -> None:
    frame = _raw_frame(20)
    config = {"features": {"atr_period": 2, "baseline_bars": 3, "baseline_minimum_bars": 2}}
    prepared = CAMPAIGN.prepare_features(frame, config)
    examples = {
        "FLOW_CONTINUATION": {
            "imbalance_window": "15m",
            "imbalance_min": 0.05,
            "book_min": 0.0,
            "intensity_min": 0.6,
            "efficiency_min": 0.1,
            "spread_ratio_max": 1.3,
            "require_body_alignment": False,
            "require_trend_alignment": False,
            "session": "ALL",
        },
        "FLOW_EXHAUSTION": {
            "impulse_bars": 12,
            "impulse_atr_min": 0.4,
            "impulse_tick_min": 0.03,
            "reversal_book_min": 0.0,
            "reversal_location_min": 0.45,
            "intensity_min": 0.8,
            "session": "ALL",
        },
        "BOOK_ABSORPTION": {
            "price_window": 6,
            "move_atr_min": 0.2,
            "reversal_book_min": 0.08,
            "price_tick_min": 0.0,
            "efficiency_max": 1.0,
            "intensity_min": 0.6,
            "session": "ALL",
        },
        "LIQUIDITY_SHOCK_REVERSION": {
            "impulse_bars": 3,
            "move_atr_min": 0.5,
            "spread_ratio_min": 1.05,
            "variance_ratio_min": 1.1,
            "intensity_min": 1.0,
            "reversal_location_min": 0.35,
            "session": "ALL",
        },
        "POST_SHOCK_NORMALIZATION": {
            "prior_spread_ratio_min": 1.15,
            "current_spread_ratio_max": 1.25,
            "imbalance_min": 0.02,
            "book_min": 0.0,
            "intensity_min": 0.7,
            "require_body_alignment": False,
            "session": "ALL",
        },
    }
    for mechanic, params in examples.items():
        mask, direction = CAMPAIGN.signal_mask_direction(prepared, mechanic, params)
        assert len(mask) == len(prepared)
        assert direction.notna().all()


def test_long_execution_enters_ask_and_exits_bid_target() -> None:
    starts = pd.date_range("2020-01-01T00:00:00", periods=5, freq="5min").to_numpy()
    ends = starts + np.timedelta64(5, "m")
    arrays = {
        "starts": starts,
        "ends": ends,
        "atr": np.ones(5),
        "bid_open": np.array([99.9, 100.0, 100.0, 100.0, 100.0]),
        "bid_high": np.array([100.2, 101.3, 100.2, 100.2, 100.2]),
        "bid_low": np.array([99.7, 99.8, 99.8, 99.8, 99.8]),
        "bid_close": np.array([100.0, 101.0, 100.0, 100.0, 100.0]),
        "ask_open": np.array([100.1, 100.2, 100.2, 100.2, 100.2]),
        "ask_high": np.array([100.4, 101.5, 100.4, 100.4, 100.4]),
        "ask_low": np.array([99.9, 100.0, 100.0, 100.0, 100.0]),
        "ask_close": np.array([100.2, 101.2, 100.2, 100.2, 100.2]),
    }
    geometry = {"stop_atr": 1.0, "target_r": 1.0, "hold_bars": 2}
    execution = {
        "maximum_entry_spread_r": 0.3,
        "maximum_research_risk_usd": 50.0,
        "current_account_risk_usd": 8.0,
        "ounces_at_lot_size": 1.0,
        "extra_execution_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
    }
    outcome = CAMPAIGN.simulate_trade(
        arrays,
        0,
        1,
        geometry,
        execution,
        pd.Timestamp("2020-01-02T00:00:00Z"),
    )
    assert outcome is not None
    assert outcome["entry_price"] == 100.2
    assert outcome["exit_price"] == 101.2
    assert outcome["exit_reason"] == "TARGET"
    assert outcome["net_r"] == 1.0


def test_same_bar_ambiguity_is_stop_first() -> None:
    starts = pd.date_range("2020-01-01T00:00:00", periods=5, freq="5min").to_numpy()
    ends = starts + np.timedelta64(5, "m")
    arrays = {
        "starts": starts,
        "ends": ends,
        "atr": np.ones(5),
        "bid_open": np.full(5, 100.0),
        "bid_high": np.array([100.2, 101.4, 100.2, 100.2, 100.2]),
        "bid_low": np.array([99.8, 98.8, 99.8, 99.8, 99.8]),
        "bid_close": np.full(5, 100.0),
        "ask_open": np.full(5, 100.2),
        "ask_high": np.full(5, 100.4),
        "ask_low": np.full(5, 100.0),
        "ask_close": np.full(5, 100.2),
    }
    outcome = CAMPAIGN.simulate_trade(
        arrays,
        0,
        1,
        {"stop_atr": 1.0, "target_r": 1.0, "hold_bars": 2},
        {
            "maximum_entry_spread_r": 0.3,
            "maximum_research_risk_usd": 50.0,
            "current_account_risk_usd": 8.0,
            "ounces_at_lot_size": 1.0,
            "extra_execution_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        },
        pd.Timestamp("2020-01-02T00:00:00Z"),
    )
    assert outcome is not None
    assert outcome["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert outcome["net_r"] == -1.0


def test_drawdown_includes_starting_equity() -> None:
    assert CAMPAIGN.closed_drawdown(pd.Series([-2.0, 3.0])) == 2.0


def test_bh_adjustment_is_bounded_and_ordered() -> None:
    pvalues = pd.Series([0.001, 0.02, 0.04, 0.5])
    adjusted = CAMPAIGN.benjamini_hochberg(pvalues)
    assert adjusted.between(0.0, 1.0).all()
    assert adjusted.is_monotonic_increasing


def test_contract_registers_no_execution_or_training_authority() -> None:
    config = json.loads(
        (ROOT / "config" / "m5_microstructure_mechanics_v1.json").read_text(
            encoding="utf-8"
        )
    )
    controls = config["research_controls"]
    assert controls["registered_policy_count"] == 1000
    assert controls["campaign_attempts_before_v1"] == 6093
    assert controls["same_version_post_outcome_tuning_authorized"] is False
    for name in (
        "paid_data_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "model_training_authorized",
        "ea_consumption_authorized",
    ):
        assert controls[name] is False


def test_small_policy_evaluation_runs_end_to_end() -> None:
    raw = _raw_frame(80)
    config = {
        "features": {
            "atr_period": 2,
            "baseline_bars": 3,
            "baseline_minimum_bars": 2,
        },
        "windows": {
            "discovery": ["2020-01-01T00:00:00Z", "2020-01-01T06:00:00Z"]
        },
        "segments": {
            "discovery": [
                ["2020-01-01T00:00:00Z", "2020-01-01T06:00:00Z"]
            ]
        },
        "mechanics": {
            "FLOW_CONTINUATION": {
                "stop_atr": 1.0,
                "target_r": 1.0,
                "hold_bars": 2,
            }
        },
        "execution": {
            "maximum_entry_spread_r": 0.5,
            "maximum_research_risk_usd": 50.0,
            "current_account_risk_usd": 8.0,
            "ounces_at_lot_size": 1.0,
            "extra_execution_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
            "cooldown_bars": 1,
            "maximum_trades_per_policy_utc_day": 6,
        },
        "gates": {
            "discovery": {
                "minimum_trades": 1,
                "minimum_trades_per_source_day": 0.0,
                "minimum_stress_pf": 0.0,
                "minimum_average_stress_r": -10.0,
                "minimum_positive_month_share": 0.0,
                "maximum_closed_drawdown_r": 100.0,
                "top_winners_removed": 0,
                "minimum_profitable_segments": 0,
                "minimum_worst_segment_pf": 0.0,
                "maximum_fdr_qvalue": 1.0,
            }
        },
    }
    frame = CAMPAIGN.prepare_features(raw, config)
    params = {
        "imbalance_window": "15m",
        "imbalance_min": 0.01,
        "book_min": 0.0,
        "intensity_min": 0.3,
        "efficiency_min": 0.0,
        "spread_ratio_max": 2.0,
        "require_body_alignment": False,
        "require_trend_alignment": False,
        "session": "ALL",
    }
    manifest = pd.DataFrame(
        [
            {
                "attempt_no": 6094,
                "policy_id": "synthetic",
                "mechanic": "FLOW_CONTINUATION",
                "parameters_json": json.dumps(params, sort_keys=True),
            }
        ]
    )
    metrics, _ = CAMPAIGN.evaluate_policies(frame, manifest, config, "discovery")
    assert len(metrics) == 1
    assert metrics.loc[0, "trades"] > 0
    assert "maximum_fdr_qvalue" in json.loads(metrics.loc[0, "gate_checks_json"])
