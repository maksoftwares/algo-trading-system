from __future__ import annotations

import lzma
from pathlib import Path
import struct
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from economic_test import (  # noqa: E402
    decode_bi5_hour,
    dukascopy_url,
    expected_capital_paths,
    expected_dukascopy_hours,
    load_config,
    metrics_for_trades,
    simulate_trades,
)


def test_bi5_decoder_preserves_tick_order_and_quotes() -> None:
    hour = pd.Timestamp("2026-07-01T10:00:00Z")
    raw = b"".join(
        (
            struct.pack(">IIIff", 100, 2000300, 2000000, 2.0, 3.0),
            struct.pack(">IIIff", 250, 2000400, 2000100, 4.0, 5.0),
        )
    )
    payload = decode_bi5_hour(lzma.compress(raw), hour, 1000)
    assert payload["times"] == [100, 150]
    assert payload["ask"] == 2000.3
    assert payload["bid"] == 2000.0
    assert payload["asks"] == [0, 100]
    assert payload["bids"] == [0, 100]
    assert payload["askVolumes"] == [2.0, 4.0]
    assert payload["bidVolumes"] == [3.0, 5.0]


def test_public_url_uses_zero_based_month() -> None:
    config = load_config(ROOT)
    url = dukascopy_url(config, pd.Timestamp("2026-07-01T10:00:00Z"))
    assert url.endswith("/XAUUSD/2026/06/01/10h_ticks.bi5")


def test_sealed_source_inventory_counts_are_fixed() -> None:
    config = load_config(ROOT)
    assert len(expected_capital_paths(config)) == 17
    assert len(expected_dukascopy_hours(config)) == 408


def test_simulation_uses_later_quote_and_independent_lag_overlap() -> None:
    config = load_config(ROOT)
    start = int(pd.Timestamp("2026-07-01T00:00:00Z").timestamp() * 1000)
    timestamps = start + np.arange(70, dtype=np.int64) * 5000
    mid = 2000.0 + np.arange(70) * 0.02
    paired = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(timestamps, unit="ms", utc=True),
            "capital_timestamp_ms": timestamps,
            "capital_bid": mid - 0.25,
            "capital_ask": mid + 0.25,
        }
    )
    candidates = pd.DataFrame(
        {
            "evidence_partition": ["SEALED_CONFIRMATION"] * 2,
            "safety_lag_ms": [15000, 20000],
            "date_utc": ["2026-07-01"] * 2,
            "timestamp_utc": [pd.Timestamp("2026-07-01T00:00:00Z")] * 2,
            "capital_timestamp_ms": [start, start],
            "candidate_side": ["LONG", "LONG"],
            "absolute_residual_z": [5.0, 5.0],
            "fair_value_residual": [1.0, 1.0],
            "dukas_impulse": [1.0, 1.0],
        }
    )
    trades = simulate_trades(paired, candidates, ["2026-07-01"], config)
    assert len(trades) == 2
    assert set(trades["safety_lag_ms"]) == {15000, 20000}
    assert trades["entry_timestamp_ms"].gt(start).all()
    assert trades["entry_delay_ms"].eq(5000).all()


def test_daily_metrics_count_zero_trade_full_days() -> None:
    config = load_config(ROOT)
    trades = pd.DataFrame(
        {
            "evidence_partition": ["SEALED_CONFIRMATION"],
            "safety_lag_ms": [15000],
            "entry_timestamp_ms": [1],
            "date_utc": ["2026-07-01"],
            "side": ["LONG"],
            "base_pnl_dollars": [10.0],
            "stress_pnl_dollars": [9.0],
        }
    )
    metrics, daily = metrics_for_trades(
        trades,
        "SEALED_CONFIRMATION",
        15000,
        ["2026-07-01", "2026-07-02"],
        config,
    )
    assert len(daily) == 2
    assert daily["trades"].tolist() == [1, 0]
    assert metrics["profitable_day_share"] == 0.5


def test_config_never_authorizes_runtime_action() -> None:
    controls = load_config(ROOT)["research_controls"]
    assert controls["single_preregistered_economic_test"] is True
    assert controls["july_dukascopy_must_be_absent_before_lock"] is True
    for key in (
        "same_version_tuning_authorized",
        "strategy_admission_authorized",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    ):
        assert controls[key] is False
