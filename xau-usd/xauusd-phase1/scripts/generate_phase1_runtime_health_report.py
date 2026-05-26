from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path


DECISION_LOG = "decision_log.csv"
STARTUP_LOG = "startup_log.csv"
SHUTDOWN_LOG = "shutdown_log.csv"
DEFAULT_MAX_FRESH_MINUTES = 15
DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE1_RUNTIME_HEALTH_REPORT.md"
DEFAULT_EXPECTED_BREAKS = Path(__file__).resolve().parents[1] / "PHASE1_EXPECTED_MARKET_BREAKS.yaml"
WEEKDAY_INDEX = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


@dataclass(frozen=True)
class RuntimeHealthCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class RuntimeHealthReport:
    status: str
    report_path: Path
    rows_analyzed: int
    checks: tuple[RuntimeHealthCheck, ...]


def generate_phase1_runtime_health_report(
    files_dir: Path,
    report_path: Path | None = None,
    now: datetime | None = None,
    max_fresh_minutes: int = DEFAULT_MAX_FRESH_MINUTES,
) -> RuntimeHealthReport:
    files_dir = files_dir.resolve()
    if report_path is None:
        report_path = DEFAULT_REPORT
    report_path = report_path.resolve()
    if now is None:
        now = datetime.now()

    decision_path = files_dir / DECISION_LOG
    startup_path = files_dir / STARTUP_LOG
    shutdown_path = files_dir / SHUTDOWN_LOG
    decision_rows = _read_csv(decision_path)
    startup_rows = _read_csv(startup_path)
    shutdown_rows = _read_csv(shutdown_path)

    checks = [
        _check_file("decision_log", decision_path),
        _check_file("startup_log", startup_path),
        _check_optional_file("shutdown_log", shutdown_path),
        _check_decision_rows(decision_rows),
        _check_latest_freshness(decision_rows, now, max_fresh_minutes),
        _check_dry_run(decision_rows),
        _check_permission(decision_rows),
        _check_clock(decision_rows),
        _check_exact_duplicates(decision_rows),
        _check_unique_bar_gaps(decision_rows),
        _check_startup_shutdown_balance(startup_rows, shutdown_rows),
    ]
    status = _overall_status(checks)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(status, files_dir, decision_rows, startup_rows, shutdown_rows, checks),
        encoding="utf-8",
    )
    return RuntimeHealthReport(status, report_path, len(decision_rows), tuple(checks))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _check_file(name: str, path: Path) -> RuntimeHealthCheck:
    if path.exists() and path.stat().st_size > 0:
        return RuntimeHealthCheck(name, "PASS", f"Found `{path}` ({path.stat().st_size} bytes).")
    return RuntimeHealthCheck(name, "FAIL", f"Missing or empty `{path}`.")


def _check_optional_file(name: str, path: Path) -> RuntimeHealthCheck:
    if path.exists() and path.stat().st_size > 0:
        return RuntimeHealthCheck(name, "PASS", f"Found `{path}` ({path.stat().st_size} bytes).")
    return RuntimeHealthCheck(name, "WARN", f"Optional lifecycle file missing or empty: `{path}`.")


def _check_decision_rows(rows: list[dict[str, str]]) -> RuntimeHealthCheck:
    if rows:
        return RuntimeHealthCheck("decision_rows", "PASS", f"Decision rows: {len(rows)}.")
    return RuntimeHealthCheck("decision_rows", "FAIL", "No decision rows found.")


def _check_latest_freshness(
    rows: list[dict[str, str]],
    now: datetime,
    max_fresh_minutes: int,
) -> RuntimeHealthCheck:
    if not rows:
        return RuntimeHealthCheck("latest_freshness", "FAIL", "No latest row available.")
    latest = rows[-1]
    latest_time = _parse_mt5_datetime(latest.get("timestamp_local", "")) or _parse_mt5_datetime(
        latest.get("timestamp_broker", "")
    )
    if latest_time is None:
        return RuntimeHealthCheck("latest_freshness", "WARN", "Latest row timestamp could not be parsed.")
    age = (now - latest_time).total_seconds() / 60
    if age < -2:
        return RuntimeHealthCheck(
            "latest_freshness",
            "WARN",
            f"Latest row is {abs(age):.1f} minute(s) ahead of local clock.",
        )
    if age <= max_fresh_minutes:
        return RuntimeHealthCheck(
            "latest_freshness",
            "PASS",
            f"Latest row age is {max(age, 0):.1f} minute(s); limit {max_fresh_minutes}.",
        )
    if _is_weekend_market_break(now):
        return RuntimeHealthCheck(
            "latest_freshness",
            "PASS",
            (
                f"Latest row age is {age:.1f} minute(s), but local date is a weekend "
                "market break; runtime freshness is paused."
            ),
        )
    return RuntimeHealthCheck(
        "latest_freshness",
        "WARN",
        f"Latest row age is {age:.1f} minute(s); limit {max_fresh_minutes}.",
    )


