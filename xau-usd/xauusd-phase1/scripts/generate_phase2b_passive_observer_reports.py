from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median


DEFAULT_LOG = Path("outputs") / "paper_observer" / "passive_cost_observer_log.csv"
DEFAULT_REPORT_DIR = Path("outputs") / "reports"
MIN_ACTIVE_MARKET_DAYS = 20
MIN_EVENTS_WITH_WARNING = 100
PREFERRED_UNIQUE_EVENTS = 300


REPORT_NAMES = {
    "cost_feasibility": "PHASE2B_COST_FEASIBILITY_REPORT.md",
    "stop_distance": "PHASE2B_STOP_DISTANCE_SURVIVAL_REPORT.md",
    "spread_regime": "PHASE2B_SPREAD_REGIME_SURVIVAL_REPORT.md",
    "session_cost": "PHASE2B_SESSION_COST_REPORT.md",
    "hour_of_day": "PHASE2B_HOUR_OF_DAY_COST_REPORT.md",
    "candidate_decision": "PHASE2B_CANDIDATE_FEASIBILITY_DECISION.md",
    "manifest": "PHASE2B_PASSIVE_OBSERVER_REPORTS.json",
}


@dataclass(frozen=True)
class Phase2BReportOutput:
    status: str
    log_path: Path
    report_paths: tuple[Path, ...]
    rows: int
    unique_events: int
    active_market_days: int


