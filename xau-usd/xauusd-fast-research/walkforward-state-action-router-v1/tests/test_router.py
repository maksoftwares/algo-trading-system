from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from router import (  # noqa: E402
    generate_manifest,
    posterior_lcb,
    select_trades,
    simulate_fixed_trade,
    state_codes,
    walkforward_statistics,
)


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "walkforward_state_action_router_v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_manifest_is_exactly_balanced_and_numbered() -> None:
    manifest = generate_manifest(_config())
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(22120, 23120))
    assert manifest["variant_id"].is_unique
    assert manifest.groupby("regime_owner").size().to_dict() == {
        "CHOP": 500,
        "TRANSITION": 500,
    }
    assert manifest.groupby(["regime_owner", "schema_id"]).size().eq(50).all()


def test_direction_aligned_state_is_action_specific() -> None:
    frame = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(["2024-01-02T12:00:00Z"]),
            "atr14": [2.0],
            "mid_close": [2020.0],
            "prior_low_24": [2010.0],
            "prior_high_24": [2030.0],
            "return_16_local": [4.0],
            "vwap_deviation_atr": [1.0],
            "ema_fast": [2018.0],
            "candle_direction": [1],
            "last_resolved_regime": ["CHOP"],
            "adx_h4": [18.0],
            "er_h4": [0.10],
            "atr_ratio": [1.0],
            "spread_atr": [0.2],
            "quote_intensity_ratio": [1.0],
            "body": [0.5],
            "transition_age_m15": [0],
            "range_atr": [1.0],
        }
    )
    codes, cardinality = state_codes(
        frame,
        np.array([0, 0]),
        np.array([-1, 1]),
        "CHOP",
        "C03_MOMENTUM_VWAP",
        _config(),
    )
    assert cardinality > 1
    assert np.all(codes >= 0)
    assert codes[0] != codes[1]


def test_walkforward_excludes_purge_and_test_outcomes() -> None:
    config = _config()
    config["source"]["start_utc"] = "2010-01-01T00:00:00Z"
    config["walk_forward"].update(
        {
            "oos_start_utc": "2012-01-01T00:00:00Z",
            "oos_end_exclusive_utc": "2012-07-01T00:00:00Z",
            "evaluation_block_months": 6,
            "purge_hours": 24,
            "history_modes": ["EXPANDING"],
        }
    )
    labels = pd.DataFrame(
        {
            "signal_time": pd.to_datetime(
                [
                    "2011-06-01T00:00:00Z",
                    "2011-06-01T00:00:00Z",
                    "2011-12-31T12:00:00Z",
                    "2011-12-31T12:00:00Z",
                    "2012-01-02T00:00:00Z",
                    "2012-01-02T00:00:00Z",
                    "2012-02-01T00:00:00Z",
                    "2012-02-01T00:00:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2011-06-01T01:00:00Z",
                    "2011-06-01T01:00:00Z",
                    "2011-12-31T13:00:00Z",
                    "2011-12-31T13:00:00Z",
                    "2012-01-02T01:00:00Z",
                    "2012-01-02T01:00:00Z",
                    "2012-02-01T01:00:00Z",
                    "2012-02-01T01:00:00Z",
                ]
            ),
            "direction_sign": [-1, 1, -1, 1, -1, 1, -1, 1],
            "stress_net_r": [-1.0, 1.0, 100.0, 100.0, 200.0, 200.0, 300.0, 300.0],
        }
    )
    stats, diagnostics = walkforward_statistics(
        labels, np.zeros(len(labels), dtype=np.int32), 1, "EXPANDING", config
    )
    assert stats["cell_n"][4:8].tolist() == [1, 1, 1, 1]
    assert stats["cell_sum"][4:8].tolist() == [-1.0, 1.0, -1.0, 1.0]
    assert diagnostics[0]["training_action_rows"] == 2


def test_posterior_requires_support_and_shrinks_to_baseline() -> None:
    stats = {
        "oos": np.array([True]),
        "cell_n": np.array([10]),
        "cell_sum": np.array([5.0]),
        "cell_sumsq": np.array([10.0]),
        "global_n": np.array([100]),
        "global_sum": np.array([0.0]),
        "global_sumsq": np.array([100.0]),
    }
    rejected, _, _ = posterior_lcb(stats, 20, 10.0, 1.0, 50)
    accepted, mean, standard_error = posterior_lcb(stats, 10, 10.0, 1.0, 50)
    assert np.isneginf(rejected[0])
    assert 0.0 < mean[0] < 0.5
    assert standard_error[0] > 0.0
    assert np.isfinite(accepted[0])


