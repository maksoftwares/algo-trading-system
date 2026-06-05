from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_wr50_daily_report import compute_metrics, write_reports
from validate_wr50_logs import validate_ledger_rows
from validate_wr50_registry import parse_registry_markdown


REGISTRY = {int(row["active_magic"]): row for row in parse_registry_markdown(ROOT / "docs" / "WR50_EA_REGISTRY.md")}


def _valid_row(magic: str = "930000", comment: str = "WR50|BEV0|R240604A") -> dict[str, str]:
    return {
        "timestamp_broker": "2026.06.04 18:05:00",
        "timestamp_utc": "2026-06-04T14:05:00Z",
        "timestamp_local": "2026-06-04T18:05:00+04:00",
        "account": "1025742",
        "server": "Capital.ComMena-Demo",
        "symbol": "XAUUSD",
        "ea_id": "wr50_bev0",
        "ea_short_code": "BEV0",
        "ea_version": "v0",
        "strategy_family": "breakout_retest_wr50_experimental",
        "experiment_id": "WR50_20260604_A",
        "run_id": "R240604A",
        "magic": magic,
        "order_ticket": "1001",
        "position_id": "2001",
        "deal_ticket": "3001",
        "direction": "BUY",
        "entry_type": "BUY_STOP",
        "lot": "0.01",
        "entry_price": "2350.0",
        "sl_price": "2348.0",
        "tp_price": "2353.0",
        "exit_price": "2353.0",
        "entry_time_broker": "2026.06.04 18:05:00",
        "exit_time_broker": "2026.06.04 19:05:00",
        "entry_spread_points": "45",
        "exit_spread_points": "50",
        "commission": "0",
        "swap": "0",
        "profit_account_currency": "3.0",
        "gross_r": "1.5",
        "net_r": "1.5",
        "cost_r": "0.1",
        "session_bucket": "evening",
        "reason_code": "WR50_BEV0_LONG",
        "block_reason": "",
        "comment": comment,
    }


def test_unknown_magic_in_sample_ledger_fails_log_validator() -> None:
    result = validate_ledger_rows([_valid_row(magic="930999")], REGISTRY)
    assert not result.ok
    assert any("unknown WR50 magic" in error for error in result.errors)


def test_valid_sample_ledger_passes_log_validator() -> None:
    result = validate_ledger_rows([_valid_row()], REGISTRY)
    assert result.ok, result.errors


def test_report_builder_outputs_group_summary(tmp_path: Path) -> None:
    rows = [_valid_row(), {**_valid_row(), "order_ticket": "1002", "deal_ticket": "3002", "profit_account_currency": "-2.0", "net_r": "-1.0"}]
    metrics = compute_metrics(rows)
    assert len(metrics) == 1
    assert metrics[0].trades == 2
    assert metrics[0].win_rate == 0.5

    root = tmp_path / "wr50"
    write_reports(root, rows, metrics)
    summary = root / "outputs" / "reports" / "WR50_EXPERIMENTAL_SUMMARY.csv"
    assert summary.exists()
    with summary.open(newline="", encoding="utf-8") as handle:
        summary_rows = list(csv.DictReader(handle))
    assert summary_rows[0]["ea_id"] == "wr50_bev0"

