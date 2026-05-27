from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def generate_phase3_experimental_status(phase3_root: Path, repo_root: Path | None = None) -> Path:
    phase3_root = phase3_root.resolve()
    repo_root = (repo_root or phase3_root.parents[1]).resolve()
    reports = phase3_root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    simulation = _read_json(reports / "PHASE3_EXPERIMENTAL_SIMULATION.json")
    phase1_summary = _read_json(repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_STATUS_SUMMARY.json")
    phase2_readiness = _read_markdown_status(
        repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    )
    phase1_acceptance = _read_markdown_status(
        repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_ACCEPTANCE_REPORT.md"
    )
    latest = _mapping(_mapping(phase1_summary.get("runtime")).get("latest_row"))
    status = {
        "status": "EXPERIMENTAL_ACTIVE",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": "repo_only_no_mt5_deployment_no_phase2_status_change",
        "real_phase1_acceptance": phase1_acceptance or "UNKNOWN",
        "real_phase2_readiness": phase2_readiness or "UNKNOWN",
        "assumption": "assumes_phase2_pass_for_design_only",
        "authorized_for_deployment": False,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "latest_phase1_bar": latest.get("bar_time", ""),
        "latest_phase1_run_id": latest.get("run_id", ""),
        "latest_phase1_dry_run": latest.get("dry_run", ""),
        "latest_phase1_trade_permission": latest.get("trade_permission", ""),
        "simulation": simulation,
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
    return "\n".join(
        [
            "# Phase 3 Experimental Status",
            "",
            f"Overall status: {status['status']}",
            "",
            "## Boundary",
            "",
            "- Real Phase 2 remains governed by `PHASE2_READINESS_REPORT.md`.",
            "- This sandbox assumes Phase 2 PASS for design only.",
            "- MT5 runtime was not touched.",
            "- Broker-action code is not allowed.",
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
                    ("Rejected source rows", str(simulation.get("rejected_source_rows", "0"))),
                    ("Median proxy cost R", str(simulation.get("median_proxy_cost_r", "n/a"))),
                    ("Median net after proxy cost R", str(simulation.get("median_net_after_proxy_cost_r", "n/a"))),
                    ("Minimum net expectancy R", str(simulation.get("minimum_net_expectancy_r", "n/a"))),
                ]
            ),
            "",
        ]
    )


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
