from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_demo_countdown_tracks_wait_gates_and_owner_actions(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    report_dir.mkdir(parents=True)
    phase0_reports.mkdir(parents=True)
    _write_readiness(report_dir / "PHASE2_READINESS_REPORT.md")
    _write_status(report_dir / "PHASE1_ACCEPTANCE_REPORT.md", "PENDING")
    _write_summary(report_dir / "PHASE1_STATUS_SUMMARY.json")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_status(phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md", "PENDING")
    _write_status(phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md", "PENDING")

    output = module.generate_phase2_demo_countdown_report(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "DEMO_NOT_READY"
    assert output.pending_gate_count == 5
    assert payload["paper_mode_authorized"] is False
    assert payload["broker_execution_authorized"] is False
    assert payload["live_trading_authorized"] is False
    assert any(item["gate"] == "Active-market 72-hour soak" and item["remaining"] == 46.58 for item in payload["wait_gates"])
    assert any(item["gate"] == "Process/code-freeze 96-hour gate" and item["remaining"] == 69.46 for item in payload["wait_gates"])
    assert any(item["gate"] == "Measured cost model" and item["remaining"] == 3.0 for item in payload["wait_gates"])
    assert any(item["gate"] == "VPS selection" for item in payload["owner_actions_now"])
    assert "This report is a countdown aid only" in markdown
    assert "Paper mode authorized" in markdown
    assert "false" in markdown


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_demo_countdown_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_demo_countdown_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_demo_countdown_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _write_readiness(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 2 Readiness Report",
                "",
                "Overall status: PENDING",
                "",
                "## Gates",
                "",
                "| Gate | Status | Evidence |",
                "| --- | --- | --- |",
                "| Phase 2 preparation spec | PASS | complete |",
                "| VPS selection | PENDING | owner decision required |",
                "| Measured cost model | PENDING | two fresh days observed |",
                "| Active-market 72-hour soak | PENDING | waiting |",
                "| Process/code-freeze 96-hour gate | PENDING | waiting |",
                "| Project owner approval | PENDING | approval not signed |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_summary(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "runtime": {
                    "decision_rows": 1040,
                    "latest_row": {
                        "bar_time": "2026.05.28 13:10:00",
                        "dry_run": "true",
                        "trade_permission": "false",
                        "server_time_status": "CLOCK_OK",
                    },
                },
                "soak": {
                    "current_streak_hours": 25.42,
                    "required_uninterrupted_streak_hours": 72.0,
                    "code_freeze_hours": 26.54,
                    "required_code_freeze_hours": 96.0,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_measured_cost(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Measured Cost Model",
                "",
                "Overall status: PENDING",
                "",
                "## Coverage",
                "",
                "| Observed Rows | Required Rows | Observed Days | Required Days |",
                "| --- | --- | --- | --- |",
                "| 25858 | 500 | 2 | 5 |",
                "",
            ]
        ),
        encoding="utf-8",
    )
