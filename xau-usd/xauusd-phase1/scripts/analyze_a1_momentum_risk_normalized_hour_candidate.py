from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_hour_prune_broad_search import dedupe_after_hour_block, load_seed_rows
from analyze_a1_momentum_market_day_coverage_search import date_window, day_distribution
from analyze_a1_momentum_market_day_coverage_stress import grouped_stats
from analyze_a1_momentum_position_sizing_diagnostic import r_profit, rel, top_removed


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_RISK_NORMALIZED_HOUR_CANDIDATE_2026_07_03"
BROAD_CSV = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_HOUR_PRUNE_BROAD_SEARCH_2026_07_03.csv"
RISK_USD_EXAMPLES = (5.0, 10.0, 20.0)


def pf(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss <= 0:
        return None
    return round(gross_profit / gross_loss, 3)


def rolling(values: list[float], window: int) -> dict[str, Any]:
    if len(values) < window:
        return {"available": False, "window": window}
    nets = [round(sum(values[index : index + window]), 2) for index in range(0, len(values) - window + 1)]
    return {
        "available": True,
        "window": window,
        "count": len(nets),
        "negative_windows": sum(1 for value in nets if value < 0),
        "worst_net_r": min(nets),
        "best_net_r": max(nets),
    }


def candidate_combos() -> list[tuple[int, ...]]:
    rows: list[dict[str, str]] = []
    with BROAD_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not row.get("blocked_hours_csv"):
                continue
            if float(row.get("trades_per_market_day") or 0.0) < 3.0:
                continue
            if float(row.get("win_rate_pct") or 0.0) < 60.0:
                continue
            if float(row.get("profit_factor") or 0.0) < 1.25:
                continue
            if float(row.get("top300_removed_r") or 0.0) <= 0.0:
                continue
            if int(float(row.get("rolling_250_negative") or 0.0)) != 0:
                continue
            rows.append(row)
    rows.sort(key=lambda row: (float(row.get("top300_removed_r") or 0.0), float(row.get("net_usd") or 0.0)), reverse=True)
    combos: list[tuple[int, ...]] = []
    for row in rows[:12]:
        combo = tuple(int(token) for token in row["blocked_hours_csv"].split(",") if token != "")
        if combo not in combos:
            combos.append(combo)
    return combos


def evaluate(sorted_rows: list[dict[str, Any]], blocked_hours: tuple[int, ...]) -> dict[str, Any]:
    kept, duplicate_drops = dedupe_after_hour_block(sorted_rows, blocked_hours)
    ordered = sorted(kept, key=lambda row: (row["exit_time"], row["entry_time"], row["variant"]))
    start, end, market_days = date_window(ordered)
    usd_values = [float(row.get("profit", 0.0) or 0.0) for row in ordered]
    r_values = [r_profit(row) for row in ordered]
    wins = sum(1 for value in r_values if value > 0)
    half = grouped_stats(ordered, "half_year")
    quarter = grouped_stats(ordered, "quarter")
    row: dict[str, Any] = {
        "decision": "RISK_NORMALIZED_REVIEW_CANDIDATE",
        "blocked_hours_csv": ",".join(str(hour) for hour in blocked_hours),
        "trades": len(ordered),
        "wins": wins,
        "win_rate_pct": round(100.0 * wins / len(ordered), 2) if ordered else 0.0,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
        "duplicate_drops": duplicate_drops,
        "net_usd_fixed_lot": round(sum(usd_values), 2),
        "pf_usd_fixed_lot": pf(usd_values),
        "top200_removed_usd_fixed_lot": top_removed(usd_values, 200),
        "net_r": round(sum(r_values), 2),
        "pf_r": pf(r_values),
        "top100_removed_r": top_removed(r_values, 100),
        "top200_removed_r": top_removed(r_values, 200),
        "top300_removed_r": top_removed(r_values, 300),
        "negative_half_years": sum(1 for value in half if value["net_usd"] <= 0),
        "negative_quarters": sum(1 for value in quarter if value["net_usd"] <= 0),
        "rolling250_r": rolling(r_values, 250),
        "rolling500_r": rolling(r_values, 500),
    }
    row.update(day_distribution(ordered, market_days))
    for risk_usd in RISK_USD_EXAMPLES:
        row[f"estimated_net_usd_at_{int(risk_usd)}_risk"] = round(row["net_r"] * risk_usd, 2)
        row[f"estimated_top300_usd_at_{int(risk_usd)}_risk"] = round(row["top300_removed_r"] * risk_usd, 2)
    if row["trades"] < 1000:
        row["decision"] = "FAIL_SAMPLE"
    elif row["trades_per_market_day"] < 3.0:
        row["decision"] = "FAIL_CADENCE"
    elif row["win_rate_pct"] < 60.0 or (row["pf_r"] or 0.0) < 1.25:
        row["decision"] = "FAIL_R_QUALITY"
    elif row["top300_removed_r"] <= 0.0:
        row["decision"] = "FAIL_R_TOP300"
    elif row["rolling250_r"].get("negative_windows", 0) > 0 or row["rolling500_r"].get("negative_windows", 0) > 0:
        row["decision"] = "FAIL_R_ROLLING"
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "blocked_hours_csv",
        "trades",
        "win_rate_pct",
        "trades_per_market_day",
        "net_r",
        "pf_r",
        "top100_removed_r",
        "top200_removed_r",
        "top300_removed_r",
        "rolling250_negative",
        "rolling250_worst_r",
        "rolling500_negative",
        "rolling500_worst_r",
        "net_usd_fixed_lot",
        "pf_usd_fixed_lot",
        "top200_removed_usd_fixed_lot",
        "estimated_net_usd_at_5_risk",
        "estimated_net_usd_at_10_risk",
        "estimated_net_usd_at_20_risk",
        "estimated_top300_usd_at_10_risk",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{field: row.get(field) for field in fields},
                    "rolling250_negative": row["rolling250_r"].get("negative_windows"),
                    "rolling250_worst_r": row["rolling250_r"].get("worst_net_r"),
                    "rolling500_negative": row["rolling500_r"].get("negative_windows"),
                    "rolling500_worst_r": row["rolling500_r"].get("worst_net_r"),
                }
            )


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        "# A1 XAU M5 Momentum Risk-Normalized Hour Candidate - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Why This Exists",
        "",
        "The broad hour-prune search still fails fixed-lot USD top-200 robustness by a small amount. The same candidate is positive under fixed-risk R, which suggests part of the weakness is position-sizing geometry: fixed 0.01 lots let large-stop winners carry the book while small-stop losses remain noisy.",
        "",
        "This report treats each trade as fixed-risk: losers are `-1R`, winners use the tested RR from the source row. It does not prove live profitability, but it tells us whether a risk-normalized lot-sizing EA is worth reviewer/owner evaluation.",
        "",
        "## Best Risk-Normalized Candidate",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best['decision']}` |",
        f"| Blocked hours | `{best['blocked_hours_csv']}` |",
        f"| Trades | {best['trades']} |",
        f"| Win rate | {best['win_rate_pct']}% |",
        f"| Trades / market day | {best['trades_per_market_day']} |",
        f"| Net R | {best['net_r']}R |",
        f"| PF R | {best['pf_r']} |",
        f"| Top 300 removed | {best['top300_removed_r']}R |",
        f"| Rolling 250 negative | {best['rolling250_r'].get('negative_windows')} |",
        f"| Rolling 500 negative | {best['rolling500_r'].get('negative_windows')} |",
        f"| Fixed-lot USD top200 removed | {best['top200_removed_usd_fixed_lot']} USD |",
        f"| Estimated net at $10 risk/trade | {best['estimated_net_usd_at_10_risk']} USD |",
        f"| Estimated top300 removed at $10 risk/trade | {best['estimated_top300_usd_at_10_risk']} USD |",
        "",
        "## Candidate Rows",
        "",
        "| Rank | Decision | Block Hours | Trades | WR | T/market day | Net R | PF R | Top300 R | Roll250 neg | Est net @ $10R |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["rows"], start=1):
        lines.append(
            f"| {index} | `{row['decision']}` | `{row['blocked_hours_csv']}` | {row['trades']} | {row['win_rate_pct']}% | {row['trades_per_market_day']} | {row['net_r']} | {row['pf_r']} | {row['top300_removed_r']} | {row['rolling250_r'].get('negative_windows')} | {row['estimated_net_usd_at_10_risk']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "This is not an attachment approval. The default-off EA support must be independently reviewed and exact-tested before any demo runtime change.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Report: `{payload['report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    sorted_rows = load_seed_rows()
    rows = [evaluate(sorted_rows, combo) for combo in candidate_combos()]
    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "RISK_NORMALIZED_REVIEW_CANDIDATE" else 1,
            -float(row.get("top300_removed_r") or 0.0),
            -float(row.get("net_r") or 0.0),
        )
    )
    best = rows[0] if rows else {}
    verdict = (
        "FOUND_RISK_NORMALIZED_REVIEW_CANDIDATE"
        if best.get("decision") == "RISK_NORMALIZED_REVIEW_CANDIDATE"
        else "NO_RISK_NORMALIZED_CANDIDATE"
    )
    next_action = (
        "review_default_off_risk_sizing_and_exact_test_before_runtime"
        if verdict == "FOUND_RISK_NORMALIZED_REVIEW_CANDIDATE"
        else "continue_new_entry_search"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_RISK_NORMALIZED_REPORT_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_analysis_only_no_runtime_change",
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "rows": rows,
        "json": rel(output_json),
        "csv": rel(output_csv),
        "report": rel(output_md),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(json.dumps({k: best.get(k) for k in ("decision", "blocked_hours_csv", "trades", "win_rate_pct", "net_r", "pf_r", "top300_removed_r")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
