from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase3_simulation_filters_unsafe_rows(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")
    input_csv = tmp_path / "would.csv"
    _write_would_signal_csv(input_csv)

    output = module.simulate_phase3_from_would_signals(input_csv, tmp_path / "reports")

    assert output.status == "EXPERIMENTAL_ACTIVE"
    assert output.accepted_events == 1
    assert output.rejected_source_rows == 2
    with output.ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["source_dry_run"] == "true"
    assert rows[0]["source_trade_permission"] == "false"
    assert rows[0]["experimental_state"] == "EXPERIMENT_ONLY"


def test_phase3_status_preserves_real_phase2_pending(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    input_csv = tmp_path / "would.csv"
    _write_would_signal_csv(input_csv)
    simulator.simulate_phase3_from_would_signals(input_csv, phase3 / "outputs" / "reports")
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "latest_row": {
                        "bar_time": "2026.05.27 19:20:00",
                        "run_id": "phase1-dry-run-v0.7",
                        "dry_run": "true",
                        "trade_permission": "false",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "EXPERIMENTAL_ACTIVE"
    assert status["real_phase2_readiness"] == "PENDING"
    assert status["authorized_for_deployment"] is False
    assert status["mt5_runtime_touched"] is False


def test_phase3_safety_audit_passes():
    module = _load_script("audit_phase3_experimental_safety")

    findings = module.audit_phase3_tree(ROOT)

    assert findings == []


def _load_script(name: str):
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


def _write_would_signal_csv(path: Path) -> None:
    fieldnames = [
        "cluster_id",
        "observer",
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "bar_time",
        "run_id",
        "symbol",
        "direction",
        "level_kind",
        "level_price",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
        "spread_points",
        "risk_state",
        "execution_state",
        "server_time_status",
        "reason_code",
        "trade_permission",
        "dry_run",
    ]
    rows = [
        _row("WS001"),
        _row("WS002", dry_run="false"),
        _row("WS003", trade_permission="true"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row(cluster_id: str, dry_run: str = "true", trade_permission: str = "false") -> dict[str, str]:
    return {
        "cluster_id": cluster_id,
        "observer": "breakout_retest",
        "timestamp_broker": "2026.05.27 12:00:00",
        "timestamp_utc": "2026.05.27 08:00:00",
        "timestamp_local": "2026.05.27 17:30:00",
        "bar_time": "2026.05.27 12:00:00",
        "run_id": "phase1-dry-run-v0.7",
        "symbol": "XAUUSD",
        "direction": "LONG",
        "level_kind": "latest_swing_high",
        "level_price": "4500.00",
        "entry_price": "4502.00",
        "stop_loss": "4497.00",
        "take_profit": "4509.50",
        "stop_distance_points": "500.00",
        "spread_points": "50.00",
        "risk_state": "NORMAL",
        "execution_state": "EXECUTION_OK",
        "server_time_status": "CLOCK_OK",
        "reason_code": "DRY_RUN_SIGNAL",
        "trade_permission": trade_permission,
        "dry_run": dry_run,
    }
