from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from proxy_data import (  # noqa: E402
    acquire_metadata,
    acquire_symbol,
    acquisition_hours,
    write_json,
)


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "macro_transition_proxy_replication_v2.json").read_text(
            encoding="utf-8"
        )
    )
    source = config["proxy_source"]
    storage = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    )
    external_root = storage / source["root"]
    external_root.mkdir(parents=True, exist_ok=True)
    origin = str(source["official_origin"])
    timeout = int(source["timeout_seconds"])
    metadata = []
    hourly_rows = []

    def progress(number: int, total: int, symbol: str) -> None:
        print(f"{symbol}: acquired_or_resumed={number}/{total}", flush=True)

    end = datetime.fromisoformat(source["end_exclusive_utc"].replace("Z", "+00:00"))
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    for symbol, settings in source["symbols"].items():
        source_code = str(settings["source_code"])
        metadata.append(
            acquire_metadata(external_root, origin, symbol, source_code, timeout)
        )
        start = datetime.fromisoformat(str(settings["start_utc"]).replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        hours = acquisition_hours(start, end, source["utc_hours"])
        quarantined = {
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            .astimezone(UTC)
            .isoformat()
            for value in source["quarantined_hours"].get(symbol, [])
        }
        hourly_rows.extend(
            acquire_symbol(
                external_root,
                origin,
                symbol,
                source_code,
                hours,
                timeout,
                int(source["maximum_concurrency"]),
                quarantined,
                progress,
            )
        )
    manifest = {
        "schema_version": "xauusd_macro_transition_proxy_acquisition_v2",
        "official_origin": origin,
        "paid_data_used": False,
        "quarantined_hours": source["quarantined_hours"],
        "metadata": metadata,
        "hours": sorted(hourly_rows, key=lambda row: (row["symbol"], row["hour_utc"])),
    }
    path = external_root / source["acquisition_manifest"]
    write_json(path, manifest)
    print(
        json.dumps(
            {
                "manifest": str(path),
                "hour_rows": len(hourly_rows),
                "ticks": sum(int(row["tick_count"]) for row in hourly_rows),
                "compressed_bytes": sum(
                    int(row["compressed_bytes"]) for row in hourly_rows
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
