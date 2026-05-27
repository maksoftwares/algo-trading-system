from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any


BASELINE_NET_EXPECTANCY_R = 0.1888
BASELINE_ASSUMED_COST_R = 0.3228
BASELINE_GROSS_EDGE_R = BASELINE_NET_EXPECTANCY_R + BASELINE_ASSUMED_COST_R
GROSS_EXPECTANCY_R_SOURCE = "fixed_notional_phase0_baseline"
MINIMUM_NET_EXPECTANCY_R = 0.15
MAX_COST_PROXY_R = BASELINE_GROSS_EDGE_R - MINIMUM_NET_EXPECTANCY_R
PHASE2_AUTHORITY_SENTENCE = (
    "This report has no authority over Phase 2 readiness. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)


def analyze_suspend_family(
    ledger_path: Path,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_csv(ledger_path)
    suspend_rows = [row for row in rows if row.get("kill_rule_state") == "SUSPEND_FAMILY"]
    enriched = [_enrich(row) for row in suspend_rows]
    summary = _summary(ledger_path, rows, enriched)
    json_path = output_dir / "PHASE3_SUSPEND_FAMILY_REVIEW.json"
    md_path = output_dir / "PHASE3_SUSPEND_FAMILY_REVIEW.md"
    csv_path = output_dir / "PHASE3_SUSPEND_FAMILY_ROWS.csv"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_csv(csv_path, enriched)
    md_path.write_text(_render_markdown(summary, enriched), encoding="utf-8")
    return json_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "event_id",
        "family_event_id",
        "family_event_role",
        "primary_stream_allowed",
        "observer",
        "decision_bar_time",
        "direction",
        "level_kind",
        "spread_points",
        "total_cost_points",
        "stop_distance_points",
        "measured_cost_r_proxy",
        "net_expectancy_r_after_proxy_cost",
        "gross_expectancy_r_source",
        "baseline_assumed_cost_r",
        "baseline_net_expectancy_r",
        "proxy_cost_r",
        "net_after_proxy_from_gross_r",
        "net_delta_vs_assumed_baseline_r",
        "cost_excess_r",
        "cost_excess_points",
        "diagnosis",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _enrich(row: dict[str, str]) -> dict[str, Any]:
    stop_distance = _to_float(row.get("stop_distance_points")) or 0.0
    cost_points = _to_float(row.get("total_cost_points")) or 0.0
    cost_r = _to_float(row.get("measured_cost_r_proxy")) or 0.0
    net_after_proxy = _to_float(row.get("net_expectancy_r_after_proxy_cost")) or 0.0
    threshold_points = MAX_COST_PROXY_R * stop_distance
    diagnosis = _diagnosis(row, stop_distance, cost_points)
    return {
        "event_id": row.get("event_id", ""),
        "family_event_id": row.get("family_event_id", ""),
        "family_event_role": row.get("family_event_role", ""),
        "primary_stream_allowed": row.get("primary_stream_allowed", ""),
        "observer": row.get("observer", ""),
        "decision_bar_time": row.get("decision_bar_time", ""),
        "direction": row.get("direction", ""),
        "level_kind": row.get("level_kind", ""),
        "spread_points": _fmt(_to_float(row.get("spread_points")) or 0.0),
        "total_cost_points": _fmt(cost_points),
        "stop_distance_points": _fmt(stop_distance),
        "measured_cost_r_proxy": _fmt(cost_r),
        "net_expectancy_r_after_proxy_cost": _fmt(net_after_proxy),
        "gross_expectancy_r_source": row.get("gross_expectancy_r_source", GROSS_EXPECTANCY_R_SOURCE),
        "baseline_assumed_cost_r": row.get("baseline_assumed_cost_r", _fmt(BASELINE_ASSUMED_COST_R)),
        "baseline_net_expectancy_r": row.get("baseline_net_expectancy_r", _fmt(BASELINE_NET_EXPECTANCY_R)),
        "proxy_cost_r": row.get("proxy_cost_r", _fmt(cost_r)),
        "net_after_proxy_from_gross_r": row.get("net_after_proxy_from_gross_r", _fmt(net_after_proxy)),
        "net_delta_vs_assumed_baseline_r": row.get(
            "net_delta_vs_assumed_baseline_r",
            _fmt(net_after_proxy - BASELINE_NET_EXPECTANCY_R),
        ),
        "cost_excess_r": _fmt(max(0.0, cost_r - MAX_COST_PROXY_R)),
        "cost_excess_points": _fmt(max(0.0, cost_points - threshold_points)),
        "diagnosis": diagnosis,
    }


def _diagnosis(row: dict[str, str], stop_distance: float, cost_points: float) -> str:
    spread = _to_float(row.get("spread_points")) or 0.0
    if stop_distance <= 225:
        return "tight_stop_cost_dominates"
    if spread >= 75:
        return "wide_spread_plus_entry_exit_cost"
    if cost_points >= 150:
        return "entry_exit_cost_high_for_stop"
    return "normal_spread_small_stop"


def _summary(
    ledger_path: Path,
    all_rows: list[dict[str, str]],
    suspend_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    primary_rows = [row for row in suspend_rows if row.get("primary_stream_allowed") == "true"]
    family_ids = {str(row.get("family_event_id", "")) for row in suspend_rows if row.get("family_event_id")}
    primary_family_ids = {str(row.get("family_event_id", "")) for row in primary_rows if row.get("family_event_id")}
    cost_values = [_to_float(row.get("measured_cost_r_proxy")) for row in suspend_rows]
    cost_values = [value for value in cost_values if value is not None]
    delta_values = [_to_float(row.get("net_delta_vs_assumed_baseline_r")) for row in suspend_rows]
    delta_values = [value for value in delta_values if value is not None]
    stop_values = [_to_float(row.get("stop_distance_points")) for row in suspend_rows]
    stop_values = [value for value in stop_values if value is not None]
    return {
        "status": "REVIEW_READY",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "ledger_path": str(ledger_path),
        "raw_ledger_rows": len(all_rows),
        "suspend_raw_rows": len(suspend_rows),
        "suspend_unique_family_events": len(family_ids),
        "suspend_primary_rows": len(primary_rows),
        "suspend_primary_family_events": len(primary_family_ids),
        "suspend_duplicate_rows": len(suspend_rows) - len(primary_rows),
        "gross_expectancy_r_source": GROSS_EXPECTANCY_R_SOURCE,
        "baseline_assumed_cost_r": BASELINE_ASSUMED_COST_R,
        "baseline_net_expectancy_r": BASELINE_NET_EXPECTANCY_R,
        "baseline_gross_edge_r": round(BASELINE_GROSS_EDGE_R, 4),
        "max_cost_proxy_r_before_suspend": round(MAX_COST_PROXY_R, 4),
        "minimum_net_expectancy_r": MINIMUM_NET_EXPECTANCY_R,
        "median_suspend_cost_r": round(median(cost_values), 4) if cost_values else None,
        "mean_suspend_cost_r": round(mean(cost_values), 4) if cost_values else None,
        "median_suspend_net_delta_vs_assumed_baseline_r": round(median(delta_values), 4) if delta_values else None,
        "median_suspend_stop_distance_points": round(median(stop_values), 4) if stop_values else None,
        "diagnosis_counts": _counts(row.get("diagnosis", "") for row in suspend_rows),
        "role_counts": _counts(row.get("family_event_role", "") for row in suspend_rows),
        "observer_counts": _counts(row.get("observer", "") for row in suspend_rows),
        "direction_counts": _counts(row.get("direction", "") for row in suspend_rows),
        "level_kind_counts": _counts(row.get("level_kind", "") for row in suspend_rows),
        "recommendation": (
            "Do not promote these rows into real execution. If Phase 2 later passes, use this review "
            "to require cost-aware entry blocking before any paper-mode order path is considered."
        ),
    }


def _render_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# Phase 3 Suspend Family Review",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Summary",
            "",
            _table(
                [
                    ("Raw ledger rows", str(summary["raw_ledger_rows"])),
                    ("Suspend raw rows", str(summary["suspend_raw_rows"])),
                    ("Suspend unique family events", str(summary["suspend_unique_family_events"])),
                    ("Suspend primary rows", str(summary["suspend_primary_rows"])),
                    ("Suspend duplicate observer rows", str(summary["suspend_duplicate_rows"])),
                    ("Gross expectancy R source", str(summary["gross_expectancy_r_source"])),
                    ("Baseline assumed cost R", str(summary["baseline_assumed_cost_r"])),
                    ("Baseline net expectancy R", str(summary["baseline_net_expectancy_r"])),
                    ("Max cost proxy R before suspend", str(summary["max_cost_proxy_r_before_suspend"])),
                    ("Median suspend cost R", str(summary["median_suspend_cost_r"])),
                    (
                        "Median suspend net delta vs assumed baseline R",
                        str(summary["median_suspend_net_delta_vs_assumed_baseline_r"]),
                    ),
                    ("Median suspend stop distance points", str(summary["median_suspend_stop_distance_points"])),
                ]
            ),
            "",
            "## Cost Semantics",
            "",
            "Suspension rows are identified from baseline gross expectancy minus the Phase 3 proxy cost. The delta column is the proxy-based net minus the Phase 0 assumed-cost baseline net; it is a design stress signal, not Phase 2 readiness evidence.",
            "",
            "## Diagnosis Counts",
            "",
            _table(sorted((key, str(value)) for key, value in summary["diagnosis_counts"].items())),
            "",
            "## Role Counts",
            "",
            _table(sorted((key, str(value)) for key, value in summary["role_counts"].items())),
            "",
            "## Highest Cost Suspensions",
            "",
            _event_table(sorted(rows, key=lambda row: float(row["measured_cost_r_proxy"]), reverse=True)[:12]),
            "",
            "## Recommendation",
            "",
            str(summary["recommendation"]),
            "",
        ]
    )


def _event_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No suspended rows."
    columns = [
        "event_id",
        "family_event_id",
        "family_event_role",
        "observer",
        "decision_bar_time",
        "direction",
        "total_cost_points",
        "stop_distance_points",
        "measured_cost_r_proxy",
        "net_delta_vs_assumed_baseline_r",
        "cost_excess_r",
        "diagnosis",
    ]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _counts(values) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for value in values:
        counts[str(value) or "blank"] += 1
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
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Analyze Phase 3 SUSPEND_FAMILY rows.")
    parser.add_argument("--ledger-path", type=Path, default=reports / "PHASE3_EXPERIMENTAL_LEDGER.csv")
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = analyze_suspend_family(args.ledger_path, args.output_dir)
    print(f"Phase 3 suspend-family review: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
