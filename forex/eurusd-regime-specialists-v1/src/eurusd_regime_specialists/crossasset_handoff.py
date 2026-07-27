from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .confirmed_reversal import walk_exit
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


OWNERS = ["X1_LONDON_CROSSASSET_HANDOFF", "X2_NEWYORK_CROSSASSET_HANDOFF"]


def load_config() -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / "config" / "frozen_crossasset_handoff.json").read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_CROSSASSET_HANDOFF_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_crossasset_handoff_outcome_inspection") is not True:
        raise RuntimeError("Cross-asset handoff contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Cross-asset handoff lock mismatch: {relative}")
        checked[relative] = actual
    return checked


def generate_signals(
    m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    signal_cfg = cfg["signal"]
    seed = {
        "bands_period": 20,
        "bands_deviation": 2.0,
        "rsi_period": 14,
        "atr_period": signal_cfg["atr_period"],
        "recent_low_bars": 6,
    }
    m15 = add_seed_indicators(
        aggregate_signal_bars(m5, signal_cfg["timeframe_minutes"]), seed
    )
    m15["utc_date"] = pd.Series(m15.index.date, index=m15.index)
    m15["hour"] = m15.index.hour
    candidates = []
    for owner, spec in cfg["specialists"].items():
        reference = m15[m15["hour"].isin(spec["reference_hours_utc"])]
        ranges = reference.groupby("utc_date").agg(
            reference_high=("bid_high", "max"),
            reference_low=("bid_low", "min"),
            reference_bars=("bid_close", "size"),
        )
        decision = m15[m15["hour"].isin(spec["decision_hours_utc"])].copy()
        decision = decision.join(ranges, on="utc_date")
        expected_bars = len(spec["reference_hours_utc"]) * 4
        decision = decision[decision["reference_bars"] >= expected_bars]
        buffer = signal_cfg["breakout_buffer_atr"] * decision["atr"]
        decision["long_break"] = (
            decision["bid_close"] > decision["reference_high"] + buffer
        )
        decision["short_break"] = (
            decision["bid_close"] < decision["reference_low"] - buffer
        )
        for side, column in (("LONG", "long_break"), ("SHORT", "short_break")):
            subset = decision[decision[column] & decision["atr"].notna()].copy()
            subset["specialist"] = owner
            subset["side"] = side
            subset["signal_bar_utc"] = subset.index
            subset["completion_time_utc"] = subset.index + pd.Timedelta(minutes=15)
            subset["state_time_utc"] = (
                subset["completion_time_utc"].dt.floor("h")
                - pd.Timedelta(hours=1)
            )
            candidates.append(subset)
    raw = pd.concat(candidates, ignore_index=True)
    raw["state_time_utc"] = raw["state_time_utc"].dt.as_unit("ns")
    context = state.copy()
    lookback = int(signal_cfg["dxy_impulse_lookback_h1"])
    context["DXY_prior_high"] = (
        context["DXY_high"].rolling(lookback, min_periods=lookback).max().shift(1)
    )
    context["DXY_prior_low"] = (
        context["DXY_low"].rolling(lookback, min_periods=lookback).min().shift(1)
    )
    columns = [
        "direction",
        "phase",
        "shock",
        "DXY_close",
        "DXY_prior_high",
        "DXY_prior_low",
    ]
    context = (
        context[columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    context["matched_state_time_utc"] = context[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    joined = pd.merge_asof(
        raw.sort_values("state_time_utc"),
        context,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    long_ok = (
        joined["side"].eq("LONG")
        & joined["direction"].eq("USD_DOWN")
        & (joined["DXY_close"] < joined["DXY_prior_low"])
    )
    short_ok = (
        joined["side"].eq("SHORT")
        & joined["direction"].eq("USD_UP")
        & (joined["DXY_close"] > joined["DXY_prior_high"])
    )
    joined = joined[
        ~joined["shock"].astype("boolean").fillna(True) & (long_ok | short_ok)
    ].copy()
    return (
        joined.sort_values(["completion_time_utc", "specialist"])
        .drop_duplicates(["utc_date", "specialist"], keep="first")
        .reset_index(drop=True)
    )


def census(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    base = load_ensemble_config()
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    days = active_weekday_fx_days(m5, start, end)
    windows = {
        name: int(
            (
                (signals["completion_time_utc"] >= pd.Timestamp(a))
                & (signals["completion_time_utc"] <= pd.Timestamp(b))
            ).sum()
        )
        for name, (a, b) in cfg["windows"].items()
    }
    result = {
        "weekday_count": days,
        "signals": int(len(signals)),
        "signals_per_weekday": float(len(signals) / days),
        "weekday_coverage": float(
            signals["completion_time_utc"].dt.date.nunique() / days
        ),
        "by_specialist": {
            owner: int((signals["specialist"] == owner).sum())
            for owner in OWNERS
        },
        "by_side": {
            side: int((signals["side"] == side).sum())
            for side in ("LONG", "SHORT")
        },
        "by_window": windows,
    }
    gate = cfg["census_gate"]
    result["passed"] = (
        result["signals_per_weekday"] >= gate["minimum_signals_per_weekday"]
        and result["weekday_coverage"] >= gate["minimum_weekday_coverage"]
        and all(
            count >= gate["minimum_signals_each_window"]
            for count in windows.values()
        )
    )
    return result


def _ask(bar: pd.Series, field: str, spread: float) -> float:
    return max(float(bar[f"ask_{field}"]), float(bar[f"bid_{field}"]) + spread)


def simulate(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    priority = {
        owner: i
        for i, owner in enumerate(cfg["portfolio_admission"]["priority"])
    }
    ordered = signals.copy()
    ordered["priority"] = ordered["specialist"].map(priority)
    ordered = ordered.sort_values(["completion_time_utc", "priority"])
    spread = cfg["execution"]["minimum_retail_spread_pips"] * PIP
    slip = cfg["execution"]["extra_slippage_pips_per_side"] * PIP
    base = load_ensemble_config()
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
        if is_quarantined(entry_time, "EURUSD", base["quarantine"]):
            continue
        side = signal["side"]
        bar = m5.iloc[position]
        entry = (
            _ask(bar, "open", spread) + slip
            if side == "LONG"
            else float(bar["bid_open"]) - slip
        )
        risk = max(
            cfg["risk"]["stop_atr_multiple"] * float(signal["atr"]),
            cfg["risk"]["stop_floor_pips"] * PIP,
        )
        if risk > cfg["risk"]["stop_ceiling_pips"] * PIP:
            continue
        if side == "LONG":
            stop = entry - risk
            target = entry + cfg["risk"]["target_r"] * risk
        else:
            stop = entry + risk
            target = entry - cfg["risk"]["target_r"] * risk
        exit_time, exit_price, reason = walk_exit(
            m5,
            position,
            entry_time + pd.Timedelta(hours=cfg["risk"]["maximum_hold_hours"]),
            side,
            stop,
            target,
            spread,
            slip,
        )
        pnl = exit_price - entry if side == "LONG" else entry - exit_price
        result_r = pnl / risk
        records.append(
            {
                "specialist": signal["specialist"],
                "side": side,
                "signal_time_utc": signal["signal_bar_utc"],
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
    trades = {
        owner: simulate(signals[signals["specialist"].eq(owner)], m5, cfg)
        for owner in OWNERS
    }
    specialists = {owner: summarize(frame, cfg) for owner, frame in trades.items()}
    admitted = [owner for owner in OWNERS if specialists[owner]["admitted"]]
    portfolio = simulate(
        signals[signals["specialist"].isin(admitted)], m5, cfg
    )
    forced = simulate(signals, m5, cfg)
    recent_a, recent_b = map(pd.Timestamp, cfg["recent_six_months"])
    recent = forced[
        (forced["entry_time_utc"] >= recent_a)
        & (forced["entry_time_utc"] <= recent_b)
    ]
    result = {
        "specialists": specialists,
        "admitted_specialists": admitted,
        "portfolio": {
            **payoff_metrics(portfolio),
            "status": "REJECTED" if not admitted else "REQUIRES_PORTFOLIO_GATE_REVIEW",
        },
        "all_specialist_diagnostic": {
            "status": "DIAGNOSTIC_ONLY",
            "overall": payoff_metrics(forced),
            "recent_six_months": {
                **payoff_metrics(recent),
                "fixed_0p01_lot_usd": float(recent["fixed_0p01_lot_usd"].sum()),
            },
        },
    }
    trades["PORTFOLIO"] = portfolio
    trades["ALL_SPECIALIST_DIAGNOSTIC"] = forced
    return result, trades


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize(payload), indent=2), encoding="utf-8")
