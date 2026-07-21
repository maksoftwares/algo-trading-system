from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
UPSTREAM_SRC = (
    REPO_ROOT / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src"
)
sys.path.insert(0, str(UPSTREAM_SRC))
sys.path.insert(0, str(ROOT))

from dukascopy_tick_foundation import foundation as upstream  # noqa: E402
from src.foundation import (  # noqa: E402
    add_causal_features,
    aggregate_m5,
    decode_vol_payload,
    sha256_file,
    validate_curated,
    write_manifest,
)


CONFIG_PATH = ROOT / "config" / "dukascopy_vol_index_v1.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def month_keys(start: datetime, end_exclusive: datetime) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = datetime(start.year, start.month, 1, tzinfo=UTC)
    while cursor < end_exclusive:
        result.append((cursor.year, cursor.month))
        cursor = datetime(
            cursor.year + int(cursor.month == 12),
            1 if cursor.month == 12 else cursor.month + 1,
            1,
            tzinfo=UTC,
        )
    return result


def main() -> None:
    storage = Path(
        os.getenv(
            CONFIG["storage_environment_variable"], CONFIG["default_storage_root"]
        )
    )
    symbol = CONFIG["symbol"]
    upstream.INSTRUMENTS[symbol] = {
        "source_code": CONFIG["source_code"],
        "pip_size": CONFIG["pip_size"],
        "price_scale": CONFIG["price_scale"],
    }
    start = datetime.fromisoformat(CONFIG["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(CONFIG["end_exclusive_utc"].replace("Z", "+00:00"))

    frames: list[pd.DataFrame] = []
    month_records = []
    for year, month in month_keys(start, end):
        partition = storage / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
        frozen_path = partition / "_FROZEN_MANIFEST.json"
        acquisition_path = partition / "_ACQUISITION_MANIFEST.json"
        if not frozen_path.is_file() or not acquisition_path.is_file():
            raise FileNotFoundError(f"Unfrozen source month: {year:04d}-{month:02d}")
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        if not bool(frozen["complete"]):
            raise ValueError(f"Incomplete source month: {year:04d}-{month:02d}")
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        acquisition_rows = acquisition["rows"]

        ticks = []
        for path, raw in upstream.iter_raw_month(storage, symbol, year, month):
            decoded, _ = decode_vol_payload(
                raw, float(CONFIG["maximum_invalid_quote_fraction_per_hour"])
            )
            ticks.extend(decoded)
        frame = aggregate_m5(ticks)
        if not frame.empty:
            frames.append(frame)
        month_records.append(
            {
                "month": f"{year:04d}-{month:02d}",
                "acquisition_manifest_sha256": sha256_file(acquisition_path),
                "frozen_manifest_sha256": sha256_file(frozen_path),
                "m5_rows": int(len(frame)),
                "source_tick_count": int(
                    sum(int(row["source_tick_count"]) for row in acquisition_rows)
                ),
                "valid_tick_count": int(
                    sum(int(row["valid_tick_count"]) for row in acquisition_rows)
                ),
                "invalid_tick_count": int(
                    sum(int(row["invalid_tick_count"]) for row in acquisition_rows)
                ),
                "maximum_invalid_quote_fraction": float(
                    max(
                        float(row["invalid_quote_fraction"]) for row in acquisition_rows
                    )
                ),
                "nonempty_hours": int(
                    sum(int(row["source_tick_count"]) > 0 for row in acquisition_rows)
                ),
            }
        )
        print(month_records[-1], flush=True)

    result = pd.concat(frames, ignore_index=True).sort_values("bar_open_timestamp_ms")
    result = add_causal_features(result)
    validate_curated(result)
    output_path = storage / CONFIG["curated_file"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False, compression="zstd")
    manifest_path = storage / CONFIG["curated_manifest"]
    write_manifest(
        manifest_path,
        {
            "schema_version": "dukascopy_vol_index_m5_v1",
            "config_sha256": sha256_file(CONFIG_PATH),
            "source": "OFFICIAL_DUKASCOPY_JETTA_V1",
            "source_code": CONFIG["source_code"],
            "paid_data_used": False,
            "rows": int(len(result)),
            "first_bar_open_timestamp_ms": int(result["bar_open_timestamp_ms"].min()),
            "last_bar_open_timestamp_ms": int(result["bar_open_timestamp_ms"].max()),
            "columns": result.columns.tolist(),
            "duplicate_timestamps": int(
                result["bar_open_timestamp_ms"].duplicated().sum()
            ),
            "source_tick_count": int(
                sum(record["source_tick_count"] for record in month_records)
            ),
            "valid_tick_count": int(
                sum(record["valid_tick_count"] for record in month_records)
            ),
            "invalid_tick_count": int(
                sum(record["invalid_tick_count"] for record in month_records)
            ),
            "maximum_invalid_quote_fraction": float(
                max(
                    record["maximum_invalid_quote_fraction"] for record in month_records
                )
            ),
            "nonempty_hours": int(
                sum(record["nonempty_hours"] for record in month_records)
            ),
            "curated_sha256": sha256_file(output_path),
            "months": month_records,
        },
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
