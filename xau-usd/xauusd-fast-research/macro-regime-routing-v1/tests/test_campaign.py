from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import campaign  # noqa: E402
from foundation import ROUTER  # noqa: E402


def _small_config() -> dict:
    return {
        "macro_features": {
            "horizons": {"H1": 2},
            "scales": {"FAST": 6},
            "minimum_scale_fraction": 0.5,
            "gold_return_horizons": {"H1": 2},
        },
        "windows": {"a": ["2024-01-01T00:00:00Z", "2024-01-01T03:00:00Z"]},
    }


def _macro(rows: int = 20) -> pd.DataFrame:
    timestamp = pd.date_range("2024-01-01T00:15:00Z", periods=rows, freq="15min")
    return pd.DataFrame(
        {
            "timestamp_utc": timestamp,
            "dollaridxusd_close": 100.0 + np.arange(rows) * 0.1,
            "ustbondtrusd_close": 200.0 + np.arange(rows) * 0.2,
        }
    )


def test_macro_features_are_causal() -> None:
    config = _small_config()
    source = _macro()
    original = campaign.build_macro_features(source, config)
    changed = source.copy()
    changed.loc[changed.index[-2] :, "dollaridxusd_close"] *= 1.5
    revised = campaign.build_macro_features(changed, config)
    pd.testing.assert_frame_equal(original.iloc[:-2], revised.iloc[:-2])


def test_noncontiguous_return_is_rejected() -> None:
    source = _macro().drop(index=5).reset_index(drop=True)
    result = campaign.build_macro_features(source, _small_config())
    after_gap = source["timestamp_utc"].iloc[6]
    value = result.loc[
        result["timestamp_utc"].eq(after_gap), "dxy_pressure_H1_FAST"
    ].iat[0]
    assert np.isnan(value)


def _decision_frame(regime: str = "CHOP") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dxy_pressure_H1_D2": [-1.2, -1.2],
            "bond_pressure_H1_D2": [-1.0, -1.0],
            "gold_return_H1_atr": [0.0, 0.0],
            "body": [0.5, 0.5],
            "candle_direction": [-1, -1],
            "regime": [regime, "UNSAFE_SHOCK"],
            "hour_utc": [12, 12],
            "atr14": [2.0, 2.0],
            "transition_age_m15": [0, 0],
            "last_resolved_regime": ["CHOP", "CHOP"],
            "ancestry_direction": [0, 0],
            "execution_index": [4, 9],
        }
    )


def _catchup_params() -> dict:
    return {
        "macro_key": "H1_D2",
        "gold_horizon": "H1",
        "pressure_min": 0.75,
        "maximum_alignment_atr": 0.25,
        "require_confirmation": True,
        "body_min": 0.2,
        "hour_window": "ALL",
        "geometry_id": "C_FAST",
    }


def test_consensus_direction_and_shock_abstention() -> None:
    mask, direction = campaign.signal_mask_direction(
        _decision_frame(), "CHOP_MACRO_CONSENSUS_CATCHUP", _catchup_params()
    )
    assert mask.tolist() == [True, False]
    assert direction.tolist() == [-1, -1]


def test_simulation_uses_complete_gold_execution_index() -> None:
    frame = _decision_frame().iloc[[0]].copy()
    row = type(
        "Row",
        (),
        {
            "parameters_json": json.dumps(_catchup_params()),
            "mechanic": "CHOP_MACRO_CONSENSUS_CATCHUP",
            "geometry_id": "C_FAST",
            "regime_owner": "CHOP",
        },
    )()
    called: list[int] = []

    def outcome(arrays, signal_index, direction, geometry, execution):
        called.append(signal_index)
        return {
            "signal_time": pd.Timestamp("2024-01-01T12:00:00Z"),
            "entry_time": pd.Timestamp("2024-01-01T12:15:00Z"),
            "exit_time": pd.Timestamp("2024-01-01T13:00:00Z"),
            "direction": "SHORT",
            "stress_net_r": 0.5,
        }

    config = {
        "geometries": {
            "CHOP": {
                "C_FAST": {
                    "stop_atr": 1.0,
                    "target_r": 1.25,
                    "maximum_hold_hours": 6.0,
                }
            }
        },
        "execution": {"maximum_trades_per_variant_utc_day": 4},
    }
    trades = campaign.simulate_variant(frame, {}, row, config, {}, outcome)
    assert called == [4]
    assert len(trades) == 1


def test_stop_wins_same_bar_collision() -> None:
    starts = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
    values = np.array([timestamp.value for timestamp in starts], dtype=np.int64)
    arrays = {
        "starts": values,
        "ends": values + 15 * 60 * 1_000_000_000,
        "signals": values + 15 * 60 * 1_000_000_000,
        "atr14": np.array([1.0, 1.0, 1.0]),
        "bid_open": np.array([100.0, 100.0, 100.0]),
        "ask_open": np.array([100.2, 100.2, 100.2]),
        "bid_high": np.array([100.0, 102.0, 100.0]),
        "bid_low": np.array([100.0, 98.0, 100.0]),
        "ask_high": np.array([100.2, 102.2, 100.2]),
        "ask_low": np.array([100.2, 98.2, 100.2]),
    }
    geometry = {"stop_atr": 1.0, "target_r": 1.0, "maximum_hold_hours": 1.0}
    execution = {
        "maximum_entry_gap_minutes": 20,
        "maximum_horizon_gap_hours": 72,
        "maximum_entry_spread_r": 0.25,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
    }
    trade = ROUTER.simulate_fixed_trade(arrays, 0, 1, geometry, execution)
    assert trade is not None
    assert trade["exit_reason"] == "STOP_AMBIGUOUS"
    assert trade["gross_r"] == pytest.approx(-1.0)


def test_parameter_spaces_are_large_enough() -> None:
    config = json.loads(
        (ROOT / "config" / "macro_regime_routing_v1.json").read_text(encoding="utf-8")
    )
    for owner, mechanics in campaign.MECHANICS.items():
        for mechanic in mechanics:
            assert (
                sum(1 for _ in campaign.parameter_space(owner, mechanic, config)) >= 100
            )


def test_generated_manifest_contract_when_present() -> None:
    path = ROOT / "outputs" / "MACRO_REGIME_ROUTING_V1_MANIFEST.csv"
    if not path.exists():
        pytest.skip("Outcome-blind manifest has not been generated yet")
    manifest = pd.read_csv(path)
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(23120, 24120))
    assert manifest.groupby("regime_owner").size().to_dict() == {
        "CHOP": 500,
        "TRANSITION": 500,
    }
    assert manifest.groupby("mechanic").size().eq(100).all()
