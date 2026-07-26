from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include UTC timezone")
    return parsed.astimezone(UTC)


def completed_hour_floor(now: datetime) -> datetime:
    return now.astimezone(UTC).replace(minute=0, second=0, microsecond=0)


def hour_range(start: datetime, end_exclusive: datetime) -> list[datetime]:
    start = start.astimezone(UTC)
    end_exclusive = end_exclusive.astimezone(UTC)
    if start.minute or start.second or start.microsecond:
        raise ValueError("start must be hour aligned")
    if end_exclusive.minute or end_exclusive.second or end_exclusive.microsecond:
        raise ValueError("end must be hour aligned")
    if end_exclusive <= start:
        raise ValueError("end must be after start")
    count = int((end_exclusive - start).total_seconds() // 3600)
    return [start + timedelta(hours=index) for index in range(count)]


def load_foundation(repo_root: Path, config: dict[str, Any]) -> ModuleType:
    source = config["source"]
    path = repo_root / source["implementation_path"]
    actual = sha256_file(path)
    if actual != source["implementation_sha256"]:
        raise ValueError(f"foundation implementation digest mismatch: {actual}")
    spec = importlib.util.spec_from_file_location("prospective_macro_foundation", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load foundation implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if module.OFFICIAL_ORIGIN != source["official_origin"]:
        raise ValueError("official source origin mismatch")
    module.INSTRUMENTS.update(config["symbols"])
    return module


def acquire(
    foundation: ModuleType,
    storage_root: Path,
    symbols: list[str],
    hours: list[datetime],
    concurrency: int,
) -> list[dict[str, Any]]:
    jobs = [(symbol, hour) for symbol in symbols for hour in hours]
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(
        max_workers=concurrency, thread_name_prefix="prospective-macro"
    ) as executor:
        futures = {
            executor.submit(foundation.acquire_hour, storage_root, symbol, hour): (
                symbol,
                hour,
            )
            for symbol, hour in jobs
        }
        for index, future in enumerate(as_completed(futures), start=1):
            rows.append(future.result())
            if index % 48 == 0 or index == len(jobs):
                print(f"completed_symbol_hours={index}/{len(jobs)}", flush=True)
    return sorted(rows, key=lambda row: (row["symbol"], row["hour_utc"]))


def run(
    lane_root: Path,
    end_exclusive: datetime,
    concurrency: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    repo_root = lane_root.parents[2]
    config = json.loads(
        (lane_root / "config" / "prospective_macro_v1.json").read_text(encoding="utf-8")
    )
    maximum = int(config["maximum_concurrency"])
    if not 1 <= concurrency <= maximum:
        raise ValueError(f"concurrency must be between 1 and {maximum}")
    observed_now = datetime.now(UTC) if now is None else now.astimezone(UTC)
    if end_exclusive > completed_hour_floor(observed_now):
        raise ValueError("end requests the open UTC hour or future data")
    start = parse_utc(config["start_utc"])
    hours = hour_range(start, end_exclusive)
    symbols = list(config["symbols"])
    foundation = load_foundation(repo_root, config)
    env_name = config["storage_environment_variable"]
    storage_raw = os.environ.get(env_name, "").strip()
    if not storage_raw:
        raise ValueError(f"{env_name} is required")
    storage_root = Path(storage_raw).expanduser().resolve()
    rows = acquire(foundation, storage_root, symbols, hours, concurrency)
    successful = {"DOWNLOADED_VALID", "RESUMED_VALID"}
    if len(rows) != len(hours) * len(symbols):
        raise ValueError("macro snapshot row count is incomplete")
    if any(row["status"] not in successful for row in rows):
        raise ValueError("macro snapshot contains a failed source hour")
    payload = {
        "schema_version": config["schema_version"],
        "created_utc": foundation.utc_now(),
        "symbols": symbols,
        "start_utc": foundation.iso_utc(start),
        "end_exclusive_utc": foundation.iso_utc(end_exclusive),
        "completed_hours_per_symbol": len(hours),
        "completed_symbol_hours": len(rows),
        "downloaded_symbol_hours": sum(
            row["status"] == "DOWNLOADED_VALID" for row in rows
        ),
        "resumed_symbol_hours": sum(row["status"] == "RESUMED_VALID" for row in rows),
        "tick_count": sum(int(row["tick_count"]) for row in rows),
        "bytes": sum(int(row["bytes"]) for row in rows),
        "rows": rows,
        "source": config["source"],
        "authorization": config["authorization"],
    }
    name = f"MACRO_{start:%Y%m%d%H}_{end_exclusive:%Y%m%d%H}_PROSPECTIVE_SNAPSHOT.json"
    manifest = storage_root / config["output"]["manifest_directory"] / name
    foundation.write_json(manifest, payload)
    return {
        "status": "DUKASCOPY_MACRO_PROSPECTIVE_SNAPSHOT_READY",
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "completed_symbol_hours": len(rows),
        "tick_count": payload["tick_count"],
        "bytes": payload["bytes"],
    }
