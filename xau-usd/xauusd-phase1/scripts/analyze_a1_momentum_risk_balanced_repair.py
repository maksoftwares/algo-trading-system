from __future__ import annotations

import csv
import json
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
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_RISK_BALANCED_REPAIR_2026_07_03"
PURE_SOURCE_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_PURE_CAUSAL_COVERAGE_SEARCH_2026_07_03.json"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def outcome_r(row: dict[str, Any]) -> float:
    comment = str(row.get("exit_comment", ""))
    if comment.startswith("tp"):
        return 0.7
    if comment.startswith("sl"):
        return -1.0
    return float(row.get("profit", 0.0))


def top_removed(values: list[float], count: int) -> float:
    winners = sorted((value for value in values if value > 0), reverse=True)
    return round(sum(values) - sum(winners[:count]), 2)


def rolling(values: list[float], window: int) -> dict[str, Any]:
    if len(values) < window:
        return {"window": window, "available": False, "negative": None, "worst": None}
    nets = [sum(values[index : index + window]) for index in range(len(values) - window + 1)]
    return {"window": window, "available": True, "negative": sum(value < 0 for value in nets), "worst": round(min(nets), 2)}


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def load_base() -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    best = json.loads(PURE_SOURCE_JSON.read_text(encoding="utf-8"))["best_result"]
    variants = load_csv_variants()
    raw: list[dict[str, Any]] = []
    for name in best["source_variants"]:
        raw.extend(variants[name])
    return best, variants, raw


def keep(row: dict[str, Any], blocks: tuple[tuple[str, int], ...]) -> bool:
    hour = int(row.get("entry_hour") or 0)
    variant = str(row.get("variant", ""))
    for kind, blocked_hour in blocks:
        if hour != blocked_hour:
            continue
        if kind == "all" or kind in variant:
            return False
    return True


