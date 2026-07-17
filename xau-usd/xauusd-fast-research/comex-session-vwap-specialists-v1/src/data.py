from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SHARED_DATA_PATH = ROOT / "independent-specialists-v1" / "src" / "data.py"


def _load_shared_data() -> Any:
    name = "xau_comex_vwap_shared_data"
    spec = importlib.util.spec_from_file_location(name, SHARED_DATA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared data module from {SHARED_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SHARED_DATA = _load_shared_data()


@dataclass(frozen=True)
class ResearchInputs:
    gold: Any
    comex_vwap: pd.DataFrame
    evidence: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_comex_vwap(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["comex_source"]
    path = Path(source["path"])
    actual_sha = sha256_file(path)
    if actual_sha != source["sha256"]:
        raise ValueError(f"COMEX VWAP cache hash mismatch: {actual_sha}")
    frame = pd.read_parquet(path)
    required = {
        "bucket",
        "volume",
        "trade_count",
        "open",
        "high",
        "low",
        "close",
        "session_date",
        "session_vwap",
        "vwap_deviation",
        "available_time_utc",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"COMEX VWAP cache is missing columns {missing}")
    if len(frame) != int(source["expected_rows"]):
        raise ValueError(f"Expected {source['expected_rows']} COMEX rows, found {len(frame)}")
    frame = frame.copy()
    frame["bucket"] = pd.to_datetime(frame["bucket"], utc=True)
    frame["available_time_utc"] = pd.to_datetime(frame["available_time_utc"], utc=True)
    frame = frame.sort_values("available_time_utc", kind="mergesort").reset_index(drop=True)
    if frame["available_time_utc"].duplicated().any():
        raise ValueError("Duplicate COMEX VWAP availability timestamps")
    if not (frame["available_time_utc"] > frame["bucket"]).all():
        raise ValueError("COMEX VWAP rows must become available after their source bucket starts")
    evidence = {
        "path": str(path),
        "sha256": actual_sha,
        "rows": int(len(frame)),
        "first_available_at": frame["available_time_utc"].min().isoformat(),
        "last_available_at": frame["available_time_utc"].max().isoformat(),
    }
    return frame, evidence


def load_inputs(config: dict[str, Any]) -> ResearchInputs:
    gold = SHARED_DATA.load_bundle(config)
    comex_vwap, comex_evidence = load_comex_vwap(config)
    return ResearchInputs(
        gold=gold,
        comex_vwap=comex_vwap,
        evidence={"gold": gold.evidence, "comex_vwap": comex_evidence},
    )
