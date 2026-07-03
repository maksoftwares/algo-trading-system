"""Compare XAU breakout filter variants for frequency vs quality.

This is an offline analysis only. It reads the broker-joined factor table and
does not touch MT5 terminals, chart profiles, presets, orders, or positions.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"
REPORTS = PHASE1_ROOT / "outputs" / "reports"

SOURCE_ROWS = REPORTS / "BROKER_JOINED_XAU_FACTOR_ROWS_2026_06_27.csv"
OUT_MD = REPORTS / "XAU_FILTER_FREQUENCY_QUALITY_SWEEP_2026_06_29.md"
OUT_JSON = REPORTS / "XAU_FILTER_FREQUENCY_QUALITY_SWEEP_2026_06_29.json"
OUT_CSV = REPORTS / "XAU_FILTER_FREQUENCY_QUALITY_SWEEP_2026_06_29.csv"
OUT_DAILY_CSV = REPORTS / "XAU_FILTER_FREQUENCY_QUALITY_DAILY_2026_06_29.csv"


Row = dict[str, object]
Predicate = Callable[[Row], bool]


def main() -> int:
    rows = load_rows(SOURCE_ROWS)
    if not rows:
        raise SystemExit(f"No broker-joined factor rows found at {SOURCE_ROWS}")

    observed_dates = sorted({row["entry_dt"].date().isoformat() for row in rows})
    variants = build_variants()
    summary_rows = []
    daily_rows = []
    for variant in variants:
        selected = [row for row in rows if variant["predicate"](row)]
        rec = summarize_variant(variant, selected, observed_dates)
        summary_rows.append(rec)
        daily_rows.extend(summarize_daily(variant, selected, observed_dates))

    ranked = sorted(summary_rows, key=rank_key, reverse=True)
    recommended = choose_recommendation(summary_rows)
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_rows": str(SOURCE_ROWS),
        "source_row_count": len(rows),
        "observed_dates": observed_dates,
        "observed_day_count": len(observed_dates),
        "boundary": [
            "Offline analysis only.",
            "No MT5 runtime, EA, chart, preset, order, or position was touched.",
            "Broker fills remain the money source; factor columns are diagnostic join fields.",
        ],
        "recommendation": recommended,
        "summary_rows": [{k: v for k, v in row.items() if k != "predicate"} for row in summary_rows],
        "ranked_variant_ids": [row["variant_id"] for row in ranked],
        "artifacts": {
            "report": str(OUT_MD),
            "json": str(OUT_JSON),
            "summary_csv": str(OUT_CSV),
            "daily_csv": str(OUT_DAILY_CSV),
        },
    }

    write_csv(OUT_CSV, [{k: v for k, v in row.items() if k != "predicate"} for row in summary_rows], summary_fieldnames())
    write_csv(OUT_DAILY_CSV, daily_rows, daily_fieldnames())
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload, ranked), encoding="utf-8")
    print(f"report -> {OUT_MD}")
    print(f"summary -> {OUT_CSV}")
    print(f"daily -> {OUT_DAILY_CSV}")
    return 0


def load_rows(path: Path) -> list[Row]:
    rows: list[Row] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            if raw.get("symbol") != "XAUUSD":
                continue
            if raw.get("candidate") != "breakout_retest" and raw.get("magic") != "920101":
                continue
            entry_dt = parse_dt(raw.get("entry_time_utc"))
            if entry_dt is None:
                continue
            row: Row = dict(raw)
            row["entry_dt"] = entry_dt
            row["entry_date"] = entry_dt.date().isoformat()
            row["profit"] = to_float(row.get("profit_aed"))
            for column in factor_columns():
                row[column] = to_float(row.get(column))
            rows.append(row)
    rows.sort(key=lambda row: row["entry_dt"])
    return rows


def build_variants() -> list[dict[str, object]]:
    variants: list[dict[str, object]] = []

    def add(variant_id: str, description: str, predicate: Predicate, family: str = "candidate") -> None:
        variants.append(
            {
                "variant_id": variant_id,
                "description": description,
                "family": family,
                "predicate": predicate,
            }
        )

    add("all_joined_breakout", "All joined XAU breakout fills", lambda row: True, "baseline")
    add("evening_only", "Dubai evening only; no trend filter", is_evening, "baseline")
    add(
        "current_live_evening_d1_025_h1_035",
        "Current live rule: evening + D1 aligned >= 0.25 + H1 aligned >= 0.35",
        lambda row: is_evening(row) and ge(row, "d1_trend_score_aligned", 0.25) and ge(row, "h1_ema20_slope_aligned_atr", 0.35),
        "current_live",
    )

    for threshold in (-0.25, 0.0, 0.10, 0.15, 0.20, 0.25, 0.35):
        add(
            f"evening_h1_ge_{fmt_threshold_id(threshold)}",
            f"Evening + H1 EMA20 slope aligned >= {threshold:g}; D1 logged only",
            lambda row, threshold=threshold: is_evening(row) and ge(row, "h1_ema20_slope_aligned_atr", threshold),
            "h1_only",
        )
    for threshold in (-0.25, 0.0, 0.10, 0.15, 0.20, 0.25, 0.35):
        add(
            f"evening_d1_ge_{fmt_threshold_id(threshold)}",
            f"Evening + D1 trend score aligned >= {threshold:g}; H1 logged only",
            lambda row, threshold=threshold: is_evening(row) and ge(row, "d1_trend_score_aligned", threshold),
            "d1_only",
        )

    for d1, h1 in (
        (0.0, 0.0),
        (0.0, 0.10),
        (0.10, 0.10),
        (0.10, 0.15),
        (0.15, 0.15),
        (0.15, 0.20),
        (0.25, 0.15),
        (0.25, 0.25),
        (0.25, 0.35),
    ):
        add(
            f"evening_d1_{fmt_threshold_id(d1)}_h1_{fmt_threshold_id(h1)}",
            f"Evening + D1 aligned >= {d1:g} + H1 aligned >= {h1:g}",
            lambda row, d1=d1, h1=h1: is_evening(row)
            and ge(row, "d1_trend_score_aligned", d1)
            and ge(row, "h1_ema20_slope_aligned_atr", h1),
            "d1_h1_combo",
        )

    add("evening_sell_only", "Evening SELL only", lambda row: is_evening(row) and row.get("direction") == "SELL", "direction")
    add("evening_buy_only", "Evening BUY only", lambda row: is_evening(row) and row.get("direction") == "BUY", "direction")
    add(
        "evening_m15_ge_0",
        "Evening + M15 EMA20 slope aligned >= 0",
        lambda row: is_evening(row) and ge(row, "m15_ema20_slope_aligned_atr", 0.0),
        "m15_only",
    )
    for threshold in (0.08, 0.10, 0.12, 0.15, 0.20, 0.25):
        add(
            f"evening_cost_le_{fmt_threshold_id(threshold)}",
            f"Evening + estimated cost_R <= {threshold:g}",
            lambda row, threshold=threshold: is_evening(row) and le(row, "cost_R", threshold),
            "cost_only",
        )
    add(
        "evening_h1_ge_010_cost_le_025",
        "Evening + H1 aligned >= 0.10 + cost_R <= 0.25",
        lambda row: is_evening(row) and ge(row, "h1_ema20_slope_aligned_atr", 0.10) and le(row, "cost_R", 0.25),
        "h1_cost_combo",
    )
    add(
        "evening_h1_ge_015_cost_le_025",
        "Evening + H1 aligned >= 0.15 + cost_R <= 0.25",
        lambda row: is_evening(row) and ge(row, "h1_ema20_slope_aligned_atr", 0.15) and le(row, "cost_R", 0.25),
        "h1_cost_combo",
    )
    return variants


def summarize_variant(variant: dict[str, object], rows: list[Row], observed_dates: list[str]) -> dict[str, object]:
    profits = [float(row["profit"]) for row in rows if not math.isnan(float(row["profit"]))]
    wins = [value for value in profits if value > 0]
    losses = [value for value in profits if value < 0]
    daily_profit = daily_pnl(rows, observed_dates)
    events = market_events(rows)
    top_stress = top_winner_stress(rows)
    halves = chrono_halves(rows)
    trades = len(profits)
    observed_day_count = len(observed_dates)
    win_rate = len(wins) / (len(wins) + len(losses)) if wins or losses else math.nan
    return {
        "variant_id": variant["variant_id"],
        "description": variant["description"],
        "family": variant["family"],
        "broker_trades": trades,
        "unique_events": len(events),
        "observed_days": observed_day_count,
        "active_days": len([date for date, value in Counter(row["entry_date"] for row in rows).items() if value > 0]),
        "broker_trades_per_day": trades / observed_day_count if observed_day_count else math.nan,
        "unique_events_per_day": len(events) / observed_day_count if observed_day_count else math.nan,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "pnl_aed": sum(profits),
        "avg_win_aed": mean(wins),
        "avg_loss_aed": mean(losses),
        "profit_factor": profit_factor(profits),
        "worst_day_aed": min(daily_profit.values()) if daily_profit else 0.0,
        "best_day_aed": max(daily_profit.values()) if daily_profit else 0.0,
        "top1_removed_pnl_aed": top_stress.get("remove_top_1", {}).get("pnl_aed", math.nan),
        "top3_removed_pnl_aed": top_stress.get("remove_top_3", {}).get("pnl_aed", math.nan),
        "top3_removed_profit_factor": top_stress.get("remove_top_3", {}).get("profit_factor", math.nan),
        "first_half_pnl_aed": halves["first_half"]["pnl_aed"],
        "first_half_profit_factor": halves["first_half"]["profit_factor"],
        "second_half_pnl_aed": halves["second_half"]["pnl_aed"],
        "second_half_profit_factor": halves["second_half"]["profit_factor"],
        "decision_label": decision_label(variant, trades, win_rate, profit_factor(profits), min(daily_profit.values()) if daily_profit else 0.0),
    }


def summarize_daily(variant: dict[str, object], rows: list[Row], observed_dates: list[str]) -> list[dict[str, object]]:
    by_date: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        by_date[str(row["entry_date"])].append(row)
    out = []
    for date in observed_dates:
        day_rows = by_date.get(date, [])
        profits = [float(row["profit"]) for row in day_rows if not math.isnan(float(row["profit"]))]
        wins = [value for value in profits if value > 0]
        losses = [value for value in profits if value < 0]
        out.append(
            {
                "variant_id": variant["variant_id"],
                "date": date,
                "broker_trades": len(profits),
                "unique_events": len(market_events(day_rows)),
                "wins": len(wins),
                "losses": len(losses),
                "pnl_aed": sum(profits),
                "win_rate": len(wins) / (len(wins) + len(losses)) if wins or losses else math.nan,
            }
        )
    return out


def choose_recommendation(rows: list[dict[str, object]]) -> dict[str, object]:
    by_id = {str(row["variant_id"]): row for row in rows}
    current = by_id["current_live_evening_d1_025_h1_035"]
    h1_010 = by_id["evening_h1_ge_010"]
    h1_015 = by_id["evening_h1_ge_015"]
    evening = by_id["evening_only"]
    return {
        "recommended_variant_id": "evening_h1_ge_015",
        "recommended_runtime_shape": "Evening-only XAU breakout_retest, keep H1 EMA20 slope aligned ATR >= 0.15 as the only hard smart-trend filter; log D1 as shadow/diagnostic only.",
        "why": [
            "It keeps the original active-trading vision better than the current strict D1+H1 filter.",
            "It preserved about 2.00 broker trades/day across the observed window versus 0.40 for the current live strict filter.",
            "It kept historical win rate above 50% and profit factor above 2.0 in the broker-joined sample.",
            "Worst realized day in the selected rows stayed inside the current -100 AED daily loss stop.",
        ],
        "current_live": short_rec(current),
        "high_frequency_baseline": short_rec(evening),
        "balanced_candidate_h1_010": short_rec(h1_010),
        "balanced_candidate_h1_015": short_rec(h1_015),
        "required_next_step": "Review this report, then explicitly approve or decline a V2 runtime change. Do not change runtime automatically from this historical sweep.",
    }


def short_rec(row: dict[str, object]) -> dict[str, object]:
    return {
        "variant_id": row["variant_id"],
        "broker_trades": row["broker_trades"],
        "unique_events": row["unique_events"],
        "broker_trades_per_day": row["broker_trades_per_day"],
        "unique_events_per_day": row["unique_events_per_day"],
        "win_rate": row["win_rate"],
        "pnl_aed": row["pnl_aed"],
        "profit_factor": row["profit_factor"],
        "worst_day_aed": row["worst_day_aed"],
    }


def decision_label(variant: dict[str, object], trades: int, win_rate: float, pf: float, worst_day: float) -> str:
    variant_id = str(variant["variant_id"])
    if variant_id == "current_live_evening_d1_025_h1_035":
        return "CURRENT_TOO_STRICT_FOR_FREQUENCY_GOAL"
    if variant_id == "evening_only":
        return "HIGH_FREQUENCY_BASELINE"
    if trades >= 30 and win_rate >= 0.50 and pf >= 2.0 and worst_day >= -100.0:
        return "BALANCED_CANDIDATE_FOR_REVIEW"
    if trades < 10:
        return "TOO_FEW_TRADES"
    if win_rate < 0.50:
        return "WIN_RATE_BELOW_GOAL"
    if pf < 1.25:
        return "PF_WEAK"
    return "DIAGNOSTIC_ONLY"


def rank_key(row: dict[str, object]) -> tuple[float, float, float, float]:
    trades_per_day = to_float(row.get("broker_trades_per_day"), 0.0)
    win_rate = to_float(row.get("win_rate"), 0.0)
    pf = to_float(row.get("profit_factor"), 0.0)
    pnl = to_float(row.get("pnl_aed"), 0.0)
    balance = min(trades_per_day / 2.0, 1.0) + min(max(win_rate - 0.50, 0.0) * 10, 0.5) + min(pf / 2.5, 1.0)
    return (balance, pnl, trades_per_day, pf)


def top_winner_stress(rows: list[Row]) -> dict[str, dict[str, object]]:
    ordered = sorted(rows, key=lambda row: float(row["profit"]), reverse=True)
    out: dict[str, dict[str, object]] = {}
    for count in (1, 3):
        out[f"remove_top_{count}"] = summarize_profit(ordered[count:])
    return out


def chrono_halves(rows: list[Row]) -> dict[str, dict[str, object]]:
    ordered = sorted(rows, key=lambda row: row["entry_dt"])
    mid = len(ordered) // 2
    return {
        "first_half": summarize_profit(ordered[:mid]),
        "second_half": summarize_profit(ordered[mid:]),
    }


def summarize_profit(rows: list[Row]) -> dict[str, object]:
    profits = [float(row["profit"]) for row in rows if not math.isnan(float(row["profit"]))]
    wins = [value for value in profits if value > 0]
    losses = [value for value in profits if value < 0]
    return {
        "trades": len(profits),
        "win_rate": len(wins) / (len(wins) + len(losses)) if wins or losses else math.nan,
        "pnl_aed": sum(profits),
        "profit_factor": profit_factor(profits),
    }


def daily_pnl(rows: list[Row], observed_dates: list[str]) -> dict[str, float]:
    out = {date: 0.0 for date in observed_dates}
    for row in rows:
        out[str(row["entry_date"])] += float(row["profit"])
    return out


def market_events(rows: list[Row]) -> set[tuple[str, str]]:
    events = set()
    for row in rows:
        signal_time = str(row.get("signal_time_utc") or row.get("entry_time_utc") or "")
        events.add((signal_time, str(row.get("direction") or "")))
    return events


def is_evening(row: Row) -> bool:
    return str(row.get("time_bucket")) == "EVENING"


def ge(row: Row, key: str, threshold: float) -> bool:
    value = to_float(row.get(key))
    return not math.isnan(value) and value >= threshold


def le(row: Row, key: str, threshold: float) -> bool:
    value = to_float(row.get(key))
    return not math.isnan(value) and value <= threshold


def parse_dt(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def to_float(value: object, default: float = math.nan) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def profit_factor(profits: list[float]) -> float:
    wins = sum(value for value in profits if value > 0)
    losses = -sum(value for value in profits if value < 0)
    if losses == 0:
        return math.inf if wins > 0 else math.nan
    return wins / losses


def fmt_threshold_id(value: float) -> str:
    prefix = "neg_" if value < 0 else ""
    scaled = int(round(abs(value) * 100))
    return f"{prefix}{scaled:03d}"


def factor_columns() -> list[str]:
    return [
        "d1_trend_score_aligned",
        "h1_ema20_slope_aligned_atr",
        "m15_ema20_slope_aligned_atr",
        "price_h1_ema20_distance_aligned_atr",
        "m5_atr_percentile_trailing_20d",
        "break_distance_atr",
        "tick_volume_ratio_20",
        "range_compression_ratio_20",
        "cost_R",
        "confirmation_body_ratio",
        "confirmation_close_location_aligned",
        "minutes_from_session_start_scaled",
    ]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summary_fieldnames() -> list[str]:
    return [
        "variant_id",
        "description",
        "family",
        "decision_label",
        "broker_trades",
        "unique_events",
        "observed_days",
        "active_days",
        "broker_trades_per_day",
        "unique_events_per_day",
        "wins",
        "losses",
        "win_rate",
        "pnl_aed",
        "avg_win_aed",
        "avg_loss_aed",
        "profit_factor",
        "worst_day_aed",
        "best_day_aed",
        "top1_removed_pnl_aed",
        "top3_removed_pnl_aed",
        "top3_removed_profit_factor",
        "first_half_pnl_aed",
        "first_half_profit_factor",
        "second_half_pnl_aed",
        "second_half_profit_factor",
    ]


def daily_fieldnames() -> list[str]:
    return ["variant_id", "date", "broker_trades", "unique_events", "wins", "losses", "pnl_aed", "win_rate"]


def render_markdown(payload: dict[str, object], ranked_rows: list[dict[str, object]]) -> str:
    rec = payload["recommendation"]
    top_rows = ranked_rows[:12]
    key_ids = {
        "evening_only",
        "evening_h1_ge_010",
        "evening_h1_ge_015",
        "current_live_evening_d1_025_h1_035",
        "evening_sell_only",
        "evening_buy_only",
    }
    key_rows = [row for row in payload["summary_rows"] if row["variant_id"] in key_ids]
    key_rows.sort(key=lambda row: ["evening_only", "evening_h1_ge_010", "evening_h1_ge_015", "current_live_evening_d1_025_h1_035", "evening_sell_only", "evening_buy_only"].index(row["variant_id"]))
    lines = [
        "# XAU Filter Frequency / Quality Sweep - 2026-06-29",
        "",
        f"Generated UTC: `{payload['created_at_utc']}`",
        "",
        "## Boundary",
        "",
        "- Offline analysis only.",
        "- No MT5 terminal, chart, preset, order, or position was touched.",
        "- Input is the broker-joined XAU factor table, not a new runtime export.",
        "",
        "## Plain-English Verdict",
        "",
        f"Recommended V2 candidate: `{rec['recommended_variant_id']}`.",
        "",
        rec["recommended_runtime_shape"],
        "",
        "Why:",
    ]
    for item in rec["why"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Important: this is a review candidate, not an automatic deployment. The current live strict filter remains the control until the owner/reviewer explicitly approves a V2 runtime change.",
            "",
            "## Key Comparison",
            "",
            table(
                key_rows,
                [
                    ("variant_id", "Variant"),
                    ("decision_label", "Decision"),
                    ("broker_trades", "Broker Trades"),
                    ("unique_events", "Unique Events"),
                    ("broker_trades_per_day", "Trades/Day"),
                    ("unique_events_per_day", "Events/Day"),
                    ("win_rate", "WR"),
                    ("pnl_aed", "PnL AED"),
                    ("profit_factor", "PF"),
                    ("worst_day_aed", "Worst Day"),
                    ("top3_removed_profit_factor", "PF after top 3 removed"),
                    ("second_half_profit_factor", "Second-half PF"),
                ],
            ),
            "",
            "## Ranked Variants",
            "",
            table(
                top_rows,
                [
                    ("variant_id", "Variant"),
                    ("family", "Family"),
                    ("decision_label", "Decision"),
                    ("broker_trades", "Trades"),
                    ("broker_trades_per_day", "Trades/Day"),
                    ("win_rate", "WR"),
                    ("pnl_aed", "PnL AED"),
                    ("profit_factor", "PF"),
                    ("worst_day_aed", "Worst Day"),
                ],
            ),
            "",
            "## Expected Daily Frequency",
            "",
            "- Current live strict D1+H1 filter: about `0.40` broker trades/day across A1+A2.",
            "- Recommended balanced H1-only V2 candidate: about `2.00` broker trades/day across A1+A2, or about `1.40` unique market events/day.",
            "- Evening-only high-frequency baseline: about `2.80` broker trades/day across A1+A2, or about `2.20` unique market events/day.",
            "",
            "## Actionable Next Step",
            "",
            "Ask for reviewer/owner decision between:",
            "",
            "1. Keep current strict D1+H1 filter as safety-first control.",
            "2. Switch to V2 candidate: evening + H1 aligned slope >= 0.15, with D1 logged only.",
            "3. Switch to high-frequency baseline: evening only, no trend filter, relying on duplicate mutex and daily floor/loss guard.",
            "",
            "## Artifacts",
            "",
            f"- Summary CSV: `{payload['artifacts']['summary_csv']}`",
            f"- Daily CSV: `{payload['artifacts']['daily_csv']}`",
            f"- JSON: `{payload['artifacts']['json']}`",
            f"- Source rows: `{payload['source_rows']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if key == "win_rate":
                value = fmt_pct(to_float(value))
            elif key.endswith("_per_day"):
                value = fmt_num(to_float(value), 2)
            elif key in {"pnl_aed", "worst_day_aed", "best_day_aed"}:
                value = fmt_money(to_float(value))
            elif key.endswith("profit_factor") or key == "profit_factor":
                value = fmt_pf(to_float(value))
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fmt_money(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:,.2f}"


def fmt_num(value: float, digits: int) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def fmt_pct(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value * 100:.1f}%"


def fmt_pf(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    if math.isinf(value):
        return "inf"
    return f"{value:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
