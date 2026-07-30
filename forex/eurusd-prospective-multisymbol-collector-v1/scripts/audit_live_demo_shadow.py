from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
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
    checks["no_feature_rows_before_floor"] = (
        not before_floor or len(feature_rows) == 0
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

    status = (
        "PASS_RUNNING_PRESTART"
        if before_floor and all(checks.values())
        else (
            "PASS_RUNNING_FORWARD"
            if not before_floor and all(checks.values())
            else "FAIL"
        )
    )
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
