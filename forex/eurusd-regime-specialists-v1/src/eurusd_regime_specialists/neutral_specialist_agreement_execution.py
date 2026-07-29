from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_specialist_agreement_execution.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_SPECIALIST_AGREEMENT_EXECUTION_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_specialist_agreement_execution"
PIP = 0.0001


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_price_path_outcome") is not True
        or lock.get("oracle_decision_use_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Specialist-agreement execution lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Specialist-agreement execution drift: {relative}"
            )
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def _utc_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="raise")


def load_candidates(config: dict[str, Any]) -> pd.DataFrame:
    census_lock = config["census_result_lock"]
    census_lock_path = PACKAGE_ROOT / census_lock["path"]
    if sha256_file(census_lock_path) != census_lock["sha256"]:
        raise RuntimeError("Agreement census result lock drift")
    census_result = json.loads(census_lock_path.read_text(encoding="utf-8"))
    if census_result["status"] != census_lock["required_status"]:
        raise RuntimeError("Agreement census did not authorize execution")
    source = config["candidate_source"]
    path = PACKAGE_ROOT / source["path"]
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("Agreement candidate source drift")
    candidates = pd.read_csv(path)
    required = {
        "entry_time_utc",
        "side",
        "distinct_experts",
        "expert_combination",
        "eligible_date",
    }
    if not required.issubset(candidates.columns):
        raise RuntimeError("Agreement candidate schema drift")
    candidates["entry_time_utc"] = _utc_series(candidates["entry_time_utc"])
    if (
        len(candidates) != int(source["rows"])
        or candidates["eligible_date"].duplicated().any()
        or not candidates["side"].isin(["LONG", "SHORT"]).all()
    ):
        raise RuntimeError("Agreement candidate census drift")
    return candidates.sort_values("entry_time_utc").reset_index(drop=True)


def load_eurusd_m5(config: dict[str, Any]) -> pd.DataFrame:
    source = config["eurusd_m5_source"]
    path = Path(source["path"])
    manifest = Path(source["manifest_path"])
    if (
        sha256_file(path) != source["sha256"]
        or sha256_file(manifest) != source["manifest_sha256"]
    ):
        raise RuntimeError("EURUSD M5 source drift")
    frame = pd.read_parquet(path)
    required = {
        "timestamp_ms",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
    }
    if not required.issubset(frame.columns):
        raise RuntimeError("EURUSD M5 schema drift")
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_ms"], unit="ms", utc=True
    )
    frame = frame.set_index("timestamp_utc").sort_index()
    if frame.index.duplicated().any():
        raise RuntimeError("Duplicate EURUSD M5 timestamps")
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_utc"])
    return frame.loc[(frame.index >= start) & (frame.index <= end)].copy()


def _effective_ask(bar: pd.Series, field: str, spread_floor: float) -> float:
    return max(
        float(bar[f"ask_{field}"]),
        float(bar[f"bid_{field}"]) + spread_floor,
    )


