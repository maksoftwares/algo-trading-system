from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from . import prospective_neutral_validation as prior
from .research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_validation_v1_1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_VALIDATION_V1_1_PREREG_2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_validation_result_v1_1"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    prior.verify_lock()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Prospective validation V1.1 is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective validation V1.1 lock mismatch: {relative}"
            )
        checked[relative] = actual
    superseded = load_config()["supersedes"]
    actual = sha256_file(PACKAGE_ROOT / superseded["path"])
    if actual != superseded["sha256"]:
        raise RuntimeError("Superseded prospective validation lock drift")
    checked[superseded["path"]] = actual
    return checked


def _closed_entries(routed: pd.DataFrame) -> pd.DataFrame:
    closed = routed[routed["status"].eq("CLOSED")].copy()
    if closed.empty:
        return pd.DataFrame(
            columns=["signal_id", "entry_time_utc", "side", "oracle_date"]
        )
    required = {"signal_id", "entry_time_utc", "side"}
    if not required.issubset(closed.columns):
        raise ValueError("Closed prospective ledger lacks temporal fields")
    if closed["signal_id"].astype(str).duplicated().any():
        raise ValueError("Temporal validation received duplicate trades")
    closed["signal_id"] = closed["signal_id"].astype(str)
    closed["entry_time_utc"] = pd.to_datetime(
        closed["entry_time_utc"], utc=True
    ).dt.as_unit("ns")
    closed["side"] = closed["side"].astype(str)
    if not closed["side"].isin(["LONG", "SHORT"]).all():
        raise ValueError("Temporal validation received an unknown side")
    closed["oracle_date"] = closed["entry_time_utc"].dt.strftime("%Y-%m-%d")
    return closed[
        ["signal_id", "entry_time_utc", "side", "oracle_date"]
    ].sort_values(["entry_time_utc", "signal_id"]).reset_index(drop=True)


def _neutral_oracle(oracle: pd.DataFrame) -> pd.DataFrame:
    if oracle.empty:
        return pd.DataFrame(
            columns=[
                "oracle_row_id",
                "oracle_date",
                "side",
                "entry_time_utc",
                "oracle_trade_number",
            ]
        )
    required = {"oracle_date", "side", "regime", "entry_time_utc"}
    if not required.issubset(oracle.columns):
        raise ValueError("Oracle evidence lacks temporal validation fields")
    neutral = oracle[oracle["regime"].eq("NEUTRAL")].copy()
    neutral["entry_time_utc"] = pd.to_datetime(
        neutral["entry_time_utc"], utc=True
    ).dt.as_unit("ns")
    neutral["oracle_date"] = pd.to_datetime(
        neutral["oracle_date"], utc=True
    ).dt.strftime("%Y-%m-%d")
    neutral["side"] = neutral["side"].astype(str)
    if not neutral["side"].isin(["LONG", "SHORT"]).all():
        raise ValueError("Oracle evidence contains an unknown side")
    if "oracle_trade_number" not in neutral.columns:
        neutral["oracle_trade_number"] = np.arange(1, len(neutral) + 1)
    neutral = neutral.sort_values(
        ["oracle_date", "side", "entry_time_utc", "oracle_trade_number"]
    ).reset_index(drop=True)
    neutral["oracle_row_id"] = np.arange(len(neutral), dtype=int)
    return neutral[
        [
            "oracle_row_id",
            "oracle_date",
            "side",
            "entry_time_utc",
            "oracle_trade_number",
        ]
    ]


def _better_state(
    candidate: tuple[int, float, tuple[tuple[str, int, float], ...]],
    incumbent: tuple[int, float, tuple[tuple[str, int, float], ...]] | None,
) -> bool:
    if incumbent is None:
        return True
    if candidate[0] != incumbent[0]:
        return candidate[0] > incumbent[0]
    if not math.isclose(candidate[1], incumbent[1], abs_tol=1e-12):
        return candidate[1] < incumbent[1]
    return candidate[2] < incumbent[2]


