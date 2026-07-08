from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    parse_dt,
    rel,
    summary_metrics,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    FROM_DATE,
    TO_DATE,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)
from run_a1_h4_d1_review_repair_exact import period_stats
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_SHORT_V2_ROBUSTNESS_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_SHORT_V2_ROBUSTNESS_20260708"
TAG = "OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606"
SHORT_PRIORITY = 88
SHORT_FAMILY = "xau_short_v2_robustness"

PARITY_EXPECTED = {
    "signals": 329,
    "win_rate_pct": 32.83,
    "avg_win_loss": 2.8332,
    "profit_factor": 1.3846,
    "net_usd": 441.42,
}

COMMON_SHORT_INPUTS = {
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.05",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
}

FROZEN_V2_INPUTS = {
    "InpSignalMode": "15",
    "InpUseH1TrendFilter": "true",
    "InpUseH4TrendFilter": "true",
    "InpH1TrendMinSlopePoints": "0",
    "InpH4TrendMinSlopePoints": "0",
    "InpShortCloseLocation": "0.42",
    "InpBearRetestLookbackBars": "10",
    "InpBearRetestSupportLookbackBars": "12",
    "InpBearRetestBreakAtr": "0.10",
    "InpBearRetestTouchAtr": "0.05",
    "InpBearRetestReclaimAtr": "0.05",
    "InpBearRetestStopBufferAtr": "0.25",
    "InpBearRetestMinBodyFraction": "0.30",
}

REGIME_DEFINITIONS = [
    {
        "rank": 1,
        "name": "short_v2_r1_d1_ema20_bearish",
        "label": "R1 baseline/parity: V2 D1 EMA20 bearish gate",
        "run_id": "BT_A1_XAU_SHORT_V2_R1_D1_EMA20_BEARISH",
        "inputs": {
            "InpD1SupportStateGateMode": "3",
            "InpD1SupportStateEmaPeriod": "20",
            "InpD1SupportStateSlopeLagBars": "5",
            "InpD1StructuralDownGateEnabled": "false",
        },
    },
    {
        "rank": 2,
        "name": "short_v2_r2_d1_ema20_nonup",
        "label": "R2: D1 EMA20 non-up gate",
        "run_id": "BT_A1_XAU_SHORT_V2_R2_D1_EMA20_NONUP",
        "inputs": {
            "InpD1SupportStateGateMode": "4",
            "InpD1SupportStateEmaPeriod": "20",
            "InpD1SupportStateSlopeLagBars": "5",
            "InpD1StructuralDownGateEnabled": "false",
        },
    },
    {
        "rank": 3,
        "name": "short_v2_r3_d1_ema50_structural_down",
        "label": "R3: D1 EMA50 structural down gate",
        "run_id": "BT_A1_XAU_SHORT_V2_R3_D1_EMA50_STRUCTURAL_DOWN",
        "inputs": {
            "InpD1SupportStateGateMode": "0",
            "InpD1StructuralDownGateEnabled": "true",
            "InpD1StructuralDownEmaPeriod": "50",
            "InpD1StructuralDownSlopeLagBars": "5",
        },
    },
]

YEAR_PERIODS = [
    ("2022", date(2022, 7, 1), date(2022, 12, 31)),
    ("2023", date(2023, 1, 1), date(2023, 12, 31)),
    ("2024", date(2024, 1, 1), date(2024, 12, 31)),
    ("2025", date(2025, 1, 1), date(2025, 12, 31)),
    ("2026", date(2026, 1, 1), date(2026, 6, 30)),
]

BLOCK_PERIODS = [
    ("B1", date(2022, 7, 1), date(2022, 12, 31)),
    ("B2", date(2023, 1, 1), date(2023, 6, 30)),
    ("B3", date(2023, 7, 1), date(2023, 12, 31)),
    ("B4", date(2024, 1, 1), date(2024, 6, 30)),
    ("B5", date(2024, 7, 1), date(2024, 12, 31)),
    ("B6", date(2025, 1, 1), date(2025, 6, 30)),
    ("B7", date(2025, 7, 1), date(2025, 12, 31)),
    ("B8", date(2026, 1, 1), date(2026, 6, 30)),
]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def parse_date(value: Any) -> date:
    return date.fromisoformat(str(value).strip())


