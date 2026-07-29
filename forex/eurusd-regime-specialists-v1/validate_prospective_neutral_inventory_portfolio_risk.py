from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import prospective_neutral_inventory_clock_transfer as transfer
import validate_prospective_neutral_inventory_clock_portfolio as portfolio
import validate_prospective_neutral_inventory_unwind_0005 as primary
from capture_prospective_neutral_inventory_unwind_0005 import _timestamp
from capture_prospective_neutral_inventory_unwind_0005_path import (
    _existing_path,
    execute_ticks,
)
from capture_prospective_neutral_ownership import decode_ticks
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_inventory_portfolio_risk_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_INVENTORY_PORTFOLIO_RISK_"
    "PREREG_2026_07_29.sha256.json"
)
PRIMARY_PATH_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-unwind-0005-v1/path"
)
TRANSFER_PATH_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-clock-transfer-v1/path"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_preregistration() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_first_portfolio_observation": True,
        "locked_with_zero_primary_paths": True,
        "locked_with_zero_transfer_paths": True,
        "historical_backtest_allowed": False,
        "historical_eurusd_pnl_allowed": False,
        "network_request_allowed": False,
        "broker_action_allowed": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("Portfolio-risk preregistration is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"Portfolio-risk implementation drift: {relative}")
    portfolio.verify_preregistration()
    return lock


def _load_ticks(path_root: Path, manifest: Mapping[str, Any]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for raw in manifest["raw_snapshots"]:
        raw_path = path_root / str(raw["raw_relative_path"])
        if sha256_file(raw_path) != str(raw["raw_sha256"]):
            raise RuntimeError("Portfolio-risk raw tick hash drift")
        frames.append(
            decode_ticks(
                raw_path.read_bytes(),
                "EURUSD",
                _timestamp(raw["hour_utc"]),
            )
        )
    if not frames:
        raise RuntimeError("Closed path has no immutable tick snapshots")
    ticks = pd.concat(frames, ignore_index=True)
    ticks["timestamp_utc"] = pd.to_datetime(
        ticks["timestamp_utc"], utc=True
    ).dt.as_unit("ns")
    return ticks.sort_values("timestamp_utc").reset_index(drop=True)


def load_closed_paths(
    path_root: Path,
    *,
    component: str,
    fixed_clock: str | None,
    evaluated_at_utc: Any,
) -> list[dict[str, Any]]:
    evaluated = _timestamp(evaluated_at_utc)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for manifest_path in sorted((path_root / "manifests").glob("PATH_*.json")):
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        decision_id = str(raw["decision_id"])
        if decision_id in seen:
            raise RuntimeError("Duplicate portfolio-risk path identity")
        seen.add(decision_id)
        manifest = _existing_path(path_root, decision_id)
        if manifest is None:
            raise RuntimeError("Portfolio-risk path disappeared during verification")
        if _timestamp(manifest["path_captured_at_utc"]) > evaluated:
            continue
        if manifest.get("historical_eurusd_pnl_loaded") is not False:
            raise RuntimeError("Portfolio-risk historical PnL boundary drift")
        if manifest.get("broker_action_allowed") is not False:
            raise RuntimeError("Portfolio-risk broker boundary drift")
        execution = manifest["execution"]
        if execution.get("status") != "CLOSED":
            continue
        clock = str(fixed_clock or manifest.get("clock"))
        if clock not in portfolio.CLOCKS:
            raise RuntimeError("Portfolio-risk clock drift")
        records.append(
            {
                "signal_id": decision_id,
                "component": component,
                "clock": clock,
                "entry_date_utc": str(manifest["entry_date_utc"]),
                "scheduled_entry_time_utc": _timestamp(
                    manifest["entry_time_utc"]
                ),
                "side": str(execution["side"]),
                "manifest": manifest,
                "execution": execution,
                "ticks": _load_ticks(path_root, manifest),
            }
        )
    return records


def collect_closed_paths(
    *,
    evaluated_at_utc: Any,
    primary_path_root: Path = PRIMARY_PATH_ROOT,
    transfer_path_root: Path = TRANSFER_PATH_ROOT,
) -> list[dict[str, Any]]:
    rows = [
        *load_closed_paths(
            primary_path_root,
            component="primary_0005",
            fixed_clock="0005",
            evaluated_at_utc=evaluated_at_utc,
        ),
        *load_closed_paths(
            transfer_path_root,
            component="transfer_0605_1205",
            fixed_clock=None,
            evaluated_at_utc=evaluated_at_utc,
        ),
    ]
    if len({row["signal_id"] for row in rows}) != len(rows):
        raise RuntimeError("Duplicate path identity across portfolio components")
    return sorted(
        rows,
        key=lambda row: (
            _timestamp(row["execution"]["entry_tick_time_utc"]),
            row["clock"],
            row["signal_id"],
        ),
    )


def trade_mark_to_market_r(trade: Mapping[str, Any]) -> pd.DataFrame:
    execution = trade["execution"]
    ticks = trade["ticks"].copy()
    entry = _timestamp(execution["entry_tick_time_utc"])
    exit_time = _timestamp(execution["exit_time_utc"])
    ticks = ticks[
        ticks["timestamp_utc"].ge(entry)
        & ticks["timestamp_utc"].le(exit_time)
    ].copy()
    if ticks.empty:
        raise RuntimeError("Closed path has no ticks inside its execution interval")
    slippage = float(execution["adverse_slippage_pips_per_side"])
    pip = 0.0001
    entry_fill = float(execution["entry_fill"])
    if execution["side"] == "LONG":
        liquidation = ticks["bid"].astype(float) - slippage * pip
        pnl_pips = (liquidation - entry_fill) / pip
    elif execution["side"] == "SHORT":
        liquidation = ticks["ask"].astype(float) + slippage * pip
        pnl_pips = (entry_fill - liquidation) / pip
    else:
        raise RuntimeError("Closed path has a non-directional side")
    result = pd.DataFrame(
        {
            "timestamp_utc": ticks["timestamp_utc"],
            "unrealized_r": pnl_pips / float(execution["fixed_stop_pips"]),
        }
    )
    if _timestamp(result.iloc[-1]["timestamp_utc"]) != exit_time:
        raise RuntimeError("Closed path is missing its exact exit tick")
    return result.reset_index(drop=True)


def floating_drawdown(
    trades: Sequence[Mapping[str, Any]],
    *,
    extra_round_trip_pips: float,
    balance_usd: float,
    usd_pip_value: float,
) -> dict[str, Any]:
    running_peak_r = 0.0
    realized_r = 0.0
    maximum_drawdown_r = 0.0
    peak_time: pd.Timestamp | None = None
    trough_time: pd.Timestamp | None = None
    current_peak_time: pd.Timestamp | None = None
    for trade in trades:
        execution = trade["execution"]
        cost_r = extra_round_trip_pips / float(execution["fixed_stop_pips"])
        curve = trade_mark_to_market_r(trade)
        for point in curve.itertuples(index=False):
            equity_r = realized_r + float(point.unrealized_r) - cost_r
            timestamp = _timestamp(point.timestamp_utc)
            if equity_r > running_peak_r:
                running_peak_r = equity_r
                current_peak_time = timestamp
            drawdown_r = running_peak_r - equity_r
            if drawdown_r > maximum_drawdown_r:
                maximum_drawdown_r = drawdown_r
                peak_time = current_peak_time
                trough_time = timestamp
        realized_r += float(execution["r"]) - cost_r
        if realized_r > running_peak_r:
            running_peak_r = realized_r
            current_peak_time = _timestamp(execution["exit_time_utc"])
    fixed_stop_pips = (
        float(trades[0]["execution"]["fixed_stop_pips"]) if trades else 6.0
    )
    risk_usd_per_r = fixed_stop_pips * usd_pip_value
    drawdown_usd = maximum_drawdown_r * risk_usd_per_r
    return {
        "trades": len(trades),
        "extra_round_trip_pips": float(extra_round_trip_pips),
        "maximum_floating_drawdown_r": maximum_drawdown_r,
        "maximum_floating_drawdown_usd": drawdown_usd,
        "maximum_floating_drawdown_fraction": (
            drawdown_usd / balance_usd if balance_usd > 0.0 else math.inf
        ),
        "peak_time_utc": peak_time.isoformat() if peak_time is not None else None,
        "trough_time_utc": (
            trough_time.isoformat() if trough_time is not None else None
        ),
        "ending_equity_r": realized_r,
        "ending_equity_usd": balance_usd + realized_r * risk_usd_per_r,
    }


def exposure_and_margin(
    trades: Sequence[Mapping[str, Any]],
    account: Mapping[str, Any],
) -> dict[str, Any]:
    units = (
        float(account["fixed_lots_per_position"])
        * float(account["standard_lot_base_units"])
    )
    notionals = [
        abs(float(row["execution"]["entry_fill"]) * units) for row in trades
    ]
    maximum_notional = max(notionals, default=0.0)
    margin = maximum_notional / float(account["assumed_retail_leverage"])
    balance = float(account["declared_research_balance_usd"])
    return {
        "maximum_concurrent_positions": 1 if trades else 0,
        "maximum_gross_lots": (
            float(account["fixed_lots_per_position"]) if trades else 0.0
        ),
        "maximum_absolute_eurusd_notional_usd": maximum_notional,
        "maximum_required_margin_usd": margin,
        "maximum_margin_utilization_fraction": (
            margin / balance if balance > 0.0 else math.inf
        ),
        "assumed_retail_leverage": float(account["assumed_retail_leverage"]),
    }


def delayed_execution_metrics(
    trades: Sequence[Mapping[str, Any]],
    delay_seconds: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for trade in trades:
        decision = {
            "side": trade["side"],
            "entry_time_utc": (
                _timestamp(trade["scheduled_entry_time_utc"])
                + pd.Timedelta(seconds=delay_seconds)
            ),
        }
        component_config = (
            primary.load_config()
            if trade["component"] == "primary_0005"
            else transfer.load_config()
        )
        execution = execute_ticks(decision, trade["ticks"], component_config)
        rows.append(
            {
                "signal_id": trade["signal_id"],
                "clock": trade["clock"],
                **execution,
            }
        )
    closed = [row for row in rows if row["status"] == "CLOSED"]
    metrics = primary.trade_metrics(row["r"] for row in closed)
    intervals = portfolio.interval_integrity(pd.DataFrame(closed))
    return {
        "delay_seconds": int(delay_seconds),
        "base_signals": len(trades),
        "closed_trades": len(closed),
        "fill_rate": len(closed) / len(trades) if trades else 0.0,
        "nonclosed_statuses": dict(
            (
                str(status),
                int(count),
            )
            for status, count in pd.Series(
                [row["status"] for row in rows if row["status"] != "CLOSED"],
                dtype=str,
            )
            .value_counts()
            .items()
        ),
        "metrics": metrics,
        "interval_integrity": intervals,
    }


def moving_block_bootstrap(
    returns_r: Sequence[float],
    *,
    simulations: int,
    block_length: int,
    seed: int,
    extra_cost_r: float,
    balance_usd: float,
    risk_usd_per_r: float,
    ruin_equity_usd: float,
    hard_drawdown_fraction: float,
    quantiles: Sequence[float],
) -> dict[str, Any]:
    values = np.asarray(list(returns_r), dtype=float)
    if values.size == 0:
        return {
            "simulations_run": 0,
            "horizon_trades": 0,
            "risk_of_ruin": 0.0,
            "hard_drawdown_probability": 0.0,
            "maximum_drawdown_usd_quantiles": {
                str(value): 0.0 for value in quantiles
            },
        }
    rng = np.random.default_rng(seed)
    blocks = int(math.ceil(values.size / block_length))
    starts = rng.integers(0, values.size, size=(simulations, blocks))
    offsets = np.arange(block_length)
    indices = (starts[:, :, None] + offsets) % values.size
    sampled = values[indices.reshape(simulations, -1)[:, : values.size]]
    sampled = sampled - float(extra_cost_r)
    equity = balance_usd + np.cumsum(sampled * risk_usd_per_r, axis=1)
    initial = np.full((simulations, 1), balance_usd)
    with_initial = np.concatenate([initial, equity], axis=1)
    peaks = np.maximum.accumulate(with_initial, axis=1)
    maximum_drawdowns = np.max(peaks - with_initial, axis=1)
    ruin = np.min(with_initial, axis=1) <= ruin_equity_usd
    hard = maximum_drawdowns >= hard_drawdown_fraction * balance_usd
    return {
        "method": "CIRCULAR_MOVING_BLOCK_BOOTSTRAP",
        "simulations_run": int(simulations),
        "horizon_trades": int(values.size),
        "block_length_trades": int(block_length),
        "random_seed": int(seed),
        "extra_cost_r_per_trade": float(extra_cost_r),
        "risk_of_ruin": float(ruin.mean()),
        "hard_drawdown_fraction": float(hard_drawdown_fraction),
        "hard_drawdown_probability": float(hard.mean()),
        "maximum_drawdown_usd_quantiles": {
            str(value): float(np.quantile(maximum_drawdowns, value))
            for value in quantiles
        },
    }


def _daily_metrics(
    trades: Sequence[Mapping[str, Any]],
    usd_pip_value: float,
) -> dict[str, Any]:
    if not trades:
        return {"active_days": 0, "worst_day_usd": 0.0, "days": {}}
    rows = []
    for trade in trades:
        execution = trade["execution"]
        rows.append(
            {
                "date": str(trade["entry_date_utc"]),
                "pnl_usd": (
                    float(execution["r"])
                    * float(execution["fixed_stop_pips"])
                    * usd_pip_value
                ),
            }
        )
    daily = pd.DataFrame(rows).groupby("date")["pnl_usd"].sum().sort_index()
    return {
        "active_days": int(len(daily)),
        "worst_day_usd": float(daily.min()),
        "days": {str(day): float(value) for day, value in daily.items()},
    }


def _calendar_months(start: pd.Timestamp, end: pd.Timestamp) -> int:
    if end < start:
        return 0
    return max(0, (end.year - start.year) * 12 + end.month - start.month + 1)


def build_status(
    *,
    evaluated_at_utc: Any | None = None,
    primary_path_root: Path = PRIMARY_PATH_ROOT,
    transfer_path_root: Path = TRANSFER_PATH_ROOT,
    verify_lock: bool = True,
) -> dict[str, Any]:
    if verify_lock:
        verify_preregistration()
    cfg = load_config()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if evaluated_at_utc is None
        else _timestamp(evaluated_at_utc)
    )
    start = _timestamp(cfg["prospective_start_utc"])
    account = cfg["account_contract"]
    stress_cfg = cfg["stress_contract"]
    mc_cfg = cfg["monte_carlo_contract"]
    gates = cfg["admission"]

    portfolio_rows = portfolio.collect_portfolio_rows(
        evaluated_at_utc=evaluated,
        primary_path_root=primary_path_root,
        transfer_path_root=transfer_path_root,
    )
    closed = portfolio_rows[portfolio_rows["status"].eq("CLOSED")].copy()
    paths = collect_closed_paths(
        evaluated_at_utc=evaluated,
        primary_path_root=primary_path_root,
        transfer_path_root=transfer_path_root,
    )
    path_ids = {row["signal_id"] for row in paths}
    closed_ids = set(closed.get("signal_id", pd.Series(dtype=str)).astype(str))
    exact_path_coverage = path_ids == closed_ids
    intervals = portfolio.interval_integrity(closed)

    base_floating = floating_drawdown(
        paths,
        extra_round_trip_pips=0.0,
        balance_usd=float(account["declared_research_balance_usd"]),
        usd_pip_value=float(account["usd_pip_value_per_0p01_lot"]),
    )
    stressed_floating = floating_drawdown(
        paths,
        extra_round_trip_pips=float(stress_cfg["extra_round_trip_cost_pips"]),
        balance_usd=float(account["declared_research_balance_usd"]),
        usd_pip_value=float(account["usd_pip_value_per_0p01_lot"]),
    )
    margin = exposure_and_margin(paths, account)
    delays = {
        str(seconds): delayed_execution_metrics(paths, int(seconds))
        for seconds in stress_cfg["delayed_entry_seconds"]
    }
    risk_usd = (
        6.0 * float(account["usd_pip_value_per_0p01_lot"])
        if not paths
        else float(paths[0]["execution"]["fixed_stop_pips"])
        * float(account["usd_pip_value_per_0p01_lot"])
    )
    extra_cost_r = float(stress_cfg["extra_round_trip_cost_pips"]) / 6.0
    monte_carlo = moving_block_bootstrap(
        [float(row["execution"]["r"]) for row in paths],
        simulations=int(mc_cfg["simulations"]),
        block_length=int(mc_cfg["block_length_trades"]),
        seed=int(mc_cfg["random_seed"]),
        extra_cost_r=extra_cost_r,
        balance_usd=float(account["declared_research_balance_usd"]),
        risk_usd_per_r=risk_usd,
        ruin_equity_usd=float(mc_cfg["ruin_equity_usd"]),
        hard_drawdown_fraction=float(mc_cfg["hard_drawdown_fraction"]),
        quantiles=[float(value) for value in mc_cfg["drawdown_quantiles"]],
    )
    months = _calendar_months(start, evaluated)
    sample_ready = (
        months >= int(gates["minimum_calendar_months"])
        and len(paths) >= int(gates["minimum_closed_trades"])
    )
    five_second = delays["5"]
    risk_gate_results = {
        "exact_path_coverage": exact_path_coverage,
        "no_duplicate_entry_timestamps": intervals[
            "no_duplicate_entry_timestamps"
        ],
        "no_position_overlap": intervals["no_position_overlap"],
        "base_floating_drawdown": (
            base_floating["maximum_floating_drawdown_fraction"]
            <= float(gates["maximum_base_floating_drawdown_fraction"])
        ),
        "stressed_floating_drawdown": (
            stressed_floating["maximum_floating_drawdown_fraction"]
            <= float(gates["maximum_stressed_floating_drawdown_fraction"])
        ),
        "margin_utilization": (
            margin["maximum_margin_utilization_fraction"]
            <= float(gates["maximum_margin_utilization_fraction"])
        ),
        "five_second_fill_rate": (
            five_second["fill_rate"]
            >= float(gates["minimum_five_second_delayed_fill_rate"])
        ),
        "five_second_profit_factor": (
            five_second["metrics"]["profit_factor"]
            >= float(gates["minimum_five_second_delayed_profit_factor"])
        ),
        "five_second_no_overlap": five_second["interval_integrity"][
            "no_position_overlap"
        ],
        "monte_carlo_risk_of_ruin": (
            monte_carlo["risk_of_ruin"]
            < float(gates["maximum_monte_carlo_risk_of_ruin_exclusive"])
        ),
    }
    portfolio_status = portfolio.build_validation_status(
        evaluated_at_utc=evaluated,
        primary_path_root=primary_path_root,
        transfer_path_root=transfer_path_root,
    )
    all_risk_gates = all(risk_gate_results.values())
    review_allowed = (
        sample_ready
        and bool(portfolio_status["research_review_allowed"])
        and all_risk_gates
    )
    if evaluated < start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif not sample_ready:
        status = "ACCUMULATING_PROSPECTIVE_RISK_EVIDENCE"
    elif review_allowed:
        status = "INDEPENDENT_RISK_REVIEW_REQUIRED"
    else:
        status = "RISK_GATES_FAILED_WITHOUT_RETUNING"
    return {
        "schema_version": cfg["schema_version"],
        "status": status,
        "evaluated_at_utc": evaluated.isoformat(),
        "calendar_months_observed": months,
        "closed_paths": len(paths),
        "exact_closed_path_coverage": exact_path_coverage,
        "interval_integrity": intervals,
        "base_floating_equity": base_floating,
        "extra_half_pip_floating_equity": stressed_floating,
        "exposure_and_margin": margin,
        "daily": _daily_metrics(
            paths, float(account["usd_pip_value_per_0p01_lot"])
        ),
        "delayed_execution": delays,
        "monte_carlo": monte_carlo,
        "sample_ready": sample_ready,
        "portfolio_all_gates_passed": bool(portfolio_status["all_gates_passed"]),
        "risk_gate_results": risk_gate_results,
        "all_risk_gates_passed": all_risk_gates,
        "research_review_allowed": review_allowed,
        "controlled_demo_ready": False,
        "exact_mt5_parity_verified": False,
        "historical_eurusd_pnl_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    return parser.parse_args()


def main() -> int:
    parse_args()
    print(json.dumps(build_status(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
