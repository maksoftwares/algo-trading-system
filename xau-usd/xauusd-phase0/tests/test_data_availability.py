from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pandas as pd
import pytest

from phase0.cli import main
from phase0.config import ConfigError, load_project_config
from phase0.constants import COMPARISON_SYMBOLS
from phase0.data_validator import BAR_REQUIRED_COLUMNS
from phase0.data_availability import (
    REQUIRED_BACKTEST_TIMEFRAMES,
    assert_processed_data_available,
    check_processed_data_availability,
    generate_data_requirements_csv,
    generate_data_readiness_report,
)


TIMEFRAME_DELTAS = {
    "M5": pd.Timedelta(minutes=5),
    "M15": pd.Timedelta(minutes=15),
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
    "D1": pd.Timedelta(days=1),
}


def test_processed_data_availability_reports_missing_sets(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    checks = check_processed_data_availability(config)

    assert len(checks) == 25
    assert all(not check.available for check in checks)
    with pytest.raises(ConfigError, match="import-required-bars"):
        assert_processed_data_available(config)


def test_processed_data_availability_passes_when_required_files_exist(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_required_bar_placeholders(root)
    config = load_project_config(root)

    checks = assert_processed_data_available(config)

    assert len(checks) == 25
    assert all(check.available for check in checks)
    assert all(check.file_count == 1 for check in checks)
    assert all(check.candidate_file_count == 1 for check in checks)


def test_processed_data_availability_rejects_malformed_files(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_malformed_bar_placeholders(root)
    config = load_project_config(root)

    checks = check_processed_data_availability(config)

    assert all(not check.available for check in checks)
    assert all(check.candidate_file_count == 1 for check in checks)
    with pytest.raises(ConfigError, match="candidate_files=1"):
        assert_processed_data_available(config)


def test_processed_data_availability_rejects_insufficient_coverage(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_short_bar_placeholders(root)
    config = load_project_config(root)

    checks = check_processed_data_availability(config)

    assert all(not check.available for check in checks)
    assert all(check.file_count == 1 for check in checks)
    assert any("coverage starts" in issue for check in checks for issue in check.issues)
    with pytest.raises(ConfigError, match="coverage starts"):
        assert_processed_data_available(config)


def test_processed_data_availability_rejects_large_internal_gaps(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_large_gap_bar_placeholders(root)
    config = load_project_config(root)

    checks = check_processed_data_availability(config)

    assert all(not check.available for check in checks)
    assert all(check.file_count == 1 for check in checks)
    assert any("largest timestamp gap" in issue for check in checks for issue in check.issues)
    with pytest.raises(ConfigError, match="largest timestamp gap"):
        assert_processed_data_available(config)


def test_check_data_availability_cli(project_root, tmp_path, capsys):
    root = _copy_config(project_root, tmp_path)
    _write_required_bar_placeholders(root)

    exit_code = main(["--root", str(root), "check-data-availability"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Processed data availability OK" in captured.out


def test_generate_data_readiness_report_lists_missing_sets(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    report_path = generate_data_readiness_report(config)

    text = report_path.read_text(encoding="utf-8")
    assert "Status: BLOCKED" in text
    assert "Blocked timeframe sets: 25" in text
    assert "capital_com | XAUUSD | M5" in text
    assert "Required Start" in text
    assert "python -m phase0 normalize-bars --broker capital_com --symbol XAUUSD --timeframe M5" in text


def test_generate_data_requirements_csv_lists_required_inputs(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    output_path = generate_data_requirements_csv(config)

    rows = list(csv.DictReader(output_path.open(encoding="utf-8")))
    assert len(rows) == 25
    first = next(row for row in rows if row["broker"] == "capital_com" and row["symbol"] == "XAUUSD")
    assert first["timeframe"] in REQUIRED_BACKTEST_TIMEFRAMES
    assert first["required_start_utc"] == "2016-01-01T00:00:00Z"
    assert first["required_end_utc"] == "2025-06-30T23:59:59Z"
    assert "data" in first["raw_dir"]
    assert first["suggested_raw_filename"].startswith(f"XAUUSD_{first['timeframe']}_")


def test_generate_data_requirements_cli(project_root, tmp_path, capsys):
    root = _copy_config(project_root, tmp_path)

    exit_code = main(["--root", str(root), "generate-data-requirements"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Required timeframe sets: 25" in captured.out
    assert (root / "outputs" / "manifests" / "PHASE0_DATA_REQUIREMENTS.csv").exists()


def test_generate_data_readiness_cli(project_root, tmp_path, capsys):
    root = _copy_config(project_root, tmp_path)

    exit_code = main(["--root", str(root), "generate-data-readiness"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Ready: 0/25" in captured.out
    assert (root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md").exists()


def _copy_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root


def _write_required_bar_placeholders(root: Path) -> None:
    _write_bar_placeholders(root, start_step_days=6)


def _write_large_gap_bar_placeholders(root: Path) -> None:
    _write_bar_placeholders(root)


def _write_bar_placeholders(root: Path, start_step_days: int | None = None) -> None:
    broker_symbols = {
        ("capital_com", "XAUUSD"),
        ("pepperstone", "XAUUSD"),
        ("dukascopy", "XAUUSD"),
        *(("capital_com", symbol) for symbol in COMPARISON_SYMBOLS),
    }
    for broker, symbol in broker_symbols:
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            directory = root / "data" / "processed" / "bars" / broker / symbol / timeframe
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"{symbol}_{broker}_{timeframe}_sample.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=BAR_REQUIRED_COLUMNS)
                writer.writeheader()
                for bar_start in _bar_start_samples(timeframe, start_step_days):
                    writer.writerow(_valid_bar_row(broker, symbol, timeframe, str(bar_start)))


def _bar_start_samples(timeframe: str, start_step_days: int | None) -> list[pd.Timestamp]:
    first_bar_start = pd.Timestamp("2016-01-01T00:00:00Z")
    last_bar_start = _last_bar_start(timeframe)
    if start_step_days is None:
        return [first_bar_start, last_bar_start]
    starts = list(pd.date_range(first_bar_start, last_bar_start, freq=f"{start_step_days}D"))
    if starts[-1] != last_bar_start:
        starts.append(last_bar_start)
    return starts


def _write_short_bar_placeholders(root: Path) -> None:
    broker_symbols = {
        ("capital_com", "XAUUSD"),
        ("pepperstone", "XAUUSD"),
        ("dukascopy", "XAUUSD"),
        *(("capital_com", symbol) for symbol in COMPARISON_SYMBOLS),
    }
    for broker, symbol in broker_symbols:
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            directory = root / "data" / "processed" / "bars" / broker / symbol / timeframe
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"{symbol}_{broker}_{timeframe}_sample.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=BAR_REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    _valid_bar_row(
                        broker,
                        symbol,
                        timeframe,
                        "2020-01-01T00:00:00Z",
                    )
                )


def _write_malformed_bar_placeholders(root: Path) -> None:
    broker_symbols = {
        ("capital_com", "XAUUSD"),
        ("pepperstone", "XAUUSD"),
        ("dukascopy", "XAUUSD"),
        *(("capital_com", symbol) for symbol in COMPARISON_SYMBOLS),
    }
    for broker, symbol in broker_symbols:
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            directory = root / "data" / "processed" / "bars" / broker / symbol / timeframe
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{symbol}_{broker}_{timeframe}_sample.csv").write_text(
                "timestamp_utc,bar_start_utc,open,high,low,close\n",
                encoding="utf-8",
            )


def _valid_bar_row(
    broker: str,
    symbol: str,
    timeframe: str,
    bar_start_utc: str,
) -> dict[str, object]:
    bar_start = pd.Timestamp(bar_start_utc)
    bar_end = bar_start + TIMEFRAME_DELTAS[timeframe]
    return {
        "timestamp_utc": _format_utc(bar_end),
        "bar_start_utc": _format_utc(bar_start),
        "bar_end_utc": _format_utc(bar_end),
        "broker": broker,
        "symbol": symbol,
        "timeframe": timeframe,
        "open": 2000.0,
        "high": 2001.0,
        "low": 1999.0,
        "close": 2000.5,
        "mid_open": 2000.0,
        "mid_high": 2001.0,
        "mid_low": 1999.0,
        "mid_close": 2000.5,
        "bid_open": 1999.9,
        "bid_high": 2000.9,
        "bid_low": 1998.9,
        "bid_close": 2000.4,
        "ask_open": 2000.1,
        "ask_high": 2001.1,
        "ask_low": 1999.1,
        "ask_close": 2000.6,
        "spread_open_points": 20.0,
        "spread_close_points": 20.0,
        "spread_median_points": 20.0,
        "spread_p95_points": 22.0,
        "tick_count": 10,
        "volume_sum": 100,
    }


def _last_bar_start(timeframe: str) -> pd.Timestamp:
    return pd.Timestamp("2026-01-01T00:00:00Z") - TIMEFRAME_DELTAS[timeframe]


def _format_utc(timestamp: pd.Timestamp) -> str:
    return pd.Timestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%SZ")
