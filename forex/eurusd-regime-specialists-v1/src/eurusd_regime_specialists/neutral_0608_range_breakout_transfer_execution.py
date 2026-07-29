from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .research import PACKAGE_ROOT, PIP, serialize, sha256_file


CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_0608_range_breakout_transfer_execution.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_0608_RANGE_BREAKOUT_TRANSFER_EXECUTION_"
    "PREREG_2026_07_29.sha256.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_0608_range_breakout_transfer_execution"
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
        raise RuntimeError("Range-breakout execution lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Range-breakout execution drift: {relative}"
            )
        checked[relative] = actual
    return checked


def _utc_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="raise")


def load_candidates(config: dict[str, Any]) -> pd.DataFrame:
    census_lock = config["census_result_lock"]
    census_lock_path = PACKAGE_ROOT / census_lock["path"]
    if sha256_file(census_lock_path) != census_lock["sha256"]:
        raise RuntimeError("V1.1 census result lock drift")
    census_result = json.loads(
        census_lock_path.read_text(encoding="utf-8")
    )
    if (
        census_result["status"] != census_lock["required_status"]
        or census_result.get("census_pass") is not True
    ):
        raise RuntimeError("V1.1 census did not authorize execution freeze")
    source = config["candidate_source"]
    path = PACKAGE_ROOT / source["path"]
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("V1.1 candidate source drift")
    candidates = pd.read_csv(path)
    required = {
        "family",
        "signal_time_utc",
        "entry_time_utc",
        "side",
        "state_known_lag_hours",
        "risk_eligible",
        "entry_position",
        "entry_price_decision_time",
        "stop_price_decision_time",
        "risk_distance",
        "risk_pips",
        "window",
    }
    if not required.issubset(candidates.columns):
        raise RuntimeError("V1.1 candidate schema drift")
    for column in (
        "signal_time_utc",
        "entry_time_utc",
        "matched_state_time_utc",
        "state_known_at_utc",
    ):
        candidates[column] = _utc_series(candidates[column])
    if (
        len(candidates) != int(source["rows"])
        or not candidates["family"].eq(source["family"]).all()
        or not candidates["side"].isin(["LONG", "SHORT"]).all()
        or not candidates["risk_eligible"].astype(bool).all()
        or candidates["state_known_lag_hours"].gt(
            float(source["maximum_state_known_lag_hours"])
        ).any()
        or candidates["risk_distance"].le(0.0).any()
    ):
        raise RuntimeError("V1.1 candidate census drift")
    return candidates.sort_values(
        ["entry_time_utc", "signal_time_utc", "side"]
    ).reset_index(drop=True)


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
    return frame.loc[
        (frame.index >= start) & (frame.index <= end)
    ].copy()


def _effective_ask(
    bar: pd.Series,
    field: str,
    spread_floor: float,
) -> float:
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
        hours=float(execution["maximum_hold_hours"])
    )
    base = {
        "family": str(candidate["family"]),
        "regime": "NEUTRAL",
        "signal_time_utc": pd.Timestamp(candidate["signal_time_utc"]),
        "entry_time_utc": entry_time,
        "side": str(candidate["side"]),
        "window": str(candidate["window"]),
        "risk_pips": float(candidate["risk_pips"]),
    }
    if entry_time not in m5.index:
        return {**base, "status": "CASH_MISSING_ENTRY_BAR"}
    if (
        execution["required_final_bar_at_maximum_hold_clock"] is True
        and hold_end not in m5.index
    ):
        return {
            **base,
            "status": "CASH_INCOMPLETE_MAXIMUM_HOLD_PATH",
        }
    path = m5.loc[entry_time:hold_end]
    if path.empty:
        return {**base, "status": "CASH_MISSING_ENTRY_BAR"}
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["adverse_slippage_pips_per_side"]) * PIP
    )
    side = str(candidate["side"])
    entry_bar = path.iloc[0]
    if side == "LONG":
        entry = (
            _effective_ask(entry_bar, "open", spread_floor)
            + slippage
        )
    else:
        entry = float(entry_bar["bid_open"]) - slippage
    tolerance = float(execution["entry_price_tolerance"])
    frozen_entry = float(candidate["entry_price_decision_time"])
    if abs(entry - frozen_entry) > tolerance:
        return {**base, "status": "CASH_ENTRY_PRICE_DRIFT"}
    stop = float(candidate["stop_price_decision_time"])
    risk = float(candidate["risk_distance"])
    expected_risk = entry - stop if side == "LONG" else stop - entry
    if (
        not np.isfinite(risk)
        or risk <= 0.0
        or abs(expected_risk - risk) > tolerance
    ):
        return {**base, "status": "CASH_RISK_CONTRACT_DRIFT"}
    target_r = float(execution["target_r"])
    target = (
        entry + target_r * risk
        if side == "LONG"
        else entry - target_r * risk
    )
    exit_time = path.index[-1]
    exit_reason = "TIME_12H"
    final_bar = path.iloc[-1]
    exit_price = (
        float(final_bar["bid_close"]) - slippage
        if side == "LONG"
        else _effective_ask(
            final_bar, "close", spread_floor
        )
        + slippage
    )
    for timestamp, bar in path.iterrows():
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                exit_time = timestamp
                exit_reason = "STOP"
                exit_price = (
                    min(float(bar["bid_open"]), stop) - slippage
                )
                break
            if float(bar["bid_high"]) >= target:
                exit_time = timestamp
                exit_reason = "TARGET"
                exit_price = (
                    max(float(bar["bid_open"]), target) - slippage
                )
                break
        else:
            ask_open = _effective_ask(
                bar, "open", spread_floor
            )
            ask_high = _effective_ask(
                bar, "high", spread_floor
            )
            ask_low = _effective_ask(
                bar, "low", spread_floor
            )
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
    pnl = (
        exit_price - entry
        if side == "LONG"
        else entry - exit_price
    )
    r_value = pnl / risk
    stress_r = r_value - (
        float(execution["extra_round_trip_stress_pips"])
        * PIP
        / risk
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
        "risk_distance": risk,
        "r": r_value,
        "extra_half_pip_stress_r": stress_r,
        "fixed_0p01_lot_usd": pnl * 1000.0,
    }


