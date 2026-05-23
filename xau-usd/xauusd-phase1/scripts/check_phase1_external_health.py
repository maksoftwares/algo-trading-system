from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DECISION_LOG = "decision_log.csv"
EXPECTED_PASS_STATUSES = ("PASS", "PENDING", "WARN")


@dataclass(frozen=True)
class HealthCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class ExternalHealthOutput:
    status: str
    checks: tuple[HealthCheck, ...]
    output_path: Path | None


def check_external_health(
    files_dir: Path,
    status_summary: Path,
    output_path: Path | None = None,
    now: datetime | None = None,
    max_fresh_minutes: int = 15,
) -> ExternalHealthOutput:
    files_dir = files_dir.resolve()
    status_summary = status_summary.resolve()
    if now is None:
        now = datetime.now()

    decision_rows = _read_csv(files_dir / DECISION_LOG)
    latest = decision_rows[-1] if decision_rows else {}
    checks = [
        _decision_log_exists(files_dir / DECISION_LOG, decision_rows),
        _summary_exists(status_summary),
        _summary_status(status_summary),
        _freshness_check(latest, now, max_fresh_minutes),
        _dry_run_check(latest),
        _permission_check(latest),
        _server_time_check(latest),
    ]
    status = "PASS" if all(check.status in EXPECTED_PASS_STATUSES for check in checks) else "FAIL"
    output = ExternalHealthOutput(status=status, checks=tuple(checks), output_path=output_path)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_render_json(output, files_dir, status_summary, now), encoding="utf-8")
    return output


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _decision_log_exists(path: Path, rows: list[dict[str, str]]) -> HealthCheck:
    if not path.exists():
        return HealthCheck("decision_log_exists", "FAIL", f"Missing {path}")
    if not rows:
        return HealthCheck("decision_log_has_rows", "FAIL", f"No rows in {path}")
    return HealthCheck("decision_log_has_rows", "PASS", f"{len(rows)} row(s) in {path}")


def _summary_exists(path: Path) -> HealthCheck:
    return HealthCheck(
        "status_summary_exists",
        "PASS" if path.exists() else "FAIL",
        f"Found {path}" if path.exists() else f"Missing {path}",
    )


def _summary_status(path: Path) -> HealthCheck:
    if not path.exists():
        return HealthCheck("status_summary_health", "FAIL", f"Missing {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    statuses = data.get("status", {})
    bad = {
        key: value
        for key, value in statuses.items()
        if value not in EXPECTED_PASS_STATUSES
    }
    if bad:
        return HealthCheck("status_summary_health", "FAIL", f"Unexpected status values: {bad}")
    return HealthCheck("status_summary_health", "PASS", f"Statuses are acceptable: {statuses}")


def _freshness_check(
    latest: dict[str, str],
    now: datetime,
    max_fresh_minutes: int,
) -> HealthCheck:
    timestamp = _parse_mt5_datetime(latest.get("timestamp_local", ""))
    if timestamp is None:
        return HealthCheck("latest_row_freshness", "FAIL", "Latest row has no parseable timestamp_local.")
    age_minutes = (now - timestamp).total_seconds() / 60
    if age_minutes <= max_fresh_minutes:
        return HealthCheck(
            "latest_row_freshness",
            "PASS",
            f"Latest row age {age_minutes:.1f} minute(s), limit {max_fresh_minutes}.",
        )
    if _is_weekend_market_break(now):
        return HealthCheck(
            "latest_row_freshness",
            "PASS",
            (
                f"Latest row age {age_minutes:.1f} minute(s), but local date is a weekend "
                "market break; do not count this as a runtime fault."
            ),
        )
    return HealthCheck(
        "latest_row_freshness",
        "FAIL",
        f"Latest row age {age_minutes:.1f} minute(s), limit {max_fresh_minutes}.",
    )


def _dry_run_check(latest: dict[str, str]) -> HealthCheck:
    value = latest.get("dry_run", "").lower()
    return HealthCheck(
        "dry_run_boundary",
        "PASS" if value == "true" else "FAIL",
        f"dry_run={latest.get('dry_run', '')}",
    )


def _permission_check(latest: dict[str, str]) -> HealthCheck:
    value = latest.get("trade_permission", "").lower()
    return HealthCheck(
        "permission_boundary",
        "PASS" if value == "false" else "FAIL",
        f"trade_permission={latest.get('trade_permission', '')}",
    )


def _server_time_check(latest: dict[str, str]) -> HealthCheck:
    value = latest.get("server_time_status", "")
    return HealthCheck(
        "server_time_status",
        "PASS" if value == "CLOCK_OK" else "FAIL",
        f"server_time_status={value}",
    )


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def _is_weekend_market_break(now: datetime) -> bool:
    return now.weekday() in {5, 6}


def _render_json(
    output: ExternalHealthOutput,
    files_dir: Path,
    status_summary: Path,
    now: datetime,
) -> str:
    data = {
        "created_at_local": now.isoformat(),
        "status": output.status,
        "files_dir": str(files_dir),
        "status_summary": str(status_summary),
        "checks": [check.__dict__ for check in output.checks],
    }
    return json.dumps(data, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="External Phase 1 dry-run health check.")
    parser.add_argument("--files-dir", type=Path, required=True)
    parser.add_argument(
        "--status-summary",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_STATUS_SUMMARY.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_EXTERNAL_HEALTH.json",
    )
    parser.add_argument("--max-fresh-minutes", type=int, default=15)
    args = parser.parse_args(argv)

    output = check_external_health(
        files_dir=args.files_dir,
        status_summary=args.status_summary,
        output_path=args.output,
        max_fresh_minutes=args.max_fresh_minutes,
    )
    print(f"External health: {output.status}")
    if output.output_path:
        print(output.output_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.evidence}")
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
