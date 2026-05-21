from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_HISTORY = Path("outputs") / "reports" / "PHASE1_SOAK_HISTORY.csv"
DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE1_SOAK_HISTORY_REPORT.md"


@dataclass(frozen=True)
class HistoryCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class SoakHistoryReport:
    status: str
    report_path: Path
    rows_analyzed: int
    checks: tuple[HistoryCheck, ...]


def generate_phase1_soak_history_report(
    history_path: Path | None = None,
    report_path: Path | None = None,
) -> SoakHistoryReport:
    if history_path is None:
        history_path = DEFAULT_HISTORY
    if report_path is None:
        report_path = DEFAULT_REPORT

    history_path = history_path.resolve()
    report_path = report_path.resolve()
    rows = _read_csv(history_path)
    checks = [
        _check_history_exists(history_path),
        _check_rows(rows),
        _check_created_at(rows),
        _check_latest_status(rows),
        _check_safety_state(rows),
        _check_progress_monotonic(rows),
    ]
    status = _overall_status(checks)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, history_path, rows, checks), encoding="utf-8")
    return SoakHistoryReport(status, report_path, len(rows), tuple(checks))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _check_history_exists(path: Path) -> HistoryCheck:
    if path.exists():
        return HistoryCheck("history_exists", "PASS", f"Found `{path}`.")
    return HistoryCheck("history_exists", "FAIL", f"Missing `{path}`.")


def _check_rows(rows: list[dict[str, str]]) -> HistoryCheck:
    if rows:
        return HistoryCheck("history_rows", "PASS", f"History rows available: {len(rows)}.")
    return HistoryCheck("history_rows", "FAIL", "No soak-history rows found.")


def _check_created_at(rows: list[dict[str, str]]) -> HistoryCheck:
    parsed = [_parse_iso(row.get("created_at_utc", "")) for row in rows]
    bad = sum(1 for value in parsed if value is None)
    if bad:
        return HistoryCheck("created_at_parse", "WARN", f"Rows with unparseable summary timestamp: {bad}.")
    if len(parsed) > 1 and any(left > right for left, right in zip(parsed, parsed[1:]) if left and right):
        return HistoryCheck("created_at_parse", "WARN", "Summary timestamps are not monotonic.")
    return HistoryCheck("created_at_parse", "PASS", "All summary timestamps are parseable and ordered.")


def _check_latest_status(rows: list[dict[str, str]]) -> HistoryCheck:
    if not rows:
        return HistoryCheck("latest_status", "FAIL", "No latest row available.")
    latest = rows[-1]
    bad = [
        name
        for name in ("log_verification", "soak_analysis", "runtime_health")
        if latest.get(name, "") != "PASS"
    ]
    warn = []
    if latest.get("would_signal", "") != "PASS":
        warn.append("would_signal")
    acceptance = latest.get("acceptance", "")
    if bad:
        return HistoryCheck("latest_status", "FAIL", "Unexpected latest status fields: " + ", ".join(bad))
    if acceptance not in {"PASS", "PENDING"}:
        warn.append("acceptance")
    if warn:
        return HistoryCheck("latest_status", "WARN", "Latest warning status fields: " + ", ".join(warn))
    return HistoryCheck(
        "latest_status",
        "PASS",
        f"Latest status is healthy; acceptance is {acceptance}.",
    )


def _check_safety_state(rows: list[dict[str, str]]) -> HistoryCheck:
    if not rows:
        return HistoryCheck("latest_safety_state", "FAIL", "No latest row available.")
    latest = rows[-1]
    dry_run = latest.get("latest_dry_run", "").lower()
    permission = latest.get("latest_trade_permission", "").lower()
    if dry_run == "true" and permission == "false":
        return HistoryCheck("latest_safety_state", "PASS", "Latest row stayed dry-run and permission-locked.")
    return HistoryCheck(
        "latest_safety_state",
        "FAIL",
        f"Unexpected dry-run/permission state: dry_run={dry_run or 'blank'}, permission={permission or 'blank'}.",
    )


