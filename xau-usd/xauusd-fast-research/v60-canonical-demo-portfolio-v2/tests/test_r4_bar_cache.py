from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from r4_bar_cache import BAR_WIDTH_MS, load_quote_bars_cached


def test_overlapping_file_boundary_is_reaggregated_exactly(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text("first\n", encoding="ascii")
    second.write_text("second\n", encoding="ascii")
    calls: list[str] = []

    def loader(paths, _config):
        path = Path(list(paths)[0])
        calls.append(path.name)
        times = [1_000, 2_000] if path == first else [3_000, 4_000]
        prices = [100.0, 101.0] if path == first else [102.0, 103.0]
        frame = pd.DataFrame(
            {
                "tick_time_msc": times,
                "bid": prices,
                "ask": np.asarray(prices) + 0.1,
                "spread_price": [0.1, 0.1],
                "source_row": [0, 1],
                "date_utc": ["1970-01-01", "1970-01-01"],
            }
        )
        daily = pd.DataFrame(
            {
                "date_utc": ["1970-01-01"],
                "raw_rows": [2],
                "unique_milliseconds": [2],
                "duplicate_millisecond_rows": [0],
                "duplicate_millisecond_share": [0.0],
            }
        )
        audit = {
            "source_files": [{"path": str(path)}],
            "raw_rows": 2,
            "unique_rows": 2,
        }
        return frame, audit, daily

    def aggregate(ticks, *, completed_through, quality):
        if ticks.empty:
            return pd.DataFrame()
        ticks = ticks.sort_values("tick_time_msc").reset_index(drop=True)
        mid = (ticks["bid"] + ticks["ask"]) / 2.0
        delta = mid.diff().fillna(0.0)
        timestamp_ms = int(ticks.iloc[0]["tick_time_msc"]) // BAR_WIDTH_MS * BAR_WIDTH_MS
        count = len(ticks)
        return pd.DataFrame(
            {
                "timestamp_ms": [timestamp_ms],
                "xau_tick_count": [count],
                "tick_signed_move": [float(np.sign(delta).sum())],
                "tick_move_count": [int(delta.ne(0).sum())],
                "tick_realized_variance": [float(np.square(delta).sum())],
                "tick_spread_mean": [0.1],
                "tick_spread_last": [0.1],
                "tick_spread_max": [0.1],
                "tick_book_imbalance_mean": [0.0],
                "price_efficiency_5m": [1.0],
                "first_quote_delay_ms": [int(ticks.iloc[0]["tick_time_msc"])],
                "last_quote_age_ms": [BAR_WIDTH_MS - int(ticks.iloc[-1]["tick_time_msc"])],
                "maximum_internal_quote_gap_ms": [int(ticks["tick_time_msc"].diff().max())],
                "bid_open": [float(ticks.iloc[0]["bid"])],
                "bid_high": [float(ticks["bid"].max())],
                "bid_low": [float(ticks["bid"].min())],
                "bid_close": [float(ticks.iloc[-1]["bid"])],
                "ask_open": [float(ticks.iloc[0]["ask"])],
                "ask_high": [float(ticks["ask"].max())],
                "ask_low": [float(ticks["ask"].min())],
                "ask_close": [float(ticks.iloc[-1]["ask"])],
                "mid_open": [float(mid.iloc[0])],
                "mid_high": [float(mid.max())],
                "mid_low": [float(mid.min())],
                "mid_close": [float(mid.iloc[-1])],
                "bar_start_utc": [pd.Timestamp(timestamp_ms, unit="ms", tz="UTC")],
                "bar_end_utc": [pd.Timestamp(timestamp_ms + BAR_WIDTH_MS, unit="ms", tz="UTC")],
                "timestamp_utc": [pd.Timestamp(timestamp_ms + BAR_WIDTH_MS, unit="ms", tz="UTC")],
                "timeframe": ["M5"],
                "tick_count": [float(count)],
                "quote_quality_passed": [True],
                "tick_imbalance_5m": [0.0],
                "tick_imbalance_15m": [np.nan],
                "quote_contiguous_15m": [False],
                "quote_intensity_ratio": [np.nan],
            }
        )

    cache = tmp_path / "cache"
    bars, audit, _ = load_quote_bars_cached(
        [first, second],
        {},
        quality={},
        completed_through=pd.Timestamp("1970-01-01T00:05:00Z"),
        cache_directory=cache,
        original_loader=loader,
        original_aggregate=aggregate,
    )
    assert len(bars) == 1
    assert int(bars.iloc[0]["xau_tick_count"]) == 4
    assert float(bars.iloc[0]["bid_open"]) == 100.0
    assert float(bars.iloc[0]["bid_close"]) == 103.0
    assert audit["bar_cache"] == {
        "schema_version": "xauusd_v60_r4_per_file_bar_cache_v2",
        "files": 2,
        "hits": 0,
        "misses": 2,
    }

    calls.clear()
    _, audit, _ = load_quote_bars_cached(
        [first, second],
        {},
        quality={},
        completed_through=pd.Timestamp("1970-01-01T00:05:00Z"),
        cache_directory=cache,
        original_loader=loader,
        original_aggregate=aggregate,
    )
    assert calls == []
    assert audit["bar_cache"]["hits"] == 2