def _quarantine_overlap(
    entry: pd.Timestamp,
    config: dict[str, Any],
) -> bool:
    hold_end = entry + pd.Timedelta(
        hours=float(config["execution"]["maximum_hold_hours"])
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
    daily_count: dict[str, int] = {}
    maximum_daily = int(
        config["execution"]["maximum_trades_per_utc_day"]
    )
    for candidate_index, candidate in candidates.iterrows():
        entry = pd.Timestamp(candidate["entry_time_utc"])
        date = entry.strftime("%Y-%m-%d")
        base = {
            "candidate_index": int(candidate_index),
            "signal_time_utc": candidate["signal_time_utc"],
            "entry_time_utc": entry,
            "side": candidate["side"],
        }
        if _quarantine_overlap(entry, config):
            routing.append(
                {**base, "status": "CASH_QUARANTINED_PATH"}
            )
            continue
        if entry <= open_until:
            routing.append(
                {
                    **base,
                    "status": "CASH_PRIOR_POSITION_OPEN",
                    "prior_position_exit_utc": open_until,
                }
            )
            continue
        if daily_count.get(date, 0) >= maximum_daily:
            routing.append(
                {**base, "status": "CASH_DAILY_CAP"}
            )
            continue
        result = simulate_one(
            candidate,
            m5,
            config["execution"],
        )
        routing.append(
            {
                **base,
                "status": result["status"],
                "prior_position_exit_utc": (
                    result.get("exit_time_utc")
                    if result["status"] == "CLOSED"
                    else pd.NaT
                ),
            }
        )
        if result["status"] != "CLOSED":
            continue
        records.append(result)
        open_until = pd.Timestamp(result["exit_time_utc"])
        daily_count[date] = daily_count.get(date, 0) + 1
    return pd.DataFrame(records), pd.DataFrame(routing)


def payoff_metrics(
    frame: pd.DataFrame,
    column: str = "r",
) -> dict[str, Any]:
    if frame.empty:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "breakevens": 0,
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
    losses = values[values < 0.0]
    breakevens = values[values == 0.0]
    average_win = float(wins.mean()) if len(wins) else 0.0
    average_loss = float(-losses.mean()) if len(losses) else 0.0
    gross_loss = float(-losses.sum())
    equity = values.cumsum()
    running_peak = equity.cummax().clip(lower=0.0)
    drawdown = running_peak - equity
    return {
        "trades": int(len(values)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "breakevens": int(len(breakevens)),
        "win_rate": float(len(wins) / len(values)),
        "average_win_r": average_win,
        "average_loss_r": average_loss,
        "realized_payoff_ratio": (
            average_win / average_loss
            if average_loss
            else math.inf
        ),
        "profit_factor": (
            float(wins.sum()) / gross_loss
            if gross_loss
            else math.inf
        ),
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()),
        "max_drawdown_r": float(drawdown.max()),
    }


def remove_top_winners(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    count = max(1, math.ceil(len(frame) * 0.05))
    return frame.drop(
        index=frame.nlargest(count, "r").index
    ).copy()


def _period(
    frame: pd.DataFrame,
    bounds: list[str],
) -> pd.DataFrame:
    start, end = (pd.Timestamp(value) for value in bounds)
    return frame[
        frame["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ]


def _greedy_one_to_one_matches(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    tolerance_minutes: int,
) -> dict[int, tuple[int, float]]:
    tolerance = float(tolerance_minutes)
    edges: list[
        tuple[float, pd.Timestamp, pd.Timestamp, int, int]
    ] = []
    for trade_index, trade in trades.iterrows():
        same_side = oracle[oracle["side"].eq(trade["side"])]
        differences = (
            same_side["entry_time_utc"]
            - trade["entry_time_utc"]
        ).abs().dt.total_seconds() / 60.0
        for oracle_index, minutes in differences.items():
            if float(minutes) <= tolerance:
                edges.append(
                    (
                        float(minutes),
                        pd.Timestamp(trade["entry_time_utc"]),
                        pd.Timestamp(
                            oracle.loc[
                                oracle_index, "entry_time_utc"
                            ]
                        ),
                        int(trade_index),
                        int(oracle_index),
                    )
                )
    edges.sort()
    used_trades: set[int] = set()
    used_oracle: set[int] = set()
    matches: dict[int, tuple[int, float]] = {}
    for minutes, _, _, trade_index, oracle_index in edges:
        if (
            trade_index in used_trades
            or oracle_index in used_oracle
        ):
            continue
        matches[trade_index] = (oracle_index, minutes)
        used_trades.add(trade_index)
        used_oracle.add(oracle_index)
    return matches


def attach_oracle_matches(
    trades: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    oracle_cfg = config["oracle"]
    path = PACKAGE_ROOT / oracle_cfg["path"]
    if sha256_file(path) != oracle_cfg["sha256"]:
        raise RuntimeError("Evaluation-only oracle drift")
    oracle = pd.read_csv(path)
    required = {"regime", "side", "entry_time_utc"}
    if not required.issubset(oracle.columns):
        raise RuntimeError("Oracle schema drift")
    oracle = oracle[
        oracle["regime"].eq(oracle_cfg["required_regime"])
    ].copy()
    oracle["entry_time_utc"] = _utc_series(
        oracle["entry_time_utc"]
    )
    oracle = oracle.sort_values(
        ["entry_time_utc", "side"]
    ).reset_index(drop=True)
    tolerance = int(
        oracle_cfg["same_side_tolerance_minutes"]
    )
    matches_15 = _greedy_one_to_one_matches(
        trades,
        oracle,
        tolerance,
    )
    matches_exact = _greedy_one_to_one_matches(
        trades,
        oracle,
        0,
    )
    records: list[dict[str, Any]] = []
    for trade_index, trade in trades.iterrows():
        matched = matches_15.get(int(trade_index))
        exact = matches_exact.get(int(trade_index))
        records.append(
            {
                "trade_index": int(trade_index),
                "entry_time_utc": trade["entry_time_utc"],
                "side": trade["side"],
                "oracle_match_exact": exact is not None,
                "oracle_match_15m": matched is not None,
                "oracle_entry_time_utc": (
                    oracle.loc[
                        matched[0], "entry_time_utc"
                    ]
                    if matched is not None
                    else pd.NaT
                ),
                "absolute_minutes": (
                    float(matched[1])
                    if matched is not None
                    else np.nan
                ),
            }
        )
    match_frame = pd.DataFrame(records)
    exact_count = len(matches_exact)
    count_15 = len(matches_15)
    return match_frame, {
        "neutral_oracle_rows": int(len(oracle)),
        "executed_trades": int(len(trades)),
        "same_side_matches_exact": int(exact_count),
        "same_side_precision_exact": (
            float(exact_count / len(trades))
            if len(trades)
            else 0.0
        ),
        "same_side_recall_exact": (
            float(exact_count / len(oracle))
            if len(oracle)
            else 0.0
        ),
        "same_side_matches_15m": int(count_15),
        "same_side_precision_15m": (
            float(count_15 / len(trades))
            if len(trades)
            else 0.0
        ),
        "same_side_recall_15m": (
            float(count_15 / len(oracle))
            if len(oracle)
            else 0.0
        ),
        "one_to_one": True,
        "oracle_used_for_decisions": False,
    }


def summarize(
    trades: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    overall = payoff_metrics(trades)
    stressed = payoff_metrics(
        trades, "extra_half_pip_stress_r"
    )
    top_removed = payoff_metrics(remove_top_winners(trades))
    windows = {
        name: payoff_metrics(_period(trades, bounds))
        for name, bounds in config["windows"].items()
    }
    sides = {
        side: payoff_metrics(
            trades[trades["side"].eq(side)]
        )
        for side in ("LONG", "SHORT")
    }
    matches, oracle = attach_oracle_matches(trades, config)
    gates = config["performance_gates"]
    main_windows = config["chronological_window_names"]
    full_oos = ("OOS_2023", "OOS_2024", "OOS_2025")
    gate_results = {
        "minimum_executed_trades_total": overall["trades"]
        >= int(gates["minimum_executed_trades_total"]),
        "minimum_executed_trades_development": windows[
            "DEVELOPMENT_2019_2022"
        ]["trades"]
        >= int(gates["minimum_executed_trades_development"]),
        "minimum_executed_trades_each_full_oos_year": all(
            windows[name]["trades"]
            >= int(
                gates[
                    "minimum_executed_trades_each_full_oos_year"
                ]
            )
            for name in full_oos
        ),
        "minimum_executed_trades_2026h1": windows[
            "OOS_2026_H1"
        ]["trades"]
        >= int(gates["minimum_executed_trades_2026h1"]),
        "minimum_executed_trades_each_side": all(
            sides[side]["trades"]
            >= int(gates["minimum_executed_trades_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "overall_win_rate": float(
            gates["minimum_overall_win_rate"]
        )
        <= overall["win_rate"]
        <= float(gates["maximum_overall_win_rate"]),
        "overall_realized_payoff_ratio": float(
            gates["minimum_overall_realized_payoff_ratio"]
        )
        <= overall["realized_payoff_ratio"]
        <= float(
            gates["maximum_overall_realized_payoff_ratio"]
        ),
        "overall_profit_factor": overall["profit_factor"]
        >= float(gates["minimum_overall_profit_factor"]),
        "each_chronological_window_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                gates[
                    "minimum_profit_factor_each_chronological_window_exclusive"
                ]
            )
            for name in main_windows
        ),
        "each_side_profit_factor": all(
            sides[side]["profit_factor"]
            > float(
                gates[
                    "minimum_each_side_profit_factor_exclusive"
                ]
            )
            for side in ("LONG", "SHORT")
        ),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "extra_half_pip_profit_factor": stressed[
            "profit_factor"
        ]
        > float(
            gates[
                "minimum_extra_half_pip_profit_factor_exclusive"
            ]
        ),
        "top_5pct_winners_removed_profit_factor": top_removed[
            "profit_factor"
        ]
        > float(
            gates[
                "minimum_top_5pct_winners_removed_profit_factor_exclusive"
            ]
        ),
        "recent_six_month_profit_factor": windows[
            "LATEST_SIX_MONTHS"
        ]["profit_factor"]
        > float(
            gates[
                "minimum_recent_six_month_profit_factor_exclusive"
            ]
        ),
        "oracle_precision_15m": oracle[
            "same_side_precision_15m"
        ]
        >= float(
            gates["minimum_same_side_15m_oracle_precision"]
        ),
        "oracle_recall_15m": oracle[
            "same_side_recall_15m"
        ]
        >= float(gates["minimum_same_side_15m_oracle_recall"]),
    }
    passed = bool(all(gate_results.values()))
    return {
        "overall": overall,
        "extra_half_pip": stressed,
        "top_5pct_winners_removed": top_removed,
        "windows": windows,
        "by_side": sides,
        "oracle_resemblance": oracle,
        "gate_results": gate_results,
        "all_performance_gates_passed": passed,
    }, matches


def run_execution() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    config = load_config()
    candidates = load_candidates(config)
    m5 = load_eurusd_m5(config)
    trades, routing = execute_candidates(
        candidates, m5, config
    )
    summary, matches = summarize(trades, config)
    status = (
        "PERFORMANCE_GATES_PASS_REQUIRES_PROSPECTIVE_FREEZE"
        if summary["all_performance_gates_passed"]
        else "REJECTED_EXACT_TRANSFER_EXECUTION"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_0608_range_breakout_transfer_"
            "execution_result_v1"
        ),
        "status": status,
        "frozen_at_utc": config["frozen_at_utc"],
        "candidates": int(len(candidates)),
        "executed_trades": int(len(trades)),
        "routing_status_counts": {
            str(key): int(value)
            for key, value in routing[
                "status"
            ].value_counts().items()
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
        return {
            str(key): _safe(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


def write_result(
    result: dict[str, Any],
    artifacts: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            _safe(serialize(result)),
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


__all__ = [
    "_greedy_one_to_one_matches",
    "execute_candidates",
    "load_candidates",
    "load_config",
    "load_eurusd_m5",
    "payoff_metrics",
    "remove_top_winners",
    "run_execution",
    "simulate_one",
    "summarize",
    "verify_lock",
    "write_result",
]
