from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


HEALTH_FILENAME = "SHARED_1033030_US500_V41_HEALTH.csv"
AUDIT_FILENAME = "SHARED_1033030_US500_V41_AUDIT.csv"
EXPECTED_CONTRACT = "SHARED_1033030_US500_V41_CAUSAL_CORE_20260804"
EXPECTED_CONFIG = "48e8b4f9545b8d37ca131abc3126eacf42609ae1fd7318e2a605c7fbe520b16e"
EXPECTED_ACCOUNT = "1033030"
EXPECTED_SERVER = "Capital.ComMena-Demo"
EXPECTED_SYMBOL = "US500"
TIME_FORMAT = "%Y.%m.%d %H:%M:%S"
NEW_YORK = ZoneInfo("America/New_York")


def default_common_path(filename: str) -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not defined; pass the Common Files path explicitly")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / filename


def default_health_path() -> Path:
    return default_common_path(HEALTH_FILENAME)


def default_audit_path() -> Path:
    return default_common_path(AUDIT_FILENAME)


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


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, TIME_FORMAT).replace(tzinfo=timezone.utc)


def _age_seconds(
    row: dict[str, str], *, now_utc: datetime, label: str, errors: list[str]
) -> float | None:
    try:
        age = (now_utc - _parse_utc(row["utc_time"])).total_seconds()
    except (KeyError, ValueError) as exc:
        errors.append(f"invalid {label} utc_time: {exc}")
        return None
    if age < -5.0:
        errors.append(f"{label} is {abs(age):.1f}s in the future")
    return age