def _optimal_group_matches(
    predictions: pd.DataFrame,
    oracle: pd.DataFrame,
    window_minutes: int,
) -> list[dict[str, Any]]:
    if predictions.empty or oracle.empty:
        return []
    oracle = oracle.sort_values(
        ["entry_time_utc", "oracle_trade_number", "oracle_row_id"]
    ).reset_index(drop=True)
    states: dict[
        int,
        tuple[int, float, tuple[tuple[str, int, float], ...]],
    ] = {0: (0, 0.0, ())}
    for prediction in predictions.sort_values(
        ["entry_time_utc", "signal_id"]
    ).to_dict(orient="records"):
        updated = dict(states)
        for mask, state in states.items():
            for local_index, candidate in enumerate(
                oracle.to_dict(orient="records")
            ):
                bit = 1 << local_index
                if mask & bit:
                    continue
                delta = abs(
                    (
                        prediction["entry_time_utc"]
                        - candidate["entry_time_utc"]
                    ).total_seconds()
                    / 60.0
                )
                if delta > window_minutes:
                    continue
                pair = (
                    str(prediction["signal_id"]),
                    int(candidate["oracle_row_id"]),
                    float(delta),
                )
                proposal = (
                    state[0] + 1,
                    state[1] + float(delta),
                    state[2] + (pair,),
                )
                target_mask = mask | bit
                if _better_state(proposal, updated.get(target_mask)):
                    updated[target_mask] = proposal
        states = updated
    best: tuple[int, float, tuple[tuple[str, int, float], ...]] | None = None
    for state in states.values():
        if _better_state(state, best):
            best = state
    if best is None:
        return []
    oracle_lookup = oracle.set_index("oracle_row_id")
    return [
        {
            "signal_id": signal_id,
            "oracle_row_id": oracle_row_id,
            "absolute_delta_minutes": delta,
            "oracle_entry_time_utc": oracle_lookup.loc[
                oracle_row_id, "entry_time_utc"
            ],
            "oracle_trade_number": int(
                oracle_lookup.loc[oracle_row_id, "oracle_trade_number"]
            ),
        }
        for signal_id, oracle_row_id, delta in best[2]
    ]


def _uniform_time_side_probability(
    day_oracle: pd.DataFrame,
    *,
    window_minutes: int,
    grid_minutes: int,
) -> float:
    if day_oracle.empty:
        return 0.0
    day = pd.Timestamp(day_oracle["oracle_date"].iloc[0], tz="UTC")
    grid = day + pd.to_timedelta(
        np.arange(0, 24 * 60, grid_minutes), unit="m"
    )
    covered = 0
    for side in ("LONG", "SHORT"):
        side_times = day_oracle.loc[
            day_oracle["side"].eq(side), "entry_time_utc"
        ]
        side_covered = np.zeros(len(grid), dtype=bool)
        for oracle_time in side_times:
            deltas = np.abs((grid - oracle_time).total_seconds() / 60.0)
            side_covered |= deltas <= window_minutes
        covered += int(side_covered.sum())
    return float(covered / (2 * len(grid)))


def temporal_oracle_metrics(
    closed: pd.DataFrame,
    oracle: pd.DataFrame,
    completed_dates: set[str],
    *,
    windows_minutes: Sequence[int],
    grid_minutes: int,
) -> dict[str, Any]:
    entries = _closed_entries(closed)
    neutral = _neutral_oracle(oracle)
    completed = {str(day) for day in completed_dates}
    traded_dates = entries["oracle_date"].tolist()
    missing_dates = sorted(set(traded_dates) - completed)
    dates_unique = not entries["oracle_date"].duplicated().any()
    all_dates_available = not missing_dates and len(entries) > 0
    results: dict[str, Any] = {}
    for window in windows_minutes:
        matches: list[dict[str, Any]] = []
        for (day, side), predictions in entries.groupby(
            ["oracle_date", "side"], sort=True
        ):
            candidates = neutral[
                neutral["oracle_date"].eq(day) & neutral["side"].eq(side)
            ]
            matches.extend(
                _optimal_group_matches(predictions, candidates, int(window))
            )
        match_count = len(matches)
        precision = (
            float(match_count / len(entries))
            if all_dates_available and len(entries)
            else None
        )
        traded_date_oracle = neutral[
            neutral["oracle_date"].isin(set(traded_dates))
        ]
        recall = (
            float(match_count / len(traded_date_oracle))
            if all_dates_available and len(traded_date_oracle)
            else None
        )
        exact_null_valid = all_dates_available and dates_unique
        probabilities = (
            [
                _uniform_time_side_probability(
                    neutral[neutral["oracle_date"].eq(day)],
                    window_minutes=int(window),
                    grid_minutes=int(grid_minutes),
                )
                for day in traded_dates
            ]
            if exact_null_valid
            else []
        )
        baseline = (
            float(np.mean(probabilities)) if probabilities else None
        )
        lift = (
            float(precision - baseline)
            if precision is not None and baseline is not None
            else None
        )
        p_value = (
            prior.poisson_binomial_tail_probability(
                probabilities, match_count
            )
            if probabilities
            else None
        )
        results[f"within_{int(window)}_minutes"] = {
            "one_to_one_matches": match_count,
            "precision": precision,
            "recall_on_traded_dates": recall,
            "uniform_time_and_side_expected_precision": baseline,
            "precision_lift_over_uniform_time_and_side": lift,
            "uniform_time_and_side_poisson_binomial_tail_p_value": p_value,
            "exact_null_valid": exact_null_valid,
            "matches": matches,
        }
    return {
        "matching": (
            "MAXIMUM_CARDINALITY_THEN_MINIMUM_DISTANCE_ONE_TO_ONE_"
            "WITHIN_UTC_DATE_AND_SIDE"
        ),
        "all_closed_trade_oracle_dates_available": all_dates_available,
        "missing_oracle_dates": missing_dates,
        "one_strategy_trade_per_utc_date": dates_unique,
        "closed_trades": len(entries),
        "neutral_oracle_rows_on_traded_dates": int(
            neutral["oracle_date"].isin(set(traded_dates)).sum()
        ),
        "uniform_entry_grid_minutes": int(grid_minutes),
        "windows": results,
    }


