from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import aggregate_signal_bars, load_ensemble_config, load_inputs
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    add_seed_indicators,
    is_quarantined,
    remove_top_winners,
    serialize,
    sha256_file,
)


OWNERS = [
    "C1_COMPRESSION_REVERSAL",
    "C2_USD_ALIGNED_PULLBACK",
    "C3_NEUTRAL_REVERSAL",
    "C4_COUNTERTREND_EXHAUSTION",
]


def load_config() -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / "config" / "frozen_confirmed_reversal.json").read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_CONFIRMED_REVERSAL_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_confirmation_outcome_inspection") is not True:
        raise RuntimeError("Confirmed-reversal contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Confirmed-reversal lock mismatch: {relative}")
        checked[relative] = actual
    return checked


def generate_confirmations(
    m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    arm_cfg = cfg["arm"]
    seed = {
        "bands_period": arm_cfg["bands_period"],
        "bands_deviation": arm_cfg["bands_deviation"],
        "rsi_period": arm_cfg["rsi_period"],
        "atr_period": arm_cfg["atr_period"],
        "recent_low_bars": 6,
    }
    m15 = add_seed_indicators(
        aggregate_signal_bars(m5, int(arm_cfg["timeframe_minutes"])), seed
    )
    m15["bb_upper"] = 2.0 * m15["bb_mid"] - m15["bb_lower"]
    long_raw = (m15["rsi"] <= arm_cfg["rsi_long_maximum"]) & (
        m15["bid_close"] <= m15["bb_lower"]
    )
    short_raw = (m15["rsi"] >= arm_cfg["rsi_short_minimum"]) & (
        m15["bid_close"] >= m15["bb_upper"]
    )
    long_arms = m15[long_raw & ~long_raw.shift(1, fill_value=False)]
    short_arms = m15[short_raw & ~short_raw.shift(1, fill_value=False)]
    lookback = int(cfg["confirmation"]["structure_lookback_bars"])
    wait = pd.Timedelta(minutes=int(cfg["confirmation"]["maximum_wait_minutes"]))
    records = []
    for side, arms in (("LONG", long_arms), ("SHORT", short_arms)):
        for arm_time, arm in arms.iterrows():
            arm_complete = arm_time + pd.Timedelta(
                minutes=int(arm_cfg["timeframe_minutes"])
            )
            start = int(m5.index.searchsorted(arm_complete, side="left"))
            stop_at = arm_complete + wait
            end = min(
                int(m5.index.searchsorted(stop_at, side="left")), len(m5) - 1
            )
            confirmed = None
            for position in range(max(start, lookback), end + 1):
                bar = m5.iloc[position]
                prior = m5.iloc[position - lookback : position]
                if side == "LONG":
                    ok = (
                        float(bar["bid_close"]) > float(bar["bid_open"])
                        and float(bar["bid_close"]) > float(prior["bid_high"].max())
                    )
                else:
                    ok = (
                        float(bar["bid_close"]) < float(bar["bid_open"])
                        and float(bar["bid_close"]) < float(prior["bid_low"].min())
                    )
                if ok:
                    confirmed = position
                    break
            if confirmed is None:
                continue
            confirm_open = m5.index[confirmed]
            confirm_complete = confirm_open + pd.Timedelta(minutes=5)
            path = m5.loc[
                (m5.index >= arm_complete) & (m5.index <= confirm_open)
            ]
            records.append(
                {
                    "side": side,
                    "arm_time_utc": arm_time,
                    "confirmation_bar_utc": confirm_open,
                    "completion_time_utc": confirm_complete,
                    "state_time_utc": confirm_complete.floor("h")
                    - pd.Timedelta(hours=1),
                    "atr": float(arm["atr"]),
                    "arm_low": float(arm["bid_low"]),
                    "arm_high": float(arm["bid_high"]),
                    "path_low": float(path["bid_low"].min())
                    if not path.empty
                    else float(arm["bid_low"]),
                    "path_high": float(path["ask_high"].max())
                    if not path.empty
                    else float(arm["ask_high"]),
                }
            )
    raw = pd.DataFrame(records)
    if raw.empty:
        return raw
    raw = raw.sort_values(["completion_time_utc", "side"]).drop_duplicates(
        ["completion_time_utc", "side"], keep="first"
    )
    raw["state_time_utc"] = raw["state_time_utc"].dt.as_unit("ns")
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
        raw.sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    joined["owner"] = "CASH_MISSING_CONTEXT"
    valid = joined["direction"].notna()
    shock = valid & joined["shock"].astype("boolean").fillna(False)
    joined.loc[shock, "owner"] = "CASH_SHOCK"
    nonshock = valid & ~joined["shock"].astype("boolean").fillna(True)
    compression = (
        nonshock
        & joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined.loc[compression, "owner"] = "C1_COMPRESSION_REVERSAL"
    remaining = nonshock & ~compression
    aligned = remaining & (
        (joined["direction"].eq("USD_DOWN") & joined["side"].eq("LONG"))
        | (joined["direction"].eq("USD_UP") & joined["side"].eq("SHORT"))
    )
    joined.loc[aligned, "owner"] = "C2_USD_ALIGNED_PULLBACK"
    neutral = remaining & joined["direction"].eq("NEUTRAL")
    joined.loc[neutral, "owner"] = "C3_NEUTRAL_REVERSAL"
    joined.loc[remaining & ~aligned & ~neutral, "owner"] = (
        "C4_COUNTERTREND_EXHAUSTION"
    )
    return joined.sort_values("completion_time_utc").reset_index(drop=True)


def census(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    base = load_ensemble_config()
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    days = active_weekday_fx_days(m5, start, end)
    owned = signals[signals["owner"].isin(OWNERS)]
    windows = {
        name: int(
            (
                (owned["completion_time_utc"] >= pd.Timestamp(a))
                & (owned["completion_time_utc"] <= pd.Timestamp(b))
            ).sum()
        )
        for name, (a, b) in cfg["windows"].items()
    }
    result = {
        "weekday_count": days,
        "confirmed_signals": int(len(signals)),
        "owned_confirmations": int(len(owned)),
        "owned_confirmations_per_weekday": float(len(owned) / days),
        "weekday_coverage": float(
            owned["completion_time_utc"].dt.date.nunique() / days
        ),
        "by_owner": {
            owner: int((owned["owner"] == owner).sum()) for owner in OWNERS
        },
        "by_side": {
            side: int((owned["side"] == side).sum())
            for side in ("LONG", "SHORT")
        },
        "by_window": windows,
    }
    gate = cfg["census_gate"]
    result["passed"] = (
        result["owned_confirmations_per_weekday"]
        >= gate["minimum_owned_confirmations_per_weekday"]
        and result["weekday_coverage"] >= gate["minimum_weekday_coverage"]
        and all(
            count >= gate["minimum_owned_confirmations_each_window"]
            for count in windows.values()
        )
    )
    return result


def _effective_ask(bar: pd.Series, field: str, floor: float) -> float:
    raw = float(bar[f"ask_{field}"])
    bid = float(bar[f"bid_{field}"])
    return max(raw, bid + floor)


def walk_exit(
    m5: pd.DataFrame,
    start: int,
    deadline: pd.Timestamp,
    side: str,
    stop: float,
    target: float,
    spread_floor: float,
    slip: float,
) -> tuple[pd.Timestamp, float, str]:
    end = min(
        max(int(m5.index.searchsorted(deadline, side="right")) - 1, start),
        len(m5) - 1,
    )
    for position in range(start, end + 1):
        bar = m5.iloc[position]
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                return m5.index[position], min(float(bar["bid_open"]), stop) - slip, "STOP"
            if float(bar["bid_high"]) >= target:
                return m5.index[position], max(float(bar["bid_open"]), target) - slip, "TARGET"
        else:
            ask_high = _effective_ask(bar, "high", spread_floor)
            ask_low = _effective_ask(bar, "low", spread_floor)
            ask_open = _effective_ask(bar, "open", spread_floor)
            if ask_high >= stop:
                return m5.index[position], max(ask_open, stop) + slip, "STOP"
            if ask_low <= target:
                return m5.index[position], min(ask_open, target) + slip, "TARGET"
    bar = m5.iloc[end]
    if side == "LONG":
        return m5.index[end], float(bar["bid_close"]) - slip, "TIME_12H"
    return (
        m5.index[end],
        _effective_ask(bar, "close", spread_floor) + slip,
        "TIME_12H",
    )


def simulate(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    priority = {
        owner: i
        for i, owner in enumerate(cfg["portfolio_admission"]["priority"])
    }
    ordered = signals.copy()
    ordered["priority"] = ordered["owner"].map(priority)
    ordered = ordered.sort_values(["completion_time_utc", "priority"])
    spread_floor = cfg["execution"]["minimum_retail_spread_pips"] * PIP
    slip = cfg["execution"]["extra_slippage_pips_per_side"] * PIP
    records = []
    open_until = None
    for _, signal in ordered.iterrows():
        position = int(
            m5.index.searchsorted(signal["completion_time_utc"], side="left")
        )
        if position >= len(m5):
            continue
        entry_time = m5.index[position]
        if open_until is not None and entry_time <= open_until:
            continue
        if is_quarantined(
            entry_time, "EURUSD", load_ensemble_config()["quarantine"]
        ):
            continue
        side = signal["side"]
        bar = m5.iloc[position]
        if side == "LONG":
            entry = _effective_ask(bar, "open", spread_floor) + slip
        else:
            entry = float(bar["bid_open"]) - slip
        atr_stop = cfg["risk"]["stop_atr_multiple"] * float(signal["atr"])
        minimum = cfg["risk"]["stop_floor_pips"] * PIP
        distance = max(atr_stop, minimum)
        if side == "LONG":
            extreme = min(float(signal["arm_low"]), float(signal["path_low"]))
            stop = min(extreme, entry - distance)
            risk = entry - stop
            target = entry + cfg["risk"]["target_r"] * risk
        else:
            extreme = max(float(signal["arm_high"]), float(signal["path_high"]))
            stop = max(extreme, entry + distance)
            risk = stop - entry
            target = entry - cfg["risk"]["target_r"] * risk
        if risk <= 0 or risk > cfg["risk"]["stop_ceiling_pips"] * PIP:
            continue
        exit_time, exit_price, reason = walk_exit(
            m5,
            position,
            entry_time + pd.Timedelta(hours=cfg["risk"]["maximum_hold_hours"]),
            side,
            stop,
            target,
            spread_floor,
            slip,
        )
        pnl = exit_price - entry if side == "LONG" else entry - exit_price
        result_r = pnl / risk
        records.append(
            {
                "specialist": signal["owner"],
                "side": side,
                "arm_time_utc": signal["arm_time_utc"],
                "confirmation_time_utc": signal["completion_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": result_r,
                "extra_half_pip_stress_r": result_r - (0.5 * PIP / risk),
                "fixed_0p01_lot_usd": pnl * 1000.0,
            }
        )
        open_until = exit_time
    return pd.DataFrame(records)


def summarize(trades: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    gate = cfg["specialist_admission"]
    windows = {}
    for name, (a, b) in cfg["windows"].items():
        frame = (
            trades[
                (trades["entry_time_utc"] >= pd.Timestamp(a))
                & (trades["entry_time_utc"] <= pd.Timestamp(b))
            ]
            if not trades.empty
            else trades
        )
        windows[name] = payoff_metrics(frame)
    overall = payoff_metrics(trades)
    removed = payoff_metrics(remove_top_winners(trades))
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    admitted = (
        all(
            block["trades"] >= gate["minimum_trades_each_window"]
            and gate["minimum_win_rate"] <= block["win_rate"] <= gate["maximum_win_rate"]
            and gate["minimum_realized_payoff_ratio"]
            <= block["realized_payoff_ratio"]
            <= gate["maximum_realized_payoff_ratio"]
            and block["profit_factor"] >= gate["minimum_profit_factor"]
            and block["expectancy_r"] > gate["minimum_expectancy_r"]
            for block in windows.values()
        )
        and overall["max_drawdown_r"] <= gate["maximum_drawdown_r_overall"]
        and removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    return {
        "admitted": admitted,
        "status": "ADMITTED_RESEARCH_COMPONENT" if admitted else "REJECTED_STANDALONE",
        "overall": overall,
        "windows": windows,
        "top_5_percent_winners_removed": removed,
        "extra_half_pip_round_trip": stressed,
    }


def run_backtest(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    owned = signals[signals["owner"].isin(OWNERS)]
    trades = {
        owner: simulate(owned[owned["owner"].eq(owner)], m5, cfg)
        for owner in OWNERS
    }
    specialists = {owner: summarize(frame, cfg) for owner, frame in trades.items()}
    admitted = [owner for owner in OWNERS if specialists[owner]["admitted"]]
    portfolio = simulate(owned[owned["owner"].isin(admitted)], m5, cfg)
    forced = simulate(owned, m5, cfg)
    base = load_ensemble_config()
    full_days = active_weekday_fx_days(
        m5,
        pd.Timestamp(base["data"]["start_utc"]),
        pd.Timestamp(base["data"]["end_utc"]),
    )
    recent_a, recent_b = map(pd.Timestamp, cfg["recent_six_months"])
    recent_forced = forced[
        (forced["entry_time_utc"] >= recent_a)
        & (forced["entry_time_utc"] <= recent_b)
    ]
    result = {
        "specialists": specialists,
        "admitted_specialists": admitted,
        "portfolio": {
            **payoff_metrics(portfolio),
            "trades_per_weekday": len(portfolio) / full_days,
            "status": "REJECTED" if not admitted else "REQUIRES_PORTFOLIO_GATE_REVIEW",
        },
        "all_owner_diagnostic": {
            "status": "DIAGNOSTIC_ONLY",
            "overall": {
                **payoff_metrics(forced),
                "trades_per_weekday": len(forced) / full_days,
            },
            "recent_six_months": {
                **payoff_metrics(recent_forced),
                "trades_per_weekday": len(recent_forced)
                / active_weekday_fx_days(m5, recent_a, recent_b),
                "fixed_0p01_lot_usd": float(
                    recent_forced["fixed_0p01_lot_usd"].sum()
                ),
            },
        },
    }
    trades["PORTFOLIO"] = portfolio
    trades["ALL_OWNER_DIAGNOSTIC"] = forced
    return result, trades


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize(payload), indent=2), encoding="utf-8")
