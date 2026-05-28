from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


GUARD_SESSION_ID = "phase3-lifecycle-guard-side-experiment-v0"
SIDE_EXPERIMENT_BOUNDARY = "side_experiment_only_guarded_lifecycle_no_mt5_touch_no_real_gate_promotion"
MAX_PROXY_COST_R = 0.30
DAILY_LOCK_R = -2.0
PORTFOLIO_DRAWDOWN_LOCK_R = -4.0

GUARD_COLUMNS = (
    "guard_event_id",
    "guard_session_id",
    "baseline_lifecycle_event_id",
    "paper_shadow_event_id",
    "source_cluster_id",
    "family_event_id",
    "decision_bar_time",
    "broker_day",
    "symbol",
    "direction",
    "input_paper_shadow_action",
    "baseline_lifecycle_stage",
    "baseline_synthetic_open_state",
    "baseline_synthetic_close_reason",
    "baseline_synthetic_net_r",
    "proxy_cost_r",
    "guard_decision",
    "guard_block_reason",
    "guarded_synthetic_net_r",
    "guarded_running_equity_r",
    "guarded_running_peak_r",
    "guarded_running_drawdown_r",
    "guarded_daily_realized_r",
    "daily_lock_active_after_event",
    "portfolio_lock_active_after_event",
    "demo_authorized",
    "blocker_override_mode",
    "mt5_runtime_touched",
    "broker_action_code_allowed",
    "guard_notes",
)


def generate_lifecycle_guard_experiment(
    lifecycle_ledger_path: Path,
    output_dir: Path,
) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = _read_csv(lifecycle_ledger_path)
    guard_rows = _guard_rows(source_rows)
    csv_path = output_dir / "PHASE3_LIFECYCLE_GUARD_LEDGER.csv"
    json_path = output_dir / "PHASE3_LIFECYCLE_GUARD_SUMMARY.json"
    md_path = output_dir / "PHASE3_LIFECYCLE_GUARD_SUMMARY.md"
    _write_csv(csv_path, guard_rows)
    summary = _summary(lifecycle_ledger_path, csv_path, source_rows, guard_rows)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary, guard_rows), encoding="utf-8")
    return json_path


def _guard_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    running_equity = 0.0
    peak_equity = 0.0
    current_day = ""
    daily_realized = 0.0
    daily_locked = False
    portfolio_locked = False
    for index, row in enumerate(source_rows, start=1):
        broker_day = _broker_day(row.get("decision_bar_time", ""))
        if broker_day and broker_day != current_day:
            current_day = broker_day
            daily_realized = 0.0
            daily_locked = False
        baseline_net = _to_float(row.get("synthetic_net_r")) or 0.0
        proxy_cost = _to_float(row.get("proxy_cost_r")) or 0.0
        drawdown_before = running_equity - peak_equity
        decision, block_reason = _guard_decision(
            row,
            proxy_cost,
            daily_locked,
            portfolio_locked,
            daily_realized,
            drawdown_before,
        )
        guarded_net = baseline_net if decision == "GUARDED_SYNTHETIC_OPEN" else 0.0
        running_equity += guarded_net
        daily_realized += guarded_net
        peak_equity = max(peak_equity, running_equity)
        drawdown = running_equity - peak_equity
        if daily_realized <= DAILY_LOCK_R:
            daily_locked = True
        if drawdown <= PORTFOLIO_DRAWDOWN_LOCK_R:
            portfolio_locked = True
        rows.append(
            {
                "guard_event_id": f"PH3GUARD{index:05d}",
                "guard_session_id": GUARD_SESSION_ID,
                "baseline_lifecycle_event_id": row.get("lifecycle_event_id", ""),
                "paper_shadow_event_id": row.get("paper_shadow_event_id", ""),
                "source_cluster_id": row.get("source_cluster_id", ""),
                "family_event_id": row.get("family_event_id", ""),
                "decision_bar_time": row.get("decision_bar_time", ""),
                "broker_day": broker_day,
                "symbol": row.get("symbol", ""),
                "direction": row.get("direction", ""),
                "input_paper_shadow_action": row.get("input_paper_shadow_action", ""),
                "baseline_lifecycle_stage": row.get("lifecycle_stage", ""),
                "baseline_synthetic_open_state": row.get("synthetic_open_state", ""),
                "baseline_synthetic_close_reason": row.get("synthetic_close_reason", ""),
                "baseline_synthetic_net_r": row.get("synthetic_net_r", ""),
                "proxy_cost_r": row.get("proxy_cost_r", ""),
                "guard_decision": decision,
                "guard_block_reason": block_reason,
                "guarded_synthetic_net_r": _fmt(guarded_net),
                "guarded_running_equity_r": _fmt(running_equity),
                "guarded_running_peak_r": _fmt(peak_equity),
                "guarded_running_drawdown_r": _fmt(drawdown),
                "guarded_daily_realized_r": _fmt(daily_realized),
                "daily_lock_active_after_event": str(daily_locked).lower(),
                "portfolio_lock_active_after_event": str(portfolio_locked).lower(),
                "demo_authorized": "false",
                "blocker_override_mode": "side_experiment_only",
                "mt5_runtime_touched": "false",
                "broker_action_code_allowed": "false",
                "guard_notes": _guard_notes(decision, block_reason),
            }
        )
    return rows


