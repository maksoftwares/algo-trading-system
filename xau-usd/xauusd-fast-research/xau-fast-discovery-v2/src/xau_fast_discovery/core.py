from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


PHASE = "XAU_FAST_DISCOVERY_V2"
BASE_COMMIT = "c3be9a149bfbdda7399a9dac6d3fd1f01e8b2c4c"
BASE_TREE = "1c3cc86a30427dc14a717f7acd5931bf84cc8407"
BRANCH = "codex/xau-fast-discovery-v2"
COMMIT_MESSAGE = "research: screen XAUUSD fast discovery v2"
SOURCE_CODE = "XAU-USD"
SOURCE_ORIGIN = "https://jetta.dukascopy.com/v1"
STORAGE_ENV = "DUKASCOPY_TICK_DATA_ROOT"
DEVELOPMENT_START = datetime(2021, 7, 1, tzinfo=UTC)
DEVELOPMENT_END = datetime(2024, 7, 1, tzinfo=UTC)
VALIDATION_START = DEVELOPMENT_END
VALIDATION_END = datetime(2025, 7, 1, tzinfo=UTC)
EXAM_START = VALIDATION_END
EXAM_END = datetime(2026, 7, 1, tzinfo=UTC)
STRATEGY_IDS = (
    "XAU_V2_H4_TREND_PULLBACK_CONTINUATION",
    "XAU_V2_H4_BREAKOUT_RETEST_CONTINUATION",
    "XAU_V2_H4_COMPRESSION_EXPANSION",
    "XAU_V2_H1_FAILED_AUCTION_REVERSAL",
    "XAU_V2_LONDON_SESSION_SWEEP_RECLAIM",
    "XAU_V2_INTRADAY_IMPULSE_CONTINUATION",
)
FINAL_CLASSIFICATIONS = (
    "XAU_FAST_DISCOVERY_V2_DATA_INCOMPLETE",
    "XAU_FAST_DISCOVERY_V2_NO_DEVELOPMENT_SURVIVOR",
    "XAU_FAST_DISCOVERY_V2_NO_PORTFOLIO_CANDIDATE",
    "XAU_FAST_DISCOVERY_V2_SURVIVOR_CONFIRMATION_REQUIRED",
    "XAU_FAST_DISCOVERY_V2_EVIDENCE_INVALID",
)
SIGNAL_FIELDS = (
    "strategy_id", "setup_episode_id", "UTC_date", "direction", "chronological_segment",
    "higher_timeframe_regime_time", "higher_timeframe_values", "setup_start_time", "signal_time",
    "signal_bar_OHLC", "ATR_values", "frozen_levels", "raw_trigger_values",
    "signal_accepted_pre_execution", "signal_accepted", "rejection_reason", "entry_time",
    "entry_bid", "entry_ask", "entry_price", "stop", "target", "initial_risk_price",
)
TRADE_FIELDS = (
    "strategy_id", "setup_episode_id", "UTC_date", "chronological_segment", "direction",
    "signal_time", "entry_time", "entry_bid", "entry_ask", "entry_price", "entry_spread",
    "stop", "target", "initial_risk_price", "exit_time", "exit_bid", "exit_ask", "exit_price",
    "exit_spread", "exit_reason", "gross_R", "baseline_net_R", "stress_incremental_entry_spread_R",
    "stress_incremental_exit_spread_R", "stress_slippage_R", "stress_net_R",
    "broker_transfer_diagnostic_R", "MFE_R", "MAE_R", "holding_minutes", "stop_gap", "target_gap",
    "identical_timestamp_ambiguity", "forced_exit", "Capital_contract_minimum_loss",
    "Capital_required_margin", "Capital_account_feasible", "Capital_rejection_reason",
)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_ms(value: int | float | datetime | None) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromtimestamp(float(value) / 1000, UTC)
    return dt.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def segment_for_ms(timestamp_ms: int) -> str:
    value = datetime.fromtimestamp(timestamp_ms / 1000, UTC)
    if DEVELOPMENT_START <= value < DEVELOPMENT_END:
        return "DEVELOPMENT"
    if VALIDATION_START <= value < VALIDATION_END:
        return "VALIDATION"
    if EXAM_START <= value < EXAM_END:
        return "LOCKED_EXAM"
    return "OUTSIDE"


def wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def true_range(frame: pd.DataFrame) -> pd.Series:
    previous = frame["close"].shift(1)
    return pd.concat([
        frame["high"] - frame["low"],
        (frame["high"] - previous).abs(),
        (frame["low"] - previous).abs(),
    ], axis=1).max(axis=1)


