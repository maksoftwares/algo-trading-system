from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from simulate_phase3_from_would_signals import PHASE2_AUTHORITY_SENTENCE


COST_GATE_THRESHOLDS_R = (0.20, 0.25, 0.30, 0.35)
STOP_DISTANCE_BUCKETS = (
    ("0_to_249", 0.0, 250.0),
    ("250_to_499", 250.0, 500.0),
    ("500_to_749", 500.0, 750.0),
    ("750_plus", 750.0, None),
)
REVIEW_ANNOTATION_OPTIONS = (
    "COST_ISSUE",
    "TIGHT_STOP_ISSUE",
    "TIMING_ISSUE",
    "DUPLICATED_OBSERVER_ISSUE",
    "UNKNOWN",
)


def generate_cost_gate_review(ledger_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_csv(ledger_path)
    thresholds = [_threshold_row(threshold, rows) for threshold in COST_GATE_THRESHOLDS_R]
    stop_buckets = [_bucket_row(name, _rows_in_stop_bucket(rows, lower, upper)) for name, lower, upper in STOP_DISTANCE_BUCKETS]
    spread_median, spread_p95 = _spread_thresholds(rows)
    spread_buckets = [
        _bucket_row(f"spread_lte_median_{_fmt_label(spread_median)}", _rows_in_spread_bucket(rows, None, spread_median)),
        _bucket_row(
            f"spread_median_to_p95_{_fmt_label(spread_median)}_{_fmt_label(spread_p95)}",
            _rows_in_spread_bucket(rows, spread_median, spread_p95),
        ),
        _bucket_row(f"spread_gt_p95_{_fmt_label(spread_p95)}", _rows_in_spread_bucket(rows, spread_p95, None)),
    ]
    kill_states = [_kill_state_row(state, state_rows) for state, state_rows in _grouped(rows, "kill_rule_state").items()]
    summary = {
        "status": "REVIEW_READY",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "ledger_path": str(ledger_path),
        "raw_ledger_rows": len(rows),
        "family_unique_events": _family_count(rows),
        "primary_rows": _primary_count(rows),
        "cost_gate_thresholds_r": list(COST_GATE_THRESHOLDS_R),
        "spread_median_points": spread_median,
        "spread_p95_points": spread_p95,
        "review_annotation_options": list(REVIEW_ANNOTATION_OPTIONS),
        "threshold_rows": thresholds,
        "stop_distance_bucket_rows": stop_buckets,
        "spread_regime_bucket_rows": spread_buckets,
        "kill_state_rows": kill_states,
    }
    csv_path = output_dir / "PHASE3_COST_GATE_REVIEW.csv"
    md_path = output_dir / "PHASE3_COST_GATE_REVIEW.md"
    json_path = output_dir / "PHASE3_COST_GATE_REVIEW.json"
    _write_csv(csv_path, thresholds, stop_buckets, spread_buckets, kill_states)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    return json_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _threshold_row(threshold_r: float, rows: list[dict[str, str]]) -> dict[str, Any]:
    blocked = [row for row in rows if (_to_float(row.get("proxy_cost_r")) or 0.0) > threshold_r]
    summary = _row_summary(blocked)
    return {
        "section": "cost_gate_threshold",
        "bucket": f"proxy_cost_gt_{threshold_r:.2f}R",
        "threshold_r": round(threshold_r, 4),
        "rule": f"proxy_cost_r > {threshold_r:.2f}",
        **summary,
    }


def _bucket_row(bucket: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "section": "bucket",
        "bucket": bucket,
        "threshold_r": "",
        "rule": bucket,
        **_row_summary(rows),
    }


def _kill_state_row(state: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "section": "kill_state",
        "bucket": state or "blank",
        "threshold_r": "",
        "rule": "kill_rule_state",
        **_row_summary(rows),
    }


def _row_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    costs = _floats(row.get("proxy_cost_r") for row in rows)
    nets = _floats(row.get("net_after_proxy_from_gross_r") for row in rows)
    stops = _floats(row.get("stop_distance_points") for row in rows)
    spreads = _floats(row.get("spread_points") for row in rows)
    kill_counts = Counter(row.get("kill_rule_state", "") or "blank" for row in rows)
    return {
        "raw_rows": len(rows),
        "family_unique_events": _family_count(rows),
        "primary_rows": _primary_count(rows),
        "observer_duplicate_rows": sum(1 for row in rows if row.get("family_event_role") == "OBSERVER_DUPLICATE"),
        "median_proxy_cost_r": _rounded_median(costs),
        "mean_proxy_cost_r": _rounded_mean(costs),
        "median_net_after_proxy_r": _rounded_median(nets),
        "median_stop_distance_points": _rounded_median(stops),
        "median_spread_points": _rounded_median(spreads),
        "normal_count": kill_counts.get("NORMAL", 0),
        "cost_watch_count": kill_counts.get("COST_WATCH", 0),
        "suspend_family_count": kill_counts.get("SUSPEND_FAMILY", 0),
    }


def _rows_in_stop_bucket(rows: list[dict[str, str]], lower: float, upper: float | None) -> list[dict[str, str]]:
    selected = []
    for row in rows:
        value = _to_float(row.get("stop_distance_points"))
        if value is None:
            continue
        if value < lower:
            continue
        if upper is not None and value >= upper:
            continue
        selected.append(row)
    return selected


def _rows_in_spread_bucket(
    rows: list[dict[str, str]],
    lower_exclusive: float | None,
    upper_inclusive: float | None,
) -> list[dict[str, str]]:
    selected = []
    for row in rows:
        value = _to_float(row.get("spread_points"))
        if value is None:
            continue
        if lower_exclusive is not None and value <= lower_exclusive:
            continue
        if upper_inclusive is not None and value > upper_inclusive:
            continue
        selected.append(row)
    return selected


def _spread_thresholds(rows: list[dict[str, str]]) -> tuple[float | None, float | None]:
    spreads = sorted(_floats(row.get("spread_points") for row in rows))
    if not spreads:
        return None, None
    p95_index = max(0, min(len(spreads) - 1, int((len(spreads) * 0.95) + 0.999999) - 1))
    return round(median(spreads), 4), round(spreads[p95_index], 4)


def _grouped(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get(key, "") or "blank", []).append(row)
    return dict(sorted(groups.items()))


def _write_csv(
    path: Path,
    thresholds: list[dict[str, Any]],
    stop_buckets: list[dict[str, Any]],
    spread_buckets: list[dict[str, Any]],
    kill_states: list[dict[str, Any]],
) -> None:
    fieldnames = [
        "section",
        "bucket",
        "threshold_r",
        "rule",
        "raw_rows",
        "family_unique_events",
        "primary_rows",
        "observer_duplicate_rows",
        "median_proxy_cost_r",
        "mean_proxy_cost_r",
        "median_net_after_proxy_r",
        "median_stop_distance_points",
        "median_spread_points",
        "normal_count",
        "cost_watch_count",
        "suspend_family_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([*thresholds, *stop_buckets, *spread_buckets, *kill_states])


def _render_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 3 Cost Gate Review",
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
                    ("Family unique events", str(summary["family_unique_events"])),
                    ("Primary rows", str(summary["primary_rows"])),
                    ("Spread median points", str(summary["spread_median_points"])),
                    ("Spread P95 points", str(summary["spread_p95_points"])),
                ]
            ),
            "",
            "## Cost-In-R Gate Prototypes",
            "",
            _rows_table(summary["threshold_rows"]),
            "",
            "## Stop-Distance Survival Buckets",
            "",
            _rows_table(summary["stop_distance_bucket_rows"]),
            "",
            "## Spread-Regime Buckets",
            "",
            _rows_table(summary["spread_regime_bucket_rows"]),
            "",
            "## Family Kill-State Summary",
            "",
            _rows_table(summary["kill_state_rows"]),
            "",
            "## Reviewer Annotation Template",
            "",
            _table([(option, _annotation_description(option)) for option in REVIEW_ANNOTATION_OPTIONS]),
            "",
            "Use these annotations on suspend-family rows only as review labels. They do not authorize paper-mode execution or change the real Phase 2 gate state.",
            "",
        ]
    )


