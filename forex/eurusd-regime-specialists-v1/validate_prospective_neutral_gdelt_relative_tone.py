from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from capture_prospective_dukascopy_event_m5 import (
    decode_ticks,
    sha256_bytes,
    sha256_file,
)
from capture_prospective_neutral_gdelt_relative_tone import (
    load_and_verify_preregistration,
)
from capture_prospective_neutral_gdelt_trade_path import (
    DEFAULT_OUTPUT_ROOT as DEFAULT_PATH_ROOT,
)
from capture_prospective_neutral_gdelt_trade_path import (
    execute_ticks,
)
from eurusd_regime_specialists.asymmetric import payoff_metrics
from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    load_oracle_evidence,
)
from eurusd_regime_specialists.prospective_neutral_validation_v1_1 import (
    temporal_oracle_metrics,
)

CONFIG_PATH = (
    ROOT / "config" / "frozen_prospective_neutral_gdelt_validation_v1.json"
)
CONTRACT_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_VALIDATION_PREREG_2026_07_28.sha256.json"
)
IMPLEMENTATION_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_VALIDATION_IMPLEMENTATION_2026_07_28.sha256.json"
)
DEFAULT_LEDGER_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-gdelt-relative-tone-v1/ledger"
)
DEFAULT_ORACLE_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/oracle"
)
DEFAULT_OWNERSHIP_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/ownership"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_gdelt_validation_result_v1"


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
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(
        _serialize(value),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_contract_lock() -> dict[str, Any]:
    lock = json.loads(CONTRACT_LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_prospective_start_and_first_source_capture")
        is not True
        or lock.get(
            "locked_before_first_decision_signal_trade_and_oracle_row"
        )
        is not True
    ):
        raise RuntimeError("GDELT validation contract was not locked in time")
    for relative, expected in lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"GDELT validation contract drift: {relative}")
    for reference_name in (
        "strategy_preregistration",
        "source_and_decision_implementation",
        "path_implementation",
    ):
        reference = lock[reference_name]
        if sha256_file(ROOT / reference["path"]) != reference["sha256"]:
            raise RuntimeError(
                f"GDELT validation reference drift: {reference_name}"
            )
    return lock


