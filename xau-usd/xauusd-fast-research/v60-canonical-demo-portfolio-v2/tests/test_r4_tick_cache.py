from __future__ import annotations

from pathlib import Path

import pandas as pd

from r4_tick_cache import load_ticks_cached


def test_cache_refreshes_only_changed_source(tmp_path: Path) -> None:
    first = tmp_path / "ticks_20260101.csv"
    second = tmp_path / "ticks_20260102.csv"
    first.write_text("one\n", encoding="ascii")
    second.write_text("two\n", encoding="ascii")
    calls: list[str] = []

    def loader(paths, _config):
        path = Path(list(paths)[0])
        calls.append(path.name)
        day = "2026-01-01" if "01" in path.stem[-2:] else "2026-01-02"
        timestamp = 1_000 if day.endswith("01") else 2_000
        frame = pd.DataFrame(
            {
                "timestamp_utc": [""],
                "tick_time_msc": [timestamp],
                "bid": [100.0],
                "ask": [100.1],
                "spread_price": [0.1],
                "source_file_order": [0],
                "source_row": [0],
                "source_path": [str(path)],
                "date_utc": [day],
            }
        )
        daily = pd.DataFrame(
            {
                "date_utc": [day],
                "raw_rows": [1],
                "unique_milliseconds": [1],
                "duplicate_millisecond_rows": [0],
                "duplicate_millisecond_share": [0.0],
            }
        )
        audit = {
            "source_files": [{"path": str(path), "raw_rows": 1}],
            "raw_rows": 1,
        }
        return frame, audit, daily

    cache = tmp_path / "cache"
    ticks, audit, _ = load_ticks_cached(
        [first, second], {}, cache_directory=cache, original_loader=loader
    )
    assert len(ticks) == 2
    assert audit["cache"]["misses"] == 2
    assert calls == [first.name, second.name]

    calls.clear()
    _, audit, _ = load_ticks_cached(
        [first, second], {}, cache_directory=cache, original_loader=loader
    )
    assert audit["cache"]["hits"] == 2
    assert calls == []

    second.write_text("two changed\n", encoding="ascii")
    calls.clear()
    _, audit, _ = load_ticks_cached(
        [first, second], {}, cache_directory=cache, original_loader=loader
    )
    assert audit["cache"]["hits"] == 1
    assert audit["cache"]["misses"] == 1
    assert calls == [second.name]


def test_cache_invalidates_when_loader_config_changes(tmp_path: Path) -> None:
    source = tmp_path / "ticks_20260101.csv"
    source.write_text("one\n", encoding="ascii")
    calls = 0

    def loader(paths, _config):
        nonlocal calls
        calls += 1
        path = Path(list(paths)[0])
        frame = pd.DataFrame(
            {
                "timestamp_utc": [""],
                "tick_time_msc": [1_000],
                "bid": [100.0],
                "ask": [100.1],
                "spread_price": [0.1],
                "source_file_order": [0],
                "source_row": [0],
                "source_path": [str(path)],
                "date_utc": ["2026-01-01"],
            }
        )
        daily = pd.DataFrame(
            {
                "date_utc": ["2026-01-01"],
                "raw_rows": [1],
                "unique_milliseconds": [1],
                "duplicate_millisecond_rows": [0],
                "duplicate_millisecond_share": [0.0],
            }
        )
        return frame, {"source_files": [], "raw_rows": 1}, daily

    cache = tmp_path / "cache"
    load_ticks_cached(
        [source], {"validation": 1}, cache_directory=cache, original_loader=loader
    )
    load_ticks_cached(
        [source], {"validation": 1}, cache_directory=cache, original_loader=loader
    )
    load_ticks_cached(
        [source], {"validation": 2}, cache_directory=cache, original_loader=loader
    )
    assert calls == 2


def test_daily_duplicate_audit_matches_cross_file_deduplication(tmp_path: Path) -> None:
    first = tmp_path / "ticks_a.csv"
    second = tmp_path / "ticks_b.csv"
    first.write_text("one\n", encoding="ascii")
    second.write_text("two\n", encoding="ascii")

    def loader(paths, _config):
        path = Path(list(paths)[0])
        timestamp = 1_000 if path == first else 1_000
        frame = pd.DataFrame(
            {
                "timestamp_utc": [""],
                "tick_time_msc": [timestamp],
                "bid": [100.0],
                "ask": [100.1],
                "spread_price": [0.1],
                "source_file_order": [0],
                "source_row": [0],
                "source_path": [str(path)],
                "date_utc": ["2026-01-01"],
            }
        )
        daily = pd.DataFrame(
            {
                "date_utc": ["2026-01-01"],
                "raw_rows": [1],
                "unique_milliseconds": [1],
                "duplicate_millisecond_rows": [0],
                "duplicate_millisecond_share": [0.0],
            }
        )
        return frame, {"source_files": [], "raw_rows": 1}, daily

    ticks, audit, daily = load_ticks_cached(
        [first, second], {}, cache_directory=tmp_path / "cache", original_loader=loader
    )
    assert len(ticks) == 1
    assert audit["duplicate_millisecond_rows"] == 1
    assert daily.iloc[0].to_dict() == {
        "date_utc": "2026-01-01",
        "raw_rows": 2,
        "unique_milliseconds": 1,
        "duplicate_millisecond_rows": 1,
        "duplicate_millisecond_share": 0.5,
    }
