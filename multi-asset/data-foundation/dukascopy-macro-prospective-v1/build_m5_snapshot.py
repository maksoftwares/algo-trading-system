from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path

import pandas as pd

from src.m5 import combine_symbols, load_symbol_hours, parity_against_frozen
from src.snapshot import load_foundation, parse_utc, sha256_file


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def rows_for_day(
    foundation, storage_root: Path, symbol: str, day: datetime
) -> list[dict]:
    rows = []
    for hour in range(24):
        moment = day.replace(hour=hour, tzinfo=UTC)
        path = foundation.raw_hour_path(storage_root, symbol, moment)
        rows.append(
            {
                "hour_utc": foundation.iso_utc(moment),
                "path": str(path.relative_to(storage_root)).replace("\\", "/"),
                "source_file_id": f"{symbol}-{moment:%Y%m%d%H}",
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build prospective macro M5 cache")
    parser.add_argument("snapshot")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "prospective_macro_v1.json").read_text(encoding="utf-8")
    )
    foundation = load_foundation(REPO_ROOT, config)
    storage_root = Path(os.environ[config["storage_environment_variable"]]).resolve()
    snapshot_path = Path(args.snapshot).resolve()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    context = config["historical_context"]
    frozen_path = storage_root / context["feature_cache"]
    frozen_manifest = storage_root / context["manifest"]
    if sha256_file(frozen_path) != context["feature_sha256"]:
        raise ValueError("frozen macro cache hash mismatch")
    if sha256_file(frozen_manifest) != context["manifest_sha256"]:
        raise ValueError("frozen macro manifest hash mismatch")
    frozen = pd.read_parquet(frozen_path)
    parity_day = datetime.fromisoformat(context["parity_date_utc"]).replace(tzinfo=UTC)
    parity_frames = {
        symbol: load_symbol_hours(
            foundation,
            storage_root,
            symbol,
            rows_for_day(foundation, storage_root, symbol, parity_day),
        )
        for symbol in config["symbols"]
    }
    parity = parity_against_frozen(combine_symbols(parity_frames), frozen)
    prospective_frames = {
        symbol: load_symbol_hours(
            foundation,
            storage_root,
            symbol,
            [row for row in snapshot["rows"] if row["symbol"] == symbol],
        )
        for symbol in config["symbols"]
    }
    features = combine_symbols(prospective_frames)
    start = parse_utc(snapshot["start_utc"])
    end = parse_utc(snapshot["end_exclusive_utc"])
    directory = storage_root / config["output"]["feature_directory"]
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"MACRO_{start:%Y%m%d%H}_{end:%Y%m%d%H}_M5_FEATURES_V1"
    output = directory / f"{stem}.parquet"
    features.to_parquet(output, index=False, compression="zstd")
    manifest_path = directory / f"{stem}.manifest.json"
    foundation.write_json(
        manifest_path,
        {
            "schema_version": "dukascopy_macro_prospective_m5_features_v1",
            "snapshot_manifest": str(snapshot_path),
            "snapshot_manifest_sha256": sha256_file(snapshot_path),
            "frozen_context": str(frozen_path),
            "frozen_context_sha256": sha256_file(frozen_path),
            "historical_parity": parity,
            "rows": len(features),
            "columns": features.columns.tolist(),
            "start_timestamp_ms": int(features["timestamp_ms"].min()),
            "end_timestamp_ms": int(features["timestamp_ms"].max()),
            "feature_path": str(output),
            "feature_sha256": sha256_file(output),
            "authorization": config["authorization"],
        },
    )
    print(
        json.dumps(
            {
                "status": "DUKASCOPY_MACRO_PROSPECTIVE_M5_FEATURES_READY",
                "rows": len(features),
                "feature_path": str(output),
                "feature_sha256": sha256_file(output),
                "manifest_path": str(manifest_path),
                "manifest_sha256": sha256_file(manifest_path),
                "historical_parity": parity,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
