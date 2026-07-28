from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .prospective_neutral_campaign_orchestration import (
    verify_lock as verify_campaign_lock,
)
from .research import PACKAGE_ROOT, PIP, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_prospective_neutral_validation_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_VALIDATION_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Prospective validation contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Prospective validation lock mismatch: {relative}")
        checked[relative] = actual
    cfg = load_config()
    campaign = cfg["campaign_orchestration_contract"]
    if sha256_file(PACKAGE_ROOT / campaign["path"]) != campaign["sha256"]:
        raise RuntimeError("Prospective validation campaign contract drift")
    verify_campaign_lock()
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
            raise ValueError("Trade path timestamps must be timezone-aware")
        result.index = result.index.tz_convert("UTC").as_unit("ns")
        result.index.name = "timestamp_utc"
    else:
        raise ValueError("Trade path requires UTC timestamps")
    required = {
        f"{side}_{field}"
        for side in ("bid", "ask")
        for field in ("open", "high", "low", "close")
    }
    if not required.issubset(result.columns):
        raise ValueError("Trade path lacks executable bid/ask OHLC")
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise ValueError("Trade path timestamps must be unique and ordered")
    values = result[list(required)].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Trade path contains non-finite prices")
    return result


def _effective_prices(
    row: pd.Series,
    spread_floor: float,
) -> dict[str, float]:
    return {
        "bid_high": min(
            float(row["bid_high"]),
            float(row["ask_high"]) - spread_floor,
        ),
        "bid_low": min(
            float(row["bid_low"]),
            float(row["ask_low"]) - spread_floor,
        ),
        "ask_high": max(
            float(row["ask_high"]),
            float(row["bid_high"]) + spread_floor,
        ),
        "ask_low": max(
            float(row["ask_low"]),
            float(row["bid_low"]) + spread_floor,
        ),
    }


def _r_mark(
    side: str,
    price: float,
    entry_price: float,
    risk_distance: float,
) -> float:
    signed = price - entry_price if side == "LONG" else entry_price - price
    return float(signed / risk_distance)


