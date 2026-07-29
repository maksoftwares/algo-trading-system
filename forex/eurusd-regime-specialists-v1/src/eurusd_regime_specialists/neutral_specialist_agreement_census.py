from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_neutral_specialist_agreement_census.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_SPECIALIST_AGREEMENT_CENSUS_V1_1_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_specialist_agreement_census"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_signal_census") is not True
        or lock.get("outcome_loading_allowed") is not False
        or lock.get("oracle_loading_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Specialist-agreement census lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Specialist-agreement census drift: {relative}")
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def load_signal_only_ledgers(
    config: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    cfg = load_config() if config is None else config
    allowed = list(cfg["source_boundary"]["csv_columns_allowed"])
    if allowed != ["entry_time_utc", "side"]:
        raise RuntimeError("Signal-only column boundary drift")
    frames: list[pd.DataFrame] = []
    census: dict[str, Any] = {}
    for expert in cfg["experts"]:
        expert_id = str(expert["expert_id"])
        path = PACKAGE_ROOT / expert["path"]
        digest = sha256_file(path)
        if digest != expert["sha256"]:
            raise RuntimeError(f"Signal source hash drift: {expert_id}")
        frame = pd.read_csv(path, usecols=allowed)
        if set(frame.columns) != set(allowed):
            raise RuntimeError(f"Signal-only schema drift: {expert_id}")
        frame["entry_time_utc"] = pd.to_datetime(
            frame["entry_time_utc"], utc=True, errors="raise"
        )
        if not frame["side"].isin(["LONG", "SHORT"]).all():
            raise RuntimeError(f"Invalid signal side: {expert_id}")
        frame["expert_id"] = expert_id
        frame["mechanism"] = str(expert["mechanism"])
        frame["source_row"] = np.arange(len(frame), dtype=np.int64)
        frames.append(frame)
        census[expert_id] = {
            "signals": len(frame),
            "first_signal_utc": frame["entry_time_utc"].min(),
            "last_signal_utc": frame["entry_time_utc"].max(),
            "sha256": digest,
        }
    signals = pd.concat(frames, ignore_index=True, sort=False)
    signals = signals.sort_values(
        ["entry_time_utc", "expert_id", "source_row"]
    ).reset_index(drop=True)
    return signals, census


def build_exact_clock_agreements(
    signals: pd.DataFrame,
    *,
    minimum_distinct_experts: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"entry_time_utc", "side", "expert_id"}
    if not required.issubset(signals.columns):
        raise ValueError("Signal frame is missing agreement columns")
    unique = signals.drop_duplicates(
        ["entry_time_utc", "expert_id", "side"]
    ).copy()
    agreements: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for clock, block in unique.groupby("entry_time_utc", sort=True):
        by_side = {
            side: sorted(set(side_block["expert_id"].astype(str)))
            for side, side_block in block.groupby("side", sort=True)
        }
        all_experts = sorted(set(block["expert_id"].astype(str)))
        if len(by_side) > 1:
            conflicts.append(
                {
                    "entry_time_utc": clock,
                    "status": "CASH_CONFLICT",
                    "long_experts": "|".join(by_side.get("LONG", [])),
                    "short_experts": "|".join(by_side.get("SHORT", [])),
                    "distinct_experts": len(all_experts),
                }
            )
            continue
        side = next(iter(by_side))
        experts = by_side[side]
        if len(experts) < minimum_distinct_experts:
            continue
        agreements.append(
            {
                "entry_time_utc": clock,
                "side": side,
                "distinct_experts": len(experts),
                "expert_combination": "|".join(experts),
                "eligible_date": clock.strftime("%Y-%m-%d"),
            }
        )
    return pd.DataFrame(agreements), pd.DataFrame(conflicts)


def route_earliest_per_day(agreements: pd.DataFrame) -> pd.DataFrame:
    if agreements.empty:
        return agreements.copy()
    ordered = agreements.sort_values(
        [
            "entry_time_utc",
            "side",
            "expert_combination",
        ]
    ).copy()
    return (
        ordered.groupby("eligible_date", sort=True, as_index=False)
        .first()
        .sort_values("entry_time_utc")
        .reset_index(drop=True)
    )


def _window_counts(
    routed: pd.DataFrame, windows: dict[str, list[str]]
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name, bounds in windows.items():
        start, end = (pd.Timestamp(value) for value in bounds)
        counts[name] = int(
            routed["entry_time_utc"]
            .between(start, end, inclusive="both")
            .sum()
        )
    return counts


def build_census(
    signals: pd.DataFrame,
    *,
    input_census: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    minimum = int(
        config["agreement_rule"]["minimum_distinct_experts_same_side"]
    )
    raw, conflicts = build_exact_clock_agreements(
        signals, minimum_distinct_experts=minimum
    )
    routed = route_earliest_per_day(raw)
    counts = _window_counts(routed, config["windows"])
    side_counts = (
        {
            str(key): int(value)
            for key, value in routed["side"].value_counts().items()
        }
        if not routed.empty
        else {}
    )
    combinations = (
        int(routed["expert_combination"].nunique())
        if not routed.empty
        else 0
    )
    contributors = (
        sorted(
            {
                expert
                for value in routed["expert_combination"]
                for expert in str(value).split("|")
            }
        )
        if not routed.empty
        else []
    )
    gates = config["capacity_gates"]
    gate_results = {
        "minimum_routed_candidates_total": len(routed)
        >= int(gates["minimum_routed_candidates_total"]),
        "minimum_routed_candidates_by_window": all(
            counts[name] >= int(required)
            for name, required in gates[
                "minimum_routed_candidates_by_window"
            ].items()
        ),
        "minimum_candidates_each_side": all(
            side_counts.get(side, 0)
            >= int(gates["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "minimum_distinct_expert_combinations": combinations
        >= int(gates["minimum_distinct_expert_combinations"]),
        "minimum_contributing_experts": len(contributors)
        >= int(gates["minimum_contributing_experts"]),
    }
    passed = bool(all(gate_results.values()))
    result = {
        "schema_version": "eurusd_neutral_specialist_agreement_census_result_v1",
        "status": (
            "CENSUS_PASS_EXECUTION_FREEZE_ALLOWED"
            if passed
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "frozen_at_utc": config["frozen_at_utc"],
        "source_columns_loaded": ["entry_time_utc", "side"],
        "input_census": input_census,
        "input_signal_rows": len(signals),
        "raw_exact_clock_agreements": len(raw),
        "conflicting_exact_clocks": len(conflicts),
        "routed_candidates": len(routed),
        "routed_candidates_by_window": counts,
        "routed_candidates_by_side": side_counts,
        "distinct_expert_combinations": combinations,
        "contributing_experts": contributors,
        "gate_results": gate_results,
        "all_capacity_gates_passed": passed,
        "eurusd_prices_loaded": False,
        "eurusd_outcomes_loaded": False,
        "pnl_loaded": False,
        "oracle_loaded": False,
        "historical_pass_can_authorize_demo": False,
        "broker_action_allowed": False,
    }
    return result, {
        "SIGNAL_ONLY_INPUTS": signals,
        "RAW_EXACT_CLOCK_AGREEMENTS": raw,
        "ROUTED_EARLIEST_DAILY_AGREEMENTS": routed,
        "CONFLICTING_EXACT_CLOCKS": conflicts,
    }


def run_census() -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    verify_lock()
    config = load_config()
    signals, input_census = load_signal_only_ledgers(config)
    return build_census(
        signals,
        input_census=input_census,
        config=config,
    )


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    return value


def write_result(
    result: dict[str, Any], artifacts: dict[str, pd.DataFrame]
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_safe(result), indent=2, sort_keys=True) + "\n"
    (OUTPUT_ROOT / "CENSUS.json").write_text(payload, encoding="utf-8")
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "build_census",
    "build_exact_clock_agreements",
    "load_signal_only_ledgers",
    "route_earliest_per_day",
    "run_census",
    "verify_lock",
    "write_result",
]
