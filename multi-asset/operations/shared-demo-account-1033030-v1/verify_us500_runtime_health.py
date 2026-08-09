from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


HEALTH_FILENAME = "SHARED_1033030_US500_V41_HEALTH.csv"
EXPECTED_CONTRACT = "SHARED_1033030_US500_V41_CAUSAL_CORE_20260804"
EXPECTED_CONFIG = "48e8b4f9545b8d37ca131abc3126eacf42609ae1fd7318e2a605c7fbe520b16e"
EXPECTED_ACCOUNT = "1033030"
EXPECTED_SERVER = "Capital.ComMena-Demo"
EXPECTED_SYMBOL = "US500"
TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


def default_health_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not defined; pass --health-file explicitly")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / HEALTH_FILENAME


def _read_text(path: Path) -> str:
    payload = path.read_bytes()
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        return payload.decode("utf-16")
    if b"\x00" in payload[:256]:
        return payload.decode("utf-16-le")
    return payload.decode("utf-8-sig")


def read_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(_read_text(path).splitlines()))


def _as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, ""))


def _as_enabled(row: dict[str, str], key: str) -> bool:
    return row.get(key) == "1"


def _identity_errors(row: dict[str, str]) -> Iterable[str]:
    expected = {
        "contract_id": EXPECTED_CONTRACT,
        "config_sha256": EXPECTED_CONFIG,
        "account": EXPECTED_ACCOUNT,
        "server": EXPECTED_SERVER,
        "symbol": EXPECTED_SYMBOL,
    }
    for key, value in expected.items():
        if row.get(key) != value:
            yield f"runtime identity mismatch for {key}: {row.get(key)!r}"


def evaluate(
    rows: list[dict[str, str]],
    *,
    now_utc: datetime | None = None,
    max_heartbeat_age_seconds: float = 130.0,
    max_order_send_ms: float = 2000.0,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    heartbeats = [row for row in rows if row.get("event") == "HEARTBEAT_HEALTH"]
    if not heartbeats:
        return {
            "status": "FAILED",
            "errors": ["no HEARTBEAT_HEALTH record exists"],
            "warnings": [],
            "heartbeat": None,
            "latest_order_execution": None,
        }

    heartbeat = max(heartbeats, key=lambda row: row.get("utc_time", ""))
    errors.extend(_identity_errors(heartbeat))
    try:
        heartbeat_time = datetime.strptime(heartbeat["utc_time"], TIME_FORMAT).replace(
            tzinfo=timezone.utc
        )
        heartbeat_age = (now - heartbeat_time).total_seconds()
        if heartbeat_age < -5.0:
            errors.append(f"health heartbeat is {abs(heartbeat_age):.1f}s in the future")
        elif heartbeat_age > max_heartbeat_age_seconds:
            errors.append(f"health heartbeat is stale: {heartbeat_age:.1f}s old")
    except (KeyError, ValueError) as exc:
        heartbeat_age = None
        errors.append(f"invalid heartbeat utc_time: {exc}")

    for key in (
        "connected",
        "terminal_trade_allowed",
        "mql_trade_allowed",
        "account_trade_allowed",
    ):
        if not _as_enabled(heartbeat, key):
            errors.append(f"runtime permission/connection is disabled: {key}")

    executions = [
        row
        for row in rows
        if row.get("event") in {"ORDER_EXECUTION", "CLOSE_EXECUTION"}
    ]
    latest_execution = max(executions, key=lambda row: row.get("utc_time", "")) if executions else None
    if latest_execution is not None:
        try:
            send_ms = _as_float(latest_execution, "order_send_ms")
            if send_ms > max_order_send_ms:
                warnings.append(
                    f"latest OrderSend latency is high: {send_ms:.1f}ms "
                    f"(threshold {max_order_send_ms:.1f}ms)"
                )
        except ValueError as exc:
            warnings.append(f"invalid latest order_send_ms: {exc}")

    status = "FAILED" if errors else ("DEGRADED" if warnings else "HEALTHY")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "heartbeat": {
            "utc_time": heartbeat.get("utc_time"),
            "age_seconds": heartbeat_age,
            "connected": heartbeat.get("connected"),
            "terminal_trade_allowed": heartbeat.get("terminal_trade_allowed"),
            "mql_trade_allowed": heartbeat.get("mql_trade_allowed"),
            "account_trade_allowed": heartbeat.get("account_trade_allowed"),
            "ping_ms": heartbeat.get("ping_ms"),
            "tick_age_ms": heartbeat.get("tick_age_ms"),
            "server_lag_seconds": heartbeat.get("server_lag_seconds"),
            "event_id": heartbeat.get("event_id"),
        },
        "latest_order_execution": latest_execution,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only health verification for the attached US500 V41 demo EA"
    )
    parser.add_argument("--health-file", type=Path)
    parser.add_argument("--max-heartbeat-age-seconds", type=float, default=130.0)
    parser.add_argument("--max-order-send-ms", type=float, default=2000.0)
    args = parser.parse_args()
    path = args.health_file or default_health_path()
    if not path.is_file():
        report = {
            "status": "FAILED",
            "health_file": str(path),
            "errors": ["health file is missing"],
            "warnings": [],
        }
    else:
        report = evaluate(
            read_rows(path),
            max_heartbeat_age_seconds=args.max_heartbeat_age_seconds,
            max_order_send_ms=args.max_order_send_ms,
        )
        report["health_file"] = str(path)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "HEALTHY" else (1 if report["status"] == "DEGRADED" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
