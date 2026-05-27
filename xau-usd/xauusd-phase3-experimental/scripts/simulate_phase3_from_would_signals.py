from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median


BASELINE_NET_EXPECTANCY_R = 0.1888
BASELINE_MODELED_COST_R = 0.3228
BASELINE_GROSS_EDGE_R = BASELINE_NET_EXPECTANCY_R + BASELINE_MODELED_COST_R
MINIMUM_NET_EXPECTANCY_R = 0.15
DEFAULT_SLIPPAGE_POINTS = 5.0
EXPERIMENTAL_SESSION_ID = "phase3-experimental-offline-v0"

LEDGER_COLUMNS = (
    "event_id",
    "experimental_session_id",
    "source_cluster_id",
    "source_run_id",
    "timestamp_broker",
    "timestamp_utc",
    "timestamp_local",
    "symbol",
    "expert_family",
    "observer",
    "decision_bar_time",
    "experimental_event_type",
    "experimental_state",
    "direction",
    "level_kind",
    "level_price",
    "entry_price_projected",
    "stop_price_projected",
    "target_price_projected",
    "stop_distance_points",
    "risk_state",
    "execution_state",
    "server_time_status",
    "spread_points",
    "slippage_points_assumed",
    "modeled_cost_r",
    "measured_cost_r_proxy",
    "net_expectancy_r_baseline",
    "net_expectancy_r_after_proxy_cost",
    "kill_rule_state",
    "source_trade_permission",
    "source_dry_run",
    "source_reason_code",
    "review_status",
    "review_notes",
)


@dataclass(frozen=True)
class SimulationOutput:
    status: str
    ledger_path: Path
    report_path: Path
    summary_path: Path
    accepted_events: int
    rejected_source_rows: int


