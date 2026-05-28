from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


LIFECYCLE_SESSION_ID = "phase3-shadow-lifecycle-side-experiment-v0"
SIDE_EXPERIMENT_BOUNDARY = "side_experiment_only_synthetic_lifecycle_no_mt5_touch_no_real_gate_promotion"
OPEN_ACTIONS = {"WOULD_PAPER_SHADOW_OPEN", "WOULD_PAPER_SHADOW_OPEN_REVIEW"}

LIFECYCLE_COLUMNS = (
    "lifecycle_event_id",
    "lifecycle_session_id",
    "paper_shadow_event_id",
    "source_cluster_id",
    "family_event_id",
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
    "input_paper_shadow_action",
    "input_paper_shadow_state",
    "lifecycle_stage",
    "synthetic_open_state",
    "synthetic_close_state",
    "synthetic_close_reason",
    "synthetic_hold_bars",
    "synthetic_gross_r",
    "synthetic_cost_r",
    "synthetic_net_r",
    "running_synthetic_equity_r",
    "running_synthetic_peak_r",
    "running_synthetic_drawdown_r",
    "risk_lock_after_event",
    "kill_rule_state",
    "proxy_cost_r",
    "net_after_proxy_from_gross_r",
    "review_priority",
    "demo_authorized",
    "real_phase2_readiness",
    "blocker_override_mode",
    "mt5_runtime_touched",
    "broker_action_code_allowed",
    "lifecycle_notes",
)


def generate_shadow_lifecycle_experiment(
    shadow_ledger_path: Path,
    output_dir: Path,
) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = _read_csv(shadow_ledger_path)
    lifecycle_rows = _lifecycle_rows(source_rows)
    csv_path = output_dir / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv"
    json_path = output_dir / "PHASE3_SHADOW_LIFECYCLE_SUMMARY.json"
    md_path = output_dir / "PHASE3_SHADOW_LIFECYCLE_SUMMARY.md"
    _write_csv(csv_path, lifecycle_rows)
    summary = _summary(shadow_ledger_path, csv_path, lifecycle_rows)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary, lifecycle_rows), encoding="utf-8")
    return json_path


def _lifecycle_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    running_equity = 0.0
    peak_equity = 0.0
    for index, row in enumerate(source_rows, start=1):
        gross_r, hold_bars, close_state, close_reason, stage, open_state = _synthetic_outcome(index, row)
        cost_r = _to_float(row.get("proxy_cost_r")) or 0.0
        net_r = 0.0 if stage == "NO_EXPOSURE_REVIEW_ONLY" else gross_r - cost_r
        running_equity += net_r
        peak_equity = max(peak_equity, running_equity)
        drawdown = running_equity - peak_equity
        rows.append(
            {
                "lifecycle_event_id": f"PH3LIFE{index:05d}",
                "lifecycle_session_id": LIFECYCLE_SESSION_ID,
                "paper_shadow_event_id": row.get("paper_shadow_event_id", ""),
                "source_cluster_id": row.get("source_cluster_id", ""),
                "family_event_id": row.get("family_event_id", ""),
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
                "input_paper_shadow_action": row.get("paper_shadow_action", ""),
                "input_paper_shadow_state": row.get("paper_shadow_state", ""),
                "lifecycle_stage": stage,
                "synthetic_open_state": open_state,
                "synthetic_close_state": close_state,
                "synthetic_close_reason": close_reason,
                "synthetic_hold_bars": str(hold_bars),
                "synthetic_gross_r": _fmt(gross_r),
                "synthetic_cost_r": _fmt(cost_r if stage != "NO_EXPOSURE_REVIEW_ONLY" else 0.0),
                "synthetic_net_r": _fmt(net_r),
                "running_synthetic_equity_r": _fmt(running_equity),
                "running_synthetic_peak_r": _fmt(peak_equity),
                "running_synthetic_drawdown_r": _fmt(drawdown),
                "risk_lock_after_event": _risk_state(drawdown),
                "kill_rule_state": row.get("kill_rule_state", ""),
                "proxy_cost_r": row.get("proxy_cost_r", ""),
                "net_after_proxy_from_gross_r": row.get("net_after_proxy_from_gross_r", ""),
                "review_priority": row.get("review_priority", ""),
                "demo_authorized": "false",
                "real_phase2_readiness": row.get("real_phase2_readiness", "UNKNOWN"),
                "blocker_override_mode": "side_experiment_only",
                "mt5_runtime_touched": "false",
                "broker_action_code_allowed": "false",
                "lifecycle_notes": _lifecycle_notes(stage, close_reason),
            }
        )
    return rows


