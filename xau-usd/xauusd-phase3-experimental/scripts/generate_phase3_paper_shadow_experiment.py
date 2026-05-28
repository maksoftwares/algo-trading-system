from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


SHADOW_SESSION_ID = "phase3-paper-shadow-side-experiment-v0"
SIDE_EXPERIMENT_BOUNDARY = "side_experiment_only_no_mt5_touch_no_real_gate_promotion"

SHADOW_COLUMNS = (
    "paper_shadow_event_id",
    "paper_shadow_session_id",
    "source_event_id",
    "source_cluster_id",
    "family_event_id",
    "family_event_role",
    "primary_stream_allowed",
    "timestamp_broker",
    "timestamp_utc",
    "timestamp_local",
    "symbol",
    "expert_family",
    "observer",
    "decision_bar_time",
    "direction",
    "entry_price_projected",
    "stop_price_projected",
    "target_price_projected",
    "stop_distance_points",
    "spread_points",
    "cost_mode",
    "proxy_cost_r",
    "net_after_proxy_from_gross_r",
    "net_delta_vs_assumed_baseline_r",
    "kill_rule_state",
    "paper_shadow_state",
    "paper_shadow_action",
    "paper_shadow_exposure_units",
    "blocked_reason",
    "review_priority",
    "demo_authorized",
    "real_phase2_readiness",
    "blocker_override_mode",
    "mt5_runtime_touched",
    "broker_action_code_allowed",
    "paper_shadow_notes",
)


def generate_paper_shadow_experiment(
    ledger_path: Path,
    output_dir: Path,
    repo_root: Path | None = None,
) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = repo_root.resolve() if repo_root else Path(__file__).resolve().parents[3]
    real_phase2_readiness = _read_markdown_status(
        repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    ) or "UNKNOWN"
    source_rows = _read_csv(ledger_path)
    shadow_rows = [
        _shadow_row(index, row, real_phase2_readiness)
        for index, row in enumerate(source_rows, start=1)
    ]
    csv_path = output_dir / "PHASE3_PAPER_SHADOW_LEDGER.csv"
    json_path = output_dir / "PHASE3_PAPER_SHADOW_SUMMARY.json"
    md_path = output_dir / "PHASE3_PAPER_SHADOW_SUMMARY.md"
    _write_csv(csv_path, shadow_rows)
    summary = _summary(ledger_path, csv_path, shadow_rows, real_phase2_readiness)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary, shadow_rows), encoding="utf-8")
    return json_path


def _shadow_row(index: int, row: dict[str, str], real_phase2_readiness: str) -> dict[str, str]:
    state, action, exposure_units, blocked_reason, review_priority, notes = _shadow_decision(row)
    return {
        "paper_shadow_event_id": f"PH3SHADOW{index:05d}",
        "paper_shadow_session_id": SHADOW_SESSION_ID,
        "source_event_id": row.get("event_id", ""),
        "source_cluster_id": row.get("source_cluster_id", ""),
        "family_event_id": row.get("family_event_id", ""),
        "family_event_role": row.get("family_event_role", ""),
        "primary_stream_allowed": row.get("primary_stream_allowed", ""),
        "timestamp_broker": row.get("timestamp_broker", ""),
        "timestamp_utc": row.get("timestamp_utc", ""),
        "timestamp_local": row.get("timestamp_local", ""),
        "symbol": row.get("symbol", ""),
        "expert_family": row.get("expert_family", ""),
        "observer": row.get("observer", ""),
        "decision_bar_time": row.get("decision_bar_time", ""),
        "direction": row.get("direction", ""),
        "entry_price_projected": row.get("entry_price_projected", ""),
        "stop_price_projected": row.get("stop_price_projected", ""),
        "target_price_projected": row.get("target_price_projected", ""),
        "stop_distance_points": row.get("stop_distance_points", ""),
        "spread_points": row.get("spread_points", ""),
        "cost_mode": row.get("cost_mode", ""),
        "proxy_cost_r": row.get("proxy_cost_r", ""),
        "net_after_proxy_from_gross_r": row.get("net_after_proxy_from_gross_r", ""),
        "net_delta_vs_assumed_baseline_r": row.get("net_delta_vs_assumed_baseline_r", ""),
        "kill_rule_state": row.get("kill_rule_state", ""),
        "paper_shadow_state": state,
        "paper_shadow_action": action,
        "paper_shadow_exposure_units": str(exposure_units),
        "blocked_reason": blocked_reason,
        "review_priority": review_priority,
        "demo_authorized": "false",
        "real_phase2_readiness": real_phase2_readiness,
        "blocker_override_mode": "side_experiment_only",
        "mt5_runtime_touched": "false",
        "broker_action_code_allowed": "false",
        "paper_shadow_notes": notes,
    }


