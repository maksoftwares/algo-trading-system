from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DECISION_LOG = "decision_log.csv"
STARTUP_LOG = "startup_log.csv"
SHUTDOWN_LOG = "shutdown_log.csv"

DECISION_REQUIRED_COLUMNS = (
    "timestamp_broker",
    "timestamp_utc",
    "timestamp_local",
    "run_id",
    "lifecycle_state",
    "symbol",
    "bar_time",
    "session",
    "regime",
    "router_version",
    "risk_state",
    "risk_ok",
    "execution_state",
    "news_state",
    "expert_lifecycle_state",
    "magic_namespace_ok",
    "server_time_status",
    "br_stage",
    "br_direction",
    "br_would_signal",
    "br_reason_code",
    "br_level_found",
    "br_break_found",
    "br_retest_valid",
    "br_confirmation_valid",
    "br_level_kind",
    "br_level_price",
    "br_entry_price",
    "br_stop_loss",
    "br_take_profit",
    "br_stop_distance_points",
    "br_break_shift",
    "sbr_stage",
    "sbr_direction",
    "sbr_would_signal",
    "sbr_reason_code",
    "sbr_level_found",
    "sbr_break_found",
    "sbr_retest_valid",
    "sbr_confirmation_valid",
    "sbr_level_kind",
    "sbr_level_price",
    "sbr_entry_price",
    "sbr_stop_loss",
    "sbr_take_profit",
    "sbr_stop_distance_points",
    "sbr_break_shift",
    "allowed_expert",
    "would_have_allowed_experts",
    "trade_permission",
    "block_reason",
    "dry_run",
)

STARTUP_REQUIRED_COLUMNS = (
    "timestamp_broker",
    "timestamp_utc",
    "timestamp_local",
    "run_id",
    "symbol",
    "dry_run_only",
    "magic_namespace_ok",
    "server_time_status",
)

SHUTDOWN_REQUIRED_COLUMNS = (
    "timestamp_broker",
    "timestamp_utc",
    "timestamp_local",
    "run_id",
    "symbol",
    "shutdown_reason",
    "last_m5_bar_time",
    "last_decision_write_time",
    "lifecycle_state",
)


@dataclass(frozen=True)
class LogCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class LogVerification:
    status: str
    report_path: Path
    checks: tuple[LogCheck, ...]


def verify_phase1_logs(files_dir: Path, report_path: Path | None = None) -> LogVerification:
    files_dir = files_dir.resolve()
    if report_path is None:
        report_path = Path.cwd() / "outputs" / "reports" / "PHASE1_DRY_RUN_LOG_REPORT.md"

    decision_path = files_dir / DECISION_LOG
    startup_path = files_dir / STARTUP_LOG
    shutdown_path = files_dir / SHUTDOWN_LOG

    decision_rows, decision_columns = _read_csv(decision_path)
    startup_rows, startup_columns = _read_csv(startup_path)
    shutdown_rows, shutdown_columns = _read_csv(shutdown_path)

    checks = [
        _check_file("decision_log_exists", decision_path),
        _check_file("startup_log_exists", startup_path),
        _check_optional_file("shutdown_log_exists", shutdown_path),
        _check_columns("decision_schema", decision_columns, DECISION_REQUIRED_COLUMNS),
        _check_columns("startup_schema", startup_columns, STARTUP_REQUIRED_COLUMNS),
        _check_columns("shutdown_schema", shutdown_columns, SHUTDOWN_REQUIRED_COLUMNS)
        if shutdown_path.exists()
        else LogCheck("shutdown_schema", "WARN", "No shutdown log exists yet."),
        _check_duplicate_headers("decision_duplicate_headers", decision_path),
        _check_duplicate_headers("startup_duplicate_headers", startup_path),
        _check_duplicate_headers("shutdown_duplicate_headers", shutdown_path)
        if shutdown_path.exists()
        else LogCheck("shutdown_duplicate_headers", "WARN", "No shutdown log exists yet."),
        _check_decision_rows(decision_rows),
        _check_dry_run_locked(decision_rows),
        _check_permission_locked(decision_rows),
        _check_breakout_observation(decision_rows),
        _check_breakout_retest_observer(decision_rows),
        _check_swing_breakout_observation(decision_rows),
        _check_swing_breakout_retest_observer(decision_rows),
        _check_startup_rows(startup_rows),
        _check_shutdown_rows(shutdown_rows),
        _check_bar_cadence(decision_rows),
        _check_risk_states(decision_rows),
    ]

    status = _overall_status(checks)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, files_dir, checks, decision_rows), encoding="utf-8")
    return LogVerification(status=status, report_path=report_path, checks=tuple(checks))


