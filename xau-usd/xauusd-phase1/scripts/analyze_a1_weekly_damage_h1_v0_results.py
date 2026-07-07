from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
DEFAULT_RESULT_JSON = REPORTS / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V14_WEEKLY_DAMAGE_H1_202207_202606.json"
BASELINE_WEEK_TABLE = REPORTS / "A1_XAU_HYBRID_WEEKLY_EXIT_ANATOMY_202207_202606_WEEK_TABLE.csv"
BASELINE_KEPT = REPORTS / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
OUTPUT_STEM = "A1_XAU_WEEKLY_DAMAGE_H1_V0_EXACT_MT5_REVIEW_202207_202606"


def parse_dt(value: Any) -> datetime:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def parse_date(value: Any) -> date:
    return date.fromisoformat(str(value).strip())


def parse_float(value: Any) -> float:
    return float(str(value or "0").strip().replace(" ", "") or "0")


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def market_weekdays(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def money_stats(values: list[float]) -> dict[str, Any]:
    trades = len(values)
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    return {
        "trades": trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / trades, 2) if trades else 0.0,
        "net_usd": round(sum(values), 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "avg_win_usd": round(avg_win, 4),
        "avg_loss_usd": round(avg_loss, 4),
        "win_loss_ratio": round(avg_win / avg_loss, 4) if avg_loss else None,
    }


def load_baseline_weeks(path: Path) -> dict[date, dict[str, Any]]:
    rows: dict[date, dict[str, Any]] = {}
    for row in read_csv(path):
        start = parse_date(row["week_start"])
        rows[start] = {
            "week_start": start,
            "net_usd": parse_float(row["net_usd"]),
            "signals": int(float(row.get("signals") or 0)),
        }
    return rows


def load_baseline_trades(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        entry_time = parse_dt(row["entry_time"])
        rows.append(
            {
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "pnl_usd": parse_float(row["pnl_usd"]),
            }
        )
    return rows


def load_variant_trades(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists() or path.stat().st_size == 0:
        return rows
    for row in read_csv(path):
        if not row:
            continue
        entry_time = parse_dt(row["entry_time"])
        exit_time = parse_dt(row["exit_time"])
        rows.append(
            {
                "entry_time": entry_time,
                "entry_date": entry_time.date(),
                "exit_time": exit_time,
                "exit_date": exit_time.date(),
                "week_start": week_start(exit_time.date()),
                "pnl_usd": parse_float(row.get("profit_aed")),
                "direction": str(row.get("direction", "")),
            }
        )
    return rows


def active_pct(entry_dates: set[date], weekdays: list[date]) -> float:
    return round(100.0 * len(entry_dates & set(weekdays)) / len(weekdays), 2) if weekdays else 0.0


def positive_week_pct(week_nets: dict[date, float], all_weeks: list[date]) -> float:
    positives = sum(1 for start in all_weeks if week_nets.get(start, 0.0) > 0)
    return round(100.0 * positives / len(all_weeks), 2) if all_weeks else 0.0


def evaluate_variant(
    result: dict[str, Any],
    baseline_weeks: dict[date, dict[str, Any]],
    baseline_trades: list[dict[str, Any]],
    all_weeks: list[date],
    weekdays: list[date],
) -> dict[str, Any]:
    trades = load_variant_trades(Path(result["trade_csv"]))
    variant_week_net: dict[date, float] = defaultdict(float)
    variant_week_trades: dict[date, int] = defaultdict(int)
    for trade in trades:
        variant_week_net[trade["week_start"]] += trade["pnl_usd"]
        variant_week_trades[trade["week_start"]] += 1

    baseline_values = [trade["pnl_usd"] for trade in baseline_trades]
    variant_values = [trade["pnl_usd"] for trade in trades]
    combined_values = baseline_values + variant_values
    standalone = money_stats(variant_values)
    hybrid = money_stats(combined_values)

    baseline_entry_dates = {trade["entry_date"] for trade in baseline_trades}
    variant_entry_dates = {trade["entry_date"] for trade in trades}
    baseline_red_weeks = [start for start in all_weeks if baseline_weeks.get(start, {}).get("net_usd", 0.0) < 0]
    touched_red = 0
    flipped_red = 0
    worsened_red = 0
    green_to_red = 0
    hybrid_week_nets: dict[date, float] = {}
    for start in all_weeks:
        baseline_net = float(baseline_weeks.get(start, {}).get("net_usd", 0.0))
        variant_net = float(variant_week_net.get(start, 0.0))
        hybrid_net = baseline_net + variant_net
        hybrid_week_nets[start] = hybrid_net
        if baseline_net < 0 and variant_week_trades.get(start, 0) > 0:
            touched_red += 1
            if hybrid_net > 0:
                flipped_red += 1
            if variant_net < 0 and hybrid_net < baseline_net:
                worsened_red += 1
        if baseline_net > 0 and hybrid_net < 0:
            green_to_red += 1

    worst_week = min((hybrid_week_nets.get(start, 0.0) for start in all_weeks), default=0.0)
    standalone_week_nets = {start: float(variant_week_net.get(start, 0.0)) for start in all_weeks}
    row = {
        "variant": result["name"],
        "label": result["label"],
        "trade_csv": result["trade_csv"],
        "standalone_trades": standalone["trades"],
        "standalone_wr_pct": standalone["win_rate_pct"],
        "standalone_wl": standalone["win_loss_ratio"],
        "standalone_pf": standalone["profit_factor"],
        "standalone_net_usd": standalone["net_usd"],
        "standalone_active_weekday_pct": active_pct(variant_entry_dates, weekdays),
        "standalone_positive_week_pct": positive_week_pct(standalone_week_nets, all_weeks),
        "hybrid_trades": hybrid["trades"],
        "hybrid_wr_pct": hybrid["win_rate_pct"],
        "hybrid_wl": hybrid["win_loss_ratio"],
        "hybrid_pf": hybrid["profit_factor"],
        "hybrid_net_usd": hybrid["net_usd"],
        "hybrid_active_weekday_pct": active_pct(baseline_entry_dates | variant_entry_dates, weekdays),
        "hybrid_positive_week_pct": positive_week_pct(hybrid_week_nets, all_weeks),
        "baseline_red_weeks": len(baseline_red_weeks),
        "red_weeks_touched": touched_red,
        "red_weeks_flipped": flipped_red,
        "red_weeks_worsened": worsened_red,
        "green_weeks_turned_red": green_to_red,
        "hybrid_worst_week_usd": round(worst_week, 2),
        "decision": "REJECT_NO_WEEKLY_TARGET_PROGRESS",
    }
    if row["hybrid_positive_week_pct"] >= 70.0 and row["hybrid_active_weekday_pct"] >= 90.0:
        row["decision"] = "WEEKLY_ACTIVITY_HIT_REVIEW_REQUIRED"
    elif row["hybrid_positive_week_pct"] > 60.0 and row["red_weeks_flipped"] > row["red_weeks_worsened"]:
        row["decision"] = "WATCHLIST_SOURCE_NEEDS_SECOND_PASS"
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["variant"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def derive_title(result_payload: dict[str, Any], output_stem: str) -> str:
    variants = result_payload.get("variants") or []
    first_label = str(variants[0].get("label") or "") if variants else ""
    if ":" in first_label:
        source = first_label.split(":", 1)[0].strip()
    else:
        source = output_stem
        for token in ("A1_XAU_", "_EXACT_MT5_REVIEW_202207_202606"):
            source = source.replace(token, "")
        source = source.replace("_", " ").title()
    return f"A1 XAU {source} Exact MT5 Weekly Target Review"


def render_markdown(payload: dict[str, Any]) -> str:
    rows = payload["rows"]
    lines = [
        f"# {payload['title']}",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "",
        "## Boundary",
        "",
        "- Exact MT5 Strategy Tester trade CSVs only.",
        "- Metrics below are recomputed from parsed trades and the frozen baseline week table.",
        f"- The `{payload['variant_count']}` tested cells were predeclared; no optimizer or post-result threshold expansion is included.",
        "",
        "## Results",
        "",
        "| Variant | Trades | WR | W/L | Net USD | Standalone +Weeks | Hybrid +Weeks | Hybrid Active | Red Touched | Red Flipped | Red Worsened | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['variant']}` | {row['standalone_trades']} | {row['standalone_wr_pct']}% | "
            f"{row['standalone_wl']} | {row['standalone_net_usd']} | "
            f"{row['standalone_positive_week_pct']}% | {row['hybrid_positive_week_pct']}% | "
            f"{row['hybrid_active_weekday_pct']}% | {row['red_weeks_touched']} | "
            f"{row['red_weeks_flipped']} | {row['red_weeks_worsened']} | `{row['decision']}` |"
        )
    best = payload["best"]
    lines.extend(
        [
            "",
            "## Best Read",
            "",
            f"- Best hybrid weekly row: `{best['variant']}`.",
            f"- Hybrid positive calendar weeks: `{best['hybrid_positive_week_pct']}%`.",
            f"- Hybrid active weekdays: `{best['hybrid_active_weekday_pct']}%`.",
            f"- Red weeks flipped/worsened: `{best['red_weeks_flipped']}` / `{best['red_weeks_worsened']}`.",
            f"- Decision: `{best['decision']}`.",
            "",
            "## Interpretation",
            "",
            "A useful source must move hybrid positive weeks materially toward 70% while not adding more damaged red weeks than it repairs. "
            "If the best row remains below 60% hybrid positive weeks, this source class should be frozen rather than tuned.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score exact MT5 variant results against the A1 weekly target.")
    parser.add_argument("--result-json", type=Path, default=DEFAULT_RESULT_JSON)
    parser.add_argument("--output-stem", default=OUTPUT_STEM)
    args = parser.parse_args()

    payload = json.loads(args.result_json.read_text(encoding="utf-8"))
    baseline_weeks = load_baseline_weeks(BASELINE_WEEK_TABLE)
    baseline_trades = load_baseline_trades(BASELINE_KEPT)
    all_weeks = sorted(baseline_weeks)
    weekdays = market_weekdays(date(2022, 7, 1), date(2026, 6, 30))
    rows = [
        evaluate_variant(result, baseline_weeks, baseline_trades, all_weeks, weekdays)
        for result in payload["variants"]
    ]
    rows.sort(
        key=lambda row: (
            row["hybrid_positive_week_pct"],
            row["red_weeks_flipped"] - row["red_weeks_worsened"],
            row["hybrid_wl"] or 0.0,
        ),
        reverse=True,
    )
    best = rows[0] if rows else {}
    report = {
        "title": derive_title(payload, args.output_stem),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_result_json": str(args.result_json),
        "baseline_week_table": str(BASELINE_WEEK_TABLE),
        "baseline_kept": str(BASELINE_KEPT),
        "variant_count": len(payload.get("variants") or []),
        "weeks": len(all_weeks),
        "weekdays": len(weekdays),
        "best": best,
        "rows": rows,
    }
    out_json = REPORTS / f"{args.output_stem}.json"
    out_md = REPORTS / f"{args.output_stem}.md"
    out_csv = REPORTS / f"{args.output_stem}_SUMMARY.csv"
    out_json.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    write_csv(out_csv, rows)
    print(json.dumps({"best": best, "report": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
