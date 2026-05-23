from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from generate_phase1_status_summary import generate_phase1_status_summary


DEFAULT_SUMMARY = Path("outputs") / "reports" / "PHASE1_STATUS_SUMMARY.json"
DEFAULT_HISTORY = Path("outputs") / "reports" / "PHASE1_SOAK_HISTORY.csv"

HISTORY_FIELDS = [
    "created_at_utc",
    "files_dir",
    "log_verification",
    "soak_analysis",
    "runtime_health",
    "would_signal",
    "acceptance",
    "decision_rows",
    "unique_run_ids",
    "latest_run_id",
    "latest_bar_time",
    "latest_timestamp_broker",
    "latest_timestamp_local",
    "latest_risk_state",
    "latest_trade_permission",
    "latest_dry_run",
    "latest_server_time_status",
    "latest_br_stage",
    "latest_br_direction",
    "latest_br_would_signal",
    "would_signal_rows",
    "would_signal_clusters",
    "required_soak_days",
    "observed_soak_days",
    "soak_progress_pct",
    "soak_current_streak_hours",
    "soak_longest_streak_hours",
    "soak_active_market_streak_hours",
    "soak_required_uninterrupted_streak_hours",
    "soak_uninterrupted_pass",
    "soak_weekend_policy",
    "soak_process_uptime_streak_hours",
    "soak_code_freeze_started_at",
    "soak_code_freeze_hours",
    "soak_required_code_freeze_hours",
    "soak_code_freeze_pass",
    "soak_process_code_freeze_pass",
    "soak_last_restart_utc",
    "summary_path",
    "log_report",
    "soak_report",
    "would_signal_report",
    "would_signal_csv",
    "acceptance_report",
]


@dataclass(frozen=True)
class SoakHistoryOutput:
    history_path: Path
    row_count: int
    appended: bool
    created_at_utc: str
    latest_bar_time: str
    acceptance_status: str


