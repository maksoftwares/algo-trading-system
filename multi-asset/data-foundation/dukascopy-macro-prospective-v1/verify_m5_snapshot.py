from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path

import pandas as pd

from src.m5 import combine_symbols, load_symbol_hours, parity_against_frozen
from src.snapshot import load_foundation, sha256_file


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def parity_rows(
    foundation, storage_root: Path, symbol: str, day: datetime
) -> list[dict]:
    return [
        {
            "hour_utc": foundation.iso_utc(day.replace(hour=hour)),
            "path": str(
                foundation.raw_hour_path(
                    storage_root, symbol, day.replace(hour=hour)
                ).relative_to(storage_root)
            ).replace("\\", "/"),
            "source_file_id": f"{symbol}-{day.replace(hour=hour):%Y%m%d%H}",
        }
        for hour in range(24)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify prospective macro M5 cache")
    parser.add_argument("manifest")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "prospective_macro_v1.json").read_text(encoding="utf-8")
    )
    foundation = load_foundation(REPO_ROOT, config)
    storage_root = Path(os.environ[config["storage_environment_variable"]]).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    feature_path = Path(manifest["feature_path"]).resolve()
    snapshot_path = Path(manifest["snapshot_manifest"]).resolve()
    if sha256_file(feature_path) != manifest["feature_sha256"]:
        raise ValueError("prospective macro feature hash mismatch")
    if sha256_file(snapshot_path) != manifest["snapshot_manifest_sha256"]:
        raise ValueError("prospective macro snapshot hash mismatch")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    context = config["historical_context"]
    frozen_path = storage_root / context["feature_cache"]
    frozen = pd.read_parquet(frozen_path)
    day = datetime.fromisoformat(context["parity_date_utc"]).replace(tzinfo=UTC)
    rebuilt_parity = combine_symbols(
        {
            symbol: load_symbol_hours(
                foundation,
                storage_root,
                symbol,
                parity_rows(foundation, storage_root, symbol, day),
            )
            for symbol in config["symbols"]
        }
    )
    parity = parity_against_frozen(rebuilt_parity, frozen)
    rebuilt = combine_symbols(
        {
            symbol: load_symbol_hours(
                foundation,
                storage_root,
                symbol,
                [row for row in snapshot["rows"] if row["symbol"] == symbol],
            )
            for symbol in config["symbols"]
        }
    )
    stored = pd.read_parquet(feature_path)
    pd.testing.assert_frame_equal(
        rebuilt,
        stored,
        check_dtype=False,
        check_exact=False,
        rtol=0.0,
        atol=1e-12,
    )
    if len(stored) != int(manifest["rows"]):
        raise ValueError("prospective macro feature row count mismatch")
    print(
        json.dumps(
            {
                "status": "DUKASCOPY_MACRO_PROSPECTIVE_M5_VERIFICATION_PASS",
                "manifest_sha256": sha256_file(manifest_path),
                "feature_sha256": sha256_file(feature_path),
                "rows": len(stored),
                "historical_parity": parity,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
