from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .prospective_neutral_campaign_orchestration import (
    verify_lock as verify_campaign_lock,
)
from .prospective_neutral_validation import (
    verify_lock as verify_validation_lock,
)
from .research import PACKAGE_ROOT, PIP, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_directional_falsification_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_DIRECTIONAL_FALSIFICATION_"
    "PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Directional falsification contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Directional falsification lock mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in ("campaign_orchestration_contract", "independent_validation_contract"):
        reference = cfg[key]
        if sha256_file(PACKAGE_ROOT / reference["path"]) != reference["sha256"]:
            raise RuntimeError(f"Directional falsification reference drift: {key}")
    verify_campaign_lock()
    verify_validation_lock()
    return checked


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    return value


def _normalize_path(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "timestamp_utc" in result.columns:
        timestamps = pd.to_datetime(result.pop("timestamp_utc"), utc=True).dt.as_unit(
            "ns"
        )
        result.index = pd.DatetimeIndex(timestamps, name="timestamp_utc")
    elif isinstance(result.index, pd.DatetimeIndex):
        if result.index.tz is None:
            raise ValueError("Counterfactual path timestamps must be timezone-aware")
        result.index = result.index.tz_convert("UTC").as_unit("ns")
        result.index.name = "timestamp_utc"
    else:
        raise ValueError("Counterfactual path requires UTC timestamps")
    required = {
        f"{side}_{field}"
        for side in ("bid", "ask")
        for field in ("open", "high", "low", "close")
    }
    if not required.issubset(result.columns):
        raise ValueError("Counterfactual path lacks executable bid/ask OHLC")
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise ValueError("Counterfactual path timestamps must be unique and ordered")
    values = result[list(required)].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Counterfactual path contains non-finite prices")
    return result


def _effective_prices(row: pd.Series, spread_floor: float) -> dict[str, float]:
    return {
        "bid_open": min(
            float(row["bid_open"]),
            float(row["ask_open"]) - spread_floor,
        ),
        "bid_high": min(
            float(row["bid_high"]),
            float(row["ask_high"]) - spread_floor,
        ),
        "bid_low": min(
            float(row["bid_low"]),
            float(row["ask_low"]) - spread_floor,
        ),
        "bid_close": min(
            float(row["bid_close"]),
            float(row["ask_close"]) - spread_floor,
        ),
        "ask_open": max(
            float(row["ask_open"]),
            float(row["bid_open"]) + spread_floor,
        ),
        "ask_high": max(
            float(row["ask_high"]),
            float(row["bid_high"]) + spread_floor,
        ),
        "ask_low": max(
            float(row["ask_low"]),
            float(row["bid_low"]) + spread_floor,
        ),
        "ask_close": max(
            float(row["ask_close"]),
            float(row["bid_close"]) + spread_floor,
        ),
    }


def execute_opposite_side_counterfactual(
    primary: Mapping[str, Any],
    path: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute the exact opposite side without changing time or risk."""
    cfg = load_config()["counterfactual"]
    primary_side = str(primary["side"])
    if primary_side not in {"LONG", "SHORT"}:
        raise ValueError("Counterfactual requires a directional primary trade")
    side = "SHORT" if primary_side == "LONG" else "LONG"
    entry = _utc(primary["entry_time_utc"])
    if _utc(path["entry_time_utc"]) != entry:
        raise RuntimeError("Counterfactual path entry does not match primary")
    expected_hash = str(primary["path_evidence_sha256"]).lower()
    if len(expected_hash) != 64 or str(path["path_evidence_sha256"]).lower() != (
        expected_hash
    ):
        raise RuntimeError("Counterfactual path evidence hash mismatch")
    frame = _normalize_path(path["frame"])
    deadline = entry + pd.Timedelta(hours=float(cfg["maximum_hold_hours"]))
    if _utc(path["deadline_utc"]) != deadline:
        raise RuntimeError("Counterfactual path deadline drift")
    expected = pd.date_range(
        entry,
        deadline - pd.Timedelta(minutes=5),
        freq="5min",
    )
    if list(frame.index) != list(expected):
        raise RuntimeError("Counterfactual path is not continuous and exact")

    risk_pips = float(primary["risk_pips"])
    if risk_pips <= 0:
        raise ValueError("Counterfactual risk must be positive")
    risk_distance = risk_pips * PIP
    spread_floor = float(cfg["minimum_retail_spread_pips"]) * PIP
    slippage = float(cfg["adverse_slippage_pips_per_side"]) * PIP
    target_r = float(cfg["target_r"])
    entry_prices = _effective_prices(frame.iloc[0], spread_floor)
    if side == "LONG":
        entry_price = entry_prices["ask_open"] + slippage
        stop_price = entry_price - risk_distance
        target_price = entry_price + target_r * risk_distance
    else:
        entry_price = entry_prices["bid_open"] - slippage
        stop_price = entry_price + risk_distance
        target_price = entry_price - target_r * risk_distance

    exit_time = deadline
    exit_reason = "TIME_12H"
    exit_price: float | None = None
    for timestamp, row in frame.iterrows():
        prices = _effective_prices(row, spread_floor)
        if side == "LONG":
            if prices["bid_low"] <= stop_price:
                exit_price = min(prices["bid_open"], stop_price) - slippage
                exit_reason = "STOP"
            elif prices["bid_high"] >= target_price:
                exit_price = max(prices["bid_open"], target_price) - slippage
                exit_reason = "TARGET"
            else:
                continue
        else:
            if prices["ask_high"] >= stop_price:
                exit_price = max(prices["ask_open"], stop_price) + slippage
                exit_reason = "STOP"
            elif prices["ask_low"] <= target_price:
                exit_price = min(prices["ask_open"], target_price) + slippage
                exit_reason = "TARGET"
            else:
                continue
        exit_time = timestamp
        break
    if exit_price is None:
        final = _effective_prices(frame.iloc[-1], spread_floor)
        exit_price = (
            final["bid_close"] - slippage
            if side == "LONG"
            else final["ask_close"] + slippage
        )
    signed_move = (
        exit_price - entry_price
        if side == "LONG"
        else entry_price - exit_price
    )
    outcome_r = signed_move / risk_distance
    return {
        "signal_id": str(primary["signal_id"]),
        "primary_side": primary_side,
        "counterfactual_side": side,
        "entry_time_utc": entry,
        "exit_time_utc": exit_time,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "risk_pips": risk_pips,
        "r": outcome_r,
        "extra_half_pip_stress_r": (
            outcome_r
            - float(cfg["extra_round_trip_stress_pips"]) / risk_pips
        ),
        "path_evidence_sha256": expected_hash,
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }


def paired_randomization_p_value(
    differences: np.ndarray,
    *,
    exact_maximum_pairs: int,
    monte_carlo_sign_vectors: int,
    seed: int,
) -> dict[str, Any]:
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("Paired differences must be a finite vector")
    if len(values) == 0:
        return {
            "available": False,
            "pairs": 0,
            "observed_mean_difference_r": None,
            "one_sided_p_value": None,
        }
    observed = float(values.mean())
    tolerance = 1e-12
    if len(values) <= int(exact_maximum_pairs):
        sums = np.asarray([0.0])
        for value in values:
            sums = np.concatenate((sums + value, sums - value))
        statistics = sums / len(values)
        p_value = float(np.mean(statistics >= observed - tolerance))
        method = "EXACT_SIGN_ENUMERATION"
        samples = len(statistics)
    else:
        simulations = int(monte_carlo_sign_vectors)
        if simulations <= 0:
            raise ValueError("Monte Carlo sign-vector count must be positive")
        rng = np.random.default_rng(int(seed))
        signs = rng.integers(
            0,
            2,
            size=(simulations, len(values)),
            dtype=np.int8,
        )
        signs = signs * 2 - 1
        statistics = signs @ values / len(values)
        exceedances = int(np.sum(statistics >= observed - tolerance))
        p_value = float((exceedances + 1) / (simulations + 1))
        method = "FIXED_SEED_MONTE_CARLO_SIGN_RANDOMIZATION"
        samples = simulations
    return {
        "available": True,
        "pairs": len(values),
        "method": method,
        "samples": samples,
        "observed_mean_difference_r": observed,
        "one_sided_p_value": p_value,
    }


def evaluate_directional_falsification(
    routed: pd.DataFrame,
    paths: Mapping[str, Mapping[str, Any]],
    *,
    evaluated_at_utc: Any,
) -> dict[str, Any]:
    cfg = load_config()
    start = _utc(cfg["prospective_start_utc"])
    evaluated = _utc(evaluated_at_utc)
    before_start = evaluated < start
    closed = routed[routed["status"].eq("CLOSED")].copy()
    required = {
        "signal_id",
        "entry_time_utc",
        "exit_time_utc",
        "side",
        "risk_pips",
        "r",
        "extra_half_pip_stress_r",
        "path_evidence_sha256",
    }
    if not closed.empty:
        if not required.issubset(closed.columns):
            raise ValueError("Primary ledger lacks falsification fields")
        if closed["signal_id"].astype(str).duplicated().any():
            raise ValueError("Directional falsification received duplicate trades")
        closed["entry_time_utc"] = pd.to_datetime(
            closed["entry_time_utc"], utc=True
        ).dt.as_unit("ns")
        closed["exit_time_utc"] = pd.to_datetime(
            closed["exit_time_utc"], utc=True
        ).dt.as_unit("ns")
        if before_start or closed["entry_time_utc"].lt(start).any():
            raise ValueError("Pre-start primary trade entered falsification")
        if closed["exit_time_utc"].gt(evaluated).any():
            raise ValueError("Future primary close entered falsification")
        closed = closed.sort_values(["entry_time_utc", "signal_id"]).reset_index(
            drop=True
        )
    else:
        for column in required - set(closed.columns):
            closed[column] = pd.Series(dtype=float)

    missing: list[str] = []
    counterfactual_records: list[dict[str, Any]] = []
    primary_by_id = {
        str(row["signal_id"]): row for row in closed.to_dict(orient="records")
    }
    for signal_id, primary in primary_by_id.items():
        path = paths.get(signal_id)
        if path is None:
            missing.append(signal_id)
            continue
        counterfactual_records.append(
            execute_opposite_side_counterfactual(primary, path)
        )
    counterfactual = pd.DataFrame(counterfactual_records)
    if counterfactual.empty:
        counterfactual = pd.DataFrame(
            columns=["signal_id", "r", "extra_half_pip_stress_r"]
        )
    paired_ids = counterfactual["signal_id"].astype(str).tolist()
    paired_primary = (
        closed.set_index(closed["signal_id"].astype(str)).loc[paired_ids]
        if paired_ids
        else closed.iloc[:0].copy()
    )
    differences = (
        paired_primary["r"].astype(float).to_numpy()
        - counterfactual["r"].astype(float).to_numpy()
    )
    randomization_cfg = cfg["paired_randomization"]
    randomization = paired_randomization_p_value(
        differences,
        exact_maximum_pairs=int(
            randomization_cfg["exact_enumeration_maximum_pairs"]
        ),
        monte_carlo_sign_vectors=int(
            randomization_cfg["monte_carlo_sign_vectors"]
        ),
        seed=int(randomization_cfg["seed"]),
    )
    primary_metrics = payoff_metrics(closed)
    primary_stressed = payoff_metrics(closed, "extra_half_pip_stress_r")
    counterfactual_metrics = payoff_metrics(counterfactual)
    counterfactual_stressed = payoff_metrics(
        counterfactual,
        "extra_half_pip_stress_r",
    )
    deltas = {
        "profit_factor": (
            primary_metrics["profit_factor"]
            - counterfactual_metrics["profit_factor"]
        ),
        "expectancy_r": (
            primary_metrics["expectancy_r"]
            - counterfactual_metrics["expectancy_r"]
        ),
        "win_rate": (
            primary_metrics["win_rate"] - counterfactual_metrics["win_rate"]
        ),
        "net_r": primary_metrics["net_r"] - counterfactual_metrics["net_r"],
    }

    sample_gate = cfg["sample_gate"]
    directional_gate = cfg["directional_gate"]
    elapsed = evaluated >= start + pd.DateOffset(
        months=int(sample_gate["minimum_calendar_months"])
    )
    sample = len(closed) >= int(sample_gate["minimum_closed_primary_trades"])
    all_paths = len(missing) == 0 and len(counterfactual) == len(closed)
    checks = {
        "minimum_calendar_months": bool(elapsed),
        "minimum_closed_primary_trades": bool(sample),
        "all_closed_primary_paths": bool(all_paths),
        "primary_profit_factor": bool(
            primary_metrics["profit_factor"]
            >= float(directional_gate["minimum_primary_profit_factor"])
        ),
        "profit_factor_advantage": bool(
            deltas["profit_factor"]
            >= float(
                directional_gate[
                    "minimum_primary_minus_counterfactual_profit_factor"
                ]
            )
        ),
        "expectancy_advantage": bool(
            deltas["expectancy_r"]
            > float(
                directional_gate[
                    "minimum_primary_minus_counterfactual_expectancy_r"
                ]
            )
        ),
        "win_rate_advantage": bool(
            deltas["win_rate"]
            > float(
                directional_gate[
                    "minimum_primary_minus_counterfactual_win_rate"
                ]
            )
        ),
        "paired_randomization": bool(
            randomization["one_sided_p_value"] is not None
            and randomization["one_sided_p_value"]
            <= float(
                directional_gate[
                    "maximum_one_sided_paired_randomization_p_value"
                ]
            )
        ),
    }
    survived = bool(all(checks.values()))
    if before_start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif not elapsed or not sample:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    elif survived:
        status = "DIRECTIONAL_HYPOTHESIS_SURVIVES_FALSIFICATION_REVIEW"
    else:
        status = "DIRECTIONAL_HYPOTHESIS_REJECTED_NO_RETUNING"
    elapsed_weekdays = (
        len(pd.bdate_range(start.floor("D"), evaluated.floor("D")))
        if evaluated >= start
        else 0
    )
    result = {
        "schema_version": (
            "eurusd_neutral_prospective_directional_falsification_result_v1"
        ),
        "status": status,
        "prospective_start_utc": start,
        "evaluated_at_utc": evaluated,
        "historical_pnl_loaded": False,
        "frequency": {
            "closed_primary_trades": len(closed),
            "elapsed_weekdays": elapsed_weekdays,
            "trades_per_elapsed_weekday": (
                float(len(closed) / elapsed_weekdays)
                if elapsed_weekdays
                else 0.0
            ),
            "admission_gate": False,
        },
        "primary": primary_metrics,
        "primary_extra_half_pip": primary_stressed,
        "opposite_side_counterfactual": counterfactual_metrics,
        "opposite_side_extra_half_pip": counterfactual_stressed,
        "primary_minus_counterfactual": deltas,
        "paired_randomization": randomization,
        "missing_path_signal_ids": missing,
        "gate_results": checks,
        "directional_hypothesis_survived": survived,
        "research_review_allowed": survived,
        "counterfactual_changed_primary_trade": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    return _serialize(result)


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "evaluate_directional_falsification",
    "execute_opposite_side_counterfactual",
    "load_config",
    "paired_randomization_p_value",
    "verify_lock",
]