def append_phase1_soak_history(
    files_dir: Path | None = None,
    summary_path: Path | None = None,
    history_path: Path | None = None,
    compile_log: Path | None = None,
    source_root: Path | None = None,
    now: datetime | None = None,
) -> SoakHistoryOutput:
    if summary_path is None:
        summary_path = DEFAULT_SUMMARY
    if history_path is None:
        history_path = DEFAULT_HISTORY

    summary_path = summary_path.resolve()
    history_path = history_path.resolve()

    if files_dir is not None:
        generate_phase1_status_summary(files_dir, summary_path, compile_log, source_root, now=now)

    if not summary_path.exists():
        raise FileNotFoundError(f"Phase 1 status summary not found: {summary_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    row = _summary_to_history_row(summary, summary_path)
    existing_rows = _read_history(history_path)
    existing_created_at = {existing.get("created_at_utc", "") for existing in existing_rows}

    appended = False
    if row["created_at_utc"] not in existing_created_at:
        existing_rows.append(row)
        appended = True

    _write_history(history_path, existing_rows)
    return SoakHistoryOutput(
        history_path=history_path,
        row_count=len(existing_rows),
        appended=appended,
        created_at_utc=row["created_at_utc"],
        latest_bar_time=row["latest_bar_time"],
        acceptance_status=row["acceptance"],
    )


def _summary_to_history_row(summary: dict[str, Any], summary_path: Path) -> dict[str, str]:
    status = _mapping(summary.get("status"))
    runtime = _mapping(summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    would_signal = _mapping(summary.get("would_signal"))
    soak = _mapping(summary.get("soak"))
    reports = _mapping(summary.get("reports"))

    return {
        "created_at_utc": _cell(summary.get("created_at_utc")),
        "files_dir": _cell(summary.get("files_dir")),
        "log_verification": _cell(status.get("log_verification")),
        "soak_analysis": _cell(status.get("soak_analysis")),
        "runtime_health": _cell(status.get("runtime_health")),
        "would_signal": _cell(status.get("would_signal")),
        "acceptance": _cell(status.get("acceptance")),
        "decision_rows": _cell(runtime.get("decision_rows")),
        "unique_run_ids": _cell(runtime.get("unique_run_ids")),
        "latest_run_id": _cell(latest.get("run_id")),
        "latest_bar_time": _cell(latest.get("bar_time")),
        "latest_timestamp_broker": _cell(latest.get("timestamp_broker")),
        "latest_timestamp_local": _cell(latest.get("timestamp_local")),
        "latest_risk_state": _cell(latest.get("risk_state")),
        "latest_trade_permission": _cell(latest.get("trade_permission")),
        "latest_dry_run": _cell(latest.get("dry_run")),
        "latest_server_time_status": _cell(latest.get("server_time_status")),
        "latest_br_stage": _cell(latest.get("br_stage")),
        "latest_br_direction": _cell(latest.get("br_direction")),
        "latest_br_would_signal": _cell(latest.get("br_would_signal")),
        "would_signal_rows": _cell(would_signal.get("rows")),
        "would_signal_clusters": _cell(would_signal.get("clusters")),
        "required_soak_days": _cell(soak.get("required_days")),
        "observed_soak_days": _cell(soak.get("observed_days")),
        "soak_progress_pct": _cell(soak.get("progress_pct")),
        "soak_current_streak_hours": _cell(soak.get("current_streak_hours")),
        "soak_longest_streak_hours": _cell(soak.get("longest_streak_hours")),
        "soak_active_market_streak_hours": _cell(soak.get("active_market_streak_hours")),
        "soak_required_uninterrupted_streak_hours": _cell(soak.get("required_uninterrupted_streak_hours")),
        "soak_uninterrupted_pass": _cell(soak.get("uninterrupted_soak_pass")),
        "soak_weekend_policy": _cell(soak.get("weekend_policy")),
        "soak_process_uptime_streak_hours": _cell(soak.get("process_uptime_streak_hours")),
        "soak_code_freeze_started_at": _cell(soak.get("code_freeze_started_at")),
        "soak_code_freeze_hours": _cell(soak.get("code_freeze_hours")),
        "soak_required_code_freeze_hours": _cell(soak.get("required_code_freeze_hours")),
        "soak_code_freeze_pass": _cell(soak.get("code_freeze_pass")),
        "soak_process_code_freeze_pass": _cell(soak.get("process_code_freeze_pass")),
        "soak_last_restart_utc": _cell(soak.get("last_restart_utc")),
        "summary_path": str(summary_path),
        "log_report": _cell(reports.get("log_report")),
        "soak_report": _cell(reports.get("soak_report")),
        "would_signal_report": _cell(reports.get("would_signal_report")),
        "would_signal_csv": _cell(would_signal.get("csv_path")),
        "acceptance_report": _cell(reports.get("acceptance_report")),
    }


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _read_history(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {field: row.get(field, "") for field in HISTORY_FIELDS}
            for row in csv.DictReader(handle)
        ]


def _write_history(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append the latest Phase 1 status summary to soak history.")
    parser.add_argument(
        "--files-dir",
        type=Path,
        default=None,
        help="Optional MT5 MQL5/Files directory. When supplied, a fresh status summary is generated first.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
        help="Phase 1 status summary JSON path.",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_HISTORY,
        help="Output soak history CSV path.",
    )
    parser.add_argument(
        "--compile-log",
        type=Path,
        default=Path("C:/MT5PortableGoldMission/compile_Phase1DryRunShell.log"),
        help="Optional MetaEditor compile log path used when generating a fresh summary.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 source root used when generating a fresh summary.",
    )
    args = parser.parse_args(argv)

    output = append_phase1_soak_history(
        args.files_dir,
        args.summary,
        args.history,
        args.compile_log,
        args.source_root,
    )
    print(f"Phase 1 soak history: {output.history_path}")
    print(f"Rows: {output.row_count}")
    print(f"Appended: {str(output.appended).lower()}")
    print(f"Latest bar: {output.latest_bar_time}")
    print(f"Acceptance status: {output.acceptance_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
