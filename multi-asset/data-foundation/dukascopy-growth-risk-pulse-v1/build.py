from __future__ import annotations

import json
import os
from datetime import datetime
from functools import reduce
from pathlib import Path

import pandas as pd

from acquire import hours_in_month, instrument_map, month_keys
from src.foundation import (
    add_causal_features,
    aggregate_hour_m5,
    read_stored_hour,
    sha256_file,
    validate_curated,
    write_json,
)


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "dukascopy_growth_risk_pulse_v1.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_symbol(
    storage: Path,
    spec: dict[str, object],
    months: list[tuple[int, int]],
) -> tuple[pd.DataFrame, dict[str, object]]:
    symbol = str(spec["symbol"])
    prefix = str(spec["prefix"])
    frames: list[pd.DataFrame] = []
    records: list[dict[str, object]] = []
    for year, month in months:
        partition = (
            storage
            / "raw"
            / symbol
            / f"year={year:04d}"
            / f"month={month:02d}"
        )
        acquisition_path = partition / "_ACQUISITION_MANIFEST.json"
        frozen_path = partition / "_FROZEN_MANIFEST.json"
        if not acquisition_path.is_file() or not frozen_path.is_file():
            raise FileNotFoundError(f"unfrozen source month: {symbol} {year:04d}-{month:02d}")
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        if (
            acquisition.get("symbol") != symbol
            or acquisition.get("month") != f"{year:04d}-{month:02d}"
            or not bool(frozen.get("complete"))
        ):
            raise ValueError(f"cross-month or incomplete source: {symbol} {year:04d}-{month:02d}")
        rows = acquisition.get("rows")
        expected_hours = hours_in_month(year, month)
        if not isinstance(rows, list) or len(rows) != len(expected_hours):
            raise ValueError(f"incomplete acquisition manifest: {symbol} {year:04d}-{month:02d}")

        month_frames: list[pd.DataFrame] = []
        for hour, row in zip(expected_hours, rows, strict=True):
            if row.get("symbol") != symbol:
                raise ValueError("cross-symbol acquisition row")
            path = storage / str(row["path"])
            if sha256_file(path) != row["stored_sha256"]:
                raise ValueError(f"stored source hash mismatch: {path}")
            _, ticks = read_stored_hour(
                path,
                hour,
                int(spec["price_scale"]),
                str(row["source_sha256"]),
            )
            frame = aggregate_hour_m5(ticks, prefix)
            if not frame.empty:
                month_frames.append(frame)
        month_frame = (
            pd.concat(month_frames, ignore_index=True)
            if month_frames
            else pd.DataFrame()
        )
        if not month_frame.empty:
            frames.append(month_frame)
        record = {
            "month": f"{year:04d}-{month:02d}",
            "acquisition_manifest_sha256": sha256_file(acquisition_path),
            "frozen_manifest_sha256": sha256_file(frozen_path),
            "source_tick_count": sum(int(row["tick_count"]) for row in rows),
            "source_bytes": sum(int(row["source_bytes"]) for row in rows),
            "stored_bytes": sum(int(row["stored_bytes"]) for row in rows),
            "m5_rows": int(len(month_frame)),
            "nonempty_hours": sum(int(row["tick_count"]) > 0 for row in rows),
        }
        records.append(record)
        print({"symbol": symbol, **record}, flush=True)

    result = pd.concat(frames, ignore_index=True).sort_values(
        "bar_open_timestamp_ms", kind="stable"
    )
    if result["bar_open_timestamp_ms"].duplicated().any():
        raise ValueError(f"duplicate {symbol} M5 timestamps")
    result = add_causal_features(result, prefix)
    metadata_path = storage / "metadata" / f"{symbol}.json"
    return result, {
        "symbol": symbol,
        "prefix": prefix,
        "source_code": spec["source_code"],
        "metadata_sha256": sha256_file(metadata_path),
        "rows": int(len(result)),
        "first_bar_open_timestamp_ms": int(result["bar_open_timestamp_ms"].min()),
        "last_bar_open_timestamp_ms": int(result["bar_open_timestamp_ms"].max()),
        "source_tick_count": sum(int(row["source_tick_count"]) for row in records),
        "source_bytes": sum(int(row["source_bytes"]) for row in records),
        "stored_bytes": sum(int(row["stored_bytes"]) for row in records),
        "months": records,
    }


def main() -> None:
    storage = Path(
        os.getenv(
            CONFIG["storage_environment_variable"], CONFIG["default_storage_root"]
        )
    )
    start = datetime.fromisoformat(CONFIG["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(CONFIG["end_exclusive_utc"].replace("Z", "+00:00"))
    months = month_keys(start, end)

    frames: list[pd.DataFrame] = []
    records: list[dict[str, object]] = []
    for spec in instrument_map().values():
        frame, record = load_symbol(storage, spec, months)
        frames.append(frame)
        records.append(record)
    result = reduce(
        lambda left, right: left.merge(
            right, on="bar_open_timestamp_ms", how="outer", validate="one_to_one"
        ),
        frames,
    ).sort_values("bar_open_timestamp_ms", kind="stable").reset_index(drop=True)
    prefixes = [str(spec["prefix"]) for spec in instrument_map().values()]
    validate_curated(result, prefixes)

    output_path = storage / CONFIG["curated_file"]
    manifest_path = storage / CONFIG["curated_manifest"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False, compression="zstd")
    write_json(
        manifest_path,
        {
            "schema_version": "dukascopy_growth_risk_pulse_m5_v1",
            "source": "OFFICIAL_DUKASCOPY_JETTA_V1",
            "config_sha256": sha256_file(CONFIG_PATH),
            "curated_sha256": sha256_file(output_path),
            "rows": int(len(result)),
            "columns": result.columns.tolist(),
            "duplicate_timestamps": int(
                result["bar_open_timestamp_ms"].duplicated().sum()
            ),
            "first_bar_open_timestamp_ms": int(
                result["bar_open_timestamp_ms"].min()
            ),
            "last_bar_open_timestamp_ms": int(
                result["bar_open_timestamp_ms"].max()
            ),
            "paid_data_used": False,
            "databento_used": False,
            "xau_outcomes_opened": False,
            "instruments": records,
        },
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
