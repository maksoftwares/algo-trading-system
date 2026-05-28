from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


REHEARSAL_SESSION_ID = "phase3-demo-rehearsal-side-experiment-v0"
SIDE_EXPERIMENT_BOUNDARY = "side_experiment_only_demo_rehearsal_no_mt5_touch_no_real_gate_promotion"
CAN_START_REAL_DEMO = False

REHEARSAL_COLUMNS = (
    "rehearsal_event_id",
    "rehearsal_session_id",
    "guard_event_id",
    "source_cluster_id",
    "family_event_id",
    "decision_bar_time",
    "broker_day",
    "symbol",
    "direction",
    "guard_decision",
    "guard_block_reason",
    "rehearsal_event_type",
    "rehearsal_action",
    "synthetic_net_r",
    "running_rehearsal_equity_r",
    "running_rehearsal_drawdown_r",
    "daily_lock_active_after_event",
    "portfolio_lock_active_after_event",
    "demo_authorized",
    "can_start_real_demo",
    "mt5_runtime_touched",
    "broker_action_code_allowed",
    "rehearsal_notes",
)


def generate_demo_rehearsal_package(
    guard_ledger_path: Path,
    guard_summary_path: Path,
    output_dir: Path,
    repo_root: Path | None = None,
) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = repo_root.resolve() if repo_root else output_dir.parents[4].resolve()
    guard_rows = _read_csv(guard_ledger_path)
    guard_summary = _read_json(guard_summary_path)
    rehearsal_rows = _rehearsal_rows(guard_rows)
    csv_path = output_dir / "PHASE3_DEMO_REHEARSAL_LEDGER.csv"
    json_path = output_dir / "PHASE3_DEMO_REHEARSAL_PLAN.json"
    md_path = output_dir / "PHASE3_DEMO_REHEARSAL_CHECKLIST.md"
    _write_csv(csv_path, rehearsal_rows)
    summary = _summary(
        repo_root=repo_root,
        guard_ledger_path=guard_ledger_path,
        guard_summary_path=guard_summary_path,
        rehearsal_ledger_path=csv_path,
        guard_summary=guard_summary,
        guard_rows=guard_rows,
        rehearsal_rows=rehearsal_rows,
    )
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary, rehearsal_rows), encoding="utf-8")
    return json_path


