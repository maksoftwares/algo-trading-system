from __future__ import annotations

import json
from typing import Any

import pandas as pd

from . import neutral_0608_range_breakout_transfer_execution as engine
from .research import PACKAGE_ROOT, serialize, sha256_file


CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_late_session_inventory_unwind_v1_1_execution.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_LATE_SESSION_INVENTORY_UNWIND_V1_1_"
    "EXECUTION_PREREG_2026_07_29.sha256.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_late_session_inventory_unwind_v1_1_execution"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_forward_price_path") is not True
        or lock.get("frozen_before_pnl") is not True
        or lock.get("oracle_decision_use_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Inventory-unwind execution lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Inventory-unwind execution drift: {relative}"
            )
        checked[relative] = actual
    return checked


def load_candidates(config: dict[str, Any]) -> pd.DataFrame:
    census_lock = config["census_result_lock"]
    census_lock_path = PACKAGE_ROOT / census_lock["path"]
    if sha256_file(census_lock_path) != census_lock["sha256"]:
        raise RuntimeError("Inventory-unwind census result lock drift")
    census_result = json.loads(
        census_lock_path.read_text(encoding="utf-8")
    )
    if (
        census_result["status"] != census_lock["required_status"]
        or census_result.get("census_pass") is not True
        or float(census_result["selected_threshold_pips"])
        != float(
            config["candidate_source"][
                "selected_displacement_threshold_pips"
            ]
        )
    ):
        raise RuntimeError("Inventory-unwind census did not pass")
    source = config["candidate_source"]
    path = PACKAGE_ROOT / source["path"]
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("Inventory-unwind candidate source drift")
    candidates = pd.read_csv(path)
    required = {
        "family",
        "signal_time_utc",
        "entry_time_utc",
        "side",
        "state_known_lag_hours",
        "risk_eligible",
        "entry_price_decision_time",
        "stop_price_decision_time",
        "risk_distance",
        "risk_pips",
        "displacement_threshold_pips",
    }
    if not required.issubset(candidates.columns):
        raise RuntimeError("Inventory-unwind candidate schema drift")
    for column in (
        "signal_time_utc",
        "entry_time_utc",
        "matched_state_time_utc",
        "state_known_at_utc",
    ):
        candidates[column] = pd.to_datetime(
            candidates[column],
            utc=True,
            errors="raise",
        )
    if (
        len(candidates) != int(source["rows"])
        or not candidates["family"].eq(source["family"]).all()
        or not candidates["side"].isin(["LONG", "SHORT"]).all()
        or not candidates["risk_eligible"].astype(bool).all()
        or candidates["entry_time_utc"].duplicated().any()
        or candidates["state_known_lag_hours"].gt(
            float(source["maximum_state_known_lag_hours"])
        ).any()
        or candidates["risk_distance"].le(0.0).any()
        or not candidates["displacement_threshold_pips"].eq(
            float(source["selected_displacement_threshold_pips"])
        ).all()
    ):
        raise RuntimeError("Inventory-unwind candidate census drift")
    candidates["window"] = ""
    for name, bounds in config["windows"].items():
        if name == "LATEST_SIX_MONTHS":
            continue
        start, end = (pd.Timestamp(value) for value in bounds)
        mask = candidates["entry_time_utc"].between(
            start,
            end,
            inclusive="both",
        )
        candidates.loc[mask, "window"] = name
    if candidates["window"].eq("").any():
        raise RuntimeError("Candidate outside frozen windows")
    return candidates.sort_values(
        ["entry_time_utc", "side"]
    ).reset_index(drop=True)


def run_execution() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    config = load_config()
    candidates = load_candidates(config)
    m5 = engine.load_eurusd_m5(config)
    trades, routing = engine.execute_candidates(candidates, m5, config)
    summary, matches = engine.summarize(trades, config)
    status = (
        "PERFORMANCE_GATES_PASS_REQUIRES_PROSPECTIVE_FREEZE"
        if summary["all_performance_gates_passed"]
        else "REJECTED_EXACT_LATE_SESSION_INVENTORY_UNWIND"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_late_session_inventory_unwind_"
            "execution_result_v1_1"
        ),
        "status": status,
        "frozen_at_utc": config["frozen_at_utc"],
        "candidates": int(len(candidates)),
        "executed_trades": int(len(trades)),
        "routing_status_counts": {
            str(key): int(value)
            for key, value in routing["status"].value_counts().items()
        },
        "summary": summary,
        "retrospective_causal_not_pristine_oos": True,
        "historical_pass_can_authorize_demo": False,
        "broker_action_allowed": False,
    }
    return result, {
        "TRADES": trades,
        "ROUTING": routing,
        "ORACLE_MATCHES": matches,
    }


def write_result(
    result: dict[str, Any],
    artifacts: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            engine._safe(serialize(result)),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT_ROOT / "RESULT.json").write_text(
        payload,
        encoding="utf-8",
    )
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


_safe = engine._safe


__all__ = [
    "_safe",
    "load_candidates",
    "load_config",
    "run_execution",
    "verify_lock",
    "write_result",
]