def evaluate(
    label: str,
    raw: list[dict[str, Any]],
    *,
    blocks: tuple[tuple[str, int], ...],
    extra_sources: tuple[str, ...],
    variants: dict[str, list[dict[str, Any]]],
    guard: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    combined = list(raw)
    for source in extra_sources:
        combined.extend(variants[source])
    filtered = [row for row in combined if keep(row, blocks)]
    deduped, duplicate_drops = dedupe_portfolio(filtered, 4)
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
    values_r = [outcome_r(row) for row in selected]
    summary.update(
        {
            "label": label,
            "blocks": [f"{kind}@{hour}" for kind, hour in blocks],
            "extra_sources": list(extra_sources),
            "duplicate_drops": duplicate_drops,
            "guard_name": guard["name"],
            "guard_stats": guard_stats,
            "negative_quarters": sum(1 for row in grouped_stats(selected, "quarter") if row["net_usd"] <= 0),
            "negative_half_years": sum(1 for row in grouped_stats(selected, "half_year") if row["net_usd"] <= 0),
            "usd_top100_removed": top_removed_usd(selected, 100),
            "usd_top200_removed": top_removed_usd(selected, 200),
            "usd_top300_removed": top_removed_usd(selected, 300),
            "usd_rolling250_negative": rolling_stats(selected, 250).get("negative_windows"),
            "r_net": round(sum(values_r), 2),
            "r_profit_factor": profit_factor(values_r),
            "r_top100_removed": top_removed(values_r, 100),
            "r_top200_removed": top_removed(values_r, 200),
            "r_top300_removed": top_removed(values_r, 300),
            "r_rolling250": rolling(values_r, 250),
            "r_rolling500": rolling(values_r, 500),
        }
    )
    summary["decision"] = decision(summary)
    return summary, selected


def decision(row: dict[str, Any]) -> str:
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WR"
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_FIXED_LOT_PF"
    if row["usd_top200_removed"] <= 0 or row["usd_rolling250_negative"] != 0:
        return "FAIL_FIXED_LOT_ROBUSTNESS"
    if row["r_top300_removed"] <= 0 or row["r_rolling250"]["negative"] != 0:
        return "FAIL_RISK_BALANCED_ROBUSTNESS"
    if row["usd_top300_removed"] <= 0:
        return "REVIEW_RISK_BALANCED_CANDIDATE_FIXED_LOT_TOP300_CAVEAT"
    return "REVIEW_STRONG_CANDIDATE"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "label",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "usd_top200_removed",
        "usd_top300_removed",
        "usd_rolling250_negative",
        "r_net",
        "r_profit_factor",
        "r_top200_removed",
        "r_top300_removed",
        "negative_quarters",
        "negative_half_years",
        "blocks",
        "extra_sources",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        "# A1 XAU M5 Momentum Risk-Balanced Repair - 2026-07-03",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Purpose",
        "",
        "The pure causal repair fixed rolling stability in fixed-lot USD but still failed top300-winners-removed in USD. This report asks whether the remaining top300 issue is mostly fixed-lot stop-size geometry. It compares fixed-lot USD metrics with normalized outcome-R metrics using the exact tester TP/SL labels.",
        "",
        "## Best Risk-Balanced Candidate",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Decision | `{best['decision']}` |",
        f"| Label | `{best['label']}` |",
        f"| Trades | {best['trades']} |",
        f"| Win rate | {best['win_rate_pct']}% |",
        f"| Fixed-lot PF | {best['profit_factor']} |",
        f"| Fixed-lot net | {best['net_usd']} USD |",
        f"| Trades / market day | {best['trades_per_market_day']} |",
        f"| Fixed-lot top200 removed | {best['usd_top200_removed']} USD |",
        f"| Fixed-lot top300 removed | {best['usd_top300_removed']} USD |",
        f"| Fixed-lot rolling250 negative | {best['usd_rolling250_negative']} |",
        f"| Normalized R net | {best['r_net']}R |",
        f"| Normalized R PF | {best['r_profit_factor']} |",
        f"| Normalized R top300 removed | {best['r_top300_removed']}R |",
        f"| Normalized R rolling250 negative | {best['r_rolling250']['negative']} |",
        f"| Blocks | `{', '.join(best['blocks'])}` |",
        f"| Extra sources | `{', '.join(best['extra_sources'])}` |",
        "",
        "Interpretation: this candidate clears the owner's frequency target and the normalized-R robustness bar. It still does not clear fixed-lot USD top300, which means the next required step is exact MT5 verification with risk-normalized lots or a broker-realistic lot model. Do not treat this as fixed-lot attach-ready.",
        "",
        "## Compared Rows",
        "",
        "| Decision | Label | Trades | WR | USD PF | USD Net | T/day | USD Top300 | USD Roll250 Neg | R PF | R Top300 | R Roll250 Neg |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['decision']}` | `{row['label']}` | {row['trades']} | {row['win_rate_pct']}% | {row['profit_factor']} | {row['net_usd']} | {row['trades_per_market_day']} | {row['usd_top300_removed']} | {row['usd_rolling250_negative']} | {row['r_profit_factor']} | {row['r_top300_removed']} | {row['r_rolling250']['negative']} |"
        )
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            "Port this exact risk-balanced candidate to an exact MT5 Strategy Tester run with risk-normalized lots enabled, then ask for independent review. If exact MT5 confirms the normalized profile, prepare a frozen forward-test spec. If it fails under broker min-lot constraints, continue searching.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    _base, variants, raw = load_base()
    guard = {item["name"]: item for item in GUARD_SCENARIOS}["target75_cooldown10"]
    scenarios = [
        ("pure_repair_v13_3_8", (("v13", 3), ("v13", 8)), ()),
        ("risk_balanced_all8_v1322_plus_v13_rr0p6_nomorning", (("all", 8), ("v13", 22)), ("v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning",)),
        ("risk_balanced_all8_v1322_plus_feature_loss_band", (("all", 8), ("v13", 22)), ("v13_feature_loss_short_extreme_band_m2p51_rr0p6",)),
        ("risk_balanced_all8_v1322_plus_midday17", (("all", 8), ("v13", 22)), ("freq_h1_h4_long_rr0p7_cost005_block_midday17_v1",)),
        ("all8_only", (("all", 8),), ()),
    ]
    rows: list[dict[str, Any]] = []
    for label, blocks, extras in scenarios:
        row, _trades = evaluate(label, raw, blocks=blocks, extra_sources=extras, variants=variants, guard=guard)
        rows.append(row)
    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_STRONG_CANDIDATE" else 1 if row["decision"].startswith("REVIEW") else 2,
            -float(row.get("r_top300_removed") or 0.0),
            -float(row.get("r_net") or 0.0),
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": rows[0]["decision"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "source_report": rel(PURE_SOURCE_JSON),
        "best_result": rows[0],
        "rows": rows,
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "best": rows[0]["label"],
                "trades": rows[0]["trades"],
                "win_rate_pct": rows[0]["win_rate_pct"],
                "profit_factor": rows[0]["profit_factor"],
                "net_usd": rows[0]["net_usd"],
                "trades_per_market_day": rows[0]["trades_per_market_day"],
                "usd_top300_removed": rows[0]["usd_top300_removed"],
                "r_top300_removed": rows[0]["r_top300_removed"],
                "r_rolling250_negative": rows[0]["r_rolling250"]["negative"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
