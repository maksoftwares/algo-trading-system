from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path

from src.snapshot import hour_range, load_foundation, parse_utc, sha256_file


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "prospective_xau_v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a prospective XAU snapshot")
    parser.add_argument("manifest")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    foundation = load_foundation(REPO_ROOT, config)
    env_name = config["storage_environment_variable"]
    storage_raw = os.environ.get(env_name, "").strip()
    if not storage_raw:
        raise ValueError(f"{env_name} is required")
    storage_root = Path(storage_raw).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest_path.relative_to(storage_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["schema_version"] != config["schema_version"]:
        raise ValueError("snapshot schema mismatch")
    if manifest["symbol"] != config["symbol"]:
        raise ValueError("snapshot symbol mismatch")
    start = parse_utc(manifest["start_utc"])
    end = parse_utc(manifest["end_exclusive_utc"])
    expected_hours = hour_range(start, end)
    rows = manifest["rows"]
    if len(rows) != len(expected_hours):
        raise ValueError("snapshot hourly cardinality mismatch")

    ticks = 0
    byte_count = 0
    for expected_hour, row in zip(expected_hours, rows, strict=True):
        observed_hour = parse_utc(row["hour_utc"])
        if observed_hour != expected_hour:
            raise ValueError(f"non-contiguous snapshot hour: {observed_hour}")
        if row["url"] != foundation.official_tick_url(config["symbol"], expected_hour):
            raise ValueError(f"official URL mismatch: {observed_hour}")
        path = (storage_root / row["path"]).resolve()
        path.relative_to(
            storage_root
            / "raw"
            / config["symbol"]
            / f"year={expected_hour.year:04d}"
            / f"month={expected_hour.month:02d}"
        )
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"raw checksum mismatch: {observed_hour}")
        payload_ticks = foundation.validate_hour_payload(
            path.read_bytes(),
            config["symbol"],
            expected_hour.astimezone(UTC),
            row["source_file_id"],
        )
        if payload_ticks != int(row["tick_count"]):
            raise ValueError(f"tick count mismatch: {observed_hour}")
        ticks += payload_ticks
        byte_count += path.stat().st_size
    if ticks != int(manifest["tick_count"]) or byte_count != int(manifest["bytes"]):
        raise ValueError("snapshot aggregate totals mismatch")
    print(
        json.dumps(
            {
                "status": "DUKASCOPY_XAU_PROSPECTIVE_SNAPSHOT_VERIFICATION_PASS",
                "manifest_sha256": sha256_file(manifest_path),
                "completed_hours": len(rows),
                "tick_count": ticks,
                "bytes": byte_count,
                "start_utc": datetime.fromtimestamp(
                    expected_hours[0].timestamp(), UTC
                ).isoformat(),
                "end_exclusive_utc": end.isoformat(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