def trade_path_marks(
    trade: Mapping[str, Any],
    path: Mapping[str, Any],
    *,
    minimum_spread_pips: float,
    adverse_slippage_pips_per_side: float,
) -> dict[str, Any]:
    """Return conservative, sequence-ordered executable floating-equity marks."""
    side = str(trade["side"])
    if side not in {"LONG", "SHORT"}:
        raise ValueError("Floating validation requires a directional trade")
    entry = _utc(trade["entry_time_utc"])
    exit_time = _utc(trade["exit_time_utc"])
    if _utc(path["entry_time_utc"]) != entry:
        raise RuntimeError("Trade path entry does not match its closed trade")
    expected_hash = str(trade["path_evidence_sha256"]).lower()
    if len(expected_hash) != 64 or str(path["path_evidence_sha256"]).lower() != (
        expected_hash
    ):
        raise RuntimeError("Trade path evidence hash does not match its trade")
    entry_price = float(trade["entry_price"])
    risk_distance = float(trade["risk_distance"])
    if not math.isfinite(entry_price) or risk_distance <= 0:
        raise ValueError("Closed trade has invalid entry or risk")
    outcome_r = float(trade["r"])
    reason = str(trade["exit_reason"])
    if reason not in {"STOP", "TARGET", "TIME_12H"}:
        raise ValueError("Closed trade has an unknown exit reason")

    frame = _normalize_path(path["frame"])
    deadline = _utc(path["deadline_utc"])
    if deadline <= entry or exit_time > deadline:
        raise RuntimeError("Closed trade exit is outside its path")
    relevant = frame[(frame.index >= entry) & (frame.index < deadline)]
    if reason in {"STOP", "TARGET"}:
        relevant = relevant[relevant.index <= exit_time]
        if exit_time not in relevant.index:
            raise RuntimeError("Price-triggered exit is absent from its path")
    if relevant.empty:
        raise RuntimeError("Closed trade path has no decision bars")

    spread_floor = float(minimum_spread_pips) * PIP
    slippage = float(adverse_slippage_pips_per_side) * PIP
    ordered_marks: list[float] = [0.0]
    bar_marks: list[dict[str, Any]] = []
    for timestamp, row in relevant.iterrows():
        prices = _effective_prices(row, spread_floor)
        if side == "LONG":
            worst_price = prices["bid_low"] - slippage
            best_price = prices["bid_high"] - slippage
        else:
            worst_price = prices["ask_high"] + slippage
            best_price = prices["ask_low"] + slippage
        worst_r = _r_mark(side, worst_price, entry_price, risk_distance)
        best_r = _r_mark(side, best_price, entry_price, risk_distance)
        is_trigger_exit = timestamp == exit_time and reason in {"STOP", "TARGET"}
        is_time_exit_bar = timestamp == relevant.index[-1] and reason == "TIME_12H"
        if is_trigger_exit and reason == "STOP":
            sequence = [outcome_r]
        elif is_trigger_exit:
            # The stop was not touched; assume the adverse extreme preceded
            # the target fill and ignore any post-fill bar movement.
            sequence = [worst_r, outcome_r]
        elif is_time_exit_bar:
            # For an unresolved intrabar order, high-before-low maximizes
            # drawdown and is therefore the fail-closed ordering.
            sequence = [best_r, worst_r, outcome_r]
        else:
            sequence = [best_r, worst_r]
        ordered_marks.extend(sequence)
        bar_marks.append(
            {
                "timestamp_utc": timestamp,
                "worst_r": worst_r,
                "best_r": best_r,
                "ordered_marks_r": sequence,
            }
        )
        if is_trigger_exit:
            break
    if not math.isclose(ordered_marks[-1], outcome_r, abs_tol=1e-10):
        raise RuntimeError("Floating path did not terminate at realized outcome")
    return {
        "signal_id": str(trade["signal_id"]),
        "ordered_marks_r": ordered_marks,
        "maximum_adverse_excursion_r": float(min(ordered_marks)),
        "maximum_favorable_excursion_r": float(max(ordered_marks)),
        "bars_evaluated": len(bar_marks),
        "bar_marks": bar_marks,
    }


