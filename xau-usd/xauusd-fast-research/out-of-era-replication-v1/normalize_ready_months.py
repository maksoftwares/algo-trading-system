from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
FOUNDATION = ROOT.parents[2] / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1"
sys.path.insert(0, str(FOUNDATION / "src"))

from dukascopy_tick_foundation.foundation import normalize_month  # noqa: E402


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "out_of_era_replication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    status_path = storage_root / source["extension_status"]
    status = json.loads(status_path.read_text(encoding="utf-8"))
    ready = list(status.get("months_complete_this_run", []))
    if args.limit > 0:
        ready = ready[: args.limit]
    replay_root = storage_root / source["replay_root"]
    manifest_root = replay_root / "manifests"
    completed: list[str] = []
    for month in ready:
        manifest_path = manifest_root / f"{month}.json"
        if manifest_path.is_file():
            completed.append(month)
            print(f"normalized_month={month} status=ALREADY_COMPLETE", flush=True)
            continue
        year, number = (int(value) for value in month.split("-"))
        print(f"normalized_month={month} status=RUNNING", flush=True)
        result = normalize_month(storage_root, replay_root, source["symbol"], year, number)
        if result["integrity"]["negative_spread_count"] != 0:
            raise ValueError(f"Negative spread found in {month}")
        _write_json(
            manifest_path,
            {
                "schema_version": "xauusd_out_of_era_normalized_month_v1",
                "normalized_utc": datetime.now(UTC).isoformat(),
                "month": month,
                "result": result,
                "strategy_scoring_performed": False,
                "outcomes_opened": False,
            },
        )
        completed.append(month)
        print(f"normalized_month={month} status=COMPLETE", flush=True)
    _write_json(
        replay_root / "status.json",
        {
            "schema_version": "xauusd_out_of_era_normalization_status_v1",
            "updated_utc": datetime.now(UTC).isoformat(),
            "ready_months_seen": ready,
            "normalized_months": completed,
            "expected_months": int(source["expected_months"]),
            "strategy_scoring_performed": False,
            "outcomes_opened": False,
            "paid_data_request_made": False,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