def _rehearsal_rows(guard_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    running_equity = 0.0
    peak_equity = 0.0
    event_number = 1
    for row in guard_rows:
        event_type, action = _event_type_and_action(row.get("guard_decision", ""))
        net_r = _to_float(row.get("guarded_synthetic_net_r")) or 0.0
        if event_type == "REHEARSAL_SHADOW_OPEN":
            open_row = _base_row(row, event_number, event_type, action, 0.0, running_equity, peak_equity)
            rows.append(open_row)
            event_number += 1
            running_equity += net_r
            peak_equity = max(peak_equity, running_equity)
            close_row = _base_row(
                row,
                event_number,
                "REHEARSAL_SHADOW_CLOSE",
                _close_action(row),
                net_r,
                running_equity,
                peak_equity,
            )
            rows.append(close_row)
            event_number += 1
            continue
        rows.append(_base_row(row, event_number, event_type, action, 0.0, running_equity, peak_equity))
        event_number += 1
    return rows


def _base_row(
    row: dict[str, str],
    event_number: int,
    event_type: str,
    action: str,
    synthetic_net_r: float,
    running_equity: float,
    peak_equity: float,
) -> dict[str, str]:
    drawdown = running_equity - peak_equity
    return {
        "rehearsal_event_id": f"PH3REHEARSAL{event_number:05d}",
        "rehearsal_session_id": REHEARSAL_SESSION_ID,
        "guard_event_id": row.get("guard_event_id", ""),
        "source_cluster_id": row.get("source_cluster_id", ""),
        "family_event_id": row.get("family_event_id", ""),
        "decision_bar_time": row.get("decision_bar_time", ""),
        "broker_day": row.get("broker_day", ""),
        "symbol": row.get("symbol", ""),
        "direction": row.get("direction", ""),
        "guard_decision": row.get("guard_decision", ""),
        "guard_block_reason": row.get("guard_block_reason", ""),
        "rehearsal_event_type": event_type,
        "rehearsal_action": action,
        "synthetic_net_r": _fmt(synthetic_net_r),
        "running_rehearsal_equity_r": _fmt(running_equity),
        "running_rehearsal_drawdown_r": _fmt(drawdown),
        "daily_lock_active_after_event": row.get("daily_lock_active_after_event", "false"),
        "portfolio_lock_active_after_event": row.get("portfolio_lock_active_after_event", "false"),
        "demo_authorized": "false",
        "can_start_real_demo": str(CAN_START_REAL_DEMO).lower(),
        "mt5_runtime_touched": "false",
        "broker_action_code_allowed": "false",
        "rehearsal_notes": _rehearsal_notes(event_type, row.get("guard_block_reason", "")),
    }


def _event_type_and_action(guard_decision: str) -> tuple[str, str]:
    if guard_decision == "GUARDED_SYNTHETIC_OPEN":
        return "REHEARSAL_SHADOW_OPEN", "record_shadow_intent_without_broker_side_effect"
    if guard_decision in {"BLOCKED_COST_R", "BLOCKED_COST_WATCH"}:
        return "REHEARSAL_BLOCKED_COST", "record_cost_block_and_no_exposure"
    if guard_decision.startswith("BLOCKED_"):
        return "REHEARSAL_BLOCKED_RISK", "record_risk_block_and_no_exposure"
    return "REHEARSAL_NO_EXPOSURE", "record_review_only_no_exposure"


def _close_action(row: dict[str, str]) -> str:
    reason = row.get("baseline_synthetic_close_reason", "") or "synthetic_close"
    return f"record_shadow_close_{reason}"


def _summary(
    repo_root: Path,
    guard_ledger_path: Path,
    guard_summary_path: Path,
    rehearsal_ledger_path: Path,
    guard_summary: dict[str, Any],
    guard_rows: list[dict[str, str]],
    rehearsal_rows: list[dict[str, str]],
) -> dict[str, Any]:
    phase2_status = _read_markdown_status(
        repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    )
    event_counts = _counts(row.get("rehearsal_event_type", "") for row in rehearsal_rows)
    blocked_events = sum(
        count
        for key, count in event_counts.items()
        if key in {"REHEARSAL_BLOCKED_COST", "REHEARSAL_BLOCKED_RISK"}
    )
    return {
        "status": "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY" if rehearsal_rows else "SIDE_EXPERIMENT_NO_REHEARSAL_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": SIDE_EXPERIMENT_BOUNDARY,
        "assumption": "assumes_phase2_pass_for_design_only_and_builds_a_non_deploying_demo_rehearsal",
        "real_phase2_readiness": phase2_status or "UNKNOWN",
        "demo_authorized": False,
        "can_start_real_demo": CAN_START_REAL_DEMO,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "blocker_override_mode": "side_experiment_only",
        "guard_ledger": str(guard_ledger_path),
        "guard_summary": str(guard_summary_path),
        "rehearsal_ledger": str(rehearsal_ledger_path),
        "source_guard_rows": len(guard_rows),
        "rehearsal_event_count": len(rehearsal_rows),
        "shadow_open_events": event_counts.get("REHEARSAL_SHADOW_OPEN", 0),
        "shadow_close_events": event_counts.get("REHEARSAL_SHADOW_CLOSE", 0),
        "blocked_events": blocked_events,
        "blocked_cost_events": event_counts.get("REHEARSAL_BLOCKED_COST", 0),
        "blocked_risk_events": event_counts.get("REHEARSAL_BLOCKED_RISK", 0),
        "no_exposure_events": event_counts.get("REHEARSAL_NO_EXPOSURE", 0),
        "event_type_counts": event_counts,
        "guarded_open_count": guard_summary.get("guarded_open_count", "UNKNOWN"),
        "guarded_blocked_count": guard_summary.get("blocked_count", "UNKNOWN"),
        "guarded_total_net_r": guard_summary.get("guarded_total_net_r", "UNKNOWN"),
        "guarded_max_drawdown_r": guard_summary.get("guarded_max_drawdown_r", "UNKNOWN"),
        "missing_real_authorizations": [
            "real_phase2_readiness_pass",
            "owner_demo_start_approval",
            "separate_runtime_deployment_review",
        ],
        "next_real_gate_needed": "PHASE2_READINESS_REPORT.md PASS plus owner approval before any runtime deployment.",
        "notes": [
            "This is a non-deploying demo rehearsal plan, not a paper account action.",
            "Every row preserves demo_authorized=false and can_start_real_demo=false.",
            "The rehearsal packages the exact sequence reviewers should expect after real approval.",
        ],
    }


def _render_markdown(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Phase 3 Demo Rehearsal Checklist",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Boundary",
            "",
            "- This is a side-experiment demo rehearsal package.",
            "- It does not start demo, paper, or live runtime activity.",
            "- It does not touch MT5 runtime files.",
            "- It does not authorize broker-side actions.",
            "- `demo_authorized` and `can_start_real_demo` remain `false`.",
            "",
            "## Rehearsal Summary",
            "",
            _table(
                [
                    ("Real Phase 2 readiness", str(summary.get("real_phase2_readiness", "UNKNOWN"))),
                    ("Source guard rows", str(summary.get("source_guard_rows", 0))),
                    ("Rehearsal events", str(summary.get("rehearsal_event_count", 0))),
                    ("Shadow open events", str(summary.get("shadow_open_events", 0))),
                    ("Shadow close events", str(summary.get("shadow_close_events", 0))),
                    ("Blocked events", str(summary.get("blocked_events", 0))),
                    ("Cost-block events", str(summary.get("blocked_cost_events", 0))),
                    ("Risk-block events", str(summary.get("blocked_risk_events", 0))),
                    ("No-exposure events", str(summary.get("no_exposure_events", 0))),
                    ("Guarded total net R", str(summary.get("guarded_total_net_r", "UNKNOWN"))),
                    ("Guarded max DD R", str(summary.get("guarded_max_drawdown_r", "UNKNOWN"))),
                    ("Can start real demo", str(summary.get("can_start_real_demo", False))),
                ]
            ),
            "",
            "## Required Before Real Demo",
            "",
            _bullet_list(_as_str_list(summary.get("missing_real_authorizations"))),
            "",
            "## Rehearsal Event Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in _mapping(summary.get("event_type_counts")).items())),
            "",
            "## Sample Rehearsal Rows",
            "",
            _sample_table(rows[:14]),
            "",
        ]
    )


