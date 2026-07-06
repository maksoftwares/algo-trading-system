from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
DOC_PATH = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_M5_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_PREREG_2026_07_05.md"
)
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
OUTPUT_STEM = "A1_XAU_M5_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_2026_07_05"

DESIGN_START = pd.Timestamp("2016-01-01T00:00:00Z")
DESIGN_END = pd.Timestamp("2021-12-31T23:59:59Z")
EXAM_START = pd.Timestamp("2022-07-01T00:00:00Z")
EXAM_END = pd.Timestamp("2025-06-30T23:59:59Z")
LAST12_START = pd.Timestamp("2024-07-01T00:00:00Z")
LAST12_END = pd.Timestamp("2025-06-30T23:59:59Z")

RR = 2.0
MAX_HOLD_BARS = 288
RANGE_SLOPE_LIMIT = 0.15


@dataclass(frozen=True)
class Params:
    name: str
    reference: str
    direction_mode: str
    sweep_min_atr: float
    close_back_atr: float
    stop_buffer_atr: float
    trend_filter: str
    session_filter: str


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def market_days(start: date, end: date) -> list[str]:
    out: list[str] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            out.append(current.isoformat())
        current += timedelta(days=1)
    return out


DESIGN_MARKET_DAYS = market_days(DESIGN_START.date(), DESIGN_END.date())
EXAM_MARKET_DAYS = market_days(EXAM_START.date(), EXAM_END.date())
LAST12_MARKET_DAYS = market_days(LAST12_START.date(), LAST12_END.date())