def bool_text(value: bool) -> str:
    return "PASS" if value else "FAIL"


def build_variant(definition: dict[str, Any], rr: str = "2.00", suffix: str = "") -> a1.Variant:
    name = definition["name"] if not suffix else f"{definition['name']}_{suffix}"
    run_id = definition["run_id"] if not suffix else f"{definition['run_id']}_{suffix.upper()}"
    inputs = {
        **COMMON_SHORT_INPUTS,
        **FROZEN_V2_INPUTS,
        **definition["inputs"],
        "InpRiskReward": rr,
    }
    return a1.Variant(
        name=name,
        label=f"{definition['label']}, RR {rr}",
        run_id=run_id,
        tester_inputs=inputs,
    )


def build_t1_variants() -> list[a1.Variant]:
    return [build_variant(definition) for definition in REGIME_DEFINITIONS]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def guard_counts(result: dict[str, Any]) -> dict[str, Any]:
    rows = read_tsv(Path(result["order_csv"]))
    actions: dict[str, int] = defaultdict(int)
    reasons: dict[str, int] = defaultdict(int)
    for row in rows:
        action = row.get("action", "")
        actions[action] += 1
        if action == "GUARD_BLOCK":
            reasons[row.get("reason", "")] += 1
    return {"order_rows": len(rows), "actions": dict(actions), "guard_reasons": dict(reasons)}