def simulate_phase3_from_would_signals(
    input_csv: Path,
    output_dir: Path,
    slippage_points: float = DEFAULT_SLIPPAGE_POINTS,
) -> SimulationOutput:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_csv(input_csv)
    ledger_rows: list[dict[str, str]] = []
    rejected_source_rows = 0
    for row in rows:
        if not _source_row_is_safe(row):
            rejected_source_rows += 1
            continue
        event_index = len(ledger_rows) + 1
        ledger_rows.append(_ledger_row(event_index, row, slippage_points))

    ledger_path = output_dir / "PHASE3_EXPERIMENTAL_LEDGER.csv"
    report_path = output_dir / "PHASE3_EXPERIMENTAL_SIMULATION.md"
    summary_path = output_dir / "PHASE3_EXPERIMENTAL_SIMULATION.json"
    _write_csv(ledger_path, ledger_rows)
    summary = _summary(input_csv, ledger_path, ledger_rows, rejected_source_rows, slippage_points)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_render_report(summary, ledger_rows), encoding="utf-8")
    return SimulationOutput(
        status=summary["status"],
        ledger_path=ledger_path,
        report_path=report_path,
        summary_path=summary_path,
        accepted_events=len(ledger_rows),
        rejected_source_rows=rejected_source_rows,
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _source_row_is_safe(row: dict[str, str]) -> bool:
    return (
        row.get("dry_run", "").lower() == "true"
        and row.get("trade_permission", "").lower() == "false"
        and row.get("server_time_status", "") == "CLOCK_OK"
        and row.get("execution_state", "") == "EXECUTION_OK"
        and row.get("risk_state", "") == "NORMAL"
    )


def _ledger_row(index: int, row: dict[str, str], slippage_points: float) -> dict[str, str]:
    spread_points = _to_float(row.get("spread_points")) or 0.0
    stop_distance = _to_float(row.get("stop_distance_points")) or 0.0
    measured_cost_r_proxy = ((spread_points + slippage_points) / stop_distance) if stop_distance > 0 else 999.0
    net_after_proxy = BASELINE_GROSS_EDGE_R - measured_cost_r_proxy
    return {
        "event_id": f"PH3EXP{index:05d}",
        "experimental_session_id": EXPERIMENTAL_SESSION_ID,
        "source_cluster_id": row.get("cluster_id", ""),
        "source_run_id": row.get("run_id", ""),
        "timestamp_broker": row.get("timestamp_broker", ""),
        "timestamp_utc": row.get("timestamp_utc", ""),
        "timestamp_local": row.get("timestamp_local", ""),
        "symbol": row.get("symbol", ""),
        "expert_family": "breakout_retest_family",
        "observer": row.get("observer", ""),
        "decision_bar_time": row.get("bar_time", ""),
        "experimental_event_type": "WOULD_OPEN",
        "experimental_state": "EXPERIMENT_ONLY",
        "direction": row.get("direction", ""),
        "level_kind": row.get("level_kind", ""),
        "level_price": row.get("level_price", ""),
        "entry_price_projected": row.get("entry_price", ""),
        "stop_price_projected": row.get("stop_loss", ""),
        "target_price_projected": row.get("take_profit", ""),
        "stop_distance_points": _fmt(stop_distance),
        "risk_state": row.get("risk_state", ""),
        "execution_state": row.get("execution_state", ""),
        "server_time_status": row.get("server_time_status", ""),
        "spread_points": _fmt(spread_points),
        "slippage_points_assumed": _fmt(slippage_points),
        "modeled_cost_r": _fmt(BASELINE_MODELED_COST_R),
        "measured_cost_r_proxy": _fmt(measured_cost_r_proxy),
        "net_expectancy_r_baseline": _fmt(BASELINE_NET_EXPECTANCY_R),
        "net_expectancy_r_after_proxy_cost": _fmt(net_after_proxy),
        "kill_rule_state": _kill_rule_state(net_after_proxy),
        "source_trade_permission": row.get("trade_permission", ""),
        "source_dry_run": row.get("dry_run", ""),
        "source_reason_code": row.get("reason_code", ""),
        "review_status": "PENDING",
        "review_notes": "Offline Phase 3 experiment generated from blocked Phase 1 would-signal evidence.",
    }


def _kill_rule_state(net_after_proxy: float) -> str:
    if net_after_proxy < MINIMUM_NET_EXPECTANCY_R:
        return "SUSPEND_FAMILY"
    if net_after_proxy < BASELINE_NET_EXPECTANCY_R:
        return "COST_WATCH"
    return "NORMAL"


def _summary(
    input_csv: Path,
    ledger_path: Path,
    ledger_rows: list[dict[str, str]],
    rejected_source_rows: int,
    slippage_points: float,
) -> dict[str, object]:
    costs = [_to_float(row.get("measured_cost_r_proxy")) for row in ledger_rows]
    costs = [value for value in costs if value is not None]
    net_values = [_to_float(row.get("net_expectancy_r_after_proxy_cost")) for row in ledger_rows]
    net_values = [value for value in net_values if value is not None]
    kill_counts = _counts(row.get("kill_rule_state", "") for row in ledger_rows)
    return {
        "status": "EXPERIMENTAL_ACTIVE",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": "repo_only_no_mt5_deployment_no_phase2_status_change",
        "phase2_assumption": "assumes_phase2_pass_for_design_only",
        "real_phase2_status": "unchanged_pending",
        "input_csv": str(input_csv),
        "ledger_path": str(ledger_path),
        "accepted_events": len(ledger_rows),
        "rejected_source_rows": rejected_source_rows,
        "baseline_gross_edge_r": round(BASELINE_GROSS_EDGE_R, 4),
        "baseline_net_expectancy_r": BASELINE_NET_EXPECTANCY_R,
        "baseline_modeled_cost_r": BASELINE_MODELED_COST_R,
        "minimum_net_expectancy_r": MINIMUM_NET_EXPECTANCY_R,
        "slippage_points_assumed": slippage_points,
        "median_proxy_cost_r": round(median(costs), 4) if costs else None,
        "mean_proxy_cost_r": round(mean(costs), 4) if costs else None,
        "median_net_after_proxy_cost_r": round(median(net_values), 4) if net_values else None,
        "mean_net_after_proxy_cost_r": round(mean(net_values), 4) if net_values else None,
        "kill_rule_counts": kill_counts,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
    }


def _render_report(summary: dict[str, object], ledger_rows: list[dict[str, str]]) -> str:
    kill_counts = summary.get("kill_rule_counts", {})
    if not isinstance(kill_counts, dict):
        kill_counts = {}
    return "\n".join(
        [
            "# Phase 3 Experimental Offline Simulation",
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Boundary",
            "",
            "- This is a repo-only experiment.",
            "- Real Phase 2 readiness remains unchanged.",
            "- The live MT5 dry-run and passive spread logger are not modified.",
            "- No broker-action path is implemented or authorized.",
            "",
            "## Summary",
            "",
            _markdown_table(
                [
                    ("Accepted events", str(summary["accepted_events"])),
                    ("Rejected source rows", str(summary["rejected_source_rows"])),
                    ("Baseline net expectancy R", str(summary["baseline_net_expectancy_r"])),
                    ("Median proxy cost R", str(summary["median_proxy_cost_r"])),
                    ("Median net after proxy cost R", str(summary["median_net_after_proxy_cost_r"])),
                    ("Minimum net expectancy R", str(summary["minimum_net_expectancy_r"])),
                ]
            ),
            "",
            "## Kill Rule Counts",
            "",
            _markdown_table(sorted((key, str(value)) for key, value in kill_counts.items())),
            "",
            "## Sample Events",
            "",
            _event_table(ledger_rows[:10]),
            "",
        ]
    )


def _event_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No rows."
    columns = (
        "event_id",
        "observer",
        "decision_bar_time",
        "direction",
        "measured_cost_r_proxy",
        "net_expectancy_r_after_proxy_cost",
        "kill_rule_state",
    )
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _markdown_table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Metric | Value |", "| --- | --- |", *body])


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


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    repo_root = phase3_root.parents[1]
    parser = argparse.ArgumentParser(description="Generate an offline Phase 3 experimental ledger.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_WOULD_SIGNAL_REVIEW.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=phase3_root / "outputs" / "reports")
    parser.add_argument("--slippage-points", type=float, default=DEFAULT_SLIPPAGE_POINTS)
    args = parser.parse_args(argv)

    output = simulate_phase3_from_would_signals(args.input_csv, args.output_dir, args.slippage_points)
    print(f"Phase 3 experimental simulation: {output.status}")
    print(output.report_path)
    print(f"accepted_events={output.accepted_events}; rejected_source_rows={output.rejected_source_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
