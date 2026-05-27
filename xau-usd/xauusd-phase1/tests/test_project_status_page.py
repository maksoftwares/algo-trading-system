from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_status_page_renders_milestones_and_candidates(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    phase0_reports = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase0_matrix = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "matrix_results"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    _write_phase1_summary(phase1_reports / "PHASE1_STATUS_SUMMARY.json")
    _write_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md", "PENDING")
    _write_status(phase1_reports / "PHASE2_READINESS_REPORT.md", "PENDING")
    (phase0_reports / "PHASE0_VERDICT.md").write_text(
        "| breakout_retest | PASS | PASS | PASS | PASS | PASS | PASS |\n",
        encoding="utf-8",
    )
    _write_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    _write_trade_ledger(
        phase0_matrix / "breakout_retest" / "cell_3_breakout_retest_capital_com_p95_trades.csv",
        [
            ("2024-01-03 10:00:00+00:00", 1.5),
            ("2024-01-07 10:00:00+00:00", -1.0),
            ("2024-02-03 10:00:00+00:00", 0.5),
        ],
    )
    _write_trade_ledger(
        phase0_matrix / "trend_pullback" / "cell_3_trend_pullback_capital_com_p95_trades.csv",
        [("2024-01-04 10:00:00+00:00", -1.0)],
    )

    output = module.generate_project_status_page(repo)

    html = output.output_path.read_text(encoding="utf-8")
    assert output.candidate_count == 2
    assert output.accepted_count == 1
    assert output.rejected_count == 1
    assert "Mission Control" in html
    assert "breakout_retest" in html
    assert "trend_pullback" in html
    assert "Five-day soak" in html
    assert "candidateSearch" in html
    assert "Cost edge consumption" in html
    assert "Cost viability map" in html
    assert "$1,000 Account Example" in html
    assert "1% fixed risk per trade" in html
    assert "data-account-status-filter=\"accepted\"" in html
    assert "data-account-status-filter=\"rejected\"" in html
    assert 'data-account-row data-status="accepted"' in html
    assert 'data-account-row data-status="rejected"' in html
    assert "Monthly Returns Ledger" in html
    assert "th.status-col, td.status-col" in html
    assert '<th class="status-col">Status</th>' in html
    assert '<td class="status-col"><span class="pill pass">ACCEPTED</span></td>' in html
    assert "<th class=\"num\">Trades</th>" in html
    assert "<th class=\"num\">Win Rate</th>" in html
    assert "<th class=\"num\">Wins</th>" in html
    assert "<th class=\"num\">Losses</th>" in html
    assert "<th class=\"num\">Net R</th>" in html
    assert "<th class=\"num\">Avg R</th>" in html
    assert "<th class=\"num\">Total PnL</th>" in html
    assert "monthlySearch" in html
    assert "monthlyExpertFilter" in html
    assert "monthlyStatusFilter" in html
    assert html.index("monthlyStatusFilter") < html.index("monthlyExpertFilter")
    assert '<option value="all">All classifications</option>' in html
    assert '<option value="accepted">Accepted EAs</option>' in html
    assert '<option value="pending">Provisional EAs</option>' in html
    assert '<option value="rejected">Rejected EAs</option>' in html
    assert '<option value="breakout_retest" data-status="accepted">breakout_retest (ACCEPTED)</option>' in html
    assert '<option value="trend_pullback" data-status="rejected">trend_pullback (REJECTED)</option>' in html
    assert "monthlyExpertOptions" in html
    assert "updateMonthlyExpertOptions" in html
    assert 'data-expert="breakout_retest"' in html
    assert 'data-status="accepted"' in html
    assert 'data-status="rejected"' in html
    assert "66.67%" in html
    assert "+0.50R" in html
    assert "+0.25R" in html
    assert "+$10.00" in html


def test_project_status_page_keeps_five_day_soak_pending_when_phase1_acceptance_fails(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    phase0_reports = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase0_matrix = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "matrix_results"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    _write_phase1_summary(
        phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        acceptance="FAIL",
        soak={"progress_pct": 90.0, "observed_days": 4.5, "required_days": 5},
    )
    _write_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md", "FAIL")
    _write_status(phase1_reports / "PHASE2_READINESS_REPORT.md", "FAIL")
    (phase0_reports / "PHASE0_VERDICT.md").write_text(
        "| breakout_retest | PASS | PASS | PASS | PASS | PASS | PASS |\n",
        encoding="utf-8",
    )
    _write_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    _write_trade_ledger(
        phase0_matrix / "breakout_retest" / "cell_3_breakout_retest_capital_com_p95_trades.csv",
        [("2024-01-03 10:00:00+00:00", 1.5)],
    )

    output = module.generate_project_status_page(repo)

    html = output.output_path.read_text(encoding="utf-8")
    assert '<div class="name">Five-day soak</div>' in html
    assert "Wall-clock evidence accumulating: 4.5 of 5 trading days (90%)" in html
    assert '<span class="pill pending">PENDING</span>' in html


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_project_status_page.py"
    spec = importlib.util.spec_from_file_location("generate_project_status_page", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_project_status_page"] = module
    spec.loader.exec_module(module)
    return module


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _write_phase1_summary(
    path: Path,
    acceptance: str = "PENDING",
    soak: dict[str, float] | None = None,
) -> None:
    soak = soak or {"progress_pct": 8.26, "observed_days": 0.4132, "required_days": 5}
    path.write_text(
        json.dumps(
            {
                "status": {
                    "acceptance": acceptance,
                    "log_verification": "PASS",
                    "runtime_health": "PASS",
                    "soak_analysis": "PASS",
                    "would_signal": "PASS",
                },
                "runtime": {
                    "decision_rows": 56,
                    "latest_row": {
                        "bar_time": "2026.05.22 20:55:00",
                        "dry_run": "true",
                        "trade_permission": "false",
                        "server_time_status": "CLOCK_OK",
                        "risk_state": "NORMAL",
                        "block_reason": "phase1_dry_run_only",
                    },
                },
                "soak": soak,
                "would_signal": {"rows": 10, "clusters": 10},
            }
        ),
        encoding="utf-8",
    )


def _write_fixed_notional(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Fixed",
                "",
                "Overall status: PASS",
                "",
                "| Cell | Broker | Cost | Trades | Win % | PF | Avg R | Gross R | Cost R | Net R | Cost % | Flag |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| ALL | ALL | ALL | 66759 | 48.22 | 1.3625 | 0.1888 | 0.5115 | 0.3228 | 0.1888 | 63.0938 | ORANGE |",
            ]
        ),
        encoding="utf-8",
    )


def _write_measured_cost(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Measured Cost",
                "",
                "Overall status: PENDING",
                "",
                "| Observed Rows | Required Rows | Observed Days | Required Days | Source Files |",
                "| --- | --- | --- | --- | --- |",
                "| 5759 | 500 | 2 | 5 | 2 |",
            ]
        ),
        encoding="utf-8",
    )


