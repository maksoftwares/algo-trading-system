from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit import (  # noqa: E402
    aggregate_histdata_m5,
    compare_m5_feeds,
    evaluate_gates,
    forbidden_columns,
    load_config,
    parse_histdata_timestamp,
)


def test_fixed_est_timestamp_converts_to_utc_without_dst_search() -> None:
    values = pd.Series(["20240101 180000312"])
    parsed = parse_histdata_timestamp(values, 5)
    assert parsed.iloc[0] == pd.Timestamp("2024-01-01T23:00:00.312Z")


def test_m5_bar_is_available_only_at_bar_end() -> None:
    ticks = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2024-01-02T10:00:01Z", "2024-01-02T10:04:59Z"]
            ),
            "bid": [2000.0, 2001.0],
            "ask": [2000.2, 2001.2],
            "mid": [2000.1, 2001.1],
            "spread": [0.2, 0.2],
        }
    )
    bars = aggregate_histdata_m5(ticks)
    assert len(bars) == 1
    assert bars.iloc[0]["bar_start_utc"] == pd.Timestamp("2024-01-02T10:00:00Z")
    assert bars.iloc[0]["available_time_utc"] == pd.Timestamp("2024-01-02T10:05:00Z")
    assert bars.iloc[0]["mid_close"] == 2001.1


def test_comparison_uses_identical_bar_times_and_consecutive_changes() -> None:
    starts = pd.date_range("2024-01-02T10:00:00Z", periods=4, freq="5min")
    available = starts + pd.Timedelta(minutes=5)
    hist = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "available_time_utc": available,
            "bid_close": [99.9, 100.9, 102.9, 105.9],
            "ask_close": [100.1, 101.1, 103.1, 106.1],
            "mid_close": [100.0, 101.0, 103.0, 106.0],
            "spread_median": [0.2] * 4,
            "spread_max": [0.2] * 4,
            "tick_count": [10] * 4,
        }
    )
    dukas = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "available_time_utc": available,
            "bid_close": [99.8, 100.8, 102.8, 105.8],
            "ask_close": [100.2, 101.2, 103.2, 106.2],
            "mid_close": [100.0, 101.0, 103.0, 106.0],
            "xau_tick_count": [20] * 4,
        }
    )
    _, metrics, daily = compare_m5_feeds(hist, dukas)
    assert metrics["matched_m5_bars"] == 4
    assert metrics["consecutive_return_pairs"] == 3
    assert metrics["contemporaneous_return_correlation"] == 1.0
    assert len(daily) == 1


def test_gate_evaluation_is_fixed_and_complete() -> None:
    config = load_config(ROOT)
    source = {
        "rows": 2_000_000,
        "calendar_days_spanned": 31,
        "timestamps_monotonic": True,
        "nonpositive_quote_rows": 0,
        "crossed_quote_rows": 0,
        "median_spread_dollars": 0.2,
        "spread_p99_dollars": 1.0,
    }
    comparison = {
        "active_bar_coverage_fraction": 0.95,
        "matched_m5_bars": 7000,
        "contemporaneous_return_correlation": 0.98,
        "median_absolute_basis_dollars": 0.5,
        "exact_mid_close_fraction": 0.1,
        "basis_standard_deviation_dollars": 0.2,
    }
    gates = evaluate_gates(source, comparison, config["gates"])
    assert len(gates) == 12
    assert all(gates.values())


def test_foundation_columns_contain_no_research_outcome() -> None:
    frame = pd.DataFrame(
        columns=[
            "bar_start_utc",
            "available_time_utc",
            "bid_close",
            "ask_close",
            "mid_close",
            "spread_median",
            "tick_count",
        ]
    )
    assert forbidden_columns(frame) == []


def test_contract_never_authorizes_execution_or_payment() -> None:
    config = load_config(ROOT)
    controls = config["research_controls"]
    assert controls["source_quality_only"] is True
    for key in (
        "same_version_tuning_authorized",
        "future_columns_authorized",
        "labels_authorized",
        "signals_authorized",
        "trade_outcomes_authorized",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "payment_authorized",
        "broker_action_authorized",
    ):
        assert controls[key] is False


def test_config_is_valid_json() -> None:
    path = ROOT / "config" / "histdata_xauusd_independent_feed_audit_v47.json"
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"].endswith(
        "v47"
    )
