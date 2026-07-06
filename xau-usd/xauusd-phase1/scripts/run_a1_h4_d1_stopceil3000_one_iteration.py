from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_f67_h16_no_f33_composition import read_raw_rows
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    summary_metrics,
)
from run_a1_v9_v10_rr2_stretch_probe import last12_metrics, owner_metrics, read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_PREREG_2026_07_06.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
BASELINE_RAW = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606"
OUTPUT_STEM = "A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606"
REMOVED_SOURCE = "step1_f33_r30_be_never"
REPLACED_SOURCE = "h4_d1_long_best_box2_atr80"
NEW_SOURCE = "h4_d1_long_box2_atr80_stopceil3000"


VARIANTS = [
    a1.Variant(
        name="long_box2_atr80_range150_body035_stopceil3000",
        label="D1/H4 long-only best box2 ATR80 with 3000-point stop-ceiling filter",
        run_id="BT_A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION",
        tester_inputs={
            "InpSignalMode": "7",
            "InpDirectionMode": "1",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopCeilingPoints": "3000",
            "InpMaxTradesPerDay": "6",
            "InpCooldownMinutes": "0",
            "InpOnePositionPerMagic": "false",
            "InpMaxOpenPositionsPerMagic": "32",
            "InpD1CompressionAtrPercentileMax": "80.00",
            "InpD1CompressionBoxDays": "2",
            "InpD1CompressionRangeMedianMax": "1.50",
            "InpD1CompressionH4MinBodyFraction": "0.35",
        },
    )
]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_date(value: str) -> date:
    return date.fromisoformat(str(value).strip())


def read_composition_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle), start=2):
            entry_time = parse_dt(str(row["entry_time"]))
            rows.append(
                {
                    "component": row.get("component", ""),
                    "source_id": row.get("source_id", ""),
                    "upstream_source_id": row.get("upstream_source_id", ""),
                    "upstream_component": row.get("upstream_component", ""),
                    "family_group": row.get("family_group", ""),
                    "source_priority": int(row.get("source_priority") or 0),
                    "cell_id": row.get("cell_id", ""),
                    "component_priority": int(row.get("component_priority") or 0),
                    "variant_name": row.get("variant_name", ""),
                    "entry_time": entry_time,
                    "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                    "exit_time": row.get("exit_time", ""),
                    "direction": row.get("direction", ""),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(row.get("tickets") or 1),
                    "lots": float(row.get("lots") or 0.0),
                    "source_csv": row.get("source_csv", str(path)),
                    "source_row": int(row.get("source_row") or ordinal),
                }
            )
    return rows