def add_indicators(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    result = frame.sort_values("timestamp_ms").reset_index(drop=True).copy()
    result["complete_ms"] = result["timestamp_ms"] + {"M5": 300_000, "M15": 900_000, "H1": 3_600_000, "H4": 14_400_000}[timeframe]
    tr = true_range(result)
    result["true_range"] = tr
    result["ATR14"] = wilder(tr, 14)
    result["EMA20"] = result["close"].ewm(span=20, adjust=False, min_periods=20).mean()
    result["EMA50"] = result["close"].ewm(span=50, adjust=False, min_periods=50).mean()
    if timeframe == "H4":
        result["EMA200"] = result["close"].ewm(span=200, adjust=False, min_periods=200).mean()
        up = result["high"].diff()
        down = -result["low"].diff()
        plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=result.index)
        minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=result.index)
        plus_di = 100 * wilder(plus_dm, 14) / result["ATR14"]
        minus_di = 100 * wilder(minus_dm, 14) / result["ATR14"]
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        result["ADX14"] = wilder(dx, 14)
        result["ER20"] = (result["close"] - result["close"].shift(20)).abs() / result["close"].diff().abs().rolling(20).sum()
        result["DONCHIAN_HIGH20"] = result["high"].shift(1).rolling(20).max()
        result["DONCHIAN_LOW20"] = result["low"].shift(1).rolling(20).min()
        values = result["ATR14"].to_numpy()
        percentile = np.full(len(result), np.nan)
        for index in range(252, len(result)):
            prior = values[index - 252:index]
            if np.isfinite(values[index]) and np.isfinite(prior).all():
                percentile[index] = 100 * np.mean(prior <= values[index])
        result["ATR_PERCENTILE252_PRIOR"] = percentile
    if timeframe == "H1":
        result["PRIOR_HIGH20"] = result["high"].shift(1).rolling(20).max()
        result["PRIOR_LOW20"] = result["low"].shift(1).rolling(20).min()
    result["body"] = (result["close"] - result["open"]).abs()
    result["range"] = result["high"] - result["low"]
    result["body_ratio"] = result["body"] / result["range"].replace(0, np.nan)
    result["close_location"] = (result["close"] - result["low"]) / result["range"].replace(0, np.nan)
    return result


def causal_asof(left: pd.DataFrame, right: pd.DataFrame, columns: Sequence[str], prefix: str) -> pd.DataFrame:
    source = right[["complete_ms", *columns]].sort_values("complete_ms").copy()
    source[f"{prefix}complete_ms"] = source["complete_ms"]
    source = source.rename(columns={column: f"{prefix}{column}" for column in columns})
    return pd.merge_asof(left.sort_values("complete_ms"), source, on="complete_ms", direction="backward", allow_exact_matches=True)


def _candidate(strategy_id: str, row: Mapping[str, Any], direction: str, episode: str, stop: float, rr: float | None, max_hold: int, stop_min_atr: float | None, stop_max_atr: float | None, target_level: float | None = None, setup_start_ms: int | None = None, frozen: Mapping[str, Any] | None = None, higher: Mapping[str, Any] | None = None) -> dict[str, Any]:
    signal_ms = int(row["complete_ms"])
    return {
        "strategy_id": strategy_id,
        "setup_episode_id": episode,
        "UTC_date": datetime.fromtimestamp(signal_ms / 1000, UTC).date().isoformat(),
        "direction": direction,
        "chronological_segment": segment_for_ms(signal_ms),
        "higher_timeframe_regime_time": iso_ms(row.get("h4_complete_ms") or row.get("complete_ms")),
        "higher_timeframe_values": json.dumps(higher or {}, sort_keys=True, separators=(",", ":")),
        "setup_start_time": iso_ms(setup_start_ms or signal_ms),
        "signal_time": iso_ms(signal_ms),
        "signal_ms": signal_ms,
        "signal_bar_OHLC": json.dumps({key: float(row[key]) for key in ("open", "high", "low", "close")}, sort_keys=True, separators=(",", ":")),
        "ATR_values": json.dumps({"M15_ATR14": float(row.get("ATR14", np.nan))}, sort_keys=True, separators=(",", ":")),
        "frozen_levels": json.dumps(frozen or {}, sort_keys=True, separators=(",", ":")),
        "raw_trigger_values": json.dumps({"body_ratio": float(row.get("body_ratio", np.nan)), "close_location": float(row.get("close_location", np.nan))}, sort_keys=True, separators=(",", ":")),
        "signal_accepted_pre_execution": True,
        "signal_accepted": False,
        "rejection_reason": "PENDING_EXECUTION",
        "entry_time": "", "entry_bid": "", "entry_ask": "", "entry_price": "",
        "stop": float(stop), "target": "", "initial_risk_price": "",
        "rr": rr, "target_level": target_level, "max_hold_hours": max_hold,
        "stop_min_atr": stop_min_atr, "stop_max_atr": stop_max_atr, "m15_atr": float(row.get("ATR14", np.nan)),
    }


