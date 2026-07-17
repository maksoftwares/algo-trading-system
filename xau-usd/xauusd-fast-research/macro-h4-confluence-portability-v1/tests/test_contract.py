from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from research import REPO_ROOT, _macro_context, _simulate_one, aggregate_trading_days, sha256_file


ROOT = Path(__file__).resolve().parents[1]


def config() -> dict:
    return json.loads((ROOT / "config" / "macro_h4_confluence_portability_v1.json").read_text())


def test_all_frozen_source_hashes_match() -> None:
    for item in config()["frozen_sources"]:
        assert sha256_file(REPO_ROOT / item["path"]) == item["sha256"]


def test_exam_starts_after_original_matrix_ended() -> None:
    original = REPO_ROOT / "xau-usd" / "xauusd-phase0" / "outputs" / "matrix_results" / "h4_macro_momentum_confluence_v0" / "cell_7_h4_macro_momentum_confluence_v0_dukascopy_best_case.csv"
    result = pd.read_csv(original)
    assert result.iloc[0]["time_window_end"].startswith("2024-12-31")
    assert pd.Timestamp(config()["windows"]["exam"][0]) >= pd.Timestamp("2025-01-01T00:00:00Z")


def test_macro_join_keys_are_normalized_to_nanoseconds() -> None:
    context = _macro_context(pd.Timestamp("2016-07-01T00:00:00Z"), pd.Timestamp("2026-05-15T00:00:00Z"))
    assert context
    assert {str(frame["timestamp_utc"].dtype) for frame in context.values()} == {"datetime64[ns, UTC]"}


def test_trading_day_adapter_accepts_maintenance_break() -> None:
    times = pd.to_datetime(["2026-01-02T00:00:00Z", "2026-01-02T00:05:00Z"])
    bars = pd.DataFrame(
        {
            "bar_start_utc": times,
            "bid_open": [100.0, 101.0], "bid_high": [101.0, 102.0], "bid_low": [99.0, 100.0], "bid_close": [100.5, 101.5],
            "ask_open": [100.2, 101.2], "ask_high": [101.2, 102.2], "ask_low": [99.2, 100.2], "ask_close": [100.7, 101.7],
            "mid_open": [100.1, 101.1], "mid_high": [101.1, 102.1], "mid_low": [99.1, 100.1], "mid_close": [100.6, 101.6],
            "volume": [10.0, 20.0],
        }
    )
    daily = aggregate_trading_days(bars, minimum_rows=2)
    assert len(daily) == 1
    assert daily.iloc[0]["mid_open"] == pytest.approx(100.1)
    assert daily.iloc[0]["mid_close"] == pytest.approx(101.6)
    assert daily.iloc[0]["timestamp_utc"] == pd.Timestamp("2026-01-03T00:00:00Z")


def test_native_long_execution_enters_ask_and_exits_bid_target() -> None:
    times = pd.to_datetime(["2026-01-02T10:00:00Z", "2026-01-02T10:05:00Z"])
    bars = pd.DataFrame(
        {
            "bar_start_utc": times,
            "timestamp_utc": times + pd.Timedelta(minutes=5),
            "bid_open": [100.0, 100.5], "bid_high": [100.8, 102.2], "bid_low": [99.8, 100.4], "bid_close": [100.5, 102.0],
            "ask_open": [100.2, 100.7], "ask_high": [101.0, 102.4], "ask_low": [100.0, 100.6], "ask_close": [100.7, 102.2],
            "tick_spread_max": [0.2, 0.2],
        }
    )
    candidate = pd.Series({"direction": "LONG", "stop": 99.2, "target": 102.0, "max_holding_bars": 2})
    execution = {"ounces": 1.0, "maximum_initial_risk_usd": 50.0, "ticket_cost_usd": 0.0, "holding_cost_per_24h_usd": 0.0, "stress_slippage_r": 0.0}
    result = _simulate_one(bars, 0, candidate, execution)
    assert result["entry_price"] == pytest.approx(100.2)
    assert result["exit_price"] == pytest.approx(102.0)
    assert result["net_r"] == pytest.approx(1.8)


def test_incomplete_end_of_data_path_is_not_counted() -> None:
    times = pd.to_datetime(["2026-01-02T10:00:00Z", "2026-01-02T10:05:00Z"])
    bars = pd.DataFrame(
        {
            "bar_start_utc": times,
            "timestamp_utc": times + pd.Timedelta(minutes=5),
            "bid_open": [100.0, 100.1], "bid_high": [100.4, 100.5], "bid_low": [99.8, 99.9], "bid_close": [100.1, 100.2],
            "ask_open": [100.2, 100.3], "ask_high": [100.6, 100.7], "ask_low": [100.0, 100.1], "ask_close": [100.3, 100.4],
            "tick_spread_max": [0.2, 0.2],
        }
    )
    candidate = pd.Series({"direction": "LONG", "stop": 98.0, "target": 103.0, "max_holding_bars": 12})
    execution = {"ounces": 1.0, "maximum_initial_risk_usd": 50.0, "ticket_cost_usd": 0.0, "holding_cost_per_24h_usd": 0.0, "stress_slippage_r": 0.0}
    result = _simulate_one(bars, 0, candidate, execution)
    assert result == {"accepted": False, "rejection_reason": "UNRESOLVED_END_OF_DATA"}


def test_research_result_cannot_authorize_execution() -> None:
    controls = config()["research_controls"]
    assert controls["research_only"] is True
    assert controls["python_predictions_authorized"] is False
    assert controls["ea_consumption_authorized"] is False
    assert controls["broker_action_authorized"] is False
