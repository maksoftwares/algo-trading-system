from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
FOREX_ROOT = PACKAGE_ROOT.parent
SHARED_SRC = FOREX_ROOT / "fx-regime-specialists-gold-trajectory-v1" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

from fx_regime_specialists.campaign import (  # noqa: E402
    active_fx_days,
    aggregate_fx_h1,
    build_state_table,
    is_quarantined,
    load_context_h1,
    load_fx_m5,
    metric_block,
    remove_top_winners,
    serialize,
    sha256_file,
)


PIP = 0.0001
OWNERS = [
    "S1_JOINT_COMPRESSION_FADE",
    "S2_SUPPORTIVE_ESTABLISHED",
    "S3_SUPPORTIVE_TRANSITION",
    "S4_NEUTRAL_AUCTION",
    "S5_OPPOSING_CAPITULATION",
]


def active_weekday_fx_days(
    m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> int:
    """Count standard UTC Monday-Friday FX trading dates.

    A Sunday reopening fragment is part of Monday's FX session convention,
    not a standalone full trading day for a trades/day or coverage denominator.
    """
    eligible = m5.loc[(m5.index >= start) & (m5.index <= end)]
    return len({stamp.date() for stamp in eligible.index if stamp.weekday() < 5})


def load_config() -> dict[str, Any]:
    return json.loads((PACKAGE_ROOT / "config" / "frozen_research.json").read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads((PACKAGE_ROOT / "EURUSD_REGIME_SPECIALIST_PREREG_2026_07_27.sha256.json").read_text(encoding="utf-8"))
    if lock.get("locked_before_regime_outcome_inspection") is not True:
        raise RuntimeError("Lock does not assert pre-outcome status")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Preregistration hash mismatch: {relative}")
        checked[relative] = actual
    return checked


def wilder_average(values: pd.Series, period: int) -> pd.Series:
    raw = values.to_numpy(dtype=float)
    out = np.full(len(raw), np.nan)
    if len(raw) <= period:
        return pd.Series(out, index=values.index)
    initial = raw[1 : period + 1]
    if np.isfinite(initial).all():
        out[period] = initial.mean()
    for i in range(period + 1, len(raw)):
        if math.isfinite(out[i - 1]) and math.isfinite(raw[i]):
            out[i] = ((period - 1) * out[i - 1] + raw[i]) / period
    return pd.Series(out, index=values.index)


def add_seed_indicators(m30: pd.DataFrame, seed: dict[str, Any]) -> pd.DataFrame:
    frame = m30.copy()
    close = frame["bid_close"]
    period = int(seed["bands_period"])
    frame["bb_mid"] = close.rolling(period, min_periods=period).mean()
    std = close.rolling(period, min_periods=period).std(ddof=0)
    frame["bb_lower"] = frame["bb_mid"] - float(seed["bands_deviation"]) * std
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = wilder_average(gain, int(seed["rsi_period"]))
    avg_loss = wilder_average(loss, int(seed["rsi_period"]))
    rs = avg_gain / avg_loss
    frame["rsi"] = 100.0 - 100.0 / (1.0 + rs)
    frame.loc[(avg_loss == 0) & (avg_gain > 0), "rsi"] = 100.0
    frame.loc[(avg_loss == 0) & (avg_gain == 0), "rsi"] = 50.0
    previous = close.shift(1)
    tr = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous).abs(),
            (frame["bid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["atr"] = wilder_average(tr, int(seed["atr_period"]))
    recent = int(seed["recent_low_bars"])
    frame["recent_low"] = frame["bid_low"].rolling(recent, min_periods=recent).min()
    return frame


def aggregate_m30(m5: pd.DataFrame) -> pd.DataFrame:
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
    return m5.resample("30min", label="left", closed="left").agg(columns).dropna()


def load_inputs(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    start = pd.Timestamp(cfg["data"]["start_utc"])
    end = pd.Timestamp(cfg["data"]["end_utc"])
    bar_root = Path(cfg["data"]["fx_bar_root"])
    raw_root = Path(cfg["data"]["dukascopy_raw_root"])
    cache = PACKAGE_ROOT / "outputs" / "cache"
    m5_by_symbol = {
        symbol: load_fx_m5(bar_root, symbol, start, end)
        for symbol in ("EURUSD", "GBPUSD", "USDJPY")
    }
    dxy, dxy_manifest = load_context_h1(raw_root, "DOLLARIDXUSD", start, end, cache)
    bond, bond_manifest = load_context_h1(raw_root, "USTBONDTRUSD", start, end, cache)
    fx_h1 = {symbol: aggregate_fx_h1(frame) for symbol, frame in m5_by_symbol.items()}
    state = build_state_table(dxy, bond, fx_h1, cfg["classifier"])
    manifests = {"DXY": dxy_manifest, "BOND": bond_manifest}
    return m5_by_symbol["EURUSD"], state, manifests


def generate_raw_signals(m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    seed = cfg["seed"]
    m30 = add_seed_indicators(aggregate_m30(m5), seed)
    chosen = m30[
        (m30["bid_close"] <= m30["bb_lower"])
        & (m30["rsi"] <= float(seed["rsi_oversold"]))
        & m30["atr"].notna()
        & m30["recent_low"].notna()
    ].copy()
    chosen["signal_time_utc"] = chosen.index
    chosen["completion_time_utc"] = chosen.index + pd.Timedelta(minutes=30)
    chosen["state_time_utc"] = chosen["completion_time_utc"].dt.floor("h") - pd.Timedelta(hours=1)
    state_columns = [
        "direction",
        "phase",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
    ]
    # The contract calls for the latest fully completed state.  Cross-asset
    # archives do not print every UTC hour, so an exact timestamp join would
    # incorrectly turn ordinary session gaps into missing regimes.
    signal_order = chosen.reset_index(drop=True).sort_values("state_time_utc")
    signal_order["state_time_utc"] = signal_order["state_time_utc"].dt.as_unit("ns")
    state_order = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    state_order["matched_state_time_utc"] = state_order["matched_state_time_utc"].dt.as_unit("ns")
    joined = pd.merge_asof(
        signal_order,
        state_order,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    ).set_index("signal_time_utc", drop=False)
    joined["owner"] = "CASH_MISSING_CONTEXT"
    valid = joined["direction"].notna()
    joined.loc[valid & joined["shock"].astype("boolean").fillna(False), "owner"] = "CASH_SHOCK"
    nonshock = valid & ~joined["shock"].astype("boolean").fillna(True)
    compressed = (
        nonshock
        & joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined.loc[compressed, "owner"] = "S1_JOINT_COMPRESSION_FADE"
    remaining = nonshock & ~compressed
    joined.loc[
        remaining & joined["direction"].eq("USD_DOWN") & joined["phase"].eq("ESTABLISHED"),
        "owner",
    ] = "S2_SUPPORTIVE_ESTABLISHED"
    joined.loc[
        remaining & joined["direction"].eq("USD_DOWN") & ~joined["phase"].eq("ESTABLISHED"),
        "owner",
    ] = "S3_SUPPORTIVE_TRANSITION"
    joined.loc[remaining & joined["direction"].eq("NEUTRAL"), "owner"] = "S4_NEUTRAL_AUCTION"
    joined.loc[remaining & joined["direction"].eq("USD_UP"), "owner"] = "S5_OPPOSING_CAPITULATION"
    return joined


def opportunity_census(signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    start = pd.Timestamp(cfg["data"]["start_utc"])
    end = pd.Timestamp(cfg["data"]["end_utc"])
    days = active_weekday_fx_days(m5, start, end)
    owned = signals[signals["owner"].isin(OWNERS)].copy()
    owned_dates = set(owned["completion_time_utc"].dt.date)
    windows = {}
    for name, (a, b) in cfg["windows"].items():
        subset = owned[
            (owned["completion_time_utc"] >= pd.Timestamp(a))
            & (owned["completion_time_utc"] <= pd.Timestamp(b))
        ]
        windows[name] = int(len(subset))
    by_owner = {name: int((owned["owner"] == name).sum()) for name in OWNERS}
    gate = cfg["census_gate"]
    result = {
        "active_days": days,
        "raw_signals": int(len(signals)),
        "owned_raw_signals": int(len(owned)),
        "owned_signals_per_active_day": float(len(owned) / days),
        "active_day_coverage": float(len(owned_dates) / days),
        "by_owner": by_owner,
        "by_window": windows,
    }
    result["passed"] = (
        result["owned_signals_per_active_day"] >= gate["minimum_owned_raw_signals_per_active_day"]
        and result["active_day_coverage"] >= gate["minimum_active_day_coverage"]
        and all(count >= gate["minimum_owned_raw_signals_each_window"] for count in windows.values())
    )
    return result


def _next_position(index: pd.DatetimeIndex, timestamp: pd.Timestamp) -> int | None:
    pos = int(index.searchsorted(timestamp, side="left"))
    return pos if pos < len(index) else None


def simulate_owner(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    owner: str,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    seed = cfg["seed"]
    execution = cfg["execution"]
    subset = signals[signals["owner"].eq(owner)].sort_values("completion_time_utc")
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    entries_by_day: dict[str, int] = {}
    slip = float(execution["extra_slippage_pips_per_side"]) * PIP
    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    for _, signal in subset.iterrows():
        pos = _next_position(m5.index, signal["completion_time_utc"])
        if pos is None:
            continue
        entry_time = m5.index[pos]
        if open_until is not None and entry_time <= open_until:
            continue
        if is_quarantined(entry_time, "EURUSD", cfg["quarantine"]):
            continue
        day = entry_time.strftime("%Y-%m-%d")
        if entries_by_day.get(day, 0) >= int(seed["max_trades_per_utc_day"]):
            continue
        bar = m5.iloc[pos]
        entry = max(float(bar["ask_open"]), float(bar["bid_open"]) + spread_floor) + slip
        risk_floor = float(seed["stop_floor_pips"]) * PIP
        raw_stop_distance = max(float(seed["stop_atr_multiple"]) * float(signal["atr"]), risk_floor)
        stop = min(float(signal["recent_low"]), entry - raw_stop_distance)
        risk = entry - stop
        if risk > float(seed["stop_ceiling_pips"]) * PIP:
            continue
        target = entry + float(seed["target_r"]) * risk
        exit_time, exit_price, reason = walk_long_exit(m5, pos, stop, target, slip)
        r = (exit_price - entry) / risk
        records.append(
            {
                "specialist": owner,
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
            }
        )
        open_until = exit_time
        entries_by_day[day] = entries_by_day.get(day, 0) + 1
    return pd.DataFrame(records)


def walk_long_exit(
    m5: pd.DataFrame,
    start_position: int,
    stop: float,
    target: float,
    slip: float,
) -> tuple[pd.Timestamp, float, str]:
    for position in range(start_position, len(m5)):
        timestamp = m5.index[position]
        bar = m5.iloc[position]
        if float(bar["bid_low"]) <= stop:
            return timestamp, min(float(bar["bid_open"]), stop) - slip, "STOP"
        if float(bar["bid_high"]) >= target:
            return timestamp, max(float(bar["bid_open"]), target) - slip, "TARGET"
    return m5.index[-1], float(m5.iloc[-1]["bid_close"]) - slip, "DATA_END"


def summarize(trades: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    admission = cfg["admission"]
    windows = {}
    for name, (a, b) in cfg["windows"].items():
        subset = trades[
            (trades["entry_time_utc"] >= pd.Timestamp(a))
            & (trades["entry_time_utc"] <= pd.Timestamp(b))
        ] if not trades.empty else trades
        windows[name] = metric_block(subset)
    overall = metric_block(trades)
    top_removed = metric_block(remove_top_winners(trades))
    stressed = metric_block(trades, "extra_half_pip_stress_r")
    passed = (
        all(
            x["trades"] >= admission["minimum_trades_each_window"]
            and x["profit_factor"] >= admission["minimum_profit_factor_each_window"]
            and x["expectancy_r"] > admission["minimum_expectancy_r_each_window"]
            for x in windows.values()
        )
        and overall["max_drawdown_r"] <= admission["maximum_drawdown_r_overall"]
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    return {
        "admitted": passed,
        "status": "ADMITTED_RESEARCH_COMPONENT" if passed else "REJECTED_STANDALONE",
        "overall": overall,
        "windows": windows,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
    }


def route(trades_by_owner: dict[str, pd.DataFrame], admitted: list[str], cfg: dict[str, Any]) -> pd.DataFrame:
    if not admitted:
        return pd.DataFrame()
    priority = {name: i for i, name in enumerate(cfg["portfolio"]["priority"])}
    candidates = pd.concat([trades_by_owner[name] for name in admitted], ignore_index=True)
    candidates["priority"] = candidates["specialist"].map(priority)
    candidates = candidates.sort_values(["entry_time_utc", "priority"])
    accepted = []
    open_until: pd.Timestamp | None = None
    for _, row in candidates.iterrows():
        if open_until is not None and row["entry_time_utc"] <= open_until:
            continue
        accepted.append(row.drop(labels=["priority"]).to_dict())
        open_until = row["exit_time_utc"]
    return pd.DataFrame(accepted)


def run_backtest(signals: pd.DataFrame, m5: pd.DataFrame, cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    trades = {owner: simulate_owner(signals, m5, owner, cfg) for owner in OWNERS}
    specialist_results = {owner: summarize(frame, cfg) for owner, frame in trades.items()}
    admitted = [owner for owner in OWNERS if specialist_results[owner]["admitted"]]
    portfolio = route(trades, admitted, cfg)
    portfolio_summary = summarize(portfolio, cfg)
    active_days = active_weekday_fx_days(
        m5,
        pd.Timestamp(cfg["data"]["start_utc"]),
        pd.Timestamp(cfg["data"]["end_utc"]),
    )
    frequency = len(portfolio) / active_days
    portfolio_summary["actual_trades_per_active_day"] = frequency
    gate = cfg["portfolio"]
    portfolio_pass = (
        bool(admitted)
        and portfolio_summary["overall"]["profit_factor"] >= gate["minimum_profit_factor"]
        and frequency >= gate["minimum_actual_trades_per_active_day"]
        and all(x["net_r"] > 0 for x in portfolio_summary["windows"].values())
    )
    portfolio_summary["portfolio_gate_passed"] = portfolio_pass
    portfolio_summary["status"] = "RESEARCH_PASS" if portfolio_pass else "REJECTED"
    recent_a, recent_b = map(pd.Timestamp, cfg["recent_six_months"])
    recent = portfolio[
        (portfolio["entry_time_utc"] >= recent_a) & (portfolio["entry_time_utc"] <= recent_b)
    ] if not portfolio.empty else portfolio
    recent_summary = metric_block(recent)
    if not recent.empty:
        recent_summary["active_months"] = int(recent["entry_time_utc"].dt.to_period("M").nunique())
        recent_summary["trades_per_active_day"] = float(
            len(recent)
            / active_weekday_fx_days(m5, recent_a, recent_b)
        )
        monthly = {}
        for month, frame in recent.groupby(recent["entry_time_utc"].dt.strftime("%Y-%m")):
            monthly[month] = metric_block(frame)
        recent_summary["monthly"] = monthly
    else:
        recent_summary.update({"active_months": 0, "trades_per_active_day": 0.0, "monthly": {}})
    result = {
        "specialists": specialist_results,
        "admitted_specialists": admitted,
        "portfolio": portfolio_summary,
        "recent_six_months": recent_summary,
    }
    trades["PORTFOLIO"] = portfolio
    return result, trades


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize(payload), indent=2), encoding="utf-8")


def source_manifest(m5: pd.DataFrame, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "eurusd_m5_rows": int(len(m5)),
        "eurusd_first_utc": m5.index.min().isoformat(),
        "eurusd_last_utc": m5.index.max().isoformat(),
        "eurusd_index_and_close_sha256": hashlib.sha256(
            pd.util.hash_pandas_object(m5[["bid_close", "ask_close"]], index=True).values.tobytes()
        ).hexdigest(),
        "context": context,
    }