def _paired_labels() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "signal_index": [0, 0, 1, 1],
            "direction_sign": [-1, 1, -1, 1],
            "direction": ["SHORT", "LONG", "SHORT", "LONG"],
            "signal_time": pd.to_datetime(
                [
                    "2024-01-02T00:00:00Z",
                    "2024-01-02T00:00:00Z",
                    "2024-01-02T01:00:00Z",
                    "2024-01-02T01:00:00Z",
                ]
            ),
            "entry_time": pd.to_datetime(
                [
                    "2024-01-02T00:00:00Z",
                    "2024-01-02T00:00:00Z",
                    "2024-01-02T01:00:00Z",
                    "2024-01-02T01:00:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2024-01-02T02:00:00Z",
                    "2024-01-02T02:00:00Z",
                    "2024-01-02T03:00:00Z",
                    "2024-01-02T03:00:00Z",
                ]
            ),
            "stress_net_r": [-1.0, 1.0, -1.0, 1.0],
        }
    )


def test_selection_chooses_one_direction_and_rejects_overlap() -> None:
    labels = _paired_labels()
    stats = {
        "oos": np.ones(4, dtype=bool),
        "cell_n": np.full(4, 10),
        "cell_sum": np.array([-5.0, 5.0, -5.0, 5.0]),
        "cell_sumsq": np.full(4, 10.0),
        "global_n": np.full(4, 100),
        "global_sum": np.zeros(4),
        "global_sumsq": np.full(4, 100.0),
    }
    config = _config()
    config["walk_forward"]["minimum_global_action_rows"] = 1
    policy = {
        "minimum_cell_rows": 1,
        "prior_strength": 0.0,
        "lcb_z": 0.0,
        "minimum_lcb_r": 0.0,
        "minimum_action_gap_r": 0.0,
        "maximum_trades_per_utc_day": 6,
    }
    selected, diagnostics = select_trades(labels, stats, policy, config)
    assert selected["direction"].tolist() == ["LONG"]
    assert diagnostics["direction_selected_rows"] == 2
    assert diagnostics["overlap_rejections"] == 1


def test_exact_action_tie_abstains() -> None:
    labels = _paired_labels().iloc[:2].copy()
    stats = {
        "oos": np.ones(2, dtype=bool),
        "cell_n": np.full(2, 10),
        "cell_sum": np.full(2, 5.0),
        "cell_sumsq": np.full(2, 10.0),
        "global_n": np.full(2, 100),
        "global_sum": np.zeros(2),
        "global_sumsq": np.full(2, 100.0),
    }
    config = _config()
    config["walk_forward"]["minimum_global_action_rows"] = 1
    policy = {
        "minimum_cell_rows": 1,
        "prior_strength": 0.0,
        "lcb_z": 0.0,
        "minimum_lcb_r": 0.0,
        "minimum_action_gap_r": 0.0,
        "maximum_trades_per_utc_day": 6,
    }
    selected, _ = select_trades(labels, stats, policy, config)
    assert selected.empty


def test_simulator_scores_ambiguous_bar_stop_first() -> None:
    starts = (
        pd.Series(
            pd.to_datetime(
                [
                    "2024-01-01T23:45:00Z",
                    "2024-01-02T00:00:00Z",
                    "2024-01-02T00:15:00Z",
                ]
            )
        )
        .astype("datetime64[ns, UTC]")
        .astype("int64")
        .to_numpy()
    )
    ends = starts + 15 * 60 * 1_000_000_000
    arrays = {
        "starts": starts,
        "ends": ends,
        "signals": ends,
        "bid_open": np.array([99.9, 99.9, 100.0]),
        "bid_high": np.array([100.1, 101.2, 100.1]),
        "bid_low": np.array([99.8, 98.8, 99.8]),
        "bid_close": np.array([100.0, 100.0, 100.0]),
        "ask_open": np.array([100.0, 100.0, 100.1]),
        "ask_high": np.array([100.2, 101.3, 100.2]),
        "ask_low": np.array([99.9, 98.9, 99.9]),
        "ask_close": np.array([100.1, 100.1, 100.1]),
        "atr14": np.ones(3),
    }
    geometry = {"stop_atr": 1.0, "target_r": 1.0, "maximum_hold_hours": 1.0}
    execution = {
        "maximum_entry_gap_minutes": 20,
        "maximum_horizon_gap_hours": 72,
        "maximum_entry_spread_r": 0.2,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
    }
    outcome = simulate_fixed_trade(arrays, 0, 1, geometry, execution)
    assert outcome is not None
    assert outcome["exit_reason"] == "STOP_AMBIGUOUS"
    assert outcome["stress_net_r"] == -1.0
