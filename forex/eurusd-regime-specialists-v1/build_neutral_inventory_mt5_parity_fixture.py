from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import pandas as pd

import capture_prospective_neutral_inventory_unwind_0005 as decision
import capture_prospective_neutral_inventory_unwind_0005_path as execution

FIELDS = [
    "case_id",
    "side",
    "entry_epoch",
    "tick_epoch",
    "bid",
    "ask",
    "expected_status",
    "expected_exit_reason",
    "expected_entry_tick_epoch",
    "expected_exit_tick_epoch",
    "expected_entry_fill",
    "expected_exit_fill",
    "expected_r",
]


def _ticks(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["timestamp_utc", "bid", "ask"]).assign(
        timestamp_utc=lambda frame: pd.to_datetime(
            frame["timestamp_utc"], utc=True
        )
    )


def fixture_cases() -> list[dict[str, Any]]:
    entry = "2026-07-30T00:05:00Z"
    return [
        {
            "case_id": "long_target",
            "side": "LONG",
            "entry": entry,
            "ticks": _ticks(
                [
                    (entry, 1.10000, 1.10008),
                    ("2026-07-30T00:05:01Z", 1.10050, 1.10058),
                    ("2026-07-30T00:05:02Z", 1.10105, 1.10113),
                ]
            ),
        },
        {
            "case_id": "short_stop",
            "side": "SHORT",
            "entry": entry,
            "ticks": _ticks(
                [
                    (entry, 1.10000, 1.10008),
                    ("2026-07-30T00:05:01Z", 1.10030, 1.10038),
                    ("2026-07-30T00:05:02Z", 1.10062, 1.10070),
                ]
            ),
        },
        {
            "case_id": "long_time",
            "side": "LONG",
            "entry": entry,
            "ticks": _ticks(
                [
                    (entry, 1.10000, 1.10008),
                    ("2026-07-30T03:00:00Z", 1.09990, 1.09998),
                    ("2026-07-30T06:05:00Z", 1.10020, 1.10028),
                ]
            ),
        },
        {
            "case_id": "short_target",
            "side": "SHORT",
            "entry": entry,
            "ticks": _ticks(
                [
                    (entry, 1.10000, 1.10008),
                    ("2026-07-30T00:05:01Z", 1.09940, 1.09948),
                    ("2026-07-30T00:05:02Z", 1.09892, 1.09900),
                ]
            ),
        },
        {
            "case_id": "spread_reject",
            "side": "LONG",
            "entry": entry,
            "ticks": _ticks(
                [
                    (entry, 1.10000, 1.10020),
                    ("2026-07-30T00:05:01Z", 1.10120, 1.10140),
                ]
            ),
        },
        {
            "case_id": "missing_entry",
            "side": "LONG",
            "entry": entry,
            "ticks": _ticks(
                [
                    ("2026-07-30T00:04:58Z", 1.10000, 1.10008),
                    ("2026-07-30T00:04:59Z", 1.10001, 1.10009),
                ]
            ),
        },
        {
            "case_id": "pending_time_tick",
            "side": "SHORT",
            "entry": entry,
            "ticks": _ticks(
                [
                    (entry, 1.10000, 1.10008),
                    ("2026-07-30T06:04:59Z", 1.10000, 1.10008),
                ]
            ),
        },
    ]


def _epoch(value: Any | None) -> str:
    return (
        ""
        if value is None
        else str(int(pd.Timestamp(value).timestamp()))
    )


def _number(value: Any | None) -> str:
    return "" if value is None else f"{float(value):.12f}"


def build_fixture_rows() -> list[dict[str, str]]:
    cfg = decision.load_config()
    rows: list[dict[str, str]] = []
    for case in fixture_cases():
        result = execution.execute_ticks(
            {
                "side": case["side"],
                "entry_time_utc": case["entry"],
            },
            case["ticks"],
            cfg,
        )
        for tick in case["ticks"].itertuples(index=False):
            rows.append(
                {
                    "case_id": str(case["case_id"]),
                    "side": str(case["side"]),
                    "entry_epoch": _epoch(case["entry"]),
                    "tick_epoch": _epoch(tick.timestamp_utc),
                    "bid": _number(tick.bid),
                    "ask": _number(tick.ask),
                    "expected_status": str(result["status"]),
                    "expected_exit_reason": str(
                        result.get("exit_reason", "")
                    ),
                    "expected_entry_tick_epoch": _epoch(
                        result.get("entry_tick_time_utc")
                    ),
                    "expected_exit_tick_epoch": _epoch(
                        result.get("exit_time_utc")
                    ),
                    "expected_entry_fill": _number(
                        result.get("entry_fill")
                    ),
                    "expected_exit_fill": _number(
                        result.get("exit_fill")
                    ),
                    "expected_r": _number(result.get("r")),
                }
            )
    return rows


def write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(build_fixture_rows())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_fixture(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
