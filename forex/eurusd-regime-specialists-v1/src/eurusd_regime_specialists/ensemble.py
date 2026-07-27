from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    add_seed_indicators,
    is_quarantined,
    load_inputs,
    metric_block,
    remove_top_winners,
    serialize,
    sha256_file,
    walk_long_exit,
)


OWNERS = [
    "S1_COMPRESSION_REVERSION",
    "S2_SUPPORTIVE_PULLBACK",
    "S3_NEUTRAL_AUCTION",
    "S4_OPPOSING_CAPITULATION",
]


def load_ensemble_config() -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / "config" / "frozen_two_clock_ensemble.json").read_text(encoding="utf-8")
    )


def verify_ensemble_lock() -> dict[str, str]:
    lock = json.loads(
        (PACKAGE_ROOT / "EURUSD_TWO_CLOCK_ENSEMBLE_PREREG_2026_07_27.sha256.json").read_text(
            encoding="utf-8"
        )
    )
    if lock.get("locked_before_ensemble_outcome_inspection") is not True:
        raise RuntimeError("Ensemble lock does not assert pre-outcome status")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Ensemble preregistration hash mismatch: {relative}")
        checked[relative] = actual
    return checked


def aggregate_signal_bars(m5: pd.DataFrame, minutes: int) -> pd.DataFrame:
    columns = {
        "timestamp_ms": "first",
        "bid_open": "first",
        "bid_high": "max",
        "bid_low": "min",
        "bid_close": "last",
        "ask_open": "first",
        "ask_high": "max",
        "ask_low": "min",
        "ask_close": "last",
        "tick_count": "sum",
    }
    return m5.resample(f"{minutes}min", label="left", closed="left").agg(columns).dropna()


def seed_signals(m5: pd.DataFrame, seed_id: str, seed: dict[str, Any]) -> pd.DataFrame:
    minutes = int(seed["signal_timeframe_minutes"])
    bars = add_seed_indicators(aggregate_signal_bars(m5, minutes), seed)
    if seed["mode"] == "RSI_EXTREME_BELOW_MID":
        condition = (
            (bars["rsi"] <= float(seed["rsi_oversold"]))
            & (bars["bid_close"] < bars["bb_mid"])
        )
    elif seed["mode"] == "RSI_CLOSE_BELOW_LOWER_BAND":
        condition = (
            (bars["rsi"] <= float(seed["rsi_oversold"]))
            & (bars["bid_close"] <= bars["bb_lower"])
        )
    else:
        raise ValueError(f"Unknown seed mode: {seed['mode']}")
    chosen = bars[
        condition & bars["atr"].notna() & bars["recent_low"].notna()
    ].copy()
    chosen["seed_id"] = seed_id
    chosen["signal_time_utc"] = chosen.index
    chosen["completion_time_utc"] = chosen.index + pd.Timedelta(minutes=minutes)
    chosen["state_time_utc"] = chosen["completion_time_utc"].dt.floor("h") - pd.Timedelta(hours=1)
    for name in (
        "stop_atr_multiple",
        "stop_floor_pips",
        "stop_ceiling_pips",
        "target_r",
    ):
        chosen[name] = float(seed[name])
    return chosen