def _sample_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No rows."
    columns = (
        "rehearsal_event_id",
        "source_cluster_id",
        "decision_bar_time",
        "guard_decision",
        "rehearsal_event_type",
        "rehearsal_action",
        "synthetic_net_r",
        "running_rehearsal_drawdown_r",
        "can_start_real_demo",
    )
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        output.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _rehearsal_notes(event_type: str, block_reason: str) -> str:
    if event_type == "REHEARSAL_SHADOW_OPEN":
        return "Rehearsal records an intent only; no broker-side effect is allowed."
    if event_type == "REHEARSAL_SHADOW_CLOSE":
        return "Rehearsal closes the synthetic lifecycle record only."
    if event_type == "REHEARSAL_BLOCKED_COST":
        return f"Rehearsal blocks exposure for cost control: {block_reason}."
    if event_type == "REHEARSAL_BLOCKED_RISK":
        return f"Rehearsal blocks exposure for risk control: {block_reason}."
    return "Rehearsal keeps this row review-only with no exposure."


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REHEARSAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


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


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = value or "blank"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {_escape(row)}" for row in rows) if rows else "- None."


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    repo_root = phase3_root.parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 demo rehearsal package.")
    parser.add_argument("--guard-ledger-path", type=Path, default=reports / "PHASE3_LIFECYCLE_GUARD_LEDGER.csv")
    parser.add_argument("--guard-summary-path", type=Path, default=reports / "PHASE3_LIFECYCLE_GUARD_SUMMARY.json")
    parser.add_argument("--output-dir", type=Path, default=reports)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    args = parser.parse_args(argv)
    path = generate_demo_rehearsal_package(
        args.guard_ledger_path,
        args.guard_summary_path,
        args.output_dir,
        args.repo_root,
    )
    summary = json.loads(path.read_text(encoding="utf-8"))
    print(f"Phase 3 demo rehearsal package: {summary['status']}")
    print(path)
    print(
        f"events={summary['rehearsal_event_count']}; "
        f"opens={summary['shadow_open_events']}; "
        f"blocked={summary['blocked_events']}; "
        f"can_start_real_demo={summary['can_start_real_demo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