def _check_dry_run(rows: list[dict[str, str]]) -> RuntimeHealthCheck:
    bad = [
        row
        for row in rows
        if row.get("dry_run", "").lower() != "true" or row.get("lifecycle_state", "") != "DRY_RUN"
    ]
    if bad:
        return RuntimeHealthCheck("dry_run_lock", "FAIL", f"Rows outside dry-run state: {len(bad)}.")
    return RuntimeHealthCheck("dry_run_lock", "PASS", "All decision rows stayed dry-run.")


def _check_permission(rows: list[dict[str, str]]) -> RuntimeHealthCheck:
    bad = [row for row in rows if row.get("trade_permission", "").lower() != "false"]
    if bad:
        return RuntimeHealthCheck("permission_lock", "FAIL", f"Rows with permission not false: {len(bad)}.")
    return RuntimeHealthCheck("permission_lock", "PASS", "All decision rows kept permission false.")


def _check_clock(rows: list[dict[str, str]]) -> RuntimeHealthCheck:
    values = sorted({row.get("server_time_status", "") for row in rows if row.get("server_time_status", "")})
    if not values:
        return RuntimeHealthCheck("server_time_status", "WARN", "No server-time status values found.")
    if values == ["CLOCK_OK"]:
        return RuntimeHealthCheck("server_time_status", "PASS", "All rows report CLOCK_OK.")
    latest_status = rows[-1].get("server_time_status", "") if rows else ""
    if latest_status == "CLOCK_OK":
        historical_non_ok = sum(1 for row in rows[:-1] if row.get("server_time_status", "") != "CLOCK_OK")
        return RuntimeHealthCheck(
            "server_time_status",
            "PASS",
            f"Latest row reports CLOCK_OK; historical non-CLOCK_OK rows: {historical_non_ok}.",
        )
    return RuntimeHealthCheck("server_time_status", "WARN", "Latest server-time status is " + (latest_status or "blank"))


def _check_exact_duplicates(rows: list[dict[str, str]]) -> RuntimeHealthCheck:
    keys = [
        (row.get("run_id", ""), row.get("timestamp_broker", ""), row.get("bar_time", ""))
        for row in rows
    ]
    duplicates = len(keys) - len(set(keys))
    if duplicates:
        return RuntimeHealthCheck("exact_duplicate_rows", "WARN", f"Exact duplicate runtime rows: {duplicates}.")
    return RuntimeHealthCheck("exact_duplicate_rows", "PASS", "No exact duplicate runtime rows found.")


def _check_unique_bar_gaps(rows: list[dict[str, str]]) -> RuntimeHealthCheck:
    gaps = _unique_bar_gaps(rows)
    long_gaps = [gap for gap in gaps if gap["minutes"] > 5 and not gap["expected_market_break"]]
    tolerated_gaps = [gap for gap in gaps if gap["minutes"] > 5 and gap["expected_market_break"]]
    if not gaps:
        return RuntimeHealthCheck("unique_bar_gaps", "WARN", "Not enough unique bars to evaluate gaps.")
    if long_gaps:
        largest = max(long_gaps, key=lambda item: int(item["minutes"]))
        return RuntimeHealthCheck(
            "unique_bar_gaps",
            "WARN",
            f"Larger-than-M5 gaps: {len(long_gaps)}; largest {largest['minutes']} minute(s).",
        )
    if tolerated_gaps:
        return RuntimeHealthCheck(
            "unique_bar_gaps",
            "PASS",
            f"Only expected market-break gaps found: {len(tolerated_gaps)}.",
        )
    return RuntimeHealthCheck("unique_bar_gaps", "PASS", "Unique bar sequence has no larger-than-M5 gaps.")


