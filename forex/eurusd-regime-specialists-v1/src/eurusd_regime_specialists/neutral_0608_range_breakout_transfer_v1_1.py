from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from . import neutral_0608_range_breakout_transfer as parent
from .research import PACKAGE_ROOT, serialize, sha256_file


CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_0608_range_breakout_transfer_v1_1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_0608_RANGE_BREAKOUT_TRANSFER_V1_1_"
    "PREREG_2026_07_29.sha256.json"
)
PARENT_CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_0608_range_breakout_transfer.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_0608_range_breakout_transfer_v1_1"
)


def load_overlay() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_config() -> dict[str, Any]:
    overlay = load_overlay()
    cfg = copy.deepcopy(parent.load_config())
    if (
        cfg["outcome_blind_capacity_gates"]
        != overlay["outcome_blind_capacity_gates"]
    ):
        raise RuntimeError("V1.1 capacity gates drifted from v1")
    cfg["schema_version"] = overlay["schema_version"]
    cfg["campaign_id"] = overlay["campaign_id"]
    cfg["frozen_at_utc"] = overlay["frozen_at_utc"]
    cfg["information_status"] = overlay["information_status"]
    cfg["strategy"]["family"] = overlay["family"]
    cfg["eligibility_revision"] = overlay["eligibility_revision"]
    cfg["census_boundaries"] = overlay["census_boundaries"]
    cfg["prohibitions"] = overlay["prohibitions"]
    return cfg


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_v1_1_census") is not True
        or lock.get("locked_before_any_outcome") is not True
        or lock.get("census_forbids_outcome_loading") is not True
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Freshness correction was not locked in time")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Freshness-correction preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    return checked


def apply_freshness_eligibility(
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    revised = candidates.copy()
    prior = revised["risk_eligible"].astype(bool)
    maximum_lag = float(
        cfg["eligibility_revision"]["maximum_state_known_lag_hours"]
    )
    state_fresh = revised["state_known_lag_hours"].le(maximum_lag)
    revised["risk_eligible_before_state_freshness"] = prior
    revised["state_fresh"] = state_fresh
    revised["risk_eligible"] = prior & state_fresh
    revised["family"] = cfg["strategy"]["family"]
    return revised


def summarize_census(
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    parent_manifests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    census = parent.summarize_census(
        candidates,
        cfg,
        parent_manifests=parent_manifests,
    )
    prior = candidates[
        candidates["risk_eligible_before_state_freshness"].astype(bool)
    ]
    rejected = prior[~prior["state_fresh"].astype(bool)]
    census["schema_version"] = (
        "eurusd_neutral_0608_range_breakout_transfer_census_v1_1"
    )
    census["family"] = cfg["strategy"]["family"]
    census["freshness_eligibility"] = {
        "maximum_state_known_lag_hours": float(
            cfg["eligibility_revision"][
                "maximum_state_known_lag_hours"
            ]
        ),
        "parent_risk_eligible_candidates": int(len(prior)),
        "stale_candidates_rejected": int(len(rejected)),
        "stale_candidate_dates_rejected": int(
            rejected["entry_time_utc"].dt.date.nunique()
        ),
    }
    return census


def run_census() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    parent.verify_lock()
    verify_lock()
    cfg = load_config()
    if sha256_file(PARENT_CONFIG_PATH) != load_overlay()[
        "parent_candidate"
    ]["config_sha256"]:
        raise RuntimeError("V1 parent configuration drift")
    parent_cfg = parent.load_parent_config()
    m5, state, manifests = parent.load_inputs(parent_cfg)
    base_candidates = parent.build_candidates(m5, state, cfg)
    candidates = apply_freshness_eligibility(base_candidates, cfg)
    census = summarize_census(
        candidates,
        cfg,
        parent_manifests=manifests,
    )
    eligible = candidates[
        candidates["risk_eligible"].astype(bool)
    ].copy()
    forbidden = {
        "r",
        "pnl",
        "return",
        "exit_time_utc",
        "exit_price",
        "exit_reason",
        "oracle_member",
    }
    if forbidden & set(eligible.columns):
        raise RuntimeError("Outcome field entered v1.1 candidate manifest")
    manifest_bytes = eligible.to_csv(index=False).encode("utf-8")
    census["candidate_manifest_sha256"] = hashlib.sha256(
        manifest_bytes
    ).hexdigest()
    return census, {
        "CANDIDATES": eligible,
        "ALL_SESSION_SIGNALS": candidates,
    }


def write_census(
    census: dict[str, Any],
    artifacts: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            serialize(census),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT_ROOT / "CENSUS.json").write_text(
        payload,
        encoding="utf-8",
    )
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "apply_freshness_eligibility",
    "load_config",
    "run_census",
    "summarize_census",
    "verify_lock",
    "write_census",
]
