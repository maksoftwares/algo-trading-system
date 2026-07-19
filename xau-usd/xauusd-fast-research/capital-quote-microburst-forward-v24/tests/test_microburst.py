from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from microburst import (  # noqa: E402
    assess_full_days,
    evaluate_stage,
    generate_candidates,
    load_config,
    load_ticks,
    simulate_trades,
)


def _burst_ticks(start_ms: int, block_offset_ms: int = 0) -> pd.DataFrame:
    count = 260
    times = start_ms + block_offset_ms + np.arange(count, dtype=np.int64) * 100
    mid = np.full(count, 4000.0)
    for index in range(50, 70):
        mid[index] = 4000.0 + (index - 49) * 0.05
    mid[70:150] = mid[69]
    for index in range(150, 170):
        mid[index] = mid[149] + (index - 149) * 0.05
    mid[170:] = mid[169]
    timestamp = pd.to_datetime(times, unit="ms", utc=True)
    return pd.DataFrame(
        {
            "tick_time_msc": times,
            "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "date_utc": timestamp.strftime("%Y-%m-%d"),
            "bid": mid - 0.15,
            "ask": mid + 0.15,
            "spread_price": 0.30,
        }
    )


def test_candidate_is_causal_and_first_event_per_block() -> None:
    config = load_config(ROOT)
    start_ms = int(pd.Timestamp("2026-07-17T12:00:00Z").timestamp() * 1000)
    ticks = _burst_ticks(start_ms)
    candidates, features = generate_candidates(ticks, config)
    assert int(features["raw_gate_crossing"].sum()) == 2
    assert len(candidates) == 1
    assert candidates.iloc[0]["candidate_side"] == "LONG"

    prefix = ticks.iloc[:120].copy()
    prefix_candidates, _ = generate_candidates(prefix, config)
    cutoff = int(prefix["tick_time_msc"].iloc[-1])
    full_before_cutoff = candidates.loc[candidates["tick_time_msc"].le(cutoff)]
    pd.testing.assert_frame_equal(
        prefix_candidates.reset_index(drop=True),
        full_before_cutoff.reset_index(drop=True),
    )


def test_each_four_hour_block_can_contribute_at_most_one_event() -> None:
    config = load_config(ROOT)
    start_ms = int(pd.Timestamp("2026-07-17T12:00:00Z").timestamp() * 1000)
    first = _burst_ticks(start_ms)
    second = _burst_ticks(start_ms, 4 * 60 * 60 * 1000)
    ticks = pd.concat([first, second], ignore_index=True)
    candidates, _ = generate_candidates(ticks, config)
    assert len(candidates) == 2
    assert candidates["utc_block_start_ms"].nunique() == 2


def test_loader_keeps_last_duplicate_millisecond(tmp_path: Path) -> None:
    config = deepcopy(load_config(ROOT))
    path = tmp_path / "xau_ticks_20260717.csv"
    times = [1784246400000, 1784246400000, 1784246400100]
    timestamps = pd.to_datetime(times, unit="ms", utc=True).strftime(
        "%Y.%m.%d %H:%M:%S.%fZ"
    )
    frame = pd.DataFrame(
        {
            "schema_version": "xau_prospective_tick_v1",
            "timestamp_utc": timestamps,
            "tick_time_msc": times,
            "account_login": 1033669,
            "account_server": "Capital.ComMena-Demo",
            "symbol": "XAUUSD",
            "bid": [4000.0, 4000.1, 4000.2],
            "ask": [4000.3, 4000.4, 4000.5],
            "spread_price": [0.3, 0.3, 0.3],
        }
    )
    frame.to_csv(path, index=False)
    ticks, audit, raw_daily = load_ticks([path], config)
    assert len(ticks) == 2
    assert ticks.iloc[0]["bid"] == pytest.approx(4000.1)
    assert audit["duplicate_millisecond_rows"] == 1
    assert raw_daily.iloc[0]["duplicate_millisecond_share"] == pytest.approx(1 / 3)


