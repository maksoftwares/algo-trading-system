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
from typing import Any, Iterable


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
    spec = importlib.util.spec_from_file_location("prospective_xau_foundation", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load foundation implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if module.OFFICIAL_ORIGIN != source["official_origin"]:
        raise ValueError("official source origin mismatch")
    return module


def acquire(
    foundation: ModuleType,
    storage_root: Path,
    symbol: str,
    hours: Iterable[datetime],
    concurrency: int,
) -> list[dict[str, Any]]:
    hour_list = list(hours)
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(
        max_workers=concurrency, thread_name_prefix="prospective-xau"
    ) as executor:
        futures = {
            executor.submit(foundation.acquire_hour, storage_root, symbol, hour): hour
            for hour in hour_list
        }
        for index, future in enumerate(as_completed(futures), start=1):
            rows.append(future.result())
            if index % 24 == 0 or index == len(hour_list):
                print(f"completed_hours={index}/{len(hour_list)}", flush=True)
    return sorted(rows, key=lambda row: row["hour_utc"])


def write_snapshot_manifest(
    foundation: ModuleType,
    storage_root: Path,
    config: dict[str, Any],
    start: datetime,
    end_exclusive: datetime,
    rows: list[dict[str, Any]],
) -> Path:
    expected = len(hour_range(start, end_exclusive))
    successful = {"DOWNLOADED_VALID", "RESUMED_VALID"}
    if len(rows) != expected or any(row["status"] not in successful for row in rows):
        raise ValueError("prospective snapshot contains missing or failed hours")
    payload = {
        "schema_version": config["schema_version"],
        "created_utc": foundation.utc_now(),
        "symbol": config["symbol"],
        "start_utc": foundation.iso_utc(start),
        "end_exclusive_utc": foundation.iso_utc(end_exclusive),
        "completed_hours": expected,
        "downloaded_hours": sum(row["status"] == "DOWNLOADED_VALID" for row in rows),
        "resumed_hours": sum(row["status"] == "RESUMED_VALID" for row in rows),
        "tick_count": sum(int(row["tick_count"]) for row in rows),
        "bytes": sum(int(row["bytes"]) for row in rows),
        "rows": rows,
        "source": config["source"],
        "authorization": config["authorization"],
    }
    name = (
        f"XAUUSD_{start:%Y%m%d%H}_{end_exclusive:%Y%m%d%H}_"
        "PROSPECTIVE_SNAPSHOT.json"
    )
    path = storage_root / config["output"]["manifest_directory"] / name
    foundation.write_json(path, payload)
    return path


def run(
    lane_root: Path,
    end_exclusive: datetime,
    concurrency: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    repo_root = lane_root.parents[2]
    config = json.loads(
        (lane_root / "config" / "prospective_xau_v1.json").read_text(encoding="utf-8")
    )
    maximum = int(config["maximum_concurrency"])
    if not 1 <= concurrency <= maximum:
        raise ValueError(f"concurrency must be between 1 and {maximum}")
    observed_now = datetime.now(UTC) if now is None else now.astimezone(UTC)
    maximum_end = completed_hour_floor(observed_now)
    end_exclusive = end_exclusive.astimezone(UTC)
    if end_exclusive > maximum_end:
        raise ValueError("end requests the open UTC hour or future data")
    start = parse_utc(config["start_utc"])
    hours = hour_range(start, end_exclusive)
    foundation = load_foundation(repo_root, config)
    env_name = config["storage_environment_variable"]
    storage_raw = os.environ.get(env_name, "").strip()
    if not storage_raw:
        raise ValueError(f"{env_name} is required")
    storage_root = Path(storage_raw).expanduser().resolve()
    storage_root.mkdir(parents=True, exist_ok=True)
    rows = acquire(foundation, storage_root, config["symbol"], hours, concurrency)
    manifest = write_snapshot_manifest(
        foundation, storage_root, config, start, end_exclusive, rows
    )
    return {
        "status": "DUKASCOPY_XAU_PROSPECTIVE_SNAPSHOT_READY",
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "completed_hours": len(rows),
        "tick_count": sum(int(row["tick_count"]) for row in rows),
        "bytes": sum(int(row["bytes"]) for row in rows),
    }
