from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.early_exit import (
    annual_training_split,
    apply_first_exit_signal,
    build_feature_matrix,
    build_snapshots,
    validate_feature_contract,
    verify_sources,
)


def synthetic_context():
    times = pd.date_range("2022-01-01", periods=60, freq="5min", tz="UTC")
    center = 100.0 + np.linspace(0.0, -3.0, len(times))
    cap = pd.DataFrame(
        {
            "bid_open": center - 0.1,
            "bid_low": center - 0.3,
            "bid_close": center - 0.1,
            "ask_open": center + 0.1,
            "ask_high": center + 0.3,
            "ask_close": center + 0.1,
        }
    )
    n = len(times)
    values = np.arange(n, dtype=float)
    cumulative = np.concatenate([[0.0], np.cumsum(values)])
    return {
        "cap": cap,
        "cap_t": times.tz_localize(None).to_numpy(),
        "t": pd.Series(times),
        "reg": np.array(["R1_UPTREND"] * n),
        "csm": cumulative,
        "cbi": cumulative * 0.01,
        "ctc": cumulative + np.arange(n + 1) * 10.0,
        "cts": cumulative * 0.001,
        "cpe": cumulative * 0.002,
        "slope": np.linspace(0.0, 1.0, n),
    }


def synthetic_trade():
    return pd.DataFrame(
        {
            "i": [1],
            "long": [True],
            "entry_time": [pd.Timestamp("2022-01-01 00:00", tz="UTC")],
            "exit_time": [pd.Timestamp("2022-01-01 04:00", tz="UTC")],
            "entry_price": [100.1],
            "exit_price": [98.0],
            "risk_usd": [2.0],
            "pnl_usd": [-2.4],
            "fee_stress_pnl_usd": [-2.9],
            "open_cost_usd": [0.3],
            "fee_stress_open_cost_usd": [0.7],
            "net_r": [-1.2],
            "stress_net_r": [-1.45],
            "regime": ["R1_UPTREND"],
            "direction": ["LONG"],
            "trade_id": ["T1"],
        }
    )


def test_snapshot_uses_next_bar_open_and_ignores_later_bars(config, stress):
    config["snapshots"]["checkpoint_minutes"] = [30]
    context = synthetic_context()
    first, _ = build_snapshots(synthetic_trade(), context, config, stress)
    expected = pd.Timestamp("2022-01-01 00:30", tz="UTC")
    assert first.loc[0, "early_exit_time"] == expected
    assert first.loc[0, "early_exit_price"] == pytest.approx(
        context["cap"].loc[6, "bid_open"]
    )

    changed = synthetic_context()
    changed["cap"].loc[7:, ["bid_open", "bid_low", "bid_close"]] = -999.0
    second, _ = build_snapshots(synthetic_trade(), changed, config, stress)
    pd.testing.assert_frame_equal(
        build_feature_matrix(first, config),
        build_feature_matrix(second, config),
    )


def test_snapshot_is_never_executed_at_or_after_original_exit(config, stress):
    config["snapshots"]["checkpoint_minutes"] = [30, 60]
    trade = synthetic_trade()
    trade["exit_time"] = pd.Timestamp("2022-01-01 00:30", tz="UTC")
    with pytest.raises(ValueError, match="No causal post-entry snapshots"):
        build_snapshots(trade, synthetic_context(), config, stress)


def test_first_high_confidence_signal_is_applied_and_reconciles():
    source = synthetic_trade()
    predictions = pd.DataFrame(
        {
            "source_trade_id": ["T1", "T1"],
            "checkpoint_minutes": [30, 60],
            "exit_trigger": [True, True],
            "early_exit_time": pd.to_datetime(
                ["2022-01-01 00:30", "2022-01-01 01:00"], utc=True
            ),
            "early_exit_price": [99.0, 99.5],
            "early_base_pnl_usd": [-1.4, -0.9],
            "early_stress_open_cost_usd": [0.7, 0.8],
            "early_stress_pnl_usd": [-1.8, -1.4],
            "exit_probability": [0.80, 0.90],
        }
    )
    managed, actions = apply_first_exit_signal(source, predictions)
    assert managed.loc[0, "management_checkpoint_minutes"] == 30
    assert managed.loc[0, "exit_price"] == pytest.approx(99.0)
    assert managed.loc[0, "fee_stress_pnl_usd"] == pytest.approx(-1.8)
    assert actions.loc[0, "management_action"] == "EARLY_EXIT"


def test_annual_split_purges_original_exits():
    snapshots = pd.DataFrame(
        {
            "original_exit_time": pd.to_datetime(
                ["2021-12-28", "2021-12-31", "2022-01-01"], utc=True
            )
        }
    )
    train = annual_training_split(snapshots, 2022, 48)
    assert train["original_exit_time"].tolist() == [
        pd.Timestamp("2021-12-28", tz="UTC")
    ]


def test_feature_contract_rejects_outcome_columns(config):
    config["features"]["numeric"].append("future_return")
    with pytest.raises(ValueError, match="Outcome-derived"):
        validate_feature_contract(config)


def test_verify_sources_fails_closed(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("changed", encoding="utf-8")
    config = {
        "sources": {
            "source": {"path": str(source), "sha256": "0" * 64}
        }
    }
    with pytest.raises(ValueError, match="Locked source drift"):
        verify_sources(config)