def _write_candidate_audit(path: Path) -> None:
    fieldnames = [
        "candidate",
        "decision_scope",
        "frequency_bias_diagnosis",
        "complete_cells",
        "pf_passing_cells",
        "total_trades",
        "median_cell_trades",
        "failed_gates",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "candidate": "breakout_retest",
                "decision_scope": "APPROVED_OR_ACTIVE",
                "frequency_bias_diagnosis": "APPROVED_EDGE_FAMILY",
                "complete_cells": "9",
                "pf_passing_cells": "7",
                "total_trades": "66759",
                "median_cell_trades": "7287",
                "failed_gates": "none",
            }
        )
        writer.writerow(
            {
                "candidate": "trend_pullback",
                "decision_scope": "REJECTED_OR_RESEARCH",
                "frequency_bias_diagnosis": "EDGE_EXPECTANCY_FAILURE",
                "complete_cells": "9",
                "pf_passing_cells": "0",
                "total_trades": "27576",
                "median_cell_trades": "3039",
                "failed_gates": "multi_cell_survival;concentration",
            }
        )


def _write_trade_ledger(path: Path, rows: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["expert", "exit_time_utc", "r_multiple"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for exit_time, r_multiple in rows:
            writer.writerow({"expert": path.parent.name, "exit_time_utc": exit_time, "r_multiple": r_multiple})
