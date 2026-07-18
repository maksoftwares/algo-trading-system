from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
FOUNDATION_ROOT = ROOT.parent / "dukascopy-ticks-v1"
sys.path.insert(0, str(FOUNDATION_ROOT / "src"))

from dukascopy_tick_foundation.foundation import (  # noqa: E402
    CorruptRawFileError,
    acquire_month,
    freeze_raw_month,
    validate_month_acquisition_manifest,
    write_month_acquisition_manifest,
)


def month_keys(first_month: str, end_exclusive_month: str) -> list[str]:
    start = pd.Period(first_month, freq="M")
    end = pd.Period(end_exclusive_month, freq="M")
    if start >= end:
        raise ValueError("The extension month range is empty")
    return [str(value) for value in pd.period_range(start, end - 1, freq="M")]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _month_complete(storage_root: Path, symbol: str, month: str) -> bool:
    year, month_number = (int(value) for value in month.split("-"))
    try:
        validate_month_acquisition_manifest(
            storage_root, symbol, year, month_number
        )
        return True
    except (CorruptRawFileError, FileNotFoundError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "xau_extension_v2.json").read_text(encoding="utf-8")
    )
    if not 1 <= args.concurrency <= int(config["maximum_concurrency"]):
        raise ValueError("Concurrency is outside the frozen boundary")
    storage_root = Path(
        os.environ.get(
            config["storage_environment_variable"], config["default_storage_root"]
        )
    ).resolve()
    if not storage_root.is_dir():
        raise FileNotFoundError(storage_root)
    months = month_keys(config["first_month"], config["end_exclusive_month"])
    status_path = storage_root / "extension-v2" / "status.json"
    completed: list[str] = []
    failed: list[str] = []
    for index, month in enumerate(months, start=1):
        symbol = str(config["symbol"])
        if _month_complete(storage_root, symbol, month):
            completed.append(month)
            print(f"extension_month={month} status=ALREADY_COMPLETE", flush=True)
            continue
        year, month_number = (int(value) for value in month.split("-"))
        print(
            f"extension_month={month} status=ACQUIRING position={index}/{len(months)}",
            flush=True,
        )
        rows = acquire_month(
            storage_root,
            symbol,
            year,
            month_number,
            concurrency=args.concurrency,
        )
        if all(
            row["status"] in {"DOWNLOADED_VALID", "RESUMED_VALID"}
            for row in rows
        ):
            write_month_acquisition_manifest(
                storage_root, symbol, year, month_number, rows
            )
            validate_month_acquisition_manifest(
                storage_root, symbol, year, month_number
            )
            freeze_raw_month(storage_root, symbol, year, month_number)
            completed.append(month)
            print(f"extension_month={month} status=COMPLETE", flush=True)
        else:
            failed.append(month)
            print(f"extension_month={month} status=INCOMPLETE", flush=True)
        _write_json(
            status_path,
            {
                "schema_version": config["schema_version"],
                "updated_utc": datetime.now(UTC).isoformat(),
                "months_total": len(months),
                "months_complete_this_run": completed,
                "months_incomplete_this_run": failed,
                "paid_data_request_made": False,
                "strategy_scoring_performed": False,
                "broker_action_performed": False,
            },
        )
    final = {
        "schema_version": config["schema_version"],
        "updated_utc": datetime.now(UTC).isoformat(),
        "months_total": len(months),
        "months_complete_this_run": completed,
        "months_incomplete_this_run": failed,
        "decision": "COMPLETE" if not failed else "PARTIAL_RETRY_REQUIRED",
        "paid_data_request_made": False,
        "strategy_scoring_performed": False,
        "broker_action_performed": False,
    }
    _write_json(status_path, final)
    print(json.dumps(final, indent=2, sort_keys=True), flush=True)
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