def _rows_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No rows."
    columns = [
        "bucket",
        "rule",
        "raw_rows",
        "family_unique_events",
        "primary_rows",
        "observer_duplicate_rows",
        "median_proxy_cost_r",
        "median_net_after_proxy_r",
        "median_stop_distance_points",
        "median_spread_points",
        "normal_count",
        "cost_watch_count",
        "suspend_family_count",
    ]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _annotation_description(option: str) -> str:
    return {
        "COST_ISSUE": "Spread/slippage proxy dominates an otherwise mechanically valid event.",
        "TIGHT_STOP_ISSUE": "Stop distance is so small that normal cost consumes the edge.",
        "TIMING_ISSUE": "Event timing appears structurally poor even before cost.",
        "DUPLICATED_OBSERVER_ISSUE": "Suspension belongs to a duplicate observer row, not a primary event.",
        "UNKNOWN": "Reviewer could not classify the suspension with current evidence.",
    }[option]


def _family_count(rows: list[dict[str, str]]) -> int:
    return len({row.get("family_event_id", "") for row in rows if row.get("family_event_id")})


def _primary_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("primary_stream_allowed") == "true")


def _floats(values) -> list[float]:
    parsed = [_to_float(value) for value in values]
    return [value for value in parsed if value is not None]


def _rounded_median(values: list[float]) -> float | None:
    return round(median(values), 4) if values else None


def _rounded_mean(values: list[float]) -> float | None:
    return round(mean(values), 4) if values else None


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _fmt_label(value: float | None) -> str:
    if value is None:
        return "na"
    return str(value).replace(".", "_")


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    phase3_root = Path(__file__).resolve().parents[1]
    reports = phase3_root / "outputs" / "reports"
    parser = argparse.ArgumentParser(description="Generate Phase 3 cost-gate and bucket review report.")
    parser.add_argument("--ledger-path", type=Path, default=reports / "PHASE3_EXPERIMENTAL_LEDGER.csv")
    parser.add_argument("--output-dir", type=Path, default=reports)
    args = parser.parse_args(argv)
    path = generate_cost_gate_review(args.ledger_path, args.output_dir)
    print(f"Phase 3 cost-gate review: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