def _read_csv(path: Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    if not path.exists():
        return [], ()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), tuple(reader.fieldnames or ())


def _check_file(name: str, path: Path) -> LogCheck:
    if path.exists():
        return LogCheck(name, "PASS", f"Found {path}.")
    return LogCheck(name, "FAIL", f"Missing {path}.")


def _check_optional_file(name: str, path: Path) -> LogCheck:
    if path.exists():
        return LogCheck(name, "PASS", f"Found {path}.")
    return LogCheck(name, "WARN", f"Missing optional lifecycle log {path}.")


def _check_columns(name: str, columns: tuple[str, ...], required: tuple[str, ...]) -> LogCheck:
    missing = [column for column in required if column not in columns]
    if missing:
        return LogCheck(name, "FAIL", "Missing column(s): " + ", ".join(missing))
    return LogCheck(name, "PASS", f"Required columns present ({len(required)} checked).")


def _check_duplicate_headers(name: str, path: Path) -> LogCheck:
    if not path.exists():
        return LogCheck(name, "WARN", f"Missing {path}.")
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines:
        return LogCheck(name, "FAIL", f"{path} is empty.")
    header = lines[0].strip()
    repeats = sum(1 for line in lines[1:] if line.strip() == header)
    if repeats:
        return LogCheck(name, "FAIL", f"Duplicate CSV header rows found: {repeats}.")
    return LogCheck(name, "PASS", "No duplicate CSV headers found.")


def _check_decision_rows(rows: list[dict[str, str]]) -> LogCheck:
    if rows:
        return LogCheck("decision_rows", "PASS", f"Decision rows: {len(rows)}.")
    return LogCheck("decision_rows", "FAIL", "No decision rows found.")


def _check_dry_run_locked(rows: list[dict[str, str]]) -> LogCheck:
    bad = [
        row.get("run_id", "")
        for row in rows
        if row.get("dry_run", "").lower() != "true" or row.get("lifecycle_state") != "DRY_RUN"
    ]
    if bad:
        return LogCheck("dry_run_locked", "FAIL", f"Rows outside dry-run state: {len(bad)}.")
    return LogCheck("dry_run_locked", "PASS", "All decision rows are dry-run.")


def _check_permission_locked(rows: list[dict[str, str]]) -> LogCheck:
    bad = [row.get("run_id", "") for row in rows if row.get("trade_permission", "").lower() != "false"]
    if bad:
        return LogCheck("trade_permission_locked", "FAIL", f"Rows with permission not false: {len(bad)}.")
    return LogCheck("trade_permission_locked", "PASS", "All decision rows keep permission false.")


def _check_breakout_observation(rows: list[dict[str, str]]) -> LogCheck:
    observed = any("breakout_retest" in _expert_list(row.get("would_have_allowed_experts", "")) for row in rows)
    if observed:
        return LogCheck("breakout_observation", "PASS", "breakout_retest appears as dry-run observed expert.")
    return LogCheck("breakout_observation", "WARN", "breakout_retest was not observed in decision rows.")


def _check_breakout_retest_observer(rows: list[dict[str, str]]) -> LogCheck:
    stages = sorted({row.get("br_stage", "") for row in rows if row.get("br_stage", "")})
    if not stages:
        return LogCheck("breakout_retest_observer", "FAIL", "No breakout_retest observer stages found.")
    if all(stage == "NOT_EVALUATED" for stage in stages):
        return LogCheck("breakout_retest_observer", "WARN", "Observer only reported NOT_EVALUATED.")
    return LogCheck("breakout_retest_observer", "PASS", "Observer stages found: " + ", ".join(stages))