def simulate_one(
    candidate: pd.Series,
    m5: pd.DataFrame,
    execution: dict[str, Any],
) -> dict[str, Any]:
    entry_time = pd.Timestamp(candidate["entry_time_utc"])
    hold_end = entry_time + pd.Timedelta(
        hours=int(execution["maximum_hold_hours"])
    )
    base = {
        "eligible_date": str(candidate["eligible_date"]),
        "entry_time_utc": entry_time,
        "side": str(candidate["side"]),
        "distinct_experts": int(candidate["distinct_experts"]),
        "expert_combination": str(candidate["expert_combination"]),
    }
    if entry_time not in m5.index:
        return {**base, "status": "CASH_MISSING_ENTRY_BAR"}
    if (
        execution["required_final_bar_at_maximum_hold_clock"] is True
        and hold_end not in m5.index
    ):
        return {**base, "status": "CASH_INCOMPLETE_MAXIMUM_HOLD_PATH"}
    path = m5.loc[entry_time:hold_end]
    if path.empty:
        return {**base, "status": "CASH_MISSING_ENTRY_BAR"}
    stop_distance = float(execution["stop_pips"]) * PIP
    target_distance = float(execution["target_pips"]) * PIP
    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    slippage = float(execution["adverse_slippage_pips_per_side"]) * PIP
    side = str(candidate["side"])
    entry_bar = path.iloc[0]
    if side == "LONG":
        entry = _effective_ask(entry_bar, "open", spread_floor) + slippage
        stop = entry - stop_distance
        target = entry + target_distance
    else:
        entry = float(entry_bar["bid_open"]) - slippage
        stop = entry + stop_distance
        target = entry - target_distance
    exit_time = path.index[-1]
    exit_reason = "TIME"
    final_bar = path.iloc[-1]
    exit_price = (
        float(final_bar["bid_close"]) - slippage
        if side == "LONG"
        else _effective_ask(final_bar, "close", spread_floor) + slippage
    )
    for timestamp, bar in path.iterrows():
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                exit_time = timestamp
                exit_reason = "STOP"
                exit_price = min(float(bar["bid_open"]), stop) - slippage
                break
            if float(bar["bid_high"]) >= target:
                exit_time = timestamp
                exit_reason = "TARGET"
                exit_price = max(float(bar["bid_open"]), target) - slippage
                break
        else:
            ask_open = _effective_ask(bar, "open", spread_floor)
            ask_high = _effective_ask(bar, "high", spread_floor)
            ask_low = _effective_ask(bar, "low", spread_floor)
            if ask_high >= stop:
                exit_time = timestamp
                exit_reason = "STOP"
                exit_price = max(ask_open, stop) + slippage
                break
            if ask_low <= target:
                exit_time = timestamp
                exit_reason = "TARGET"
                exit_price = min(ask_open, target) + slippage
                break
    r_value = (
        (exit_price - entry) / stop_distance
        if side == "LONG"
        else (entry - exit_price) / stop_distance
    )
    stress_r = r_value - (
        float(execution["extra_round_trip_stress_pips"])
        / float(execution["stop_pips"])
    )
    return {
        **base,
        "status": "CLOSED",
        "exit_time_utc": exit_time,
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "risk_distance": stop_distance,
        "risk_pips": float(execution["stop_pips"]),
        "r": r_value,
        "extra_half_pip_stress_r": stress_r,
        "fixed_0p01_lot_usd": r_value
        * float(execution["stop_pips"])
        * 0.1,
    }


def _quarantine_overlap(
    entry: pd.Timestamp, config: dict[str, Any]
) -> bool:
    hold_end = entry + pd.Timedelta(
        hours=int(config["execution"]["maximum_hold_hours"])
    )
    return any(
        entry <= pd.Timestamp(row["end_utc"])
        and hold_end >= pd.Timestamp(row["start_utc"])
        for row in config["quarantine"]
    )


def execute_candidates(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, Any]] = []
    routing: list[dict[str, Any]] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    for _, candidate in candidates.iterrows():
        entry = pd.Timestamp(candidate["entry_time_utc"])
        base = {
            "eligible_date": candidate["eligible_date"],
            "entry_time_utc": entry,
            "side": candidate["side"],
            "expert_combination": candidate["expert_combination"],
        }
        if _quarantine_overlap(entry, config):
            routing.append({**base, "status": "CASH_QUARANTINED_PATH"})
            continue
        if entry < open_until:
            routing.append(
                {
                    **base,
                    "status": "CASH_PRIOR_POSITION_OPEN",
                    "prior_position_exit_utc": open_until,
                }
            )
            continue
        result = simulate_one(candidate, m5, config["execution"])
        routing.append(
            {
                **base,
                "status": result["status"],
                "prior_position_exit_utc": (
                    result.get("exit_time_utc") if result["status"] == "CLOSED" else pd.NaT
                ),
            }
        )
        if result["status"] != "CLOSED":
            continue
        records.append(result)
        open_until = pd.Timestamp(result["exit_time_utc"])
    return pd.DataFrame(records), pd.DataFrame(routing)


