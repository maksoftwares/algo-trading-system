from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


HOUR_MS = 3_600_000
M5_MS = 300_000
DAY_MS = 86_400_000


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, np.generic):
        return json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    return value


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        json_ready(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def verify_bound_file(repo_root: Path, spec: Mapping[str, Any], label: str) -> Path:
    path = resolve_path(repo_root, str(spec["path"])).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = sha256_file(path)
    if observed != str(spec["sha256"]):
        raise ValueError(f"Hash mismatch for {label}: {path}")
    return path


def timestamp_ms(value: Any) -> int:
    return int(pd.Timestamp(value).value // 1_000_000)


def timestamp_utc_ms(value: int | None) -> pd.Timestamp | pd.NaT:
    if value is None:
        return pd.NaT
    return pd.Timestamp(int(value), unit="ms", tz="UTC")


def stable_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, compression="zstd")
