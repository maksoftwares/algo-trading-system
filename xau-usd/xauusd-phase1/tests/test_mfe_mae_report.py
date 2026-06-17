from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mfe_mae_uses_path_snapshots_and_flags_green_loser(tmp_path: Path):
    module = _load_module()
    actual = tmp_path / "actual.csv"
    _write_rows(
        actual,
        [
            "entry_time",
            "exit_time",
            "candidate",
            "symbol",
            "direction",
            "volume",
            "entry_price",
            "exit_price",
            "sl",
            "tp",
            "state",
            "profit_aed",
            "position_ticket",
            "time_bucket",
        ],
        [
            {
                "entry_time": "2026-06-16 18:00:00",
                "exit_time": "2026-06-16 18:20:00",
                "candidate": "breakout_retest",
                "symbol": "XAUUSD",
                "direction": "BUY",
                "volume": "0.01",
                "entry_price": "4300.00",
                "exit_price": "4297.00",
                "sl": "4297.00",
                "tp": "4304.50",
                "state": "CLOSED",
                "profit_aed": "-10.00",
                "position_ticket": "1001",
                "time_bucket": "Evening 16:00-19:59",
            }
        ],
    )
    path_dir = tmp_path / "path"
    path_dir.mkdir()
    _write_rows(
        path_dir / "position_path_log_20260616.csv",
        [
            "ts_utc",
            "position_ticket",
            "symbol",
            "direction",
            "entry_price",
            "price_current",
            "unrealized_R",
        ],
        [
            {
                "ts_utc": "2026.06.16 18:05:00",
                "position_ticket": "1001",
                "symbol": "XAUUSD",
                "direction": "BUY",
                "entry_price": "4300.00",
                "price_current": "4302.00",
                "unrealized_R": "0.6667",
            },
            {
                "ts_utc": "2026.06.16 18:15:00",
                "position_ticket": "1001",
                "symbol": "XAUUSD",
                "direction": "BUY",
                "entry_price": "4300.00",
                "price_current": "4297.00",
                "unrealized_R": "-1.0000",
            },
        ],
    )

    output = module.generate_mfe_mae_report(
        tmp_path,
        actual_trades_csv=actual,
        position_path_files=path_dir,
        output_csv=tmp_path / "mfe.csv",
        output_json=tmp_path / "mfe.json",
        output_md=tmp_path / "mfe.md",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = _read_rows(tmp_path / "mfe.csv")

    assert payload["status"] == "PASS"
    assert rows[0]["source"] == "PATH_SNAPSHOTS"
    assert rows[0]["mfe_points"] == "200.0000"
    assert rows[0]["mfe_r"] == "0.6667"
    assert rows[0]["mae_r"] == "1.0000"
    assert rows[0]["went_green_then_lost"] == "true"


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_module():
    path = ROOT / "scripts" / "generate_mfe_mae_report.py"
    spec = importlib.util.spec_from_file_location("generate_mfe_mae_report", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_mfe_mae_report"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
