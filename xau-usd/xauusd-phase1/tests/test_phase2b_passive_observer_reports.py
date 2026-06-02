from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2b_reports_are_pending_without_passive_log(tmp_path):
    module = _load_module("generate_phase2b_passive_observer_reports")
    root = tmp_path / "phase1"
    root.mkdir()

    output = module.generate_phase2b_passive_observer_reports(root)

    assert output.status == "PENDING"
    assert output.rows == 0
    report = (root / "outputs" / "reports" / "PHASE2B_COST_FEASIBILITY_REPORT.md").read_text(encoding="utf-8")
    assert "Overall status: PENDING" in report
    assert "does not read experimental demo order logs" in report
    assert "does not authorize canonical Phase 2" in report


def test_phase2b_reports_summarize_passive_cost_rows(tmp_path):
    module = _load_module("generate_phase2b_passive_observer_reports")
    root = tmp_path / "phase1"
    log = root / "outputs" / "paper_observer" / "passive_cost_observer_log.csv"
    log.parent.mkdir(parents=True)
    _write_passive_log(log)

    output = module.generate_phase2b_passive_observer_reports(root)

    assert output.status == "PENDING_SAMPLE"
    assert output.rows == 4
    assert output.unique_events == 4
    cost_report = (root / "outputs" / "reports" / "PHASE2B_COST_FEASIBILITY_REPORT.md").read_text(encoding="utf-8")
    stop_report = (root / "outputs" / "reports" / "PHASE2B_STOP_DISTANCE_SURVIVAL_REPORT.md").read_text(
        encoding="utf-8"
    )
    manifest = json.loads((root / "outputs" / "reports" / "PHASE2B_PASSIVE_OBSERVER_REPORTS.json").read_text())

    assert "COST_OK_ACCEPTABLE" in cost_report
    assert "COST_BLOCK" in cost_report
    assert "250_to_499" in stop_report
    assert "750_plus" in stop_report
    assert manifest["passive_log_only"] is True
    assert manifest["experimental_demo_order_logs_used"] is False
    assert manifest["canonical_phase2_authorized"] is False


def test_phase2b_sample_requirements_doc_exists():
    text = (ROOT / "docs" / "PHASE2B_PASSIVE_OBSERVER_SAMPLE_REQUIREMENTS.md").read_text(encoding="utf-8")

    assert "Active market days" in text
    assert ">= 20" in text
    assert "Unique family events preferred" in text
    assert ">= 300" in text
    assert "Experimental demo order logs as Phase 2 evidence" in text
    assert "Forbidden" in text


def _write_passive_log(path: Path) -> None:
    fieldnames = [
        "timestamp_utc",
        "timestamp_broker",
        "symbol",
        "candidate",
        "candidate_family",
        "candidate_status",
        "would_signal",
        "signal_direction",
        "intended_entry_price",
        "intended_stop_loss",
        "stop_distance_points",
        "spread_points",
        "estimated_total_cost_R",
        "estimated_gross_edge_R",
        "estimated_net_edge_R",
        "cost_gate_status",
        "session_label",
        "hour_utc",
        "tick_fresh",
    ]
    rows = [
        ("2026-06-02T08:00:00Z", "XAUUSD", "breakout_retest_cost_aware_v2", 420, 50, 0.18, 0.50, 0.32, "COST_OK_ACCEPTABLE", "LONDON", "8"),
        ("2026-06-02T09:00:00Z", "XAUUSD", "breakout_retest_cost_aware_v2", 240, 75, 0.35, 0.50, 0.15, "COST_BLOCK", "LONDON", "9"),
        ("2026-06-03T15:00:00Z", "EURUSD", "breakout_retest_cost_aware_v2", 610, 25, 0.10, 0.45, 0.35, "COST_OK_STRONG", "NY", "15"),
        ("2026-06-03T16:00:00Z", "USDJPY", "breakout_retest_cost_aware_v2", 780, 35, 0.14, 0.42, 0.28, "COST_OK_STRONG", "NY", "16"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for timestamp, symbol, candidate, stop, spread, cost, gross, net, gate, session, hour in rows:
            writer.writerow(
                {
                    "timestamp_utc": timestamp,
                    "timestamp_broker": timestamp.replace("T", " ").replace("Z", ""),
                    "symbol": symbol,
                    "candidate": candidate,
                    "candidate_family": "breakout_retest_family",
                    "candidate_status": "PASSIVE_OBSERVER_ONLY",
                    "would_signal": "true",
                    "signal_direction": "BUY",
                    "intended_entry_price": "4500.0",
                    "intended_stop_loss": str(4500.0 - stop / 100),
                    "stop_distance_points": stop,
                    "spread_points": spread,
                    "estimated_total_cost_R": cost,
                    "estimated_gross_edge_R": gross,
                    "estimated_net_edge_R": net,
                    "cost_gate_status": gate,
                    "session_label": session,
                    "hour_utc": hour,
                    "tick_fresh": "true",
                }
            )


def _load_module(name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