def _synthetic_outcome(index: int, row: dict[str, str]) -> tuple[float, int, str, str, str, str]:
    action = row.get("paper_shadow_action", "")
    if action not in OPEN_ACTIONS:
        return (
            0.0,
            0,
            "NO_SYNTHETIC_CLOSE",
            row.get("blocked_reason", "no_exposure_review_only") or "no_exposure_review_only",
            "NO_EXPOSURE_REVIEW_ONLY",
            "NO_SYNTHETIC_OPEN",
        )
    if action == "WOULD_PAPER_SHADOW_OPEN_REVIEW":
        return (
            0.0,
            1,
            "CLOSED_BY_REVIEW",
            "cost_watch_review_exit",
            "OPENED_THEN_REVIEW_CLOSED",
            "SYNTHETIC_OPENED_REVIEW_ONLY",
        )
    cost_r = _to_float(row.get("proxy_cost_r")) or 0.0
    if cost_r >= 0.30:
        return (
            0.25,
            3,
            "CLOSED_BY_COST_DRIFT",
            "cost_drift_exit",
            "OPENED_THEN_COST_DRIFT_CLOSED",
            "SYNTHETIC_OPENED",
        )
    scenario = index % 5
    if scenario == 0:
        return (1.5, 8, "CLOSED_TARGET", "synthetic_target_hit", "OPENED_THEN_CLOSED", "SYNTHETIC_OPENED")
    if scenario == 1:
        return (-1.0, 5, "CLOSED_STOP", "synthetic_stop_hit", "OPENED_THEN_CLOSED", "SYNTHETIC_OPENED")
    if scenario == 2:
        return (0.0, 6, "CLOSED_BREAK_EVEN", "synthetic_break_even", "OPENED_THEN_CLOSED", "SYNTHETIC_OPENED")
    if scenario == 3:
        return (0.35, 12, "CLOSED_TIME_STOP", "synthetic_time_stop_small_win", "OPENED_THEN_CLOSED", "SYNTHETIC_OPENED")
    return (-0.25, 12, "CLOSED_TIME_STOP", "synthetic_time_stop_small_loss", "OPENED_THEN_CLOSED", "SYNTHETIC_OPENED")


