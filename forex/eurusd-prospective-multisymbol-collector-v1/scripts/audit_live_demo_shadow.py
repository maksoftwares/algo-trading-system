from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, time, timezone
from pathlib import Path


FEATURE_NAME = "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
ENVIRONMENT_NAME = "EURUSD_PROSPECTIVE_M5_ENVIRONMENT_V1.csv"
HEARTBEAT_NAME = "EURUSD_PROSPECTIVE_M5_HEARTBEAT_V1.csv"
EXPECTED_SOURCES = (
    "EURUSD|EURGBP|EURJPY|GBPUSD|USDJPY|GBPJPY|"
    "DOLLARIDXUSD|USTBONDTRUSD"
)
TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def utc_text(value: datetime) -> str:
    return value.strftime(TIME_FORMAT)


def audit(
    common_files: Path,
    now_utc: datetime | None = None,
) -> dict[str, object]:
    now = now_utc or datetime.now(timezone.utc).replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)

    feature_rows = read_csv(common_files / FEATURE_NAME)
    environment_rows = read_csv(common_files / ENVIRONMENT_NAME)
    heartbeat_rows = read_csv(common_files / HEARTBEAT_NAME)
    environment = {
        row.get("key", ""): row.get("value", "") for row in environment_rows
    }

    checks = {
        "environment_present": bool(environment_rows),
        "heartbeat_present": bool(heartbeat_rows),
        "scope_is_prospective_demo": all(
            row.get("evidence_scope") == "PROSPECTIVE_DEMO"
            for row in environment_rows + heartbeat_rows + feature_rows
        )
        and bool(environment_rows)
        and bool(heartbeat_rows),
        "account_is_demo": environment.get("account_trade_mode") == "0",
        "trade_permission_is_none": (
            environment.get("trade_permission") == "NONE_READ_ONLY"
        ),
        "chart_is_eurusd_m5": (
            environment.get("target_symbol") == "EURUSD"
            and environment.get("chart_period") == "PERIOD_M5"
        ),
        "source_list_exact": (
            environment.get("reference_symbols") == EXPECTED_SOURCES
        ),
        "forward_floor_exact": (
            environment.get("frozen_forward_floor_utc")
            == "2026.08.01 00:00"
            and environment.get("prospective_start_utc")
            == "2026.08.01 00:00"
        ),
        "startup_latch_present": any(
            row.get("event") == "STARTUP_LATCH" for row in heartbeat_rows
        ),
    }

    floor = datetime.strptime("2026.08.01 00:00:00", TIME_FORMAT)
    before_floor = now < floor
    parsed_feature_times: list[datetime] = []
    try:
        parsed_feature_times = [
            datetime.strptime(row["interval_open_configured_utc"], TIME_FORMAT)
            for row in feature_rows
        ]
    except (KeyError, ValueError):
        parsed_feature_times = []
    checks["no_feature_rows_before_floor"] = (
        not feature_rows
        or (
            len(parsed_feature_times) == len(feature_rows)
            and all(value >= floor for value in parsed_feature_times)
        )
    )
    checks["prestart_transition_refused"] = (
        not before_floor
        or any(
            row.get("event") == "INTERVAL_REFUSED"
            and row.get("detail")
            == "before_frozen_or_configured_prospective_start"
            for row in heartbeat_rows
        )
    )

    latest_heartbeat_utc: datetime | None = None
    if heartbeat_rows:
        try:
            latest_heartbeat_utc = max(
                datetime.strptime(row["recorded_at_utc"], TIME_FORMAT)
                for row in heartbeat_rows
                if row.get("recorded_at_utc")
            )
        except (KeyError, ValueError):
            latest_heartbeat_utc = None
    heartbeat_age_seconds = (
        max(0.0, (now - latest_heartbeat_utc).total_seconds())
        if latest_heartbeat_utc is not None
        else None
    )
    checks["heartbeat_fresh"] = (
        heartbeat_age_seconds is not None and heartbeat_age_seconds <= 300.0
    )

    market_open_expected = (
        now.weekday() < 5
        and time(0, 15) <= now.time() <= time(21, 59, 59)
    )
    latest_feature_utc: datetime | None = None
    if feature_rows:
        try:
            latest_feature_utc = max(
                datetime.strptime(row["recorded_at_utc"], TIME_FORMAT)
                for row in feature_rows
                if row.get("recorded_at_utc")
            )
        except (KeyError, ValueError):
            latest_feature_utc = None
    feature_age_seconds = (
        max(0.0, (now - latest_feature_utc).total_seconds())
        if latest_feature_utc is not None
        else None
    )
    last_interval_rows: list[dict[str, str]] = []
    if parsed_feature_times:
        last_interval = max(parsed_feature_times)
        last_interval_rows = [
            row
            for row, interval_open in zip(feature_rows, parsed_feature_times)
            if interval_open == last_interval
        ]
    checks["forward_rows_available_when_expected"] = (
        before_floor or not market_open_expected or bool(feature_rows)
    )
    checks["forward_features_fresh_when_expected"] = (
        before_floor
        or not market_open_expected
        or (feature_age_seconds is not None and feature_age_seconds <= 600.0)
    )
    checks["last_interval_has_eight_source_rows_when_expected"] = (
        before_floor
        or not market_open_expected
        or len(last_interval_rows) == 8
    )

    if not all(checks.values()):
        status = "FAIL"
    elif before_floor:
        status = "PASS_RUNNING_PRESTART"
    elif not market_open_expected:
        status = "PASS_WAITING_MARKET_OPEN"
    else:
        status = "PASS_RUNNING_FORWARD"
    return {
        "artifact": "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_V1",
        "audited_at_utc": utc_text(now),
        "status": status,
        "account_login": environment.get("account_login"),
        "account_server": environment.get("account_server"),
        "terminal_build": environment.get("terminal_build"),
        "before_forward_floor": before_floor,
        "feature_rows": len(feature_rows),
        "environment_rows": len(environment_rows),
        "heartbeat_rows": len(heartbeat_rows),
        "heartbeat_events": dict(
            sorted(Counter(row.get("event", "") for row in heartbeat_rows).items())
        ),
        "latest_heartbeat_utc": (
            utc_text(latest_heartbeat_utc)
            if latest_heartbeat_utc is not None
            else None
        ),
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "market_open_expected": market_open_expected,
        "latest_feature_utc": (
            utc_text(latest_feature_utc)
            if latest_feature_utc is not None
            else None
        ),
        "feature_age_seconds": feature_age_seconds,
        "last_interval_source_rows": len(last_interval_rows),
        "observed_current_minus_gmt_seconds": environment.get(
            "observed_current_minus_gmt_seconds"
        ),
        "configured_broker_utc_offset_seconds": environment.get(
            "configured_broker_utc_offset_seconds"
        ),
        "source_status": dict(
            sorted(Counter(row.get("source_status", "") for row in feature_rows).items())
        ),
        "checks": checks,
    }


