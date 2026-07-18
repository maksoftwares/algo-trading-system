from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(root: Path) -> dict[str, Any]:
    overlay = json.loads(
        (root / "config" / "m5_passive_regime_campaign_v5_1.json").read_text(
            encoding="utf-8"
        )
    )
    base_path = (root / str(overlay["base"]["config_path"])).resolve()
    invalidation_path = (root / str(overlay["base"]["invalidation_path"])).resolve()
    unchanged_manifest = (
        root / str(overlay["base"]["unchanged_manifest_path"])
    ).resolve()
    if sha256_file(base_path) != str(overlay["base"]["config_sha256"]):
        raise ValueError("V5 base config hash mismatch")
    if sha256_file(invalidation_path) != str(overlay["base"]["invalidation_sha256"]):
        raise ValueError("V5 invalidation hash mismatch")
    if sha256_file(unchanged_manifest) != str(
        overlay["base"]["unchanged_manifest_sha256"]
    ):
        raise ValueError("V5 manifest hash mismatch")

    v5 = json.loads(base_path.read_text(encoding="utf-8"))
    original_base = (base_path.parent.parent / str(v5["base"]["config_path"])).resolve()
    if sha256_file(original_base) != str(v5["base"]["config_sha256"]):
        raise ValueError("Original M15 base config hash mismatch")
    config = json.loads(original_base.read_text(encoding="utf-8"))
    for key in (
        "schema_version",
        "selection",
        "passive_execution",
        "outputs",
        "research_controls",
    ):
        config[key] = v5[key]
    for key in ("schema_version", "outputs", "research_controls"):
        config[key] = overlay[key]
    config["base"] = overlay["base"]
    config["correction"] = overlay["correction"]
    return config


def utc_nanoseconds(values: pd.Series) -> np.ndarray:
    normalized = pd.to_datetime(values, utc=True).astype("datetime64[ns, UTC]")
    return normalized.astype("int64").to_numpy()


def m5_execution_arrays(m5: pd.DataFrame) -> dict[str, np.ndarray]:
    starts = utc_nanoseconds(m5["bar_start_utc"])
    ends = utc_nanoseconds(m5["bar_end_utc"])
    if np.any(ends <= starts):
        raise ValueError("Nonpositive M5 bar duration after clock normalization")
    return {
        "starts": starts,
        "ends": ends,
        **{
            column: m5[column].to_numpy(dtype=float)
            for column in (
                "bid_open",
                "bid_high",
                "bid_low",
                "bid_close",
                "ask_open",
                "ask_high",
                "ask_low",
                "ask_close",
            )
        },
    }


def activation_gaps_minutes(
    arrays: Mapping[str, np.ndarray], decisions_ns: np.ndarray
) -> np.ndarray:
    positions = np.searchsorted(arrays["starts"], decisions_ns, side="left")
    in_bounds = positions < len(arrays["starts"])
    gaps = np.full(len(decisions_ns), np.nan)
    gaps[in_bounds] = (
        arrays["starts"][positions[in_bounds]] - decisions_ns[in_bounds]
    ) / 60_000_000_000
    return gaps