def _check_swing_breakout_observation(rows: list[dict[str, str]]) -> LogCheck:
    observed = any("swing_breakout_retest_v0" in _expert_list(row.get("would_have_allowed_experts", "")) for row in rows)
    if observed:
        return LogCheck(
            "swing_breakout_observation",
            "PASS",
            "swing_breakout_retest_v0 appears as dry-run observed expert.",
        )
    return LogCheck("swing_breakout_observation", "WARN", "swing_breakout_retest_v0 was not observed in decision rows.")


def _check_swing_breakout_retest_observer(rows: list[dict[str, str]]) -> LogCheck:
    stages = sorted({row.get("sbr_stage", "") for row in rows if row.get("sbr_stage", "")})
    if not stages:
        return LogCheck("swing_breakout_retest_observer", "FAIL", "No swing_breakout_retest_v0 observer stages found.")
    if all(stage == "NOT_EVALUATED" for stage in stages):
        return LogCheck("swing_breakout_retest_observer", "WARN", "Swing observer only reported NOT_EVALUATED.")
    return LogCheck("swing_breakout_retest_observer", "PASS", "Swing observer stages found: " + ", ".join(stages))


def _check_startup_rows(rows: list[dict[str, str]]) -> LogCheck:
    if len(rows) >= 2:
        return LogCheck("startup_restarts", "PASS", f"Startup rows: {len(rows)}; restart append observed.")
    if len(rows) == 1:
        return LogCheck("startup_restarts", "WARN", "Only one startup row found.")
    return LogCheck("startup_restarts", "FAIL", "No startup rows found.")


def _check_shutdown_rows(rows: list[dict[str, str]]) -> LogCheck:
    if rows:
        return LogCheck("shutdown_rows", "PASS", f"Shutdown rows: {len(rows)}.")
    return LogCheck("shutdown_rows", "WARN", "No shutdown rows found.")


def _check_bar_cadence(rows: list[dict[str, str]]) -> LogCheck:
    ordered = _unique_bar_rows(rows)
    if len(ordered) < 2:
        return LogCheck("bar_cadence", "WARN", "Not enough unique bar times to evaluate cadence.")

    exact_row_keys = {
        (
            row.get("run_id", ""),
            row.get("timestamp_broker", ""),
            row.get("bar_time", ""),
        )
        for row in rows
    }
    duplicate_count = len(rows) - len(exact_row_keys)
    gaps: list[int] = []
    tolerated_gaps: list[int] = []
    for (left, left_row), (right, right_row) in zip(ordered, ordered[1:]):
        minutes = int((right - left).total_seconds() / 60)
        if minutes <= 5:
            continue
        if _is_expected_market_break(left, right, left_row, right_row):
            tolerated_gaps.append(minutes)
        else:
            gaps.append(minutes)
    if duplicate_count:
        return LogCheck(
            "bar_cadence",
            "WARN",
            f"Exact duplicate decision rows: {duplicate_count}; larger-than-M5 gaps: {len(gaps)}.",
        )
    if gaps:
        return LogCheck("bar_cadence", "WARN", f"Larger-than-M5 gaps found: {len(gaps)}.")
    if tolerated_gaps:
        return LogCheck(
            "bar_cadence",
            "PASS",
            f"Decision rows follow M5 cadence outside expected market breaks; tolerated gaps: {len(tolerated_gaps)}.",
        )
    return LogCheck("bar_cadence", "PASS", "Decision rows follow M5 cadence; restart duplicates are tolerated.")


def _check_risk_states(rows: list[dict[str, str]]) -> LogCheck:
    states = sorted({row.get("risk_state", "") for row in rows if row.get("risk_state", "")})
    required_locks = {"LOCKED_DAILY_LOSS", "LOCKED_WEEKLY_LOSS", "LOCKED_MONTHLY_LOSS", "MANUAL_LOCK"}
    missing = sorted(required_locks.difference(states))
    if missing:
        return LogCheck("risk_state_coverage", "WARN", "Missing simulated state(s): " + ", ".join(missing))
    return LogCheck("risk_state_coverage", "PASS", "All simulated lock states observed.")


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


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
    if minutes > 90:
        return False
    right_session = right_row.get("session", "")
    left_minute = left.hour * 60 + left.minute
    right_minute = right.hour * 60 + right.minute
    crosses_known_gold_break = left_minute <= 21 * 60 <= right_minute or left_minute <= 22 * 60 <= right_minute
    return right_session == "ROLLOVER" and crosses_known_gold_break


