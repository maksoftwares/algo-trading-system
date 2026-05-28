from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def verify_status_dashboard_freshness(repo_root: Path, status_path: Path | None = None) -> list[str]:
    repo_root = repo_root.resolve()
    status_path = (status_path or repo_root / "status.html").resolve()
    phase0_reports = repo_root / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"

    canonical_paths = {
        "phase1_summary": phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        "measured_cost": phase0_reports / "MEASURED_COST_MODEL.md",
        "phase2_demo_countdown": phase1_reports / "PHASE2_DEMO_COUNTDOWN.json",
        "phase2_demo_preflight": phase1_reports / "PHASE2_DEMO_PREFLIGHT.json",
        "phase2_vps_bootstrap": phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json",
        "phase2_readiness": phase1_reports / "PHASE2_READINESS_REPORT.md",
        "phase3_status": phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json",
    }
    errors = [f"missing status dashboard: {status_path}"] if not status_path.exists() else []
    for label, path in canonical_paths.items():
        if not path.exists():
            errors.append(f"missing canonical report {label}: {path}")
    if errors:
        return errors

    actual = status_path.read_text(encoding="utf-8", errors="replace")

    phase1_summary = _read_json(canonical_paths["phase1_summary"])
    phase3_status = _read_json(canonical_paths["phase3_status"])
    phase2_countdown = _read_json(canonical_paths["phase2_demo_countdown"])
    phase2_preflight = _read_json(canonical_paths["phase2_demo_preflight"])
    phase2_bootstrap = _read_json(canonical_paths["phase2_vps_bootstrap"])
    measured_cost = _parse_measured_cost(canonical_paths["measured_cost"])
    phase2_status = _markdown_status(canonical_paths["phase2_readiness"])

    runtime = _mapping(phase1_summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(phase1_summary.get("soak"))
    phase3_cost_modes = _mapping(phase3_status.get("cost_mode_comparison"))
    phase3_paper_shadow = _mapping(phase3_status.get("paper_shadow_experiment"))
    phase3_lifecycle = _mapping(phase3_status.get("shadow_lifecycle_experiment"))
    phase3_guard = _mapping(phase3_status.get("lifecycle_guard_experiment"))
    phase3_rehearsal = _mapping(phase3_status.get("demo_rehearsal"))
    bootstrap_source_status = _mapping(phase2_bootstrap.get("source_status"))
    median_net_by_mode = _mapping(phase3_cost_modes.get("median_net_after_proxy_by_mode"))
    suspend_count_by_mode = _mapping(phase3_cost_modes.get("suspend_family_count_by_mode"))
    core_expectations = {
        "decision row count": runtime.get("decision_rows"),
        "latest bar": latest.get("bar_time"),
        "soak observed days": soak.get("observed_days"),
        "soak progress pct": f"{_to_float(soak.get('progress_pct')):.2f}%" if _to_float(soak.get("progress_pct")) is not None else None,
        "measured cost status": measured_cost.get("status"),
        "measured cost observed rows": measured_cost.get("observed_rows"),
        "measured cost observed days": measured_cost.get("observed_days"),
        "demo countdown status": phase2_countdown.get("status"),
        "demo countdown pending gate count": phase2_countdown.get("pending_gate_count"),
        "demo preflight status": phase2_preflight.get("status"),
        "demo preflight implementation authorization": str(
            phase2_preflight.get("paper_mode_implementation_authorized", "")
        ).lower(),
        "vps bootstrap status": phase2_bootstrap.get("status"),
        "vps bootstrap demo authorization": str(phase2_bootstrap.get("demo_trading_authorized", "")).lower(),
        "vps bootstrap selection status": bootstrap_source_status.get("vps_selection"),
        "vps bootstrap latency status": bootstrap_source_status.get("vps_latency"),
        "vps bootstrap first-day status": bootstrap_source_status.get("vps_first_day_verification"),
        "vps bootstrap owner approval status": bootstrap_source_status.get("project_owner_approval"),
        "demo countdown paper authorization": str(phase2_countdown.get("paper_mode_authorized", "")).lower(),
        "demo countdown broker execution authorization": str(
            phase2_countdown.get("broker_execution_authorized", "")
        ).lower(),
        "demo countdown live trading authorization": str(
            phase2_countdown.get("live_trading_authorized", "")
        ).lower(),
        "phase2 readiness status": phase2_status,
        "phase3 experimental status": phase3_status.get("status"),
        "entry_exit_proxy median net": median_net_by_mode.get("entry_exit_proxy"),
        "p95_fresh_proxy median net": median_net_by_mode.get("p95_fresh_proxy"),
        "stress_2x_p95_proxy median net": median_net_by_mode.get("stress_2x_p95_proxy"),
        "entry_exit_proxy suspend count": suspend_count_by_mode.get("entry_exit_proxy"),
        "p95_fresh_proxy suspend count": suspend_count_by_mode.get("p95_fresh_proxy"),
        "stress_2x_p95_proxy suspend count": suspend_count_by_mode.get("stress_2x_p95_proxy"),
        "paper-shadow status": phase3_paper_shadow.get("status"),
        "paper-shadow would-open count": phase3_paper_shadow.get("would_open_count"),
        "paper-shadow blocked suspend count": phase3_paper_shadow.get("blocked_suspend_count"),
        "shadow lifecycle status": phase3_lifecycle.get("status"),
        "shadow lifecycle synthetic open count": phase3_lifecycle.get("synthetic_open_count"),
        "shadow lifecycle total net R": phase3_lifecycle.get("synthetic_total_net_r"),
        "lifecycle guard status": phase3_guard.get("status"),
        "lifecycle guard open count": phase3_guard.get("guarded_open_count"),
        "lifecycle guard total net R": phase3_guard.get("guarded_total_net_r"),
        "demo rehearsal status": phase3_rehearsal.get("status"),
        "demo rehearsal event count": phase3_rehearsal.get("rehearsal_event_count"),
        "demo rehearsal shadow opens": phase3_rehearsal.get("shadow_open_events"),
        "demo rehearsal blocked events": phase3_rehearsal.get("blocked_events"),
        "demo rehearsal can start real demo": phase3_rehearsal.get("can_start_real_demo"),
    }
    for wait_gate in phase2_countdown.get("wait_gates", []):
        if not isinstance(wait_gate, dict):
            continue
        gate = str(wait_gate.get("gate", ""))
        if gate:
            core_expectations[f"demo wait gate {gate}"] = gate
        if wait_gate.get("remaining") not in {None, ""}:
            core_expectations[f"demo wait gate {gate} remaining"] = wait_gate.get("remaining")
    for phase in phase2_bootstrap.get("bootstrap_phases", []):
        if not isinstance(phase, dict):
            continue
        name = phase.get("phase")
        if name:
            core_expectations[f"vps bootstrap phase {name}"] = name
    for label, value in core_expectations.items():
        if value is None or value == "":
            continue
        text = html.escape(str(value), quote=True)
        if text not in actual:
            errors.append(f"status.html is missing {label}: {value}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _markdown_status(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_measured_cost(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"status": _markdown_status(path)}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|") or "Observed Rows" not in line or "Observed Days" not in line:
            continue
        if index + 2 >= len(lines):
            continue
        headers = [part.strip() for part in line.strip("|").split("|")]
        values = [part.strip() for part in lines[index + 2].strip("|").split("|")]
        row = dict(zip(headers, values))
        result["observed_rows"] = row.get("Observed Rows", "")
        result["observed_days"] = row.get("Observed Days", "")
        result["required_days"] = row.get("Required Days", "")
        break
    return result


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Verify that status.html matches canonical project reports.")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--status-path", type=Path, default=None)
    args = parser.parse_args(argv)
    errors = verify_status_dashboard_freshness(args.repo_root, args.status_path)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Status dashboard freshness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