def payoff_metrics(frame: pd.DataFrame, column: str = "r") -> dict[str, Any]:
    if frame.empty:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "average_win_r": 0.0,
            "average_loss_r": 0.0,
            "realized_payoff_ratio": 0.0,
            "profit_factor": 0.0,
            "net_r": 0.0,
            "expectancy_r": 0.0,
            "max_drawdown_r": 0.0,
        }
    values = frame[column].astype(float)
    wins = values[values > 0.0]
    losses = values[values <= 0.0]
    average_win = float(wins.mean()) if len(wins) else 0.0
    average_loss = float(-losses.mean()) if len(losses) else 0.0
    gross_loss = float(-losses.sum())
    equity = values.cumsum()
    drawdown = equity.cummax().clip(lower=0.0) - equity
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": float(len(wins) / len(values)),
        "average_win_r": average_win,
        "average_loss_r": average_loss,
        "realized_payoff_ratio": (
            average_win / average_loss if average_loss else math.inf
        ),
        "profit_factor": (
            float(wins.sum()) / gross_loss if gross_loss else math.inf
        ),
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()),
        "max_drawdown_r": float(drawdown.max()),
    }


def remove_top_winners(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    count = max(1, math.ceil(len(frame) * 0.05))
    return frame.drop(index=frame.nlargest(count, "r").index).copy()


def attach_oracle_matches(
    trades: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    oracle_cfg = config["oracle"]
    path = PACKAGE_ROOT / oracle_cfg["path"]
    if sha256_file(path) != oracle_cfg["sha256"]:
        raise RuntimeError("Evaluation-only oracle drift")
    oracle = pd.read_csv(path)
    oracle = oracle[oracle["regime"].eq(oracle_cfg["required_regime"])].copy()
    oracle["entry_time_utc"] = _utc_series(oracle["entry_time_utc"])
    tolerance = pd.Timedelta(
        minutes=int(oracle_cfg["same_side_tolerance_minutes"])
    )
    records: list[dict[str, Any]] = []
    for index, trade in trades.iterrows():
        block = oracle[
            oracle["side"].eq(trade["side"])
            & oracle["entry_time_utc"].between(
                trade["entry_time_utc"] - tolerance,
                trade["entry_time_utc"] + tolerance,
                inclusive="both",
            )
        ].copy()
        if block.empty:
            records.append(
                {
                    "trade_index": int(index),
                    "entry_time_utc": trade["entry_time_utc"],
                    "side": trade["side"],
                    "oracle_match": False,
                    "oracle_entry_time_utc": pd.NaT,
                    "absolute_minutes": np.nan,
                }
            )
            continue
        block["absolute_minutes"] = (
            block["entry_time_utc"] - trade["entry_time_utc"]
        ).abs().dt.total_seconds() / 60.0
        match = block.sort_values(
            ["absolute_minutes", "entry_time_utc", "oracle_trade_number"]
        ).iloc[0]
        records.append(
            {
                "trade_index": int(index),
                "entry_time_utc": trade["entry_time_utc"],
                "side": trade["side"],
                "oracle_match": True,
                "oracle_entry_time_utc": match["entry_time_utc"],
                "absolute_minutes": float(match["absolute_minutes"]),
            }
        )
    matches = pd.DataFrame(records)
    matched = int(matches["oracle_match"].sum()) if not matches.empty else 0
    return matches, {
        "neutral_oracle_rows": len(oracle),
        "executed_trades": len(trades),
        "same_side_matches_15m": matched,
        "same_side_precision_15m": (
            float(matched / len(trades)) if len(trades) else 0.0
        ),
        "same_side_recall_15m": (
            float(matched / len(oracle)) if len(oracle) else 0.0
        ),
        "oracle_used_for_decisions": False,
    }


def _period(frame: pd.DataFrame, bounds: list[str]) -> pd.DataFrame:
    start, end = (pd.Timestamp(value) for value in bounds)
    return frame[
        frame["entry_time_utc"].between(start, end, inclusive="both")
    ]


def summarize(
    trades: pd.DataFrame, config: dict[str, Any]
) -> tuple[dict[str, Any], pd.DataFrame]:
    overall = payoff_metrics(trades)
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(remove_top_winners(trades))
    windows = {
        name: payoff_metrics(_period(trades, bounds))
        for name, bounds in config["windows"].items()
    }
    sides = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    combinations = {
        combination: payoff_metrics(block)
        for combination, block in trades.groupby(
            "expert_combination", sort=True
        )
    }
    matches, oracle = attach_oracle_matches(trades, config)
    gates = config["research_gates"]
    gate_results = {
        "minimum_executed_trades": overall["trades"]
        >= int(gates["minimum_executed_trades"]),
        "win_rate": float(gates["minimum_win_rate"])
        <= overall["win_rate"]
        <= float(gates["maximum_win_rate"]),
        "realized_payoff_ratio": float(
            gates["minimum_realized_payoff_ratio"]
        )
        <= overall["realized_payoff_ratio"]
        <= float(gates["maximum_realized_payoff_ratio"]),
        "profit_factor": overall["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "each_window_profit_factor": all(
            metrics["profit_factor"]
            > float(gates["minimum_profit_factor_each_window_exclusive"])
            for metrics in windows.values()
        ),
        "latest_six_month_capacity": windows["LATEST_SIX_MONTHS"]["trades"]
        >= int(gates["minimum_latest_six_month_trades"]),
        "latest_six_month_profit_factor": windows[
            "LATEST_SIX_MONTHS"
        ]["profit_factor"]
        > float(
            gates["minimum_latest_six_month_profit_factor_exclusive"]
        ),
        "both_sides": all(
            sides[side]["trades"] >= int(gates["minimum_trades_each_side"])
            and sides[side]["profit_factor"]
            > float(gates["minimum_profit_factor_each_side_exclusive"])
            for side in ("LONG", "SHORT")
        ),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "extra_half_pip_profit_factor": stressed["profit_factor"]
        > float(
            gates["minimum_extra_half_pip_profit_factor_exclusive"]
        ),
        "top_5pct_winners_removed_profit_factor": top_removed[
            "profit_factor"
        ]
        > float(
            gates[
                "minimum_top_5pct_winners_removed_profit_factor_exclusive"
            ]
        ),
        "oracle_precision": oracle["same_side_precision_15m"]
        >= float(gates["minimum_same_side_oracle_precision_15m"]),
        "oracle_recall": oracle["same_side_recall_15m"]
        >= float(gates["minimum_same_side_oracle_recall_15m"]),
    }
    passed = bool(all(gate_results.values()))
    return {
        "overall": overall,
        "extra_half_pip": stressed,
        "top_5pct_winners_removed": top_removed,
        "windows": windows,
        "by_side": sides,
        "by_expert_combination": combinations,
        "oracle_resemblance": oracle,
        "gate_results": gate_results,
        "all_research_gates_passed": passed,
    }, matches


def run_execution() -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    verify_lock()
    config = load_config()
    candidates = load_candidates(config)
    m5 = load_eurusd_m5(config)
    trades, routing = execute_candidates(candidates, m5, config)
    summary, matches = summarize(trades, config)
    status = (
        "RESEARCH_GATES_PASS_REQUIRES_SEPARATE_PROSPECTIVE_FREEZE"
        if summary["all_research_gates_passed"]
        else "REJECTED_EXACT_AGREEMENT_EXECUTION"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_specialist_agreement_execution_result_v1"
        ),
        "status": status,
        "frozen_at_utc": config["frozen_at_utc"],
        "candidates": len(candidates),
        "executed_trades": len(trades),
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


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_result(
    result: dict[str, Any], artifacts: dict[str, pd.DataFrame]
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_safe(result), indent=2, sort_keys=True) + "\n"
    (OUTPUT_ROOT / "RESULT.json").write_text(payload, encoding="utf-8")
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "execute_candidates",
    "load_candidates",
    "load_eurusd_m5",
    "payoff_metrics",
    "run_execution",
    "simulate_one",
    "verify_lock",
    "write_result",
]
