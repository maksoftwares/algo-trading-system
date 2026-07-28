from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd

from .adaptive_frequency_audit import match_oracle
from .asymmetric import payoff_metrics
from .ensemble import aggregate_signal_bars, load_ensemble_config
from .research import (
    PACKAGE_ROOT,
    PIP,
    add_seed_indicators,
    is_quarantined,
    load_inputs,
    serialize,
    sha256_file,
)


FAMILY = "N34_NEUTRAL_SYMMETRIC_RSI_1P5R"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_symmetric_rsi_1p5r"
PREREG_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_SYMMETRIC_RSI_1P5R_PREREG_2026_07_28.md"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_SYMMETRIC_RSI_1P5R_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_symmetric_rsi_1p5r.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("Symmetric RSI contract is not outcome-locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Symmetric RSI preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def _effective_ask(
    bar: pd.Series,
    field: str,
    spread_floor: float,
) -> float:
    return max(
        float(bar[f"ask_{field}"]),
        float(bar[f"bid_{field}"]) + spread_floor,
    )


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def build_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    minutes = int(strategy["signal_timeframe_minutes"])
    seed = {
        "bands_period": strategy["bands_period"],
        "bands_deviation": strategy["bands_deviation"],
        "rsi_period": strategy["rsi_period"],
        "atr_period": strategy["atr_period"],
        "recent_low_bars": strategy["recent_extreme_bars"],
    }
    bars = add_seed_indicators(
        aggregate_signal_bars(m5, minutes),
        seed,
    )
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    effective_ask_high = pd.concat(
        [
            bars["ask_high"],
            bars["bid_high"] + spread_floor,
        ],
        axis=1,
    ).max(axis=1)
    recent = int(strategy["recent_extreme_bars"])
    bars["recent_ask_high"] = effective_ask_high.rolling(
        recent, min_periods=recent
    ).max()
    ready = (
        bars["atr"].notna()
        & bars["recent_low"].notna()
        & bars["recent_ask_high"].notna()
        & bars["bb_mid"].notna()
        & bars["rsi"].notna()
    )
    long_signal = (
        ready
        & (bars["rsi"] <= float(strategy["long_rsi_maximum"]))
        & (bars["bid_close"] < bars["bb_mid"])
    )
    short_signal = (
        ready
        & (bars["rsi"] >= float(strategy["short_rsi_minimum"]))
        & (bars["bid_close"] > bars["bb_mid"])
    )
    selected = []
    for side, mask in (("LONG", long_signal), ("SHORT", short_signal)):
        frame = bars[mask].copy()
        frame["side"] = side
        selected.append(frame)
    raw = pd.concat(selected).sort_index()
    raw["signal_time_utc"] = raw.index
    raw["completion_time_utc"] = (
        raw.index + pd.Timedelta(minutes=minutes)
    )
    raw["state_time_utc"] = (
        raw["completion_time_utc"].dt.floor("h")
        - pd.Timedelta(hours=1)
    ).dt.as_unit("ns")
    state_columns = [
        "direction",
        "phase",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
    ]
    states = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    states["matched_state_time_utc"] = states[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    joined = pd.merge_asof(
        raw.reset_index(drop=True).sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    neutral = (
        joined["direction"].eq("NEUTRAL")
        & ~joined["shock"].astype("boolean").fillna(True)
        & ~(
            joined["DXY_compressed"].astype("boolean").fillna(False)
            & joined["EURUSD_compressed"]
            .astype("boolean")
            .fillna(False)
        )
    )
    candidates = joined[neutral].copy()
    candidates["family"] = FAMILY
    candidates["regime"] = "NEUTRAL"
    candidates["window"] = candidates["completion_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    quarantine = load_ensemble_config()["quarantine"]
    candidates = candidates[
        ~candidates["completion_time_utc"].map(
            lambda value: is_quarantined(
                value, "EURUSD", quarantine
            )
        )
    ]
    census = {
        "all_ready_long_signals": int(long_signal.sum()),
        "all_ready_short_signals": int(short_signal.sum()),
        "neutral_signals": int(len(candidates)),
        "neutral_by_side": {
            side: int((candidates["side"] == side).sum())
            for side in ("LONG", "SHORT")
        },
        "neutral_by_window": {
            name: int((candidates["window"] == name).sum())
            for name in cfg["windows"]
        },
    }
    gate = cfg["outcome_blind_census"]
    full_years = [
        name
        for name in cfg["windows"]
        if name != "recent_2026_h1"
    ]
    gate_results = {
        "total": (
            census["neutral_signals"]
            >= int(gate["minimum_neutral_signals_total"])
        ),
        "full_year_windows": all(
            census["neutral_by_window"][name]
            >= int(
                gate[
                    "minimum_neutral_signals_each_full_year_window"
                ]
            )
            for name in full_years
        ),
        "recent_half_year": (
            census["neutral_by_window"]["recent_2026_h1"]
            >= int(gate["minimum_neutral_signals_recent_half_year"])
        ),
        "both_directions": all(
            census["neutral_by_side"][side] > 0
            for side in ("LONG", "SHORT")
        ),
    }
    census["gate_results"] = gate_results
    census["passed"] = bool(all(gate_results.values()))
    return (
        candidates.sort_values(["completion_time_utc", "side"])
        .reset_index(drop=True),
        census,
    )


def _walk_exit(
    m5: pd.DataFrame,
    start: int,
    deadline: pd.Timestamp,
    side: str,
    stop: float,
    target: float,
    spread_floor: float,
    slippage: float,
) -> tuple[pd.Timestamp, float, str]:
    end = min(
        max(
            int(m5.index.searchsorted(deadline, side="right")) - 1,
            start,
        ),
        len(m5) - 1,
    )
    for position in range(start, end + 1):
        bar = m5.iloc[position]
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                return (
                    m5.index[position],
                    min(float(bar["bid_open"]), stop) - slippage,
                    "STOP",
                )
            if float(bar["bid_high"]) >= target:
                return (
                    m5.index[position],
                    max(float(bar["bid_open"]), target) - slippage,
                    "TARGET",
                )
        else:
            ask_open = _effective_ask(bar, "open", spread_floor)
            ask_high = _effective_ask(bar, "high", spread_floor)
            ask_low = _effective_ask(bar, "low", spread_floor)
            if ask_high >= stop:
                return (
                    m5.index[position],
                    max(ask_open, stop) + slippage,
                    "STOP",
                )
            if ask_low <= target:
                return (
                    m5.index[position],
                    min(ask_open, target) + slippage,
                    "TARGET",
                )
    final = m5.iloc[end]
    if side == "LONG":
        return (
            m5.index[end],
            float(final["bid_close"]) - slippage,
            "TIME_12H",
        )
    return (
        m5.index[end],
        _effective_ask(final, "close", spread_floor) + slippage,
        "TIME_12H",
    )


def execute(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    hold = pd.Timedelta(
        hours=float(strategy["maximum_hold_hours"])
    )
    records = []
    open_until: pd.Timestamp | None = None
    skipped_open = 0
    skipped_ceiling = 0
    for _, signal in candidates.sort_values(
        ["completion_time_utc", "side"]
    ).iterrows():
        position = int(
            m5.index.searchsorted(
                signal["completion_time_utc"], side="left"
            )
        )
        if position >= len(m5):
            continue
        entry_time = m5.index[position]
        if open_until is not None and entry_time <= open_until:
            skipped_open += 1
            continue
        bar = m5.iloc[position]
        side = str(signal["side"])
        floor = max(
            float(strategy["stop_atr_multiple"])
            * float(signal["atr"]),
            float(strategy["stop_floor_pips"]) * PIP,
        )
        if side == "LONG":
            entry = (
                max(
                    float(bar["ask_open"]),
                    float(bar["bid_open"]) + spread_floor,
                )
                + slippage
            )
            stop = min(
                float(signal["recent_low"]),
                entry - floor,
            )
            risk = entry - stop
            target = entry + float(strategy["target_r"]) * risk
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = max(
                float(signal["recent_ask_high"]),
                entry + floor,
            )
            risk = stop - entry
            target = entry - float(strategy["target_r"]) * risk
        risk_pips = risk / PIP
        if risk_pips > float(strategy["stop_ceiling_pips"]):
            skipped_ceiling += 1
            continue
        exit_time, exit_price, exit_reason = _walk_exit(
            m5,
            position,
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        signed_move = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        outcome_r = signed_move / risk
        stress_r = (
            outcome_r
            - float(execution["extra_round_trip_stress_pips"])
            / risk_pips
        )
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "side": side,
                "window": signal["window"],
                "signal_time_utc": signal["signal_time_utc"],
                "completion_time_utc": signal["completion_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": exit_reason,
                "risk_distance": risk,
                "risk_pips": risk_pips,
                "r": outcome_r,
                "extra_half_pip_stress_r": stress_r,
                "fixed_0p01_lot_usd": (
                    signed_move / PIP * 0.10
                ),
            }
        )
        open_until = exit_time
    columns = [
        "family",
        "regime",
        "side",
        "window",
        "signal_time_utc",
        "completion_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "entry_price",
        "stop_price",
        "target_price",
        "exit_price",
        "exit_reason",
        "risk_distance",
        "risk_pips",
        "r",
        "extra_half_pip_stress_r",
        "fixed_0p01_lot_usd",
    ]
    return (
        pd.DataFrame(records, columns=columns),
        {
            "candidate_signals": int(len(candidates)),
            "executed_trades": int(len(records)),
            "skipped_while_position_open": skipped_open,
            "skipped_stop_ceiling": skipped_ceiling,
        },
    )


def _top_removed(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    remove = int(math.ceil(len(trades) * 0.05))
    return trades.sort_values("r").iloc[:-remove].copy()


def load_oracle() -> pd.DataFrame:
    path = (
        PACKAGE_ROOT
        / "outputs"
        / "retrospective_overfit"
        / "FULL_CALENDAR_PERFECT_FORESIGHT_TRADES.csv"
    )
    oracle = pd.read_csv(path)
    for column in ("entry_time_utc", "exit_time_utc"):
        oracle[column] = pd.to_datetime(
            oracle[column], utc=True
        ).dt.as_unit("ns")
    return oracle[oracle["regime"].eq("NEUTRAL")].copy()


def oracle_metrics(
    trades: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    predictions = trades.rename(
        columns={
            "entry_time_utc": "entry_time",
            "family": "sleeve",
        }
    )
    oracle = load_oracle()
    exact = match_oracle(predictions, oracle, 0)
    tolerant = match_oracle(predictions, oracle, 15)
    return (
        {
            "oracle_trades": int(len(oracle)),
            "exact_matches": int(len(exact)),
            "exact_precision": (
                float(len(exact) / len(trades))
                if len(trades)
                else 0.0
            ),
            "exact_recall": float(len(exact) / len(oracle)),
            "same_side_15m_matches": int(len(tolerant)),
            "same_side_15m_precision": (
                float(len(tolerant) / len(trades))
                if len(trades)
                else 0.0
            ),
            "same_side_15m_recall": float(
                len(tolerant) / len(oracle)
            ),
        },
        tolerant,
    )


def summarize(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    overall = payoff_metrics(trades)
    windows = {
        name: payoff_metrics(trades[trades["window"].eq(name)])
        for name in cfg["windows"]
    }
    by_side = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    top_removed = payoff_metrics(_top_removed(trades))
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    oracle, matches = oracle_metrics(trades)
    gate = cfg["admission"]
    full_windows = [
        name for name in cfg["windows"] if name != "recent_2026_h1"
    ]
    gate_results = {
        "total_trades": (
            overall["trades"]
            >= int(gate["minimum_executed_trades_total"])
        ),
        "window_sample": (
            all(
                windows[name]["trades"]
                >= int(
                    gate[
                        "minimum_executed_trades_each_full_year_window"
                    ]
                )
                for name in full_windows
            )
            and windows["recent_2026_h1"]["trades"]
            >= int(gate["minimum_executed_trades_recent_half_year"])
        ),
        "win_rate": (
            float(gate["minimum_overall_win_rate"])
            <= overall["win_rate"]
            <= float(gate["maximum_overall_win_rate"])
        ),
        "payoff": (
            float(gate["minimum_overall_realized_payoff_ratio"])
            <= overall["realized_payoff_ratio"]
            <= float(gate["maximum_overall_realized_payoff_ratio"])
        ),
        "overall_profit_factor": (
            overall["profit_factor"]
            >= float(gate["minimum_overall_profit_factor"])
        ),
        "every_window_profitable": all(
            result["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            for result in windows.values()
        ),
        "both_sides": all(
            by_side[side]["trades"]
            >= int(gate["minimum_each_side_trades"])
            and by_side[side]["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "drawdown": (
            overall["max_drawdown_r"]
            <= float(gate["maximum_drawdown_r"])
        ),
        "top_winner_removal": (
            top_removed["profit_factor"]
            >= float(gate["minimum_top_5pct_removed_profit_factor"])
        ),
        "extra_half_pip": (
            stressed["profit_factor"]
            >= float(gate["minimum_extra_half_pip_profit_factor"])
        ),
        "oracle_precision": (
            oracle["same_side_15m_precision"]
            >= float(
                gate["minimum_same_side_15m_oracle_precision"]
            )
        ),
        "oracle_recall": (
            oracle["same_side_15m_recall"]
            >= float(gate["minimum_same_side_15m_oracle_recall"])
        ),
    }
    return (
        {
            "overall": overall,
            "windows": windows,
            "by_side": by_side,
            "top_5pct_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "oracle_resemblance": oracle,
            "gate_results": gate_results,
            "passed": bool(all(gate_results.values())),
        },
        matches,
    )


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    candidates, census = build_candidates(m5, state, cfg)
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_symmetric_rsi_1p5r_census_v1"
                ),
                "family": FAMILY,
                "status": (
                    "CENSUS_PASS_BACKTEST_ALLOWED"
                    if census["passed"]
                    else "CENSUS_FAIL_NO_PNL_ALLOWED"
                ),
                "census": census,
                "data_manifests": manifests,
            }
        ),
        candidates,
    )


def run_backtest() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    candidates, census = build_candidates(m5, state, cfg)
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L is forbidden")
    trades, execution = execute(candidates, m5, cfg)
    summary, matches = summarize(trades, cfg)
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if summary["passed"]
        else "REJECTED_NEUTRAL_SYMMETRIC_RSI_1P5R_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_symmetric_rsi_1p5r_result_v1"
        ),
        "family": FAMILY,
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "information_status": cfg["information_status"],
        "research_boundary": (
            "All archived windows are adaptive historical development data. "
            "Chronological labels do not make them pristine holdouts."
        ),
        "census": census,
        "execution": execution,
        "summary": summary,
        "data_manifests": manifests,
        "decision_policy": cfg["decision_policy"],
    }
    return (
        serialize(result),
        {
            "CANDIDATES": candidates,
            "TRADES": trades,
            "ORACLE_MATCHES_15M": matches,
        },
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "OUTPUT_ROOT",
    "_walk_exit",
    "build_candidates",
    "execute",
    "load_config",
    "run_backtest",
    "run_census",
    "summarize",
    "verify_lock",
    "write_json",
]
