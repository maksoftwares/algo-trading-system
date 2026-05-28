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


PHASE3_REPO_REQUIREMENTS = (
    ("scope_doc", "Experimental scope defines allowed work and hard boundaries."),
    ("freeze_doc", "Experimental freeze note blocks new feature expansion until real gates pass or owner opens a new ticket."),
    ("simulation", "Offline ledger/simulation exists from Phase 1 would-signal evidence."),
    ("safety", "Phase 3 source safety audit passes with no broker-action findings."),
    ("family_dedup", "Family de-duplication/observer conflict audit is generated."),
    ("cost_modes", "Cost-mode comparison is generated."),
    ("cost_gates", "Cost-in-R gate review is generated."),
    ("suspend_review", "Suspend-family review is generated."),
    ("suspend_decision", "Primary suspended family rows have explicit keep-suspended decisions."),
    ("paper_shadow", "Paper-shadow side-experiment ledger and summary are generated without demo authorization."),
    ("shadow_lifecycle", "Synthetic shadow lifecycle ledger and summary are generated without demo authorization."),
    ("lifecycle_guard", "Guarded lifecycle controller comparison is generated without demo authorization."),
    ("demo_rehearsal", "Demo rehearsal checklist and ledger are generated without demo authorization."),
    ("demo_handoff", "Phase 3 to demo handoff is generated without demo authorization."),
    ("promotion_rollback", "Promotion and rollback criteria are documented."),
    ("observer_conflict_playbook", "Observer conflict playbook is documented."),
    ("future_prompt", "Future real-implementation prompt is documented."),
    ("review_bundle", "Portable review bundle exists."),
    ("manifest", "Phase 3 manifest exists and records the current review/worktree state."),
    ("dashboard", "Root status dashboard is updated from Phase 3 status."),
)


def generate_phase3_completion_audit(phase3_root: Path, repo_root: Path | None = None) -> Path:
    phase3_root = phase3_root.resolve()
    repo_root = (repo_root or phase3_root.parents[1]).resolve()
    reports = phase3_root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    status = _read_json(reports / "PHASE3_EXPERIMENTAL_STATUS.json")
    manifest = _read_json(reports / "PHASE3_EXPERIMENTAL_MANIFEST.json")
    safety = _read_json(reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json")
    phase2_report = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    phase1_report = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_ACCEPTANCE_REPORT.md"
    phase2_countdown = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_DEMO_COUNTDOWN.json"

    evidence_paths = _evidence_paths(phase3_root, repo_root)
    requirement_rows = [
        _requirement_row(key, label, evidence_paths.get(key), status, manifest, safety)
        for key, label in PHASE3_REPO_REQUIREMENTS
    ]
    release_clean = all(row["status"] == "PASS" for row in requirement_rows)
    repo_complete = all(row["status"] in {"PASS", "WARN"} for row in requirement_rows)
    phase1_status = _read_markdown_status(phase1_report) or "UNKNOWN"
    phase2_status = _read_markdown_status(phase2_report) or "UNKNOWN"
    countdown = _read_json(phase2_countdown)
    external_blockers = _phase2_pending_gates(phase2_report, countdown) if phase2_status != "PASS" else []
    demo_authorized = release_clean and phase1_status == "PASS" and phase2_status == "PASS" and not external_blockers
    if release_clean and not demo_authorized:
        overall_status = "REPO_SIDE_COMPLETE_WAITING_REAL_GATES"
    elif repo_complete and not release_clean:
        overall_status = "REPO_SIDE_COMPLETE_WITH_WARNINGS_WAITING_REAL_GATES"
    else:
        overall_status = "PENDING"
    audit = {
        "status": overall_status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": "repo_only_no_mt5_deployment_no_phase2_status_change",
        "phase3_repo_complete": repo_complete,
        "phase3_release_clean": release_clean,
        "demo_authorized": demo_authorized,
        "real_phase1_acceptance": phase1_status,
        "real_phase2_readiness": phase2_status,
        "repo_requirement_rows": requirement_rows,
        "remaining_phase3_repo_items": [row for row in requirement_rows if row["status"] != "PASS"],
        "external_blockers": external_blockers,
        "next_when_real_gates_pass": [
            "Use PHASE3_REAL_IMPLEMENTATION_PROMPT.md as the starting prompt.",
            "Keep the first real reuse paper-shadow only.",
            "Carry forward cost-aware blocking, family de-duplication, and keep-suspended decisions.",
            "Do not add broker-action code until a separate owner-approved implementation phase allows it.",
        ],
    }

    json_path = reports / "PHASE3_COMPLETION_AUDIT.json"
    md_path = reports / "PHASE3_COMPLETION_AUDIT.md"
    json_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(audit), encoding="utf-8")
    return json_path


