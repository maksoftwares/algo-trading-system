from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import contract, downtrend  # noqa: E402


def _m5(starts: pd.DatetimeIndex) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "timestamp_utc": starts + pd.Timedelta(minutes=5),
            "tick_count": np.full(len(starts), 10),
        }
    )
    for side, spread in (("bid", 0.0), ("ask", 0.2), ("mid", 0.1)):
        frame[f"{side}_open"] = 100.0 + spread
        frame[f"{side}_high"] = 101.0 + spread
        frame[f"{side}_low"] = 99.0 + spread
        frame[f"{side}_close"] = 100.0 + spread
    return frame


def _execution_config() -> dict:
    config = copy.deepcopy(contract.load_config())
    config["execution"].update(
        {
            "ticket_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        }
    )
    return config


def _candidate(decision: pd.Timestamp, risk: float = 3.5) -> pd.Series:
    return pd.Series(
        {
            "decision_time": decision,
            "raw_stop_distance": risk,
            "candidate_id": "candidate",
            "candidate_row_id": 0,
        }
    )


def _raw_store(
    tmp_path: Path,
    times: list[pd.Timestamp],
    bids: list[float],
    asks: list[float],
    config: dict,
) -> downtrend.VerifiedTickStore:
    assert len(times) == len(bids) == len(asks) and times
    hour = times[0].floor("h")
    path = (
        tmp_path
        / "raw"
        / "XAUUSD"
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour.year:04d}{hour.month:02d}{hour.day:02d}{hour.hour:02d}.json"
    )
    path.parent.mkdir(parents=True)
    timestamps = [int(value.value // 1_000_000) for value in times]
    time_deltas = [timestamps[0] - int(hour.value // 1_000_000)] + [
        value - previous for previous, value in zip(timestamps, timestamps[1:])
    ]
    bid_deltas = [0] + [
        int(round((value - previous) * 1_000))
        for previous, value in zip(bids, bids[1:])
    ]
    ask_deltas = [0] + [
        int(round((value - previous) * 1_000))
        for previous, value in zip(asks, asks[1:])
    ]
    payload = {
        "timestamp": int(hour.value // 1_000_000),
        "multiplier": 0.001,
        "bid": bids[0],
        "ask": asks[0],
        "times": time_deltas,
        "bids": bid_deltas,
        "asks": ask_deltas,
        "bidVolumes": [1.0] * len(times),
        "askVolumes": [1.0] * len(times),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return downtrend.VerifiedTickStore(tmp_path, config)


def _simulate(
    frame: pd.DataFrame,
    candidate: pd.Series,
    config: dict,
    store: downtrend.VerifiedTickStore,
) -> dict:
    return downtrend._simulate_short(
        frame,
        downtrend.timestamp_series_ms(frame["bar_start_utc"]),
        downtrend.timestamp_series_ms(frame["bar_end_utc"]),
        frame["ask_high"].to_numpy(dtype=float),
        frame["ask_low"].to_numpy(dtype=float),
        candidate,
        config,
        store,
    )


def test_h1_aggregation_keeps_both_dst_fallback_hours() -> None:
    starts = pd.date_range("2020-10-25T00:00:00Z", periods=24, freq="5min")
    result = downtrend.aggregate_broker_bars(
        _m5(starts), 60, "H1", "Europe/Helsinki"
    )
    assert len(result) == 2
    assert result["bar_start_utc"].tolist() == [starts[0], starts[12]]
    assert result["source_rows"].tolist() == [12, 12]


def test_regime_join_is_causal_and_uses_completed_states() -> None:
    state_time = pd.Timestamp("2020-01-01T00:00:00Z")
    candidates = pd.DataFrame(
        {"decision_time": [state_time + pd.Timedelta(minutes=30)]}
    )
    states = {
        "D1": pd.DataFrame(
            {
                "timestamp_utc": [state_time],
                "persistent_down": [True],
                "shock_d1": [False],
                "atr_percentile_d1": [50.0],
            }
        ),
        "H4": pd.DataFrame(
            {"timestamp_utc": [state_time], "trend_down": [True]}
        ),
        "H1": pd.DataFrame(
            {"timestamp_utc": [state_time], "shock_h1": [False]}
        ),
    }
    result = downtrend.attach_r2_regime(candidates, states)
    assert bool(result.loc[0, "r2_allowed"])
    assert result.loc[0, "d1_feature_time"] <= result.loc[0, "decision_time"]
    assert result.loc[0, "h4_feature_time"] <= result.loc[0, "decision_time"]
    assert result.loc[0, "h1_feature_time"] <= result.loc[0, "decision_time"]


def test_raw_tick_order_resolves_both_thresholds_inside_one_m5_bar(
    tmp_path: Path,
) -> None:
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=1, freq="5min")
    frame = _m5(starts)
    frame.loc[0, "ask_high"] = 104.2
    frame.loc[0, "ask_low"] = 93.0
    config = _execution_config()
    store = _raw_store(
        tmp_path,
        [starts[0], starts[0] + pd.Timedelta(seconds=1), starts[0] + pd.Timedelta(seconds=2)],
        [100.0, 92.8, 104.0],
        [100.2, 93.0, 104.2],
        config,
    )
    outcome = _simulate(frame, _candidate(starts[0]), config, store)
    assert outcome["accepted"]
    assert outcome["exit_reason"] == "TARGET"
    assert outcome["net_r"] == 2.0
    assert outcome["m5_both_thresholds_resolved_by_ticks"]


def test_short_stop_crossing_pays_observed_ask_slippage(tmp_path: Path) -> None:
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=1, freq="5min")
    frame = _m5(starts)
    frame.loc[0, ["ask_high", "ask_low", "ask_close"]] = [104.2, 99.8, 104.2]
    config = _execution_config()
    store = _raw_store(
        tmp_path,
        [starts[0], starts[0] + pd.Timedelta(seconds=1)],
        [100.0, 104.0],
        [100.2, 104.2],
        config,
    )
    outcome = _simulate(frame, _candidate(starts[0]), config, store)
    assert outcome["exit_reason"] == "STOP_SLIPPAGE"
    assert outcome["exit_price"] == 104.2
    assert outcome["net_r"] < -1.0


def test_last_quote_lookup_searches_backward_from_dataset_end(tmp_path: Path) -> None:
    start = pd.Timestamp("2020-01-01T00:00:00Z")
    config = _execution_config()
    store = _raw_store(
        tmp_path,
        [start, start + pd.Timedelta(seconds=30)],
        [100.0, 100.1],
        [100.2, 100.3],
        config,
    )
    quote = store.last_quote_at_or_before(
        int((start + pd.Timedelta(minutes=59)).value // 1_000_000),
        int(start.value // 1_000_000),
    )
    assert quote is not None
    assert quote.timestamp_ms == int(
        (start + pd.Timedelta(seconds=30)).value // 1_000_000
    )
    assert quote.ask == 100.3


def test_empty_candidate_and_trade_sets_remain_reportable() -> None:
    config = contract.load_config()
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=1, freq="5min")
    frame = _m5(starts)
    candidates = pd.DataFrame(
        columns=[
            "decision_time",
            "candidate_id",
            "mechanism_family",
            "attempt_no",
            "candidate_row_id",
        ]
    )
    ledger, trades = downtrend.simulate_candidates(
        frame, candidates, config, None  # type: ignore[arg-type]
    )
    assert ledger.empty and trades.empty
    assert {"accepted", "rejection_reason"}.issubset(ledger.columns)
    metrics = downtrend.evaluate_windows(trades, frame, config)
    assert len(metrics) == len(config["attempts"]) * len(config["windows"])
    assert all(row["trades"] == 0 for row in metrics)


def test_account_policy_enforces_concurrency_without_cross_variant_leakage() -> None:
    config = _execution_config()
    config["execution"]["maximum_concurrent_positions"] = 1
    config["execution"]["maximum_entries_per_broker_day"] = 2
    entries = pd.to_datetime(
        ["2020-01-01T00:00:00Z", "2020-01-01T00:05:00Z", "2020-01-01T01:05:00Z"]
    )
    trades = pd.DataFrame(
        {
            "candidate_id": ["a", "a", "a"],
            "candidate_row_id": [0, 1, 2],
            "entry_time": entries,
            "exit_time": pd.to_datetime(
                ["2020-01-01T01:00:00Z", "2020-01-01T00:10:00Z", "2020-01-01T01:10:00Z"]
            ),
        }
    )
    selected = downtrend.apply_account_policy(trades, config)
    assert selected["candidate_row_id"].tolist() == [0, 2]


def test_holm_adjustment_penalizes_all_four_frozen_attempts() -> None:
    adjusted = downtrend.holm_adjust(
        {"a": 0.01, "b": 0.03, "c": 0.20, "d": 0.90}
    )
    assert np.isclose(adjusted["a"], 0.04)
    assert np.isclose(adjusted["b"], 0.09)
    assert np.isclose(adjusted["c"], 0.40)
    assert adjusted["d"] == 0.90


def test_closed_drawdown_includes_initial_equity_peak() -> None:
    assert downtrend.closed_drawdown(pd.Series([-2.0, 3.0])) == 2.0
