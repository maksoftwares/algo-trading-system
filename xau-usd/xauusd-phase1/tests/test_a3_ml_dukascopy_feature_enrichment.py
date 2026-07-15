from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from ml.a3_meta_v1 import dukascopy_feature_enrichment as D


def _fixture_storage(tmp_path: Path) -> tuple[Path, object]:
    storage = tmp_path / "storage"
    month = storage / "raw" / "XAUUSD" / "year=2024" / "month=01"
    month.mkdir(parents=True)
    rows = []
    for hour in (4, 5):
        raw = f"hour={hour}".encode("ascii")
        path = month / f"20240102{hour:02d}.json"
        path.write_bytes(raw)
        relative = path.relative_to(storage).as_posix()
        rows.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "status": "DOWNLOADED_VALID",
            }
        )
    (month / "_ACQUISITION_MANIFEST.json").write_text(json.dumps({"rows": rows}), encoding="utf-8")

    def decoder(raw: bytes, symbol: str, source_file_id: str) -> list[SimpleNamespace]:
        hour = int(raw.decode("ascii").split("=")[1])
        base = int(datetime(2024, 1, 2, hour, tzinfo=UTC).timestamp() * 1000)
        ticks = []
        for minute in range(60):
            spread = 20.0 if hour == 5 and minute == 30 else 0.30
            ticks.append(
                SimpleNamespace(
                    timestamp_ms=base + minute * 60_000,
                    bid=2000.0 + minute / 100.0,
                    ask=2000.0 + minute / 100.0 + spread,
                )
            )
        return ticks

    return storage, decoder


def test_enrichment_is_strictly_pre_entry_and_manifest_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo" / "xau-usd" / "xauusd-phase1"
    root.mkdir(parents=True)
    storage, decoder = _fixture_storage(tmp_path)
    monkeypatch.setenv("DUKASCOPY_TICK_DATA_ROOT", str(storage))
    monkeypatch.setattr(D, "_load_decoder", lambda _root: decoder)
    rows = [
        {
            "split": "validation",
            "strategy_family": "family",
            "direction": "LONG",
            "entry_time": "2024-01-02T05:30:00Z",
        }
    ]
    config = {
        "source": "OFFICIAL_DUKASCOPY_JETTA_V1",
        "storage_environment_variable": "DUKASCOPY_TICK_DATA_ROOT",
        "symbol": "XAUUSD",
        "coverage_start_utc": "2024-01-01T00:00:00Z",
        "coverage_end_exclusive_utc": "2024-02-01T00:00:00Z",
        "strictly_before_entry": True,
        "lookback_minutes": 60,
        "pre_roll_minutes": 5,
        "exclude_unavailable_rows": True,
    }

    enriched, audit = D.enrich_rows_with_dukascopy_features(root, rows, config)

    assert enriched[0]["duka_spread_last_bps"] < 10.0
    assert audit["future_ticks_used"] == 0
    assert audit["missing_rows"] == 0
    assert audit["source_hour_files"] == 2


def test_enrichment_fails_closed_on_missing_raw_hour(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo" / "xau-usd" / "xauusd-phase1"
    root.mkdir(parents=True)
    storage = tmp_path / "storage"
    (storage / "raw" / "XAUUSD").mkdir(parents=True)
    monkeypatch.setenv("DUKASCOPY_TICK_DATA_ROOT", str(storage))
    monkeypatch.setattr(D, "_load_decoder", lambda _root: lambda *_args: [])
    config = {
        "source": "OFFICIAL_DUKASCOPY_JETTA_V1",
        "storage_environment_variable": "DUKASCOPY_TICK_DATA_ROOT",
        "symbol": "XAUUSD",
        "coverage_start_utc": "2024-01-01T00:00:00Z",
        "coverage_end_exclusive_utc": "2024-02-01T00:00:00Z",
        "strictly_before_entry": True,
        "lookback_minutes": 60,
        "pre_roll_minutes": 5,
        "exclude_unavailable_rows": True,
    }
    rows = [
        {
            "split": "validation",
            "strategy_family": "family",
            "direction": "LONG",
            "entry_time": "2024-01-02T05:30:00Z",
        }
    ]

    with pytest.raises(ValueError, match="missing Dukascopy raw hour"):
        D.enrich_rows_with_dukascopy_features(root, rows, config)
