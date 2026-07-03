from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
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
OUTPUT_STEM = "XAU_M5_SESSION_OPENING_DRIVE_SCREEN_2026_07_03"

SCREEN_START = pd.Timestamp("2022-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    family: str
    direction_mode: str
    sessions: tuple[str, ...]
    opening_bars: int
    rr: float
    min_opening_range_atr: float
    max_opening_range_atr: float
    break_buffer_atr: float
    close_loc: float
    min_body: float
    min_risk_atr: float
    max_risk_atr: float
    max_cost_r: float
    time_stop_bars: int
    trend_filter: str
    one_trade_per_session: bool


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def market_days(start: date, end: date) -> int:
    total = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current += timedelta(days=1)
    return total


def session_bucket(hour: int) -> str:
    if 0 <= int(hour) <= 5:
        return "night"
    if 6 <= int(hour) <= 11:
        return "morning"
    if 12 <= int(hour) <= 15:
        return "afternoon"
    if 16 <= int(hour) <= 19:
        return "evening"
    return "late"


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
        "tick_count",
        "volume_sum",
    ]
    df = pd.read_csv(BAR_PATH, usecols=usecols)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df[(df["timestamp_utc"] >= SCREEN_START) & (df["timestamp_utc"] <= SCREEN_END)].copy()
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
    df["ema20"] = df["mid_close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["mid_close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["mid_close"].ewm(span=200, adjust=False).mean()
    df["ema50_slope_atr"] = (df["ema50"] - df["ema50"].shift(12)) / df["atr14"]
    candle_range = (df["mid_high"] - df["mid_low"]).replace(0, pd.NA)
    df["body_frac"] = ((df["mid_close"] - df["mid_open"]).abs() / candle_range).fillna(0.0)
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["range_atr"] = candle_range / df["atr14"]
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()
    df["dubai_time"] = df["timestamp_utc"] + pd.Timedelta(hours=4)
    df["dubai_date"] = df["dubai_time"].dt.date.astype(str)
    df["dubai_hour"] = df["dubai_time"].dt.hour
    df["entry_date"] = df["dubai_date"]
    df["session"] = df["dubai_hour"].map(session_bucket)
    df["session_id"] = df["dubai_date"] + "_" + df["session"]
    df["session_bar_index"] = df.groupby("session_id").cumcount()

    h1 = df.set_index("timestamp_utc").resample("1h").agg({"mid_close": "last"}).dropna()
    h1["h1_ema20"] = h1["mid_close"].ewm(span=20, adjust=False).mean()
    h1["h1_ema50"] = h1["mid_close"].ewm(span=50, adjust=False).mean()
    h1["h1_slope"] = h1["h1_ema20"] - h1["h1_ema20"].shift(3)
    h1 = h1[["h1_ema20", "h1_ema50", "h1_slope"]].reset_index()
    df = pd.merge_asof(df.sort_values("timestamp_utc"), h1, on="timestamp_utc", direction="backward")
    required = [
        "atr14",
        "ema20",
        "ema50",
        "ema200",
        "ema50_slope_atr",
        "body_frac",
        "close_location",
        "spread_price",
        "h1_ema20",
        "h1_ema50",
        "h1_slope",
    ]
    return df.dropna(subset=required).reset_index(drop=True)


def trend_ok(row: dict[str, Any], direction: str, params: Params) -> bool:
    if params.trend_filter == "none":
        return True
    if params.trend_filter == "m5_ema":
        if direction == "LONG":
            return float(row["ema20"]) > float(row["ema50"]) and float(row["ema50_slope_atr"]) > 0
        return float(row["ema20"]) < float(row["ema50"]) and float(row["ema50_slope_atr"]) < 0
    if params.trend_filter == "h1":
        if direction == "LONG":
            return float(row["h1_ema20"]) > float(row["h1_ema50"]) and float(row["h1_slope"]) > 0
        return float(row["h1_ema20"]) < float(row["h1_ema50"]) and float(row["h1_slope"]) < 0
    if params.trend_filter == "h1_m5":
        return trend_ok(row, direction, Params(**{**asdict(params), "trend_filter": "h1"})) and trend_ok(
            row, direction, Params(**{**asdict(params), "trend_filter": "m5_ema"})
        )
    return True


def opening_range_for(rows: list[dict[str, Any]], index: int, opening_bars: int) -> tuple[float, float, int] | None:
    row = rows[index]
    session_id = row["session_id"]
    if int(row["session_bar_index"]) < opening_bars:
        return None
    start = index - int(row["session_bar_index"])
    end = start + opening_bars
    if end > index:
        return None
    opening_rows = rows[start:end]
    if len(opening_rows) != opening_bars or any(item["session_id"] != session_id for item in opening_rows):
        return None
    high = max(float(item["mid_high"]) for item in opening_rows)
    low = min(float(item["mid_low"]) for item in opening_rows)
    return high, low, start


def signal_for(rows: list[dict[str, Any]], index: int, params: Params) -> tuple[str, float, float, int] | None:
    row = rows[index]
    if row["session"] not in params.sessions:
        return None
    opening = opening_range_for(rows, index, params.opening_bars)
    if opening is None:
        return None
    opening_high, opening_low, session_start_index = opening
    atr = float(row["atr14"])
    if atr <= 0:
        return None
    opening_range_atr = (opening_high - opening_low) / atr
    if not (params.min_opening_range_atr <= opening_range_atr <= params.max_opening_range_atr):
        return None
    if float(row["body_frac"]) < params.min_body:
        return None

    buffer = params.break_buffer_atr * atr
    close_location = float(row["close_location"])
    long_allowed = params.direction_mode in {"both", "long"}
    short_allowed = params.direction_mode in {"both", "short"}

    if params.family == "opening_breakout":
        if (
            long_allowed
            and float(row["mid_close"]) > opening_high + buffer
            and close_location >= params.close_loc
            and trend_ok(row, "LONG", params)
        ):
            return "LONG", opening_high, opening_low, session_start_index
        if (
            short_allowed
            and float(row["mid_close"]) < opening_low - buffer
            and close_location <= 1.0 - params.close_loc
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT", opening_high, opening_low, session_start_index

    if params.family == "failed_opening_break":
        previous = rows[index - 1]
        if (
            short_allowed
            and float(previous["mid_high"]) > opening_high + buffer
            and float(row["mid_close"]) < opening_high
            and close_location <= 0.45
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT", opening_high, opening_low, session_start_index
        if (
            long_allowed
            and float(previous["mid_low"]) < opening_low - buffer
            and float(row["mid_close"]) > opening_low
            and close_location >= 0.55
            and trend_ok(row, "LONG", params)
        ):
            return "LONG", opening_high, opening_low, session_start_index
    return None


def simulate_exit(
    rows: list[dict[str, Any]], entry_index: int, direction: str, entry: float, risk: float, rr: float, time_stop_bars: int
) -> tuple[int, float, str]:
    if direction == "LONG":
        sl = entry - risk
        tp = entry + rr * risk
    else:
        sl = entry + risk
        tp = entry - rr * risk
    end = min(entry_index + time_stop_bars, len(rows) - 1)
    for index in range(entry_index, end + 1):
        bar = rows[index]
        if direction == "LONG":
            hit_sl = float(bar["bid_low"]) <= sl
            hit_tp = float(bar["bid_high"]) >= tp
            if hit_sl and hit_tp:
                return index, sl, "sl_adverse_first"
            if hit_sl:
                return index, sl, "sl"
            if hit_tp:
                return index, tp, "tp"
        else:
            hit_sl = float(bar["ask_high"]) >= sl
            hit_tp = float(bar["ask_low"]) <= tp
            if hit_sl and hit_tp:
                return index, sl, "sl_adverse_first"
            if hit_sl:
                return index, sl, "sl"
            if hit_tp:
                return index, tp, "tp"
    last = rows[end]
    return end, float(last["bid_close"] if direction == "LONG" else last["ask_close"]), "time_stop"


def simulate(df: pd.DataFrame, params: Params) -> list[dict[str, Any]]:
    rows = df.to_dict("records")
    trades: list[dict[str, Any]] = []
    traded_sessions: set[str] = set()
    index = 260
    while index < len(rows) - params.time_stop_bars - 2:
        row = rows[index]
        if params.one_trade_per_session and row["session_id"] in traded_sessions:
            index += 1
            continue
        signal = signal_for(rows, index, params)
        if signal is None:
            index += 1
            continue
        direction, opening_high, opening_low, _session_start_index = signal
        entry_index = index + 1
        entry_row = rows[entry_index]
        atr = float(row["atr14"])
        spread = float(entry_row["spread_price"])
        if direction == "LONG":
            entry = float(entry_row["ask_open"])
            structure = opening_low if params.family == "opening_breakout" else min(opening_low, float(row["mid_low"]))
            risk = max(entry - structure + 0.05 * atr, params.min_risk_atr * atr, 3.0 * spread)
        else:
            entry = float(entry_row["bid_open"])
            structure = opening_high if params.family == "opening_breakout" else max(opening_high, float(row["mid_high"]))
            risk = max(structure - entry + 0.05 * atr, params.min_risk_atr * atr, 3.0 * spread)
        if risk <= 0 or risk > params.max_risk_atr * atr or (spread / risk) > params.max_cost_r:
            index += 1
            continue
        exit_index, exit_price, reason = simulate_exit(rows, entry_index, direction, entry, risk, params.rr, params.time_stop_bars)
        profit = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
        trades.append(
            {
                "variant": params.name,
                "family": params.family,
                "entry_time": entry_row["timestamp_utc"].isoformat(),
                "entry_date": entry_row["entry_date"],
                "entry_hour": int(entry_row["dubai_hour"]),
                "entry_session": entry_row["session"],
                "session_id": entry_row["session_id"],
                "direction": direction,
                "entry": round(entry, 2),
                "exit_time": rows[exit_index]["timestamp_utc"].isoformat(),
                "exit": round(exit_price, 2),
                "profit": round(profit, 2),
                "r": round(profit / risk, 4),
                "risk": round(risk, 4),
                "atr14": round(atr, 4),
                "spread": round(spread, 4),
                "cost_r": round(spread / risk, 4),
                "exit_reason": reason,
                "opening_high": round(opening_high, 2),
                "opening_low": round(opening_low, 2),
                "opening_range_atr": round((opening_high - opening_low) / atr, 4),
                "body_frac": round(float(row["body_frac"]), 4),
                "close_location": round(float(row["close_location"]), 4),
                "trend_filter": params.trend_filter,
            }
        )
        traded_sessions.add(row["session_id"])
        index = exit_index + 1
    return trades


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def top_removed(values: list[float], count: int) -> float:
    wins = sorted((value for value in values if value > 0), reverse=True)
    return round(sum(values) - sum(wins[:count]), 2)


def rolling_negative(values: list[float], window: int) -> dict[str, Any]:
    if len(values) < window:
        return {"window": window, "available": False}
    nets = [sum(values[index : index + window]) for index in range(len(values) - window + 1)]
    return {"window": window, "available": True, "worst": round(min(nets), 2), "negative": sum(value < 0 for value in nets)}


def summarize(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {"name": name, "trades": 0}
    values = [float(row["r"]) for row in trades]
    ordered = [float(row["r"]) for row in sorted(trades, key=lambda item: item["exit_time"])]
    by_day: dict[str, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    by_direction: dict[str, list[float]] = defaultdict(list)
    by_session: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["r"]))
        by_month[row["entry_date"][:7]].append(float(row["r"]))
        by_direction[row["direction"]].append(float(row["r"]))
        by_session[row["entry_session"]].append(float(row["r"]))
    start = min(pd.Timestamp(row["entry_time"]).date() for row in trades)
    end = max(pd.Timestamp(row["entry_time"]).date() for row in trades)
    days = market_days(start, end)
    wins = sum(value > 0 for value in values)
    return {
        "name": name,
        "family": trades[0]["family"],
        "trades": len(trades),
        "wins": wins,
        "losses": sum(value < 0 for value in values),
        "win_rate_pct": round(100.0 * wins / len(trades), 2),
        "net_r": round(sum(values), 2),
        "profit_factor_r": profit_factor(values),
        "market_days": days,
        "active_days": len(by_day),
        "trades_per_market_day": round(len(trades) / days, 2),
        "trades_per_active_day": round(len(trades) / len(by_day), 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(day_values) >= 3 for day_values in by_day.values()) / days, 2),
        "positive_months": sum(sum(month_values) > 0 for month_values in by_month.values()),
        "negative_months": sum(sum(month_values) < 0 for month_values in by_month.values()),
        "top100_removed_r": top_removed(values, 100),
        "top200_removed_r": top_removed(values, 200),
        "top300_removed_r": top_removed(values, 300),
        "rolling100": rolling_negative(ordered, 100),
        "rolling250": rolling_negative(ordered, 250),
        "direction": {
            direction: {"trades": len(direction_values), "net_r": round(sum(direction_values), 2), "pf_r": profit_factor(direction_values)}
            for direction, direction_values in sorted(by_direction.items())
        },
        "session": {
            session: {"trades": len(session_values), "net_r": round(sum(session_values), 2), "pf_r": profit_factor(session_values)}
            for session, session_values in sorted(by_session.items())
        },
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 500:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 3.0:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 60.0:
        return "FAIL_WR"
    if (row.get("profit_factor_r") or 0.0) < 1.25:
        return "FAIL_PF"
    if row.get("top200_removed_r", 0.0) <= 0:
        return "FAIL_TOP200"
    if row.get("top300_removed_r", 0.0) <= 0:
        return "REVISE_TOP300"
    if row.get("rolling250", {}).get("negative", 1) > 0:
        return "REVISE_ROLLING250"
    return "SESSION_OPENING_DRIVE_REVIEW_CANDIDATE"


def build_params() -> list[Params]:
    session_sets = {
        "all": ("night", "morning", "afternoon", "evening", "late"),
        "liquid": ("morning", "afternoon", "evening"),
        "night_evening": ("night", "evening"),
        "morning_evening": ("morning", "evening"),
    }
    rows: list[Params] = []
    for family in ("opening_breakout", "failed_opening_break"):
        for direction in ("both", "long", "short"):
            for session_name, sessions in session_sets.items():
                for opening_bars in (3, 6, 9):
                    for rr in (0.7, 1.0):
                        for trend in ("none", "m5_ema", "h1"):
                            name = (
                                f"session_{family}_{direction}_{session_name}_or{opening_bars}_"
                                f"rr{str(rr).replace('.', 'p')}_{trend}"
                            )
                            rows.append(
                                Params(
                                    name=name,
                                    family=family,
                                    direction_mode=direction,
                                    sessions=sessions,
                                    opening_bars=opening_bars,
                                    rr=rr,
                                    min_opening_range_atr=0.35,
                                    max_opening_range_atr=2.8,
                                    break_buffer_atr=0.05,
                                    close_loc=0.62,
                                    min_body=0.25,
                                    min_risk_atr=0.55,
                                    max_risk_atr=3.0,
                                    max_cost_r=0.12,
                                    time_stop_bars=12 if rr < 0.8 else 18,
                                    trend_filter=trend,
                                    one_trade_per_session=True,
                                )
                            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        "# XAU M5 Session Opening Drive Screen - 2026-07-03",
        "",
        "Scope: offline bar-level discovery only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Hypothesis",
        "",
        "Test whether XAUUSD has a repeatable session-opening drive or failed-break reversal edge around Dubai session opens. This is distinct from the existing momentum package and the suspended breakout-retest family.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision')}` |",
        f"| Variant | `{best.get('name')}` |",
        f"| Trades | {best.get('trades')} |",
        f"| Win rate | {best.get('win_rate_pct')}% |",
        f"| PF R | {best.get('profit_factor_r')} |",
        f"| Net R | {best.get('net_r')} |",
        f"| Trades / market day | {best.get('trades_per_market_day')} |",
        f"| Top200 R | {best.get('top200_removed_r')} |",
        f"| Top300 R | {best.get('top300_removed_r')} |",
        f"| Rolling250 negative | {best.get('rolling250', {}).get('negative')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Variant | Trades | WR | PF R | Net R | T/day | Top300 R | Roll250 neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top300:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision"),
                name=row.get("name"),
                trades=row.get("trades", 0),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor_r"),
                net=row.get("net_r", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top300=row.get("top300_removed_r", 0.0),
                roll=row.get("rolling250", {}).get("negative", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "Any review candidate must be exact-tested in MT5 Strategy Tester before demo use.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Best trades CSV: `{payload['best_trades_csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    df = load_bars()
    summaries: list[dict[str, Any]] = []
    trades_by_name: dict[str, list[dict[str, Any]]] = {}
    params_list = build_params()
    print(f"screening {len(params_list)} session opening-drive variants", flush=True)
    for offset, params in enumerate(params_list, start=1):
        if offset == 1 or offset % 25 == 0:
            print(f"variant {offset}/{len(params_list)}: {params.name}", flush=True)
        trades = simulate(df, params)
        summary = summarize(params.name, trades) if trades else {"name": params.name, "family": params.family, "trades": 0}
        summary["params"] = asdict(params)
        summary["decision"] = decision(summary)
        summaries.append(summary)
        trades_by_name[params.name] = trades

    summaries.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -float(row.get("trades_per_market_day") or 0.0),
            -float(row.get("profit_factor_r") or 0.0),
            -float(row.get("net_r") or 0.0),
        )
    )
    best = summaries[0]
    verdict = (
        "FOUND_SESSION_OPENING_DRIVE_REVIEW_CANDIDATE"
        if str(best.get("decision")).endswith("CANDIDATE")
        else "NO_SESSION_OPENING_DRIVE_CANDIDATE"
    )
    next_action = "port_to_exact_mt5_strategy_tester" if verdict.startswith("FOUND") else "continue_new_mechanism_search"

    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    payload = {
        "status": "PASS_SESSION_OPENING_DRIVE_SCREEN_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_discovery_only_no_runtime_change",
        "window": f"{SCREEN_START.date()} -> {SCREEN_END.date()}",
        "variant_count": len(summaries),
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": summaries[:50],
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
        "best_trades_csv": rel(output_trades),
    }
    output_md.write_text(render(payload), encoding="utf-8")
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(
        output_csv,
        summaries,
        [
            "decision",
            "family",
            "name",
            "trades",
            "win_rate_pct",
            "profit_factor_r",
            "net_r",
            "trades_per_market_day",
            "top100_removed_r",
            "top200_removed_r",
            "top300_removed_r",
            "positive_months",
            "negative_months",
        ],
    )
    best_trades = trades_by_name.get(str(best.get("name")), [])
    if best_trades:
        write_csv(
            output_trades,
            best_trades,
            [
                "variant",
                "family",
                "entry_time",
                "entry_date",
                "entry_hour",
                "entry_session",
                "session_id",
                "direction",
                "entry",
                "exit_time",
                "exit",
                "r",
                "risk",
                "atr14",
                "spread",
                "cost_r",
                "exit_reason",
                "opening_high",
                "opening_low",
                "opening_range_atr",
                "body_frac",
                "close_location",
                "trend_filter",
            ],
        )
    print(f"wrote {output_md}")
    print(f"verdict={verdict} best={best.get('name')} decision={best.get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
