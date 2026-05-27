from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median

from phase1_gap_classifier import classify_gap


DECISION_LOG = "decision_log.csv"
STARTUP_LOG = "startup_log.csv"
SHUTDOWN_LOG = "shutdown_log.csv"
DEFAULT_MAX_FRESH_MINUTES = 15


@dataclass(frozen=True)
class SoakCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class SoakAnalysis:
    status: str
    report_path: Path
    rows_analyzed: int
    checks: tuple[SoakCheck, ...]


def analyze_phase1_soak(
    files_dir: Path,
    report_path: Path | None = None,
    now: datetime | None = None,
    max_fresh_minutes: int = DEFAULT_MAX_FRESH_MINUTES,
) -> SoakAnalysis:
    files_dir = files_dir.resolve()
    if report_path is None:
        report_path = Path.cwd() / "outputs" / "reports" / "PHASE1_SOAK_DRIFT_REPORT.md"
    if now is None:
        now = datetime.now()

    decision_rows = _read_csv(files_dir / DECISION_LOG)
    startup_rows = _read_csv(files_dir / STARTUP_LOG)
    shutdown_rows = _read_csv(files_dir / SHUTDOWN_LOG)

    checks = [
        _check_rows(decision_rows),
        _check_dry_run(decision_rows),
        _check_permission(decision_rows),
        _check_lifecycle_rows(startup_rows, shutdown_rows),
        _check_per_run_cadence(decision_rows),
        _check_latest_row_freshness(decision_rows, now, max_fresh_minutes),
        _check_clock_status(decision_rows),
        _check_observer_activity(decision_rows),
    ]

    status = _overall_status(checks)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(status, files_dir, checks, decision_rows, startup_rows, shutdown_rows),
        encoding="utf-8",
    )
    return SoakAnalysis(
        status=status,
        report_path=report_path,
        rows_analyzed=len(decision_rows),
        checks=tuple(checks),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _check_rows(rows: list[dict[str, str]]) -> SoakCheck:
    if rows:
        return SoakCheck("decision_rows", "PASS", f"Rows available for soak analysis: {len(rows)}.")
    return SoakCheck("decision_rows", "FAIL", "No decision rows found.")


def _check_dry_run(rows: list[dict[str, str]]) -> SoakCheck:
    bad = [
        row.get("run_id", "")
        for row in rows
        if row.get("dry_run", "").lower() != "true" or row.get("lifecycle_state", "") != "DRY_RUN"
    ]
    if bad:
        return SoakCheck("dry_run_state", "FAIL", f"Rows outside dry-run state: {len(bad)}.")
    return SoakCheck("dry_run_state", "PASS", "All rows stayed in dry-run state.")


def _check_permission(rows: list[dict[str, str]]) -> SoakCheck:
    bad = [row.get("run_id", "") for row in rows if row.get("trade_permission", "").lower() != "false"]
    if bad:
        return SoakCheck("permission_state", "FAIL", f"Rows with permission not false: {len(bad)}.")
    return SoakCheck("permission_state", "PASS", "All rows kept permission false.")


def _check_lifecycle_rows(startup_rows: list[dict[str, str]], shutdown_rows: list[dict[str, str]]) -> SoakCheck:
    if not startup_rows:
        return SoakCheck("lifecycle_rows", "WARN", "No startup rows found.")
    if len(startup_rows) == 1 and not shutdown_rows:
        return SoakCheck("lifecycle_rows", "PASS", "One active startup row and no shutdown row yet.")
    return SoakCheck(
        "lifecycle_rows",
        "PASS",
        f"Startup rows: {len(startup_rows)}; shutdown rows: {len(shutdown_rows)}.",
    )


def _check_per_run_cadence(rows: list[dict[str, str]]) -> SoakCheck:
    problems: list[str] = []
    tolerated: list[str] = []
    for run_id, run_rows in _group_by(rows, "run_id").items():
        ordered = _unique_bar_rows(run_rows)
        if len(ordered) < 2:
            continue
        gaps: list[int] = []
        tolerated_gaps: list[int] = []
        for (left, left_row), (right, right_row) in zip(ordered, ordered[1:]):
            minutes = int((right - left).total_seconds() / 60)
            if minutes <= 5:
                continue
            classification = classify_gap(left, right, left_row, right_row)
            if not classification.counts_as_runtime_warning:
                tolerated_gaps.append(minutes)
            else:
                gaps.append(minutes)
        if gaps:
            problems.append(f"{run_id}: {len(gaps)} gap(s)")
        if tolerated_gaps:
            tolerated.append(f"{run_id}: {len(tolerated_gaps)} expected market-break gap(s)")
    if problems:
        return SoakCheck("per_run_bar_cadence", "WARN", "; ".join(problems))
    if tolerated:
        return SoakCheck("per_run_bar_cadence", "PASS", "; ".join(tolerated))
    return SoakCheck("per_run_bar_cadence", "PASS", "No larger-than-M5 gaps inside individual run IDs.")


def _check_latest_row_freshness(
    rows: list[dict[str, str]],
    now: datetime,
    max_fresh_minutes: int,
) -> SoakCheck:
    if not rows:
        return SoakCheck("latest_row_freshness", "FAIL", "No decision rows found.")
    latest = rows[-1]
    latest_time = _parse_mt5_datetime(latest.get("timestamp_local", "")) or _parse_mt5_datetime(
        latest.get("timestamp_broker", "")
    )
    if latest_time is None:
        return SoakCheck("latest_row_freshness", "WARN", "Latest row has no parseable local or broker timestamp.")
    age_minutes = (now - latest_time).total_seconds() / 60
    if age_minutes < -2:
        return SoakCheck(
            "latest_row_freshness",
            "WARN",
            f"Latest row timestamp is {abs(age_minutes):.1f} minute(s) ahead of local clock.",
        )
    if age_minutes <= max_fresh_minutes:
        return SoakCheck(
            "latest_row_freshness",
            "PASS",
            f"Latest row age is {max(age_minutes, 0):.1f} minute(s); limit {max_fresh_minutes}.",
        )
    if _is_weekend_market_break(now):
        return SoakCheck(
            "latest_row_freshness",
            "PASS",
            (
                f"Latest row age is {age_minutes:.1f} minute(s), but local date is a weekend "
                "market break; soak time remains paused."
            ),
        )
    return SoakCheck(
        "latest_row_freshness",
        "WARN",
        f"Latest row age is {age_minutes:.1f} minute(s); limit {max_fresh_minutes}.",
    )


def _check_clock_status(rows: list[dict[str, str]]) -> SoakCheck:
    statuses = sorted({row.get("server_time_status", "") for row in rows if row.get("server_time_status", "")})
    if not statuses:
        return SoakCheck("server_time_status", "WARN", "No server-time status values found.")
    if statuses == ["CLOCK_OK"]:
        return SoakCheck("server_time_status", "PASS", "All rows report CLOCK_OK.")
    latest_status = rows[-1].get("server_time_status", "") if rows else ""
    if latest_status == "CLOCK_OK":
        historical_non_ok = sum(1 for row in rows[:-1] if row.get("server_time_status", "") != "CLOCK_OK")
        return SoakCheck(
            "server_time_status",
            "PASS",
            f"Latest row reports CLOCK_OK; historical non-CLOCK_OK rows: {historical_non_ok}.",
        )
    return SoakCheck("server_time_status", "WARN", "Latest server-time status is " + (latest_status or "blank"))


def _check_observer_activity(rows: list[dict[str, str]]) -> SoakCheck:
    stages = sorted({row.get("br_stage", "") for row in rows if row.get("br_stage", "")})
    if not stages:
        return SoakCheck("breakout_retest_observer", "FAIL", "No observer stage values found.")
    if stages == ["NOT_EVALUATED"]:
        return SoakCheck("breakout_retest_observer", "WARN", "Observer never moved beyond NOT_EVALUATED.")
    return SoakCheck("breakout_retest_observer", "PASS", "Observed stage values: " + ", ".join(stages))


def _overall_status(checks: list[SoakCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "WARN"
    return "PASS"


def _render_report(
    status: str,
    files_dir: Path,
    checks: list[SoakCheck],
    decision_rows: list[dict[str, str]],
    startup_rows: list[dict[str, str]],
    shutdown_rows: list[dict[str, str]],
) -> str:
    latest = decision_rows[-1] if decision_rows else {}
    first_time, latest_time = _first_latest_bar(decision_rows)
    latest_local_time = latest.get("timestamp_local", "n/a") if latest else "n/a"
    spread_stats = _numeric_stats(row.get("spread_points", "") for row in decision_rows)
    stale_stats = _numeric_stats(row.get("stale_seconds", "") for row in decision_rows)
    observer_transitions = _transition_count(decision_rows, ("br_stage", "br_direction", "br_would_signal"))

    return "\n".join(
        [
            "# Phase 1 Soak Drift Report",
            "",
            f"Overall status: {status}",
            "",
            f"Files directory: `{files_dir}`",
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": item.name, "Status": item.status, "Message": item.message} for item in checks],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Runtime Summary",
            "",
            f"- Decision rows: {len(decision_rows)}",
            f"- Startup rows: {len(startup_rows)}",
            f"- Shutdown rows: {len(shutdown_rows)}",
            f"- Unique run IDs: {len({row.get('run_id', '') for row in decision_rows})}",
            f"- First bar time: {first_time or 'n/a'}",
            f"- Latest bar time: {latest_time or 'n/a'}",
            f"- Latest local timestamp: {latest_local_time}",
            f"- Observer transitions: {observer_transitions}",
            "",
            "## Latest Row",
            "",
            _markdown_table(
                [
                    {
                        "Run ID": latest.get("run_id", "n/a"),
                        "Broker Time": latest.get("timestamp_broker", "n/a"),
                        "Bar Time": latest.get("bar_time", "n/a"),
                        "Risk": latest.get("risk_state", "n/a"),
                        "Execution": latest.get("execution_state", "n/a"),
                        "Server Time": latest.get("server_time_status", "n/a"),
                        "BR Stage": latest.get("br_stage", "n/a"),
                        "BR Direction": latest.get("br_direction", "n/a"),
                        "Would Signal": latest.get("br_would_signal", "n/a"),
                    }
                ]
                if latest
                else [],
                [
                    "Run ID",
                    "Broker Time",
                    "Bar Time",
                    "Risk",
                    "Execution",
                    "Server Time",
                    "BR Stage",
                    "BR Direction",
                    "Would Signal",
                ],
            ),
            "",
            "## Spread Points",
            "",
            _stats_table(spread_stats),
            "",
            "## Stale Seconds",
            "",
            _stats_table(stale_stats),
            "",
            "## State Counts",
            "",
            "### Risk",
            "",
            _count_table(row.get("risk_state", "") for row in decision_rows),
            "",
            "### Execution",
            "",
            _count_table(row.get("execution_state", "") for row in decision_rows),
            "",
            "### Server Time",
            "",
            _count_table(row.get("server_time_status", "") for row in decision_rows),
            "",
            "### Breakout-Retest Stage",
            "",
            _count_table(row.get("br_stage", "") for row in decision_rows),
            "",
            "### Breakout-Retest Direction",
            "",
            _count_table(row.get("br_direction", "") for row in decision_rows),
            "",
            "### Breakout-Retest Would-Signal",
            "",
            _count_table(row.get("br_would_signal", "") for row in decision_rows),
            "",
            "## Rows By Run ID",
            "",
            _markdown_table(
                [
                    {
                        "Run ID": run_id or "blank",
                        "Rows": str(len(run_rows)),
                        "First Bar": _first_latest_bar(run_rows)[0] or "n/a",
                        "Latest Bar": _first_latest_bar(run_rows)[1] or "n/a",
                    }
                    for run_id, run_rows in sorted(_group_by(decision_rows, "run_id").items())
                ],
                ["Run ID", "Rows", "First Bar", "Latest Bar"],
            ),
            "",
        ]
    )


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def _is_weekend_market_break(now: datetime) -> bool:
    return now.weekday() in {5, 6}


def _unique_bar_rows(rows: list[dict[str, str]]) -> list[tuple[datetime, dict[str, str]]]:
    seen: dict[datetime, dict[str, str]] = {}
    for row in rows:
        parsed = _parse_mt5_datetime(row.get("bar_time", ""))
        if parsed is not None and parsed not in seen:
            seen[parsed] = row
    return sorted(seen.items(), key=lambda item: item[0])


def _first_latest_bar(rows: list[dict[str, str]]) -> tuple[str | None, str | None]:
    parsed = sorted(
        {value for value in (_parse_mt5_datetime(row.get("bar_time", "")) for row in rows) if value}
    )
    if not parsed:
        return None, None
    return (
        parsed[0].strftime("%Y.%m.%d %H:%M:%S"),
        parsed[-1].strftime("%Y.%m.%d %H:%M:%S"),
    )


def _numeric_stats(values) -> dict[str, str]:
    parsed = sorted(_to_float(value) for value in values if _to_float(value) is not None)
    if not parsed:
        return {"count": "0", "min": "n/a", "median": "n/a", "p95": "n/a", "max": "n/a"}
    return {
        "count": str(len(parsed)),
        "min": f"{parsed[0]:.2f}",
        "median": f"{median(parsed):.2f}",
        "p95": f"{_percentile(parsed, 95):.2f}",
        "max": f"{parsed[-1]:.2f}",
    }


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _percentile(values: list[float], percentile: int) -> float:
    if len(values) == 1:
        return values[0]
    index = round((percentile / 100) * (len(values) - 1))
    return values[index]


def _transition_count(rows: list[dict[str, str]], fields: tuple[str, ...]) -> int:
    ordered = sorted(
        rows,
        key=lambda row: (
            _parse_mt5_datetime(row.get("timestamp_broker", "")) or datetime.min,
            row.get("run_id", ""),
        ),
    )
    previous: tuple[str, ...] | None = None
    transitions = 0
    for row in ordered:
        current = tuple(row.get(field, "") for field in fields)
        if previous is not None and current != previous:
            transitions += 1
        previous = current
    return transitions


def _group_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get(key, ""), []).append(row)
    return groups


def _count_table(values) -> str:
    counts: dict[str, int] = {}
    for value in values:
        key = value or "blank"
        counts[key] = counts.get(key, 0) + 1
    return _markdown_table(
        [{"Value": key, "Count": str(value)} for key, value in sorted(counts.items())],
        ["Value", "Count"],
    )


def _stats_table(stats: dict[str, str]) -> str:
    return _markdown_table([stats], ["count", "min", "median", "p95", "max"])


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze Phase 1 dry-run soak and drift logs.")
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument("--max-fresh-minutes", type=int, default=DEFAULT_MAX_FRESH_MINUTES)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_SOAK_DRIFT_REPORT.md",
        help="Markdown report path.",
    )
    args = parser.parse_args(argv)

    output = analyze_phase1_soak(args.files_dir, args.report, max_fresh_minutes=args.max_fresh_minutes)
    print(f"Phase 1 soak analysis: {output.status}")
    print(output.report_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.message}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
