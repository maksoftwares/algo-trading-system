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
        (root / "config" / "m15_regime_target_campaign_v2.json").read_text(
            encoding="utf-8"
        )
    )
    base_path = (root / str(overlay["base"]["config_path"])).resolve()
    invalidation_path = (root / str(overlay["base"]["invalidation_path"])).resolve()
    if sha256_file(base_path) != str(overlay["base"]["config_sha256"]):
        raise ValueError("V1 base config hash mismatch")
    if sha256_file(invalidation_path) != str(overlay["base"]["invalidation_sha256"]):
        raise ValueError("V1 invalidation hash mismatch")
    config = json.loads(base_path.read_text(encoding="utf-8"))
    for key in ("schema_version", "selection", "outputs", "research_controls"):
        config[key] = overlay[key]
    config["base"] = overlay["base"]
    config["correction"] = overlay["correction"]
    return config


def _utc_nanoseconds(values: pd.Series) -> np.ndarray:
    normalized = pd.to_datetime(values, utc=True).astype("datetime64[ns, UTC]")
    return normalized.astype("int64").to_numpy()


def execution_arrays(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    starts = _utc_nanoseconds(frame["bar_start_utc"])
    ends = _utc_nanoseconds(frame["bar_end_utc"])
    signals = _utc_nanoseconds(frame["timestamp_utc"])
    if not np.array_equal(signals, ends):
        raise ValueError("Signal timestamp must equal completed bar end")
    if np.any(ends <= starts):
        raise ValueError("Nonpositive bar duration after clock normalization")
    return {
        "starts": starts,
        "ends": ends,
        "signals": signals,
        **{
            column: frame[column].to_numpy(dtype=float)
            for column in (
                "bid_open", "bid_high", "bid_low", "bid_close",
                "ask_open", "ask_high", "ask_low", "ask_close", "atr14",
            )
        },
    }


def verify_next_bar_gap(
    arrays: Mapping[str, np.ndarray], signal_index: int
) -> float:
    entry_index = signal_index + 1
    if entry_index >= len(arrays["starts"]):
        raise IndexError(signal_index)
    return (
        int(arrays["starts"][entry_index]) - int(arrays["signals"][signal_index])
    ) / 60_000_000_000
