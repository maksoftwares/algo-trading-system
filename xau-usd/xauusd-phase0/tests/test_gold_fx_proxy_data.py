from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pandas as pd
import pytest

from phase0.cli import main
from phase0.config import ConfigError, load_project_config
from phase0.data_validator import BAR_REQUIRED_COLUMNS
from phase0.gold_fx_proxy_data import (
    check_gold_fx_proxy_data,
    generate_gold_fx_proxy_data_readiness,
)
from phase0.matrix import run_phase0_matrix


def test_gold_fx_proxy_data_readiness_reports_missing_venue_proxy_sets(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_h1_placeholder(
        root,
        "capital_com",
        "EURUSD",
        "2016-01-01T00:00:00Z",
        "2018-12-31T23:00:00Z",
    )
    _write_h1_placeholder(
        root,
        "capital_com",
        "USDJPY",
        "2016-01-01T00:00:00Z",
        "2018-12-31T23:00:00Z",
    )
    config = load_project_config(root)

    checks = check_gold_fx_proxy_data(config)

    assert len(checks) == 6
    assert sum(check.available for check in checks) == 2
    missing = {(check.broker, check.symbol) for check in checks if not check.available}
    assert ("pepperstone", "EURUSD") in missing
    assert ("dukascopy", "USDJPY") in missing


def test_generate_gold_fx_proxy_data_readiness_artifacts(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    output = generate_gold_fx_proxy_data_readiness(config)

    assert output.status == "BLOCKED"
    assert output.report_path.exists()
    assert output.requirements_path.exists()
    text = output.report_path.read_text(encoding="utf-8")
    assert "Status: BLOCKED" in text
    assert "Capital.com EURUSD/USDJPY may not be substituted" in text
    rows = list(csv.DictReader(output.requirements_path.open(encoding="utf-8")))
    assert len(rows) == 6
    assert any(row["broker"] == "pepperstone" and row["symbol"] == "EURUSD" for row in rows)


def test_generate_gold_fx_proxy_data_readiness_cli(project_root, tmp_path, capsys):
    root = _copy_config(project_root, tmp_path)

    exit_code = main(["--root", str(root), "generate-gold-fx-proxy-data-readiness"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "gold_fx_proxy_divergence_v0 data readiness: BLOCKED" in captured.out
    assert (
        root / "outputs" / "manifests" / "GOLD_FX_PROXY_DIVERGENCE_V0_DATA_READINESS.md"
    ).exists()


def test_gold_fx_proxy_research_matrix_blocks_before_partial_outputs(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    config = load_project_config(root)

    with pytest.raises(ConfigError, match="blocked by missing proxy data"):
        run_phase0_matrix(
            config,
            "gold_fx_proxy_divergence_v0",
            allow_research_candidate=True,
        )

    assert not (root / "outputs" / "matrix_results" / "gold_fx_proxy_divergence_v0").exists()


def _copy_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root


def _write_h1_placeholder(
    root: Path,
    broker: str,
    symbol: str,
    start_utc: str,
    end_start_utc: str,
) -> None:
    directory = root / "data" / "processed" / "bars" / broker / symbol / "H1"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{symbol}_{broker}_H1_sample.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BAR_REQUIRED_COLUMNS)
        writer.writeheader()
        for bar_start in pd.date_range(start_utc, end_start_utc, freq="6D"):
            writer.writerow(_valid_h1_bar_row(broker, symbol, bar_start))
        writer.writerow(_valid_h1_bar_row(broker, symbol, pd.Timestamp(end_start_utc)))


def _valid_h1_bar_row(broker: str, symbol: str, bar_start: pd.Timestamp) -> dict[str, object]:
    bar_end = pd.Timestamp(bar_start) + pd.Timedelta(hours=1)
    return {
        "timestamp_utc": _format_utc(bar_end),
        "bar_start_utc": _format_utc(bar_start),
        "bar_end_utc": _format_utc(bar_end),
        "broker": broker,
        "symbol": symbol,
        "timeframe": "H1",
        "open": 1.0,
        "high": 1.1,
        "low": 0.9,
        "close": 1.02,
        "mid_open": 1.0,
        "mid_high": 1.1,
        "mid_low": 0.9,
        "mid_close": 1.02,
        "bid_open": 0.999,
        "bid_high": 1.099,
        "bid_low": 0.899,
        "bid_close": 1.019,
        "ask_open": 1.001,
        "ask_high": 1.101,
        "ask_low": 0.901,
        "ask_close": 1.021,
        "spread_open_points": 20.0,
        "spread_close_points": 20.0,
        "spread_median_points": 20.0,
        "spread_p95_points": 22.0,
        "tick_count": 10,
        "volume_sum": 100,
    }


def _format_utc(timestamp: pd.Timestamp) -> str:
    return pd.Timestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%SZ")