def _summary(
    shadow_ledger_path: Path,
    lifecycle_ledger_path: Path,
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    open_rows = [row for row in rows if row.get("synthetic_open_state") != "NO_SYNTHETIC_OPEN"]
    closed_rows = [row for row in open_rows if row.get("synthetic_close_state", "").startswith("CLOSED")]
    net_values = [_to_float(row.get("synthetic_net_r")) for row in open_rows]
    net_values = [value for value in net_values if value is not None]
    gross_values = [_to_float(row.get("synthetic_gross_r")) for row in open_rows]
    gross_values = [value for value in gross_values if value is not None]
    win_count = sum(1 for value in net_values if value > 0)
    loss_count = sum(1 for value in net_values if value < 0)
    final_equity = _to_float(rows[-1].get("running_synthetic_equity_r")) if rows else 0.0
    min_drawdown = min((_to_float(row.get("running_synthetic_drawdown_r")) or 0.0 for row in rows), default=0.0)
    return {
        "status": "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY" if rows else "SIDE_EXPERIMENT_NO_LIFECYCLE_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": SIDE_EXPERIMENT_BOUNDARY,
        "assumption": "assumes_phase2_pass_for_design_only_and_uses_synthetic_not_real_closes",
        "demo_authorized": False,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "blocker_override_mode": "side_experiment_only",
        "shadow_ledger": str(shadow_ledger_path),
        "lifecycle_ledger": str(lifecycle_ledger_path),
        "source_shadow_rows": len(rows),
        "synthetic_open_count": len(open_rows),
        "synthetic_close_count": len(closed_rows),
        "no_exposure_review_only_count": len(rows) - len(open_rows),
        "win_count": win_count,
        "loss_count": loss_count,
        "flat_count": len(net_values) - win_count - loss_count,
        "synthetic_win_rate_pct": round(win_count / len(net_values) * 100.0, 2) if net_values else None,
        "synthetic_total_gross_r": round(sum(gross_values), 4) if gross_values else 0.0,
        "synthetic_total_net_r": round(sum(net_values), 4) if net_values else 0.0,
        "synthetic_mean_net_r": round(mean(net_values), 4) if net_values else None,
        "synthetic_final_equity_r": round(final_equity or 0.0, 4),
        "synthetic_max_drawdown_r": round(min_drawdown, 4),
        "risk_lock_counts": _counts(row.get("risk_lock_after_event", "") for row in rows),
        "close_reason_counts": _counts(row.get("synthetic_close_reason", "") for row in rows),
        "lifecycle_stage_counts": _counts(row.get("lifecycle_stage", "") for row in rows),
        "notes": [
            "This is a deterministic lifecycle stress model, not a backtest and not paper trading.",
            "Synthetic closes are generated from fixed side-experiment rules because no broker execution occurred.",
            "Real promotion still requires a separate owner-approved implementation path.",
        ],
    }


def _render_markdown(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Phase 3 Shadow Lifecycle Side Experiment",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Boundary",
            "",
            "- This is a repo-only synthetic lifecycle experiment.",
            "- It is not a backtest and not paper trading.",
            "- Real Phase 2 readiness is not modified.",
            "- MT5 runtime is not touched.",
            "- Broker-action code is not allowed.",
            "- `demo_authorized` remains `false` in every output row.",
            "",
            "## Summary",
            "",
            _table(
                [
                    ("Source shadow rows", str(summary.get("source_shadow_rows", 0))),
                    ("Synthetic opens", str(summary.get("synthetic_open_count", 0))),
                    ("Synthetic closes", str(summary.get("synthetic_close_count", 0))),
                    ("No-exposure review-only rows", str(summary.get("no_exposure_review_only_count", 0))),
                    ("Synthetic win rate pct", str(summary.get("synthetic_win_rate_pct", "n/a"))),
                    ("Synthetic total gross R", str(summary.get("synthetic_total_gross_r", 0))),
                    ("Synthetic total net R", str(summary.get("synthetic_total_net_r", 0))),
                    ("Synthetic mean net R", str(summary.get("synthetic_mean_net_r", "n/a"))),
                    ("Synthetic final equity R", str(summary.get("synthetic_final_equity_r", 0))),
                    ("Synthetic max drawdown R", str(summary.get("synthetic_max_drawdown_r", 0))),
                    ("Demo authorized", str(summary.get("demo_authorized", False))),
                    ("Boundary", str(summary.get("boundary", ""))),
                ]
            ),
            "",
            "## Lifecycle Stage Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in _mapping(summary.get("lifecycle_stage_counts")).items())),
            "",
            "## Close Reason Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in _mapping(summary.get("close_reason_counts")).items())),
            "",
            "## Risk Lock Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in _mapping(summary.get("risk_lock_counts")).items())),
            "",
            "## Sample Rows",
            "",
            _sample_table(rows[:12]),
            "",
        ]
    )


def _risk_state(drawdown: float) -> str:
    if drawdown <= -5.0:
        return "SYNTHETIC_DAILY_LOCK"
    if drawdown <= -3.0:
        return "SYNTHETIC_DEFENSIVE"
    return "NORMAL"


def _lifecycle_notes(stage: str, close_reason: str) -> str:
    if stage == "NO_EXPOSURE_REVIEW_ONLY":
        return "No synthetic exposure was created; row remains review-only."
    return f"Synthetic lifecycle close reason: {close_reason}. This is not broker or market execution."


def _sample_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No rows."
    columns = (
        "lifecycle_event_id",
        "paper_shadow_event_id",
        "source_cluster_id",
        "decision_bar_time",
        "input_paper_shadow_action",
        "lifecycle_stage",
        "synthetic_close_reason",
        "synthetic_hold_bars",
        "synthetic_net_r",
        "running_synthetic_equity_r",
        "risk_lock_after_event",
    )
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        output.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LIFECYCLE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


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


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 synthetic shadow lifecycle artifacts.")
    parser.add_argument("--shadow-ledger-path", type=Path, default=reports / "PHASE3_PAPER_SHADOW_LEDGER.csv")
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = generate_shadow_lifecycle_experiment(args.shadow_ledger_path, args.output_dir)
    summary = json.loads(path.read_text(encoding="utf-8"))
    print(f"Phase 3 shadow lifecycle side experiment: {summary['status']}")
    print(path)
    print(
        f"synthetic_opens={summary['synthetic_open_count']}; "
        f"synthetic_total_net_r={summary['synthetic_total_net_r']}; "
        f"synthetic_max_drawdown_r={summary['synthetic_max_drawdown_r']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
