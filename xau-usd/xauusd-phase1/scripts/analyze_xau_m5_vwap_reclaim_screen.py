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
OUTPUT_STEM = "XAU_M5_VWAP_RECLAIM_SCREEN_2026_07_03"

SCREEN_START = pd.Timestamp("2022-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    family: str
    direction_mode: str
    anchor: str
    rr: float
    min_distance_atr: float
    max_distance_atr: float
    min_body: float
    close_loc: float
    min_slope_atr: float
    min_risk_atr: float
    max_risk_atr: float
    max_cost_r: float
    time_stop_bars: int
    blocked_hours: tuple[int, ...]
    h1_trend: bool


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
    candle_range = (df["mid_high"] - df["mid_low"]).replace(0, pd.NA)
    df["body_frac"] = ((df["mid_close"] - df["mid_open"]).abs() / candle_range).fillna(0.0)
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["move3_atr"] = (df["mid_close"] - df["mid_close"].shift(3)) / df["atr14"]
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()
    df["typical"] = (df["mid_high"] + df["mid_low"] + df["mid_close"]) / 3.0
    df["weight"] = df["volume_sum"].where(df["volume_sum"] > 0, df["tick_count"]).fillna(1.0).clip(lower=1.0)
    df["dubai_time"] = df["timestamp_utc"] + pd.Timedelta(hours=4)
    df["dubai_date"] = df["dubai_time"].dt.date.astype(str)
    df["dubai_hour"] = df["dubai_time"].dt.hour
    df["entry_date"] = df["dubai_date"]
    df["session_id"] = df["dubai_date"] + "_" + df["dubai_hour"].map(session_bucket)

    for anchor, group_key in (("daily", "dubai_date"), ("session", "session_id")):
        pv = df["typical"] * df["weight"]
        df[f"{anchor}_vwap"] = pv.groupby(df[group_key]).cumsum() / df["weight"].groupby(df[group_key]).cumsum()
        df[f"{anchor}_vwap_slope_atr"] = (df[f"{anchor}_vwap"] - df[f"{anchor}_vwap"].shift(6)) / df["atr14"]
        df[f"{anchor}_vwap_dist_atr"] = (df["mid_close"] - df[f"{anchor}_vwap"]) / df["atr14"]
        df[f"{anchor}_prev_dist_atr"] = df[f"{anchor}_vwap_dist_atr"].shift(1)

    h1 = df.set_index("timestamp_utc").resample("1h").agg({"mid_close": "last"}).dropna()
    h1["h1_ema20"] = h1["mid_close"].ewm(span=20, adjust=False).mean()
    h1["h1_ema50"] = h1["mid_close"].ewm(span=50, adjust=False).mean()
    h1["h1_slope"] = h1["h1_ema20"] - h1["h1_ema20"].shift(3)
    h1 = h1[["h1_ema20", "h1_ema50", "h1_slope"]].reset_index()
    df = pd.merge_asof(df.sort_values("timestamp_utc"), h1, on="timestamp_utc", direction="backward")
    required = [
        "atr14",
        "body_frac",
        "close_location",
        "daily_vwap",
        "session_vwap",
        "daily_prev_dist_atr",
        "session_prev_dist_atr",
        "daily_vwap_slope_atr",
        "session_vwap_slope_atr",
        "h1_ema20",
        "h1_ema50",
        "h1_slope",
    ]
    return df.dropna(subset=required).reset_index(drop=True)


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


def trend_ok(row: dict[str, Any], direction: str, params: Params) -> bool:
    if not params.h1_trend:
        return True
    if direction == "LONG":
        return float(row["h1_ema20"]) > float(row["h1_ema50"]) and float(row["h1_slope"]) > 0
    return float(row["h1_ema20"]) < float(row["h1_ema50"]) and float(row["h1_slope"]) < 0


def signal_for(row: dict[str, Any], params: Params) -> str | None:
    if int(row["dubai_hour"]) in params.blocked_hours:
        return None
    if float(row["body_frac"]) < params.min_body:
        return None
    dist = float(row[f"{params.anchor}_vwap_dist_atr"])
    prev_dist = float(row[f"{params.anchor}_prev_dist_atr"])
    slope = float(row[f"{params.anchor}_vwap_slope_atr"])
    close_loc = float(row["close_location"])
    long_allowed = params.direction_mode in {"both", "long"}
    short_allowed = params.direction_mode in {"both", "short"}

    if params.family == "reclaim":
        if (
            long_allowed
            and prev_dist <= -params.min_distance_atr
            and dist >= 0.0
            and abs(dist) <= params.max_distance_atr
            and close_loc >= params.close_loc
            and slope >= -params.min_slope_atr
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and prev_dist >= params.min_distance_atr
            and dist <= 0.0
            and abs(dist) <= params.max_distance_atr
            and close_loc <= 1.0 - params.close_loc
            and slope <= params.min_slope_atr
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "bounce":
        if (
            long_allowed
            and -params.max_distance_atr <= dist <= params.min_distance_atr
            and float(row["mid_low"]) <= float(row[f"{params.anchor}_vwap"])
            and close_loc >= params.close_loc
            and slope >= params.min_slope_atr
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and -params.min_distance_atr <= dist <= params.max_distance_atr
            and float(row["mid_high"]) >= float(row[f"{params.anchor}_vwap"])
            and close_loc <= 1.0 - params.close_loc
            and slope <= -params.min_slope_atr
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "extreme_revert":
        if (
            short_allowed
            and dist >= params.max_distance_atr
            and close_loc <= 1.0 - params.close_loc
            and not trend_ok(row, "LONG", params)
        ):
            return "SHORT"
        if (
            long_allowed
            and dist <= -params.max_distance_atr
            and close_loc >= params.close_loc
            and not trend_ok(row, "SHORT", params)
        ):
            return "LONG"
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
    index = 260
    while index < len(rows) - params.time_stop_bars - 2:
        row = rows[index]
        direction = signal_for(row, params)
        if direction is None:
            index += 1
            continue
        entry_index = index + 1
        entry_row = rows[entry_index]
        atr = float(row["atr14"])
        spread = float(entry_row["spread_price"])
        vwap = float(row[f"{params.anchor}_vwap"])
        if direction == "LONG":
            entry = float(entry_row["ask_open"])
            structure = min(float(row["mid_low"]), vwap)
            risk = max(entry - structure, params.min_risk_atr * atr, 3.0 * spread)
        else:
            entry = float(entry_row["bid_open"])
            structure = max(float(row["mid_high"]), vwap)
            risk = max(structure - entry, params.min_risk_atr * atr, 3.0 * spread)
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
                "entry_session": session_bucket(int(entry_row["dubai_hour"])),
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
                "dist_atr": round(float(row[f"{params.anchor}_vwap_dist_atr"]), 4),
                "slope_atr": round(float(row[f"{params.anchor}_vwap_slope_atr"]), 4),
                "body_frac": round(float(row["body_frac"]), 4),
                "close_location": round(float(row["close_location"]), 4),
            }
        )
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
    values = [float(row["profit"]) for row in trades]
    ordered = [float(row["profit"]) for row in sorted(trades, key=lambda item: item["exit_time"])]
    by_day: dict[str, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    by_direction: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["profit"]))
        by_month[row["entry_date"][:7]].append(float(row["profit"]))
        by_direction[row["direction"]].append(float(row["profit"]))
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
        "net": round(sum(values), 2),
        "profit_factor": profit_factor(values),
        "market_days": days,
        "active_days": len(by_day),
        "trades_per_market_day": round(len(trades) / days, 2),
        "trades_per_active_day": round(len(trades) / len(by_day), 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(day_values) >= 3 for day_values in by_day.values()) / days, 2),
        "positive_months": sum(sum(month_values) > 0 for month_values in by_month.values()),
        "negative_months": sum(sum(month_values) < 0 for month_values in by_month.values()),
        "top50_removed": top_removed(values, 50),
        "top100_removed": top_removed(values, 100),
        "top200_removed": top_removed(values, 200),
        "rolling100": rolling_negative(ordered, 100),
        "rolling250": rolling_negative(ordered, 250),
        "direction": {
            direction: {"trades": len(direction_values), "net": round(sum(direction_values), 2), "pf": profit_factor(direction_values)}
            for direction, direction_values in sorted(by_direction.items())
        },
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 1000:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 3.0:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 60.0:
        return "FAIL_WR"
    if (row.get("profit_factor") or 0.0) < 1.25:
        return "FAIL_PF"
    if row.get("top100_removed", 0.0) <= 0:
        return "FAIL_TOP100"
    if row.get("top200_removed", 0.0) <= 0:
        return "FAIL_TOP200"
    if row.get("rolling250", {}).get("negative", 1) > 0:
        return "REVISE_ROLLING250"
    return "VWAP_REVIEW_CANDIDATE"


