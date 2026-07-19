from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
PACKAGE = (
    REPO
    / "xau-usd"
    / "xauusd-fast-research"
    / "capital-dukas-lagged-economic-test-v23"
)
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(PACKAGE / "src"))

from download_sealed_dukascopy import verify_contract  # noqa: E402
from economic_test import (  # noqa: E402
    _download_bytes,
    decode_bi5_hour,
    dukascopy_path,
    dukascopy_url,
    expected_dukascopy_hours,
    load_config,
    path_record,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Acquire one transport-only shard of sealed V23 data."
    )
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.shard_count <= 0:
        raise ValueError("shard-count must be positive")
    if not 0 <= args.shard_index < args.shard_count:
        raise ValueError("shard-index must be within shard-count")

    config = load_config(PACKAGE)
    contract = verify_contract(config)
    hours = expected_dukascopy_hours(config)[
        args.shard_index :: args.shard_count
    ]
    divisor = int(config["confirmation"]["dukascopy_price_divisor"])
    records: list[dict[str, object]] = []

    for hour in hours:
        path = dukascopy_path(config, hour)
        url = dukascopy_url(config, hour)
        compressed = _download_bytes(url)
        payload = decode_bi5_hour(compressed, hour, divisor)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.part")
        temporary.write_text(
            json.dumps(payload, separators=(",", ":"), allow_nan=False),
            encoding="utf-8",
        )
        temporary.replace(path)
        record = path_record(path)
        record.update(
            {
                "hour_utc": hour.isoformat(),
                "url": url,
                "tick_count": int(len(payload["times"])),
            }
        )
        records.append(record)

    print(
        json.dumps(
            {
                "contract_sha256": contract["contract_sha256"],
                "shard_count": args.shard_count,
                "shard_index": args.shard_index,
                "hour_count": len(records),
                "tick_count": sum(int(row["tick_count"]) for row in records),
                "files": records,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
