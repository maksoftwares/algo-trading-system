from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
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
OUTPUT_STEM = "XAU_M5_IMPULSE_PULLBACK_RESUME_SCREEN_2026_07_03"

SCREEN_START = pd.Timestamp("2022-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    direction_mode: str
    impulse_bars: int
    impulse_atr: float
    pullback_min_atr: float
    pullback_max_atr: float
    rr: float
    blocked_hours: tuple[int, ...]
    expiry_bars: int = 18
    min_risk_atr: float = 0.65
    max_risk_atr: float = 2.40
    time_stop_bars: int = 18


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


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
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["dubai_hour"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.hour
    df["entry_date"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.date.astype(str)
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()

    # H1 trend is formed from completed M5 bars, then merged back causally.
    h1 = df.set_index("timestamp_utc").resample("1h").agg({"mid_close": "last"}).dropna()
    h1["h1_ema20"] = h1["mid_close"].ewm(span=20, adjust=False).mean()
    h1["h1_ema50"] = h1["mid_close"].ewm(span=50, adjust=False).mean()
    h1["h1_slope"] = h1["h1_ema20"] - h1["h1_ema20"].shift(3)
    h1 = h1[["h1_ema20", "h1_ema50", "h1_slope"]].reset_index()
    df = pd.merge_asof(df.sort_values("timestamp_utc"), h1, on="timestamp_utc", direction="backward")
    return df.dropna(subset=["atr14", "ema50_slope_atr", "h1_ema20", "h1_ema50", "h1_slope"]).reset_index(drop=True)


def htf_ok(row: dict[str, Any], direction: str) -> bool:
    if direction == "LONG":
        return (
            row["h1_ema20"] > row["h1_ema50"]
            and row["h1_slope"] > 0
            and row["ema20"] > row["ema50"] > row["ema200"]
            and row["ema50_slope_atr"] > 0.015
        )
    return (
        row["h1_ema20"] < row["h1_ema50"]
        and row["h1_slope"] < 0
        and row["ema20"] < row["ema50"] < row["ema200"]
        and row["ema50_slope_atr"] < -0.015
    )


def simulate_exit(rows: list[dict[str, Any]], entry_index: int, direction: str, entry: float, risk: float, rr: float, time_stop: int) -> tuple[int, float, str]:
    if direction == "LONG":
        sl = entry - risk
        tp = entry + rr * risk
    else:
        sl = entry + risk
        tp = entry - rr * risk
    exit_index = min(entry_index + time_stop, len(rows) - 1)
    exit_price: float | None = None
    exit_reason = "time_stop"
    for j in range(entry_index, exit_index + 1):
        bar = rows[j]
        if direction == "LONG":
            hit_sl = float(bar["bid_low"]) <= sl
            hit_tp = float(bar["bid_high"]) >= tp
            if hit_sl and hit_tp:
                return j, sl, "sl_adverse_first"
            if hit_sl:
                return j, sl, "sl"
            if hit_tp:
                return j, tp, "tp"
        else:
            hit_sl = float(bar["ask_high"]) >= sl
            hit_tp = float(bar["ask_low"]) <= tp
            if hit_sl and hit_tp:
                return j, sl, "sl_adverse_first"
            if hit_sl:
                return j, sl, "sl"
            if hit_tp:
                return j, tp, "tp"
    last = rows[exit_index]
    exit_price = float(last["bid_close"] if direction == "LONG" else last["ask_close"])
    return exit_index, exit_price, exit_reason


def simulate(df: pd.DataFrame, params: Params) -> list[dict[str, Any]]:
    rows = df.to_dict("records")
    trades: list[dict[str, Any]] = []
    long_setup: dict[str, Any] | None = None
    short_setup: dict[str, Any] | None = None
    i = max(params.impulse_bars + 3, 220)
    while i < len(rows) - params.time_stop_bars - 2:
        row = rows[i]
        hour = int(row["dubai_hour"])
        if hour in params.blocked_hours:
            long_setup = None
            short_setup = None
            i += 1
            continue
        atr = float(row["atr14"])
        if atr <= 0:
            i += 1
            continue

        for direction in ("LONG", "SHORT"):
            if params.direction_mode not in {"both", direction.lower()}:
                continue
            previous = rows[i - params.impulse_bars]
            move_atr = (
                (float(row["mid_close"]) - float(previous["mid_close"])) / atr
                if direction == "LONG"
                else (float(previous["mid_close"]) - float(row["mid_close"])) / atr
            )
            extreme_close = float(row["close_location"]) >= 0.65 if direction == "LONG" else float(row["close_location"]) <= 0.35
            if move_atr >= params.impulse_atr and extreme_close and htf_ok(row, direction):
                window = rows[i - params.impulse_bars : i + 1]
                setup = {
                    "direction": direction,
                    "expires": i + params.expiry_bars,
                    "impulse_index": i,
                    "impulse_high": max(float(bar["mid_high"]) for bar in window),
                    "impulse_low": min(float(bar["mid_low"]) for bar in window),
                    "pullback_seen": False,
                    "pullback_low": float(row["mid_low"]),
                    "pullback_high": float(row["mid_high"]),
                    "move_atr": move_atr,
                }
                if direction == "LONG":
                    long_setup = setup
                else:
                    short_setup = setup

        for setup_name, setup in (("LONG", long_setup), ("SHORT", short_setup)):
            if setup is None:
                continue
            direction = setup["direction"]
            if i <= setup["impulse_index"]:
                continue
            if i > setup["expires"] or not htf_ok(row, direction):
                if direction == "LONG":
                    long_setup = None
                else:
                    short_setup = None
                continue
            if direction == "LONG":
                pullback_depth = (setup["impulse_high"] - float(row["mid_low"])) / atr
                near_ema = float(row["mid_low"]) <= float(row["ema20"]) + 0.25 * atr
                setup["pullback_low"] = min(float(setup["pullback_low"]), float(row["mid_low"]))
                trigger = (
                    setup["pullback_seen"]
                    and float(row["mid_close"]) > float(rows[i - 1]["mid_high"])
                    and float(row["close_location"]) >= 0.60
                    and float(row["mid_close"]) > float(row["ema20"])
                )
            else:
                pullback_depth = (float(row["mid_high"]) - setup["impulse_low"]) / atr
                near_ema = float(row["mid_high"]) >= float(row["ema20"]) - 0.25 * atr
                setup["pullback_high"] = max(float(setup["pullback_high"]), float(row["mid_high"]))
                trigger = (
                    setup["pullback_seen"]
                    and float(row["mid_close"]) < float(rows[i - 1]["mid_low"])
                    and float(row["close_location"]) <= 0.40
                    and float(row["mid_close"]) < float(row["ema20"])
                )
            if params.pullback_min_atr <= pullback_depth <= params.pullback_max_atr and near_ema:
                setup["pullback_seen"] = True
            if not trigger:
                continue
            entry_index = i + 1
            entry_row = rows[entry_index]
            spread = float(entry_row["spread_price"])
            if direction == "LONG":
                entry = float(entry_row["ask_open"])
                structural_risk = entry - float(setup["pullback_low"]) + 0.10 * atr
            else:
                entry = float(entry_row["bid_open"])
                structural_risk = float(setup["pullback_high"]) - entry + 0.10 * atr
            risk = max(structural_risk, params.min_risk_atr * atr, 3.0 * spread)
            if risk <= 0 or risk > params.max_risk_atr * atr:
                if direction == "LONG":
                    long_setup = None
                else:
                    short_setup = None
                continue
            exit_index, exit_price, exit_reason = simulate_exit(rows, entry_index, direction, entry, risk, params.rr, params.time_stop_bars)
            profit = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
            trades.append(
                {
                    "variant": params.name,
                    "entry_time": entry_row["timestamp_utc"].isoformat(),
                    "entry_date": entry_row["entry_date"],
                    "entry_hour": int(entry_row["dubai_hour"]),
                    "direction": direction,
                    "entry": round(entry, 2),
                    "exit_time": rows[exit_index]["timestamp_utc"].isoformat(),
                    "exit": round(exit_price, 2),
                    "profit": round(profit, 2),
                    "r": round(profit / risk, 4),
                    "risk": round(risk, 4),
                    "atr14": round(atr, 4),
                    "spread": round(spread, 4),
                    "exit_reason": exit_reason,
                    "impulse_move_atr": round(float(setup["move_atr"]), 4),
                    "pullback_depth_atr": round(float(pullback_depth), 4),
                    "close_location": round(float(row["close_location"]), 4),
                }
            )
            long_setup = None
            short_setup = None
            i = exit_index + 1
            break
        else:
            i += 1
            continue
    return trades


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def top_removed(values: list[float], count: int) -> float:
    ordered = sorted(values, reverse=True)
    return round(sum(values) - sum(ordered[:count]), 2)


def market_days(start: str, end: str) -> int:
    return len(pd.bdate_range(pd.Timestamp(start), pd.Timestamp(end)))


def summarize_trades(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {"name": name, "trades": 0}
    profits = [float(row["profit"]) for row in trades]
    r_values = [float(row["r"]) for row in trades]
    wins = sum(1 for value in profits if value > 0)
    by_day: dict[str, list[float]] = {}
    by_month: dict[str, list[float]] = {}
    for row in trades:
        by_day.setdefault(row["entry_date"], []).append(float(row["profit"]))
        by_month.setdefault(row["entry_date"][:7], []).append(float(row["profit"]))
    day_values = [sum(values) for values in by_day.values()]
    month_values = [sum(values) for values in by_month.values()]
    start = min(row["entry_date"] for row in trades)
    end = max(row["entry_date"] for row in trades)
    bdays = market_days(start, end)
    return {
        "name": name,
        "trades": len(trades),
        "wins": wins,
        "losses": sum(1 for value in profits if value < 0),
        "win_rate_pct": round(100.0 * wins / len(trades), 2),
        "net_usd": round(sum(profits), 2),
        "profit_factor": profit_factor(profits),
        "net_r": round(sum(r_values), 2),
        "profit_factor_r": profit_factor(r_values),
        "active_days": len(by_day),
        "market_days": bdays,
        "trades_per_market_day": round(len(trades) / bdays, 2) if bdays else 0.0,
        "trades_per_active_day": round(len(trades) / len(by_day), 2) if by_day else 0.0,
        "positive_days": sum(1 for value in day_values if value > 0),
        "negative_days": sum(1 for value in day_values if value < 0),
        "positive_months": sum(1 for value in month_values if value > 0),
        "negative_months": sum(1 for value in month_values if value < 0),
        "top25_removed_usd": top_removed(profits, 25),
        "top50_removed_usd": top_removed(profits, 50),
        "top100_removed_usd": top_removed(profits, 100),
        "top25_removed_r": top_removed(r_values, 25),
        "top50_removed_r": top_removed(r_values, 50),
        "top100_removed_r": top_removed(r_values, 100),
        "worst_day_usd": round(min(day_values), 2),
        "best_day_usd": round(max(day_values), 2),
        "worst_month_usd": round(min(month_values), 2),
        "best_month_usd": round(max(month_values), 2),
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 500:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 1.5:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 55.0:
        return "FAIL_WIN_RATE"
    if (row.get("profit_factor") or 0.0) < 1.20:
        return "FAIL_PF"
    if row.get("top50_removed_usd", 0.0) <= 0:
        return "FAIL_TOP50"
    if row.get("negative_months", 0) > row.get("positive_months", 0):
        return "FAIL_MONTHS"
    if row.get("trades_per_market_day", 0.0) < 3.0:
        return "REVIEW_LOW_CADENCE_CANDIDATE"
    return "REVIEW_OWNER_CADENCE_CANDIDATE"


def render(payload: dict[str, Any]) -> str:
    best = payload.get("best_result", {})
    lines = [
        "# XAU M5 Impulse Pullback Resume Screen - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline bar-level screen only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Hypothesis",
        "",
        "After a clean impulse in the H1/M5 trend direction, wait for a pullback into EMA20 structure and enter only after price resumes. This tests whether the missing ingredient in the momentum family is structured pullback quality rather than more hour filters.",
        "",
        "## Data",
        "",
        f"- Bars: `{payload['bar_path']}`",
        f"- Window: `{payload['window']}`",
        "- Entry/exit uses bid/ask bar prices and adverse-first same-bar TP/SL ordering.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Variant | `{best.get('name', '')}` |",
        f"| Trades | {best.get('trades', 'n/a')} |",
        f"| Win rate | {best.get('win_rate_pct', 'n/a')}% |",
        f"| PF | {best.get('profit_factor', 'n/a')} |",
        f"| Net | {best.get('net_usd', 'n/a')} USD |",
        f"| Trades / market day | {best.get('trades_per_market_day', 'n/a')} |",
        f"| Top50 removed | {best.get('top50_removed_usd', 'n/a')} USD |",
        f"| Positive / negative months | {best.get('positive_months', 'n/a')} / {best.get('negative_months', 'n/a')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Variant | Trades | WR | PF | Net | T/market day | Top50 | +M | -M |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:25], start=1):
        lines.append(
            f"| {index} | `{row.get('decision', '')}` | `{row.get('name', '')}` | {row.get('trades', '')} | {row.get('win_rate_pct', '')}% | {row.get('profit_factor', '')} | {row.get('net_usd', '')} | {row.get('trades_per_market_day', '')} | {row.get('top50_removed_usd', '')} | {row.get('positive_months', '')} | {row.get('negative_months', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "This is a discovery screen, not a production EA. A review candidate must be exact-tested in MT5 Strategy Tester before any demo attach.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Trades CSV: `{payload['trades_csv']}`",
            f"- Report: `{payload['report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> int:
    df = load_bars()
    blocked_sets = {
        "no_rollover": (0, 1, 22, 23),
        "active_only": (0, 1, 2, 3, 4, 21, 22, 23),
    }
    params: list[Params] = []
    for direction in ("both", "long", "short"):
        for impulse_bars in (12,):
            for impulse_atr in (1.4, 2.0):
                for pullback_max in (1.2, 1.8):
                    for rr in (0.7, 1.0):
                        for blocked_name, blocked in blocked_sets.items():
                            name = (
                                f"ipr_{direction}_ib{impulse_bars}_imp{str(impulse_atr).replace('.', 'p')}_"
                                f"pb{str(pullback_max).replace('.', 'p')}_rr{str(rr).replace('.', 'p')}_{blocked_name}"
                            )
                            params.append(
                                Params(
                                    name=name,
                                    direction_mode=direction,
                                    impulse_bars=impulse_bars,
                                    impulse_atr=impulse_atr,
                                    pullback_min_atr=0.25,
                                    pullback_max_atr=pullback_max,
                                    rr=rr,
                                    blocked_hours=blocked,
                                )
                            )
    summaries: list[dict[str, Any]] = []
    trades_by_name: dict[str, list[dict[str, Any]]] = {}
    for param in params:
        trades = simulate(df, param)
        summary = summarize_trades(param.name, trades)
        summary["decision"] = decision(summary)
        summary["params"] = param.__dict__
        summaries.append(summary)
        trades_by_name[param.name] = trades
    summaries.sort(
        key=lambda row: (
            0 if str(row.get("decision", "")).startswith("REVIEW") else 1,
            -float(row.get("net_usd") or 0.0),
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    best = summaries[0] if summaries else {}
    verdict = (
        "FOUND_REVIEW_CANDIDATE"
        if str(best.get("decision", "")).startswith("REVIEW")
        else "NO_IMPULSE_PULLBACK_CANDIDATE"
    )
    next_action = (
        "port_to_mt5_strategy_tester_for_exact_test"
        if verdict == "FOUND_REVIEW_CANDIDATE"
        else "redesign_pullback_or_try_news_session_breakout_family"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    payload = {
        "status": "PASS_IMPULSE_PULLBACK_SCREEN_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_screen_only_no_runtime_change",
        "bar_path": rel(BAR_PATH),
        "window": f"{SCREEN_START.date()} -> {SCREEN_END.date()}",
        "variant_count": len(params),
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": summaries[:50],
        "json": rel(output_json),
        "csv": rel(output_csv),
        "trades_csv": rel(output_trades),
        "report": rel(output_md),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(
        output_csv,
        summaries,
        [
            "decision",
            "name",
            "trades",
            "wins",
            "losses",
            "win_rate_pct",
            "net_usd",
            "profit_factor",
            "net_r",
            "profit_factor_r",
            "trades_per_market_day",
            "trades_per_active_day",
            "positive_months",
            "negative_months",
            "top25_removed_usd",
            "top50_removed_usd",
            "top100_removed_usd",
            "worst_month_usd",
            "best_month_usd",
        ],
    )
    best_trades = trades_by_name.get(str(best.get("name")), [])
    if best_trades:
        write_csv(
            output_trades,
            best_trades,
            [
                "variant",
                "entry_time",
                "entry_date",
                "entry_hour",
                "direction",
                "entry",
                "exit_time",
                "exit",
                "profit",
                "r",
                "risk",
                "atr14",
                "spread",
                "exit_reason",
                "impulse_move_atr",
                "pullback_depth_atr",
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
                "name": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net_usd": best.get("net_usd"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top50_removed_usd": best.get("top50_removed_usd"),
                "positive_months": best.get("positive_months"),
                "negative_months": best.get("negative_months"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
