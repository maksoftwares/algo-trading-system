from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILIES = [
    "N1_ROLLING_SWEEP_FADE",
    "N2_ASIA_RANGE_FADE",
    "N3_ANCHOR_REVERSION",
    "N4_MICRO_BREAKOUT",
]


def load_config() -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / "config" / "frozen_neutral_causal.json").read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_CAUSAL_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_neutral_candidate_outcome_inspection") is not True:
        raise RuntimeError("Neutral causal contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Neutral causal preregistration mismatch: {relative}")
        checked[relative] = actual
    return checked


def add_causal_features(
    m5: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    feature_cfg = cfg["features"]
    frame = m5.copy()
    close = frame["bid_close"].astype(float)
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous_close).abs(),
            (frame["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_bars = int(feature_cfg["atr_bars"])
    frame["atr"] = true_range.rolling(
        atr_bars, min_periods=atr_bars
    ).mean()
    extreme_bars = int(feature_cfg["rolling_extreme_bars"])
    frame["prior_high"] = (
        frame["bid_high"]
        .shift(1)
        .rolling(extreme_bars, min_periods=extreme_bars)
        .max()
    )
    frame["prior_low"] = (
        frame["bid_low"]
        .shift(1)
        .rolling(extreme_bars, min_periods=extreme_bars)
        .min()
    )
    median_bars = int(feature_cfg["tick_median_bars"])
    frame["prior_tick_median"] = (
        frame["tick_count"]
        .shift(1)
        .rolling(median_bars, min_periods=median_bars)
        .median()
    )
    frame["tick_ratio"] = (
        frame["tick_count"] / frame["prior_tick_median"].replace(0, np.nan)
    )
    frame["ema_fast"] = close.ewm(
        span=int(feature_cfg["ema_fast_bars"]), adjust=False
    ).mean()
    frame["ema_slow"] = close.ewm(
        span=int(feature_cfg["ema_slow_bars"]), adjust=False
    ).mean()
    bar_range = (frame["bid_high"] - frame["bid_low"]).replace(0, np.nan)
    frame["close_location"] = (
        (frame["bid_close"] - frame["bid_low"]) / bar_range
    ).fillna(0.5)
    utc_date = pd.Series(frame.index.strftime("%Y-%m-%d"), index=frame.index)
    asia_cfg = cfg["families"]["N2_ASIA_RANGE_FADE"]
    asia_mask = (
        (frame.index.hour >= int(asia_cfg["asian_start_hour_utc"]))
        & (frame.index.hour < int(asia_cfg["asian_end_hour_utc"]))
    )
    asia = (
        frame.loc[asia_mask]
        .assign(utc_date=utc_date.loc[asia_mask])
        .groupby("utc_date")
        .agg(
            asia_high=("bid_high", "max"),
            asia_low=("bid_low", "min"),
        )
    )
    frame["utc_date"] = utc_date
    frame["asia_high"] = utc_date.map(asia["asia_high"])
    frame["asia_low"] = utc_date.map(asia["asia_low"])
    return frame


def _episode_records(
    features: pd.DataFrame,
    condition: pd.Series,
    family: str,
    side: str,
) -> list[dict[str, Any]]:
    first = condition.fillna(False) & ~condition.fillna(False).shift(
        1, fill_value=False
    )
    records = []
    for timestamp, row in features.loc[first].iterrows():
        records.append(
            {
                "family": family,
                "side": side,
                "signal_time_utc": timestamp,
                "completion_time_utc": timestamp + pd.Timedelta(minutes=5),
                "state_time_utc": (
                    timestamp + pd.Timedelta(minutes=5)
                ).floor("h")
                - pd.Timedelta(hours=1),
                "signal_atr": float(row["atr"]),
                "tick_ratio": float(row["tick_ratio"]),
                "close_location": float(row["close_location"]),
            }
        )
    return records


def generate_candidates(
    m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = add_causal_features(m5, cfg)
    complete = (
        frame["atr"].notna()
        & frame["prior_high"].notna()
        & frame["prior_low"].notna()
        & frame["tick_ratio"].notna()
    )
    records: list[dict[str, Any]] = []

    sweep = cfg["families"]["N1_ROLLING_SWEEP_FADE"]
    sweep_location = float(sweep["close_location_minimum"])
    sweep_ticks = frame["tick_ratio"] >= float(sweep["minimum_tick_ratio"])
    records.extend(
        _episode_records(
            frame,
            complete
            & sweep_ticks
            & (frame["bid_low"] < frame["prior_low"])
            & (frame["bid_close"] > frame["prior_low"])
            & (frame["close_location"] >= sweep_location),
            "N1_ROLLING_SWEEP_FADE",
            "LONG",
        )
    )
    records.extend(
        _episode_records(
            frame,
            complete
            & sweep_ticks
            & (frame["bid_high"] > frame["prior_high"])
            & (frame["bid_close"] < frame["prior_high"])
            & (frame["close_location"] <= 1.0 - sweep_location),
            "N1_ROLLING_SWEEP_FADE",
            "SHORT",
        )
    )

    asia = cfg["families"]["N2_ASIA_RANGE_FADE"]
    in_asia_trade_window = (
        (frame.index.hour >= int(asia["trade_start_hour_utc"]))
        & (frame.index.hour < int(asia["trade_end_hour_utc"]))
    )
    asia_location = float(asia["close_location_minimum"])
    asia_ticks = frame["tick_ratio"] >= float(asia["minimum_tick_ratio"])
    asia_complete = (
        complete
        & in_asia_trade_window
        & frame["asia_high"].notna()
        & frame["asia_low"].notna()
        & asia_ticks
    )
    records.extend(
        _episode_records(
            frame,
            asia_complete
            & (frame["bid_low"] < frame["asia_low"])
            & (frame["bid_close"] > frame["asia_low"])
            & (frame["close_location"] >= asia_location),
            "N2_ASIA_RANGE_FADE",
            "LONG",
        )
    )
    records.extend(
        _episode_records(
            frame,
            asia_complete
            & (frame["bid_high"] > frame["asia_high"])
            & (frame["bid_close"] < frame["asia_high"])
            & (frame["close_location"] <= 1.0 - asia_location),
            "N2_ASIA_RANGE_FADE",
            "SHORT",
        )
    )

    anchor = cfg["families"]["N3_ANCHOR_REVERSION"]
    anchor_location = float(anchor["close_location_minimum"])
    anchor_deviation = float(anchor["minimum_atr_deviation"])
    anchor_ticks = frame["tick_ratio"] >= float(anchor["minimum_tick_ratio"])
    records.extend(
        _episode_records(
            frame,
            complete
            & anchor_ticks
            & (
                frame["bid_close"]
                <= frame["ema_slow"] - anchor_deviation * frame["atr"]
            )
            & (frame["bid_close"] > frame["bid_open"])
            & (frame["close_location"] >= anchor_location),
            "N3_ANCHOR_REVERSION",
            "LONG",
        )
    )
    records.extend(
        _episode_records(
            frame,
            complete
            & anchor_ticks
            & (
                frame["bid_close"]
                >= frame["ema_slow"] + anchor_deviation * frame["atr"]
            )
            & (frame["bid_close"] < frame["bid_open"])
            & (frame["close_location"] <= 1.0 - anchor_location),
            "N3_ANCHOR_REVERSION",
            "SHORT",
        )
    )

    breakout = cfg["families"]["N4_MICRO_BREAKOUT"]
    breakout_location = float(breakout["close_location_minimum"])
    breakout_ticks = (
        frame["tick_ratio"] >= float(breakout["minimum_tick_ratio"])
    )
    records.extend(
        _episode_records(
            frame,
            complete
            & breakout_ticks
            & (frame["bid_close"] > frame["prior_high"])
            & (frame["ema_fast"] > frame["ema_slow"])
            & (frame["close_location"] >= breakout_location),
            "N4_MICRO_BREAKOUT",
            "LONG",
        )
    )
    records.extend(
        _episode_records(
            frame,
            complete
            & breakout_ticks
            & (frame["bid_close"] < frame["prior_low"])
            & (frame["ema_fast"] < frame["ema_slow"])
            & (frame["close_location"] <= 1.0 - breakout_location),
            "N4_MICRO_BREAKOUT",
            "SHORT",
        )
    )

    raw = pd.DataFrame(records).sort_values(
        ["completion_time_utc", "family", "side"]
    )
    raw["state_time_utc"] = raw["state_time_utc"].dt.as_unit("ns")
    state_columns = [
        "direction",
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
        raw,
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    shock = joined["shock"].astype("boolean").fillna(True)
    joint_compression = (
        joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    eligible = (
        joined["direction"].eq("NEUTRAL") & ~shock & ~joint_compression
    )
    joined["neutral_eligible"] = eligible
    joined["regime"] = np.where(eligible, "NEUTRAL", "OTHER_OR_CASH")
    return joined.sort_values("completion_time_utc"), frame


def census(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    eligible = signals[signals["neutral_eligible"]]
    base = load_ensemble_config()
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    days = active_weekday_fx_days(m5, start, end)
    return {
        "raw_candidates": int(len(signals)),
        "neutral_candidates": int(len(eligible)),
        "neutral_candidates_per_weekday": float(len(eligible) / days),
        "neutral_candidate_weekday_coverage": float(
            eligible["completion_time_utc"].dt.date.nunique() / days
        ),
        "by_family": {
            family: int(eligible["family"].eq(family).sum())
            for family in FAMILIES
        },
        "by_side": {
            side: int(eligible["side"].eq(side).sum())
            for side in ("LONG", "SHORT")
        },
        "by_window": {
            name: int(
                (
                    (eligible["completion_time_utc"] >= pd.Timestamp(a))
                    & (eligible["completion_time_utc"] <= pd.Timestamp(b))
                ).sum()
            )
            for name, (a, b) in cfg["windows"].items()
        },
    }


def _effective_ask(bar: pd.Series, field: str, spread_floor: float) -> float:
    return max(
        float(bar[f"ask_{field}"]),
        float(bar[f"bid_{field}"]) + spread_floor,
    )


def walk_exit(
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
        max(int(m5.index.searchsorted(deadline, side="right")) - 1, start),
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
            ask_high = _effective_ask(bar, "high", spread_floor)
            ask_low = _effective_ask(bar, "low", spread_floor)
            ask_open = _effective_ask(bar, "open", spread_floor)
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
    bar = m5.iloc[end]
    if side == "LONG":
        return (
            m5.index[end],
            float(bar["bid_close"]) - slippage,
            "TIME_12H",
        )
    return (
        m5.index[end],
        _effective_ask(bar, "close", spread_floor) + slippage,
        "TIME_12H",
    )


def simulate(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    execution = cfg["execution"]
    priority = {
        family: index
        for index, family in enumerate(execution["family_priority"])
    }
    ordered = signals[signals["neutral_eligible"]].copy()
    ordered["family_priority"] = ordered["family"].map(priority)
    ordered = ordered.sort_values(
        ["completion_time_utc", "family_priority", "side"]
    )
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    risk = float(execution["risk_pips"]) * PIP
    target_distance = float(execution["target_r"]) * risk
    hold = pd.Timedelta(hours=float(execution["maximum_hold_hours"]))
    base = load_ensemble_config()
    records = []
    open_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    for _, signal in ordered.iterrows():
        position = int(
            m5.index.searchsorted(
                signal["completion_time_utc"], side="left"
            )
        )
        if position >= len(m5):
            continue
        entry_time = m5.index[position]
        if open_until is not None and entry_time <= open_until:
            continue
        if is_quarantined(
            entry_time, "EURUSD", base["quarantine"]
        ):
            continue
        date = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(date, 0) >= int(
            execution["max_trades_per_utc_day"]
        ):
            continue
        bar = m5.iloc[position]
        if signal["side"] == "LONG":
            entry = _effective_ask(bar, "open", spread_floor) + slippage
            stop = entry - risk
            target = entry + target_distance
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = entry + risk
            target = entry - target_distance
        exit_time, exit_price, reason = walk_exit(
            m5,
            position,
            entry_time + hold,
            signal["side"],
            stop,
            target,
            spread_floor,
            slippage,
        )
        pnl = (
            exit_price - entry
            if signal["side"] == "LONG"
            else entry - exit_price
        )
        result_r = pnl / risk
        records.append(
            {
                "family": signal["family"],
                "regime": "NEUTRAL",
                "side": signal["side"],
                "signal_time_utc": signal["signal_time_utc"],
                "completion_time_utc": signal["completion_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": result_r,
                "extra_half_pip_stress_r": (
                    result_r - 0.5 * PIP / risk
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
            }
        )
        open_until = exit_time
        daily_count[date] = daily_count.get(date, 0) + 1
    return pd.DataFrame(records)


def _window(
    trades: pd.DataFrame, start: str, end: str
) -> pd.DataFrame:
    if trades.empty:
        return trades
    return trades[
        (trades["entry_time_utc"] >= pd.Timestamp(start))
        & (trades["entry_time_utc"] <= pd.Timestamp(end))
    ]


def metrics_by_window(
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    return {
        name: payoff_metrics(_window(trades, start, end))
        for name, (start, end) in cfg["windows"].items()
    }


def selected_on_development(
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> bool:
    gate = cfg["development_selection"]
    windows = metrics_by_window(trades, cfg)
    return all(
        windows[name]["trades"]
        >= int(gate["minimum_trades_each_selection_window"])
        and windows[name]["profit_factor"]
        >= float(gate["minimum_profit_factor_each_selection_window"])
        and windows[name]["expectancy_r"]
        > float(gate["minimum_expectancy_r_each_selection_window"])
        for name in cfg["selection_windows"]
    )


def strategy_summary(
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    return {
        "overall": payoff_metrics(trades),
        "windows": metrics_by_window(trades, cfg),
        "top_5_percent_winners_removed": payoff_metrics(
            remove_top_winners(trades)
        ),
        "extra_half_pip_round_trip": payoff_metrics(
            trades, "extra_half_pip_stress_r"
        ),
    }


def final_admitted(
    summary: dict[str, Any], cfg: dict[str, Any]
) -> bool:
    gate = cfg["final_admission"]
    evaluation = [
        summary["windows"][name] for name in cfg["evaluation_windows"]
    ]
    return (
        all(
            block["trades"]
            >= int(gate["minimum_trades_each_evaluation_window"])
            and float(gate["minimum_win_rate"])
            <= block["win_rate"]
            <= float(gate["maximum_win_rate"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= block["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and block["profit_factor"]
            >= float(gate["minimum_profit_factor"])
            and block["expectancy_r"]
            > float(gate["minimum_expectancy_r"])
            for block in evaluation
        )
        and summary["overall"]["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r_overall"])
        and summary["top_5_percent_winners_removed"]["net_r"] > 0
        and summary["extra_half_pip_round_trip"]["net_r"] > 0
    )


def oracle_match(
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> tuple[dict[str, Any], pd.DataFrame]:
    oracle_path = (
        PACKAGE_ROOT
        / "outputs"
        / "retrospective_overfit"
        / "FULL_CALENDAR_PERFECT_FORESIGHT_TRADES.csv"
    )
    oracle = pd.read_csv(
        oracle_path,
        parse_dates=["entry_time_utc", "exit_time_utc"],
    )
    oracle = oracle[oracle["regime"].eq("NEUTRAL")].copy()
    oracle["utc_date"] = oracle["entry_time_utc"].dt.strftime("%Y-%m-%d")
    if trades.empty:
        return (
            {
                "causal_trades": 0,
                "neutral_oracle_trades": int(len(oracle)),
                "matched_trades": 0,
                "precision": 0.0,
                "recall": 0.0,
                "median_absolute_difference_minutes": None,
            },
            pd.DataFrame(
                columns=[
                    "causal_trade_index",
                    "family",
                    "side",
                    "causal_entry_time_utc",
                    "oracle_entry_time_utc",
                    "absolute_difference_minutes",
                ]
            ),
        )
    tolerance = pd.Timedelta(
        minutes=float(
            cfg["oracle_matching"][
                "maximum_absolute_entry_time_difference_minutes"
            ]
        )
    )
    used: set[int] = set()
    matches = []
    for trade_index, trade in trades.sort_values(
        "entry_time_utc"
    ).iterrows():
        date = trade["entry_time_utc"].strftime("%Y-%m-%d")
        candidates = oracle[
            oracle["utc_date"].eq(date)
            & oracle["side"].eq(trade["side"])
            & ~oracle.index.isin(used)
        ]
        if candidates.empty:
            continue
        differences = (
            candidates["entry_time_utc"] - trade["entry_time_utc"]
        ).abs()
        oracle_index = int(differences.idxmin())
        difference = differences.loc[oracle_index]
        if difference > tolerance:
            continue
        used.add(oracle_index)
        matches.append(
            {
                "causal_trade_index": int(trade_index),
                "family": trade["family"],
                "side": trade["side"],
                "causal_entry_time_utc": trade["entry_time_utc"],
                "oracle_entry_time_utc": oracle.loc[
                    oracle_index, "entry_time_utc"
                ],
                "absolute_difference_minutes": (
                    difference.total_seconds() / 60.0
                ),
            }
        )
    match_frame = pd.DataFrame(matches)
    return (
        {
            "causal_trades": int(len(trades)),
            "neutral_oracle_trades": int(len(oracle)),
            "matched_trades": int(len(match_frame)),
            "precision": (
                float(len(match_frame) / len(trades))
                if len(trades)
                else 0.0
            ),
            "recall": (
                float(len(match_frame) / len(oracle))
                if len(oracle)
                else 0.0
            ),
            "median_absolute_difference_minutes": (
                float(match_frame["absolute_difference_minutes"].median())
                if not match_frame.empty
                else None
            ),
        },
        match_frame,
    )


def _recent_summary(
    trades: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    start, end = cfg["recent_six_months"]
    recent = _window(trades, start, end)
    block = payoff_metrics(recent)
    block["trades_per_weekday"] = len(recent) / active_weekday_fx_days(
        m5, pd.Timestamp(start), pd.Timestamp(end)
    )
    block["fixed_0p01_lot_usd"] = (
        float(recent["fixed_0p01_lot_usd"].sum())
        if not recent.empty
        else 0.0
    )
    return block


def _yearly(trades: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if trades.empty:
        return {}
    return {
        str(year): payoff_metrics(frame)
        for year, frame in trades.groupby(trades["entry_time_utc"].dt.year)
    }


def run_neutral_causal() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    signals, _ = generate_candidates(m5, state, cfg)
    eligible = signals[signals["neutral_eligible"]].copy()
    family_trades = {
        family: simulate(
            eligible[eligible["family"].eq(family)], m5, cfg
        )
        for family in FAMILIES
    }
    selected = [
        family
        for family in FAMILIES
        if selected_on_development(family_trades[family], cfg)
    ]
    selected_signals = eligible[eligible["family"].isin(selected)]
    portfolio = simulate(selected_signals, m5, cfg)
    forced_all = simulate(eligible, m5, cfg)
    family_summaries = {
        family: {
            "selected_on_development": family in selected,
            **strategy_summary(frame, cfg),
        }
        for family, frame in family_trades.items()
    }
    portfolio_summary = strategy_summary(portfolio, cfg)
    admitted = bool(selected) and final_admitted(portfolio_summary, cfg)
    portfolio_match, portfolio_matches = oracle_match(portfolio, cfg)
    forced_match, forced_matches = oracle_match(forced_all, cfg)
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    active_days = active_weekday_fx_days(m5, start, end)
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_CAUSAL_V1"
        ),
        "information_status": cfg["information_status"],
        "causality": {
            "regime": (
                "Latest available state no later than completion-hour "
                "minus one hour"
            ),
            "signal": "Completed M5 bars only",
            "entry": "First M5 open after signal completion",
            "oracle_usage": cfg["oracle_usage"],
            "future_information_in_execution": False,
        },
        "source_manifests": manifests,
        "census": census(signals, m5, cfg),
        "selected_on_development": selected,
        "families": family_summaries,
        "portfolio": {
            "admitted": admitted,
            "active_weekdays": active_days,
            "trades_per_weekday": (
                len(portfolio) / active_days if active_days else 0.0
            ),
            **portfolio_summary,
            "recent_six_months": _recent_summary(
                portfolio, m5, cfg
            ),
            "yearly": _yearly(portfolio),
            "oracle_imitation": portfolio_match,
        },
        "forced_all_family_diagnostic": {
            "status": "DIAGNOSTIC_NOT_SELECTION_ELIGIBLE",
            "trades_per_weekday": (
                len(forced_all) / active_days if active_days else 0.0
            ),
            **strategy_summary(forced_all, cfg),
            "recent_six_months": _recent_summary(
                forced_all, m5, cfg
            ),
            "yearly": _yearly(forced_all),
            "oracle_imitation": forced_match,
        },
        "verdict": (
            "Passes the frozen causal and stability gates; prospective "
            "forward evidence is still required."
            if admitted
            else "No development-selected Neutral combination passed all "
            "frozen chronological and robustness gates."
        ),
    }
    artifacts = {
        "SIGNALS": signals,
        **{
            f"{family}_TRADES": frame
            for family, frame in family_trades.items()
        },
        "SELECTED_PORTFOLIO_TRADES": portfolio,
        "FORCED_ALL_FAMILY_TRADES": forced_all,
        "SELECTED_PORTFOLIO_ORACLE_MATCHES": portfolio_matches,
        "FORCED_ALL_FAMILY_ORACLE_MATCHES": forced_matches,
    }
    return result, artifacts


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