def _overall_status(checks: list[LogCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "WARN"
    return "PASS"


def _render_report(
    status: str,
    files_dir: Path,
    checks: list[LogCheck],
    decision_rows: list[dict[str, str]],
) -> str:
    risk_states = _counts(row.get("risk_state", "") for row in decision_rows)
    block_reasons = _counts(row.get("block_reason", "") for row in decision_rows)
    breakout_stages = _counts(row.get("br_stage", "") for row in decision_rows)
    breakout_directions = _counts(row.get("br_direction", "") for row in decision_rows)
    breakout_signal_counts = _counts(row.get("br_would_signal", "") for row in decision_rows)
    swing_stages = _counts(row.get("sbr_stage", "") for row in decision_rows)
    swing_directions = _counts(row.get("sbr_direction", "") for row in decision_rows)
    swing_signal_counts = _counts(row.get("sbr_would_signal", "") for row in decision_rows)
    latest = decision_rows[-1] if decision_rows else {}
    return "\n".join(
        [
            "# Phase 1 Dry-Run Log Report",
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
            "## Summary",
            "",
            f"- Decision rows: {len(decision_rows)}",
            f"- Unique run IDs: {len({row.get('run_id', '') for row in decision_rows})}",
            f"- Latest run ID: {decision_rows[-1].get('run_id', '') if decision_rows else 'n/a'}",
            "",
            "## Risk States",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in risk_states.items()],
                ["Value", "Count"],
            ),
            "",
            "## Block Reasons",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in block_reasons.items()],
                ["Value", "Count"],
            ),
            "",
            "## Breakout-Retest Observer",
            "",
            "### Stages",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in breakout_stages.items()],
                ["Value", "Count"],
            ),
            "",
            "### Directions",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in breakout_directions.items()],
                ["Value", "Count"],
            ),
            "",
            "### Would-Signal",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in breakout_signal_counts.items()],
                ["Value", "Count"],
            ),
            "",
            "## Swing Breakout-Retest Observer",
            "",
            "### Stages",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in swing_stages.items()],
                ["Value", "Count"],
            ),
            "",
            "### Directions",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in swing_directions.items()],
                ["Value", "Count"],
            ),
            "",
            "### Would-Signal",
            "",
            _markdown_table(
                [{"Value": key, "Count": str(value)} for key, value in swing_signal_counts.items()],
                ["Value", "Count"],
            ),
            "",
            "### Latest Observer Row",
            "",
            _markdown_table(
                [
                    {
                        "Run ID": latest.get("run_id", "n/a"),
                        "Bar Time": latest.get("bar_time", "n/a"),
                        "Stage": latest.get("br_stage", "n/a"),
                        "Direction": latest.get("br_direction", "n/a"),
                        "Reason": latest.get("br_reason_code", "n/a"),
                        "Level": latest.get("br_level_price", "n/a"),
                        "Would Signal": latest.get("br_would_signal", "n/a"),
                    }
                ]
                if latest
                else [],
                ["Run ID", "Bar Time", "Stage", "Direction", "Reason", "Level", "Would Signal"],
            ),
            "",
        ]
    )


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = value or "blank"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _expert_list(value: str) -> set[str]:
    return {item.strip() for item in value.replace(",", ";").split(";") if item.strip()}


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 1 dry-run MT5 CSV logs.")
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_DRY_RUN_LOG_REPORT.md",
        help="Markdown report path.",
    )
    args = parser.parse_args(argv)

    output = verify_phase1_logs(args.files_dir, args.report)
    print(f"Phase 1 log verification: {output.status}")
    print(output.report_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.message}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
