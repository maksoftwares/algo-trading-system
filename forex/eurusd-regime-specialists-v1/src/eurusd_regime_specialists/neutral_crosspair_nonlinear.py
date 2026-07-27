from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .neutral_crosspair import run_neutral_crosspair_with_config
from .research import PACKAGE_ROOT, serialize, sha256_file


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_crosspair_nonlinear.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_CROSSPAIR_NONLINEAR_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_nonlinear_outcome_inspection") is not True:
        raise RuntimeError("Neutral nonlinear contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Neutral nonlinear preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def run_neutral_crosspair_nonlinear() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    return run_neutral_crosspair_with_config(load_config())


def write_json(path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
