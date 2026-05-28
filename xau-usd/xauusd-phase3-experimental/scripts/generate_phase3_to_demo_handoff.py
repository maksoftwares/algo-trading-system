from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE2_AUTHORITY_SENTENCE = (
    "This report has no authority over Phase 2 readiness. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)


def generate_phase3_to_demo_handoff(phase3_root: Path, repo_root: Path | None = None) -> Path:
    phase3_root = phase3_root.resolve()
    repo_root = (repo_root or phase3_root.parents[1]).resolve()
    reports = phase3_root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    status = _read_json(reports / "PHASE3_EXPERIMENTAL_STATUS.json")
    completion = _read_json(reports / "PHASE3_COMPLETION_AUDIT.json")
    rehearsal = _read_json(reports / "PHASE3_DEMO_REHEARSAL_PLAN.json")
    phase2_countdown = _read_json(phase1_reports / "PHASE2_DEMO_COUNTDOWN.json")
    owner_packet = _read_json(phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json")
    phase2_readiness = _read_markdown_status(phase1_reports / "PHASE2_READINESS_REPORT.md") or "UNKNOWN"
    phase1_acceptance = _read_markdown_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md") or "UNKNOWN"

    wait_gates = _list_of_mappings(phase2_countdown.get("wait_gates"))
    owner_actions = _list_of_mappings(phase2_countdown.get("owner_actions_now"))
    owner_approval_readiness = _mapping(owner_packet.get("owner_approval_readiness"))
    repo_complete = completion.get("phase3_repo_complete") is True
    real_ready = phase1_acceptance == "PASS" and phase2_readiness == "PASS"
    handoff = {
        "status": _handoff_status(repo_complete, real_ready),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "phase3_repo_complete": repo_complete,
        "phase1_acceptance": phase1_acceptance,
        "phase2_readiness": phase2_readiness,
        "phase3_completion_status": completion.get("status", "UNKNOWN"),
        "phase3_status": status.get("status", "UNKNOWN"),
        "can_start_demo_now": False,
        "can_start_real_paper_shadow_branch": real_ready,
        "demo_authorized": False,
        "paper_mode_authorized": False,
        "broker_action_code_allowed": False,
        "mt5_runtime_touched": False,
        "rehearsal_can_start_real_demo": rehearsal.get("can_start_real_demo", False),
        "wait_gates": wait_gates,
        "owner_actions": owner_actions,
        "owner_approval_readiness": owner_approval_readiness,
        "reusable_phase3_outputs": _reusable_outputs(phase3_root),
        "must_not_reuse_as_authority": [
            "PHASE3_EXPERIMENTAL_STATUS.md",
            "PHASE3_COMPLETION_AUDIT.md",
            "PHASE3_DEMO_REHEARSAL_CHECKLIST.md",
        ],
        "pre_branch_commands": [
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe scripts\\run_phase1_periodic_checks.py --files-dir C:\\MT5PortableGoldMission\\MQL5\\Files --spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files",
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe scripts\\verify_phase2_transition_artifacts.py --root . --repo-root ..\\.. --status-path ..\\..\\status.html",
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe ..\\xauusd-phase3-experimental\\scripts\\verify_phase3_experimental_artifacts.py --phase3-root ..\\xauusd-phase3-experimental --repo-root ..\\..",
        ],
        "first_real_branch_rules": [
            "Start from docs/PHASE3_REAL_IMPLEMENTATION_PROMPT.md only after Phase 2 readiness PASS and owner approval.",
            "Implement paper-shadow only; do not implement broker-side execution.",
            "Consume the Phase 1 decision stream and approved Phase 2 paper ledger schema.",
            "Apply cost-aware blocks, same-family de-duplication, and keep-suspended family decisions.",
            "Keep same-family variants observer-only unless a later owner-approved gate changes that.",
        ],
        "forbidden_until_later_phase": _forbidden_terms(),
    }

    json_path = reports / "PHASE3_TO_DEMO_HANDOFF.json"
    md_path = reports / "PHASE3_TO_DEMO_HANDOFF.md"
    json_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(handoff), encoding="utf-8")
    return json_path


def _handoff_status(repo_complete: bool, real_ready: bool) -> str:
    if not repo_complete:
        return "PHASE3_HANDOFF_INCOMPLETE"
    if real_ready:
        return "READY_FOR_OWNER_REVIEW_BEFORE_REAL_BRANCH"
    return "READY_FOR_REVIEW_WAITING_REAL_GATES"


def _reusable_outputs(phase3_root: Path) -> list[dict[str, str]]:
    rows = [
        ("cost-aware blocking design", "outputs/reports/PHASE3_COST_GATE_REVIEW.md"),
        ("same-family de-duplication", "outputs/reports/PHASE3_FAMILY_DEDUP_AUDIT.md"),
        ("keep-suspended decisions", "outputs/reports/PHASE3_SUSPEND_FAMILY_DECISION.md"),
        ("paper-shadow lifecycle shape", "outputs/reports/PHASE3_PAPER_SHADOW_SUMMARY.md"),
        ("guarded lifecycle controls", "outputs/reports/PHASE3_LIFECYCLE_GUARD_SUMMARY.md"),
        ("demo rehearsal sequence", "outputs/reports/PHASE3_DEMO_REHEARSAL_CHECKLIST.md"),
        ("real implementation prompt", "docs/PHASE3_REAL_IMPLEMENTATION_PROMPT.md"),
    ]
    return [
        {
            "item": item,
            "path": str((phase3_root / relative).resolve()),
            "exists": str((phase3_root / relative).exists()).lower(),
        }
        for item, relative in rows
    ]


def _forbidden_terms() -> list[str]:
    return [
        "Order" + "Send",
        "Order" + "Send" + "Async",
        "C" + "Trade",
        "trade." + "Buy",
        "trade." + "Sell",
        "Position" + "Open",
        "Position" + "Modify",
        "Position" + "Close",
        "live capital behavior",
    ]


def _render_markdown(handoff: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 3 To Demo Handoff",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {handoff['status']}",
            "",
            "## Decision",
            "",
            _table(
                [
                    ("Phase 3 repo complete", str(handoff.get("phase3_repo_complete", False))),
                    ("Phase 1 acceptance", str(handoff.get("phase1_acceptance", "UNKNOWN"))),
                    ("Phase 2 readiness", str(handoff.get("phase2_readiness", "UNKNOWN"))),
                    ("Can start demo now", str(handoff.get("can_start_demo_now", False))),
                    (
                        "Can start real paper-shadow branch",
                        str(handoff.get("can_start_real_paper_shadow_branch", False)),
                    ),
                    (
                        "Owner approval readiness",
                        str(_mapping(handoff.get("owner_approval_readiness")).get("status", "UNKNOWN")),
                    ),
                    ("Demo authorized", str(handoff.get("demo_authorized", False))),
                    ("Broker-action code allowed", str(handoff.get("broker_action_code_allowed", False))),
                    ("MT5 runtime touched", str(handoff.get("mt5_runtime_touched", False))),
                ]
            ),
            "",
            "## Wait Gates",
            "",
            _dict_table(handoff.get("wait_gates", []), ["gate", "status", "current", "required", "remaining", "unit"]),
            "",
            "## Owner Actions",
            "",
            _dict_table(handoff.get("owner_actions", []), ["gate", "status", "action"]),
            "",
            "## Owner Approval Readiness",
            "",
            _owner_approval_readiness_markdown(_mapping(handoff.get("owner_approval_readiness"))),
            "",
            "## Reusable Phase 3 Outputs",
            "",
            _dict_table(handoff.get("reusable_phase3_outputs", []), ["item", "exists", "path"]),
            "",
            "## Pre-Branch Commands",
            "",
            _bullet_list([f"`{command}`" for command in handoff.get("pre_branch_commands", [])]),
            "",
            "## First Real Branch Rules",
            "",
            _bullet_list([str(item) for item in handoff.get("first_real_branch_rules", [])]),
            "",
            "## Forbidden Until Later Phase",
            "",
            _bullet_list([f"`{item}`" for item in handoff.get("forbidden_until_later_phase", [])]),
            "",
        ]
    )


