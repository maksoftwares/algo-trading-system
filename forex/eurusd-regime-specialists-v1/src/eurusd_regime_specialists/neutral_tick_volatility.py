from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .neutral_tick_microstructure import (
    MODEL_FEATURE_COLUMNS,
    run_neutral_tick_microstructure_with_config,
)
from .research import PACKAGE_ROOT, serialize, sha256_file


VOLATILITY_MODEL_FEATURES = MODEL_FEATURE_COLUMNS + ["risk_pips"]


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_tick_volatility.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_TICK_VOLATILITY_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_volatility_lifecycle_outcome_inspection")
        is not True
    ):
        raise RuntimeError("Neutral tick-volatility contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Neutral tick-volatility preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def run_neutral_tick_volatility() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    return run_neutral_tick_microstructure_with_config(
        load_config(), VOLATILITY_MODEL_FEATURES
    )


def write_json(path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