def _shadow_decision(row: dict[str, str]) -> tuple[str, str, int, str, str, str]:
    role = row.get("family_event_role", "")
    is_primary = row.get("primary_stream_allowed", "").lower() == "true"
    kill_state = row.get("kill_rule_state", "")
    if not is_primary:
        if role == "OBSERVER_DUPLICATE":
            return (
                "DUPLICATE_IGNORED",
                "NO_EXPOSURE_DUPLICATE_IGNORED",
                0,
                "observer_duplicate",
                "LOW",
                "Same-family observer row is retained for review but cannot create extra exposure.",
            )
        if role == "OBSERVER_CONFLICT":
            return (
                "CONFLICT_REVIEW",
                "NO_EXPOSURE_CONFLICT_REVIEW",
                0,
                "observer_conflict",
                "HIGH",
                "Same-bar observer conflict requires review before any real implementation reuse.",
            )
        return (
            "OBSERVER_ONLY_REVIEW",
            "NO_EXPOSURE_OBSERVER_ONLY",
            0,
            "observer_only_no_primary",
            "MEDIUM",
            "Observer-only event has no primary breakout-retest row and remains review-only.",
        )
    if kill_state == "SUSPEND_FAMILY":
        return (
            "SUSPEND_FAMILY_BLOCKED",
            "BLOCKED_SUSPEND_FAMILY",
            0,
            "net_expectancy_below_minimum_after_proxy_cost",
            "HIGH",
            "Primary family event remains blocked by the experimental cost-survival rule.",
        )
    if kill_state == "COST_WATCH":
        return (
            "COST_WATCH_OPEN_WITH_REVIEW",
            "WOULD_PAPER_SHADOW_OPEN_REVIEW",
            1,
            "",
            "MEDIUM",
            "Primary family event would be shadow-opened but tagged for cost review.",
        )
    return (
        "PAPER_SHADOW_ELIGIBLE",
        "WOULD_PAPER_SHADOW_OPEN",
        1,
        "",
        "LOW",
        "Primary family event is eligible in the side-experiment paper-shadow ledger.",
    )


def _summary(
    input_ledger: Path,
    shadow_ledger: Path,
    rows: list[dict[str, str]],
    real_phase2_readiness: str,
) -> dict[str, Any]:
    action_counts = _counts(row.get("paper_shadow_action", "") for row in rows)
    state_counts = _counts(row.get("paper_shadow_state", "") for row in rows)
    primary_rows = [row for row in rows if row.get("primary_stream_allowed", "").lower() == "true"]
    would_open_rows = [
        row
        for row in rows
        if row.get("paper_shadow_action") in {"WOULD_PAPER_SHADOW_OPEN", "WOULD_PAPER_SHADOW_OPEN_REVIEW"}
    ]
    suspend_rows = [row for row in rows if row.get("paper_shadow_action") == "BLOCKED_SUSPEND_FAMILY"]
    net_values = [_to_float(row.get("net_after_proxy_from_gross_r")) for row in would_open_rows]
    net_values = [value for value in net_values if value is not None]
    status = "SIDE_EXPERIMENT_NO_EVENTS"
    if would_open_rows and suspend_rows:
        status = "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS"
    elif would_open_rows:
        status = "SIDE_EXPERIMENT_READY_FOR_PAPER_SHADOW_PROTOTYPE"
    elif rows:
        status = "SIDE_EXPERIMENT_REVIEW_ONLY_NO_SHADOW_OPENS"
    return {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": SIDE_EXPERIMENT_BOUNDARY,
        "assumption": "assumes_phase2_pass_for_design_only",
        "real_phase2_readiness": real_phase2_readiness,
        "demo_authorized": False,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "blocker_override_mode": "side_experiment_only",
        "input_ledger": str(input_ledger),
        "paper_shadow_ledger": str(shadow_ledger),
        "source_ledger_rows": len(rows),
        "paper_shadow_rows": len(rows),
        "primary_stream_rows": len(primary_rows),
        "would_open_count": len(would_open_rows),
        "would_open_review_count": action_counts.get("WOULD_PAPER_SHADOW_OPEN_REVIEW", 0),
        "blocked_suspend_count": len(suspend_rows),
        "observer_no_exposure_count": sum(1 for row in rows if row.get("paper_shadow_exposure_units") == "0")
        - len(suspend_rows),
        "duplicate_ignored_count": action_counts.get("NO_EXPOSURE_DUPLICATE_IGNORED", 0),
        "conflict_review_count": action_counts.get("NO_EXPOSURE_CONFLICT_REVIEW", 0),
        "estimated_monthly_shadow_open_count": _estimated_monthly_count(would_open_rows),
        "mean_shadow_open_net_r": round(mean(net_values), 4) if net_values else None,
        "action_counts": action_counts,
        "state_counts": state_counts,
        "first_event_time": _first_last_event(rows)[0],
        "last_event_time": _first_last_event(rows)[1],
        "notes": [
            "This is an offline side experiment for controller design.",
            "It must not be interpreted as Phase 2 or real Phase 3 approval.",
            "No runtime, broker, account, or MT5 state is changed by this report.",
        ],
    }


