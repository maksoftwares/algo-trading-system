from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pandas as pd

from phase0.cli import main
from phase0.config import load_project_config
from phase0.data_validator import BAR_REQUIRED_COLUMNS
from phase0.xau_xag_relative_data import (
    check_xau_xag_relative_data,
    generate_xau_xag_relative_data_readiness,
)


def test_xau_xag_relative_data_readiness_reports_missing_xag_sets(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    checks = check_xau_xag_relative_data(config)

    assert len(checks) == 3
    assert {check.broker for check in checks} == {"capital_com", "pepperstone", "dukascopy"}
    assert all(check.symbol == "XAGUSD" for check in checks)
    assert sum(check.available for check in checks) == 0


def test_xau_xag_relative_data_readiness_passes_when_all_broker_sets_exist(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_h1_placeholder(root, "capital_com", "2016-01-01T00:00:00Z", "2018-12-31T23:00:00Z")
    _write_h1_placeholder(root, "pepperstone", "2019-01-01T00:00:00Z", "2021-12-31T23:00:00Z")
    _write_h1_placeholder(root, "dukascopy", "2022-01-01T00:00:00Z", "2024-12-31T23:00:00Z")
    config = load_project_config(root)

    output = generate_xau_xag_relative_data_readiness(config)

    assert output.status == "PASS"
    assert output.ready_count == 3
    rows = list(csv.DictReader(output.requirements_path.open(encoding="utf-8")))
    assert len(rows) == 3
    assert all(row["strict_authoritative_use"] == "present_locally" for row in rows)


def test_generate_xau_xag_relative_data_readiness_cli(project_root, tmp_path, capsys):
    root = _copy_config(project_root, tmp_path)

    exit_code = main(["--root", str(root), "generate-xau-xag-relative-data-readiness"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "xau_xag_relative_value_v0 data readiness: BLOCKED" in captured.out
    assert (
        root / "outputs" / "manifests" / "XAU_XAG_RELATIVE_VALUE_V0_DATA_READINESS.md"
    ).exists()


def _copy_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root


def _write_h1_placeholder(root: Path, broker: str, start_utc: str, end_start_utc: str) -> None:
    directory = root / "data" / "processed" / "bars" / broker / "XAGUSD" / "H1"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"XAGUSD_{broker}_H1_sample.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BAR_REQUIRED_COLUMNS)
        writer.writeheader()
        for bar_start in pd.date_range(start_utc, end_start_utc, freq="6D"):
            writer.writerow(_valid_h1_bar_row(broker, bar_start))
        writer.writerow(_valid_h1_bar_row(broker, pd.Timestamp(end_start_utc)))


def _valid_h1_bar_row(broker: str, bar_start: pd.Timestamp) -> dict[str, object]:
    bar_end = pd.Timestamp(bar_start) + pd.Timedelta(hours=1)
    return {
        "timestamp_utc": _format_utc(bar_end),
        "bar_start_utc": _format_utc(bar_start),
        "bar_end_utc": _format_utc(bar_end),
        "broker": broker,
        "symbol": "XAGUSD",
        "timeframe": "H1",
        "open": 24.0,
        "high": 24.1,
        "low": 23.9,
        "close": 24.02,
        "mid_open": 24.0,
        "mid_high": 24.1,
        "mid_low": 23.9,
        "mid_close": 24.02,
        "bid_open": 23.999,
        "bid_high": 24.099,
        "bid_low": 23.899,
        "bid_close": 24.019,
        "ask_open": 24.001,
        "ask_high": 24.101,
        "ask_low": 23.901,
        "ask_close": 24.021,
        "spread_open_points": 2.0,
        "spread_close_points": 2.0,
        "spread_median_points": 2.0,
        "spread_p95_points": 3.0,
        "tick_count": 10,
        "volume_sum": 100,
    }


def _format_utc(timestamp: pd.Timestamp) -> str:
    return pd.Timestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%SZ")