def _check_startup_shutdown_balance(
    startup_rows: list[dict[str, str]],
    shutdown_rows: list[dict[str, str]],
) -> RuntimeHealthCheck:
    if not startup_rows:
        return RuntimeHealthCheck("startup_shutdown_rows", "FAIL", "No startup rows found.")
    if len(startup_rows) >= len(shutdown_rows):
        return RuntimeHealthCheck(
            "startup_shutdown_rows",
            "PASS",
            f"Startup rows: {len(startup_rows)}; shutdown rows: {len(shutdown_rows)}.",
        )
    return RuntimeHealthCheck(
        "startup_shutdown_rows",
        "PASS",
        (
            "Startup and shutdown logs are both present; shutdown rows exceed startup rows "
            f"({len(shutdown_rows)} > {len(startup_rows)}) after restart/test cycles."
        ),
    )


def _overall_status(checks: list[RuntimeHealthCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "WARN"
    return "PASS"


def _render_report(
    status: str,
    files_dir: Path,
    decision_rows: list[dict[str, str]],
    startup_rows: list[dict[str, str]],
    shutdown_rows: list[dict[str, str]],
    checks: list[RuntimeHealthCheck],
) -> str:
    latest = decision_rows[-1] if decision_rows else {}
    first_bar, latest_bar = _first_latest_bar(decision_rows)
    gaps = _unique_bar_gaps(decision_rows)
    long_gaps = [gap for gap in gaps if gap["minutes"] > 5 and not gap["expected_market_break"]]
    tolerated_gaps = [gap for gap in gaps if gap["minutes"] > 5 and gap["expected_market_break"]]
    return "\n".join(
        [
            "# Phase 1 Runtime Health Report",
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
            "## Runtime Shape",
            "",
            f"- Decision rows: {len(decision_rows)}",
            f"- Startup rows: {len(startup_rows)}",
            f"- Shutdown rows: {len(shutdown_rows)}",
            f"- Unique run IDs: {len({row.get('run_id', '') for row in decision_rows})}",
            f"- First unique M5 bar: {first_bar or 'n/a'}",
            f"- Latest unique M5 bar: {latest_bar or 'n/a'}",
            f"- Larger-than-M5 gaps: {len(long_gaps)}",
            f"- Expected market-break gaps: {len(tolerated_gaps)}",
            "",
            "## Latest Row",
            "",
            _markdown_table(
                [
                    {
                        "Run ID": latest.get("run_id", "n/a"),
                        "Broker Time": latest.get("timestamp_broker", "n/a"),
                        "Local Time": latest.get("timestamp_local", "n/a"),
                        "Bar Time": latest.get("bar_time", "n/a"),
                        "Dry Run": latest.get("dry_run", "n/a"),
                        "Permission": latest.get("trade_permission", "n/a"),
                        "Server Time": latest.get("server_time_status", "n/a"),
                        "BR Stage": latest.get("br_stage", "n/a"),
                    }
                ]
                if latest
                else [],
                ["Run ID", "Broker Time", "Local Time", "Bar Time", "Dry Run", "Permission", "Server Time", "BR Stage"],
            ),
            "",
            "## Recent Gaps",
            "",
            _markdown_table(
                [
                    {
                        "Left Bar": gap["left"],
                        "Right Bar": gap["right"],
                        "Minutes": str(gap["minutes"]),
                        "Reason": "unexpected",
                    }
                    for gap in long_gaps[-10:]
                ],
                ["Left Bar", "Right Bar", "Minutes", "Reason"],
            ),
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


def _unique_bar_gaps(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    parsed = _unique_bar_rows(rows)
    return [
        {
            "left": left_time.strftime("%Y.%m.%d %H:%M:%S"),
            "right": right_time.strftime("%Y.%m.%d %H:%M:%S"),
            "minutes": int((right_time - left_time).total_seconds() / 60),
            "expected_market_break": _is_expected_market_break(left_time, right_time, left_row, right_row),
        }
        for (left_time, left_row), (right_time, right_row) in zip(parsed, parsed[1:])
    ]


def _unique_bar_rows(rows: list[dict[str, str]]) -> list[tuple[datetime, dict[str, str]]]:
    seen: dict[datetime, dict[str, str]] = {}
    for row in rows:
        parsed = _parse_mt5_datetime(row.get("bar_time", ""))
        if parsed is not None and parsed not in seen:
            seen[parsed] = row
    return sorted(seen.items(), key=lambda item: item[0])


def _is_expected_market_break(
    left: datetime,
    right: datetime,
    left_row: dict[str, str],
    right_row: dict[str, str],
) -> bool:
    minutes = int((right - left).total_seconds() / 60)
    if _is_weekend_stale_resume_gap(right_row):
        return True
    if _spans_weekend_market_break(left, right):
        return True
    if _is_configured_market_break(left, right):
        return True
    if minutes > 90:
        return False
    right_session = right_row.get("session", "")
    left_minute = left.hour * 60 + left.minute
    right_minute = right.hour * 60 + right.minute
    crosses_known_gold_break = left_minute <= 21 * 60 <= right_minute or left_minute <= 22 * 60 <= right_minute
    return right_session == "ROLLOVER" and crosses_known_gold_break


def _is_weekend_stale_resume_gap(row: dict[str, str]) -> bool:
    if row.get("session", "").upper() != "WEEKEND":
        return False
    if row.get("execution_state", "").upper() != "STALE_TICK":
        return False
    timestamp_broker = _parse_mt5_datetime(row.get("timestamp_broker", ""))
    if timestamp_broker is None:
        return False
    return timestamp_broker.weekday() in {5, 6}


def _spans_weekend_market_break(left: datetime, right: datetime) -> bool:
    if right <= left:
        return False
    hours = (right - left).total_seconds() / 3600
    if hours > 96:
        return False
    day = left.date()
    end_day = right.date()
    while day <= end_day:
        if day.weekday() in {5, 6}:
            return True
        day += timedelta(days=1)
    return False


def _is_configured_market_break(left: datetime, right: datetime, path: Path = DEFAULT_EXPECTED_BREAKS) -> bool:
    minutes = int((right - left).total_seconds() / 60)
    for item in _load_expected_market_breaks(path):
        max_gap = _to_int(item.get("max_gap_minutes")) or 0
        if max_gap <= 0 or minutes > max_gap:
            continue
        weekdays = _weekday_indexes(item.get("weekdays", ""))
        if weekdays and left.weekday() not in weekdays:
            continue
        start = _parse_time(item.get("start_utc", ""))
        end = _parse_time(item.get("end_utc", ""))
        if start is None or end is None:
            continue
        start_at = datetime.combine(left.date(), start)
        end_at = datetime.combine(left.date(), end)
        if end_at <= start_at:
            end_at += timedelta(days=1)
        if left <= start_at and right >= end_at:
            return True
    return False


def _load_expected_market_breaks(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- label:"):
            if current:
                rows.append(current)
            current = {"label": _yaml_value(line.split(":", 1)[1])}
            continue
        if current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = _yaml_value(value)
    if current:
        rows.append(current)
    return rows


def _yaml_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _weekday_indexes(value: str) -> set[int]:
    cleaned = value.strip().strip("[]")
    return {
        WEEKDAY_INDEX[item.strip().upper()]
        for item in cleaned.split(",")
        if item.strip().upper() in WEEKDAY_INDEX
    }


def _parse_time(value: str) -> time | None:
    try:
        hour, minute = value.split(":", 1)
        return time(int(hour), int(minute))
    except (ValueError, TypeError):
        return None


def _to_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _first_latest_bar(rows: list[dict[str, str]]) -> tuple[str | None, str | None]:
    parsed = sorted(
        {value for value in (_parse_mt5_datetime(row.get("bar_time", "")) for row in rows) if value}
    )
    if not parsed:
        return None, None
    return parsed[0].strftime("%Y.%m.%d %H:%M:%S"), parsed[-1].strftime("%Y.%m.%d %H:%M:%S")


def _group_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get(key, ""), []).append(row)
    return groups


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def _is_weekend_market_break(now: datetime) -> bool:
    return now.weekday() in {5, 6}


def _markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
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
    parser = argparse.ArgumentParser(description="Generate a Phase 1 runtime health and gap report.")
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument("--max-fresh-minutes", type=int, default=DEFAULT_MAX_FRESH_MINUTES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Markdown report path.")
    args = parser.parse_args(argv)

    output = generate_phase1_runtime_health_report(
        args.files_dir,
        args.report,
        max_fresh_minutes=args.max_fresh_minutes,
    )
    print(f"Phase 1 runtime health report: {output.status}")
    print(output.report_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.message}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
