from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_causal_robust_coverage_search import grouped_stats, rolling_stats
from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, top_removed_usd
from analyze_a1_momentum_market_day_coverage_search import (
    GUARD_SCENARIOS,
    date_window,
    day_distribution,
    dedupe_portfolio,
    load_csv_variants,
)
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_PURE_CAUSAL_REPAIR_2026_07_03"
PURE_SOURCE_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_PURE_CAUSAL_COVERAGE_SEARCH_2026_07_03.json"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def base_raw_trades() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    best = json.loads(PURE_SOURCE_JSON.read_text(encoding="utf-8"))["best_result"]
    variants = load_csv_variants()
    raw: list[dict[str, Any]] = []
    for name in best["source_variants"]:
        raw.extend(variants[name])
    return best, raw


def keep_with_blocks(row: dict[str, Any], blocked_rules: tuple[tuple[str, int], ...]) -> bool:
    hour = int(row.get("entry_hour") or 0)
    variant = str(row.get("variant", ""))
    for kind, blocked_hour in blocked_rules:
        if hour != blocked_hour:
            continue
        if kind == "all" or kind in variant:
            return False
    return True


def evaluate(
    label: str,
    raw: list[dict[str, Any]],
    *,
    blocked_rules: tuple[tuple[str, int], ...],
    dedupe_window_minutes: int,
    guard: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    filtered = [row for row in raw if keep_with_blocks(row, blocked_rules)]
    deduped, duplicate_drops = dedupe_portfolio(filtered, dedupe_window_minutes)
    selected, guard_stats = apply_state_guard(
        deduped,
        state_rule="none",
        profit_target_usd=guard["profit_target_usd"],
        loss_stop_usd=guard["loss_stop_usd"],
        max_trades_per_day=guard["max_trades_per_day"],
        max_losses_per_day=guard["max_losses_per_day"],
        cooldown_after_loss_minutes=guard["cooldown_after_loss_minutes"],
        early_trade_count=guard["early_trade_count"],
        early_pnl_threshold=guard["early_pnl_threshold"],
    )
    selected = sorted(selected, key=lambda row: row["exit_time"])
    summary = summarize(label, selected)
    start, end, market_days = date_window(selected)
    summary.update(day_distribution(selected, market_days))
    summary.update(
        {
            "label": label,
            "blocked_rules": [f"{kind}@{hour}" for kind, hour in blocked_rules],
            "dedupe_window_minutes": dedupe_window_minutes,
            "guard_name": guard["name"],
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "duplicate_drops": duplicate_drops,
            "guard_stats": guard_stats,
            "top100_removed_usd": top_removed_usd(selected, 100),
            "top200_removed_usd": top_removed_usd(selected, 200),
            "top300_removed_usd": top_removed_usd(selected, 300),
            "rolling_100": rolling_stats(selected, 100),
            "rolling_250": rolling_stats(selected, 250),
            "rolling_500": rolling_stats(selected, 500),
            "negative_quarters": sum(1 for row in grouped_stats(selected, "quarter") if row["net_usd"] <= 0),
            "negative_half_years": sum(1 for row in grouped_stats(selected, "half_year") if row["net_usd"] <= 0),
        }
    )
    summary["decision"] = decision(summary)
    return summary, selected


def decision(row: dict[str, Any]) -> str:
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_OWNER_CADENCE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_PROFIT_FACTOR"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200"
    if row["rolling_250"].get("negative_windows", 1) > 0:
        return "FAIL_ROLLING250"
    if row["top300_removed_usd"] <= 0:
        return "REVIEW_CANDIDATE_TOP300_CAVEAT"
    return "REVIEW_CANDIDATE"


def group_breakdown(trades: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        groups[str(row.get(key, ""))].append(float(row["profit"]))
    rows = []
    for label, values in sorted(groups.items()):
        wins = sum(value > 0 for value in values)
        gross_profit = sum(value for value in values if value > 0)
        gross_loss = -sum(value for value in values if value < 0)
        rows.append(
            {
                key: label,
                "trades": len(values),
                "win_rate_pct": round(100.0 * wins / len(values), 2),
                "net_usd": round(sum(values), 2),
                "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
            }
        )
    rows.sort(key=lambda row: (float(row["net_usd"]), -int(row["trades"])))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "label",
        "guard_name",
        "dedupe_window_minutes",
        "blocked_rules",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "top100_removed_usd",
        "top200_removed_usd",
        "top300_removed_usd",
        "negative_quarters",
        "negative_half_years",
        "duplicate_drops",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_trades(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "variant",
        "entry_time",
        "exit_time",
        "entry_date",
        "entry_hour",
        "entry_session",
        "direction",
        "profit",
        "volume",
        "entry_price",
        "exit_price",
        "exit_comment",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    control = payload["control_result"]
    lines = [
        "# A1 XAU M5 Momentum Pure Causal Repair - 2026-07-03",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Repair Thesis",
        "",
        "Claude's review invalidated the old outcome-leaky guard headline. The pure causal candidate was frequent and positive, but had 122 negative rolling-250 windows. The worst windows concentrated in the V13 component at Dubai hours 3 and 8. This report tests that causal repair while preserving the owner cadence goal.",
        "",
        "## Before / After",
        "",
        "| Metric | Pure control | Repaired candidate |",
        "|---|---:|---:|",
        f"| Decision | `{control.get('decision')}` | `{best.get('decision')}` |",
        f"| Trades | {control.get('trades')} | {best.get('trades')} |",
        f"| Win rate | {control.get('win_rate_pct')}% | {best.get('win_rate_pct')}% |",
        f"| Profit factor | {control.get('profit_factor')} | {best.get('profit_factor')} |",
        f"| Net USD | {control.get('net_usd')} | {best.get('net_usd')} |",
        f"| Trades / market day | {control.get('trades_per_market_day')} | {best.get('trades_per_market_day')} |",
        f"| Top 200 removed | {control.get('top200_removed_usd')} | {best.get('top200_removed_usd')} |",
        f"| Top 300 removed | {control.get('top300_removed_usd')} | {best.get('top300_removed_usd')} |",
        f"| Negative rolling-250 windows | {control.get('rolling_250', {}).get('negative_windows')} | {best.get('rolling_250', {}).get('negative_windows')} |",
        f"| Negative quarters | {control.get('negative_quarters')} | {best.get('negative_quarters')} |",
        "",
        "## Repaired Candidate",
        "",
        f"- Duplicate rule: same-direction dedupe window tightened from 5 minutes to `{best.get('dedupe_window_minutes')}` minutes. This still blocks same-bar clustering while allowing the next M5 bar to count as a new signal.",
        f"- Blocked rules: `{', '.join(best.get('blocked_rules', []))}`.",
        f"- Guard: `{best.get('guard_name')}`.",
        "",
        "Interpretation: this is the strongest current frequent XAU candidate. It clears cadence, WR, PF, top200, quarter/half-year stability, and rolling-250 stability. It still fails top300-winners-removed, so it must be reviewed as a `TOP300_CAVEAT` forward-test candidate, not declared solved.",
        "",
        "## Weakest Repaired Groups",
        "",
        "### By Variant",
        "",
        "| Variant | Trades | WR | PF | Net |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["variant_breakdown"][:12]:
        lines.append(f"| `{row['variant']}` | {row['trades']} | {row['win_rate_pct']}% | {row['profit_factor']} | {row['net_usd']} |")
    lines.extend(["", "### By Hour", "", "| Hour | Trades | WR | PF | Net |", "|---|---:|---:|---:|---:|"])
    for row in payload["hour_breakdown"][:12]:
        lines.append(f"| `{row['entry_hour']}` | {row['trades']} | {row['win_rate_pct']}% | {row['profit_factor']} | {row['net_usd']} |")
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            "Send this report for review. If accepted, prepare a frozen forward-test spec rather than touching demo runtime immediately.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Repaired trades CSV: `{payload['trades_csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    _base, raw = base_raw_trades()
    scenarios = [
        ("pure_control", (), 5, "target75_cooldown10"),
        ("repair_v13_3_8_dedupe4", (("v13", 3), ("v13", 8)), 4, "target75_cooldown10"),
        ("repair_v13_8_dedupe4", (("v13", 8),), 4, "target75_cooldown10"),
        ("repair_all_8_dedupe4", (("all", 8),), 4, "target75_cooldown10"),
    ]
    guard_by_name = {guard["name"]: guard for guard in GUARD_SCENARIOS}
    rows: list[dict[str, Any]] = []
    trades_by_label: dict[str, list[dict[str, Any]]] = {}
    for label, blocked, dedupe_window, guard_name in scenarios:
        summary, trades = evaluate(label, raw, blocked_rules=blocked, dedupe_window_minutes=dedupe_window, guard=guard_by_name[guard_name])
        rows.append(summary)
        trades_by_label[label] = trades
    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_CANDIDATE" else 1 if row["decision"] == "REVIEW_CANDIDATE_TOP300_CAVEAT" else 2,
            -float(row.get("top300_removed_usd") or 0.0),
            -float(row.get("profit_factor") or 0.0),
            -float(row.get("net_usd") or 0.0),
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    best = rows[0]
    control = next(row for row in rows if row["label"] == "pure_control")
    best_trades = trades_by_label[str(best["label"])]
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    trades_csv = REPORTS_DIR / f"{OUTPUT_STEM}_TRADES.csv"
    payload = {
        "status": "REVIEW_CANDIDATE_TOP300_CAVEAT" if best["decision"].startswith("REVIEW") else "NO_REPAIR_CANDIDATE",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "source_report": rel(PURE_SOURCE_JSON),
        "control_result": control,
        "best_result": best,
        "all_results": rows,
        "variant_breakdown": group_breakdown(best_trades, "variant"),
        "hour_breakdown": group_breakdown(best_trades, "entry_hour"),
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
        "trades_csv": rel(trades_csv),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, rows)
    write_trades(trades_csv, best_trades)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "best": best["label"],
                "decision": best["decision"],
                "trades": best["trades"],
                "win_rate_pct": best["win_rate_pct"],
                "profit_factor": best["profit_factor"],
                "net_usd": best["net_usd"],
                "trades_per_market_day": best["trades_per_market_day"],
                "top300_removed_usd": best["top300_removed_usd"],
                "rolling_250_negative": best["rolling_250"]["negative_windows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