def evaluate_validation(
    routed: pd.DataFrame,
    paths: Mapping[str, Mapping[str, Any]],
    oracle: pd.DataFrame,
    completed_oracle_dates: set[str],
    *,
    evaluated_at_utc: Any,
) -> dict[str, Any]:
    result = prior.evaluate_validation(
        routed,
        paths,
        oracle,
        completed_oracle_dates,
        evaluated_at_utc=evaluated_at_utc,
    )
    cfg = load_config()
    gate = cfg["temporal_oracle_gate"]
    timing = temporal_oracle_metrics(
        routed,
        oracle,
        completed_oracle_dates,
        windows_minutes=gate["reported_windows_minutes"],
        grid_minutes=int(gate["uniform_entry_grid_minutes"]),
    )
    primary = timing["windows"][
        f"within_{int(gate['primary_window_minutes'])}_minutes"
    ]
    checks = dict(result["gate_results"])
    temporal_checks = {
        "oracle_one_to_one_dates_complete": bool(
            timing["all_closed_trade_oracle_dates_available"]
        ),
        "oracle_exact_temporal_null_valid": bool(
            timing["one_strategy_trade_per_utc_date"]
            and primary["exact_null_valid"]
        ),
        "oracle_one_to_one_temporal_precision": bool(
            primary["precision"] is not None
            and primary["precision"]
            >= float(gate["minimum_primary_window_precision"])
        ),
        "oracle_temporal_precision_lift": bool(
            primary["precision_lift_over_uniform_time_and_side"] is not None
            and primary["precision_lift_over_uniform_time_and_side"]
            > float(
                gate[
                    "minimum_primary_window_lift_over_uniform_time_and_side"
                ]
            )
        ),
        "oracle_uniform_time_and_side_test": bool(
            primary[
                "uniform_time_and_side_poisson_binomial_tail_p_value"
            ]
            is not None
            and primary[
                "uniform_time_and_side_poisson_binomial_tail_p_value"
            ]
            <= float(
                gate[
                    "maximum_primary_window_uniform_time_and_side_tail_p_value"
                ]
            )
        ),
    }
    checks.update(temporal_checks)
    passed = bool(all(checks.values()))
    if result["status"] in {
        "WAITING_FOR_PROSPECTIVE_START",
        "ACCUMULATING_PROSPECTIVE_EVIDENCE",
    }:
        status = result["status"]
    elif passed:
        status = "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
    else:
        status = "REJECTED_WITHOUT_RETUNING"
    imitation_allowed = bool(all(temporal_checks.values()))
    result.update(
        {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "oracle_temporal_approximation": timing,
            "gate_results": checks,
            "all_gates_passed": passed,
            "oracle_imitation_claim_allowed": imitation_allowed,
            "research_review_allowed": passed,
            "controlled_demo_ready": False,
            "historical_pnl_loaded": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )
    return prior._serialize(result)


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "evaluate_validation",
    "load_config",
    "temporal_oracle_metrics",
    "verify_lock",
]