def generate_family_a(m15: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame) -> list[dict[str, Any]]:
    columns_h4 = ["close", "EMA50", "EMA200", "ADX14", "ER20"]
    columns_h1 = ["EMA20", "EMA50"]
    joined = causal_asof(m15, h4, columns_h4, "h4_")
    joined = causal_asof(joined, h1.assign(EMA20_SHIFT3=h1["EMA20"].shift(3)), ["EMA20", "EMA50", "EMA20_SHIFT3"], "h1_")
    result = []
    for index, row in joined.iterrows():
        if not np.isfinite(row.get("ATR14", np.nan)) or row["range"] <= 0:
            continue
        long = row.h4_close > row.h4_EMA50 > row.h4_EMA200 and row.h4_ADX14 >= 22 and row.h4_ER20 >= .35 and row.h1_EMA20 > row.h1_EMA50 and row.h1_EMA20 > row.h1_EMA20_SHIFT3 and row.low <= row.EMA20 and row.close > row.EMA20 and row.close > row.open and row.body_ratio >= .50 and row.close_location >= .75
        short = row.h4_close < row.h4_EMA50 < row.h4_EMA200 and row.h4_ADX14 >= 22 and row.h4_ER20 >= .35 and row.h1_EMA20 < row.h1_EMA50 and row.h1_EMA20 < row.h1_EMA20_SHIFT3 and row.high >= row.EMA20 and row.close < row.EMA20 and row.close < row.open and row.body_ratio >= .50 and row.close_location <= .25
        if long or short:
            start = max(0, index - 4)
            stop = joined.iloc[start:index + 1].low.min() - .10 * row.ATR14 if long else joined.iloc[start:index + 1].high.max() + .10 * row.ATR14
            result.append(_candidate(STRATEGY_IDS[0], row, "LONG" if long else "SHORT", f"A-{int(row.complete_ms)}", stop, 2.0, 10, .75, 2.0, higher={key: row.get(f"h4_{key}") for key in columns_h4}))
    return result


def generate_family_b(m15: pd.DataFrame, h4: pd.DataFrame) -> list[dict[str, Any]]:
    result = []
    for _, breakout in h4.iterrows():
        long = breakout.close >= breakout.DONCHIAN_HIGH20 + .10 * breakout.ATR14 and breakout.ADX14 >= 20
        short = breakout.close <= breakout.DONCHIAN_LOW20 - .10 * breakout.ATR14 and breakout.ADX14 >= 20
        if not (long or short):
            continue
        level = breakout.DONCHIAN_HIGH20 if long else breakout.DONCHIAN_LOW20
        window = m15[(m15.complete_ms > breakout.complete_ms) & (m15.complete_ms <= breakout.complete_ms + 12 * 900_000)]
        for _, row in window.iterrows():
            qualifies = row.low <= level + .15 * row.ATR14 and row.close > level and row.close > row.open and row.body_ratio >= .45 and row.close_location >= .70 if long else row.high >= level - .15 * row.ATR14 and row.close < level and row.close < row.open and row.body_ratio >= .45 and row.close_location <= .30
            if qualifies:
                stop = row.low - .10 * row.ATR14 if long else row.high + .10 * row.ATR14
                result.append(_candidate(STRATEGY_IDS[1], row, "LONG" if long else "SHORT", f"B-{int(breakout.complete_ms)}", stop, 2.0, 12, .75, 2.0, setup_start_ms=int(breakout.complete_ms), frozen={"breakout_level": float(level)}))
                break
    return result


def generate_family_c(m15: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame) -> list[dict[str, Any]]:
    compression = (h4.ATR_PERCENTILE252_PRIOR <= 30) & (h4.ADX14 <= 20)
    starts = h4[compression & ~compression.shift(1, fill_value=False)]
    result = []
    for _, state in starts.iterrows():
        next_h1 = h1[h1.complete_ms > state.complete_ms].head(1)
        if next_h1.empty:
            continue
        row_h1 = next_h1.iloc[0]
        width = row_h1.PRIOR_HIGH20 - row_h1.PRIOR_LOW20
        if not np.isfinite(width) or width > 3 * row_h1.ATR14:
            continue
        later_h4 = h4[(h4.complete_ms > state.complete_ms) & ~compression]
        end = int(later_h4.iloc[0].complete_ms) if not later_h4.empty else int(m15.complete_ms.max())
        window = m15[(m15.complete_ms > row_h1.complete_ms) & (m15.complete_ms <= end)]
        used = set()
        for _, row in window.iterrows():
            long = row.close >= row_h1.PRIOR_HIGH20 + .10 * row.ATR14 and row.close > row.open and row.body_ratio >= .60 and row.close_location >= .80
            short = row.close <= row_h1.PRIOR_LOW20 - .10 * row.ATR14 and row.close < row.open and row.body_ratio >= .60 and row.close_location <= .20
            direction = "LONG" if long else "SHORT" if short else ""
            if direction and direction not in used:
                used.add(direction)
                stop = row.low - .10 * row.ATR14 if long else row.high + .10 * row.ATR14
                result.append(_candidate(STRATEGY_IDS[2], row, direction, f"C-{int(row_h1.complete_ms)}-{direction}", stop, 2.0, 8, .75, 1.75, setup_start_ms=int(state.complete_ms), frozen={"box_high": float(row_h1.PRIOR_HIGH20), "box_low": float(row_h1.PRIOR_LOW20)}))
    return result