def markdown(result: dict[str, object]) -> str:
    checks = result["checks"]
    assert isinstance(checks, dict)
    lines = [
        "# EURUSD prospective collector live-demo audit",
        "",
        f"Status: `{result['status']}`",
        "",
        f"- Audited at UTC: `{result['audited_at_utc']}`",
        (
            f"- Demo identity: `{result['account_login']} / "
            f"{result['account_server']}`"
        ),
        f"- Terminal build: `{result['terminal_build']}`",
        f"- Feature rows: `{result['feature_rows']}`",
        f"- Heartbeat rows: `{result['heartbeat_rows']}`",
        f"- Latest heartbeat UTC: `{result['latest_heartbeat_utc']}`",
        f"- Heartbeat age seconds: `{result['heartbeat_age_seconds']}`",
        f"- Market open expected: `{result['market_open_expected']}`",
        f"- Latest feature UTC: `{result['latest_feature_utc']}`",
        f"- Feature age seconds: `{result['feature_age_seconds']}`",
        "",
        "## Checks",
        "",
    ]
    for name, passed in checks.items():
        lines.append(f"- [{'x' if passed else ' '}] `{name}`")
    lines.extend(
        [
            "",
            (
                "A pre-start pass proves only that the read-only collector is "
                "running safely. It does not prove a trading edge."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--common-files", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--now-utc",
        help="Optional deterministic audit time in YYYY.MM.DD HH:MM:SS",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    now = (
        datetime.strptime(args.now_utc, TIME_FORMAT)
        if args.now_utc
        else None
    )
    result = audit(args.common_files, now)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "LIVE_DEMO_AUDIT.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with (args.output_dir / "LIVE_DEMO_AUDIT.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(markdown(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