def _evidence_paths(phase3_root: Path, repo_root: Path) -> dict[str, Path]:
    reports = phase3_root / "outputs" / "reports"
    return {
        "scope_doc": phase3_root / "docs" / "PHASE3_EXPERIMENTAL_SCOPE.md",
        "freeze_doc": phase3_root / "docs" / "PHASE3_EXPERIMENTAL_FREEZE.md",
        "simulation": reports / "PHASE3_EXPERIMENTAL_SIMULATION.md",
        "safety": reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md",
        "family_dedup": reports / "PHASE3_FAMILY_DEDUP_AUDIT.md",
        "cost_modes": reports / "PHASE3_COST_MODE_COMPARISON.md",
        "cost_gates": reports / "PHASE3_COST_GATE_REVIEW.md",
        "suspend_review": reports / "PHASE3_SUSPEND_FAMILY_REVIEW.md",
        "suspend_decision": reports / "PHASE3_SUSPEND_FAMILY_DECISION.md",
        "paper_shadow": reports / "PHASE3_PAPER_SHADOW_SUMMARY.md",
        "shadow_lifecycle": reports / "PHASE3_SHADOW_LIFECYCLE_SUMMARY.md",
        "lifecycle_guard": reports / "PHASE3_LIFECYCLE_GUARD_SUMMARY.md",
        "demo_rehearsal": reports / "PHASE3_DEMO_REHEARSAL_CHECKLIST.md",
        "demo_handoff": reports / "PHASE3_TO_DEMO_HANDOFF.md",
        "promotion_rollback": phase3_root / "docs" / "PHASE3_PROMOTION_ROLLBACK_CRITERIA.md",
        "observer_conflict_playbook": phase3_root / "docs" / "PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md",
        "future_prompt": phase3_root / "docs" / "PHASE3_REAL_IMPLEMENTATION_PROMPT.md",
        "review_bundle": phase3_root / "outputs" / "review_bundles" / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip",
        "manifest": reports / "PHASE3_EXPERIMENTAL_MANIFEST.md",
        "dashboard": repo_root / "status.html",
    }