def generate_family_d(m15: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame) -> list[dict[str, Any]]:
    h4b = h4.assign(BALANCE=(h4.ADX14 <= 22) & (h4.ER20 <= .30) & ((h4.close - h4.close.shift(20)).abs() / h4.ATR14 <= 1.75))
    joined_h1 = causal_asof(h1, h4b, ["BALANCE"], "h4_")
    result = []
    for _, auction in joined_h1.iterrows():
        width = auction.PRIOR_HIGH20 - auction.PRIOR_LOW20
        if auction.h4_BALANCE is not True and auction.h4_BALANCE != True:
            continue
        if not (2 * auction.ATR14 <= width <= 6 * auction.ATR14):
            continue
        midpoint = (auction.PRIOR_HIGH20 + auction.PRIOR_LOW20) / 2
        window = m15[(m15.complete_ms > auction.complete_ms) & (m15.complete_ms <= auction.complete_ms + 3_600_000)]
        used = set()
        for _, row in window.iterrows():
            short = row.high >= auction.PRIOR_HIGH20 + .15 * row.ATR14 and row.close < auction.PRIOR_HIGH20 and row.close < row.open and row.body_ratio >= .40 and row.close_location <= .35
            long = row.low <= auction.PRIOR_LOW20 - .15 * row.ATR14 and row.close > auction.PRIOR_LOW20 and row.close > row.open and row.body_ratio >= .40 and row.close_location >= .65
            direction = "SHORT" if short else "LONG" if long else ""
            if direction and direction not in used:
                used.add(direction)
                stop = row.high + .10 * row.ATR14 if short else row.low - .10 * row.ATR14
                result.append(_candidate(STRATEGY_IDS[3], row, direction, f"D-{int(auction.complete_ms)}-{direction}", stop, None, 8, None, None, target_level=float(midpoint), frozen={"range_high": float(auction.PRIOR_HIGH20), "range_low": float(auction.PRIOR_LOW20), "midpoint": float(midpoint)}))
    return result


def generate_family_e(m15: pd.DataFrame, h1: pd.DataFrame) -> list[dict[str, Any]]:
    london = ZoneInfo("Europe/London")
    local = pd.to_datetime(m15.complete_ms, unit="ms", utc=True).dt.tz_convert(london)
    work = m15.copy()
    work["local_date"] = local.dt.date.astype(str)
    work["local_minutes"] = local.dt.hour * 60 + local.dt.minute
    with_h1 = causal_asof(work, h1, ["ATR14"], "h1_")
    result = []
    for date, group in with_h1.groupby("local_date", sort=True):
        pre = group[(group.local_minutes > 0) & (group.local_minutes <= 7 * 60)]
        # complete_ms labels bar completion; 00:15..07:00 represent [00:00,07:00).
        if len(pre) < 20:
            continue
        high, low = pre.high.max(), pre.low.min()
        width = high - low
        atr = pre.iloc[-1].h1_ATR14
        if not np.isfinite(atr) or not (.5 * atr <= width <= 2.5 * atr):
            continue
        signals = group[(group.local_minutes > 7 * 60) & (group.local_minutes <= 10 * 60)]
        for _, row in signals.iterrows():
            long = row.low <= low - .15 * row.ATR14 and row.close > low and row.close > row.open and row.body_ratio >= .40 and row.close_location >= .65
            short = row.high >= high + .15 * row.ATR14 and row.close < high and row.close < row.open and row.body_ratio >= .40 and row.close_location <= .35
            if long or short:
                stop = row.low - .10 * row.ATR14 if long else row.high + .10 * row.ATR14
                result.append(_candidate(STRATEGY_IDS[4], row, "LONG" if long else "SHORT", f"E-{date}", stop, 1.75, 6, None, None, frozen={"range_high": float(high), "range_low": float(low)}))
                break
    return result