def build_params() -> list[Params]:
    blocked_sets = {
        "all": (),
        "no_rollover": (0, 1, 22, 23),
        "active": (0, 1, 2, 3, 4, 21, 22, 23),
    }
    rows: list[Params] = []
    for family in ("reclaim", "bounce"):
        for anchor in ("session",):
            for direction in ("both", "long", "short"):
                for rr in (0.7,):
                    for blocked_name, blocked_hours in blocked_sets.items():
                        if blocked_name == "active":
                            continue
                        distances = ((0.25, 1.4),)
                        for min_dist, max_dist in distances:
                            name = (
                                f"vwap_{family}_{anchor}_{direction}_rr{str(rr).replace('.', 'p')}_"
                                f"d{str(min_dist).replace('.', 'p')}_{str(max_dist).replace('.', 'p')}_{blocked_name}"
                            )
                            rows.append(
                                Params(
                                    name=name,
                                    family=family,
                                    direction_mode=direction,
                                    anchor=anchor,
                                    rr=rr,
                                    min_distance_atr=min_dist,
                                    max_distance_atr=max_dist,
                                    min_body=0.25 if family != "extreme_revert" else 0.15,
                                    close_loc=0.62,
                                    min_slope_atr=0.02,
                                    min_risk_atr=0.55,
                                    max_risk_atr=2.5,
                                    max_cost_r=0.12,
                                    time_stop_bars=18 if rr >= 1.0 else 12,
                                    blocked_hours=blocked_hours,
                                    h1_trend=family != "extreme_revert",
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
        "# XAU M5 VWAP Reclaim Screen - 2026-07-03",
        "",
        "Scope: offline bar-level discovery only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Hypothesis",
        "",
        "Test session/daily VWAP as a fair-value reference: reclaim, bounce, and extreme-reversion patterns. This is distinct from the existing raw momentum family.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision')}` |",
        f"| Variant | `{best.get('name')}` |",
        f"| Trades | {best.get('trades')} |",
        f"| Win rate | {best.get('win_rate_pct')}% |",
        f"| PF | {best.get('profit_factor')} |",
        f"| Net | {best.get('net')} |",
        f"| Trades / market day | {best.get('trades_per_market_day')} |",
        f"| Top100 removed | {best.get('top100_removed')} |",
        f"| Top200 removed | {best.get('top200_removed')} |",
        f"| Rolling250 negative | {best.get('rolling250', {}).get('negative')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Variant | Trades | WR | PF | Net | T/market day | Top200 | Roll250 neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top200:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision"),
                name=row.get("name"),
                trades=row.get("trades", 0),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor"),
                net=row.get("net", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top200=row.get("top200_removed", 0.0),
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
            "A VWAP candidate must still be exact-tested in MT5 Strategy Tester before any demo use.",
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
    for params in build_params():
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
            -float(row.get("profit_factor") or 0.0),
            -float(row.get("net") or 0.0),
        )
    )
    best = summaries[0]
    verdict = "FOUND_VWAP_REVIEW_CANDIDATE" if str(best.get("decision")).endswith("CANDIDATE") else "NO_VWAP_CANDIDATE"
    next_action = "port_to_exact_mt5_strategy_tester" if verdict.startswith("FOUND") else "continue_different_entry_family"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    payload = {
        "status": "PASS_VWAP_SCREEN_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_discovery_only_no_runtime_change",
        "bar_path": rel(BAR_PATH),
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
            "profit_factor",
            "net",
            "trades_per_market_day",
            "top100_removed",
            "top200_removed",
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
                "direction",
                "entry",
                "exit_time",
                "exit",
                "profit",
                "r",
                "risk",
                "atr14",
                "spread",
                "cost_r",
                "exit_reason",
                "dist_atr",
                "slope_atr",
                "body_frac",
                "close_location",
            ],
        )
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "variant": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net": best.get("net"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top200_removed": best.get("top200_removed"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