def replacement_rows(trade_csv: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        rows.append(
            {
                "component": NEW_SOURCE,
                "source_id": NEW_SOURCE,
                "upstream_source_id": NEW_SOURCE,
                "upstream_component": "h4_d1_stopceil3000_one_iteration",
                "family_group": "h4_d1_core_shape",
                "source_priority": 80,
                "cell_id": "",
                "component_priority": 0,
                "variant_name": "h4_box2_stopceil3000",
                "entry_time": entry_time,
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "exit_time": row.get("exit_time", ""),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": float(row.get("profit_float") or 0.0),
                "tickets": 1,
                "lots": float(row.get("volume") or 0.0),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def write_signal_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "component",
        "source_id",
        "upstream_source_id",
        "upstream_component",
        "family_group",
        "source_priority",
        "cell_id",
        "component_priority",
        "variant_name",
        "entry_time",
        "entry_date",
        "exit_time",
        "direction",
        "pnl_usd",
        "tickets",
        "lots",
        "source_csv",
        "source_row",
        "drop_reason",
        "duplicate_of_source_id",
        "duplicate_of_entry_time",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            if isinstance(out.get("entry_time"), datetime):
                out["entry_time"] = out["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(out.get("entry_date"), "isoformat"):
                out["entry_date"] = out["entry_date"].isoformat()
            writer.writerow(out)


def remove_sources(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    kept: list[dict[str, Any]] = []
    counts = {"removed_f33": 0, "removed_replaced_h4": 0}
    for row in raw:
        source = row.get("source_id", "")
        upstream = row.get("upstream_source_id", "")
        if source == REMOVED_SOURCE or upstream == REMOVED_SOURCE:
            counts["removed_f33"] += 1
            continue
        if source == REPLACED_SOURCE or upstream == REPLACED_SOURCE:
            counts["removed_replaced_h4"] += 1
            continue
        kept.append(row)
    return kept, counts


def weekly_monthly_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_week: dict[tuple[int, int], float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    for row in rows:
        entry_date = row["entry_date"]
        pnl = float(row["pnl_usd"])
        iso = entry_date.isocalendar()
        by_week[(iso.year, iso.week)] += pnl
        by_month[entry_date.strftime("%Y-%m")] += pnl

    weeks = sorted(by_week)
    positive_weeks = sum(1 for key in weeks if by_week[key] > 0)
    rolling_positive = 0
    rolling_total = 0
    for idx in range(len(weeks) - 3):
        value = sum(by_week[weeks[j]] for j in range(idx, idx + 4))
        rolling_total += 1
        if value > 0:
            rolling_positive += 1

    months = sorted(by_month)
    june_2026 = by_month.get("2026-06", 0.0)
    return {
        "trade_weeks": len(weeks),
        "positive_weeks": positive_weeks,
        "positive_week_pct": round(100.0 * positive_weeks / len(weeks), 2) if weeks else 0.0,
        "worst_week_usd": round(min(by_week.values(), default=0.0), 2),
        "best_week_usd": round(max(by_week.values(), default=0.0), 2),
        "rolling_4_week_positive_pct": round(100.0 * rolling_positive / rolling_total, 2) if rolling_total else 0.0,
        "months": len(months),
        "positive_months": sum(1 for key in months if by_month[key] > 0),
        "positive_month_pct": round(100.0 * sum(1 for key in months if by_month[key] > 0) / len(months), 2)
        if months
        else 0.0,
        "worst_month_usd": round(min(by_month.values(), default=0.0), 2),
        "best_month_usd": round(max(by_month.values(), default=0.0), 2),
        "june_2026_net_usd": round(june_2026, 2),
    }


def remove_top_winners(rows: list[dict[str, Any]], pct: float) -> dict[str, Any]:
    wins = sorted((row for row in rows if float(row["pnl_usd"]) > 0), key=lambda row: float(row["pnl_usd"]), reverse=True)
    remove_count = math.ceil(len(wins) * pct)
    remove_ids = {id(row) for row in wins[:remove_count]}
    kept = [row for row in rows if id(row) not in remove_ids]
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    return {
        "removed_winners": remove_count,
        "signals": metrics["signals"],
        "win_rate_pct": metrics["win_rate_pct"],
        "avg_win_loss": metrics["avg_win_loss"],
        "profit_factor": metrics["profit_factor"],
        "net_usd": metrics["net_usd"],
    }


def composition_decision(metrics: dict[str, Any], shape: dict[str, Any]) -> str:
    wl = metrics.get("avg_win_loss") or 0.0
    if metrics["win_rate_pct"] >= 50.0 and wl >= 2.0 and metrics["active_weekday_pct"] >= 90.0:
        return "OWNER_GOAL_HIT_REVIEW_REQUIRED"
    if metrics["win_rate_pct"] >= 50.0 and wl >= 2.0 and shape["worst_week_usd"] >= -300.0:
        return "CORE_SHAPE_WITH_WEEKLY_REPAIR_NEEDS_FREQUENCY"
    if metrics["win_rate_pct"] >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_ACTIVITY_GAP_WEEKLY_NOT_FIXED"
    return "REJECT_BREAKS_CORE_SHAPE"


def metric_line(name: str, metrics: dict[str, Any], shape: dict[str, Any], decision: str) -> str:
    return (
        f"| `{name}` | {metrics['signals']} | {metrics['win_rate_pct']:.2f} | "
        f"{(metrics.get('avg_win_loss') or 0.0):.4f} | {metrics['active_weekday_pct']:.2f} | "
        f"{(metrics.get('profit_factor') or 0.0):.4f} | {metrics['net_usd']:.2f} | "
        f"{metrics['max_closed_drawdown_usd']:.2f} | {shape['positive_week_pct']:.2f} | "
        f"{shape['worst_week_usd']:.2f} | {shape['positive_month_pct']:.2f} | "
        f"{shape['worst_month_usd']:.2f} | {shape['june_2026_net_usd']:.2f} | `{decision}` |"
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4/D1 Stop-Ceiling One Iteration",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: one exact-MT5 Strategy Tester run in the isolated backtest root, followed by exact-ledger recomposition. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        "",
        "## Standalone MT5 Component",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Net USD | Max DD | Last12 WR/WL/Active |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    standalone = payload["standalone"]
    last12 = payload["standalone_last12"]
    lines.append(
        f"| `{standalone['variant']}` | {standalone['trades']} | {standalone['win_rate_pct']:.2f} | "
        f"{standalone['avg_win_loss_ratio'] or 0.0:.4f} | {standalone['active_day_pct']:.2f} | "
        f"{standalone['profit_factor'] or 0.0:.4f} | {standalone['manual_pnl']:.2f} | "
        f"{standalone['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/"
        f"{last12['avg_win_loss_ratio'] or 0.0:.4f}/{last12['active_day_pct']:.2f} |"
    )

    lines.extend(
        [
            "",
            "## Recomposed Hybrid",
            "",
            "| Book | Signals | WR% | W/L | Active% | PF | Net USD | Max DD | Positive weeks% | Worst week | Positive months% | Worst month | June 2026 | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            metric_line(
                "baseline_f67_h16_no_f33",
                payload["baseline_metrics"],
                payload["baseline_shape"],
                payload["baseline_decision"],
            ),
            metric_line(
                "replace_h4_best_with_stopceil3000",
                payload["replacement_metrics"],
                payload["replacement_shape"],
                payload["replacement_decision"],
            ),
            "",
            "## Tail Reliance",
            "",
            "| Book | Ex-top-1% removed | Ex-top-1% W/L | Ex-top-1% PF | Ex-top-1% net | Ex-top-2% removed | Ex-top-2% W/L | Ex-top-2% PF | Ex-top-2% net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, prefix in [("baseline", "baseline"), ("replacement", "replacement")]:
        one = payload[f"{prefix}_ex_top_1pct"]
        two = payload[f"{prefix}_ex_top_2pct"]
        lines.append(
            f"| `{name}` | {one['removed_winners']} | {one['avg_win_loss'] or 0.0:.4f} | "
            f"{one['profit_factor'] or 0.0:.4f} | {one['net_usd']:.2f} | {two['removed_winners']} | "
            f"{two['avg_win_loss'] or 0.0:.4f} | {two['profit_factor'] or 0.0:.4f} | {two['net_usd']:.2f} |"
        )

    lines.extend(["", "## Verdict", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one exact-MT5 H4/D1 stop-ceiling iteration.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(BASELINE_KEPT)
    require_file(BASELINE_RAW)

    a1.VARIANTS = VARIANTS
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )
    result = mt5_payload["variants"][0]
    trade_csv = Path(result["trade_csv"])
    mt5_rows = read_trade_csv(trade_csv)
    standalone_metrics = owner_metrics(mt5_rows, FROM_DATE, TO_DATE)
    standalone_metrics["variant"] = result["name"]
    standalone_last12 = last12_metrics(mt5_rows, TO_DATE)

    baseline_rows = read_composition_csv(BASELINE_KEPT)
    baseline_metrics = summary_metrics(baseline_rows, market_days=MARKET_DAYS)
    baseline_last12 = summary_metrics(
        [row for row in baseline_rows if row["entry_date"] >= LAST12_START],
        market_days=LAST12_MARKET_DAYS,
    )
    baseline_metrics.update(
        {
            "last12_win_rate_pct": baseline_last12["win_rate_pct"],
            "last12_avg_win_loss": baseline_last12["avg_win_loss"],
            "last12_active_weekday_pct": baseline_last12["active_weekday_pct"],
        }
    )
    baseline_shape = weekly_monthly_shape(baseline_rows)

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_sources(raw)
    replacement_raw = filtered_raw + replacement_rows(trade_csv)
    replacement_kept, replacement_dropped = dedupe_signals(replacement_raw)
    replacement_metrics = summary_metrics(replacement_kept, market_days=MARKET_DAYS)
    replacement_last12 = summary_metrics(
        [row for row in replacement_kept if row["entry_date"] >= LAST12_START],
        market_days=LAST12_MARKET_DAYS,
    )
    replacement_metrics.update(
        {
            "last12_win_rate_pct": replacement_last12["win_rate_pct"],
            "last12_avg_win_loss": replacement_last12["avg_win_loss"],
            "last12_active_weekday_pct": replacement_last12["active_weekday_pct"],
        }
    )
    replacement_shape = weekly_monthly_shape(replacement_kept)

    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "replacement_kept_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_REPLACEMENT_KEPT.csv"),
        "replacement_dropped_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_REPLACEMENT_DROPPED.csv"),
        "mt5_trade_csv": str(trade_csv),
        "mt5_html_report": result["html_report"],
    }
    write_signal_csv(Path(outputs["replacement_kept_csv"]), replacement_kept)
    write_signal_csv(Path(outputs["replacement_dropped_csv"]), replacement_dropped)

    replacement_decision = composition_decision(replacement_metrics, replacement_shape)
    baseline_decision = composition_decision(baseline_metrics, baseline_shape)
    if replacement_decision == "CORE_SHAPE_WITH_WEEKLY_REPAIR_NEEDS_FREQUENCY":
        status = "USEFUL_RISK_SHAPE_CLUE_NOT_DEMO_READY"
        interpretation = (
            "The stop-ceiling replacement kept the core WR/W-L shape and improved the weekly loss shape enough to keep this risk-shape direction alive, "
            "but it still needs frequency/robustness work before demo review."
        )
    elif replacement_decision == "CORE_SHAPE_ACTIVITY_GAP_WEEKLY_NOT_FIXED":
        status = "CORE_SHAPE_SURVIVES_WEEKLY_NOT_FIXED"
        interpretation = (
            "The replacement preserved WR/W-L but did not materially fix the weekly loss-shape blocker. Do not spend the reviewer token on this single cell."
        )
    else:
        status = "REJECT_STOPCEIL3000_BREAKS_OR_FAILS_FRONTIER"
        interpretation = (
            "The replacement did not improve the current frontier enough. This argues against simple stop-ceiling filtering as the fast path; the next useful move is a true stop/risk geometry edit, not more ceiling filters."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "mt5_scope": mt5_payload["scope"],
        "standalone": standalone_metrics,
        "standalone_last12": standalone_last12,
        "baseline_metrics": baseline_metrics,
        "baseline_shape": baseline_shape,
        "baseline_decision": baseline_decision,
        "baseline_ex_top_1pct": remove_top_winners(baseline_rows, 0.01),
        "baseline_ex_top_2pct": remove_top_winners(baseline_rows, 0.02),
        "replacement_metrics": replacement_metrics,
        "replacement_shape": replacement_shape,
        "replacement_decision": replacement_decision,
        "replacement_ex_top_1pct": remove_top_winners(replacement_kept, 0.01),
        "replacement_ex_top_2pct": remove_top_winners(replacement_kept, 0.02),
        "removal_counts": removal_counts,
        "replacement_raw_rows": len(replacement_raw),
        "replacement_kept_rows": len(replacement_kept),
        "replacement_dropped_rows": len(replacement_dropped),
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "standalone": standalone_metrics,
                "replacement": {
                    "signals": replacement_metrics["signals"],
                    "wr": replacement_metrics["win_rate_pct"],
                    "wl": replacement_metrics["avg_win_loss"],
                    "active": replacement_metrics["active_weekday_pct"],
                    "net": replacement_metrics["net_usd"],
                    "positive_week_pct": replacement_shape["positive_week_pct"],
                    "worst_week": replacement_shape["worst_week_usd"],
                    "june_2026": replacement_shape["june_2026_net_usd"],
                    "decision": replacement_decision,
                },
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