def generate_phase2b_passive_observer_reports(
    root: Path,
    log_path: Path | None = None,
    report_dir: Path | None = None,
) -> Phase2BReportOutput:
    root = root.resolve()
    log_path = (root / DEFAULT_LOG if log_path is None else log_path).resolve()
    report_dir = (root / DEFAULT_REPORT_DIR if report_dir is None else report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_rows(log_path)
    enriched = [_enrich_row(row) for row in rows]
    unique_events = _unique_event_count(enriched)
    active_days = _active_market_days(enriched)
    coverage = _cost_coverage(enriched)
    status = _overall_status(log_path, enriched, unique_events, active_days, coverage)

    report_paths = {
        key: report_dir / name
        for key, name in REPORT_NAMES.items()
        if key != "manifest"
    }
    report_paths["cost_feasibility"].write_text(
        _render_cost_feasibility(status, log_path, enriched, unique_events, active_days, coverage),
        encoding="utf-8",
    )
    report_paths["stop_distance"].write_text(
        _render_group_report(
            title="Phase 2B Stop-Distance Survival Report",
            status=status,
            log_path=log_path,
            rows=enriched,
            groups=_stop_distance_groups(enriched),
            note="Wider stop-distance buckets should reduce cost_R pressure. This report is passive evidence only.",
        ),
        encoding="utf-8",
    )
    report_paths["spread_regime"].write_text(
        _render_group_report(
            title="Phase 2B Spread-Regime Survival Report",
            status=status,
            log_path=log_path,
            rows=enriched,
            groups=_spread_regime_groups(enriched),
            note="Spread regimes are measured from passive rows only and cannot authorize Phase 2 execution.",
        ),
        encoding="utf-8",
    )
    report_paths["session_cost"].write_text(
        _render_group_report(
            title="Phase 2B Session Cost Report",
            status=status,
            log_path=log_path,
            rows=enriched,
            groups=_field_groups(enriched, "session_label", "UNKNOWN_SESSION"),
            note="Session buckets help identify where live cost feasibility is concentrated.",
        ),
        encoding="utf-8",
    )
    report_paths["hour_of_day"].write_text(
        _render_group_report(
            title="Phase 2B Hour-of-Day Cost Report",
            status=status,
            log_path=log_path,
            rows=enriched,
            groups=_field_groups(enriched, "hour_utc", "UNKNOWN_HOUR"),
            note="Hour-of-day buckets are UTC hours from passive rows only.",
        ),
        encoding="utf-8",
    )
    report_paths["candidate_decision"].write_text(
        _render_candidate_decision(status, log_path, enriched, unique_events, active_days, coverage),
        encoding="utf-8",
    )

    manifest_path = report_dir / REPORT_NAMES["manifest"]
    manifest = {
        "status": status,
        "created_at_utc": _now(),
        "log_path": str(log_path),
        "passive_log_only": True,
        "experimental_demo_order_logs_used": False,
        "canonical_phase2_authorized": False,
        "paper_mode_execution_allowed": False,
        "rows": len(enriched),
        "unique_family_events": unique_events,
        "active_market_days": active_days,
        "cost_r_coverage_pct": coverage,
        "report_paths": {key: str(path) for key, path in report_paths.items()},
        "sample_requirements": {
            "active_market_days_required": MIN_ACTIVE_MARKET_DAYS,
            "unique_family_events_preferred": PREFERRED_UNIQUE_EVENTS,
            "unique_family_events_minimum_with_warning": MIN_EVENTS_WITH_WARNING,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    output_paths = tuple(report_paths.values()) + (manifest_path,)
    return Phase2BReportOutput(status, log_path, output_paths, len(enriched), unique_events, active_days)


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def _enrich_row(row: dict[str, str]) -> dict[str, object]:
    enriched: dict[str, object] = dict(row)
    cost_r = _float(row.get("estimated_total_cost_R") or row.get("estimated_total_cost_r"))
    stop_points = _float(row.get("stop_distance_points"))
    spread_points = _float(row.get("spread_points"))
    net_edge = _float(row.get("estimated_net_edge_R") or row.get("estimated_net_edge_r"))
    gross_edge = _float(row.get("estimated_gross_edge_R") or row.get("estimated_gross_edge_r"))
    enriched["_cost_r"] = cost_r
    enriched["_stop_distance_points"] = stop_points
    enriched["_spread_points"] = spread_points
    enriched["_net_edge_r"] = net_edge
    enriched["_gross_edge_r"] = gross_edge
    enriched["_cost_gate_status"] = row.get("cost_gate_status") or _classify_cost_gate(cost_r)
    enriched["_event_key"] = _event_key(row)
    enriched["_date_key"] = _date_key(row)
    return enriched


def _event_key(row: dict[str, str]) -> str:
    parts = [
        row.get("timestamp_utc") or row.get("timestamp_broker") or "",
        row.get("candidate_family") or row.get("candidate") or "",
        row.get("symbol") or "",
        row.get("signal_direction") or "",
        row.get("intended_entry_price") or "",
        row.get("intended_stop_loss") or "",
    ]
    key = "|".join(parts).strip("|")
    return key or str(id(row))


def _date_key(row: dict[str, str]) -> str:
    raw = row.get("timestamp_utc") or row.get("timestamp_broker") or ""
    raw = raw.strip()
    if not raw:
        return ""
    for separator in ("T", " "):
        if separator in raw:
            return raw.split(separator, 1)[0].replace(".", "-")
    return raw[:10].replace(".", "-")


def _unique_event_count(rows: list[dict[str, object]]) -> int:
    return len({str(row.get("_event_key", "")) for row in rows}) if rows else 0


def _active_market_days(rows: list[dict[str, object]]) -> int:
    return len({str(row.get("_date_key", "")) for row in rows if row.get("_date_key")})


def _cost_coverage(rows: list[dict[str, object]]) -> float:
    if not rows:
        return 0.0
    with_cost = sum(1 for row in rows if row.get("_cost_r") is not None)
    return with_cost / len(rows) * 100.0


def _overall_status(
    log_path: Path,
    rows: list[dict[str, object]],
    unique_events: int,
    active_days: int,
    coverage: float,
) -> str:
    if not log_path.exists() or not rows:
        return "PENDING"
    if coverage < 100.0:
        return "WARN_INCOMPLETE_COST_R"
    if active_days >= MIN_ACTIVE_MARKET_DAYS and unique_events >= PREFERRED_UNIQUE_EVENTS:
        return "PASS"
    if unique_events >= MIN_EVENTS_WITH_WARNING:
        return "REVIEW_READY_LOW_SAMPLE"
    return "PENDING_SAMPLE"


def _render_cost_feasibility(
    status: str,
    log_path: Path,
    rows: list[dict[str, object]],
    unique_events: int,
    active_days: int,
    coverage: float,
) -> str:
    gate_rows = _gate_counts(rows)
    summary_rows = [
        ("Overall status", status),
        ("Passive log path", str(log_path)),
        ("Rows", len(rows)),
        ("Unique family events", unique_events),
        ("Active market days", active_days),
        ("Cost_R coverage", f"{coverage:.2f}%"),
        ("Median cost_R", _fmt(_median_value(rows, "_cost_r"))),
        ("Median net edge_R", _fmt(_median_value(rows, "_net_edge_r"))),
        ("Mean cost_R", _fmt(_mean_value(rows, "_cost_r"))),
        ("Mean net edge_R", _fmt(_mean_value(rows, "_net_edge_r"))),
    ]
    return "\n".join(
        [
            "# Phase 2B Cost Feasibility Report",
            "",
            f"Overall status: {status}",
            "",
            "This report reads passive paper-observer logs only. It does not read experimental demo order logs and does not authorize canonical Phase 2, paper-mode execution, demo execution as Phase 2 evidence, or live trading.",
            "",
            "## Summary",
            "",
            _table(("Field", "Value"), [(key, value) for key, value in summary_rows]),
            "",
            "## Cost Gate Counts",
            "",
            _table(("Cost gate", "Rows"), gate_rows),
            "",
            "## Sample Requirements",
            "",
            _sample_requirement_table(unique_events, active_days, coverage),
            "",
            _decision_text(status),
            "",
        ]
    )


def _render_group_report(
    title: str,
    status: str,
    log_path: Path,
    rows: list[dict[str, object]],
    groups: dict[str, list[dict[str, object]]],
    note: str,
) -> str:
    table_rows: list[tuple[object, ...]] = []
    for name, group_rows in groups.items():
        table_rows.append(
            (
                name,
                len(group_rows),
                _fmt(_median_value(group_rows, "_cost_r")),
                _fmt(_median_value(group_rows, "_net_edge_r")),
                _fmt(_median_value(group_rows, "_stop_distance_points")),
                _fmt(_median_value(group_rows, "_spread_points")),
                _gate_summary(group_rows),
            )
        )
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Overall status: {status}",
            "",
            note,
            "",
            f"Passive log: `{log_path}`",
            "",
            "## Buckets",
            "",
            _table(
                (
                    "Bucket",
                    "Rows",
                    "Median cost_R",
                    "Median net edge_R",
                    "Median stop points",
                    "Median spread points",
                    "Gate counts",
                ),
                table_rows,
            ),
            "",
            "## Boundary",
            "",
            "This report is passive-observer research evidence only. It cannot make a cost-suspended family execution-eligible.",
            "",
        ]
    )


def _render_candidate_decision(
    status: str,
    log_path: Path,
    rows: list[dict[str, object]],
    unique_events: int,
    active_days: int,
    coverage: float,
) -> str:
    candidate_groups = _field_groups(rows, "candidate", "UNKNOWN_CANDIDATE")
    candidate_rows = []
    for candidate, group_rows in candidate_groups.items():
        candidate_rows.append(
            (
                candidate,
                len(group_rows),
                _fmt(_median_value(group_rows, "_cost_r")),
                _fmt(_median_value(group_rows, "_net_edge_r")),
                _gate_summary(group_rows),
                _candidate_read(group_rows),
            )
        )
    return "\n".join(
        [
            "# Phase 2B Candidate Feasibility Decision",
            "",
            f"Overall status: {status}",
            "",
            "Decision authority: PASSIVE OBSERVER ONLY. A feasible subset must become a new locked Phase 0R hypothesis before any canonical Phase 2 reconsideration.",
            "",
            "## Candidate Reads",
            "",
            _table(
                ("Candidate", "Rows", "Median cost_R", "Median net edge_R", "Gate counts", "Passive read"),
                candidate_rows,
            ),
            "",
            "## Current Decision",
            "",
            _candidate_decision(status, unique_events, active_days, coverage),
            "",
            "## Source Boundary",
            "",
            f"- Passive log: `{log_path}`",
            "- Experimental demo order logs used: false",
            "- Canonical Phase 2 authorized: false",
            "- Paper-mode execution allowed: false",
            "",
        ]
    )


def _stop_distance_groups(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    buckets = {"0_to_249": [], "250_to_499": [], "500_to_749": [], "750_plus": [], "unknown": []}
    for row in rows:
        value = row.get("_stop_distance_points")
        if value is None:
            buckets["unknown"].append(row)
        elif float(value) < 250:
            buckets["0_to_249"].append(row)
        elif float(value) < 500:
            buckets["250_to_499"].append(row)
        elif float(value) < 750:
            buckets["500_to_749"].append(row)
        else:
            buckets["750_plus"].append(row)
    return {key: value for key, value in buckets.items() if value}


def _spread_regime_groups(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    buckets = {"spread_lte_50": [], "spread_50_to_75": [], "spread_gt_75": [], "unknown": []}
    for row in rows:
        value = row.get("_spread_points")
        if value is None:
            buckets["unknown"].append(row)
        elif float(value) <= 50:
            buckets["spread_lte_50"].append(row)
        elif float(value) <= 75:
            buckets["spread_50_to_75"].append(row)
        else:
            buckets["spread_gt_75"].append(row)
    return {key: value for key, value in buckets.items() if value}


def _field_groups(rows: list[dict[str, object]], field: str, missing_label: str) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        label = str(row.get(field) or missing_label)
        grouped[label].append(row)
    return dict(sorted(grouped.items()))


def _gate_counts(rows: list[dict[str, object]]) -> list[tuple[str, int]]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get("_cost_gate_status") or "UNKNOWN")] += 1
    if not counts:
        return [("NO_PASSIVE_ROWS", 0)]
    return sorted(counts.items())


def _gate_summary(rows: list[dict[str, object]]) -> str:
    return ", ".join(f"{key}={value}" for key, value in _gate_counts(rows))


def _candidate_read(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "NO_DATA"
    cost = _median_value(rows, "_cost_r")
    net = _median_value(rows, "_net_edge_r")
    if cost is None or net is None:
        return "INCOMPLETE_COST_DATA"
    if cost <= 0.20 and net >= 0.15:
        return "COST_FEASIBLE_CANDIDATE_FOR_HUMAN_REVIEW"
    if cost <= 0.30 and net >= 0.15:
        return "MARGINAL_REVIEW_REQUIRED"
    return "COST_BLOCK_OR_LOW_NET"


def _candidate_decision(status: str, unique_events: int, active_days: int, coverage: float) -> str:
    if status == "PASS":
        return "Passive sample requirements are met. Human review may use these reports to draft a new locked hypothesis; this still does not authorize execution."
    if status == "REVIEW_READY_LOW_SAMPLE":
        return "Enough events exist for preliminary review, but the preferred sample is not complete. Keep observing before candidate promotion decisions."
    if status == "WARN_INCOMPLETE_COST_R":
        return "Rows exist, but cost_R coverage is incomplete. Fix observer logging before using the evidence."
    return (
        "Passive sample is not ready. Required: "
        f"{MIN_ACTIVE_MARKET_DAYS} active market days, "
        f"{PREFERRED_UNIQUE_EVENTS} preferred unique family events, "
        f"{MIN_EVENTS_WITH_WARNING} minimum with warning, and 100% cost_R coverage. "
        f"Observed: active_days={active_days}, unique_events={unique_events}, coverage={coverage:.2f}%."
    )


def _sample_requirement_table(unique_events: int, active_days: int, coverage: float) -> str:
    rows = [
        ("Active market days", f">= {MIN_ACTIVE_MARKET_DAYS}", active_days, _pass_fail(active_days >= MIN_ACTIVE_MARKET_DAYS)),
        ("Unique family events preferred", f">= {PREFERRED_UNIQUE_EVENTS}", unique_events, _pass_fail(unique_events >= PREFERRED_UNIQUE_EVENTS)),
        ("Unique family events minimum", f">= {MIN_EVENTS_WITH_WARNING}", unique_events, _pass_fail(unique_events >= MIN_EVENTS_WITH_WARNING)),
        ("Cost_R coverage", "100%", f"{coverage:.2f}%", _pass_fail(coverage >= 100.0)),
    ]
    return _table(("Requirement", "Target", "Observed", "Status"), rows)


def _decision_text(status: str) -> str:
    return "\n".join(["## Decision", "", _candidate_decision(status, 0, 0, 0.0) if status == "PENDING" else "See `PHASE2B_CANDIDATE_FEASIBILITY_DECISION.md` for the candidate-level passive read."])


def _median_value(rows: list[dict[str, object]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return median(values) if values else None


def _mean_value(rows: list[dict[str, object]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return mean(values) if values else None


def _float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _classify_cost_gate(cost_r: float | None) -> str:
    if cost_r is None:
        return "UNKNOWN"
    if cost_r <= 0.15:
        return "COST_OK_STRONG"
    if cost_r <= 0.20:
        return "COST_OK_ACCEPTABLE"
    if cost_r <= 0.30:
        return "COST_WARN"
    return "COST_BLOCK"


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def _pass_fail(value: bool) -> str:
    return "PASS" if value else "PENDING"


def _table(headers: tuple[object, ...], rows: list[tuple[object, ...]]) -> str:
    header = "| " + " | ".join(str(value) for value in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    if not rows:
        return "\n".join([header, separator, "| " + " | ".join("n/a" for _ in headers) + " |"])
    body = [
        "| " + " | ".join(_escape(str(value)) for value in row) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2B passive-observer cost feasibility reports.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--log-path", type=Path, default=None)
    parser.add_argument("--report-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    output = generate_phase2b_passive_observer_reports(args.root, args.log_path, args.report_dir)
    print(f"Phase 2B passive observer reports: {output.status}")
    print(f"Rows: {output.rows}; unique events: {output.unique_events}; active days: {output.active_market_days}")
    for path in output.report_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
