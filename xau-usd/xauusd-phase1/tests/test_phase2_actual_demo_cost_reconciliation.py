from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_actual_demo_cost_reconciliation_marks_cost_resolved_without_phase2_promotion(tmp_path):
    module = _load_module()
    root = tmp_path / "repo" / "xau-usd" / "xauusd-phase1"
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    reports = root / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_status(phase0_reports / "MEASURED_COST_MODEL.md", "PASS")
    _write_status(phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md", "FAIL")
    _write_status(phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md", "FAIL")
    _write_status(phase0_reports / "BREAKOUT_RETEST_COST_R_DIAGNOSTIC.md", "FAIL")
    actual = reports / "actual.csv"
    order_log = reports / "order_log.csv"
    _write_actual_trades(actual)
    _write_order_log(order_log)

    output = module.generate_phase2_actual_demo_cost_reconciliation(
        root=root,
        actual_trades_csv=actual,
        order_log_csv=order_log,
        output_json=reports / "PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.json",
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    report = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert payload["resolution_status"] == "RESOLVED_FOR_ACTUAL_DEMO_COST_REVIEW"
    assert payload["canonical_phase2_evidence"] is False
    assert payload["phase2_readiness_override"] is False
    assert payload["demo_execution_as_phase2_evidence"] is False
    assert "does not change `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md`" in report
    assert "Cost is no longer treated as the current practical blocker" in report


def _write_actual_trades(path: Path) -> None:
    fields = [
        "entry_time",
        "exit_time",
        "candidate",
        "status",
        "symbol",
        "direction",
        "volume",
        "entry_price",
        "exit_price",
        "sl",
        "tp",
        "state",
        "profit_aed",
        "is_duplicate",
    ]
    rows = []
    for index in range(35):
        rows.append(
            {
                "entry_time": f"2026-06-08 10:{index:02d}:00",
                "exit_time": f"2026-06-08 10:{index:02d}:30",
                "candidate": "breakout_retest",
                "status": "ACCEPTED",
                "symbol": "XAUUSD",
                "direction": "BUY",
                "volume": "0.01",
                "entry_price": "4300.00",
                "exit_price": "4301.00",
                "sl": "4290.00",
                "tp": "4315.00",
                "state": "CLOSED",
                "profit_aed": "10.00" if index < 20 else "-5.00",
                "is_duplicate": "false",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_order_log(path: Path) -> None:
    fields = [
        "timestamp_broker",
        "action",
        "spread_at_order_points",
        "slippage_points",
        "estimated_cost_R",
        "stop_distance_points",
        "order_ticket",
    ]
    rows = [
        {
            "timestamp_broker": "2026.06.08 10:00:00",
            "action": "ORDER_SEND_OK",
            "spread_at_order_points": "50.00",
            "slippage_points": "3.00",
            "estimated_cost_R": "0.0500",
            "stop_distance_points": "1000.00",
            "order_ticket": "1",
        },
        {
            "timestamp_broker": "2026.06.08 10:05:00",
            "action": "GUARD_BLOCK",
            "spread_at_order_points": "75.00",
            "slippage_points": "0.00",
            "estimated_cost_R": "0.1000",
            "stop_distance_points": "750.00",
            "order_ticket": "0",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_actual_demo_cost_reconciliation.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_actual_demo_cost_reconciliation", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_actual_demo_cost_reconciliation"] = module
    spec.loader.exec_module(module)
    return module
