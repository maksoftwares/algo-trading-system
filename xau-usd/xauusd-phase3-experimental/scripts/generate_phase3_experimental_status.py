from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PHASE2_AUTHORITY_SENTENCE = (
    "This report has no authority over Phase 2 readiness. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)


def generate_phase3_experimental_status(phase3_root: Path, repo_root: Path | None = None) -> Path:
    phase3_root = phase3_root.resolve()
    repo_root = (repo_root or phase3_root.parents[1]).resolve()
    reports = phase3_root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    simulation = _read_json(reports / "PHASE3_EXPERIMENTAL_SIMULATION.json")
    safety = _read_json(reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json")
    manifest = _read_json(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json")
    suspend_family = _read_json(reports / "PHASE3_SUSPEND_FAMILY_REVIEW.json")
    phase1_summary = _read_json(repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_STATUS_SUMMARY.json")
    phase2_readiness = _read_markdown_status(
        repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    )
    phase1_acceptance = _read_markdown_status(
        repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_ACCEPTANCE_REPORT.md"
    )
    latest = _mapping(_mapping(phase1_summary.get("runtime")).get("latest_row"))
    status_label = _phase3_status(simulation, safety)
    status = {
        "status": status_label,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": "repo_only_no_mt5_deployment_no_phase2_status_change",
        "real_phase1_acceptance": phase1_acceptance or "UNKNOWN",
        "real_phase2_readiness": phase2_readiness or "UNKNOWN",
        "assumption": "assumes_phase2_pass_for_design_only",
        "authorized_for_deployment": False,
        "owner_approval_flow": "excluded_from_real_phase2_phase3_approval_flow",
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "latest_phase1_bar": latest.get("bar_time", ""),
        "latest_phase1_run_id": latest.get("run_id", ""),
        "latest_phase1_dry_run": latest.get("dry_run", ""),
        "latest_phase1_trade_permission": latest.get("trade_permission", ""),
        "simulation": simulation,
        "safety": safety,
        "suspend_family_review": suspend_family,
        "manifest": _manifest_summary(manifest),
        "known_state_strings": [
            "EXPERIMENTAL_ACTIVE",
            "EXPERIMENTAL_WAITING_FOR_PHASE2",
            "EXPERIMENTAL_COST_SUSPEND_SCENARIO",
            "EXPERIMENTAL_BOUNDARY_FAIL",
            "EXPERIMENTAL_REVIEW_READY",
            "EXPERIMENTAL_ARCHIVED",
        ],
        "docs": [
            "docs/PHASE3_EXPERIMENTAL_SCOPE.md",
            "docs/PHASE3_EXECUTION_READINESS_DESIGN.md",
        ],
    }
    json_path = reports / "PHASE3_EXPERIMENTAL_STATUS.json"
    md_path = reports / "PHASE3_EXPERIMENTAL_STATUS.md"
    json_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(status), encoding="utf-8")
    return json_path


def _render_markdown(status: dict[str, object]) -> str:
    simulation = _mapping(status.get("simulation"))
    safety = _mapping(status.get("safety"))
    suspend_family = _mapping(status.get("suspend_family_review"))
    manifest = _mapping(status.get("manifest"))
    return "\n".join(
        [
            "# Phase 3 Experimental Status",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {status['status']}",
            "",
            "## Boundary",
            "",
            "- Real Phase 2 remains governed by `PHASE2_READINESS_REPORT.md`.",
            "- This sandbox assumes Phase 2 PASS for design only.",
            "- MT5 runtime was not touched.",
            "- Broker-action code is not allowed.",
            "- This experiment is excluded from the owner approval flow for real Phase 2 or real Phase 3.",
            "",
            "## Current Real Gate State",
            "",
            _table(
                [
                    ("Phase 1 acceptance", str(status.get("real_phase1_acceptance", "UNKNOWN"))),
                    ("Phase 2 readiness", str(status.get("real_phase2_readiness", "UNKNOWN"))),
                    ("Latest Phase 1 bar", str(status.get("latest_phase1_bar", ""))),
                    ("Latest Phase 1 dry run", str(status.get("latest_phase1_dry_run", ""))),
                    ("Latest Phase 1 trade permission", str(status.get("latest_phase1_trade_permission", ""))),
                ]
            ),
            "",
            "## Experimental Simulation",
            "",
            _table(
                [
                    ("Accepted events", str(simulation.get("accepted_events", "0"))),
                    ("Raw observer events", str(simulation.get("raw_observer_event_count", "0"))),
                    ("Family unique events", str(simulation.get("family_unique_event_count", "0"))),
                    ("Observer duplicates", str(simulation.get("observer_duplicate_count", "0"))),
                    ("Observer conflicts", str(simulation.get("observer_conflict_count", "0"))),
                    ("Rejected source rows", str(simulation.get("rejected_source_rows", "0"))),
                    ("Cost mode", str(simulation.get("cost_mode", "n/a"))),
                    ("Median proxy cost R", str(simulation.get("median_proxy_cost_r", "n/a"))),
                    ("Median net after proxy cost R", str(simulation.get("median_net_after_proxy_cost_r", "n/a"))),
                    ("Minimum net expectancy R", str(simulation.get("minimum_net_expectancy_r", "n/a"))),
                ]
            ),
            "",
            "## Safety And Manifest",
            "",
            _table(
                [
                    ("Safety status", str(safety.get("status", "UNKNOWN"))),
                    ("Safety findings", str(safety.get("findings_count", "UNKNOWN"))),
                    ("Suspend review status", str(suspend_family.get("status", "UNKNOWN"))),
                    ("Suspend unique family events", str(suspend_family.get("suspend_unique_family_events", "UNKNOWN"))),
                    ("Suspend primary rows", str(suspend_family.get("suspend_primary_rows", "UNKNOWN"))),
                    ("Manifest status", str(manifest.get("status", "UNKNOWN"))),
                    ("Manifest commit", str(manifest.get("commit_short", "UNKNOWN"))),
                ]
            ),
            "",
        ]
    )


def _phase3_status(simulation: dict[str, object], safety: dict[str, object]) -> str:
    if safety and safety.get("status") != "PASS":
        return "EXPERIMENTAL_BOUNDARY_FAIL"
    if not simulation:
        return "EXPERIMENTAL_WAITING_FOR_PHASE2"
    simulation_status = str(simulation.get("status") or "")
    if simulation_status == "EXPERIMENTAL_COST_SUSPEND_SCENARIO":
        return simulation_status
    return "EXPERIMENTAL_ACTIVE"


def _manifest_summary(manifest: dict[str, object]) -> dict[str, object]:
    if not manifest:
        return {}
    return {
        "status": manifest.get("status", "UNKNOWN"),
        "commit_short": manifest.get("commit_short", ""),
        "created_at_utc": manifest.get("created_at_utc", ""),
    }


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {key} | {value} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate Phase 3 experimental status.")
    parser.add_argument("--phase3-root", type=Path, default=phase3_root)
    parser.add_argument("--repo-root", type=Path, default=phase3_root.parents[1])
    args = parser.parse_args(argv)
    path = generate_phase3_experimental_status(args.phase3_root, args.repo_root)
    print(f"Phase 3 experimental status: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
