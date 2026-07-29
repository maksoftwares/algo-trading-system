from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from eurusd_regime_specialists import neutral_rate_differential_census as parent

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_rate_differential_capacity_ladder.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_RATE_DIFFERENTIAL_CAPACITY_LADDER_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_rate_differential_capacity_ladder"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_threshold_screen") is not True
        or lock.get("eurusd_outcome_use_allowed") is not False
        or lock.get("post_screen_threshold_change_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Rate capacity-ladder lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Rate capacity-ladder drift: {relative}")
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def verify_parent_contract(
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = config["parent_census_contract"]
    for path_key, hash_key in (
        ("config_path", "config_sha256"),
        ("preregistration_lock_path", "preregistration_lock_sha256"),
        ("result_lock_path", "result_lock_sha256"),
    ):
        path = PACKAGE_ROOT / contract[path_key]
        if sha256_file(path) != contract[hash_key]:
            raise RuntimeError(f"Parent rate census drift: {path_key}")
    parent_result = json.loads(
        (PACKAGE_ROOT / contract["result_lock_path"]).read_text(
            encoding="utf-8"
        )
    )
    if (
        parent_result["status"] != contract["required_result_status"]
        or parent_result["boundaries"]["pnl_loaded"]
        is not contract["required_pnl_loaded"]
    ):
        raise RuntimeError("Parent rate census boundary drift")
    parent_config = json.loads(
        (PACKAGE_ROOT / contract["config_path"]).read_text(encoding="utf-8")
    )
    return parent_config, parent_result


def select_highest_passing(
    threshold_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for result in threshold_results:
        if result["census"]["all_capacity_gates_passed"]:
            return result
    return None


def screen_thresholds(
    neutral: pd.DataFrame,
    common_curve: pd.DataFrame,
    parent_config: dict[str, Any],
    ladder_config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    results: list[dict[str, Any]] = []
    candidates_by_threshold: dict[float, pd.DataFrame] = {}
    for threshold in ladder_config["threshold_ladder_bps_descending"]:
        config = copy.deepcopy(parent_config)
        config["signal"][
            "minimum_absolute_common_date_spread_change_bps_inclusive"
        ] = float(threshold)
        candidates, census = parent.build_candidates(
            neutral, common_curve, config
        )
        threshold_value = float(threshold)
        candidates_by_threshold[threshold_value] = candidates
        results.append(
            {
                "threshold_bps": threshold_value,
                "census": census,
            }
        )
    selected = select_highest_passing(results)
    if selected is None:
        selected_candidates = pd.DataFrame()
        selected_threshold = None
        status = "CENSUS_FAIL_NO_PNL_ALLOWED"
    else:
        selected_threshold = float(selected["threshold_bps"])
        selected_candidates = candidates_by_threshold[selected_threshold]
        status = "CAPACITY_PASS_EXECUTION_FREEZE_ALLOWED"
    screen = {
        "schema_version": (
            "eurusd_neutral_rate_differential_capacity_screen_v1"
        ),
        "status": status,
        "threshold_results": [
            {
                "threshold_bps": row["threshold_bps"],
                "candidates": row["census"]["candidates"],
                "candidates_by_window": row["census"][
                    "candidates_by_window"
                ],
                "candidates_by_side": row["census"]["candidates_by_side"],
                "gate_results": row["census"]["gate_results"],
                "all_capacity_gates_passed": row["census"][
                    "all_capacity_gates_passed"
                ],
            }
            for row in results
        ],
        "selected_threshold_bps": selected_threshold,
        "selected_candidates": len(selected_candidates),
        "selection_rule": ladder_config["selection_rule"],
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "oracle_rows_loaded": False,
        "pnl_loaded": False,
        "post_screen_threshold_change_allowed": False,
        "broker_action_allowed": False,
    }
    return selected_candidates, screen


def run_screen() -> dict[str, Any]:
    verify_lock()
    config = load_config()
    parent_config, _ = verify_parent_contract(config)
    treasury, ecb = parent.load_official_rates(parent_config)
    common = parent.build_common_curve(treasury, ecb)
    neutral = parent.load_neutral_midnights(parent_config)
    selected, screen = screen_thresholds(
        neutral, common, parent_config, config
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    selected.to_csv(
        OUTPUT_ROOT / "SELECTED_CANDIDATES.csv",
        index=False,
        date_format="%Y-%m-%dT%H:%M:%S.%fZ",
    )
    (OUTPUT_ROOT / "SCREEN.json").write_text(
        json.dumps(screen, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return screen