def _requirement_row(
    key: str,
    label: str,
    path: Path | None,
    status: dict[str, Any],
    manifest: dict[str, Any],
    safety: dict[str, Any],
) -> dict[str, str]:
    evidence = path.resolve() if path else None
    exists = bool(evidence and evidence.exists())
    gate_ok = exists
    detail = "evidence exists"
    if key == "safety":
        gate_ok = gate_ok and safety.get("status") == "PASS" and safety.get("findings_count") == 0
        detail = f"safety={safety.get('status', 'UNKNOWN')}; findings={safety.get('findings_count', 'UNKNOWN')}"
    elif key == "manifest":
        manifest_status = str(manifest.get("status", "UNKNOWN"))
        manifest_clean = manifest.get("working_tree_clean")
        if not gate_ok:
            row_status = "PENDING"
        elif manifest_status == "PASS" and manifest_clean is True:
            row_status = "PASS"
        elif manifest_status == "DIRTY_WORKTREE" or manifest_clean is False:
            row_status = "WARN"
        else:
            row_status = "PENDING"
        detail = f"manifest={manifest_status}; clean={manifest_clean}"
        return {
            "key": key,
            "requirement": label,
            "status": row_status,
            "evidence": str(evidence) if evidence else "",
            "detail": detail if exists else "missing evidence",
        }
    elif key == "suspend_decision":
        decision = _mapping(status.get("suspend_family_decision"))
        gate_ok = gate_ok and decision.get("status") == "REVIEW_READY_KEEP_SUSPENDED"
        detail = f"decision={decision.get('status', 'UNKNOWN')}; keep_suspended={decision.get('keep_suspended_primary_rows', 'UNKNOWN')}"
    elif key == "family_dedup":
        audit = _mapping(status.get("family_dedup_audit"))
        gate_ok = gate_ok and audit.get("status") == "REVIEW_READY"
        detail = f"audit={audit.get('status', 'UNKNOWN')}; conflicts={_mapping(status.get('simulation')).get('observer_conflict_count', 'UNKNOWN')}"
    elif key == "cost_modes":
        comparison = _mapping(status.get("cost_mode_comparison"))
        gate_ok = gate_ok and comparison.get("status") == "REVIEW_READY"
        detail = f"comparison={comparison.get('status', 'UNKNOWN')}; modes={comparison.get('mode_count', 'UNKNOWN')}"
    elif key == "cost_gates":
        review = _mapping(status.get("cost_gate_review"))
        gate_ok = gate_ok and review.get("status") == "REVIEW_READY"
        detail = f"review={review.get('status', 'UNKNOWN')}; thresholds={review.get('threshold_count', 'UNKNOWN')}"
    elif key == "simulation":
        simulation = _mapping(status.get("simulation"))
        gate_ok = gate_ok and bool(simulation.get("accepted_events"))
        detail = f"accepted_events={simulation.get('accepted_events', 'UNKNOWN')}; status={simulation.get('status', 'UNKNOWN')}"
    elif key == "paper_shadow":
        paper_shadow = _mapping(status.get("paper_shadow_experiment"))
        gate_ok = (
            gate_ok
            and bool(paper_shadow.get("would_open_count"))
            and paper_shadow.get("demo_authorized") is False
        )
        detail = (
            f"status={paper_shadow.get('status', 'UNKNOWN')}; "
            f"would_open={paper_shadow.get('would_open_count', 'UNKNOWN')}; "
            f"demo_authorized={paper_shadow.get('demo_authorized', 'UNKNOWN')}"
        )
    elif key == "shadow_lifecycle":
        lifecycle = _mapping(status.get("shadow_lifecycle_experiment"))
        gate_ok = (
            gate_ok
            and bool(lifecycle.get("synthetic_open_count"))
            and lifecycle.get("demo_authorized") is False
        )
        detail = (
            f"status={lifecycle.get('status', 'UNKNOWN')}; "
            f"opens={lifecycle.get('synthetic_open_count', 'UNKNOWN')}; "
            f"net_r={lifecycle.get('synthetic_total_net_r', 'UNKNOWN')}; "
            f"demo_authorized={lifecycle.get('demo_authorized', 'UNKNOWN')}"
        )
    elif key == "lifecycle_guard":
        guard = _mapping(status.get("lifecycle_guard_experiment"))
        gate_ok = (
            gate_ok
            and bool(guard.get("guarded_open_count"))
            and guard.get("demo_authorized") is False
        )
        detail = (
            f"status={guard.get('status', 'UNKNOWN')}; "
            f"opens={guard.get('guarded_open_count', 'UNKNOWN')}; "
            f"net_r={guard.get('guarded_total_net_r', 'UNKNOWN')}; "
            f"dd_r={guard.get('guarded_max_drawdown_r', 'UNKNOWN')}; "
            f"demo_authorized={guard.get('demo_authorized', 'UNKNOWN')}"
        )
    elif key == "demo_rehearsal":
        rehearsal = _mapping(status.get("demo_rehearsal"))
        gate_ok = (
            gate_ok
            and bool(rehearsal.get("rehearsal_event_count"))
            and rehearsal.get("demo_authorized") is False
            and rehearsal.get("can_start_real_demo") is False
        )
        detail = (
            f"status={rehearsal.get('status', 'UNKNOWN')}; "
            f"events={rehearsal.get('rehearsal_event_count', 'UNKNOWN')}; "
            f"opens={rehearsal.get('shadow_open_events', 'UNKNOWN')}; "
            f"blocked={rehearsal.get('blocked_events', 'UNKNOWN')}; "
            f"can_start_real_demo={rehearsal.get('can_start_real_demo', 'UNKNOWN')}"
        )
    elif key == "demo_handoff":
        handoff = _mapping(status.get("demo_handoff"))
        gate_ok = (
            gate_ok
            and handoff.get("can_start_demo_now") is False
            and handoff.get("demo_authorized") is False
        )
        detail = (
            f"status={handoff.get('status', 'UNKNOWN')}; "
            f"phase2={handoff.get('phase2_readiness', 'UNKNOWN')}; "
            f"can_start_demo_now={handoff.get('can_start_demo_now', 'UNKNOWN')}"
        )
    return {
        "key": key,
        "requirement": label,
        "status": "PASS" if gate_ok else "PENDING",
        "evidence": str(evidence) if evidence else "",
        "detail": detail if exists else "missing evidence",
    }


def _phase2_pending_gates(path: Path, countdown: dict[str, Any]) -> list[dict[str, str]]:
    if not path.exists():
        return [{"gate": "Phase 2 readiness report", "status": "MISSING", "evidence": str(path)}]
    wait_gate_details = _countdown_wait_gate_details(countdown)
    owner_action_details = _countdown_owner_action_details(countdown)
    rows: list[dict[str, str]] = []
    in_gates = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            in_gates = line.strip() == "## Gates"
            continue
        if not in_gates:
            continue
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Gate |"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        gate, status, evidence = parts[:3]
        if status != "PASS":
            detail = wait_gate_details.get(gate) or owner_action_details.get(gate)
            row = {"gate": gate, "status": status, "evidence": evidence}
            if detail:
                row["current_detail"] = detail
            rows.append(row)
    return rows