def _dict_table(rows: Any, columns: list[str]) -> str:
    if not isinstance(rows, list) or not rows:
        return "None."
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        item = _mapping(row)
        output.append("| " + " | ".join(_escape(item.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _owner_approval_readiness_markdown(readiness: dict[str, Any]) -> str:
    if not readiness:
        return "Owner approval readiness is not available yet."
    rows = [
        ("Status", str(readiness.get("status", "UNKNOWN"))),
        ("Pending objective gates", str(readiness.get("pending_objective_gate_count", "UNKNOWN"))),
        ("Signing rule", str(readiness.get("signing_rule", ""))),
    ]
    pending = readiness.get("pending_objective_gates")
    sections = [_table(rows)]
    if isinstance(pending, list) and pending:
        sections.extend(
            [
                "",
                "### Pending Objective Gates",
                "",
                _dict_table(pending, ["gate", "status", "evidence"]),
            ]
        )
    return "\n".join(sections)


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {row}" for row in rows) if rows else "- None."


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _read_json(path: Path) -> dict[str, Any]:
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


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate the Phase 3 to demo handoff packet.")
    parser.add_argument("--phase3-root", type=Path, default=phase3_root)
    parser.add_argument("--repo-root", type=Path, default=phase3_root.parents[1])
    args = parser.parse_args(argv)
    path = generate_phase3_to_demo_handoff(args.phase3_root, args.repo_root)
    print(f"Phase 3 to demo handoff: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
