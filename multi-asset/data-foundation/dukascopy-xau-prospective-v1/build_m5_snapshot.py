from __future__ import annotations

import argparse
from datetime import timedelta
import json
import os
from pathlib import Path

import pandas as pd

from src.m5 import (
    add_rolling_features,
    load_hours,
    parity_against_frozen,
    write_features,
)
from src.snapshot import load_foundation, parse_utc


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "prospective_xau_v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build prospective XAU M5 features")
    parser.add_argument("snapshot")
    parser.add_argument("frozen_cache")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    foundation = load_foundation(REPO_ROOT, config)
    storage_root = Path(os.environ[config["storage_environment_variable"]]).resolve()
    snapshot_path = Path(args.snapshot).resolve()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    frozen_path = Path(args.frozen_cache).resolve()
    frozen = pd.read_parquet(frozen_path)

    start = parse_utc(snapshot["start_utc"])
    parity_day = start - timedelta(days=1)
    parity_rows = []
    for hour in range(24):
        moment = parity_day.replace(hour=hour)
        path = foundation.raw_hour_path(storage_root, config["symbol"], moment)
        parity_rows.append(
            {
                "hour_utc": foundation.iso_utc(moment),
                "path": str(path.relative_to(storage_root)).replace("\\", "/"),
                "source_file_id": f"{config['symbol']}-{moment:%Y%m%d%H}",
            }
        )
    rebuilt = load_hours(
        foundation, storage_root, config["symbol"], parity_rows
    )
    parity = parity_against_frozen(rebuilt, frozen)
    prospective = load_hours(
        foundation, storage_root, config["symbol"], snapshot["rows"]
    )
    features = add_rolling_features(prospective, frozen)
    output, manifest = write_features(
        foundation,
        storage_root,
        snapshot_path,
        frozen_path,
        features,
        parity,
    )
    print(
        json.dumps(
            {
                "status": "DUKASCOPY_XAU_PROSPECTIVE_M5_FEATURES_READY",
                "rows": len(features),
                "feature_path": str(output),
                "manifest_path": str(manifest),
                "historical_parity": parity,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