def _check_progress_monotonic(rows: list[dict[str, str]]) -> HistoryCheck:
    values = [_to_float(row.get("soak_progress_pct", "")) for row in rows]
    parsed = [value for value in values if value is not None]
    if not parsed:
        return HistoryCheck("progress_monotonic", "WARN", "No numeric soak progress values found.")
    if len(parsed) > 1 and any(left > right for left, right in zip(parsed, parsed[1:])):
        return HistoryCheck("progress_monotonic", "WARN", "Soak progress decreased between history rows.")
    return HistoryCheck("progress_monotonic", "PASS", "Soak progress is monotonic.")


def _overall_status(checks: list[HistoryCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "WARN"
    return "PASS"


def _render_report(
    status: str,
    history_path: Path,
    rows: list[dict[str, str]],
    checks: list[HistoryCheck],
) -> str:
    latest = rows[-1] if rows else {}
    first = rows[0] if rows else {}
    return "\n".join(
        [
            "# Phase 1 Soak History Report",
            "",
            f"Overall status: {status}",
            "",
            f"History CSV: `{history_path}`",
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": item.name, "Status": item.status, "Message": item.message} for item in checks],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Summary",
            "",
            f"- History rows: {len(rows)}",
            f"- First summary: {first.get('created_at_utc', 'n/a') if first else 'n/a'}",
            f"- Latest summary: {latest.get('created_at_utc', 'n/a') if latest else 'n/a'}",
            f"- Latest M5 bar: {latest.get('latest_bar_time', 'n/a') if latest else 'n/a'}",
            f"- Latest soak progress: {latest.get('soak_progress_pct', 'n/a') if latest else 'n/a'}%",
            f"- Latest would-signal rows: {latest.get('would_signal_rows', 'n/a') if latest else 'n/a'}",
            f"- Latest setup clusters: {latest.get('would_signal_clusters', 'n/a') if latest else 'n/a'}",
            "",
            "## Latest Status",
            "",
            _markdown_table(
                [
                    {
                        "Log": latest.get("log_verification", "n/a"),
                        "Soak": latest.get("soak_analysis", "n/a"),
                        "Runtime": latest.get("runtime_health", "n/a"),
                        "Would-Signal": latest.get("would_signal", "n/a"),
                        "Acceptance": latest.get("acceptance", "n/a"),
                        "Dry Run": latest.get("latest_dry_run", "n/a"),
                        "Permission": latest.get("latest_trade_permission", "n/a"),
                    }
                ]
                if latest
                else [],
                ["Log", "Soak", "Runtime", "Would-Signal", "Acceptance", "Dry Run", "Permission"],
            ),
            "",
            "## Recent History",
            "",
            _markdown_table(
                [
                    {
                        "Summary UTC": row.get("created_at_utc", ""),
                        "Latest Bar": row.get("latest_bar_time", ""),
                        "Rows": row.get("decision_rows", ""),
                        "Progress %": row.get("soak_progress_pct", ""),
                        "Would Rows": row.get("would_signal_rows", ""),
                        "Clusters": row.get("would_signal_clusters", ""),
                        "Acceptance": row.get("acceptance", ""),
                    }
                    for row in rows[-12:]
                ],
                ["Summary UTC", "Latest Bar", "Rows", "Progress %", "Would Rows", "Clusters", "Acceptance"],
            ),
            "",
        ]
    )


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
    parser = argparse.ArgumentParser(description="Generate a Phase 1 soak-history markdown report.")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY, help="Soak-history CSV path.")
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Markdown report path.",
    )
    args = parser.parse_args(argv)

    output = generate_phase1_soak_history_report(args.history, args.report)
    print(f"Phase 1 soak history report: {output.status}")
    print(output.report_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.message}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