def generate_family_f(m5: pd.DataFrame, m15: pd.DataFrame, h1: pd.DataFrame) -> list[dict[str, Any]]:
    joined = causal_asof(m15, h1.assign(EMA50_SHIFT3=h1.EMA50.shift(3)), ["close", "EMA50", "EMA50_SHIFT3"], "h1_")
    result = []
    for _, impulse in joined.iterrows():
        long = impulse.h1_close > impulse.h1_EMA50 > impulse.h1_EMA50_SHIFT3 and impulse.true_range >= 1.80 * impulse.ATR14 and impulse.close > impulse.open and impulse.body_ratio >= .70 and impulse.close_location >= .80
        short = impulse.h1_close < impulse.h1_EMA50 < impulse.h1_EMA50_SHIFT3 and impulse.true_range >= 1.80 * impulse.ATR14 and impulse.close < impulse.open and impulse.body_ratio >= .70 and impulse.close_location <= .20
        if not (long or short):
            continue
        consolidation = m5[(m5.complete_ms > impulse.complete_ms) & (m5.complete_ms <= impulse.complete_ms + 3 * 300_000)]
        if len(consolidation) != 3:
            continue
        midpoint = (impulse.high + impulse.low) / 2
        valid = (consolidation.close >= midpoint).all() and consolidation.low.min() >= impulse.low + .50 * impulse.range if long else (consolidation.close <= midpoint).all() and consolidation.high.max() <= impulse.high - .50 * impulse.range
        if not valid:
            continue
        triggers = m5[(m5.complete_ms > consolidation.complete_ms.max()) & (m5.complete_ms <= consolidation.complete_ms.max() + 3 * 300_000)]
        for _, trigger in triggers.iterrows():
            qualifies = trigger.close > impulse.high if long else trigger.close < impulse.low
            if qualifies:
                row = trigger.copy()
                row["ATR14"] = impulse.ATR14
                stop = consolidation.low.min() - .10 * impulse.ATR14 if long else consolidation.high.max() + .10 * impulse.ATR14
                result.append(_candidate(STRATEGY_IDS[5], row, "LONG" if long else "SHORT", f"F-{int(impulse.complete_ms)}", stop, 2.0, 6, .60, 1.50, setup_start_ms=int(impulse.complete_ms), frozen={"impulse_high": float(impulse.high), "impulse_low": float(impulse.low)}))
                break
    return result


