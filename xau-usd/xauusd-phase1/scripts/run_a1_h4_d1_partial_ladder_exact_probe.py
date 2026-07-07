from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_f67_h16_no_f33_composition import read_raw_rows
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    summary_metrics,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    BASELINE_KEPT,
    BASELINE_RAW,
    FROM_DATE,
    REPLACED_SOURCE,
    REMOVED_SOURCE,
    TO_DATE,
    decision_for,
    parse_date,
    read_composition_csv,
    remove_sources,
    remove_top_winners,
    result_row,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_PARTIAL_LADDER_EXACT_PROBE_PREREG_2026_07_06.md"
OUTPUT_STEM = "A1_XAU_H4_D1_PARTIAL_LADDER_EXACT_PROBE_202207_202606"
TAG = "OWNER_GOAL_H4_D1_PARTIAL_LADDER_202207_202606"


BASE_H4_INPUTS = {
    "InpSignalMode": "7",
    "InpDirectionMode": "1",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.15",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
    "InpMaxTradesPerDay": "6",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "false",
    "InpMaxOpenPositionsPerMagic": "32",
    "InpD1CompressionAtrPercentileMax": "80.00",
    "InpD1CompressionBoxDays": "2",
    "InpD1CompressionRangeMedianMax": "1.50",
    "InpD1CompressionH4MinBodyFraction": "0.35",
}


LADDER_SPECS = {
    "p33_t2_run4_be": {
        "lots": "0.03",
        "normalizer": 3.0,
        "fraction": "0.34",
        "trigger": "2.00",
        "runner": "4.00",
        "be": "true",
    },
    "p33_t2_run4_nobe": {
        "lots": "0.03",
        "normalizer": 3.0,
        "fraction": "0.34",
        "trigger": "2.00",
        "runner": "4.00",
        "be": "false",
    },
    "p50_t3_run6_be": {
        "lots": "0.02",
        "normalizer": 2.0,
        "fraction": "0.50",
        "trigger": "3.00",
        "runner": "6.00",
        "be": "true",
    },
    "p50_t3_run6_nobe": {
        "lots": "0.02",
        "normalizer": 2.0,
        "fraction": "0.50",
        "trigger": "3.00",
        "runner": "6.00",
        "be": "false",
    },
}


def ladder_variant(name: str, spec: dict[str, Any]) -> a1.Variant:
    return a1.Variant(
        name=name,
        label=(
            f"H4/D1 partial ladder {name}: lot {spec['lots']}, "
            f"bank fraction {spec['fraction']} at {spec['trigger']}R, runner {spec['runner']}R, "
            f"BE after partial={spec['be']}"
        ),
        run_id=f"BT_A1_XAU_H4_D1_LADDER_{name.upper()}",
        tester_inputs={
            **BASE_H4_INPUTS,
            "InpFixedLots": spec["lots"],
            "InpMaxRiskLots": spec["lots"],
            "InpPartialCloseEnabled": "true",
            "InpPartialCloseShadowOnly": "false",
            "InpPartialFraction": spec["fraction"],
            "InpPartialTriggerR": spec["trigger"],
            "InpRunnerTargetR": spec["runner"],
            "InpMoveSLToBEOnPartial": spec["be"],
        },
    )


VARIANTS = [ladder_variant(name, spec) for name, spec in LADDER_SPECS.items()]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def read_deal_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if rows and len(rows[0]) == 1:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    return rows


def parse_money(value: str) -> float:
    return float((value or "0").replace(" ", ""))


