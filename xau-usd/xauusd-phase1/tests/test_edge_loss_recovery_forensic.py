from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_edge_loss_recovery_forensic.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_edge_loss_recovery_forensic", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_trades(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def base_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "entry_time": "2026-06-01 16:05:00",
        "exit_time": "2026-06-01 16:35:00",
        "candidate": "breakout_retest",
        "status": "CLOSED",
        "symbol": "XAUUSD",
        "direction": "BUY",
        "volume": "0.01",
        "entry_price": "3300.0",
        "exit_price": "3310.0",
        "sl": "3290.0",
        "tp": "3315.0",
        "state": "CLOSED",
        "profit_aed": "100.00",
        "position_ticket": "1",
        "magic": "920101",
        "entry_order": "1",
        "exit_order": "2",
        "entry_deal": "3",
        "exit_deal": "4",
        "duplicate_key": "k1",
        "duplicate_role": "unique",
        "is_duplicate": "false",
        "time_bucket": "Evening 16:00-19:59",
        "weakness_shadow_action": "KEEP",
        "weakness_shadow_reason": "test",
        "entry_comment": "entry",
        "exit_comment": "exit",
    }
    row.update(overrides)
    return row


def test_edge_loss_payload_identifies_positive_core_and_weak_lanes(tmp_path: Path) -> None:
    module = load_module()
    module.runtime_log_findings = lambda: {"mock": {"exists": False}}
    trades_csv = tmp_path / "trades.csv"
    write_trades(
        trades_csv,
        [
            base_row(profit_aed="100.00", position_ticket="1"),
            base_row(
                entry_time="2026-06-01 16:06:00",
                profit_aed="80.00",
                position_ticket="2",
                duplicate_role="duplicate",
                is_duplicate="true",
            ),
            base_row(
                entry_time="2026-06-09 10:00:00",
                candidate="symbol_normalized_round_retest_v0",
                symbol="XAUUSD",
                magic="920301",
                profit_aed="-60.00",
                position_ticket="3",
                time_bucket="Morning 06:00-11:59",
            ),
            base_row(
                entry_time="2026-06-16 17:00:00",
                candidate="breakout_retest",
                symbol="EURUSD",
                magic="920101",
                profit_aed="-30.00",
                position_ticket="4",
            ),
        ],
    )

    payload = module.build_payload(trades_csv)
    markdown = module.render_markdown(payload)

    assert payload["status"] == "OFFLINE_FORENSIC_NO_RUNTIME_CHANGE"
    assert payload["row_counts"] == {"raw_closed": 4, "deduped_closed": 3, "duplicates_removed": 1}
    assert payload["periods"]["early_window_jun_01_07"]["deduped"]["pnl_aed"] == 100.0
    assert payload["periods"]["expansion_loss_jun_08_14"]["deduped"]["pnl_aed"] == -60.0
    assert payload["periods"]["guardrail_drift_jun_15_19"]["deduped"]["pnl_aed"] == -30.0
    assert payload["positive_core"]["evening_920101_xau"]["pnl_aed"] == 100.0
    assert payload["weak_lanes"]["overall"]["pnl_aed"] == -60.0
    assert "OFFLINE_FORENSIC_NO_RUNTIME_CHANGE" in markdown
    assert "The fix is not to go back to the broad old portfolio." in markdown


def test_group_sort_can_rank_losses_ascending_when_requested() -> None:
    module = load_module()
    rows = [
        {"entry_date": "2026-06-01", "profit_aed": 5.0, "bucket": "b"},
        {"entry_date": "2026-06-01", "profit_aed": -10.0, "bucket": "a"},
    ]

    ranked = module.sorted_group(rows, "bucket", reverse=False)

    assert [item["group"] for item in ranked] == ["a", "b"]