def generate_all_candidates(bars: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    m5 = add_indicators(bars["M5"], "M5")
    m15 = add_indicators(bars["M15"], "M15")
    h1 = add_indicators(bars["H1"], "H1")
    h4 = add_indicators(bars["H4"], "H4")
    candidates = (
        generate_family_a(m15, h1, h4)
        + generate_family_b(m15, h4)
        + generate_family_c(m15, h1, h4)
        + generate_family_d(m15, h1, h4)
        + generate_family_e(m15, h1)
        + generate_family_f(m5, m15, h1)
    )
    return sorted(candidates, key=lambda row: (row["signal_ms"], row["strategy_id"], row["setup_episode_id"]))


def _tick_key(row: pd.Series) -> tuple[int, str]:
    return int(row["timestamp_msc"]), str(row["source_sequence"])


def _side_price(row: pd.Series, direction: str, entry: bool) -> float:
    if direction == "LONG":
        return float(row["ask"] if entry else row["bid"])
    return float(row["bid"] if entry else row["ask"])


def execute_candidates(
    candidates: Sequence[Mapping[str, Any]],
    ticks_by_date: Mapping[str, pd.DataFrame],
    development_spread_p95: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute frozen candidates against native quotes in deterministic source order."""
    prepared: list[tuple[tuple[int, str], dict[str, Any], pd.DataFrame, int]] = []
    ledger: list[dict[str, Any]] = []
    for source in candidates:
        candidate = dict(source)
        day = ticks_by_date.get(candidate["UTC_date"])
        if day is None or day.empty:
            candidate["rejection_reason"] = "MISSING_EXECUTION_INTERVAL"
            ledger.append(candidate)
            continue
        day = day.sort_values(["timestamp_msc", "source_sequence"], kind="mergesort").reset_index(drop=True)
        valid = day.index[day["timestamp_msc"] >= int(candidate["signal_ms"])].tolist()
        if not valid:
            candidate["rejection_reason"] = "MISSING_EXECUTION_INTERVAL"
            ledger.append(candidate)
            continue
        index = valid[0]
        tick = day.iloc[index]
        hour = datetime.fromtimestamp(int(tick.timestamp_msc) / 1000, UTC).hour
        if not (6 <= hour < 17):
            candidate["rejection_reason"] = "OUTSIDE_COMMON_ENTRY_WINDOW"
            ledger.append(candidate)
            continue
        prepared.append((_tick_key(tick), candidate, day, index))

    family_dates: set[tuple[str, str]] = set()
    open_until: tuple[int, str] | None = None
    trades: list[dict[str, Any]] = []
    for executable_key, candidate, day, entry_index in sorted(
        prepared, key=lambda value: (value[0][0], value[0][1], value[1]["strategy_id"], value[1]["setup_episode_id"])
    ):
        family_date = (candidate["strategy_id"], candidate["UTC_date"])
        if family_date in family_dates:
            candidate["rejection_reason"] = "FAMILY_DAILY_TRADE_ALREADY_USED"
            ledger.append(candidate)
            continue
        if open_until is not None and executable_key <= open_until:
            candidate["rejection_reason"] = "GLOBAL_XAU_POSITION_ALREADY_OPEN"
            ledger.append(candidate)
            continue
        entry_tick = day.iloc[entry_index]
        direction = candidate["direction"]
        entry_price = _side_price(entry_tick, direction, True)
        stop = float(candidate["stop"])
        risk = entry_price - stop if direction == "LONG" else stop - entry_price
        atr = float(candidate["m15_atr"])
        if not (math.isfinite(risk) and risk > 0 and math.isfinite(atr) and atr > 0):
            candidate["rejection_reason"] = "INVALID_INITIAL_RISK"
            ledger.append(candidate)
            continue
        risk_atr = risk / atr
        minimum, maximum = candidate.get("stop_min_atr"), candidate.get("stop_max_atr")
        if minimum is not None and not (float(minimum) <= risk_atr <= float(maximum)):
            candidate["rejection_reason"] = "STOP_DISTANCE_OUTSIDE_FROZEN_RANGE"
            ledger.append(candidate)
            continue
        target = float(candidate["target_level"]) if candidate.get("target_level") is not None else (
            entry_price + float(candidate["rr"]) * risk if direction == "LONG" else entry_price - float(candidate["rr"]) * risk
        )
        reward = target - entry_price if direction == "LONG" else entry_price - target
        if candidate.get("target_level") is not None and reward / risk < 1.5:
            candidate["rejection_reason"] = "MIDPOINT_REWARD_BELOW_1_50R"
            ledger.append(candidate)
            continue

        entry_ms = int(entry_tick.timestamp_msc)
        hold_deadline = entry_ms + int(candidate["max_hold_hours"]) * 3_600_000
        date_start = int(datetime.fromisoformat(candidate["UTC_date"]).replace(tzinfo=UTC).timestamp() * 1000)
        force_ms = date_start + 20 * 3_600_000
        exit_tick: pd.Series | None = None
        exit_reason = ""
        exit_price = math.nan
        stop_gap = False
        target_gap = False
        ambiguity = False
        favorable = 0.0
        adverse = 0.0
        path = day.iloc[entry_index + 1:]
        ambiguous_stop_rows: dict[tuple[int, str], pd.Series] = {}
        for key, group in path.groupby(["timestamp_msc", "source_sequence"], sort=False):
            if len(group) < 2:
                continue
            prices = group["bid"] if direction == "LONG" else group["ask"]
            stop_mask = prices <= stop if direction == "LONG" else prices >= stop
            target_mask = prices >= target if direction == "LONG" else prices <= target
            if stop_mask.any() and target_mask.any():
                ambiguous_stop_rows[(int(key[0]), str(key[1]))] = group.loc[stop_mask].iloc[0]
        for _, tick in path.iterrows():
            tick_ms = int(tick.timestamp_msc)
            price = _side_price(tick, direction, False)
            pnl = price - entry_price if direction == "LONG" else entry_price - price
            favorable = max(favorable, pnl)
            adverse = min(adverse, pnl)
            if tick_ms >= min(hold_deadline, force_ms):
                exit_tick, exit_price = tick, price
                exit_reason = "MAXIMUM_ELAPSED_HOLD" if hold_deadline <= force_ms else "SAME_DAY_20_UTC_FORCE_CLOSE"
                break
            ambiguous_tick = ambiguous_stop_rows.get(_tick_key(tick))
            if ambiguous_tick is not None:
                exit_tick = ambiguous_tick
                exit_price = _side_price(ambiguous_tick, direction, False)
                exit_reason = "IDENTICAL_TIMESTAMP_STOP_FIRST"
                ambiguity = True
                stop_gap = not math.isclose(exit_price, stop)
                break
            stop_true = price <= stop if direction == "LONG" else price >= stop
            target_true = price >= target if direction == "LONG" else price <= target
            if stop_true and target_true:
                ambiguity = True
                exit_tick, exit_price, exit_reason = tick, price, "IDENTICAL_TIMESTAMP_STOP_FIRST"
                stop_gap = not math.isclose(price, stop)
                break
            if stop_true:
                exit_tick, exit_price, exit_reason = tick, price, "STOP"
                stop_gap = not math.isclose(price, stop)
                break
            if target_true:
                exit_tick, exit_price, exit_reason = tick, target, "TARGET"
                target_gap = not math.isclose(price, target)
                break
        if exit_tick is None:
            candidate["rejection_reason"] = "MISSING_SAME_DAY_EXIT_PATH"
            ledger.append(candidate)
            continue
        if int(exit_tick.timestamp_msc) >= date_start + 86_400_000:
            candidate["rejection_reason"] = "MISSING_SAME_DAY_EXIT_PATH"
            ledger.append(candidate)
            continue

        pnl = exit_price - entry_price if direction == "LONG" else entry_price - exit_price
        baseline = pnl / risk
        entry_spread = float(entry_tick.ask - entry_tick.bid)
        exit_spread = float(exit_tick.ask - exit_tick.bid)
        entry_increment = max(0.0, development_spread_p95 - entry_spread) / risk
        exit_increment = max(0.0, development_spread_p95 - exit_spread) / risk
        candidate.update({
            "signal_accepted": True, "rejection_reason": "", "entry_time": iso_ms(entry_ms),
            "entry_bid": float(entry_tick.bid), "entry_ask": float(entry_tick.ask),
            "entry_price": entry_price, "target": target, "initial_risk_price": risk,
        })
        ledger.append(candidate)
        trade = {
            **{key: candidate.get(key, "") for key in ("strategy_id", "setup_episode_id", "UTC_date", "chronological_segment", "direction", "signal_time")},
            "entry_time": iso_ms(entry_ms), "entry_bid": float(entry_tick.bid), "entry_ask": float(entry_tick.ask),
            "entry_price": entry_price, "entry_spread": entry_spread, "stop": stop, "target": target,
            "initial_risk_price": risk, "exit_time": iso_ms(int(exit_tick.timestamp_msc)),
            "exit_bid": float(exit_tick.bid), "exit_ask": float(exit_tick.ask), "exit_price": exit_price,
            "exit_spread": exit_spread, "exit_reason": exit_reason, "gross_R": baseline,
            "baseline_net_R": baseline, "stress_incremental_entry_spread_R": entry_increment,
            "stress_incremental_exit_spread_R": exit_increment, "stress_slippage_R": .05,
            "stress_net_R": baseline - entry_increment - exit_increment - .05,
            "broker_transfer_diagnostic_R": baseline - .15, "MFE_R": favorable / risk,
            "MAE_R": adverse / risk, "holding_minutes": (int(exit_tick.timestamp_msc) - entry_ms) / 60_000,
            "stop_gap": stop_gap, "target_gap": target_gap,
            "identical_timestamp_ambiguity": ambiguity, "forced_exit": "FORCE_CLOSE" in exit_reason,
            "Capital_contract_minimum_loss": "", "Capital_required_margin": "",
            "Capital_account_feasible": "", "Capital_rejection_reason": "",
            "entry_delay_minutes": (entry_ms - int(candidate["signal_ms"])) / 60_000,
        }
        trades.append(trade)
        family_dates.add(family_date)
        open_until = _tick_key(exit_tick)
    return sorted(ledger, key=lambda row: (row["signal_ms"], row["strategy_id"], row["setup_episode_id"])), trades


def weighted_percentile(histogram: Mapping[float, int], percentile: float) -> float:
    total = sum(histogram.values())
    if total == 0:
        return math.nan
    target = math.ceil(total * percentile)
    cumulative = 0
    for value, count in sorted(histogram.items()):
        cumulative += count
        if cumulative >= target:
            return value
    return max(histogram)


def compute_metrics(trades: Sequence[Mapping[str, Any]], value_field: str = "baseline_net_R") -> dict[str, Any]:
    values = [float(row[value_field]) for row in trades]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    pf = gross_profit / gross_loss if gross_loss else (math.inf if gross_profit else 0.0)
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    top_ten = sum(sorted(wins, reverse=True)[:10]) / gross_profit if gross_profit else 0.0
    return {
        "trades": len(values), "wins": len(wins), "losses": len(losses), "net_R": sum(values),
        "expectancy_R": sum(values) / len(values) if values else 0.0, "profit_factor": pf,
        "maximum_closed_drawdown_R": max_dd, "top_ten_winner_share": top_ten,
    }


def development_gate(metrics: Mapping[str, Any], stress: Mapping[str, Any]) -> tuple[bool, list[str]]:
    checks = {
        "accepted_trades>=60": metrics["trades"] >= 60,
        "baseline_PF>=1.05": metrics["profit_factor"] >= 1.05,
        "baseline_expectancy>=0.02R": metrics["expectancy_R"] >= .02,
        "baseline_net>0": metrics["net_R"] > 0,
        "stress_PF>=1.00": stress["profit_factor"] >= 1.0,
        "stress_net>0": stress["net_R"] > 0,
        "maximum_closed_drawdown<=20R": metrics["maximum_closed_drawdown_R"] <= 20,
        "top_ten_winners<=50pct_gross": metrics["top_ten_winner_share"] <= .50,
    }
    return all(checks.values()), [name for name, passed in checks.items() if not passed]


def final_family_gate(report: Mapping[str, Any]) -> tuple[bool, list[str]]:
    checks = {
        "full_period_trades>=150": report["full_period_trades"] >= 150,
        "validation_trades>=25": report["validation_trades"] >= 25,
        "locked_exam_trades>=25": report["locked_exam_trades"] >= 25,
        "baseline_PF>=1.12": report["baseline_PF"] >= 1.12,
        "baseline_expectancy>=0.05R": report["baseline_expectancy_R"] >= .05,
        "baseline_net>0": report["baseline_net_R"] > 0,
        "stress_PF>=1.03": report["stress_PF"] >= 1.03,
        "stress_expectancy>0": report["stress_expectancy_R"] > 0,
        "stress_net>0": report["stress_net_R"] > 0,
        "validation_net>0": report["validation_net_R"] > 0,
        "locked_exam_PF>=1.05": report["locked_exam_PF"] >= 1.05,
        "locked_exam_expectancy>0": report["locked_exam_expectancy_R"] > 0,
        "locked_exam_net>0": report["locked_exam_net_R"] > 0,
        "maximum_closed_drawdown<=15R": report["maximum_closed_drawdown_R"] <= 15,
        "top_ten_winners<=35pct_gross": report["top_ten_winner_share"] <= .35,
        "top_three_winning_days<=25pct_gross": report["top_three_winning_day_share"] <= .25,
        "no_segment_PF<0.90": report["minimum_segment_PF"] >= .90,
    }
    return all(checks.values()), [name for name, passed in checks.items() if not passed]


def commercial_portfolio_gate(report: Mapping[str, Any]) -> tuple[bool, list[str]]:
    checks = {
        "full_period_independent_trades>=600": report["full_period_trades"] >= 600,
        "annualized_trades>=120": report["annualized_trades"] >= 120,
        "median_monthly_trades>=8": report["median_monthly_trades"] >= 8,
        "locked_exam_trades>=100": report["locked_exam_trades"] >= 100,
        "latest_six_months_trades>=45": report["latest_six_months_trades"] >= 45,
        "latest_three_months_trades>=20": report["latest_three_months_trades"] >= 20,
        "locked_exam_active_months>=9": report["locked_exam_active_months"] >= 9,
        "baseline_PF>=1.25": report["baseline_PF"] >= 1.25,
        "baseline_expectancy>=0.08R": report["baseline_expectancy_R"] >= .08,
        "baseline_net>0": report["baseline_net_R"] > 0,
        "stress_PF>=1.10": report["stress_PF"] >= 1.10,
        "stress_expectancy>=0.03R": report["stress_expectancy_R"] >= .03,
        "stress_net>0": report["stress_net_R"] > 0,
        "locked_exam_PF>=1.15": report["locked_exam_PF"] >= 1.15,
        "locked_exam_expectancy>=0.05R": report["locked_exam_expectancy_R"] >= .05,
        "locked_exam_net>0": report["locked_exam_net_R"] > 0,
        "baseline_floating_drawdown<=20R": report["baseline_floating_drawdown_R"] <= 20,
        "stress_floating_drawdown<=25R": report["stress_floating_drawdown_R"] <= 25,
        "top_ten_winners<=30pct_gross": report["top_ten_winner_share"] <= .30,
        "top_three_winning_days<=20pct_gross": report["top_three_winning_day_share"] <= .20,
        "maximum_family_positive_net_share<=60pct": report["maximum_family_positive_net_share"] <= .60,
        "positive_rolling_12m_windows>=70pct": report["positive_rolling_12m_share"] >= .70,
    }
    return all(checks.values()), [name for name, passed in checks.items() if not passed]


def account_feasibility(minimum_losses_usd: Sequence[float], margins_usd: Sequence[float]) -> tuple[bool, dict[str, Any]]:
    if len(minimum_losses_usd) != len(margins_usd) or not minimum_losses_usd:
        return False, {"rejection_rate": 1.0, "failed": ["NO_FINAL_OPPORTUNITIES_OR_CARDINALITY_MISMATCH"]}
    accepted = [loss <= 5 and margin <= 200 and 1000 - margin >= 800 for loss, margin in zip(minimum_losses_usd, margins_usd)]
    rejection_rate = 1 - sum(accepted) / len(accepted)
    rejection_reasons = []
    if any(loss > 5 for loss in minimum_losses_usd):
        rejection_reasons.append("MINIMUM_VOLUME_TOTAL_LOSS_GT_USD5")
    if any(margin > 200 or 1000 - margin < 800 for margin in margins_usd):
        rejection_reasons.append("MARGIN_OR_FREE_MARGIN_GATE")
    failures = []
    if rejection_rate > .10:
        failures.append("SIZING_REJECTION_RATE_GT_10PCT")
    return not failures, {"rejection_rate": rejection_rate, "failed": failures, "opportunity_rejection_reasons": rejection_reasons}


def classification(evidence_valid: bool, data_complete: bool, development_survivors: int, final_passers: int = 0, portfolio_pass: bool = False) -> str:
    if not evidence_valid:
        return "XAU_FAST_DISCOVERY_V2_EVIDENCE_INVALID"
    if not data_complete:
        return "XAU_FAST_DISCOVERY_V2_DATA_INCOMPLETE"
    if development_survivors == 0:
        return "XAU_FAST_DISCOVERY_V2_NO_DEVELOPMENT_SURVIVOR"
    if final_passers < 2 or not portfolio_pass:
        return "XAU_FAST_DISCOVERY_V2_NO_PORTFOLIO_CANDIDATE"
    return "XAU_FAST_DISCOVERY_V2_SURVIVOR_CONFIRMATION_REQUIRED"
