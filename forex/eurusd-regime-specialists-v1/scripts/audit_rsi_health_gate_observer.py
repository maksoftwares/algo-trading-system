from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


EXPECTED_HEADER = [
    "recorded_at_broker",
    "recorded_at_utc",
    "run_id",
    "event",
    "detail",
    "account",
    "server",
    "symbol",
    "observer_id",
    "signal_time_utc",
    "entry",
    "stop",
    "target",
    "exit",
    "pnl_pips",
    "pnl_usd_001_lot",
    "health_buffer_count",
    "trailing_profit_factor",
    "health_gate_admitted",
    "virtual_active",
]


def _encoding(path: Path) -> str:
    prefix = path.read_bytes()[:4]
    if prefix.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"
    return "utf-8-sig"


def _time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S").replace(
        tzinfo=UTC
    )


def _factor(values: list[float]) -> float:
    gains = sum(value for value in values if value > 0.0)
    losses = -sum(value for value in values if value < 0.0)
    if losses == 0.0:
        return math.inf if gains > 0.0 else 0.0
    return gains / losses


def _json_factor(values: list[float]) -> float | str:
    value = _factor(values)
    return value if math.isfinite(value) else "INF"


def audit(
    audit_csv: Path,
    prospective_start: datetime,
    now_utc: datetime,
) -> dict[str, Any]:
    with audit_csv.open(
        "r", encoding=_encoding(audit_csv), newline=""
    ) as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        rows = list(reader)

    events = [row.get("event", "") for row in rows]
    opens = [row for row in rows if row.get("event") == "VIRTUAL_OPEN"]
    closes = [row for row in rows if row.get("event") == "VIRTUAL_CLOSE"]
    admitted_opens = [
        row
        for row in opens
        if row.get("health_gate_admitted", "").lower() == "true"
    ]
    admitted_closes = [
        row
        for row in closes
        if row.get("health_gate_admitted", "").lower() == "true"
    ]
    close_pips = [float(row["pnl_pips"]) for row in closes]
    admitted_close_pips = [
        float(row["pnl_pips"]) for row in admitted_closes
    ]
    open_times = [
        _time(row["signal_time_utc"])
        for row in opens
        if row.get("signal_time_utc")
    ]
    admitted_buffers = [
        int(row["health_buffer_count"]) for row in admitted_opens
    ]
    forbidden_execution_events = [
        event
        for event in events
        if event.startswith(("ORDER_", "DEAL_", "POSITION_"))
    ]
    identity_rows = [
        row
        for row in rows
        if row.get("event") in {"INIT_OK", "STATE_INITIALIZED", "STATE_RESTORED"}
    ]
    checks = {
        "exact_header": header == EXPECTED_HEADER,
        "rows_present": bool(rows),
        "init_ok_present": "INIT_OK" in events,
        "startup_latch_present": "STARTUP_LATCH" in events,
        "no_init_failure": "INIT_FAILED" not in events,
        "no_execution_event": not forbidden_execution_events,
        "single_run_id": {
            row.get("run_id") for row in rows
        } == {"EURUSD_RSI_HEALTH_GATE_FORWARD_V1"},
        "single_symbol": {
            row.get("symbol") for row in identity_rows
        } <= {"EURUSD"},
        "no_pre_floor_virtual_open": all(
            value >= prospective_start for value in open_times
        ),
        "admission_requires_full_30_trade_buffer": all(
            count == 30 for count in admitted_buffers
        ),
        "no_more_closes_than_opens": len(closes) <= len(opens),
    }
    passed = all(checks.values())
    if not passed:
        status = "FAIL"
    elif now_utc < prospective_start and not opens:
        status = "PASS_RUNNING_PRESTART"
    else:
        status = "PASS_PROSPECTIVE_ZERO_ORDER"
    return {
        "schema_version": "eurusd_rsi_health_gate_observer_audit_v1",
        "generated_at_utc": now_utc.isoformat(),
        "status": status,
        "demo_order_authorized": False,
        "prospective_start_utc": prospective_start.isoformat(),
        "rows": len(rows),
        "virtual_opens": len(opens),
        "virtual_closes": len(closes),
        "health_admitted_opens": len(admitted_opens),
        "health_admitted_closes": len(admitted_closes),
        "raw_virtual_profit_factor": _json_factor(close_pips),
        "admitted_virtual_profit_factor": _json_factor(admitted_close_pips),
        "forbidden_execution_events": forbidden_execution_events,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--prospective-start-utc",
        default="2026-08-01T00:00:00+00:00",
    )
    args = parser.parse_args()
    start = datetime.fromisoformat(args.prospective_start_utc).astimezone(UTC)
    result = audit(args.audit_csv, start, datetime.now(UTC))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "OBSERVER_HEALTH.json"
    output.write_text(
        json.dumps(result, indent=2, allow_nan=False, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, allow_nan=False, default=str))
    if result["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
