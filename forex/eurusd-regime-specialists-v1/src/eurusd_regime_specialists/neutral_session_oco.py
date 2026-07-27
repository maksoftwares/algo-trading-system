from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_causal import oracle_match
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    load_inputs,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILY = "N13_NEUTRAL_SESSION_OCO_BREAKOUT"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_oco_breakout.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_SESSION_OCO_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_historical_outcome_pass") is not True:
        raise RuntimeError("Neutral session OCO contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral session OCO preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    return checked


def _effective_ask(
    bar: pd.Series, field: str, spread_floor: float
) -> float:
    return max(
        float(bar[f"ask_{field}"]),
        float(bar[f"bid_{field}"]) + spread_floor,
    )


def build_anchor_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    strategy = cfg["strategy"]
    anchor_hours = set(int(x) for x in strategy["anchor_hours_utc"])
    anchors = m5.index[
        (m5.index.minute == 0)
        & np.isin(m5.index.hour, list(anchor_hours))
        & (m5.index.weekday < 5)
    ]
    lookback = int(strategy["range_lookback_m5_bars"])
    records: list[dict[str, Any]] = []
    for anchor in anchors:
        position = int(m5.index.searchsorted(anchor, side="left"))
        if position < lookback:
            continue
        history = m5.iloc[position - lookback : position]
        expected_first = anchor - pd.Timedelta(minutes=5 * lookback)
        expected_last = anchor - pd.Timedelta(minutes=5)
        if (
            len(history) != lookback
            or history.index[0] != expected_first
            or history.index[-1] != expected_last
        ):
            continue
        records.append(
            {
                "family": FAMILY,
                "anchor_time_utc": anchor,
                "state_time_utc": anchor.floor("h")
                - pd.Timedelta(hours=1),
                "prior_range_high": float(history["bid_high"].max()),
                "prior_range_low": float(history["bid_low"].min()),
                "prior_range_pips": float(
                    (
                        history["bid_high"].max()
                        - history["bid_low"].min()
                    )
                    / PIP
                ),
            }
        )
    raw = pd.DataFrame(records)
    if raw.empty:
        return raw
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
        raw.sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    shock = joined["shock"].astype("boolean").fillna(True)
    compression = (
        joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined["neutral_eligible"] = (
        joined["direction"].eq(
            cfg["neutral_ownership"]["requires_direction"]
        )
        & ~shock
        & ~compression
    )
    return joined.sort_values("anchor_time_utc").reset_index(drop=True)


def _find_trigger(
    candidate: pd.Series,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    spread_floor: float,
    slippage: float,
) -> dict[str, Any]:
    strategy = cfg["strategy"]
    anchor = candidate["anchor_time_utc"]
    start = int(m5.index.searchsorted(anchor, side="left"))
    deadline = anchor + pd.Timedelta(
        minutes=float(strategy["pending_order_minutes"])
    )
    end = min(
        int(m5.index.searchsorted(deadline, side="left")),
        len(m5),
    )
    buffer_distance = float(strategy["entry_buffer_pips"]) * PIP
    buy_trigger = float(candidate["prior_range_high"]) + buffer_distance
    sell_trigger = float(candidate["prior_range_low"]) - buffer_distance
    for position in range(start, end):
        bar = m5.iloc[position]
        long_hit = (
            _effective_ask(bar, "high", spread_floor) >= buy_trigger
        )
        short_hit = float(bar["bid_low"]) <= sell_trigger
        if long_hit and short_hit:
            return {
                "trigger_status": "AMBIGUOUS_BOTH_SIDES_NO_TRADE",
                "trigger_time_utc": m5.index[position],
                "buy_trigger": buy_trigger,
                "sell_trigger": sell_trigger,
            }
        if long_hit:
            return {
                "trigger_status": "TRIGGERED",
                "trigger_time_utc": m5.index[position],
                "trigger_position": position,
                "side": "LONG",
                "entry_price": max(
                    _effective_ask(bar, "open", spread_floor),
                    buy_trigger,
                )
                + slippage,
                "buy_trigger": buy_trigger,
                "sell_trigger": sell_trigger,
            }
        if short_hit:
            return {
                "trigger_status": "TRIGGERED",
                "trigger_time_utc": m5.index[position],
                "trigger_position": position,
                "side": "SHORT",
                "entry_price": min(
                    float(bar["bid_open"]), sell_trigger
                )
                - slippage,
                "buy_trigger": buy_trigger,
                "sell_trigger": sell_trigger,
            }
    return {
        "trigger_status": "EXPIRED_NO_TRIGGER",
        "trigger_time_utc": pd.NaT,
        "buy_trigger": buy_trigger,
        "sell_trigger": sell_trigger,
    }


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
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    risk = float(execution["risk_pips"]) * PIP
    target_distance = float(execution["target_r"]) * risk
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    base = load_ensemble_config()
    open_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    diagnostics: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    eligible = candidates[candidates["neutral_eligible"]]
    for _, candidate in eligible.iterrows():
        anchor = candidate["anchor_time_utc"]
        if open_until is not None and anchor <= open_until:
            diagnostics.append(
                {
                    "anchor_time_utc": anchor,
                    "trigger_status": "SKIP_POSITION_OPEN",
                }
            )
            continue
        trigger = _find_trigger(
            candidate, m5, cfg, spread_floor, slippage
        )
        diagnostics.append(
            {
                "anchor_time_utc": anchor,
                "prior_range_pips": candidate["prior_range_pips"],
                **{
                    key: value
                    for key, value in trigger.items()
                    if key != "trigger_position"
                },
            }
        )
        if trigger["trigger_status"] != "TRIGGERED":
            continue
        entry_time = trigger["trigger_time_utc"]
        if is_quarantined(
            entry_time, "EURUSD", base["quarantine"]
        ):
            diagnostics[-1]["trigger_status"] = "SKIP_QUARANTINE"
            continue
        date = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(date, 0) >= int(
            strategy["maximum_trades_per_utc_day"]
        ):
            diagnostics[-1]["trigger_status"] = "SKIP_DAILY_CAP"
            continue
        entry = float(trigger["entry_price"])
        side = str(trigger["side"])
        if side == "LONG":
            stop = entry - risk
            target = entry + target_distance
        else:
            stop = entry + risk
            target = entry - target_distance
        exit_time, exit_price, reason = _walk_exit(
            m5,
            int(trigger["trigger_position"]),
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        pnl = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        result_r = pnl / risk
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "side": side,
                "anchor_time_utc": anchor,
                "state_time_utc": candidate["state_time_utc"],
                "matched_state_time_utc": candidate[
                    "matched_state_time_utc"
                ],
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
                "prior_range_pips": candidate["prior_range_pips"],
            }
        )
        open_until = exit_time
        daily_count[date] = daily_count.get(date, 0) + 1
    return pd.DataFrame(records), pd.DataFrame(diagnostics)


def _window(
    trades: pd.DataFrame, start: str, end: str
) -> pd.DataFrame:
    if trades.empty:
        return trades
    return trades[
        (trades["entry_time_utc"] >= pd.Timestamp(start))
        & (trades["entry_time_utc"] <= pd.Timestamp(end))
    ]


def summarize(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    windows = {
        name: payoff_metrics(_window(trades, start, end))
        for name, (start, end) in cfg["windows"].items()
    }
    overall = payoff_metrics(trades)
    top_removed = payoff_metrics(remove_top_winners(trades))
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    gate = cfg["admission"]
    admitted = (
        all(
            block["trades"] >= int(gate["minimum_trades_each_window"])
            and float(gate["minimum_win_rate"])
            <= block["win_rate"]
            <= float(gate["maximum_win_rate"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= block["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and block["profit_factor"]
            >= float(gate["minimum_profit_factor"])
            for block in windows.values()
        )
        and overall["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r"])
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    recent_start, recent_end = cfg["recent_six_months"]
    recent = _window(trades, recent_start, recent_end)
    recent_metrics = payoff_metrics(recent)
    recent_days = active_weekday_fx_days(
        m5, pd.Timestamp(recent_start), pd.Timestamp(recent_end)
    )
    recent_metrics["trades_per_weekday"] = (
        len(recent) / recent_days if recent_days else 0.0
    )
    return {
        "admitted": admitted,
        "overall": overall,
        "windows": windows,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
        "recent_six_months": recent_metrics,
    }


def run_neutral_session_oco() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    candidates = build_anchor_candidates(m5, state, cfg)
    trades, diagnostics = simulate(candidates, m5, cfg)
    summary = summarize(trades, m5, cfg)
    match, matches = oracle_match(trades, cfg)
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if summary["admitted"]
            else "REJECTED_NEUTRAL_SESSION_OCO_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "causality": {
            "direction": "first executable OCO side, not predicted",
            "regime": cfg["neutral_ownership"]["state"],
            "future_information_in_signal_or_execution": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "census": {
            "anchors": int(len(candidates)),
            "neutral_anchors": int(
                candidates["neutral_eligible"].sum()
            ),
            "triggered_trades": int(len(trades)),
            "trigger_status": {
                str(key): int(value)
                for key, value in diagnostics[
                    "trigger_status"
                ].value_counts().items()
            },
        },
        "strategy": summary,
        "oracle_imitation": match,
        "verdict": (
            "The fixed no-options OCO rule passed all gates; it still "
            "requires untouched prospective confirmation."
            if summary["admitted"]
            else "The fixed no-options OCO rule failed its frozen gates "
            "and is closed without repair."
        ),
    }
    return result, {
        "CANDIDATES": candidates,
        "TRIGGER_DIAGNOSTICS": diagnostics,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