def decision_session_active(now_utc: datetime) -> bool:
    ny = now_utc.astimezone(NEW_YORK)
    minute = ny.hour * 60 + ny.minute
    return ny.weekday() < 5 and 9 * 60 + 25 <= minute <= 14 * 60 + 5


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
    audit_rows: list[dict[str, str]],
    *,
    now_utc: datetime | None = None,
    max_heartbeat_age_seconds: float = 130.0,
    max_order_send_ms: float = 2000.0,
    max_tick_age_ms: float = 30_000.0,
    max_server_lag_seconds: float = 30.0,
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
    heartbeat_age = _age_seconds(
        heartbeat, now_utc=now, label="health heartbeat", errors=errors
    )
    if heartbeat_age is not None and heartbeat_age > max_heartbeat_age_seconds:
        errors.append(f"health heartbeat is stale: {heartbeat_age:.1f}s old")

    for key in (
        "connected",
        "terminal_trade_allowed",
        "mql_trade_allowed",
        "account_trade_allowed",
    ):
        if not _as_enabled(heartbeat, key):
            errors.append(f"runtime permission/connection is disabled: {key}")

    session_freshness_required = decision_session_active(now)
    try:
        tick_age_ms = _as_float(heartbeat, "tick_age_ms")
        if session_freshness_required and tick_age_ms > max_tick_age_ms:
            errors.append(
                f"US500 tick is stale during the decision session: {tick_age_ms:.1f}ms old"
            )
    except ValueError as exc:
        tick_age_ms = None
        errors.append(f"invalid tick_age_ms: {exc}")
    try:
        server_lag_seconds = _as_float(heartbeat, "server_lag_seconds")
        if abs(server_lag_seconds) > max_server_lag_seconds:
            errors.append(
                f"server clock lag exceeds limit: {server_lag_seconds:.1f}s "
                f"(limit {max_server_lag_seconds:.1f}s)"
            )
    except ValueError as exc:
        server_lag_seconds = None
        errors.append(f"invalid server_lag_seconds: {exc}")

    ea_heartbeats = [row for row in audit_rows if row.get("event") == "HEARTBEAT"]
    init_rows = [row for row in audit_rows if row.get("event") == "INIT"]
    ea_heartbeat: dict[str, str] | None = None
    latest_init: dict[str, str] | None = None
    ea_heartbeat_age: float | None = None
    if not ea_heartbeats:
        errors.append("no EA HEARTBEAT audit record exists")
    else:
        ea_heartbeat = max(ea_heartbeats, key=lambda row: row.get("utc_time", ""))
        errors.extend(_identity_errors(ea_heartbeat))
        ea_heartbeat_age = _age_seconds(
            ea_heartbeat, now_utc=now, label="EA audit heartbeat", errors=errors
        )
        if (
            ea_heartbeat_age is not None
            and ea_heartbeat_age > max_heartbeat_age_seconds
        ):
            errors.append(f"EA audit heartbeat is stale: {ea_heartbeat_age:.1f}s old")
        if ea_heartbeat.get("detail") != "OK":
            errors.append(
                f"EA execution state is not OK: {ea_heartbeat.get('detail')!r}"
            )
        for key in ("orders_enabled", "broker_allowed"):
            if not _as_enabled(ea_heartbeat, key):
                errors.append(f"EA execution gate is disabled: {key}")
    if not init_rows:
        errors.append("no EA INIT audit record exists")
    else:
        latest_init = max(init_rows, key=lambda row: row.get("utc_time", ""))
        errors.extend(_identity_errors(latest_init))
        if latest_init.get("detail") != "ORDER_MODE_AUTHORIZED":
            errors.append(
                f"latest EA initialization is not order-authorized: {latest_init.get('detail')!r}"
            )

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
            "tick_age_ms": tick_age_ms,
            "server_lag_seconds": server_lag_seconds,
            "event_id": heartbeat.get("event_id"),
        },
        "ea_audit": {
            "utc_time": ea_heartbeat.get("utc_time") if ea_heartbeat else None,
            "age_seconds": ea_heartbeat_age,
            "detail": ea_heartbeat.get("detail") if ea_heartbeat else None,
            "orders_enabled": ea_heartbeat.get("orders_enabled") if ea_heartbeat else None,
            "broker_allowed": ea_heartbeat.get("broker_allowed") if ea_heartbeat else None,
            "symbol_exposure": ea_heartbeat.get("symbol_exposure") if ea_heartbeat else None,
            "own_positions": ea_heartbeat.get("own_positions") if ea_heartbeat else None,
            "event_id": ea_heartbeat.get("event_id") if ea_heartbeat else None,
            "latest_init_detail": latest_init.get("detail") if latest_init else None,
        },
        "session_freshness_required": session_freshness_required,
        "latest_order_execution": latest_execution,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only health verification for the attached US500 V41 demo EA"
    )
    parser.add_argument("--health-file", type=Path)
    parser.add_argument("--audit-file", type=Path)
    parser.add_argument("--max-heartbeat-age-seconds", type=float, default=130.0)
    parser.add_argument("--max-order-send-ms", type=float, default=2000.0)
    parser.add_argument("--max-tick-age-ms", type=float, default=30_000.0)
    parser.add_argument("--max-server-lag-seconds", type=float, default=30.0)
    args = parser.parse_args()
    health_path = args.health_file or default_health_path()
    audit_path = args.audit_file or default_audit_path()
    missing = [str(path) for path in (health_path, audit_path) if not path.is_file()]
    if missing:
        report = {
            "status": "FAILED",
            "health_file": str(health_path),
            "audit_file": str(audit_path),
            "errors": [f"required runtime file is missing: {path}" for path in missing],
            "warnings": [],
        }
    else:
        report = evaluate(
            read_rows(health_path),
            read_rows(audit_path),
            max_heartbeat_age_seconds=args.max_heartbeat_age_seconds,
            max_order_send_ms=args.max_order_send_ms,
            max_tick_age_ms=args.max_tick_age_ms,
            max_server_lag_seconds=args.max_server_lag_seconds,
        )
        report["health_file"] = str(health_path)
        report["audit_file"] = str(audit_path)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "HEALTHY" else (1 if report["status"] == "DEGRADED" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
