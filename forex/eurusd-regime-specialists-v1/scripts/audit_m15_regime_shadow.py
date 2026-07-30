from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TIME_FORMAT = "%Y.%m.%d %H:%M:%S"
FORWARD_FLOOR = datetime(2026, 8, 1, tzinfo=UTC)
FIELDS = (
    "recorded_at_broker",
    "recorded_at_utc",
    "run_id",
    "event",
    "detail",
    "account",
    "server",
    "symbol",
    "magic",
    "regime",
    "side",
    "lots",
    "entry",
    "stop",
    "target",
    "shadow",
    "orders_enabled",
    "emergency_stop",
)


def load_rows(path: Path) -> tuple[list[dict[str, str]], bool]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        raw = list(csv.reader(handle))
    if not raw:
        raise ValueError("shadow audit is empty")
    header_present = tuple(raw[0]) == FIELDS
    data = raw[1:] if header_present else raw
    if any(len(row) != len(FIELDS) for row in data):
        raise ValueError("shadow audit contains malformed rows")
    return [dict(zip(FIELDS, row, strict=True)) for row in data], header_present


def audit(path: Path, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    rows, header_present = load_rows(path)
    events = Counter(row["event"] for row in rows)
    signal_rows = [row for row in rows if row["event"] == "SIGNAL"]
    blocked_rows = [row for row in rows if row["event"] == "ORDER_BLOCKED"]
    parsed_times: list[datetime] = []
    try:
        parsed_times = [
            datetime.strptime(row["recorded_at_utc"], TIME_FORMAT).replace(
                tzinfo=UTC
            )
            for row in rows
        ]
    except ValueError:
        parsed_times = []
    pre_floor_signals = [
        row
        for row, timestamp in zip(rows, parsed_times)
        if row["event"] == "SIGNAL" and timestamp < FORWARD_FLOOR
    ]
    checks = {
        "rows_present": bool(rows),
        "timestamps_parse": len(parsed_times) == len(rows),
        "run_id_exact": all(
            row["run_id"] == "EURUSD_M15_REGIME_FORWARD_V1" for row in rows
        ),
        "account_exact": all(row["account"] == "1033669" for row in rows),
        "server_exact": all(
            row["server"] == "Capital.ComMena-Demo" for row in rows
        ),
        "symbol_exact": all(row["symbol"] == "EURUSD" for row in rows),
        "shadow_true": all(row["shadow"] == "true" for row in rows),
        "orders_disabled": all(
            row["orders_enabled"] == "false" for row in rows
        ),
        "emergency_stop_true": all(
            row["emergency_stop"] == "true" for row in rows
        ),
        "init_ok": events["INIT_OK"] >= 1,
        "startup_latch": events["STARTUP_LATCH"] >= 1,
        "no_init_failure": events["INIT_FAILED"] == 0,
        "no_order_send": events["ORDER_SEND_OK"] == 0
        and events["ORDER_SEND_FAILED"] == 0,
        "no_management_action": events["TIME_EXIT_OK"] == 0,
        "no_pre_floor_signal": not pre_floor_signals,
        "all_signals_blocked_in_shadow": len(signal_rows) == len(blocked_rows)
        and all(row["detail"] == "shadow_or_orders_disabled" for row in blocked_rows),
    }
    status = (
        "PASS_RUNNING_PRESTART"
        if now < FORWARD_FLOOR and all(checks.values())
        else (
            "PASS_RUNNING_FORWARD_SHADOW"
            if now >= FORWARD_FLOOR and all(checks.values())
            else "FAIL"
        )
    )
    return {
        "artifact": "EURUSD_M15_REGIME_PORTFOLIO_SHADOW_V1",
        "audited_at_utc": now.strftime(TIME_FORMAT),
        "status": status,
        "forward_floor_utc": FORWARD_FLOOR.strftime(TIME_FORMAT),
        "before_forward_floor": now < FORWARD_FLOOR,
        "rows": len(rows),
        "header_present": header_present,
        "latest_recorded_at_utc": (
            max(parsed_times).strftime(TIME_FORMAT) if parsed_times else None
        ),
        "signals": len(signal_rows),
        "blocked_signals": len(blocked_rows),
        "event_counts": dict(sorted(events.items())),
        "checks": checks,
    }


def markdown(result: dict[str, Any]) -> str:
    checks = "\n".join(
        f"- {name}: `{value}`" for name, value in result["checks"].items()
    )
    return f"""# EURUSD M15 regime portfolio live shadow audit

Status: **{result["status"]}**

- Audited at UTC: `{result["audited_at_utc"]}`
- Forward floor UTC: `{result["forward_floor_utc"]}`
- Rows: `{result["rows"]}`
- Signals: `{result["signals"]}`
- Signals blocked in shadow: `{result["blocked_signals"]}`
- Latest audit event UTC: `{result["latest_recorded_at_utc"]}`

## Checks

{checks}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.audit_csv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "LIVE_SHADOW_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (args.output_dir / "LIVE_SHADOW_AUDIT.md").write_text(
        markdown(result), encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
