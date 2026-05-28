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
    suspend_family_decision = _read_json(reports / "PHASE3_SUSPEND_FAMILY_DECISION.json")
    cost_mode_comparison = _read_json(reports / "PHASE3_COST_MODE_COMPARISON.json")
    cost_gate_review = _read_json(reports / "PHASE3_COST_GATE_REVIEW.json")
    family_dedup_audit = _read_json(reports / "PHASE3_FAMILY_DEDUP_AUDIT.json")
    completion_audit = _read_json(reports / "PHASE3_COMPLETION_AUDIT.json")
    paper_shadow = _read_json(reports / "PHASE3_PAPER_SHADOW_SUMMARY.json")
    shadow_lifecycle = _read_json(reports / "PHASE3_SHADOW_LIFECYCLE_SUMMARY.json")
    lifecycle_guard = _read_json(reports / "PHASE3_LIFECYCLE_GUARD_SUMMARY.json")
    demo_rehearsal = _read_json(reports / "PHASE3_DEMO_REHEARSAL_PLAN.json")
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
        "suspend_family_decision": _suspend_decision_summary(suspend_family_decision),
        "cost_mode_comparison": _comparison_summary(cost_mode_comparison),
        "cost_gate_review": _cost_gate_summary(cost_gate_review),
        "family_dedup_audit": _audit_summary(family_dedup_audit),
        "paper_shadow_experiment": _paper_shadow_summary(paper_shadow),
        "shadow_lifecycle_experiment": _shadow_lifecycle_summary(shadow_lifecycle),
        "lifecycle_guard_experiment": _lifecycle_guard_summary(lifecycle_guard),
        "demo_rehearsal": _demo_rehearsal_summary(demo_rehearsal),
        "completion_audit": _completion_audit_summary(completion_audit),
        "manifest": _manifest_summary(manifest),
        "known_state_strings": [
            "EXPERIMENTAL_ACTIVE",
            "EXPERIMENTAL_WAITING_FOR_PHASE2",
            "EXPERIMENTAL_COST_SUSPEND_SCENARIO",
            "EXPERIMENTAL_BOUNDARY_FAIL",
            "EXPERIMENTAL_REVIEW_READY",
            "EXPERIMENTAL_ARCHIVED",
            "SIDE_EXPERIMENT_READY_FOR_PAPER_SHADOW_PROTOTYPE",
            "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS",
            "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY",
            "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY",
            "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY",
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
    suspend_family_decision = _mapping(status.get("suspend_family_decision"))
    cost_mode_comparison = _mapping(status.get("cost_mode_comparison"))
    cost_gate_review = _mapping(status.get("cost_gate_review"))
    family_dedup_audit = _mapping(status.get("family_dedup_audit"))
    paper_shadow = _mapping(status.get("paper_shadow_experiment"))
    shadow_lifecycle = _mapping(status.get("shadow_lifecycle_experiment"))
    lifecycle_guard = _mapping(status.get("lifecycle_guard_experiment"))
    demo_rehearsal = _mapping(status.get("demo_rehearsal"))
    completion_audit = _mapping(status.get("completion_audit"))
    manifest = _mapping(status.get("manifest"))
    median_net_by_mode = _mapping(cost_mode_comparison.get("median_net_after_proxy_by_mode"))
    suspend_count_by_mode = _mapping(cost_mode_comparison.get("suspend_family_count_by_mode"))
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
                    ("Gross expectancy R source", str(simulation.get("gross_expectancy_r_source", "n/a"))),
                    ("Baseline assumed cost R", str(simulation.get("baseline_assumed_cost_r", "n/a"))),
                    ("Baseline net expectancy R", str(simulation.get("baseline_net_expectancy_r", "n/a"))),
                    ("Median proxy cost R", str(simulation.get("median_proxy_cost_r", "n/a"))),
                    ("Median net after proxy cost R", str(simulation.get("median_net_after_proxy_cost_r", "n/a"))),
                    (
                        "Median net delta vs assumed baseline R",
                        str(simulation.get("median_net_delta_vs_assumed_baseline_r", "n/a")),
                    ),
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
                    ("Suspend decision", str(suspend_family_decision.get("status", "UNKNOWN"))),
                    ("Keep-suspended primary rows", str(suspend_family_decision.get("keep_suspended_primary_rows", "UNKNOWN"))),
                    ("Cost-mode comparison", str(cost_mode_comparison.get("status", "UNKNOWN"))),
                    ("entry_exit_proxy median net R", str(median_net_by_mode.get("entry_exit_proxy", "UNKNOWN"))),
                    ("p95_fresh_proxy median net R", str(median_net_by_mode.get("p95_fresh_proxy", "UNKNOWN"))),
                    ("stress_2x_p95_proxy median net R", str(median_net_by_mode.get("stress_2x_p95_proxy", "UNKNOWN"))),
                    ("entry_exit_proxy SUSPEND_FAMILY rows", str(suspend_count_by_mode.get("entry_exit_proxy", "UNKNOWN"))),
                    ("p95_fresh_proxy SUSPEND_FAMILY rows", str(suspend_count_by_mode.get("p95_fresh_proxy", "UNKNOWN"))),
                    ("stress_2x_p95_proxy SUSPEND_FAMILY rows", str(suspend_count_by_mode.get("stress_2x_p95_proxy", "UNKNOWN"))),
                    ("Stress suspend family events", str(cost_mode_comparison.get("stress_suspend_family_unique_events", "UNKNOWN"))),
                    ("Cost-gate review", str(cost_gate_review.get("status", "UNKNOWN"))),
                    ("Cost-gate 0.25R blocked families", str(cost_gate_review.get("threshold_0_25_family_unique_events", "UNKNOWN"))),
                    ("Spread P95 points", str(cost_gate_review.get("spread_p95_points", "UNKNOWN"))),
                    ("Kill-state summary", str(cost_gate_review.get("kill_state_counts", "UNKNOWN"))),
                    ("De-dup audit", str(family_dedup_audit.get("status", "UNKNOWN"))),
                    ("De-dup classifications", str(family_dedup_audit.get("classification_counts", "UNKNOWN"))),
                    ("Paper-shadow status", str(paper_shadow.get("status", "UNKNOWN"))),
                    ("Paper-shadow would-open", str(paper_shadow.get("would_open_count", "UNKNOWN"))),
                    ("Paper-shadow cost-review opens", str(paper_shadow.get("would_open_review_count", "UNKNOWN"))),
                    ("Paper-shadow blocked suspend", str(paper_shadow.get("blocked_suspend_count", "UNKNOWN"))),
                    ("Paper-shadow observer no-exposure", str(paper_shadow.get("observer_no_exposure_count", "UNKNOWN"))),
                    ("Paper-shadow monthly estimate", str(paper_shadow.get("estimated_monthly_shadow_open_count", "UNKNOWN"))),
                    ("Shadow lifecycle status", str(shadow_lifecycle.get("status", "UNKNOWN"))),
                    ("Shadow lifecycle synthetic opens", str(shadow_lifecycle.get("synthetic_open_count", "UNKNOWN"))),
                    ("Shadow lifecycle net R", str(shadow_lifecycle.get("synthetic_total_net_r", "UNKNOWN"))),
                    ("Shadow lifecycle max DD R", str(shadow_lifecycle.get("synthetic_max_drawdown_r", "UNKNOWN"))),
                    ("Shadow lifecycle risk locks", str(shadow_lifecycle.get("risk_lock_counts", "UNKNOWN"))),
                    ("Lifecycle guard status", str(lifecycle_guard.get("status", "UNKNOWN"))),
                    ("Lifecycle guard opens", str(lifecycle_guard.get("guarded_open_count", "UNKNOWN"))),
                    ("Lifecycle guard net R", str(lifecycle_guard.get("guarded_total_net_r", "UNKNOWN"))),
                    ("Lifecycle guard max DD R", str(lifecycle_guard.get("guarded_max_drawdown_r", "UNKNOWN"))),
                    ("Lifecycle guard net improvement R", str(lifecycle_guard.get("net_improvement_r", "UNKNOWN"))),
                    ("Lifecycle guard DD improvement R", str(lifecycle_guard.get("drawdown_improvement_r", "UNKNOWN"))),
                    ("Demo rehearsal status", str(demo_rehearsal.get("status", "UNKNOWN"))),
                    ("Demo rehearsal events", str(demo_rehearsal.get("rehearsal_event_count", "UNKNOWN"))),
                    ("Demo rehearsal shadow opens", str(demo_rehearsal.get("shadow_open_events", "UNKNOWN"))),
                    ("Demo rehearsal blocked", str(demo_rehearsal.get("blocked_events", "UNKNOWN"))),
                    ("Demo rehearsal can start real demo", str(demo_rehearsal.get("can_start_real_demo", "UNKNOWN"))),
                    ("Completion audit", str(completion_audit.get("status", "UNKNOWN"))),
                    ("Phase 3 repo complete", str(completion_audit.get("phase3_repo_complete", "UNKNOWN"))),
                    ("Demo authorized", str(completion_audit.get("demo_authorized", "UNKNOWN"))),
                    ("External blockers", str(completion_audit.get("external_blocker_count", "UNKNOWN"))),
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


def _suspend_decision_summary(decision: dict[str, object]) -> dict[str, object]:
    if not decision:
        return {}
    counts = decision.get("codex_review_decision_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    return {
        "status": decision.get("status", "UNKNOWN"),
        "created_at_utc": decision.get("created_at_utc", ""),
        "primary_suspend_rows": decision.get("primary_suspend_rows", "UNKNOWN"),
        "unique_family_events": decision.get("unique_family_events", "UNKNOWN"),
        "keep_suspended_primary_rows": counts.get("KEEP_SUSPENDED", "UNKNOWN"),
        "future_rule_counts": decision.get("future_rule_counts", {}),
    }


def _comparison_summary(comparison: dict[str, object]) -> dict[str, object]:
    if not comparison:
        return {}
    rows = comparison.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    by_mode = {
        str(row.get("cost_mode")): row
        for row in rows
        if isinstance(row, dict) and row.get("cost_mode")
    }
    stress = next(
        (row for row in rows if isinstance(row, dict) and row.get("cost_mode") == "stress_2x_p95_proxy"),
        {},
    )
    return {
        "status": comparison.get("status", "UNKNOWN"),
        "mode_count": len(rows),
        "stress_suspend_family_unique_events": stress.get("suspend_family_unique_events", "UNKNOWN")
        if isinstance(stress, dict)
        else "UNKNOWN",
        "median_net_after_proxy_by_mode": {
            mode: row.get("median_net_after_proxy_cost_r", "UNKNOWN") for mode, row in sorted(by_mode.items())
        },
        "suspend_family_count_by_mode": {
            mode: row.get("suspend_family_count", "UNKNOWN") for mode, row in sorted(by_mode.items())
        },
        "suspend_family_unique_events_by_mode": {
            mode: row.get("suspend_family_unique_events", "UNKNOWN") for mode, row in sorted(by_mode.items())
        },
    }


def _cost_gate_summary(review: dict[str, object]) -> dict[str, object]:
    if not review:
        return {}
    threshold_rows = review.get("threshold_rows", [])
    if not isinstance(threshold_rows, list):
        threshold_rows = []
    kill_rows = review.get("kill_state_rows", [])
    if not isinstance(kill_rows, list):
        kill_rows = []
    threshold_025 = next(
        (row for row in threshold_rows if isinstance(row, dict) and str(row.get("threshold_r")) == "0.25"),
        {},
    )
    kill_state_counts = {
        str(row.get("bucket", "UNKNOWN")): row.get("family_unique_events", "UNKNOWN")
        for row in kill_rows
        if isinstance(row, dict)
    }
    return {
        "status": review.get("status", "UNKNOWN"),
        "created_at_utc": review.get("created_at_utc", ""),
        "threshold_count": len(threshold_rows),
        "threshold_0_25_family_unique_events": threshold_025.get("family_unique_events", "UNKNOWN")
        if isinstance(threshold_025, dict)
        else "UNKNOWN",
        "stop_bucket_count": len(review.get("stop_distance_bucket_rows", []))
        if isinstance(review.get("stop_distance_bucket_rows"), list)
        else "UNKNOWN",
        "spread_bucket_count": len(review.get("spread_regime_bucket_rows", []))
        if isinstance(review.get("spread_regime_bucket_rows"), list)
        else "UNKNOWN",
        "spread_median_points": review.get("spread_median_points", "UNKNOWN"),
        "spread_p95_points": review.get("spread_p95_points", "UNKNOWN"),
        "kill_state_counts": kill_state_counts,
    }


def _audit_summary(audit: dict[str, object]) -> dict[str, object]:
    if not audit:
        return {}
    return {
        "status": audit.get("status", "UNKNOWN"),
        "family_group_count": audit.get("family_group_count", "UNKNOWN"),
        "multi_row_group_count": audit.get("multi_row_group_count", "UNKNOWN"),
        "classification_counts": audit.get("classification_counts", {}),
    }


def _paper_shadow_summary(summary: dict[str, object]) -> dict[str, object]:
    if not summary:
        return {}
    return {
        "status": summary.get("status", "UNKNOWN"),
        "created_at_utc": summary.get("created_at_utc", ""),
        "real_phase2_readiness": summary.get("real_phase2_readiness", "UNKNOWN"),
        "demo_authorized": summary.get("demo_authorized", "UNKNOWN"),
        "source_ledger_rows": summary.get("source_ledger_rows", "UNKNOWN"),
        "primary_stream_rows": summary.get("primary_stream_rows", "UNKNOWN"),
        "would_open_count": summary.get("would_open_count", "UNKNOWN"),
        "would_open_review_count": summary.get("would_open_review_count", "UNKNOWN"),
        "blocked_suspend_count": summary.get("blocked_suspend_count", "UNKNOWN"),
        "observer_no_exposure_count": summary.get("observer_no_exposure_count", "UNKNOWN"),
        "duplicate_ignored_count": summary.get("duplicate_ignored_count", "UNKNOWN"),
        "conflict_review_count": summary.get("conflict_review_count", "UNKNOWN"),
        "estimated_monthly_shadow_open_count": summary.get("estimated_monthly_shadow_open_count", "UNKNOWN"),
        "mean_shadow_open_net_r": summary.get("mean_shadow_open_net_r", "UNKNOWN"),
    }


def _shadow_lifecycle_summary(summary: dict[str, object]) -> dict[str, object]:
    if not summary:
        return {}
    return {
        "status": summary.get("status", "UNKNOWN"),
        "created_at_utc": summary.get("created_at_utc", ""),
        "demo_authorized": summary.get("demo_authorized", "UNKNOWN"),
        "source_shadow_rows": summary.get("source_shadow_rows", "UNKNOWN"),
        "synthetic_open_count": summary.get("synthetic_open_count", "UNKNOWN"),
        "synthetic_close_count": summary.get("synthetic_close_count", "UNKNOWN"),
        "no_exposure_review_only_count": summary.get("no_exposure_review_only_count", "UNKNOWN"),
        "synthetic_win_rate_pct": summary.get("synthetic_win_rate_pct", "UNKNOWN"),
        "synthetic_total_gross_r": summary.get("synthetic_total_gross_r", "UNKNOWN"),
        "synthetic_total_net_r": summary.get("synthetic_total_net_r", "UNKNOWN"),
        "synthetic_mean_net_r": summary.get("synthetic_mean_net_r", "UNKNOWN"),
        "synthetic_max_drawdown_r": summary.get("synthetic_max_drawdown_r", "UNKNOWN"),
        "risk_lock_counts": summary.get("risk_lock_counts", {}),
        "close_reason_counts": summary.get("close_reason_counts", {}),
    }


def _lifecycle_guard_summary(summary: dict[str, object]) -> dict[str, object]:
    if not summary:
        return {}
    return {
        "status": summary.get("status", "UNKNOWN"),
        "created_at_utc": summary.get("created_at_utc", ""),
        "demo_authorized": summary.get("demo_authorized", "UNKNOWN"),
        "baseline_open_count": summary.get("baseline_open_count", "UNKNOWN"),
        "guarded_open_count": summary.get("guarded_open_count", "UNKNOWN"),
        "blocked_count": summary.get("blocked_count", "UNKNOWN"),
        "baseline_total_net_r": summary.get("baseline_total_net_r", "UNKNOWN"),
        "guarded_total_net_r": summary.get("guarded_total_net_r", "UNKNOWN"),
        "net_improvement_r": summary.get("net_improvement_r", "UNKNOWN"),
        "baseline_max_drawdown_r": summary.get("baseline_max_drawdown_r", "UNKNOWN"),
        "guarded_max_drawdown_r": summary.get("guarded_max_drawdown_r", "UNKNOWN"),
        "drawdown_improvement_r": summary.get("drawdown_improvement_r", "UNKNOWN"),
        "guarded_win_rate_pct": summary.get("guarded_win_rate_pct", "UNKNOWN"),
        "guard_decision_counts": summary.get("guard_decision_counts", {}),
        "guard_block_reason_counts": summary.get("guard_block_reason_counts", {}),
    }


def _demo_rehearsal_summary(summary: dict[str, object]) -> dict[str, object]:
    if not summary:
        return {}
    return {
        "status": summary.get("status", "UNKNOWN"),
        "created_at_utc": summary.get("created_at_utc", ""),
        "real_phase2_readiness": summary.get("real_phase2_readiness", "UNKNOWN"),
        "demo_authorized": summary.get("demo_authorized", "UNKNOWN"),
        "can_start_real_demo": summary.get("can_start_real_demo", "UNKNOWN"),
        "mt5_runtime_touched": summary.get("mt5_runtime_touched", "UNKNOWN"),
        "broker_action_code_allowed": summary.get("broker_action_code_allowed", "UNKNOWN"),
        "source_guard_rows": summary.get("source_guard_rows", "UNKNOWN"),
        "rehearsal_event_count": summary.get("rehearsal_event_count", "UNKNOWN"),
        "shadow_open_events": summary.get("shadow_open_events", "UNKNOWN"),
        "shadow_close_events": summary.get("shadow_close_events", "UNKNOWN"),
        "blocked_events": summary.get("blocked_events", "UNKNOWN"),
        "blocked_cost_events": summary.get("blocked_cost_events", "UNKNOWN"),
        "blocked_risk_events": summary.get("blocked_risk_events", "UNKNOWN"),
        "no_exposure_events": summary.get("no_exposure_events", "UNKNOWN"),
        "guarded_total_net_r": summary.get("guarded_total_net_r", "UNKNOWN"),
        "guarded_max_drawdown_r": summary.get("guarded_max_drawdown_r", "UNKNOWN"),
        "event_type_counts": summary.get("event_type_counts", {}),
        "next_real_gate_needed": summary.get("next_real_gate_needed", ""),
    }


def _completion_audit_summary(audit: dict[str, object]) -> dict[str, object]:
    if not audit:
        return {}
    blockers = audit.get("external_blockers", [])
    remaining = audit.get("remaining_phase3_repo_items", [])
    if not isinstance(blockers, list):
        blockers = []
    if not isinstance(remaining, list):
        remaining = []
    return {
        "status": audit.get("status", "UNKNOWN"),
        "created_at_utc": audit.get("created_at_utc", ""),
        "phase3_repo_complete": audit.get("phase3_repo_complete", "UNKNOWN"),
        "demo_authorized": audit.get("demo_authorized", "UNKNOWN"),
        "remaining_phase3_repo_items": len(remaining),
        "external_blocker_count": len(blockers),
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
