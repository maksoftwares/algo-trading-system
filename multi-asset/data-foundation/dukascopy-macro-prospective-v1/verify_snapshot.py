from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path

from src.snapshot import hour_range, load_foundation, parse_utc, sha256_file


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify macro prospective snapshot")
    parser.add_argument("snapshot")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "prospective_macro_v1.json").read_text(encoding="utf-8")
    )
    foundation = load_foundation(REPO_ROOT, config)
    storage_root = Path(os.environ[config["storage_environment_variable"]]).resolve()
    manifest_path = Path(args.snapshot).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    start = parse_utc(manifest["start_utc"])
    end = parse_utc(manifest["end_exclusive_utc"])
    expected_hours = {foundation.iso_utc(hour) for hour in hour_range(start, end)}
    symbols = list(config["symbols"])
    rows = manifest["rows"]
    if len(rows) != len(expected_hours) * len(symbols):
        raise ValueError("macro snapshot row count mismatch")
    counts = Counter(row["symbol"] for row in rows)
    if counts != Counter({symbol: len(expected_hours) for symbol in symbols}):
        raise ValueError("macro snapshot symbol coverage mismatch")
    tick_count = 0
    byte_count = 0
    for symbol in symbols:
        observed = {row["hour_utc"] for row in rows if row["symbol"] == symbol}
        if observed != expected_hours:
            raise ValueError(f"macro hourly coverage mismatch: {symbol}")
    for row in rows:
        path = (storage_root / row["path"]).resolve()
        path.relative_to(storage_root)
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"macro raw hash mismatch: {path}")
        ticks = foundation.decode_payload(
            path.read_bytes(), row["symbol"], row["source_file_id"]
        )
        if len(ticks) != int(row["tick_count"]):
            raise ValueError(f"macro tick count mismatch: {path}")
        tick_count += len(ticks)
        byte_count += path.stat().st_size
    if tick_count != int(manifest["tick_count"]):
        raise ValueError("macro manifest tick total mismatch")
    if byte_count != int(manifest["bytes"]):
        raise ValueError("macro manifest byte total mismatch")
    print(
        json.dumps(
            {
                "status": "DUKASCOPY_MACRO_PROSPECTIVE_SNAPSHOT_VERIFICATION_PASS",
                "manifest_sha256": sha256_file(manifest_path),
                "symbol_hours": len(rows),
                "ticks": tick_count,
                "bytes": byte_count,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