def variant_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    name = result["name"]
    trade_csv = Path(result["trade_csv"])
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        exit_text = str(row.get("exit_time") or "").strip()
        exit_time = parse_dt(exit_text) if exit_text else entry_time
        rows.append(
            {
                "component": name,
                "source_id": name,
                "upstream_source_id": name,
                "upstream_component": "exact_mt5_short_v2_robustness",
                "family_group": SHORT_FAMILY,
                "source_priority": SHORT_PRIORITY,
                "cell_id": name,
                "component_priority": 0,
                "variant_name": name,
                "entry_time": entry_time,
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "exit_time": exit_time,
                "exit_date": exit_time.date(),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": parse_money(row.get("profit_float") or row.get("profit_aed")),
                "tickets": 1,
                "lots": parse_money(row.get("volume")),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def period_rows(rows: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    return [row for row in rows if start <= row["entry_date"] <= end]


def period_metric_row(variant: str, period: str, rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    stats = period_stats(rows, start, end)
    return {
        "variant": variant,
        "period": period,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "trades": stats["signals"],
        "wins": stats["wins"],
        "losses": stats["losses"],
        "wr": stats["win_rate_pct"],
        "wl": stats["avg_win_loss"],
        "pf": stats["profit_factor"],
        "net": stats["net_usd"],
    }


def concentration_stats(rows: list[dict[str, Any]], net: float) -> dict[str, Any]:
    wins = sorted((float(row["pnl_usd"]) for row in rows if float(row["pnl_usd"]) > 0.0), reverse=True)
    by_day: dict[date, float] = defaultdict(float)
    for row in rows:
        by_day[row["entry_date"]] += float(row["pnl_usd"])

    top_days = sorted(by_day.items(), key=lambda item: item[1], reverse=True)
    top1_day = top_days[0][1] if top_days else 0.0
    top3_day_sum = sum(value for _day, value in top_days[:3])
    return {
        "top1_removed_net": round(net - sum(wins[:1]), 2),
        "top5_removed_net": round(net - sum(wins[:5]), 2),
        "top10_removed_net": round(net - sum(wins[:10]), 2),
        "best_day_net": round(top1_day, 2),
        "best_day_share_pct": round(100.0 * max(top1_day, 0.0) / net, 2) if net > 0.0 else None,
        "top3_days_removed_net": round(net - top3_day_sum, 2),
        "top3_days": [
            {"date": day.isoformat(), "net": round(value, 2)}
            for day, value in top_days[:3]
        ],
    }


def parity_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "signals_match": int(row["trades"]) == PARITY_EXPECTED["signals"],
        "wr_match": abs(float(row["wr"]) - PARITY_EXPECTED["win_rate_pct"]) <= 0.01,
        "wl_match": abs(float(row["wl"] or 0.0) - PARITY_EXPECTED["avg_win_loss"]) <= 0.0001,
        "pf_match": abs(float(row["pf"] or 0.0) - PARITY_EXPECTED["profit_factor"]) <= 0.0001,
        "net_match": abs(float(row["net"]) - PARITY_EXPECTED["net_usd"]) <= 0.01,
    }


def t1_checks(
    metrics: dict[str, Any],
    stress: dict[str, Any],
    year_rows: list[dict[str, Any]],
) -> dict[str, bool]:
    yearly_positive = sum(1 for row in year_rows if float(row["net"]) > 0.0)
    net_2023_2024 = sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"})
    return {
        "positive_year_buckets_ge_3": yearly_positive >= 3,
        "y2023_2024_net_ge_0": net_2023_2024 >= 0.0,
        "full_net_gt_0": metrics["net_usd"] > 0.0,
        "stress_pf_ge_1p20": (stress["profit_factor"] or 0.0) >= 1.20,
        "trades_ge_200": metrics["signals"] >= 200,
    }


def t2_checks(metrics: dict[str, Any], block_rows: list[dict[str, Any]]) -> dict[str, Any]:
    full_net = float(metrics["net_usd"])
    nonnegative_blocks = sum(1 for row in block_rows if float(row["net"]) >= 0.0)
    max_block_net = max((float(row["net"]) for row in block_rows), default=0.0)
    max_block_share_pct = round(100.0 * max(max_block_net, 0.0) / full_net, 2) if full_net > 0.0 else None
    early_positive = any(float(row["net"]) > 0.0 for row in block_rows[:6])
    return {
        "nonnegative_blocks": nonnegative_blocks,
        "max_block_net": round(max_block_net, 2),
        "max_block_share_pct": max_block_share_pct,
        "early_block_positive": early_positive,
        "nonnegative_blocks_ge_6": nonnegative_blocks >= 6,
        "no_single_block_gt_50pct": max_block_share_pct is not None and max_block_share_pct <= 50.0,
        "at_least_one_b1_b6_positive": early_positive,
    }


def variant_summary(definition: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(rows)
    year_rows = [period_metric_row(definition["name"], label, rows, start, end) for label, start, end in YEAR_PERIODS]
    block_rows = [period_metric_row(definition["name"], label, rows, start, end) for label, start, end in BLOCK_PERIODS]
    concentration = concentration_stats(rows, metrics["net_usd"])
    checks = t1_checks(metrics, stress, year_rows)
    concentration_checks = {
        "top10_removed_net_gt_0": concentration["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": concentration["top3_days_removed_net"] > 0.0,
    }
    return {
        "variant": definition["name"],
        "rank": definition["rank"],
        "label": definition["label"],
        "trades": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_trades": stress["signals"],
        "stress_030_wr": stress["win_rate_pct"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_pf": stress["profit_factor"],
        "stress_030_net": stress["net_usd"],
        "positive_week_pct": shape["positive_week_pct"],
        "worst_week": shape["worst_week_usd"],
        "top1_removed_net": concentration["top1_removed_net"],
        "top5_removed_net": concentration["top5_removed_net"],
        "top10_removed_net": concentration["top10_removed_net"],
        "best_day_share_pct": concentration["best_day_share_pct"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "top3_days": concentration["top3_days"],
        "positive_year_buckets": sum(1 for row in year_rows if float(row["net"]) > 0.0),
        "net_2023_2024": round(sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"}), 2),
        "t1_checks": checks,
        "t1_pass": all(checks.values()),
        "concentration_checks": concentration_checks,
        "concentration_pass": all(concentration_checks.values()),
        "t2_checks": t2_checks(metrics, block_rows),
        "year_rows": year_rows,
        "block_rows": block_rows,
    }


def flat_summary_row(summary: dict[str, Any]) -> dict[str, Any]:
    checks = summary["t1_checks"]
    concentration = summary["concentration_checks"]
    t2 = summary["t2_checks"]
    return {
        "variant": summary["variant"],
        "trades": summary["trades"],
        "wins": summary["wins"],
        "losses": summary["losses"],
        "wr": summary["wr"],
        "wl": summary["wl"],
        "pf": summary["pf"],
        "net": summary["net"],
        "stress_030_pf": summary["stress_030_pf"],
        "stress_030_wl": summary["stress_030_wl"],
        "stress_030_net": summary["stress_030_net"],
        "positive_week_pct": summary["positive_week_pct"],
        "worst_week": summary["worst_week"],
        "positive_year_buckets": summary["positive_year_buckets"],
        "net_2023_2024": summary["net_2023_2024"],
        "top10_removed_net": summary["top10_removed_net"],
        "top3_days_removed_net": summary["top3_days_removed_net"],
        "best_day_share_pct": summary["best_day_share_pct"],
        "t1_pass": summary["t1_pass"],
        "concentration_pass": summary["concentration_pass"],
        "t2_nonnegative_blocks": t2["nonnegative_blocks"],
        "t2_max_block_share_pct": t2["max_block_share_pct"],
        "t2_early_block_positive": t2["early_block_positive"],
        **{f"t1_{key}": value for key, value in checks.items()},
        **{f"concentration_{key}": value for key, value in concentration.items()},
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_mt5_variants(
    variants: list[a1.Variant],
    tag: str,
    report_md: Path,
    report_json: Path,
    timeout: int,
) -> dict[str, Any]:
    a1.VARIANTS = variants
    return a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(tag),
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=timeout,
        deposit="1000",
        currency="USD",
    )


def run_t3(
    winner_definition: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    rr_variants = [
        build_variant(winner_definition, rr="1.50", suffix="rr15"),
        build_variant(winner_definition, rr="2.00", suffix="rr20"),
        build_variant(winner_definition, rr="2.50", suffix="rr25"),
    ]
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}_T3_RR_MT5_COMPONENTS.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}_T3_RR_MT5_COMPONENTS.json"
    mt5_payload = run_mt5_variants(
        rr_variants,
        f"{TAG}_T3_RR",
        report_md,
        report_json,
        timeout,
    )

    rr_rows = []
    for result in mt5_payload["variants"]:
        rows = variant_rows(result)
        metrics = summary_metrics(rows, market_days=MARKET_DAYS)
        stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
        rr_rows.append(
            {
                "variant": result["name"],
                "trades": metrics["signals"],
                "wr": metrics["win_rate_pct"],
                "wl": metrics["avg_win_loss"],
                "pf": metrics["profit_factor"],
                "net": metrics["net_usd"],
                "stress_030_pf": stress["profit_factor"],
                "stress_030_wl": stress["avg_win_loss"],
                "stress_030_net": stress["net_usd"],
                "t3_pass": metrics["net_usd"] > 0.0 and (stress["profit_factor"] or 0.0) >= 1.15,
            }
        )
    return {
        "mt5_payload": mt5_payload,
        "rows": rr_rows,
        "t3_pass": bool(rr_rows) and all(row["t3_pass"] for row in rr_rows),
        "outputs": {
            "t3_mt5_components_md": str(report_md),
            "t3_mt5_components_json": str(report_json),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Short V2 Robustness Exact MT5 Pass",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 robustness pass for `short_hedge_v2_breakdown_retest`. The pass changes only the preregistered D1 regime definition across R1/R2/R3; no session/hour/day/month filters or post-result quality filters were added.",
        "",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## T1 Regime Results",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Pos year buckets | 2023+2024 net | Top10-removed net | Top3-days-removed net | T1 | Conc. |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["summary_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | "
            f"{(row['pf'] or 0.0):.4f} | {row['net']:.2f} | {(row['stress_030_pf'] or 0.0):.4f} | "
            f"{row['stress_030_net']:.2f} | {row['positive_year_buckets']} | {row['net_2023_2024']:.2f} | "
            f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | "
            f"{bool_text(row['t1_pass'])} | {bool_text(row['concentration_pass'])} |"
        )

    lines.extend(["", "## By Year", ""])
    for variant in payload["variant_summaries"]:
        lines.extend(
            [
                f"### `{variant['variant']}`",
                "",
                "| Year | Trades | WR% | W/L | PF | Net |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in variant["year_rows"]:
            lines.append(
                f"| {row['period']} | {row['trades']} | {row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | "
                f"{(row['pf'] or 0.0):.4f} | {row['net']:.2f} |"
            )
        lines.append("")

    lines.extend(["## Walk-Forward Blocks", ""])
    for variant in payload["variant_summaries"]:
        t2 = variant["t2_checks"]
        lines.extend(
            [
                f"### `{variant['variant']}`",
                "",
                f"T2 preview: `{t2['nonnegative_blocks']}/8` nonnegative blocks, max block share `{t2['max_block_share_pct']}`, early positive block `{t2['early_block_positive']}`.",
                "",
                "| Block | Start | End | Trades | WR% | W/L | PF | Net |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in variant["block_rows"]:
            lines.append(
                f"| {row['period']} | {row['start']} | {row['end']} | {row['trades']} | "
                f"{row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | {(row['pf'] or 0.0):.4f} | {row['net']:.2f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Decision",
            "",
            payload["interpretation"],
            "",
        ]
    )
    if payload.get("winner"):
        lines.extend(
            [
                f"T1 winner by preregistered simplicity rule: `{payload['winner']['variant']}`",
                f"T2 pass: `{bool_text(payload['winner']['t2_pass'])}`",
                f"Concentration pass: `{bool_text(payload['winner']['concentration_pass'])}`",
                "",
            ]
        )
    if payload.get("t3"):
        lines.extend(
            [
                "## T3 RR Robustness",
                "",
                "| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Pass |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in payload["t3"]["rows"]:
            lines.append(
                f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | "
                f"{(row['pf'] or 0.0):.4f} | {row['net']:.2f} | {(row['stress_030_pf'] or 0.0):.4f} | "
                f"{row['stress_030_net']:.2f} | {bool_text(row['t3_pass'])} |"
            )
        lines.append("")

    lines.extend(["## R1 Parity", ""])
    for key, value in payload["r1_parity_checks"].items():
        lines.append(f"- `{key}`: `{bool_text(value)}`")
    lines.extend(["", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 short V2 regime robustness pass.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    summary_csv = REPORTS_DIR / f"{OUTPUT_STEM}_SUMMARY.csv"
    year_csv = REPORTS_DIR / f"{OUTPUT_STEM}_YEAR.csv"
    block_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BLOCK.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"

    mt5_payload = run_mt5_variants(
        build_t1_variants(),
        TAG,
        mt5_report_md,
        mt5_report_json,
        args.variant_timeout_seconds,
    )

    definition_by_name = {definition["name"]: definition for definition in REGIME_DEFINITIONS}
    rows_by_name = {result["name"]: variant_rows(result) for result in mt5_payload["variants"]}
    variant_summaries = [
        variant_summary(definition_by_name[name], rows_by_name[name])
        for name in [definition["name"] for definition in REGIME_DEFINITIONS]
    ]
    summary_rows = [flat_summary_row(summary) for summary in variant_summaries]
    year_rows = [row for summary in variant_summaries for row in summary["year_rows"]]
    block_rows = [row for summary in variant_summaries for row in summary["block_rows"]]

    for name, rows in rows_by_name.items():
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{name}_NORMALIZED_TRADES.csv", rows)

    write_csv(summary_csv, summary_rows)
    write_csv(year_csv, year_rows)
    write_csv(block_csv, block_rows)

    r1_summary = variant_summaries[0]
    r1_parity = parity_checks(flat_summary_row(r1_summary))
    t1_passers = [summary for summary in variant_summaries if summary["t1_pass"]]
    winner = sorted(t1_passers, key=lambda row: row["rank"])[0] if t1_passers else None

    t3_payload: dict[str, Any] | None = None
    if winner:
        winner_t2 = winner["t2_checks"]
        t2_pass = (
            winner_t2["nonnegative_blocks_ge_6"]
            and winner_t2["no_single_block_gt_50pct"]
            and winner_t2["at_least_one_b1_b6_positive"]
        )
        winner["t2_pass"] = t2_pass
        if t2_pass and winner["concentration_pass"]:
            winner_definition = definition_by_name[winner["variant"]]
            t3_payload = run_t3(winner_definition, args.variant_timeout_seconds)
            write_csv(REPORTS_DIR / f"{OUTPUT_STEM}_T3_RR.csv", t3_payload["rows"])
    else:
        t2_pass = False

    if winner and winner.get("t2_pass") and winner["concentration_pass"]:
        status = "VALIDATED_STANDALONE_SHORT_BASE_REVIEW_REQUIRED"
        if t3_payload and not t3_payload["t3_pass"]:
            status = "VALIDATED_STANDALONE_SHORT_BASE_RR_FRAGILE_REVIEW_REQUIRED"
        interpretation = (
            f"`{winner['variant']}` passed the preregistered T1 gate, T2 walk-forward gate, "
            "and concentration guard. This is still research-only and needs reviewer sign-off before any forward-watchlist spec."
        )
    elif winner:
        status = "RECENT_REGIME_ARTIFACT_NOT_PROMOTED"
        failed = []
        if not winner.get("t2_pass"):
            failed.append("T2 walk-forward")
        if not winner["concentration_pass"]:
            failed.append("concentration")
        interpretation = (
            f"`{winner['variant']}` passed T1 by the preregistered simplicity rule but failed "
            f"{', '.join(failed)}. Keep V2 frozen as a reference; do not promote the standalone short."
        )
    else:
        status = "NO_DURABLE_STANDALONE_SHORT_EDGE"
        interpretation = (
            "No preregistered D1 regime definition passed T1. The standalone breakdown-retest short did not close "
            "the 2023-2024 stability hole while preserving positive full-window/stress/frequency gates. "
            "Per the work order, downgrade it to combined-portfolio hedge-only and stop standalone short iteration."
        )

    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "summary_csv": str(summary_csv),
        "year_csv": str(year_csv),
        "block_csv": str(block_csv),
        "mt5_components_md": str(mt5_report_md),
        "mt5_components_json": str(mt5_report_json),
    }
    if t3_payload:
        outputs.update(t3_payload["outputs"])
        outputs["t3_rr_csv"] = str(REPORTS_DIR / f"{OUTPUT_STEM}_T3_RR.csv")
    for name in rows_by_name:
        outputs[f"{name}_normalized_trades_csv"] = str(REPORTS_DIR / f"{OUTPUT_STEM}_{name}_NORMALIZED_TRADES.csv")

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "scope": {
            "period": f"{FROM_DATE} -> {TO_DATE}",
            "terminal_sandbox": mt5_payload["scope"]["terminal_sandbox"],
            "tester_model": mt5_payload["scope"]["model"],
            "deposit": mt5_payload["scope"]["tester_deposit"],
            "currency": mt5_payload["scope"]["tester_currency"],
            "no_live_runtime_change": mt5_payload["scope"]["no_live_runtime_change"],
        },
        "compile_log": mt5_payload["compile_log"],
        "mt5_component_details": [
            {
                "variant": result["name"],
                "trade_rows": len(rows_by_name[result["name"]]),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
            for result in mt5_payload["variants"]
        ],
        "summary_rows": summary_rows,
        "variant_summaries": variant_summaries,
        "winner": {
            "variant": winner["variant"],
            "t1_pass": winner["t1_pass"],
            "t2_pass": winner.get("t2_pass", False),
            "concentration_pass": winner["concentration_pass"],
            "t2_checks": winner["t2_checks"],
        }
        if winner
        else None,
        "t3": t3_payload,
        "r1_parity_checks": r1_parity,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "winner": payload["winner"],
                "summary_rows": summary_rows,
                "r1_parity_checks": r1_parity,
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