def verify_implementation_lock() -> dict[str, Any]:
    verify_contract_lock()
    lock = json.loads(IMPLEMENTATION_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_first_prospective_path_outcome") is not True:
        raise RuntimeError("GDELT validator was not locked before outcomes")
    for relative, expected in lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(
                f"GDELT validation implementation drift: {relative}"
            )
    reference = lock["validation_contract"]
    if sha256_file(ROOT / reference["path"]) != reference["sha256"]:
        raise RuntimeError("GDELT validation contract lock drift")
    return lock


def _file_hash_suffix(path: Path, digest: str) -> bool:
    return path.stem.endswith(f"_{digest[:16]}")


def load_decisions(
    ledger_root: Path,
    *,
    evaluated_at_utc: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evaluated = _utc(evaluated_at_utc)
    accepted: list[dict[str, Any]] = []
    excluded_after_as_of = 0
    seen_dates: set[str] = set()
    inventory: list[tuple[str, str]] = []
    for path in sorted(ledger_root.glob("decisions/DECISION_*.json")):
        payload = path.read_bytes()
        digest = sha256_bytes(payload)
        if not _file_hash_suffix(path, digest):
            raise RuntimeError(f"Decision filename/hash drift: {path.name}")
        decision = json.loads(payload)
        required = {
            "entry_date_utc",
            "evaluated_at_utc",
            "decision_time_utc",
            "status",
            "side",
        }
        if not required.issubset(decision):
            raise ValueError(f"Decision lacks required fields: {path.name}")
        observed = _utc(decision["evaluated_at_utc"])
        decision_time = _utc(decision["decision_time_utc"])
        entry_date = str(decision["entry_date_utc"])
        expected_name = f"DECISION_{entry_date}_{digest[:16]}.json"
        if path.name != expected_name:
            raise RuntimeError(f"Decision identity drift: {path.name}")
        if observed > evaluated:
            excluded_after_as_of += 1
            continue
        if decision_time > evaluated or decision_time > observed:
            raise ValueError("Decision contains future information")
        if entry_date in seen_dates:
            raise RuntimeError(f"Multiple decisions for {entry_date}")
        status = str(decision["status"])
        side = decision.get("side")
        if status == "SIGNAL" and side not in ("LONG", "SHORT"):
            raise ValueError("Directional GDELT signal lacks a valid side")
        if status != "SIGNAL" and side is not None:
            raise ValueError("Cash GDELT decision unexpectedly has a side")
        seen_dates.add(entry_date)
        relative = path.relative_to(ledger_root).as_posix()
        accepted.append(
            {
                **decision,
                "decision_id": digest,
                "decision_sha256": digest,
                "decision_relative_path": relative,
            }
        )
        inventory.append((relative, digest))
    accepted.sort(key=lambda row: row["entry_date_utc"])
    return accepted, {
        "decision_files_available_as_of": len(accepted),
        "decision_files_excluded_after_as_of": excluded_after_as_of,
        "decision_inventory": inventory,
    }


def _validate_raw_snapshot(
    output_root: Path,
    raw: Mapping[str, Any],
    *,
    evaluated_at_utc: pd.Timestamp,
) -> pd.DataFrame:
    raw_path = output_root / str(raw["raw_relative_path"])
    metadata_path = output_root / str(raw["metadata_relative_path"])
    if sha256_file(raw_path) != str(raw["raw_sha256"]):
        raise RuntimeError("GDELT raw path tick evidence drift")
    if sha256_file(metadata_path) != str(raw["metadata_sha256"]):
        raise RuntimeError("GDELT raw path metadata drift")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if str(metadata["raw_sha256"]) != str(raw["raw_sha256"]):
        raise RuntimeError("GDELT raw metadata does not bind its archive")
    observed = _utc(raw["observed_at_utc"])
    metadata_observed = _utc(metadata["observed_at_utc"])
    if observed != metadata_observed or observed > evaluated_at_utc:
        raise ValueError("GDELT raw path contains future observation time")
    hour = _utc(raw["hour_utc"])
    if hour != _utc(metadata["hour_utc"]):
        raise RuntimeError("GDELT raw path hour metadata drift")
    return decode_ticks(raw_path.read_bytes(), "EURUSD", hour)


def load_paths(
    output_root: Path,
    decisions: list[dict[str, Any]],
    strategy_config: dict[str, Any],
    *,
    evaluated_at_utc: Any,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    evaluated = _utc(evaluated_at_utc)
    decision_by_id = {
        str(decision["decision_id"]): decision for decision in decisions
    }
    accepted: dict[str, dict[str, Any]] = {}
    excluded_after_as_of = 0
    replayed = 0
    inventory: list[tuple[str, str]] = []
    for path in sorted(output_root.glob("manifests/PATH_*.json")):
        payload = path.read_bytes()
        digest = sha256_bytes(payload)
        if not _file_hash_suffix(path, digest):
            raise RuntimeError(f"Path filename/hash drift: {path.name}")
        manifest = json.loads(payload)
        required = {
            "decision_id",
            "decision_sha256",
            "decision_relative_path",
            "captured_at_utc",
            "execution",
            "raw_snapshots",
        }
        if not required.issubset(manifest):
            raise ValueError(f"Path manifest lacks fields: {path.name}")
        decision_id = str(manifest["decision_id"])
        expected_name = f"PATH_{decision_id}_{digest[:16]}.json"
        if path.name != expected_name:
            raise RuntimeError(f"Path manifest identity drift: {path.name}")
        captured = _utc(manifest["captured_at_utc"])
        if captured > evaluated:
            excluded_after_as_of += 1
            continue
        decision = decision_by_id.get(decision_id)
        if decision is None:
            raise RuntimeError("Path references no accepted decision")
        if (
            str(manifest["decision_sha256"]) != decision_id
            or str(manifest["decision_relative_path"])
            != str(decision["decision_relative_path"])
        ):
            raise RuntimeError("Path-to-decision binding drift")
        if decision_id in accepted:
            raise RuntimeError("Multiple GDELT paths for one decision")
        execution = manifest["execution"]
        if str(manifest.get("status")) != str(execution.get("status")):
            raise RuntimeError("Path manifest and execution status disagree")
        raw_snapshots = list(manifest["raw_snapshots"])
        if raw_snapshots:
            frames = [
                _validate_raw_snapshot(
                    output_root,
                    raw,
                    evaluated_at_utc=evaluated,
                )
                for raw in raw_snapshots
            ]
            replay = execute_ticks(
                decision,
                pd.concat(frames, ignore_index=True),
                strategy_config,
            )
            if _canonical(replay) != _canonical(execution):
                raise RuntimeError("Recorded GDELT execution failed tick replay")
            replayed += 1
        elif str(execution.get("status")) == "CLOSED":
            raise RuntimeError("Closed GDELT path lacks raw tick evidence")
        relative = path.relative_to(output_root).as_posix()
        accepted[decision_id] = {
            **manifest,
            "manifest_relative_path": relative,
            "manifest_sha256": digest,
            "tick_replay_verified": bool(raw_snapshots),
        }
        inventory.append((relative, digest))
    return accepted, {
        "path_manifests_available_as_of": len(accepted),
        "path_manifests_excluded_after_as_of": excluded_after_as_of,
        "path_manifests_tick_replayed": replayed,
        "path_inventory": inventory,
    }


def _closed_ledger(
    decisions: list[dict[str, Any]],
    paths: Mapping[str, Mapping[str, Any]],
    strategy_config: Mapping[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    risk_pips = float(strategy_config["risk"]["fixed_stop_pips"])
    pip_value = 0.1
    for decision in decisions:
        if decision["status"] != "SIGNAL":
            continue
        decision_id = str(decision["decision_id"])
        path = paths.get(decision_id)
        if path is None:
            continue
        execution = path["execution"]
        if execution["status"] != "CLOSED":
            continue
        if not path.get("tick_replay_verified"):
            raise RuntimeError("Closed path entered ledger without tick replay")
        rows.append(
            {
                "signal_id": decision_id,
                "status": "CLOSED",
                "entry_time_utc": _utc(execution["entry_time_utc"]),
                "exit_time_utc": _utc(execution["exit_time_utc"]),
                "side": str(execution["side"]),
                "exit_reason": str(execution["exit_reason"]),
                "r": float(execution["r"]),
                "extra_half_pip_stress_r": float(
                    execution["extra_half_pip_stress_r"]
                ),
                "risk_pips": risk_pips,
                "fixed_0p01_lot_usd": float(execution["r"])
                * risk_pips
                * pip_value,
                "path_evidence_sha256": str(path["manifest_sha256"]),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "signal_id",
                "status",
                "entry_time_utc",
                "exit_time_utc",
                "side",
                "exit_reason",
                "r",
                "extra_half_pip_stress_r",
                "risk_pips",
                "fixed_0p01_lot_usd",
                "path_evidence_sha256",
            ]
        )
    frame = pd.DataFrame(rows).sort_values(
        ["exit_time_utc", "signal_id"]
    ).reset_index(drop=True)
    if frame["signal_id"].duplicated().any():
        raise RuntimeError("Duplicate closed GDELT trade")
    return frame


def _monthly_metrics(closed: pd.DataFrame) -> dict[str, Any]:
    if closed.empty:
        return {
            "active_months": 0,
            "positive_active_months": 0,
            "positive_active_month_rate": 0.0,
            "largest_month_share_of_positive_profit": 0.0,
            "months": {},
        }
    working = closed.copy()
    working["month"] = working["exit_time_utc"].dt.strftime("%Y-%m")
    metrics = {
        str(month): payoff_metrics(group)
        for month, group in working.groupby("month", sort=True)
    }
    positive = [
        float(value["net_r"])
        for value in metrics.values()
        if float(value["net_r"]) > 0.0
    ]
    positive_total = sum(positive)
    concentration = (
        max(positive) / positive_total
        if positive_total > 0.0
        else 1.0
    )
    return {
        "active_months": len(metrics),
        "positive_active_months": len(positive),
        "positive_active_month_rate": len(positive) / len(metrics),
        "largest_month_share_of_positive_profit": concentration,
        "months": metrics,
    }


def _remove_top_winners(closed: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    winners = closed[closed["r"].gt(0.0)].sort_values(
        ["r", "exit_time_utc", "signal_id"],
        ascending=[False, True, True],
    )
    remove_count = math.ceil(len(winners) * 0.05) if len(winners) else 0
    if not remove_count:
        return closed.copy(), 0
    removed_ids = set(winners.head(remove_count)["signal_id"].astype(str))
    return (
        closed[~closed["signal_id"].astype(str).isin(removed_ids)].copy(),
        remove_count,
    )


def _monte_carlo(
    values: np.ndarray,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    block = int(config["block_length_trades"])
    horizon = int(config["horizon_trades"])
    simulations = int(config["simulations"])
    if len(values) < block:
        return {
            "available": False,
            "reason": "INSUFFICIENT_TRADES_FOR_FROZEN_BLOCK_LENGTH",
            "trades": len(values),
        }
    rng = np.random.default_rng(int(config["seed"]))
    drawdowns = np.empty(simulations, dtype=float)
    blocks_needed = math.ceil(horizon / block)
    offsets = np.arange(block)
    for index in range(simulations):
        starts = rng.integers(0, len(values), size=blocks_needed)
        sample = np.concatenate(
            [values[(start + offsets) % len(values)] for start in starts]
        )[:horizon]
        equity = np.concatenate(([0.0], np.cumsum(sample)))
        drawdowns[index] = float(
            np.max(np.maximum.accumulate(equity) - equity)
        )
    hard = float(config["hard_drawdown_r"])
    return {
        "available": True,
        "method": str(config["method"]),
        "seed": int(config["seed"]),
        "simulations": simulations,
        "block_length_trades": block,
        "horizon_trades": horizon,
        "hard_drawdown_r": hard,
        "hard_drawdown_breach_probability": float(
            np.mean(drawdowns >= hard)
        ),
        "maximum_drawdown_r_quantiles": {
            "p50": float(np.quantile(drawdowns, 0.50)),
            "p90": float(np.quantile(drawdowns, 0.90)),
            "p95": float(np.quantile(drawdowns, 0.95)),
            "p99": float(np.quantile(drawdowns, 0.99)),
        },
    }


def _same_day_oracle_metrics(
    closed: pd.DataFrame,
    oracle: pd.DataFrame,
    completed_dates: set[str],
) -> dict[str, Any]:
    if closed.empty:
        return {
            "all_closed_trade_oracle_dates_available": False,
            "missing_oracle_dates": [],
            "matches": 0,
            "precision": None,
        }
    entries = closed.copy()
    entries["oracle_date"] = entries["entry_time_utc"].dt.strftime("%Y-%m-%d")
    completed = {str(day) for day in completed_dates}
    missing = sorted(set(entries["oracle_date"]) - completed)
    if oracle.empty:
        neutral = pd.DataFrame(columns=["oracle_date", "side"])
    else:
        required = {"oracle_date", "side", "regime"}
        if not required.issubset(oracle.columns):
            raise ValueError("Oracle lacks same-day validation fields")
        neutral = oracle[oracle["regime"].eq("NEUTRAL")].copy()
        neutral["oracle_date"] = pd.to_datetime(
            neutral["oracle_date"], utc=True
        ).dt.strftime("%Y-%m-%d")
    pairs = set(
        zip(
            neutral["oracle_date"].astype(str),
            neutral["side"].astype(str),
            strict=False,
        )
    )
    matches = sum(
        (str(row.oracle_date), str(row.side)) in pairs
        for row in entries[["oracle_date", "side"]].itertuples(index=False)
    )
    complete = not missing
    return {
        "all_closed_trade_oracle_dates_available": complete,
        "missing_oracle_dates": missing,
        "matches": int(matches),
        "precision": float(matches / len(entries)) if complete else None,
    }


def evaluate_validation(
    decisions: list[dict[str, Any]],
    paths: Mapping[str, Mapping[str, Any]],
    oracle: pd.DataFrame,
    completed_oracle_dates: set[str],
    strategy_config: Mapping[str, Any],
    *,
    evaluated_at_utc: Any,
) -> dict[str, Any]:
    config = load_config()
    evaluated = _utc(evaluated_at_utc)
    start = _utc(config["prospective_start_utc"])
    if any(
        pd.Timestamp(decision["entry_date_utc"], tz="UTC") < start.floor("D")
        for decision in decisions
    ):
        raise ValueError("Pre-start decision entered prospective validation")
    closed = _closed_ledger(decisions, paths, strategy_config)
    if (
        not closed.empty
        and closed["exit_time_utc"].gt(evaluated).any()
    ):
        raise ValueError("Future close entered prospective validation")

    overall = payoff_metrics(closed)
    stressed = payoff_metrics(closed, "extra_half_pip_stress_r")
    sides = {
        side: payoff_metrics(closed[closed["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    top_removed_frame, removed_winners = _remove_top_winners(closed)
    top_removed = payoff_metrics(top_removed_frame)
    monthly = _monthly_metrics(closed)
    monte_carlo = _monte_carlo(
        closed["extra_half_pip_stress_r"].to_numpy(dtype=float),
        config["monte_carlo"],
    )
    same_day = _same_day_oracle_metrics(
        closed,
        oracle,
        completed_oracle_dates,
    )
    temporal = temporal_oracle_metrics(
        closed,
        oracle,
        completed_oracle_dates,
        windows_minutes=config["oracle_gate"][
            "reported_temporal_windows_minutes"
        ],
        grid_minutes=int(
            config["oracle_gate"]["uniform_entry_grid_minutes"]
        ),
    )

    decision_counts = Counter(str(row["status"]) for row in decisions)
    path_counts = Counter(
        str(path["execution"]["status"]) for path in paths.values()
    )
    signals = int(decision_counts["SIGNAL"])
    missing_paths = sum(
        str(row["decision_id"]) not in paths
        for row in decisions
        if row["status"] == "SIGNAL"
    )
    elapsed_weekdays = (
        len(pd.bdate_range(start.floor("D"), evaluated.floor("D")))
        if evaluated >= start
        else 0
    )
    frequency = {
        "eligible_decisions_recorded": len(decisions),
        "signals": signals,
        "cash_decisions": len(decisions) - signals,
        "closed_trades": len(closed),
        "active_trade_days": (
            int(closed["entry_time_utc"].dt.floor("D").nunique())
            if len(closed)
            else 0
        ),
        "elapsed_weekdays": elapsed_weekdays,
        "trades_per_elapsed_weekday": (
            float(len(closed) / elapsed_weekdays) if elapsed_weekdays else 0.0
        ),
        "admission_gate": False,
    }

    sample_gate = config["sample_gate"]
    economic_gate = config["economic_gate"]
    oracle_gate = config["oracle_gate"]
    mc_gate = config["monte_carlo"]
    elapsed = evaluated >= start + pd.DateOffset(
        months=int(sample_gate["minimum_calendar_months"])
    )
    sample_checks = {
        "minimum_calendar_months": bool(elapsed),
        "minimum_closed_trades": bool(
            len(closed) >= int(sample_gate["minimum_closed_trades"])
        ),
        "minimum_each_side_trades": bool(
            all(
                sides[side]["trades"]
                >= int(sample_gate["minimum_each_side_trades"])
                for side in ("LONG", "SHORT")
            )
        ),
        "all_closed_trade_paths": bool(
            len(closed)
            == sum(
                str(path["execution"]["status"]) == "CLOSED"
                and bool(path.get("tick_replay_verified"))
                for path in paths.values()
            )
        ),
    }
    economic_checks = {
        "win_rate": bool(
            float(economic_gate["minimum_win_rate"])
            <= overall["win_rate"]
            <= float(economic_gate["maximum_win_rate"])
        ),
        "realized_payoff_ratio": bool(
            float(economic_gate["minimum_realized_payoff_ratio"])
            <= overall["realized_payoff_ratio"]
            <= float(economic_gate["maximum_realized_payoff_ratio"])
        ),
        "profit_factor": bool(
            overall["profit_factor"]
            >= float(economic_gate["minimum_profit_factor"])
        ),
        "positive_expectancy": bool(
            overall["expectancy_r"]
            > float(economic_gate["minimum_expectancy_r"])
        ),
        "both_side_profit_factors": bool(
            all(
                sides[side]["profit_factor"]
                >= float(economic_gate["minimum_each_side_profit_factor"])
                for side in ("LONG", "SHORT")
            )
        ),
        "extra_half_pip_profit_factor": bool(
            stressed["profit_factor"]
            >= float(
                economic_gate["minimum_extra_half_pip_profit_factor"]
            )
        ),
        "maximum_closed_trade_drawdown": bool(
            overall["max_drawdown_r"]
            <= float(economic_gate["maximum_closed_trade_drawdown_r"])
            and len(closed)
        ),
        "top_5pct_winners_removed": bool(
            top_removed["profit_factor"]
            >= float(
                economic_gate[
                    "minimum_top_5pct_winners_removed_profit_factor"
                ]
            )
        ),
        "positive_active_month_rate": bool(
            monthly["positive_active_month_rate"]
            >= float(economic_gate["minimum_positive_active_month_rate"])
        ),
        "monthly_profit_concentration": bool(
            monthly["largest_month_share_of_positive_profit"]
            <= float(
                economic_gate[
                    "maximum_largest_month_share_of_positive_profit"
                ]
            )
            and len(closed)
        ),
        "monte_carlo_hard_drawdown": bool(
            monte_carlo["available"]
            and monte_carlo["hard_drawdown_breach_probability"]
            <= float(mc_gate["maximum_breach_probability"])
        ),
    }
    primary = temporal["windows"][
        f"within_{int(oracle_gate['primary_temporal_window_minutes'])}_minutes"
    ]
    same_day_checks = {
        "all_closed_trade_oracle_dates": bool(
            same_day["all_closed_trade_oracle_dates_available"]
            and len(closed)
        ),
        "same_day_same_side_precision": bool(
            same_day["precision"] is not None
            and same_day["precision"]
            >= float(
                oracle_gate["minimum_same_day_same_side_precision"]
            )
        ),
    }
    temporal_checks = {
        "one_strategy_trade_per_utc_date": bool(
            temporal["one_strategy_trade_per_utc_date"]
        ),
        "primary_temporal_precision": bool(
            primary["precision"] is not None
            and primary["precision"]
            >= float(oracle_gate["minimum_primary_temporal_precision"])
        ),
        "primary_temporal_lift": bool(
            primary["precision_lift_over_uniform_time_and_side"] is not None
            and primary["precision_lift_over_uniform_time_and_side"]
            > float(
                oracle_gate[
                    "minimum_primary_lift_over_uniform_time_and_side"
                ]
            )
        ),
        "primary_temporal_uniform_null_test": bool(
            primary[
                "uniform_time_and_side_poisson_binomial_tail_p_value"
            ]
            is not None
            and primary[
                "uniform_time_and_side_poisson_binomial_tail_p_value"
            ]
            <= float(
                oracle_gate[
                    "maximum_primary_uniform_time_and_side_tail_p_value"
                ]
            )
        ),
    }
    sample_passed = bool(all(sample_checks.values()))
    economic_passed = bool(
        sample_passed and all(economic_checks.values())
    )
    same_day_passed = bool(
        economic_passed and all(same_day_checks.values())
    )
    temporal_passed = bool(
        same_day_passed and all(temporal_checks.values())
    )
    if evaluated < start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif not sample_passed:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    elif temporal_passed:
        status = "INDEPENDENT_FULL_ORACLE_IMITATION_REVIEW_REQUIRED"
    elif same_day_passed:
        status = "INDEPENDENT_SAME_DAY_REGIME_REVIEW_REQUIRED"
    elif economic_passed:
        status = "INDEPENDENT_PROFITABILITY_REVIEW_REQUIRED"
    else:
        status = "REJECTED_WITHOUT_RETUNING"

    return _serialize(
        {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "prospective_start_utc": start,
            "evaluated_at_utc": evaluated,
            "frequency": frequency,
            "reason_census": {
                "decision_statuses": dict(sorted(decision_counts.items())),
                "path_statuses": dict(sorted(path_counts.items())),
                "signals_without_path_manifest": int(missing_paths),
            },
            "overall": overall,
            "by_side": sides,
            "extra_half_pip_round_trip": stressed,
            "top_5pct_winners_removed": {
                **top_removed,
                "removed_winners": removed_winners,
            },
            "monthly": monthly,
            "monte_carlo": monte_carlo,
            "same_day_oracle_resemblance": same_day,
            "temporal_oracle_resemblance": temporal,
            "sample_gate_results": sample_checks,
            "economic_and_robustness_gate_results": economic_checks,
            "same_day_regime_gate_results": same_day_checks,
            "temporal_oracle_gate_results": temporal_checks,
            "sample_gates_passed": sample_passed,
            "economic_and_robustness_gates_passed": economic_passed,
            "same_day_regime_resemblance_gates_passed": same_day_passed,
            "full_temporal_oracle_imitation_gates_passed": temporal_passed,
            "profitability_review_allowed": economic_passed,
            "same_day_regime_review_allowed": same_day_passed,
            "oracle_imitation_claim_allowed": temporal_passed,
            "research_review_allowed": economic_passed,
            "controlled_demo_ready": False,
            "historical_eurusd_pnl_loaded": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )


def _inventory_sha256(
    decisions: Mapping[str, Any],
    paths: Mapping[str, Any],
) -> str:
    payload = json.dumps(
        {
            "decisions": decisions["decision_inventory"],
            "paths": paths["path_inventory"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_validation_status(
    *,
    evaluated_at_utc: Any,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    path_root: Path = DEFAULT_PATH_ROOT,
    oracle_root: Path = DEFAULT_ORACLE_ROOT,
    ownership_root: Path = DEFAULT_OWNERSHIP_ROOT,
) -> dict[str, Any]:
    implementation_lock = verify_implementation_lock()
    strategy_config, _ = load_and_verify_preregistration()
    evaluated = _utc(evaluated_at_utc)
    decisions, decision_census = load_decisions(
        ledger_root,
        evaluated_at_utc=evaluated,
    )
    paths, path_census = load_paths(
        path_root,
        decisions,
        strategy_config,
        evaluated_at_utc=evaluated,
    )
    oracle, completed_dates, oracle_census = load_oracle_evidence(
        oracle_root,
        ownership_root,
        evaluated_at_utc=evaluated,
    )
    validation = evaluate_validation(
        decisions,
        paths,
        oracle,
        completed_dates,
        strategy_config,
        evaluated_at_utc=evaluated,
    )
    return _serialize(
        {
            "schema_version": (
                "eurusd_neutral_prospective_gdelt_validation_status_v1"
            ),
            "evaluated_at_utc": evaluated,
            "status": validation["status"],
            "validation": validation,
            "evidence_census": {
                **{
                    key: value
                    for key, value in decision_census.items()
                    if key != "decision_inventory"
                },
                **{
                    key: value
                    for key, value in path_census.items()
                    if key != "path_inventory"
                },
                **oracle_census,
            },
            "evidence_inventory_sha256": _inventory_sha256(
                decision_census,
                path_census,
            ),
            "validation_implementation_lock_sha256": sha256_file(
                IMPLEMENTATION_LOCK_PATH
            ),
            "validation_implementation_locked_at_utc": implementation_lock[
                "locked_at_utc"
            ],
            "historical_eurusd_pnl_loaded": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    parser.add_argument("--as-of")
    parser.add_argument(
        "--ledger-root",
        type=Path,
        default=DEFAULT_LEDGER_ROOT,
    )
    parser.add_argument(
        "--path-root",
        type=Path,
        default=DEFAULT_PATH_ROOT,
    )
    parser.add_argument(
        "--oracle-root",
        type=Path,
        default=DEFAULT_ORACLE_ROOT,
    )
    parser.add_argument(
        "--ownership-root",
        type=Path,
        default=DEFAULT_OWNERSHIP_ROOT,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    evaluated = (
        pd.Timestamp.now(tz="UTC")
        if args.as_of is None
        else _utc(args.as_of)
    )
    result = build_validation_status(
        evaluated_at_utc=evaluated,
        ledger_root=args.ledger_root,
        path_root=args.path_root,
        oracle_root=args.oracle_root,
        ownership_root=args.ownership_root,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