def _portfolio_floating_drawdown(
    closed: pd.DataFrame,
    paths: Mapping[str, Mapping[str, Any]],
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    robustness = cfg["robustness_gate"]
    execution = cfg["execution_reference"]
    pip_value = float(robustness["pip_value_usd_at_fixed_lots"])
    balance = float(robustness["starting_balance_usd"])
    base_equity = 0.0
    stress_equity = 0.0
    base_peak = 0.0
    stress_peak = 0.0
    base_drawdown = 0.0
    stress_drawdown = 0.0
    missing: list[str] = []
    trade_excursions: list[dict[str, Any]] = []
    for trade in closed.sort_values(["entry_time_utc", "signal_id"]).to_dict(
        orient="records"
    ):
        signal_id = str(trade["signal_id"])
        path = paths.get(signal_id)
        if path is None:
            missing.append(signal_id)
            continue
        marks = trade_path_marks(
            trade,
            path,
            minimum_spread_pips=float(execution["minimum_retail_spread_pips"]),
            adverse_slippage_pips_per_side=float(
                execution["adverse_slippage_pips_per_side"]
            ),
        )
        risk_usd = float(trade["risk_pips"]) * pip_value
        if risk_usd <= 0:
            raise ValueError("Closed trade has non-positive fixed-lot risk")
        base_outcome_usd = float(trade["r"]) * risk_usd
        stress_outcome_usd = (
            float(trade["extra_half_pip_stress_r"]) * risk_usd
        )
        recorded_usd = float(trade["fixed_0p01_lot_usd"])
        if not math.isclose(base_outcome_usd, recorded_usd, abs_tol=1e-8):
            raise RuntimeError("Fixed-lot P&L does not reconcile with R outcome")
        stress_penalty_r = float(trade["r"]) - float(
            trade["extra_half_pip_stress_r"]
        )
        for mark_r in marks["ordered_marks_r"]:
            base_mark = base_equity + float(mark_r) * risk_usd
            base_peak = max(base_peak, base_mark)
            base_drawdown = max(base_drawdown, base_peak - base_mark)
            stress_mark = (
                stress_equity + (float(mark_r) - stress_penalty_r) * risk_usd
            )
            stress_peak = max(stress_peak, stress_mark)
            stress_drawdown = max(
                stress_drawdown,
                stress_peak - stress_mark,
            )
        base_equity += base_outcome_usd
        stress_equity += stress_outcome_usd
        base_peak = max(base_peak, base_equity)
        stress_peak = max(stress_peak, stress_equity)
        trade_excursions.append(
            {
                "signal_id": signal_id,
                "risk_usd": risk_usd,
                "maximum_adverse_excursion_r": marks[
                    "maximum_adverse_excursion_r"
                ],
                "maximum_favorable_excursion_r": marks[
                    "maximum_favorable_excursion_r"
                ],
                "bars_evaluated": marks["bars_evaluated"],
            }
        )
    return {
        "all_closed_trade_paths_available": len(missing) == 0,
        "missing_signal_ids": missing,
        "base_maximum_floating_drawdown_usd": base_drawdown,
        "base_maximum_floating_drawdown_pct": 100.0 * base_drawdown / balance,
        "stressed_maximum_floating_drawdown_usd": stress_drawdown,
        "stressed_maximum_floating_drawdown_pct": (
            100.0 * stress_drawdown / balance
        ),
        "base_terminal_net_usd": base_equity,
        "stressed_terminal_net_usd": stress_equity,
        "trade_excursions": trade_excursions,
    }


def poisson_binomial_tail_probability(
    probabilities: Sequence[float],
    observed_successes: int,
) -> float:
    if observed_successes <= 0:
        return 1.0
    distribution = np.asarray([1.0], dtype=float)
    for probability in probabilities:
        p = float(probability)
        if not 0.0 <= p <= 1.0:
            raise ValueError("Poisson-binomial probabilities must be in [0, 1]")
        updated = np.zeros(len(distribution) + 1, dtype=float)
        updated[:-1] += distribution * (1.0 - p)
        updated[1:] += distribution * p
        distribution = updated
    if observed_successes >= len(distribution):
        return 0.0
    return float(distribution[observed_successes:].sum())


def _oracle_metrics(
    closed: pd.DataFrame,
    oracle: pd.DataFrame,
    completed_dates: set[str],
    windows: Sequence[int],
) -> dict[str, Any]:
    by_date: dict[str, pd.DataFrame] = {}
    if not oracle.empty:
        required = {"oracle_date", "side", "regime", "entry_time_utc"}
        if not required.issubset(oracle.columns):
            raise ValueError("Oracle evidence lacks validation fields")
        neutral = oracle[oracle["regime"].eq("NEUTRAL")].copy()
        neutral["entry_time_utc"] = pd.to_datetime(
            neutral["entry_time_utc"], utc=True
        ).dt.as_unit("ns")
        by_date = {
            str(day): frame.copy()
            for day, frame in neutral.groupby(neutral["oracle_date"].astype(str))
        }
    matches: list[bool] = []
    probabilities: list[float] = []
    timing_hits = {int(window): 0 for window in windows}
    missing_dates: list[str] = []
    for trade in closed.to_dict(orient="records"):
        entry = _utc(trade["entry_time_utc"])
        day = entry.strftime("%Y-%m-%d")
        if day not in completed_dates:
            missing_dates.append(day)
            continue
        labels = by_date.get(day, pd.DataFrame())
        sides = (
            set(labels["side"].astype(str))
            if not labels.empty
            else set()
        )
        side = str(trade["side"])
        matched = side in sides
        matches.append(matched)
        probabilities.append(len(sides) / 2.0)
        if matched:
            same_side = labels[labels["side"].astype(str).eq(side)]
            distances = (
                same_side["entry_time_utc"].sub(entry).abs().dt.total_seconds()
                / 60.0
            )
            nearest = float(distances.min())
            for window in timing_hits:
                if nearest <= window:
                    timing_hits[window] += 1
    complete = len(missing_dates) == 0 and len(matches) == len(closed)
    precision = float(np.mean(matches)) if complete and matches else None
    baseline = (
        float(np.mean(probabilities)) if complete and probabilities else None
    )
    lift = (
        float(precision - baseline)
        if precision is not None and baseline is not None
        else None
    )
    p_value = (
        poisson_binomial_tail_probability(probabilities, int(sum(matches)))
        if complete and matches
        else None
    )
    return {
        "all_closed_trade_oracle_dates_available": complete,
        "missing_oracle_dates": sorted(set(missing_dates)),
        "same_day_same_side_precision": precision,
        "random_side_expected_precision": baseline,
        "precision_lift_over_random_side": lift,
        "random_side_poisson_binomial_tail_p_value": p_value,
        "timing_precision": {
            f"within_{window}_minutes": (
                float(count / len(closed)) if len(closed) else None
            )
            for window, count in timing_hits.items()
        },
    }


def _monthly_metrics(closed: pd.DataFrame) -> dict[str, Any]:
    if closed.empty:
        return {
            "active_months": 0,
            "positive_active_months": 0,
            "positive_active_month_rate": 0.0,
            "largest_month_share_of_positive_profit": 0.0,
            "months": {},
        }
    month_keys = closed["exit_time_utc"].dt.strftime("%Y-%m")
    monthly = {
        str(month): payoff_metrics(frame)
        for month, frame in closed.groupby(month_keys)
    }
    positive = [block["net_r"] for block in monthly.values() if block["net_r"] > 0]
    positive_total = float(sum(positive))
    largest_share = (
        float(max(positive) / positive_total) if positive_total > 0 else 0.0
    )
    return {
        "active_months": len(monthly),
        "positive_active_months": len(positive),
        "positive_active_month_rate": float(len(positive) / len(monthly)),
        "largest_month_share_of_positive_profit": largest_share,
        "months": monthly,
    }


def _monte_carlo(
    stressed_pnl_usd: np.ndarray,
    cfg: Mapping[str, Any],
    starting_balance_usd: float,
) -> dict[str, Any]:
    if len(stressed_pnl_usd) == 0:
        return {
            "available": False,
            "simulations": 0,
            "hard_drawdown_breach_probability": None,
        }
    simulations = int(cfg["simulations"])
    block = int(cfg["block_length_trades"])
    horizon = int(cfg["horizon_trades"])
    if simulations <= 0 or block <= 0 or horizon <= 0:
        raise ValueError("Monte Carlo dimensions must be positive")
    rng = np.random.default_rng(int(cfg["seed"]))
    blocks = math.ceil(horizon / block)
    starts = rng.integers(0, len(stressed_pnl_usd), size=(simulations, blocks))
    offsets = np.arange(block, dtype=int)
    indices = (starts[..., None] + offsets) % len(stressed_pnl_usd)
    indices = indices.reshape(simulations, -1)[:, :horizon]
    samples = stressed_pnl_usd[indices]
    equity = np.cumsum(samples, axis=1)
    equity = np.concatenate(
        [np.zeros((simulations, 1), dtype=float), equity],
        axis=1,
    )
    peaks = np.maximum.accumulate(equity, axis=1)
    drawdowns = np.max(peaks - equity, axis=1)
    hard_usd = (
        float(cfg["hard_drawdown_pct"]) / 100.0 * starting_balance_usd
    )
    return {
        "available": True,
        "method": str(cfg["method"]),
        "seed": int(cfg["seed"]),
        "simulations": simulations,
        "block_length_trades": block,
        "horizon_trades": horizon,
        "hard_drawdown_pct": float(cfg["hard_drawdown_pct"]),
        "hard_drawdown_breach_probability": float(
            np.mean(drawdowns >= hard_usd)
        ),
        "maximum_drawdown_usd_quantiles": {
            "p50": float(np.quantile(drawdowns, 0.50)),
            "p90": float(np.quantile(drawdowns, 0.90)),
            "p95": float(np.quantile(drawdowns, 0.95)),
            "p99": float(np.quantile(drawdowns, 0.99)),
        },
    }


def evaluate_validation(
    routed: pd.DataFrame,
    paths: Mapping[str, Mapping[str, Any]],
    oracle: pd.DataFrame,
    completed_oracle_dates: set[str],
    *,
    evaluated_at_utc: Any,
) -> dict[str, Any]:
    """Evaluate immutable prospective outcomes without changing trade routing."""
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
        "entry_price",
        "risk_pips",
        "risk_distance",
        "exit_reason",
        "r",
        "extra_half_pip_stress_r",
        "fixed_0p01_lot_usd",
        "path_evidence_sha256",
    }
    if not closed.empty:
        if not required.issubset(closed.columns):
            raise ValueError("Closed prospective ledger lacks validation fields")
        if closed["signal_id"].astype(str).duplicated().any():
            raise ValueError("Prospective validation received duplicate trades")
        closed["entry_time_utc"] = pd.to_datetime(
            closed["entry_time_utc"], utc=True
        ).dt.as_unit("ns")
        closed["exit_time_utc"] = pd.to_datetime(
            closed["exit_time_utc"], utc=True
        ).dt.as_unit("ns")
        if before_start or closed["entry_time_utc"].lt(start).any():
            raise ValueError("Pre-start trade entered prospective validation")
        if closed["exit_time_utc"].gt(evaluated).any():
            raise ValueError("Future close entered prospective validation")
        closed = closed.sort_values(["exit_time_utc", "signal_id"]).reset_index(
            drop=True
        )
    else:
        for column in required - set(closed.columns):
            closed[column] = pd.Series(dtype=float)

    overall = payoff_metrics(closed)
    stressed = payoff_metrics(closed, "extra_half_pip_stress_r")
    sides = {
        side: payoff_metrics(closed[closed["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    remove_count = math.ceil(len(closed) * 0.05) if len(closed) else 0
    top_removed_frame = (
        closed.sort_values("r").iloc[:-remove_count].copy()
        if remove_count
        else closed.copy()
    )
    top_removed = payoff_metrics(top_removed_frame)
    trailing_cutoff = evaluated - pd.DateOffset(months=12)
    trailing = payoff_metrics(
        closed[closed["exit_time_utc"].ge(trailing_cutoff)]
        if len(closed)
        else closed
    )
    monthly = _monthly_metrics(closed)
    floating = _portfolio_floating_drawdown(closed, paths, cfg)
    oracle_metrics = _oracle_metrics(
        closed,
        oracle,
        completed_oracle_dates,
        cfg["oracle_gate"]["timing_windows_minutes_reported"],
    )

    robustness = cfg["robustness_gate"]
    risk_usd = (
        closed["risk_pips"].astype(float).to_numpy()
        * float(robustness["pip_value_usd_at_fixed_lots"])
        if len(closed)
        else np.asarray([], dtype=float)
    )
    stressed_pnl_usd = (
        closed["extra_half_pip_stress_r"].astype(float).to_numpy() * risk_usd
    )
    monte_carlo = _monte_carlo(
        stressed_pnl_usd,
        cfg["monte_carlo"],
        float(robustness["starting_balance_usd"]),
    )

    elapsed_weekdays = (
        len(pd.bdate_range(start.floor("D"), evaluated.floor("D")))
        if evaluated >= start
        else 0
    )
    frequency = {
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

    sample_gate = cfg["sample_gate"]
    economic_gate = cfg["economic_gate"]
    oracle_gate = cfg["oracle_gate"]
    mc_gate = cfg["monte_carlo"]
    elapsed = evaluated >= start + pd.DateOffset(
        months=int(sample_gate["minimum_calendar_months"])
    )
    sample = len(closed) >= int(sample_gate["minimum_closed_trades"])
    checks = {
        "minimum_calendar_months": bool(elapsed),
        "minimum_closed_trades": bool(sample),
        "all_closed_trade_paths": bool(
            floating["all_closed_trade_paths_available"]
        ),
        "all_closed_trade_oracle_dates": bool(
            oracle_metrics["all_closed_trade_oracle_dates_available"]
            and len(closed)
        ),
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
        "both_sides": bool(
            all(
                sides[side]["trades"]
                >= int(sample_gate["minimum_each_side_trades"])
                and sides[side]["profit_factor"]
                >= float(economic_gate["minimum_each_side_profit_factor"])
                for side in ("LONG", "SHORT")
            )
        ),
        "extra_half_pip_profit_factor": bool(
            stressed["profit_factor"]
            >= float(economic_gate["minimum_extra_half_pip_profit_factor"])
        ),
        "trailing_12_month_profitability": bool(
            trailing["profit_factor"]
            >= float(
                economic_gate["minimum_trailing_12_month_profit_factor"]
            )
            and trailing["net_r"]
            > float(economic_gate["minimum_trailing_12_month_net_r"])
        ),
        "positive_active_month_rate": bool(
            monthly["positive_active_month_rate"]
            >= float(robustness["minimum_positive_active_month_rate"])
        ),
        "top_5pct_winner_removal": bool(
            top_removed["profit_factor"]
            >= float(
                robustness[
                    "minimum_top_5pct_winners_removed_profit_factor"
                ]
            )
        ),
        "monthly_profit_concentration": bool(
            monthly["largest_month_share_of_positive_profit"]
            <= float(
                robustness["maximum_largest_month_share_of_positive_profit"]
            )
            and len(closed)
        ),
        "base_floating_drawdown": bool(
            floating["all_closed_trade_paths_available"]
            and floating["base_maximum_floating_drawdown_pct"]
            <= float(robustness["maximum_base_floating_drawdown_pct"])
        ),
        "stressed_floating_drawdown": bool(
            floating["all_closed_trade_paths_available"]
            and floating["stressed_maximum_floating_drawdown_pct"]
            <= float(robustness["maximum_stressed_floating_drawdown_pct"])
        ),
        "oracle_precision": bool(
            oracle_metrics["same_day_same_side_precision"] is not None
            and oracle_metrics["same_day_same_side_precision"]
            >= float(oracle_gate["minimum_same_day_same_side_precision"])
        ),
        "oracle_precision_lift": bool(
            oracle_metrics["precision_lift_over_random_side"] is not None
            and oracle_metrics["precision_lift_over_random_side"]
            > float(oracle_gate["minimum_precision_lift_over_random_side"])
        ),
        "oracle_random_side_test": bool(
            oracle_metrics[
                "random_side_poisson_binomial_tail_p_value"
            ]
            is not None
            and oracle_metrics[
                "random_side_poisson_binomial_tail_p_value"
            ]
            <= float(
                oracle_gate[
                    "maximum_random_side_poisson_binomial_tail_p_value"
                ]
            )
        ),
        "monte_carlo_hard_drawdown": bool(
            monte_carlo["available"]
            and monte_carlo["hard_drawdown_breach_probability"]
            < float(mc_gate["maximum_breach_probability"])
        ),
    }
    review_allowed = bool(all(checks.values()))
    if before_start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif not elapsed or not sample:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    elif review_allowed:
        status = "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
    else:
        status = "REJECTED_WITHOUT_RETUNING"
    result = {
        "schema_version": "eurusd_neutral_prospective_validation_result_v1",
        "status": status,
        "prospective_start_utc": start,
        "evaluated_at_utc": evaluated,
        "historical_pnl_loaded": False,
        "frequency": frequency,
        "overall": overall,
        "by_side": sides,
        "extra_half_pip_round_trip": stressed,
        "trailing_12_months": trailing,
        "top_5pct_winners_removed": top_removed,
        "monthly": monthly,
        "floating_equity": floating,
        "oracle_approximation": oracle_metrics,
        "monte_carlo": monte_carlo,
        "gate_results": checks,
        "all_gates_passed": review_allowed,
        "research_review_allowed": review_allowed,
        "controlled_demo_ready": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    return _serialize(result)


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "evaluate_validation",
    "load_config",
    "poisson_binomial_tail_probability",
    "trade_path_marks",
    "verify_lock",
]
