from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .research import PACKAGE_ROOT, sha256_file


CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_macro_crossasset_agreement.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_MACRO_CROSSASSET_AGREEMENT_PREREG_2026_07_28.sha256.json"
)
ALLOWED_FAMILIES = frozenset({"CPI", "PPI", "NFP"})
MINIMUM_FORECAST_LEAD_SECONDS = 60
MINIMUM_ACTUAL_LAG_SECONDS = 60


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_first_prospective_signal") is not True:
        raise RuntimeError("Prospective strategy is not preregistered")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in (
        "parent_neutral_date_contract",
        "data_and_classifier_contract",
    ):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"{key} drift")
    parent = cfg["parent_neutral_date_contract"]
    if (
        sha256_file(PACKAGE_ROOT / parent["paired_source_path"])
        != parent["paired_source_sha256"]
    ):
        raise RuntimeError("Parent Neutral-date source drift")
    crossasset = cfg["crossasset_contract"]
    external_checks = {
        crossasset["schema_reference_path"]: crossasset[
            "schema_reference_sha256"
        ],
        crossasset["manifest_path"]: crossasset["manifest_sha256"],
    }
    for path, expected in external_checks.items():
        if sha256_file(Path(path)) != expected:
            raise RuntimeError(f"Cross-asset contract drift: {path}")
    manifest = json.loads(
        Path(crossasset["manifest_path"]).read_text(encoding="utf-8")
    )
    if (
        manifest["bars"]["sha256"]
        != crossasset["schema_reference_sha256"]
    ):
        raise RuntimeError("Cross-asset bars hash drift inside manifest")
    if manifest["contract_sha256"] != crossasset["contract_sha256"]:
        raise RuntimeError("Cross-asset timestamp contract drift")
    return checked


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("All decision timestamps must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _finite(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _direction(change: float, *, positive: str, negative: str) -> str:
    if change > 0:
        return positive
    if change < 0:
        return negative
    return "CASH"


def decide_side(
    *,
    family: str,
    is_neutral: bool,
    neutral_known_at_utc: Any,
    event_time_utc: Any,
    forecast_observed_at_utc: Any,
    actual_observed_at_utc: Any,
    observation_completed_at_utc: Any,
    entry_time_utc: Any,
    forecast_value: float,
    actual_value: float,
    eurusd_pre_mid: float,
    eurusd_post_mid: float,
    dxy_pre_mid: float,
    dxy_post_mid: float,
    treasury_pre_mid: float,
    treasury_post_mid: float,
) -> dict[str, Any]:
    """Return a prospective signal using only information known by entry.

    The scalar reaction endpoints must come from fully completed bars. The
    entry bar is deliberately absent from this interface, so it cannot alter
    any confirmation input.
    """

    event = _utc(event_time_utc)
    neutral_known = _utc(neutral_known_at_utc)
    forecast_observed = _utc(forecast_observed_at_utc)
    actual_observed = _utc(actual_observed_at_utc)
    observation_completed = _utc(observation_completed_at_utc)
    entry = _utc(entry_time_utc)
    event_day_start = event.floor("D")

    if neutral_known > event_day_start:
        raise ValueError("Neutral ownership was not known by UTC midnight")
    if (
        event - forecast_observed
    ).total_seconds() < MINIMUM_FORECAST_LEAD_SECONDS:
        raise ValueError("Forecast lacks the frozen pre-release lead")
    if (
        actual_observed - event
    ).total_seconds() < MINIMUM_ACTUAL_LAG_SECONDS:
        raise ValueError("Actual lacks the frozen post-release lag")
    if actual_observed > entry:
        raise ValueError("Actual was not observable by entry")
    if observation_completed > entry:
        raise ValueError("Observation bars were not complete by entry")
    if entry.floor("D") != event_day_start:
        raise ValueError("Entry must share the event UTC date")

    if family not in ALLOWED_FAMILIES:
        return {
            "side": "CASH",
            "reason": "FAMILY_NOT_OWNED",
            "agreement": False,
        }
    if not is_neutral:
        return {
            "side": "CASH",
            "reason": "DATE_NOT_NEUTRAL",
            "agreement": False,
        }

    surprise = _finite("actual_value", actual_value) - _finite(
        "forecast_value", forecast_value
    )
    eurusd_change = _finite("eurusd_post_mid", eurusd_post_mid) - _finite(
        "eurusd_pre_mid", eurusd_pre_mid
    )
    dxy_change = _finite("dxy_post_mid", dxy_post_mid) - _finite(
        "dxy_pre_mid", dxy_pre_mid
    )
    treasury_change = _finite(
        "treasury_post_mid", treasury_post_mid
    ) - _finite("treasury_pre_mid", treasury_pre_mid)

    macro_side = _direction(
        surprise, positive="SHORT", negative="LONG"
    )
    eurusd_side = _direction(
        eurusd_change, positive="LONG", negative="SHORT"
    )
    crossasset_side = "CASH"
    if dxy_change > 0 and treasury_change < 0:
        crossasset_side = "SHORT"
    elif dxy_change < 0 and treasury_change > 0:
        crossasset_side = "LONG"

    components = {
        "macro_side": macro_side,
        "eurusd_side": eurusd_side,
        "crossasset_side": crossasset_side,
        "surprise_value": surprise,
        "eurusd_change": eurusd_change,
        "dxy_change": dxy_change,
        "treasury_change": treasury_change,
    }
    sides = {macro_side, eurusd_side, crossasset_side}
    if "CASH" in sides:
        return {
            "side": "CASH",
            "reason": "ZERO_OR_NON_DIRECTIONAL_COMPONENT",
            "agreement": False,
            **components,
        }
    if len(sides) != 1:
        return {
            "side": "CASH",
            "reason": "THREE_WAY_DISAGREEMENT",
            "agreement": False,
            **components,
        }
    return {
        "side": macro_side,
        "reason": "THREE_WAY_AGREEMENT",
        "agreement": True,
        **components,
    }


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "decide_side",
    "load_config",
    "verify_lock",
]