def load_bars() -> pd.DataFrame:
    usecols = [
        "timestamp_utc",
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
    df["ema50"] = df["mid_close"].ewm(span=50, adjust=False).mean()
    df["ema50_slope_atr"] = (df["ema50"] - df["ema50"].shift(12)) / df["atr14"]

    df["rolling_48_high"] = df["mid_high"].shift(1).rolling(48, min_periods=48).max()
    df["rolling_48_low"] = df["mid_low"].shift(1).rolling(48, min_periods=48).min()
    df["rolling_96_high"] = df["mid_high"].shift(1).rolling(96, min_periods=96).max()
    df["rolling_96_low"] = df["mid_low"].shift(1).rolling(96, min_periods=96).min()

    dubai_ts = df["timestamp_utc"] + pd.Timedelta(hours=4)
    df["dubai_date"] = dubai_ts.dt.date.astype(str)
    df["dubai_hour"] = dubai_ts.dt.hour
    df["entry_date"] = df["dubai_date"]
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()

    day_ranges = (
        df.groupby("dubai_date", as_index=True)
        .agg(day_high=("mid_high", "max"), day_low=("mid_low", "min"))
        .sort_index()
    )
    prev_day_ranges = day_ranges.shift(1).rename(
        columns={"day_high": "previous_dubai_day_high", "day_low": "previous_dubai_day_low"}
    )
    df = df.join(prev_day_ranges, on="dubai_date")

    asia = df[(df["dubai_hour"] >= 0) & (df["dubai_hour"] <= 7)]
    asia_ranges = (
        asia.groupby("dubai_date", as_index=True)
        .agg(asia_range_high=("mid_high", "max"), asia_range_low=("mid_low", "min"))
        .sort_index()
    )
    df = df.join(asia_ranges, on="dubai_date")

    needed = [
        "atr14",
        "ema50_slope_atr",
        "rolling_48_high",
        "rolling_48_low",
        "rolling_96_high",
        "rolling_96_low",
        "previous_dubai_day_high",
        "previous_dubai_day_low",
        "asia_range_high",
        "asia_range_low",
    ]
    return df.dropna(subset=needed).reset_index(drop=True)


def build_params() -> list[Params]:
    params: list[Params] = []
    for reference in ("rolling_48", "rolling_96", "previous_dubai_day", "asia_range"):
        for direction_mode in ("both", "long", "short"):
            for sweep_min_atr in (0.05, 0.15, 0.30):
                for close_back_atr in (0.00, 0.05):
                    for stop_buffer_atr in (0.05, 0.15):
                        for trend_filter in ("none", "range"):
                            for session_filter in ("liquid", "no_rollover"):
                                name = (
                                    f"lsr2_{reference}_{direction_mode}_sw{sweep_min_atr:.2f}"
                                    f"_cb{close_back_atr:.2f}_buf{stop_buffer_atr:.2f}"
                                    f"_{trend_filter}_{session_filter}"
                                ).replace(".", "p")
                                params.append(
                                    Params(
                                        name=name,
                                        reference=reference,
                                        direction_mode=direction_mode,
                                        sweep_min_atr=sweep_min_atr,
                                        close_back_atr=close_back_atr,
                                        stop_buffer_atr=stop_buffer_atr,
                                        trend_filter=trend_filter,
                                        session_filter=session_filter,
                                    )
                                )
    return params


def session_ok(row: dict[str, Any], params: Params) -> bool:
    hour = int(row["dubai_hour"])
    if params.reference == "asia_range" and not (8 <= hour <= 20):
        return False
    if params.session_filter == "liquid":
        return 6 <= hour <= 20
    if params.session_filter == "no_rollover":
        return hour not in {0, 1, 22, 23}
    return True


def trend_ok(row: dict[str, Any], params: Params) -> bool:
    if params.trend_filter == "none":
        return True
    return abs(float(row["ema50_slope_atr"])) <= RANGE_SLOPE_LIMIT


def refs(row: dict[str, Any], reference: str) -> tuple[float, float]:
    return float(row[f"{reference}_high"]), float(row[f"{reference}_low"])


def signal_direction(row: dict[str, Any], params: Params) -> str | None:
    if not session_ok(row, params) or not trend_ok(row, params):
        return None
    ref_high, ref_low = refs(row, params.reference)
    atr = float(row["atr14"])
    long_allowed = params.direction_mode in {"both", "long"}
    short_allowed = params.direction_mode in {"both", "short"}
    short_hit = (
        short_allowed
        and float(row["mid_high"]) >= ref_high + params.sweep_min_atr * atr
        and float(row["mid_close"]) <= ref_high - params.close_back_atr * atr
    )
    long_hit = (
        long_allowed
        and float(row["mid_low"]) <= ref_low - params.sweep_min_atr * atr
        and float(row["mid_close"]) >= ref_low + params.close_back_atr * atr
    )
    if short_hit and long_hit:
        return None
    if short_hit:
        return "SHORT"
    if long_hit:
        return "LONG"
    return None


def signal_candidates(df: pd.DataFrame, params: Params) -> list[tuple[int, str]]:
    hour = df["dubai_hour"].astype(int)
    if params.reference == "asia_range":
        mask = (hour >= 8) & (hour <= 20)
    elif params.session_filter == "liquid":
        mask = (hour >= 6) & (hour <= 20)
    elif params.session_filter == "no_rollover":
        mask = ~hour.isin([0, 1, 22, 23])
    else:
        mask = pd.Series(True, index=df.index)

    if params.trend_filter == "range":
        mask = mask & (df["ema50_slope_atr"].abs() <= RANGE_SLOPE_LIMIT)

    ref_high = df[f"{params.reference}_high"]
    ref_low = df[f"{params.reference}_low"]
    atr = df["atr14"]
    short_allowed = params.direction_mode in {"both", "short"}
    long_allowed = params.direction_mode in {"both", "long"}
    short_hit = (
        mask
        & short_allowed
        & (df["mid_high"] >= ref_high + params.sweep_min_atr * atr)
        & (df["mid_close"] <= ref_high - params.close_back_atr * atr)
    )
    long_hit = (
        mask
        & long_allowed
        & (df["mid_low"] <= ref_low - params.sweep_min_atr * atr)
        & (df["mid_close"] >= ref_low + params.close_back_atr * atr)
    )
    ambiguous = short_hit & long_hit
    short_indices = [(int(index), "SHORT") for index in df.index[short_hit & ~ambiguous]]
    long_indices = [(int(index), "LONG") for index in df.index[long_hit & ~ambiguous]]
    return sorted(short_indices + long_indices, key=lambda item: item[0])


def simulate(rows: list[dict[str, Any]], candidates: list[tuple[int, str]], params: Params) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    candidate_index = 0
    while candidate_index < len(candidates):
        i, direction = candidates[candidate_index]
        row = rows[i]

        entry_index = i + 1
        if entry_index >= len(rows):
            break
        entry_row = rows[entry_index]
        ref_high, ref_low = refs(row, params.reference)
        atr = float(row["atr14"])
        spread = float(entry_row["spread_price"])

        if direction == "LONG":
            entry = float(entry_row["ask_open"])
            raw_stop = float(row["mid_low"]) - params.stop_buffer_atr * atr
            risk = max(entry - raw_stop, 3.0 * spread)
            if risk <= 0:
                candidate_index += 1
                continue
            sl = entry - risk
            tp = entry + RR * risk
        else:
            entry = float(entry_row["bid_open"])
            raw_stop = float(row["mid_high"]) + params.stop_buffer_atr * atr
            risk = max(raw_stop - entry, 3.0 * spread)
            if risk <= 0:
                candidate_index += 1
                continue
            sl = entry + risk
            tp = entry - RR * risk

        exit_index = min(entry_index + MAX_HOLD_BARS, len(rows) - 1)
        exit_price = None
        exit_reason = "time_stop"
        for j in range(entry_index, exit_index + 1):
            bar = rows[j]
            if direction == "LONG":
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
            last = rows[exit_index]
            exit_price = float(last["bid_close"] if direction == "LONG" else last["ask_close"])

        pnl = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
        trades.append(
            {
                "variant": params.name,
                "entry_time_utc": entry_row["timestamp_utc"].isoformat(),
                "exit_time_utc": rows[exit_index]["timestamp_utc"].isoformat(),
                "entry_date": entry_row["entry_date"],
                "direction": direction,
                "reference": params.reference,
                "ref_high": round(ref_high, 4),
                "ref_low": round(ref_low, 4),
                "entry": round(entry, 4),
                "sl": round(sl, 4),
                "tp": round(tp, 4),
                "risk": round(risk, 4),
                "pnl_usd_001lot": round(pnl, 4),
                "r_multiple": round(pnl / risk, 4) if risk else None,
                "exit_reason": exit_reason,
                "entry_hour_dubai": int(entry_row["dubai_hour"]),
            }
        )
        while candidate_index < len(candidates) and candidates[candidate_index][0] <= exit_index:
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
    wins = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    if losses <= 0:
        return None
    return wins / losses


def summary_metrics(
    trades: list[dict[str, Any]], market_day_list: list[str], cost_per_trade: float = 0.0
) -> dict[str, Any]:
    values = [float(t["pnl_usd_001lot"]) - cost_per_trade for t in trades]
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    active_days = {t["entry_date"] for t in trades if t["entry_date"] in set(market_day_list)}
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
        "top100_removed_net": sum(sorted(values, reverse=True)[100:]) if len(values) > 100 else None,
    }