def _render_markdown(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    action_counts = summary.get("action_counts", {})
    state_counts = summary.get("state_counts", {})
    if not isinstance(action_counts, dict):
        action_counts = {}
    if not isinstance(state_counts, dict):
        state_counts = {}
    return "\n".join(
        [
            "# Phase 3 Paper-Shadow Side Experiment",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Boundary",
            "",
            "- This is a repo-only side experiment.",
            "- Real Phase 2 readiness is read as context and is not modified.",
            "- MT5 runtime is not touched.",
            "- Broker-action code is not allowed.",
            "- `demo_authorized` remains `false` in every output row.",
            "",
            "## Summary",
            "",
            _table(
                [
                    ("Real Phase 2 readiness", str(summary.get("real_phase2_readiness", "UNKNOWN"))),
                    ("Source ledger rows", str(summary.get("source_ledger_rows", 0))),
                    ("Primary stream rows", str(summary.get("primary_stream_rows", 0))),
                    ("Would shadow-open", str(summary.get("would_open_count", 0))),
                    ("Would shadow-open with cost review", str(summary.get("would_open_review_count", 0))),
                    ("Blocked by suspend-family rule", str(summary.get("blocked_suspend_count", 0))),
                    ("Observer no-exposure rows", str(summary.get("observer_no_exposure_count", 0))),
                    ("Duplicate ignored", str(summary.get("duplicate_ignored_count", 0))),
                    ("Conflict review", str(summary.get("conflict_review_count", 0))),
                    ("Estimated monthly shadow opens", str(summary.get("estimated_monthly_shadow_open_count", "n/a"))),
                    ("Mean shadow-open net R", str(summary.get("mean_shadow_open_net_r", "n/a"))),
                    ("Demo authorized", str(summary.get("demo_authorized", False))),
                    ("Boundary", str(summary.get("boundary", ""))),
                ]
            ),
            "",
            "## Action Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in action_counts.items())),
            "",
            "## State Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in state_counts.items())),
            "",
            "## Sample Rows",
            "",
            _sample_table(rows[:12]),
            "",
        ]
    )


def _sample_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No rows."
    columns = (
        "paper_shadow_event_id",
        "source_cluster_id",
        "family_event_id",
        "family_event_role",
        "observer",
        "decision_bar_time",
        "direction",
        "kill_rule_state",
        "paper_shadow_state",
        "paper_shadow_action",
        "proxy_cost_r",
        "net_after_proxy_from_gross_r",
    )
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        output.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _estimated_monthly_count(rows: list[dict[str, str]]) -> float | None:
    dates = [_parse_datetime(row.get("decision_bar_time", "")) for row in rows]
    dates = [value for value in dates if value is not None]
    if not dates:
        return None
    first = min(dates)
    last = max(dates)
    days = max((last - first).total_seconds() / 86400.0, 1.0)
    return round(len(rows) / days * 30.0, 2)


def _first_last_event(rows: list[dict[str, str]]) -> tuple[str, str]:
    dates = [_parse_datetime(row.get("decision_bar_time", "")) for row in rows]
    dates = [value for value in dates if value is not None]
    if not dates:
        return "", ""
    return (
        min(dates).isoformat().replace("+00:00", "Z"),
        max(dates).isoformat().replace("+00:00", "Z"),
    )


def _parse_datetime(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    normalized = value.replace(".", "-").replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(normalized, fmt)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHADOW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


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


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    repo_root = phase3_root.parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 paper-shadow side-experiment artifacts.")
    parser.add_argument("--ledger-path", type=Path, default=reports / "PHASE3_EXPERIMENTAL_LEDGER.csv")
    parser.add_argument("--output-dir", type=Path, default=reports)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    args = parser.parse_args(argv)
    path = generate_paper_shadow_experiment(args.ledger_path, args.output_dir, args.repo_root)
    summary = json.loads(path.read_text(encoding="utf-8"))
    print(f"Phase 3 paper-shadow side experiment: {summary['status']}")
    print(path)
    print(
        f"would_open={summary['would_open_count']}; blocked_suspend={summary['blocked_suspend_count']}; "
        f"observer_no_exposure={summary['observer_no_exposure_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
