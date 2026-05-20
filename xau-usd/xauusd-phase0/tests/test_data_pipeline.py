from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from phase0.bar_builder import build_bars_from_ticks
from phase0.cli import main
from phase0.config import load_project_config
from phase0.data_validator import DataValidationError, validate_ticks
from phase0.normalizer import normalize_tick_dataframe


def test_normalize_format_a():
    raw = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T00:00:00.123Z"],
            "bid": [1061.25],
            "ask": [1061.45],
            "volume": [1],
        }
    )

    normalized = normalize_tick_dataframe(raw, "capital_com", "XAUUSD", 0.01, "sample.csv")

    assert list(normalized.columns)[0] == "timestamp_utc"
    assert normalized.loc[0, "mid"] == pytest.approx(1061.35)
    assert normalized.loc[0, "spread_points"] == pytest.approx(20.0)
    assert normalized.loc[0, "row_number"] == 2


def test_normalize_mt5_export_format():
    raw = pd.DataFrame(
        {
            "<TICKTIME>": ["2016-01-04T00:00:00Z"],
            "<BID>": [1061.25],
            "<ASK>": [1061.35],
            "<LAST>": [0],
            "<VOLUME>": [3],
        }
    )

    normalized = normalize_tick_dataframe(raw, "capital_com", "XAUUSD", 0.01, "mt5.csv")

    assert normalized.loc[0, "volume"] == 3
    assert normalized.loc[0, "spread_points"] == pytest.approx(10.0)


def test_normalize_dukascopy_format():
    raw = pd.DataFrame(
        {
            "Time": ["2016-01-04T00:00:00Z"],
            "Ask": [1061.35],
            "Bid": [1061.25],
            "AskVolume": [2],
            "BidVolume": [4],
        }
    )

    normalized = normalize_tick_dataframe(raw, "dukascopy", "XAUUSD", 0.01, "duka.csv")

    assert normalized.loc[0, "volume"] == 6
    assert normalized.loc[0, "broker"] == "dukascopy"


def test_validate_ticks_rejects_negative_spread():
    raw = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T00:00:00Z"],
            "bid": [1061.45],
            "ask": [1061.25],
            "volume": [1],
        }
    )
    normalized = normalize_tick_dataframe(raw, "capital_com", "XAUUSD", 0.01, "bad.csv")

    with pytest.raises(DataValidationError, match="Ask must be greater"):
        validate_ticks(normalized, "bad.csv")


def test_build_m5_bars_uses_bar_end_timestamp():
    ticks = _sample_normalized_ticks()

    bars = build_bars_from_ticks(ticks, "M5")

    assert len(bars) == 1
    assert bars.loc[0, "bar_start_utc"] == "2016-01-04T10:00:00Z"
    assert bars.loc[0, "bar_end_utc"] == "2016-01-04T10:05:00Z"
    assert bars.loc[0, "timestamp_utc"] == "2016-01-04T10:05:00Z"
    assert bars.loc[0, "tick_count"] == 5
    assert bars.loc[0, "open"] == pytest.approx(100.1)
    assert bars.loc[0, "close"] == pytest.approx(104.1)


def test_cli_validate_normalize_and_build_bars(project_root, tmp_path, capsys):
    root = _copy_project_config(project_root, tmp_path)
    raw_dir = root / "data" / "raw" / "capital_com"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "XAUUSD_ticks.csv"
    raw_file.write_text(
        "\n".join(
            [
                "timestamp_utc,bid,ask,volume",
                "2016-01-04T10:00:00Z,100.00,100.20,1",
                "2016-01-04T10:01:00Z,101.00,101.20,1",
                "2016-01-04T10:02:00Z,102.00,102.20,1",
                "2016-01-04T10:03:00Z,103.00,103.20,1",
                "2016-01-04T10:04:00Z,104.00,104.20,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["--root", str(root), "validate-data", "--broker", "capital_com", "--symbol", "XAUUSD"]) == 0
    assert main(["--root", str(root), "normalize-data", "--broker", "capital_com", "--symbol", "XAUUSD"]) == 0
    assert (
        main(
            [
                "--root",
                str(root),
                "build-bars",
                "--broker",
                "capital_com",
                "--symbol",
                "XAUUSD",
                "--timeframes",
                "M5",
            ]
        )
        == 0
    )

    captured = capsys.readouterr()
    assert "Validated 1 raw file" in captured.out
    assert "Normalized 1 tick file" in captured.out
    assert "Built 1 bar file" in captured.out
    assert list((root / "data" / "processed" / "ticks").rglob("*.csv"))
    assert list((root / "data" / "processed" / "bars").rglob("*.csv"))
    manifest = root / "outputs" / "manifests" / "PHASE0_DATA_MANIFEST.md"
    assert manifest.exists()
    assert "data/raw/capital_com/XAUUSD_ticks.csv" in manifest.read_text(encoding="utf-8")


def _sample_normalized_ticks() -> pd.DataFrame:
    raw = pd.DataFrame(
        {
            "timestamp_utc": [
                "2016-01-04T10:00:00Z",
                "2016-01-04T10:01:00Z",
                "2016-01-04T10:02:00Z",
                "2016-01-04T10:03:00Z",
                "2016-01-04T10:04:00Z",
            ],
            "bid": [100, 101, 102, 103, 104],
            "ask": [100.2, 101.2, 102.2, 103.2, 104.2],
            "volume": [1, 1, 1, 1, 1],
        }
    )
    return normalize_tick_dataframe(raw, "capital_com", "XAUUSD", 0.01, "sample.csv")


def _copy_project_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root