def _countdown_wait_gate_details(countdown: dict[str, Any]) -> dict[str, str]:
    details: dict[str, str] = {}
    wait_gates = countdown.get("wait_gates")
    if not isinstance(wait_gates, list):
        return details
    for raw in wait_gates:
        row = _mapping(raw)
        gate = str(row.get("gate", ""))
        if not gate:
            continue
        current = row.get("current", "UNKNOWN")
        required = row.get("required", "UNKNOWN")
        remaining = row.get("remaining", "UNKNOWN")
        unit = row.get("unit", "")
        details[gate] = f"current={current}; required={required}; remaining={remaining}; unit={unit}"
    return details


def _countdown_owner_action_details(countdown: dict[str, Any]) -> dict[str, str]:
    details: dict[str, str] = {}
    actions = countdown.get("owner_actions_now")
    if not isinstance(actions, list):
        return details
    for raw in actions:
        row = _mapping(raw)
        gate = str(row.get("gate", ""))
        action = str(row.get("action", ""))
        if gate and action:
            details[gate] = action
    return details


def _render_markdown(audit: dict[str, Any]) -> str:
    repo_rows = audit.get("repo_requirement_rows", [])
    blockers = audit.get("external_blockers", [])
    next_rows = audit.get("next_when_real_gates_pass", [])
    return "\n".join(
        [
            "# Phase 3 Completion Audit",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {audit['status']}",
            "",
            "## Decision",
            "",
            _table(
                [
                    ("Phase 3 repo-side complete", str(audit.get("phase3_repo_complete", False))),
                    ("Phase 3 release-clean", str(audit.get("phase3_release_clean", False))),
                    ("Demo/paper authorized", str(audit.get("demo_authorized", False))),
                    ("Real Phase 1 acceptance", str(audit.get("real_phase1_acceptance", "UNKNOWN"))),
                    ("Real Phase 2 readiness", str(audit.get("real_phase2_readiness", "UNKNOWN"))),
                    ("Boundary", str(audit.get("boundary", ""))),
                ]
            ),
            "",
            "## Phase 3 Repo Requirements",
            "",
            _repo_requirement_table(repo_rows if isinstance(repo_rows, list) else []),
            "",
            "## Remaining Phase 3 Repo Items",
            "",
            _remaining_repo_items(audit.get("remaining_phase3_repo_items", [])),
            "",
            "## External Gates Still Blocking Demo",
            "",
            _blocker_table(blockers if isinstance(blockers, list) else []),
            "",
            "## When Real Gates Pass",
            "",
            _bullet_list([str(item) for item in next_rows if item]),
            "",
        ]
    )


def _repo_requirement_table(rows: list[Any]) -> str:
    output = ["| Requirement | Status | Detail | Evidence |", "| --- | --- | --- | --- |"]
    for raw in rows:
        row = _mapping(raw)
        output.append(
            "| "
            + " | ".join(
                [
                    _escape(row.get("requirement", "")),
                    _escape(row.get("status", "")),
                    _escape(row.get("detail", "")),
                    _escape(row.get("evidence", "")),
                ]
            )
            + " |"
        )
    return "\n".join(output)


def _remaining_repo_items(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return "None. All repo-side Phase 3 experimental requirements are complete."
    return _repo_requirement_table(rows)


def _blocker_table(rows: list[Any]) -> str:
    if not rows:
        return "None recorded in `PHASE2_READINESS_REPORT.md`."
    output = ["| Gate | Status | Evidence | Current Detail |", "| --- | --- | --- | --- |"]
    for raw in rows:
        row = _mapping(raw)
        output.append(
            "| "
            + " | ".join(
                [
                    _escape(row.get("gate", "")),
                    _escape(row.get("status", "")),
                    _escape(row.get("evidence", "")),
                    _escape(row.get("current_detail", "")),
                ]
            )
            + " |"
        )
    return "\n".join(output)


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {_escape(row)}" for row in rows) if rows else "- None."


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
    parser = argparse.ArgumentParser(description="Generate Phase 3 completion audit.")
    parser.add_argument("--phase3-root", type=Path, default=phase3_root)
    parser.add_argument("--repo-root", type=Path, default=phase3_root.parents[1])
    args = parser.parse_args(argv)
    path = generate_phase3_completion_audit(args.phase3_root, args.repo_root)
    print(f"Phase 3 completion audit: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