def test_full_day_quality_gate_is_source_only() -> None:
    config = deepcopy(load_config(ROOT))
    config["data_quality"]["minimum_unique_quotes_per_full_day"] = 3
    config["data_quality"]["maximum_p99_interquote_gap_ms"] = 100_000_000
    day = pd.Timestamp("2026-07-20T00:00:00Z")
    times = np.array(
        [
            int(day.timestamp() * 1000),
            int((day + pd.Timedelta(hours=12)).timestamp() * 1000),
            int((day + pd.Timedelta(hours=22)).timestamp() * 1000),
        ],
        dtype=np.int64,
    )
    ticks = pd.DataFrame(
        {
            "tick_time_msc": times,
            "date_utc": "2026-07-20",
        }
    )
    raw_daily = pd.DataFrame(
        {
            "date_utc": ["2026-07-20"],
            "raw_rows": [3],
            "unique_milliseconds": [3],
            "duplicate_millisecond_rows": [0],
            "duplicate_millisecond_share": [0.0],
        }
    )
    quality = assess_full_days(ticks, raw_daily, config)
    assert bool(quality.iloc[0]["eligible_full_weekday"])


def test_simulation_uses_strict_later_entry_and_bidask_exit() -> None:
    config = load_config(ROOT)
    start_ms = int(pd.Timestamp("2026-07-20T12:00:00Z").timestamp() * 1000)
    ticks = pd.DataFrame(
        {
            "tick_time_msc": [start_ms, start_ms + 100, start_ms + 120_100],
            "bid": [4000.0, 4000.0, 4001.0],
            "ask": [4000.3, 4000.3, 4001.3],
        }
    )
    candidate = pd.DataFrame(
        {
            "date_utc": ["2026-07-20"],
            "utc_block_start_ms": [start_ms],
            "timestamp_utc": ["2026-07-20T12:00:00.000Z"],
            "tick_time_msc": [start_ms],
            "candidate_side": ["LONG"],
            "signed_update_imbalance": [1.0],
            "displacement_price": [1.0],
        }
    )
    trades = simulate_trades(
        ticks,
        candidate,
        ["2026-07-20"],
        "FORWARD_VALIDATION",
        config,
    )
    assert len(trades) == 1
    assert int(trades.iloc[0]["entry_delay_ms"]) == 100
    assert int(trades.iloc[0]["exit_delay_ms"]) == 0
    assert trades.iloc[0]["observed_bidask_move"] == pytest.approx(0.7)
    assert trades.iloc[0]["base_pnl_dollars"] == pytest.approx(0.6)
    assert trades.iloc[0]["stress_pnl_dollars"] == pytest.approx(0.4)


def test_stage_gate_counts_zero_trade_days_and_direction_balance() -> None:
    config = load_config(ROOT)
    dates = (
        pd.date_range("2026-07-20", periods=20, freq="B").strftime("%Y-%m-%d").tolist()
    )
    records = []
    sequence = 0
    for date_utc in dates:
        for side in ("LONG", "SHORT"):
            records.append(
                {
                    "evidence_partition": "FORWARD_VALIDATION",
                    "date_utc": date_utc,
                    "entry_time_msc": sequence,
                    "side": side,
                    "base_pnl_dollars": 1.0,
                    "stress_pnl_dollars": 0.8,
                }
            )
            sequence += 1
    trades = pd.DataFrame(records)
    audit, daily = evaluate_stage(trades, dates, "FORWARD_VALIDATION", config)
    assert len(daily) == 20
    assert audit["metrics"]["trades_per_full_weekday"] == pytest.approx(2.0)
    assert audit["metrics"]["long_share"] == pytest.approx(0.5)
    assert audit["metrics"]["short_share"] == pytest.approx(0.5)
    assert audit["gate_passed"]
