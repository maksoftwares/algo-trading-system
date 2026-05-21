from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DECISION_LOG = "decision_log.csv"
STARTUP_LOG = "startup_log.csv"
SHUTDOWN_LOG = "shutdown_log.csv"
DEFAULT_MAX_FRESH_MINUTES = 15
DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE1_RUNTIME_HEALTH_REPORT.md"


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
    return RuntimeHealthCheck("server_time_status", "WARN", "Observed values: " + ", ".join(values))


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
    long_gaps = [gap for gap in gaps if gap["minutes"] > 5]
    if not gaps:
        return RuntimeHealthCheck("unique_bar_gaps", "WARN", "Not enough unique bars to evaluate gaps.")
    if long_gaps:
        largest = max(long_gaps, key=lambda item: int(item["minutes"]))
        return RuntimeHealthCheck(
            "unique_bar_gaps",
            "WARN",
            f"Larger-than-M5 gaps: {len(long_gaps)}; largest {largest['minutes']} minute(s).",
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
        "WARN",
        f"Shutdown rows exceed startup rows: {len(shutdown_rows)} > {len(startup_rows)}.",
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
    long_gaps = [gap for gap in gaps if gap["minutes"] > 5]
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
                    }
                    for gap in long_gaps[-10:]
                ],
                ["Left Bar", "Right Bar", "Minutes"],
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
    parsed = sorted(
        {value for value in (_parse_mt5_datetime(row.get("bar_time", "")) for row in rows) if value}
    )
    return [
        {
            "left": left.strftime("%Y.%m.%d %H:%M:%S"),
            "right": right.strftime("%Y.%m.%d %H:%M:%S"),
            "minutes": int((right - left).total_seconds() / 60),
        }
        for left, right in zip(parsed, parsed[1:])
    ]


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
