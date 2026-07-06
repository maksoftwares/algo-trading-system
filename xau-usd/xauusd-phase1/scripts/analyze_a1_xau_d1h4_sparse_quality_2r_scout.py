from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
DOC_PATH = PHASE1_ROOT / "docs" / "A1_XAU_D1H4_SPARSE_QUALITY_2R_SCOUT_PREREG_2026_07_05.md"
BAR_PATH = (
    PHASE1_ROOT.parents[0]
    / "xauusd-phase0"
    / "data"
    / "processed"
    / "bars"
    / "capital_com"
    / "XAUUSD"
    / "M5"
    / "XAUUSD_capital_com_M5_20160103_20250701.csv"
)
OUTPUT_STEM = "A1_XAU_D1H4_SPARSE_QUALITY_2R_SCOUT_2026_07_05"

DESIGN_START = pd.Timestamp("2016-01-01T00:00:00Z")
DESIGN_END = pd.Timestamp("2021-12-31T23:59:59Z")
EXAM_START = pd.Timestamp("2022-07-01T00:00:00Z")
EXAM_END = pd.Timestamp("2025-06-30T23:59:59Z")
LAST12_START = pd.Timestamp("2024-07-01T00:00:00Z")
LAST12_END = pd.Timestamp("2025-06-30T23:59:59Z")

RR = 2.0
MAX_HOLD_BARS = 1440
STOP_BUFFER_ATR = 0.10


@dataclass(frozen=True)
class Params:
    name: str
    family: str
    direction: str
    trend_slope_min: float
    h4_body_min: float
    h4_close_location_threshold: float
    stop_anchor: str
    session_filter: str


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def market_days(start: date, end: date) -> list[str]:
    days: list[str] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    return days


DESIGN_MARKET_DAYS = market_days(DESIGN_START.date(), DESIGN_END.date())
EXAM_MARKET_DAYS = market_days(EXAM_START.date(), EXAM_END.date())
LAST12_MARKET_DAYS = market_days(LAST12_START.date(), LAST12_END.date())


def build_params() -> list[Params]:
    rows: list[Params] = []
    for family in ("trend_pullback_resume", "inside_breakout", "outside_reversal", "range_mid_reclaim"):
        for direction in ("long", "short"):
            for trend_slope_min in (0.00, 0.05):
                for h4_body_min in (0.20, 0.40):
                    for h4_close_location_threshold in (0.60, 0.75):
                        for stop_anchor in ("h4", "d1"):
                            for session_filter in ("liquid", "no_rollover"):
                                name = (
                                    f"d1h4_{family}_{direction}_sl{trend_slope_min:.2f}"
                                    f"_body{h4_body_min:.2f}_cl{h4_close_location_threshold:.2f}"
                                    f"_stop{stop_anchor}_{session_filter}"
                                ).replace(".", "p")
                                rows.append(
                                    Params(
                                        name=name,
                                        family=family,
                                        direction=direction,
                                        trend_slope_min=trend_slope_min,
                                        h4_body_min=h4_body_min,
                                        h4_close_location_threshold=h4_close_location_threshold,
                                        stop_anchor=stop_anchor,
                                        session_filter=session_filter,
                                    )
                                )
    return rows