def generate_ensemble_signals(
    m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    raw = pd.concat(
        [seed_signals(m5, seed_id, seed) for seed_id, seed in cfg["seeds"].items()],
        ignore_index=True,
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
    states["matched_state_time_utc"] = states["matched_state_time_utc"].dt.as_unit("ns")
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
    joined.loc[compression, "owner"] = "S1_COMPRESSION_REVERSION"
    remaining = nonshock & ~compression
    joined.loc[remaining & joined["direction"].eq("USD_DOWN"), "owner"] = "S2_SUPPORTIVE_PULLBACK"
    joined.loc[remaining & joined["direction"].eq("NEUTRAL"), "owner"] = "S3_NEUTRAL_AUCTION"
    opposing = remaining & joined["direction"].eq("USD_UP")
    joined.loc[
        opposing & joined["seed_id"].eq("DEEP_M30_RSI_BB"), "owner"
    ] = "S4_OPPOSING_CAPITULATION"
    joined.loc[
        opposing & ~joined["seed_id"].eq("DEEP_M30_RSI_BB"), "owner"
    ] = "CASH_REGIME_SEED_NOT_OWNED"

    priority = {name: i for i, name in enumerate(cfg["same_timestamp_seed_priority"])}
    joined["seed_priority"] = joined["seed_id"].map(priority)
    owned = joined["owner"].isin(OWNERS)
    deduped_owned = (
        joined[owned]
        .sort_values(["completion_time_utc", "owner", "seed_priority"])
        .drop_duplicates(["completion_time_utc", "owner"], keep="first")
    )
    cash = joined[~owned]
    return pd.concat([deduped_owned, cash], ignore_index=True).sort_values(
        ["completion_time_utc", "seed_priority"]
    )


def ensemble_census(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    start = pd.Timestamp(cfg["data"]["start_utc"])
    end = pd.Timestamp(cfg["data"]["end_utc"])
    days = active_weekday_fx_days(m5, start, end)
    owned = signals[signals["owner"].isin(OWNERS)]
    windows = {}
    for name, (a, b) in cfg["windows"].items():
        windows[name] = int(
            (
                (owned["completion_time_utc"] >= pd.Timestamp(a))
                & (owned["completion_time_utc"] <= pd.Timestamp(b))
            ).sum()
        )
    result = {
        "active_days": days,
        "all_seed_signals_after_same_timestamp_dedup": int(len(signals)),
        "owned_raw_signals": int(len(owned)),
        "owned_signals_per_active_day": float(len(owned) / days),
        "active_day_coverage": float(
            owned["completion_time_utc"].dt.date.nunique() / days
        ),
        "by_owner": {
            owner: int((owned["owner"] == owner).sum()) for owner in OWNERS
        },
        "by_seed": {
            seed: int((owned["seed_id"] == seed).sum()) for seed in cfg["seeds"]
        },
        "by_window": windows,
    }
    gate = cfg["census_gate"]
    result["passed"] = (
        result["owned_signals_per_active_day"]
        >= gate["minimum_owned_raw_signals_per_active_day"]
        and result["active_day_coverage"] >= gate["minimum_active_day_coverage"]
        and all(
            count >= gate["minimum_owned_raw_signals_each_window"]
            for count in windows.values()
        )
    )
    return result


def simulate_stream(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    execution = cfg["execution"]
    priority = {name: i for i, name in enumerate(cfg["portfolio"]["priority"])}
    ordered = signals.copy()
    ordered["owner_priority"] = ordered["owner"].map(priority)
    ordered = ordered.sort_values(
        ["completion_time_utc", "owner_priority", "seed_priority"]
    )
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    entries_by_day: dict[str, int] = {}
    slip = float(execution["extra_slippage_pips_per_side"]) * PIP
    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    for _, signal in ordered.iterrows():
        pos = int(m5.index.searchsorted(signal["completion_time_utc"], side="left"))
        if pos >= len(m5):
            continue
        entry_time = m5.index[pos]
        if open_until is not None and entry_time <= open_until:
            continue
        if is_quarantined(entry_time, "EURUSD", cfg["quarantine"]):
            continue
        day = entry_time.strftime("%Y-%m-%d")
        if entries_by_day.get(day, 0) >= int(execution["max_trades_per_utc_day"]):
            continue
        bar = m5.iloc[pos]
        entry = max(
            float(bar["ask_open"]), float(bar["bid_open"]) + spread_floor
        ) + slip
        minimum = float(signal["stop_floor_pips"]) * PIP
        stop_distance = max(
            float(signal["stop_atr_multiple"]) * float(signal["atr"]), minimum
        )
        stop = min(float(signal["recent_low"]), entry - stop_distance)
        risk = entry - stop
        if risk > float(signal["stop_ceiling_pips"]) * PIP:
            continue
        target = entry + float(signal["target_r"]) * risk
        exit_time, exit_price, reason = walk_long_exit(
            m5, pos, stop, target, slip
        )
        r = (exit_price - entry) / risk
        records.append(
            {
                "specialist": signal["owner"],
                "seed_id": signal["seed_id"],
                "signal_time_utc": signal["signal_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": r,
                "extra_half_pip_stress_r": r - (0.5 * PIP / risk),
                "fixed_0p01_lot_usd": (exit_price - entry) * 1000.0,
            }
        )
        open_until = exit_time
        entries_by_day[day] = entries_by_day.get(day, 0) + 1
    return pd.DataFrame(records)


def summarize(trades: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    windows = {}
    for name, (a, b) in cfg["windows"].items():
        frame = trades[
            (trades["entry_time_utc"] >= pd.Timestamp(a))
            & (trades["entry_time_utc"] <= pd.Timestamp(b))
        ] if not trades.empty else trades
        windows[name] = metric_block(frame)
    overall = metric_block(trades)
    top_removed = metric_block(remove_top_winners(trades))
    stressed = metric_block(trades, "extra_half_pip_stress_r")
    admission = cfg["admission"]
    admitted = (
        all(
            block["trades"] >= admission["minimum_trades_each_window"]
            and block["profit_factor"]
            >= admission["minimum_profit_factor_each_window"]
            and block["expectancy_r"]
            > admission["minimum_expectancy_r_each_window"]
            for block in windows.values()
        )
        and overall["max_drawdown_r"]
        <= admission["maximum_drawdown_r_overall"]
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    return {
        "admitted": admitted,
        "status": "ADMITTED_RESEARCH_COMPONENT"
        if admitted
        else "REJECTED_STANDALONE",
        "overall": overall,
        "windows": windows,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
    }


def run_ensemble_backtest(
    signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    owned = signals[signals["owner"].isin(OWNERS)]
    owner_trades = {
        owner: simulate_stream(owned[owned["owner"].eq(owner)], m5, cfg)
        for owner in OWNERS
    }
    specialist_results = {
        owner: summarize(frame, cfg) for owner, frame in owner_trades.items()
    }
    admitted = [
        owner for owner in OWNERS if specialist_results[owner]["admitted"]
    ]
    portfolio_signals = owned[owned["owner"].isin(admitted)]
    portfolio = simulate_stream(portfolio_signals, m5, cfg)
    portfolio_summary = summarize(portfolio, cfg)
    start = pd.Timestamp(cfg["data"]["start_utc"])
    end = pd.Timestamp(cfg["data"]["end_utc"])
    frequency = len(portfolio) / active_weekday_fx_days(m5, start, end)
    portfolio_summary["actual_trades_per_active_day"] = frequency
    portfolio_summary["fixed_0p01_lot_usd"] = (
        float(portfolio["fixed_0p01_lot_usd"].sum())
        if not portfolio.empty
        else 0.0
    )
    gate = cfg["portfolio"]
    portfolio_pass = (
        bool(admitted)
        and portfolio_summary["overall"]["profit_factor"]
        >= gate["minimum_profit_factor"]
        and frequency >= gate["minimum_actual_trades_per_active_day"]
        and all(block["net_r"] > 0 for block in portfolio_summary["windows"].values())
    )
    portfolio_summary["portfolio_gate_passed"] = portfolio_pass
    portfolio_summary["status"] = "RESEARCH_PASS" if portfolio_pass else "REJECTED"

    recent_a, recent_b = map(pd.Timestamp, cfg["recent_six_months"])
    recent = portfolio[
        (portfolio["entry_time_utc"] >= recent_a)
        & (portfolio["entry_time_utc"] <= recent_b)
    ] if not portfolio.empty else portfolio
    recent_summary = metric_block(recent)
    recent_summary["fixed_0p01_lot_usd"] = (
        float(recent["fixed_0p01_lot_usd"].sum()) if not recent.empty else 0.0
    )
    recent_days = active_weekday_fx_days(m5, recent_a, recent_b)
    recent_summary["trades_per_active_day"] = len(recent) / recent_days
    recent_summary["monthly"] = {
        month: {
            **metric_block(frame),
            "fixed_0p01_lot_usd": float(frame["fixed_0p01_lot_usd"].sum()),
        }
        for month, frame in (
            recent.groupby(recent["entry_time_utc"].dt.strftime("%Y-%m"))
            if not recent.empty
            else []
        )
    }
    specialist_recent = {}
    for owner, frame in owner_trades.items():
        recent_owner = frame[
            (frame["entry_time_utc"] >= recent_a)
            & (frame["entry_time_utc"] <= recent_b)
        ] if not frame.empty else frame
        specialist_recent[owner] = {
            **metric_block(recent_owner),
            "fixed_0p01_lot_usd": (
                float(recent_owner["fixed_0p01_lot_usd"].sum())
                if not recent_owner.empty
                else 0.0
            ),
        }

    # Transparent counterfactual only: this is intentionally excluded from
    # admission and cannot be promoted after every owner failed its frozen gate.
    all_owner = simulate_stream(owned, m5, cfg)
    all_recent = all_owner[
        (all_owner["entry_time_utc"] >= recent_a)
        & (all_owner["entry_time_utc"] <= recent_b)
    ] if not all_owner.empty else all_owner
    all_owner_diagnostic = {
        "overall": metric_block(all_owner),
        "fixed_0p01_lot_usd": (
            float(all_owner["fixed_0p01_lot_usd"].sum())
            if not all_owner.empty
            else 0.0
        ),
        "recent_six_months": {
            **metric_block(all_recent),
            "fixed_0p01_lot_usd": (
                float(all_recent["fixed_0p01_lot_usd"].sum())
                if not all_recent.empty
                else 0.0
            ),
            "trades_per_active_day": len(all_recent) / recent_days,
            "monthly": {
                month: {
                    **metric_block(frame),
                    "fixed_0p01_lot_usd": float(
                        frame["fixed_0p01_lot_usd"].sum()
                    ),
                }
                for month, frame in (
                    all_recent.groupby(
                        all_recent["entry_time_utc"].dt.strftime("%Y-%m")
                    )
                    if not all_recent.empty
                    else []
                )
            },
        },
        "status": "DIAGNOSTIC_ONLY_NOT_ADMITTED",
    }
    result = {
        "specialists": specialist_results,
        "specialist_recent_six_months": specialist_recent,
        "admitted_specialists": admitted,
        "portfolio": portfolio_summary,
        "recent_six_months": recent_summary,
        "all_owner_diagnostic": all_owner_diagnostic,
    }
    owner_trades["PORTFOLIO"] = portfolio
    owner_trades["ALL_OWNER_DIAGNOSTIC"] = all_owner
    return result, owner_trades


def write_payload(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize(payload), indent=2), encoding="utf-8")