def _guard_decision(
    row: dict[str, str],
    proxy_cost_r: float,
    daily_locked: bool,
    portfolio_locked: bool,
    daily_realized_r: float,
    drawdown_before_r: float,
) -> tuple[str, str]:
    if row.get("synthetic_open_state") == "NO_SYNTHETIC_OPEN":
        return "NO_EXPOSURE_REVIEW_ONLY", "baseline_no_exposure"
    if portfolio_locked:
        return "BLOCKED_PORTFOLIO_LOCK", "portfolio_drawdown_lock_active"
    if daily_locked:
        return "BLOCKED_DAILY_LOCK", "daily_loss_lock_active"
    if row.get("input_paper_shadow_action") == "WOULD_PAPER_SHADOW_OPEN_REVIEW":
        return "BLOCKED_COST_WATCH", "cost_watch_requires_review_before_exposure"
    if proxy_cost_r >= MAX_PROXY_COST_R:
        return "BLOCKED_COST_R", "proxy_cost_r_at_or_above_0_30"
    estimated_worst_case_r = -1.0 - proxy_cost_r
    if daily_realized_r + estimated_worst_case_r <= DAILY_LOCK_R:
        return "BLOCKED_DAILY_BUDGET", "daily_worst_case_loss_budget_would_breach"
    if drawdown_before_r + estimated_worst_case_r <= PORTFOLIO_DRAWDOWN_LOCK_R:
        return "BLOCKED_PORTFOLIO_BUDGET", "portfolio_worst_case_loss_budget_would_breach"
    return "GUARDED_SYNTHETIC_OPEN", ""


def _summary(
    lifecycle_ledger_path: Path,
    guard_ledger_path: Path,
    baseline_rows: list[dict[str, str]],
    guard_rows: list[dict[str, str]],
) -> dict[str, Any]:
    baseline_open_rows = [row for row in baseline_rows if row.get("synthetic_open_state") != "NO_SYNTHETIC_OPEN"]
    guarded_open_rows = [row for row in guard_rows if row.get("guard_decision") == "GUARDED_SYNTHETIC_OPEN"]
    baseline_net_values = [_to_float(row.get("synthetic_net_r")) for row in baseline_open_rows]
    baseline_net_values = [value for value in baseline_net_values if value is not None]
    guarded_net_values = [_to_float(row.get("guarded_synthetic_net_r")) for row in guarded_open_rows]
    guarded_net_values = [value for value in guarded_net_values if value is not None]
    baseline_total = sum(baseline_net_values)
    guarded_total = sum(guarded_net_values)
    baseline_dd = min((_to_float(row.get("running_synthetic_drawdown_r")) or 0.0 for row in baseline_rows), default=0.0)
    guarded_dd = min((_to_float(row.get("guarded_running_drawdown_r")) or 0.0 for row in guard_rows), default=0.0)
    guarded_wins = sum(1 for value in guarded_net_values if value > 0)
    guarded_losses = sum(1 for value in guarded_net_values if value < 0)
    return {
        "status": "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY" if guard_rows else "SIDE_EXPERIMENT_NO_GUARD_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": SIDE_EXPERIMENT_BOUNDARY,
        "assumption": "assumes_phase2_pass_for_design_only_and_blocks_exposure_with_guard_rules",
        "demo_authorized": False,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "blocker_override_mode": "side_experiment_only",
        "max_proxy_cost_r": MAX_PROXY_COST_R,
        "daily_lock_r": DAILY_LOCK_R,
        "portfolio_drawdown_lock_r": PORTFOLIO_DRAWDOWN_LOCK_R,
        "baseline_lifecycle_ledger": str(lifecycle_ledger_path),
        "guard_ledger": str(guard_ledger_path),
        "baseline_open_count": len(baseline_open_rows),
        "guarded_open_count": len(guarded_open_rows),
        "blocked_count": sum(1 for row in guard_rows if row.get("guard_decision", "").startswith("BLOCKED")),
        "no_exposure_review_only_count": sum(1 for row in guard_rows if row.get("guard_decision") == "NO_EXPOSURE_REVIEW_ONLY"),
        "baseline_total_net_r": round(baseline_total, 4),
        "guarded_total_net_r": round(guarded_total, 4),
        "net_improvement_r": round(guarded_total - baseline_total, 4),
        "baseline_max_drawdown_r": round(baseline_dd, 4),
        "guarded_max_drawdown_r": round(guarded_dd, 4),
        "drawdown_improvement_r": round(guarded_dd - baseline_dd, 4),
        "guarded_win_count": guarded_wins,
        "guarded_loss_count": guarded_losses,
        "guarded_win_rate_pct": round(guarded_wins / len(guarded_net_values) * 100.0, 2) if guarded_net_values else None,
        "guarded_mean_net_r": round(mean(guarded_net_values), 4) if guarded_net_values else None,
        "guard_decision_counts": _counts(row.get("guard_decision", "") for row in guard_rows),
        "guard_block_reason_counts": _counts(row.get("guard_block_reason", "") for row in guard_rows),
        "notes": [
            "This is a controller-design experiment, not a claim of live or paper profitability.",
            "The guard layer improves the harsh synthetic lifecycle by refusing cost-watch, high-cost, and risk-locked exposure.",
            "The real implementation path still requires separate authorization.",
        ],
    }


