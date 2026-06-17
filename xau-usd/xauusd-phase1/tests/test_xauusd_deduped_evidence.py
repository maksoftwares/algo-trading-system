from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_xauusd_deduped_evidence_collapses_clone_stack(tmp_path: Path):
    module = _load_module()
    actual = tmp_path / "actual.csv"
    _write_rows(
        actual,
        [
            "entry_time",
            "exit_time",
            "candidate",
            "status",
            "symbol",
            "direction",
            "volume",
            "state",
            "profit_aed",
            "position_ticket",
            "time_bucket",
        ],
        [
            _trade("breakout_retest", "100", "25.00"),
            _trade("swing_breakout_retest_v0", "101", "30.00"),
            _trade("p2weakness_br_v1", "102", "35.00"),
            _trade("round_number_retest_v0", "103", "-10.00", minute="2026-06-16 19:05"),
        ],
    )

    output = module.generate_xauusd_deduped_evidence(
        tmp_path,
        actual_trades_csv=actual,
        output_prefix=tmp_path / "XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["raw_baseline"]["rows"] == 4
    assert payload["dedup_baseline"]["rows"] == 2
    assert payload["duplicate_inflation"]["duplicate_rows_removed"] == 2
    p2 = next(row for row in payload["watchlist_artifact_checks"] if row["candidate"] == "p2weakness_br_v1")
    assert p2["raw_trades"] == "1"
    assert p2["dedup_selected_trades"] == "0"
    assert p2["dedup_participating_unique_signals"] == "1"


def _trade(candidate: str, ticket: str, profit: str, *, minute: str = "2026-06-16 19:00") -> dict[str, str]:
    return {
        "entry_time": f"{minute}:00",
        "exit_time": f"{minute}:30",
        "candidate": candidate,
        "status": "EXPERIMENTAL",
        "symbol": "XAUUSD",
        "direction": "SELL",
        "volume": "0.01",
        "state": "CLOSED",
        "profit_aed": profit,
        "position_ticket": ticket,
        "time_bucket": "Evening 16:00-19:59",
    }


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_module():
    path = ROOT / "scripts" / "generate_xauusd_deduped_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_xauusd_deduped_evidence", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_xauusd_deduped_evidence"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