def add_daily_features(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby("dubai_date", as_index=True)
        .agg(
            d1_open=("mid_open", "first"),
            d1_high=("mid_high", "max"),
            d1_low=("mid_low", "min"),
            d1_close=("mid_close", "last"),
        )
        .sort_index()
    )
    prev_close = daily["d1_close"].shift(1)
    true_range = pd.concat(
        [
            daily["d1_high"] - daily["d1_low"],
            (daily["d1_high"] - prev_close).abs(),
            (daily["d1_low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    daily["d1_atr14"] = true_range.rolling(14, min_periods=14).mean()
    daily["d1_ema20"] = daily["d1_close"].ewm(span=20, adjust=False).mean()
    daily["d1_ema50"] = daily["d1_close"].ewm(span=50, adjust=False).mean()
    daily["d1_ema20_slope_atr"] = (daily["d1_ema20"] - daily["d1_ema20"].shift(3)) / daily["d1_atr14"]
    daily["d1_range"] = daily["d1_high"] - daily["d1_low"]
    daily["d1_mid"] = (daily["d1_high"] + daily["d1_low"]) / 2.0
    daily["d1_body"] = (daily["d1_close"] - daily["d1_open"]).abs()
    daily["d1_close_location"] = ((daily["d1_close"] - daily["d1_low"]) / daily["d1_range"].replace(0, pd.NA)).fillna(
        0.5
    )

    prev = daily.shift(1).add_prefix("prev_")
    prev2 = daily.shift(2).add_prefix("prev2_")
    out = df.join(prev, on="dubai_date")
    out = out.join(prev2, on="dubai_date")
    return out


def load_bars() -> pd.DataFrame:
    usecols = [
        "timestamp_utc",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
    ]
    df = pd.read_csv(BAR_PATH, usecols=usecols)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df[(df["timestamp_utc"] >= DESIGN_START) & (df["timestamp_utc"] <= EXAM_END)].copy()
    df.sort_values("timestamp_utc", inplace=True)
    df.reset_index(drop=True, inplace=True)

    prev_close = df["mid_close"].shift(1)
    true_range = pd.concat(
        [
            df["mid_high"] - df["mid_low"],
            (df["mid_high"] - prev_close).abs(),
            (df["mid_low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr14"] = true_range.rolling(14, min_periods=14).mean()
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()

    dubai_ts = df["timestamp_utc"] + pd.Timedelta(hours=4)
    df["dubai_date"] = dubai_ts.dt.date.astype(str)
    df["dubai_hour"] = dubai_ts.dt.hour
    df["entry_date"] = df["dubai_date"]

    df["h4_close_bar"] = (df["timestamp_utc"].dt.minute == 0) & (df["timestamp_utc"].dt.hour.mod(4) == 0)
    df["h4_open"] = df["mid_open"].shift(47)
    df["h4_high"] = df["mid_high"].rolling(48, min_periods=48).max()
    df["h4_low"] = df["mid_low"].rolling(48, min_periods=48).min()
    df["h4_close"] = df["mid_close"]
    df["h4_range"] = df["h4_high"] - df["h4_low"]
    df["h4_body"] = (df["h4_close"] - df["h4_open"]).abs()
    df["h4_body_frac"] = (df["h4_body"] / df["h4_range"].replace(0, pd.NA)).fillna(0.0)
    df["h4_close_location"] = ((df["h4_close"] - df["h4_low"]) / df["h4_range"].replace(0, pd.NA)).fillna(0.5)

    df = add_daily_features(df)
    needed = [
        "atr14",
        "spread_price",
        "h4_open",
        "h4_high",
        "h4_low",
        "h4_close",
        "h4_range",
        "h4_body_frac",
        "h4_close_location",
        "prev_d1_open",
        "prev_d1_high",
        "prev_d1_low",
        "prev_d1_close",
        "prev_d1_atr14",
        "prev_d1_ema20",
        "prev_d1_ema50",
        "prev_d1_ema20_slope_atr",
        "prev_d1_range",
        "prev_d1_mid",
        "prev_d1_close_location",
        "prev2_d1_high",
        "prev2_d1_low",
    ]
    return df.dropna(subset=needed).reset_index(drop=True)


def base_mask(df: pd.DataFrame, params: Params) -> pd.Series:
    hour = df["dubai_hour"].astype(int)
    if params.session_filter == "liquid":
        session = (hour >= 6) & (hour <= 20)
    else:
        session = ~hour.isin([0, 1, 22, 23])

    if params.direction == "long":
        trend = (
            (df["prev_d1_close"] > df["prev_d1_ema20"])
            & (df["prev_d1_ema20"] > df["prev_d1_ema50"])
            & (df["prev_d1_ema20_slope_atr"] >= params.trend_slope_min)
        )
        h4_shape = (
            (df["h4_close"] > df["h4_open"])
            & (df["h4_body_frac"] >= params.h4_body_min)
            & (df["h4_close_location"] >= params.h4_close_location_threshold)
        )
    else:
        trend = (
            (df["prev_d1_close"] < df["prev_d1_ema20"])
            & (df["prev_d1_ema20"] < df["prev_d1_ema50"])
            & (df["prev_d1_ema20_slope_atr"] <= -params.trend_slope_min)
        )
        h4_shape = (
            (df["h4_close"] < df["h4_open"])
            & (df["h4_body_frac"] >= params.h4_body_min)
            & (df["h4_close_location"] <= 1.0 - params.h4_close_location_threshold)
        )
    return df["h4_close_bar"] & session & trend & h4_shape


def signal_candidates(df: pd.DataFrame, params: Params) -> list[int]:
    mask = base_mask(df, params)
    prev_range = df["prev_d1_range"].replace(0, pd.NA)
    prev_close_loc = df["prev_d1_close_location"]
    inside = (df["prev_d1_high"] < df["prev2_d1_high"]) & (df["prev_d1_low"] > df["prev2_d1_low"])
    outside = (df["prev_d1_high"] > df["prev2_d1_high"]) & (df["prev_d1_low"] < df["prev2_d1_low"])
    large_range = df["prev_d1_range"] >= 1.10 * df["prev_d1_atr14"]

    if params.direction == "long":
        if params.family == "trend_pullback_resume":
            family = (df["prev_d1_close"] < df["prev_d1_open"]) | (prev_close_loc <= 0.55)
            family = family & (df["h4_close"] > df["prev_d1_mid"])
        elif params.family == "inside_breakout":
            family = inside & (df["h4_close"] > df["prev_d1_high"])
        elif params.family == "outside_reversal":
            near_extreme = df["h4_low"] <= df["prev_d1_low"] + 0.25 * prev_range
            family = outside & large_range & near_extreme & (df["h4_close"] > df["prev_d1_mid"])
        else:
            near_extreme = df["h4_low"] <= df["prev_d1_low"] + 0.35 * prev_range
            family = large_range & near_extreme & (df["h4_close"] > df["prev_d1_mid"])
    else:
        if params.family == "trend_pullback_resume":
            family = (df["prev_d1_close"] > df["prev_d1_open"]) | (prev_close_loc >= 0.45)
            family = family & (df["h4_close"] < df["prev_d1_mid"])
        elif params.family == "inside_breakout":
            family = inside & (df["h4_close"] < df["prev_d1_low"])
        elif params.family == "outside_reversal":
            near_extreme = df["h4_high"] >= df["prev_d1_high"] - 0.25 * prev_range
            family = outside & large_range & near_extreme & (df["h4_close"] < df["prev_d1_mid"])
        else:
            near_extreme = df["h4_high"] >= df["prev_d1_high"] - 0.35 * prev_range
            family = large_range & near_extreme & (df["h4_close"] < df["prev_d1_mid"])

    signal = mask & family.fillna(False)
    return [int(index) for index in df.index[signal]]


def simulate(records: list[dict[str, Any]], candidates: list[int], params: Params) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    candidate_index = 0
    while candidate_index < len(candidates):
        i = candidates[candidate_index]
        row = records[i]
        entry_index = i + 1
        if entry_index >= len(records):
            break
        entry_row = records[entry_index]
        atr = float(row["atr14"])
        spread = float(entry_row["spread_price"])
        buffer = STOP_BUFFER_ATR * atr

        if params.direction == "long":
            entry = float(entry_row["ask_open"])
            anchor_low = float(row["h4_low"] if params.stop_anchor == "h4" else row["prev_d1_low"])
            raw_stop = anchor_low - buffer
            risk = max(entry - raw_stop, 3.0 * spread)
            if risk <= 0:
                candidate_index += 1
                continue
            sl = entry - risk
            tp = entry + RR * risk
        else:
            entry = float(entry_row["bid_open"])
            anchor_high = float(row["h4_high"] if params.stop_anchor == "h4" else row["prev_d1_high"])
            raw_stop = anchor_high + buffer
            risk = max(raw_stop - entry, 3.0 * spread)
            if risk <= 0:
                candidate_index += 1
                continue
            sl = entry + risk
            tp = entry - RR * risk

        exit_index = min(entry_index + MAX_HOLD_BARS, len(records) - 1)
        exit_price = None
        exit_reason = "time_stop"
        for j in range(entry_index, exit_index + 1):
            bar = records[j]
            if params.direction == "long":
                hit_sl = float(bar["bid_low"]) <= sl
                hit_tp = float(bar["bid_high"]) >= tp
                if hit_sl and hit_tp:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl_adverse_first"
                    break
                if hit_sl:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl"
                    break
                if hit_tp:
                    exit_index = j
                    exit_price = tp
                    exit_reason = "tp"
                    break
            else:
                hit_sl = float(bar["ask_high"]) >= sl
                hit_tp = float(bar["ask_low"]) <= tp
                if hit_sl and hit_tp:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl_adverse_first"
                    break
                if hit_sl:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl"
                    break
                if hit_tp:
                    exit_index = j
                    exit_price = tp
                    exit_reason = "tp"
                    break
        if exit_price is None:
            last = records[exit_index]
            exit_price = float(last["bid_close"] if params.direction == "long" else last["ask_close"])

        pnl = (exit_price - entry) if params.direction == "long" else (entry - exit_price)
        trades.append(
            {
                "variant": params.name,
                "entry_time_utc": entry_row["timestamp_utc"].isoformat(),
                "exit_time_utc": records[exit_index]["timestamp_utc"].isoformat(),
                "entry_date": entry_row["entry_date"],
                "direction": params.direction.upper(),
                "family": params.family,
                "entry": round(entry, 4),
                "sl": round(sl, 4),
                "tp": round(tp, 4),
                "risk": round(risk, 4),
                "pnl_usd_001lot": round(pnl, 4),
                "r_multiple": round(pnl / risk, 4) if risk else None,
                "exit_reason": exit_reason,
                "entry_hour_dubai": int(entry_row["dubai_hour"]),
                "stop_anchor": params.stop_anchor,
            }
        )
        while candidate_index < len(candidates) and candidates[candidate_index] <= exit_index:
            candidate_index += 1
    return trades


def max_drawdown(values: list[float]) -> float:
    peak = 0.0
    equity = 0.0
    worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def profit_factor(values: list[float]) -> float | None:
    wins = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses <= 0:
        return None
    return wins / losses


def summary_metrics(
    trades: list[dict[str, Any]], market_day_list: list[str], cost_per_trade: float = 0.0
) -> dict[str, Any]:
    values = [float(trade["pnl_usd_001lot"]) - cost_per_trade for trade in trades]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    market_day_set = set(market_day_list)
    active_days = {trade["entry_date"] for trade in trades if trade["entry_date"] in market_day_set}
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = -sum(losses) / len(losses) if losses else 0.0
    return {
        "signals": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": 100.0 * len(wins) / len(trades) if trades else 0.0,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_win_loss": avg_win / avg_loss if avg_loss else None,
        "profit_factor": profit_factor(values),
        "net_usd_001lot": sum(values),
        "max_dd_usd_001lot": max_drawdown(values),
        "active_weekdays": len(active_days),
        "active_weekday_pct": 100.0 * len(active_days) / len(market_day_list) if market_day_list else 0.0,
        "top50_removed_net": sum(sorted(values, reverse=True)[50:]) if len(values) > 50 else None,
    }


def owner_score(row: dict[str, Any]) -> float:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    pf = float(row.get("profit_factor") or 0.0)
    signals = float(row.get("signals") or 0.0)
    return (
        min(wr / 50.0, 1.2) * 375.0
        + min(wl / 2.0, 1.2) * 325.0
        + min(active / 10.0, 1.2) * 175.0
        + min(pf / 1.5, 1.1) * 75.0
        + min(signals / 100.0, 1.1) * 50.0
    )


def decision(row: dict[str, Any]) -> str:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    last_wr = float(row.get("last12_win_rate_pct") or 0.0)
    last_wl = float(row.get("last12_avg_win_loss") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 10.0 and last_wr >= 48.0 and last_wl >= 1.85:
        return "EXACT_MT5_REPLAY_CANDIDATE_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_SPARSE_CLUE"
    if wl >= 2.0:
        return "PAYOFF_ONLY_WR_FAIL"
    if wr >= 50.0:
        return "WR_ONLY_PAYOFF_FAIL"
    return "REJECT_NO_SPARSE_CORE_SHAPE"


def round_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in metrics.items():
        out[key] = round(value, 4) if isinstance(value, float) else value
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fields = keys
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_bars()
    params_list = build_params()
    print(f"loaded bars={len(df)} variants={len(params_list)}", flush=True)

    design_df = df[(df["timestamp_utc"] >= DESIGN_START) & (df["timestamp_utc"] <= DESIGN_END)].copy()
    design_df.reset_index(drop=True, inplace=True)
    exam_df = df[(df["timestamp_utc"] >= EXAM_START) & (df["timestamp_utc"] <= EXAM_END)].copy()
    exam_df.reset_index(drop=True, inplace=True)
    design_records = design_df.to_dict("records")
    exam_records = exam_df.to_dict("records")

    design_rows: list[dict[str, Any]] = []
    for index, params in enumerate(params_list, start=1):
        candidates = signal_candidates(design_df, params)
        trades = simulate(design_records, candidates, params)
        metrics = round_metrics(summary_metrics(trades, DESIGN_MARKET_DAYS))
        row = {**asdict(params), **metrics, "score": round(owner_score(metrics), 4)}
        design_rows.append(row)
        if index % 64 == 0:
            print(f"design {index}/{len(params_list)}", flush=True)

    design_rows.sort(key=lambda row: float(row["score"]), reverse=True)
    frozen = design_rows[:5]

    param_by_name = {params.name: params for params in params_list}
    exam_rows: list[dict[str, Any]] = []
    exam_trades_by_name: dict[str, list[dict[str, Any]]] = {}
    for design_row in frozen:
        params = param_by_name[str(design_row["name"])]
        candidates = signal_candidates(exam_df, params)
        trades = simulate(exam_records, candidates, params)
        exam_trades_by_name[params.name] = trades
        metrics = summary_metrics(trades, EXAM_MARKET_DAYS)
        last12 = summary_metrics(
            [trade for trade in trades if LAST12_START <= pd.Timestamp(trade["entry_time_utc"]) <= LAST12_END],
            LAST12_MARKET_DAYS,
        )
        stress = summary_metrics(trades, EXAM_MARKET_DAYS, cost_per_trade=0.30)
        row = {
            **asdict(params),
            **round_metrics(metrics),
            "design_score": design_row["score"],
            "design_win_rate_pct": design_row["win_rate_pct"],
            "design_avg_win_loss": design_row["avg_win_loss"],
            "design_active_weekday_pct": design_row["active_weekday_pct"],
            "last12_win_rate_pct": round(last12["win_rate_pct"], 4),
            "last12_avg_win_loss": round(last12["avg_win_loss"] or 0.0, 4),
            "last12_active_weekday_pct": round(last12["active_weekday_pct"], 4),
            "stress_030_avg_win_loss": round(stress["avg_win_loss"] or 0.0, 4),
        }
        row["decision"] = decision(row)
        row["score"] = round(owner_score(row), 4)
        exam_rows.append(row)

    exam_rows.sort(key=lambda row: float(row["score"]), reverse=True)
    best = exam_rows[0] if exam_rows else {}
    best_trades = exam_trades_by_name.get(str(best.get("name")), []) if best else []

    design_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DESIGN.csv"
    exam_csv = REPORTS_DIR / f"{OUTPUT_STEM}_EXAM.csv"
    trades_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_EXAM_TRADES.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    write_csv(design_csv, design_rows)
    write_csv(exam_csv, exam_rows)
    write_csv(
        trades_csv,
        best_trades,
        [
            "variant",
            "entry_time_utc",
            "exit_time_utc",
            "entry_date",
            "direction",
            "family",
            "entry",
            "sl",
            "tp",
            "risk",
            "pnl_usd_001lot",
            "r_multiple",
            "exit_reason",
            "entry_hour_dubai",
            "stop_anchor",
        ],
    )

    verdict = "NO_EXACT_MT5_REPLAY_CANDIDATE"
    if any(row["decision"] == "EXACT_MT5_REPLAY_CANDIDATE_DIAGNOSTIC" for row in exam_rows):
        verdict = "DIAGNOSTIC_EXACT_MT5_REPLAY_CANDIDATE_FOUND"
    elif any(row["decision"] == "CORE_SHAPE_SPARSE_CLUE" for row in exam_rows):
        verdict = "CORE_SHAPE_SPARSE_CLUE_NO_REPLAY"

    payload = {
        "status": verdict,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "prereg": rel(DOC_PATH),
        "bar_path": rel(BAR_PATH),
        "variant_count": len(params_list),
        "design_window": [DESIGN_START.isoformat(), DESIGN_END.isoformat()],
        "exam_window": [EXAM_START.isoformat(), EXAM_END.isoformat()],
        "frozen_exam_count": len(exam_rows),
        "best_exam": best,
        "decision": best.get("decision") if best else "NO_ROWS",
        "reports": {
            "md": rel(md_path),
            "json": rel(json_path),
            "design_csv": rel(design_csv),
            "exam_csv": rel(exam_csv),
            "best_trades_csv": rel(trades_csv),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    top_design_lines = []
    for rank, row in enumerate(design_rows[:10], start=1):
        top_design_lines.append(
            "| {rank} | `{name}` | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {profit_factor:.4f} | {net_usd_001lot:.2f} | {score:.2f} |".format(
                rank=rank,
                **row,
            )
        )
    exam_lines = []
    for rank, row in enumerate(exam_rows, start=1):
        exam_lines.append(
            "| {rank} | `{decision}` | `{name}` | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {profit_factor:.4f} | {net_usd_001lot:.2f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f}/{last12_active_weekday_pct:.2f} | {stress_030_avg_win_loss:.4f} |".format(
                rank=rank,
                **row,
            )
        )

    md = "\n".join(
        [
            "# A1 XAU D1/H4 Sparse Quality 2R Scout - 2026-07-05",
            "",
            f"Status: `{verdict}`",
            "",
            "Scope: offline diagnostic only. No MT5 terminal, chart, preset, order, position, or broker runtime was touched.",
            "",
            "## Preregistration",
            "",
            f"- Prereg: `{rel(DOC_PATH)}`",
            f"- Variants in design ledger: `{len(params_list)}`",
            f"- Frozen exam rows: `{len(exam_rows)}`",
            "- Design window selects candidates; exam rows below are the only frozen candidates evaluated after selection.",
            "- D1 context uses completed prior Dubai day bars. H4 confirmation uses completed UTC 4-hour blocks. Entry is next M5 open.",
            "",
            "## Best Exam Result",
            "",
            "| Field | Value |",
            "|---|---:|",
            f"| Decision | `{best.get('decision', 'NO_ROWS')}` |",
            f"| Variant | `{best.get('name', 'NO_ROWS')}` |",
            f"| Signals | {best.get('signals', 0)} |",
            f"| Win rate | {float(best.get('win_rate_pct') or 0):.2f}% |",
            f"| Avg win/loss | {float(best.get('avg_win_loss') or 0):.4f} |",
            f"| Active weekdays | {float(best.get('active_weekday_pct') or 0):.2f}% |",
            f"| PF | {float(best.get('profit_factor') or 0):.4f} |",
            f"| Net USD at 0.01 lot approx | {float(best.get('net_usd_001lot') or 0):.2f} |",
            f"| Last 12 WR/W-L/active | {float(best.get('last12_win_rate_pct') or 0):.2f}% / {float(best.get('last12_avg_win_loss') or 0):.4f} / {float(best.get('last12_active_weekday_pct') or 0):.2f}% |",
            f"| +0.30/trade stress W/L | {float(best.get('stress_030_avg_win_loss') or 0):.4f} |",
            "",
            "## Frozen Exam Rows",
            "",
            "| Rank | Decision | Variant | Signals | WR | W/L | Active | PF | Net | Last12 WR/W-L/Active | Stress W/L |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            *exam_lines,
            "",
            "## Top Design Rows",
            "",
            "| Rank | Variant | Signals | WR | W/L | Active | PF | Net | Score |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
            *top_design_lines,
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{verdict}`",
            "- This is not a demo spec and not a headline result; exact MT5 Strategy Tester replay is still required for promotion.",
            "- A sparse candidate only earns value as a future component if it can preserve high WR and 2R without damaging the current exact-ledger frontier.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Design CSV: `{rel(design_csv)}`",
            f"- Exam CSV: `{rel(exam_csv)}`",
            f"- Best exam trades CSV: `{rel(trades_csv)}`",
            f"- Report: `{rel(md_path)}`",
            "",
        ]
    )
    md_path.write_text(md, encoding="utf-8")
    print(f"wrote {md_path}", flush=True)


if __name__ == "__main__":
    main()