def _render_markdown(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Phase 3 Guarded Lifecycle Side Experiment",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Boundary",
            "",
            "- This is a repo-only controller-design experiment.",
            "- It compares guarded synthetic exposure against the harsh lifecycle stress model.",
            "- Real Phase 2 readiness is not modified.",
            "- MT5 runtime is not touched.",
            "- Broker-action code is not allowed.",
            "- `demo_authorized` remains `false` in every output row.",
            "",
            "## Guard Rules",
            "",
            _table(
                [
                    ("Max proxy cost R", str(summary.get("max_proxy_cost_r"))),
                    ("Daily lock R", str(summary.get("daily_lock_r"))),
                    ("Portfolio drawdown lock R", str(summary.get("portfolio_drawdown_lock_r"))),
                    ("Worst-case budget check", "blocks if a new -1R minus cost outcome would breach daily or portfolio limits"),
                    ("Cost-watch rows", "blocked before synthetic exposure"),
                    ("No-exposure rows", "kept review-only"),
                ]
            ),
            "",
            "## A/B Summary",
            "",
            _table(
                [
                    ("Baseline opens", str(summary.get("baseline_open_count", 0))),
                    ("Guarded opens", str(summary.get("guarded_open_count", 0))),
                    ("Blocked rows", str(summary.get("blocked_count", 0))),
                    ("Baseline total net R", str(summary.get("baseline_total_net_r", 0))),
                    ("Guarded total net R", str(summary.get("guarded_total_net_r", 0))),
                    ("Net improvement R", str(summary.get("net_improvement_r", 0))),
                    ("Baseline max DD R", str(summary.get("baseline_max_drawdown_r", 0))),
                    ("Guarded max DD R", str(summary.get("guarded_max_drawdown_r", 0))),
                    ("Drawdown improvement R", str(summary.get("drawdown_improvement_r", 0))),
                    ("Guarded win rate pct", str(summary.get("guarded_win_rate_pct", "n/a"))),
                    ("Demo authorized", str(summary.get("demo_authorized", False))),
                ]
            ),
            "",
            "## Guard Decision Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in _mapping(summary.get("guard_decision_counts")).items())),
            "",
            "## Block Reason Counts",
            "",
            _table(sorted((str(key), str(value)) for key, value in _mapping(summary.get("guard_block_reason_counts")).items())),
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
        "guard_event_id",
        "source_cluster_id",
        "decision_bar_time",
        "input_paper_shadow_action",
        "baseline_synthetic_net_r",
        "guard_decision",
        "guard_block_reason",
        "guarded_synthetic_net_r",
        "guarded_running_drawdown_r",
        "daily_lock_active_after_event",
        "portfolio_lock_active_after_event",
    )
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        output.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _guard_notes(decision: str, block_reason: str) -> str:
    if decision == "GUARDED_SYNTHETIC_OPEN":
        return "Guard allowed synthetic exposure in this side experiment."
    if decision == "NO_EXPOSURE_REVIEW_ONLY":
        return "No synthetic exposure was available from the paper-shadow layer."
    return f"Guard blocked synthetic exposure: {block_reason}."


def _broker_day(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    return value[:10]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GUARD_COLUMNS)
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
    parser = argparse.ArgumentParser(description="Generate Phase 3 guarded lifecycle artifacts.")
    parser.add_argument("--lifecycle-ledger-path", type=Path, default=reports / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv")
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = generate_lifecycle_guard_experiment(args.lifecycle_ledger_path, args.output_dir)
    summary = json.loads(path.read_text(encoding="utf-8"))
    print(f"Phase 3 lifecycle guard side experiment: {summary['status']}")
    print(path)
    print(
        f"guarded_opens={summary['guarded_open_count']}; "
        f"guarded_total_net_r={summary['guarded_total_net_r']}; "
        f"guarded_max_drawdown_r={summary['guarded_max_drawdown_r']}; "
        f"net_improvement_r={summary['net_improvement_r']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