def parse_deal_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def normalized_ladder_signals(deal_csv: Path, variant_name: str, normalizer: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_position: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_deal_rows(deal_csv):
        position_id = str(row.get("position_id", "")).strip()
        if position_id:
            by_position[position_id].append(row)

    signals: list[dict[str, Any]] = []
    failures: list[str] = []
    open_positions_ignored: list[str] = []
    partial_open_positions_ignored: list[str] = []
    for position_id, rows in sorted(by_position.items(), key=lambda item: min(parse_deal_time(row["timestamp_broker"]) for row in item[1])):
        rows = sorted(rows, key=lambda row: parse_deal_time(row["timestamp_broker"]))
        entries = [row for row in rows if str(row.get("entry_code", "")) == "0"]
        exits = [row for row in rows if str(row.get("entry_code", "")) in {"1", "3"}]
        if len(entries) != 1:
            failures.append(position_id)
            continue

        entry = entries[0]
        entry_time = parse_deal_time(entry["timestamp_broker"])
        initial_volume = parse_money(entry.get("volume", "0"))
        if not exits:
            open_positions_ignored.append(position_id)
            continue
        exit_volume = sum(parse_money(row.get("volume", "0")) for row in exits)
        if exit_volume + 0.0001 < initial_volume:
            partial_open_positions_ignored.append(position_id)
            continue
        if exit_volume - initial_volume > 0.0001:
            failures.append(position_id)
            continue

        exit_time = max(parse_deal_time(row["timestamp_broker"]) for row in exits)
        raw_pnl = sum(
            parse_money(row.get("profit", "0"))
            + parse_money(row.get("commission", "0"))
            + parse_money(row.get("swap", "0"))
            for row in exits
        )
        normalized_pnl = raw_pnl / normalizer
        signals.append(
            {
                "component": f"h4_d1_partial_ladder_{variant_name}",
                "source_id": f"h4_d1_partial_ladder_{variant_name}",
                "upstream_source_id": f"h4_d1_partial_ladder_{variant_name}",
                "upstream_component": "h4_d1_partial_ladder_exact_probe",
                "family_group": "h4_d1_core_shape",
                "source_priority": 80,
                "cell_id": variant_name,
                "component_priority": 0,
                "variant_name": variant_name,
                "entry_time": entry_time,
                "entry_date": entry_time.date(),
                "exit_time": exit_time,
                "direction": str(entry.get("direction", "")).upper(),
                "pnl_usd": normalized_pnl,
                "tickets": 1,
                "lots": initial_volume / normalizer,
                "source_csv": str(deal_csv),
                "source_row": int(entry.get("deal_ticket") or 0),
                "position_id": position_id,
                "raw_pnl_usd": raw_pnl,
                "normalizer": normalizer,
                "exit_parts": len(exits),
            }
        )

    return signals, {
        "deal_csv": str(deal_csv),
        "positions": len(by_position),
        "signals": len(signals),
        "failed_positions": len(failures),
        "failed_position_ids": failures[:20],
        "open_positions_ignored": len(open_positions_ignored),
        "open_position_ids_ignored": open_positions_ignored[:20],
        "partial_open_positions_ignored": len(partial_open_positions_ignored),
        "partial_open_position_ids_ignored": partial_open_positions_ignored[:20],
    }


def write_ladder_signal_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "entry_time",
        "exit_time",
        "entry_date",
        "direction",
        "pnl_usd",
        "raw_pnl_usd",
        "normalizer",
        "lots",
        "position_id",
        "exit_parts",
        "source_csv",
        "source_row",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["entry_time"] = out["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
            out["exit_time"] = out["exit_time"].strftime("%Y-%m-%d %H:%M:%S")
            out["entry_date"] = out["entry_date"].isoformat()
            writer.writerow(out)


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4/D1 Partial-Ladder Exact Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: four preregistered exact-MT5 H4/D1 partial-ladder cells in isolated Strategy Tester root, recomposed into the current best hybrid. Signal P&L is reconstructed from the EA deal log by `DEAL_POSITION_ID` and normalized back to baseline `0.01` exposure. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Baseline",
        "",
        "| Signals | WR% | W/L | Active% | PF | Net | DD | Stress -0.30 W/L | Positive weeks% | Worst week | Rolling 4w+% | June 2026 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    base = payload["baseline_row"]
    lines.append(
        f"| {base['signals']} | {base['wr']:.2f} | {base['wl'] or 0.0:.4f} | {base['active']:.2f} | "
        f"{base['pf'] or 0.0:.4f} | {base['net']:.2f} | {base['dd']:.2f} | {base['stress_030_wl'] or 0.0:.4f} | "
        f"{base['positive_week_pct']:.2f} | {base['worst_week']:.2f} | {base['rolling4_positive_pct']:.2f} | {base['june_2026']:.2f} |"
    )
    lines.extend(
        [
            "",
            "## Recomposed Cells",
            "",
            "| Variant | Signals | WR% | W/L | Active% | PF | Net | DD | Stress -0.30 W/L | Positive weeks% | Worst week | Rolling 4w+% | June 2026 | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["result_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['dd']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | {row['worst_week']:.2f} | "
            f"{row['rolling4_positive_pct']:.2f} | {row['june_2026']:.2f} | `{row['decision']}` |"
        )
    lines.extend(["", "## Deal Reconstruction", ""])
    for item in payload["parse_stats"]:
        lines.append(
            f"- `{item['variant']}`: positions `{item['positions']}`, normalized closed signals `{item['signals']}`, "
            f"open-at-end ignored `{item['open_positions_ignored']}`, partial-open ignored `{item['partial_open_positions_ignored']}`, "
            f"failed positions `{item['failed_positions']}`."
        )
    lines.extend(
        [
            "",
            "## Tail Reliance",
            "",
            "| Variant | Ex-top-1 removed | Ex-top-1 W/L | Ex-top-1 PF | Ex-top-1 net | Ex-top-2 removed | Ex-top-2 W/L | Ex-top-2 PF | Ex-top-2 net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["tail_rows"]:
        one = item["ex_top_1pct"]
        two = item["ex_top_2pct"]
        lines.append(
            f"| `{item['variant']}` | {one['removed_winners']} | {one['avg_win_loss'] or 0.0:.4f} | "
            f"{one['profit_factor'] or 0.0:.4f} | {one['net_usd']:.2f} | {two['removed_winners']} | "
            f"{two['avg_win_loss'] or 0.0:.4f} | {two['profit_factor'] or 0.0:.4f} | {two['net_usd']:.2f} |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4/D1 partial-ladder owner-goal probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    for path in (PREREG, BASELINE_KEPT, BASELINE_RAW):
        require_file(path)

    a1.VARIANTS = VARIANTS
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_VARIANTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_VARIANTS.json"
    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )

    baseline_rows = read_composition_csv(BASELINE_KEPT)
    baseline_metrics = summary_metrics(baseline_rows, market_days=MARKET_DAYS)
    baseline_stress_030 = summary_metrics(baseline_rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    baseline_shape = weekly_exit_shape(baseline_rows)
    baseline_row = result_row("baseline_f67_h16_no_f33", baseline_metrics, baseline_stress_030, baseline_shape, "BASELINE")

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_sources(raw)
    result_rows: list[dict[str, Any]] = []
    tail_rows: list[dict[str, Any]] = []
    parse_stats: list[dict[str, Any]] = []
    variant_details: list[dict[str, Any]] = []
    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "results_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"),
        "mt5_variants_md": str(mt5_report_md),
        "mt5_variants_json": str(mt5_report_json),
    }

    for result in mt5_payload["variants"]:
        variant_name = result["name"]
        spec = LADDER_SPECS[variant_name]
        deal_csv = Path(result["deal_csv"])
        ladder_rows, stats = normalized_ladder_signals(deal_csv, variant_name, float(spec["normalizer"]))
        stats["variant"] = variant_name
        parse_stats.append(stats)
        if stats["failed_positions"]:
            raise RuntimeError(f"Deal reconstruction failed for {variant_name}: {stats}")

        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_NORMALIZED_H4D1_SIGNALS.csv"
        for source_row, row in enumerate(ladder_rows, start=2):
            row["source_csv"] = str(normalized_csv)
            row["source_row"] = source_row
        write_ladder_signal_csv(normalized_csv, ladder_rows)
        outputs[f"{variant_name}_normalized_h4d1_csv"] = str(normalized_csv)

        replacement_raw = filtered_raw + ladder_rows
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
        stress_030 = summary_metrics(replacement_kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
        replacement_shape = weekly_exit_shape(replacement_kept)
        decision = decision_for(replacement_metrics, stress_030, replacement_shape, baseline_shape)
        if (
            decision == "WEEKLY_SHAPE_CLUE_NOT_DEMO_READY"
            and replacement_metrics["active_weekday_pct"] >= 90.0
            and replacement_shape["positive_week_pct"] >= 90.0
        ):
            decision = "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"
        result_rows.append(result_row(variant_name, replacement_metrics, stress_030, replacement_shape, decision))
        tail_rows.append(
            {
                "variant": variant_name,
                "ex_top_1pct": remove_top_winners(replacement_kept, 0.01),
                "ex_top_2pct": remove_top_winners(replacement_kept, 0.02),
            }
        )

        enriched_kept, kept_exit_stats = enrich_exit_times(replacement_kept)
        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_DROPPED.csv"
        write_signal_csv(kept_csv, enriched_kept)
        write_signal_csv(dropped_csv, replacement_dropped)
        outputs[f"{variant_name}_kept_csv"] = str(kept_csv)
        outputs[f"{variant_name}_dropped_csv"] = str(dropped_csv)

        standalone_metrics = summary_metrics(ladder_rows, market_days=MARKET_DAYS)
        variant_details.append(
            {
                "variant": variant_name,
                "spec": spec,
                "mt5_result": result,
                "parse_stats": stats,
                "standalone_metrics": standalone_metrics,
                "replacement_metrics": replacement_metrics,
                "replacement_stress_030": stress_030,
                "replacement_shape": replacement_shape,
                "replacement_decision": decision,
                "replacement_raw_rows": len(replacement_raw),
                "replacement_kept_rows": len(replacement_kept),
                "replacement_dropped_rows": len(replacement_dropped),
                "kept_exit_match_stats": kept_exit_stats,
                "normalized_h4d1_csv": str(normalized_csv),
                "kept_csv": str(kept_csv),
                "dropped_csv": str(dropped_csv),
            }
        )

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        keys = list(result_rows[0].keys()) if result_rows else []
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(result_rows)

    owner_hits = [row for row in result_rows if row["decision"] == "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"]
    useful = [row for row in result_rows if row["decision"] == "WEEKLY_SHAPE_CLUE_NOT_DEMO_READY"]
    if owner_hits:
        status = "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"
        best = max(owner_hits, key=lambda row: (row["positive_week_pct"], row["net"]))
        interpretation = f"`{best['variant']}` reached the preregistered owner weekly gate. It requires independent review before any demo spec."
    elif useful:
        status = "USEFUL_WEEKLY_SHAPE_CLUE_NOT_DEMO_READY"
        best = max(useful, key=lambda row: (row["positive_week_pct"], row["worst_week"], row["net"]))
        interpretation = f"`{best['variant']}` improved weekly shape while preserving core/stress gates, but did not reach 90% positive weeks."
    else:
        status = "NO_PARTIAL_LADDER_SURVIVOR"
        best = max(result_rows, key=lambda row: (row["positive_week_pct"], row["worst_week"], row["wl"] or 0.0))
        interpretation = (
            "No preregistered partial-ladder cell preserved the full owner shape. "
            f"Best raw weekly row was `{best['variant']}` with positive weeks {best['positive_week_pct']}%, "
            f"worst week {best['worst_week']}, WR {best['wr']}%, W/L {best['wl']}."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "replaced_source": REPLACED_SOURCE,
        "removed_source": REMOVED_SOURCE,
        "removal_counts": removal_counts,
        "baseline_metrics": baseline_metrics,
        "baseline_stress_030": baseline_stress_030,
        "baseline_shape": baseline_shape,
        "baseline_row": baseline_row,
        "baseline_ex_top_1pct": remove_top_winners(baseline_rows, 0.01),
        "baseline_ex_top_2pct": remove_top_winners(baseline_rows, 0.02),
        "result_rows": result_rows,
        "tail_rows": tail_rows,
        "parse_stats": parse_stats,
        "variant_details": variant_details,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": baseline_row,
                "best_by_weekly": max(result_rows, key=lambda row: (row["positive_week_pct"], row["worst_week"], row["wl"] or 0.0)),
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