def owner_score(row: dict[str, Any]) -> float:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    pf = float(row.get("profit_factor") or 0.0)
    signals = float(row.get("signals") or 0.0)
    return (
        min(wr / 50.0, 1.2) * 350.0
        + min(wl / 2.0, 1.2) * 300.0
        + min(active / 90.0, 1.15) * 250.0
        + min(pf / 1.5, 1.1) * 75.0
        + min(signals / 900.0, 1.1) * 25.0
    )


def decision(row: dict[str, Any]) -> str:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    last_wr = float(row.get("last12_win_rate_pct") or 0.0)
    last_wl = float(row.get("last12_avg_win_loss") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 70.0 and last_wr >= 48.0 and last_wl >= 1.85:
        return "EXACT_MT5_REPLAY_CANDIDATE_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_LOW_ACTIVITY"
    if active >= 70.0 and wl >= 2.0:
        return "ACTIVITY_PAYOFF_WR_FAIL"
    if active >= 70.0 and wr >= 50.0:
        return "ACTIVITY_WR_PAYOFF_FAIL"
    return "REJECT_NO_OWNER_SHAPE"


def round_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, float):
            out[key] = round(value, 4)
        else:
            out[key] = value
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
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
    design_trades_by_name: dict[str, list[dict[str, Any]]] = {}
    for index, params in enumerate(params_list, start=1):
        candidates = signal_candidates(design_df, params)
        trades = simulate(design_records, candidates, params)
        design_trades_by_name[params.name] = trades
        metrics = round_metrics(summary_metrics(trades, DESIGN_MARKET_DAYS))
        row = {**asdict(params), **metrics, "score": round(owner_score(metrics), 4)}
        design_rows.append(row)
        if index % 48 == 0:
            print(f"design {index}/{len(params_list)}", flush=True)

    design_rows.sort(key=lambda r: float(r["score"]), reverse=True)
    frozen = design_rows[:5]

    exam_rows: list[dict[str, Any]] = []
    exam_trades_by_name: dict[str, list[dict[str, Any]]] = {}
    param_by_name = {p.name: p for p in params_list}
    for design_row in frozen:
        params = param_by_name[str(design_row["name"])]
        candidates = signal_candidates(exam_df, params)
        trades = simulate(exam_records, candidates, params)
        exam_trades_by_name[params.name] = trades
        metrics = summary_metrics(trades, EXAM_MARKET_DAYS)
        last12 = summary_metrics(
            [
                t
                for t in trades
                if LAST12_START <= pd.Timestamp(t["entry_time_utc"]) <= LAST12_END
            ],
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
            "decision": "",
        }
        row["decision"] = decision(row)
        row["score"] = round(owner_score(row), 4)
        exam_rows.append(row)

    exam_rows.sort(key=lambda r: float(r["score"]), reverse=True)
    best = exam_rows[0] if exam_rows else {}
    best_trades = exam_trades_by_name.get(str(best.get("name")), []) if best else []

    design_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DESIGN.csv"
    exam_csv = REPORTS_DIR / f"{OUTPUT_STEM}_EXAM.csv"
    trades_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_EXAM_TRADES.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    design_fields = list(design_rows[0].keys()) if design_rows else []
    exam_fields = list(exam_rows[0].keys()) if exam_rows else []
    trade_fields = list(best_trades[0].keys()) if best_trades else [
        "variant",
        "entry_time_utc",
        "exit_time_utc",
        "entry_date",
        "direction",
        "pnl_usd_001lot",
    ]
    write_csv(design_csv, design_rows, design_fields)
    write_csv(exam_csv, exam_rows, exam_fields)
    write_csv(trades_csv, best_trades, trade_fields)

    artifact = {
        "status": "PASS_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_READY",
        "generated_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
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
    json_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

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

    verdict = "NO_EXACT_MT5_REPLAY_CANDIDATE"
    if any(row["decision"] == "EXACT_MT5_REPLAY_CANDIDATE_DIAGNOSTIC" for row in exam_rows):
        verdict = "DIAGNOSTIC_REPLAY_CANDIDATE_FOUND"
    elif any(row["decision"] == "CORE_SHAPE_LOW_ACTIVITY" for row in exam_rows):
        verdict = "CORE_SHAPE_CLUE_ACTIVITY_GAP"

    md = "\n".join(
        [
            "# A1 XAU M5 Liquidity Sweep Reclaim 2R Diagnostic - 2026-07-05",
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
            "- This is not a demo spec and not a headline result; exact MT5 replay is still required for any promotion.",
            "- If this fails, the immediate lesson is that this 2R-native sweep-reclaim source does not bridge the current family activity gap.",
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
