from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_h4_d1_long_only_frequency_stress_probe as h4d1
import run_a1_opening_range_reversal_step4_probe as orrev
import run_a1_v7_v8_v11_v13_rr2_stretch_probe as rr2stretch
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    rel,
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_LH3_10_13_14_EXACT_REPLAY_PREREG_2026_07_05.md"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "HYBRID_LH_EXACT_202207_202606"
OUTPUT_STEM = "A1_XAU_HYBRID_LH3_10_13_14_EXACT_REPLAY_202207_202606"
BLOCKED_LONG_HOURS = (3, 10, 13, 14)

SPLIT_COMPONENT_PRIORITY = {
    "v6": 1,
    "weak": 2,
    "v13": 3,
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_dt(value: str) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def parse_money(value: Any) -> float:
    text = str(value or "0").replace(" ", "").strip()
    return float(text or "0")


def parse_hours(value: str) -> set[int]:
    hours: set[int] = set()
    for piece in str(value or "").split(","):
        piece = piece.strip()
        if not piece:
            continue
        hours.add(int(piece))
    return hours


def merge_hours(existing: str, extra: tuple[int, ...] = BLOCKED_LONG_HOURS) -> str:
    hours = parse_hours(existing)
    hours.update(extra)
    return ",".join(str(hour) for hour in sorted(hours))


def clone_with_lh(base: a1.Variant, name: str, label: str, run_id: str) -> a1.Variant:
    inputs = dict(base.tester_inputs)
    inputs["InpBlockedLongEntryHoursCsv"] = merge_hours(inputs.get("InpBlockedLongEntryHoursCsv", ""))
    return a1.Variant(
        name=name,
        label=f"{label}; blocked LONG hours {','.join(map(str, BLOCKED_LONG_HOURS))}",
        run_id=run_id,
        tester_inputs=inputs,
    )


def build_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    base_by_name = {variant.name: variant for variant in a1.VARIANTS}
    rr2_by_name = {variant.name: variant for variant in rr2stretch.build_variants()}
    h4_by_name = {variant.name: variant for variant in h4d1.VARIANTS}

    specs: list[tuple[str, a1.Variant, str, str, dict[str, Any]]] = []

    def add_split(base_name: str, short_name: str, cell_id: str, source_id: str, source_priority: int, stage: str) -> None:
        component = short_name.split("_")[1]
        specs.append(
            (
                short_name,
                base_by_name[base_name],
                f"BT_A1_XAU_HYBRID_LH_{short_name.upper()}",
                f"Step1 {cell_id} {component}",
                {
                    "loader": "split",
                    "cell_id": cell_id,
                    "source_id": source_id,
                    "family_group": "a1_core_management",
                    "source_priority": source_priority,
                    "component": component,
                    "component_priority": SPLIT_COMPONENT_PRIORITY[component],
                    "stage": stage,
                },
            )
        )

    add_split("goal_split_f67_r20_be_tp1_v6", "f67_v6_lh", "f67_r20_be_tp1", "step1_f67_r20_be_tp1", 12, "frequency")
    add_split("goal_split_f67_r20_be_tp1_weak", "f67_weak_lh", "f67_r20_be_tp1", "step1_f67_r20_be_tp1", 12, "frequency")
    add_split("goal_split_f67_r20_be_tp1_v13", "f67_v13_lh", "f67_r20_be_tp1", "step1_f67_r20_be_tp1", 12, "frequency")
    add_split("goal_split_f33_r30_be_never_v6", "f33_v6_lh", "f33_r30_be_never", "step1_f33_r30_be_never", 11, "hybrid")
    add_split("goal_split_f33_r30_be_never_weak", "f33_weak_lh", "f33_r30_be_never", "step1_f33_r30_be_never", 11, "hybrid")
    add_split("goal_split_f33_r30_be_never_v13", "f33_v13_lh", "f33_r30_be_never", "step1_f33_r30_be_never", 11, "hybrid")

    specs.extend(
        [
            (
                "v8_lh",
                rr2_by_name["v8_compress_h1_long_rr2p0"],
                "BT_A1_XAU_HYBRID_LH_V8",
                "V8 compression H1 long RR2",
                {
                    "loader": "trade",
                    "source_id": "v8_compress_h1_long_rr2p0",
                    "family_group": "rr2_trend_stretch",
                    "source_priority": 101,
                    "component": "v8_compress_h1_long_rr2p0",
                    "stage": "frequency",
                },
            ),
            (
                "orrev_london_lh",
                orrev.make_variant("london", "London server-hour 7", 7, 60, 5, "firm", "1.50"),
                "BT_A1_XAU_HYBRID_LH_ORREV_LONDON",
                "Opening-range reversal London firm stop15",
                {
                    "loader": "trade",
                    "source_id": "orrev_london_firm_stop15",
                    "family_group": "opening_range_reversal_exam",
                    "source_priority": 250,
                    "component": "orrev_london_firm_stop15",
                    "stage": "frequency",
                },
            ),
            (
                "h4_box2_lh",
                h4_by_name["long_box2_atr80_range150_body035"],
                "BT_A1_XAU_HYBRID_LH_H4_BOX2",
                "H4/D1 long box2 ATR80",
                {
                    "loader": "trade",
                    "source_id": "h4_d1_long_best_box2_atr80",
                    "family_group": "h4_d1_core_shape",
                    "source_priority": 80,
                    "component": "h4_d1_long_best_box2_atr80",
                    "stage": "hybrid",
                },
            ),
            (
                "h4_broad_lh",
                h4_by_name["long_broad_box3_atr60_range125_body035"],
                "BT_A1_XAU_HYBRID_LH_H4_BROAD",
                "H4/D1 long broad box3 ATR60",
                {
                    "loader": "trade",
                    "source_id": "h4_d1_long_broad_box3_atr60",
                    "family_group": "h4_d1_core_shape",
                    "source_priority": 81,
                    "component": "h4_d1_long_broad_box3_atr60",
                    "stage": "hybrid",
                },
            ),
        ]
    )

    variants: list[a1.Variant] = []
    metadata: dict[str, dict[str, Any]] = {}
    for short_name, base, run_id, label, meta in specs:
        variant = clone_with_lh(base, short_name, label, run_id)
        variants.append(variant)
        metadata[short_name] = {
            **meta,
            "variant_name": short_name,
            "base_label": base.label,
            "blocked_long_hours_csv": variant.tester_inputs.get("InpBlockedLongEntryHoursCsv", ""),
            "blocked_entry_hours_csv": variant.tester_inputs.get("InpBlockedEntryHoursCsv", ""),
        }
    return variants, metadata


def read_trade_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def grouped_split_signals(result: dict[str, Any], meta: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[tuple[int, dict[str, str]]]] = defaultdict(list)
    path = Path(result["trade_csv"])
    for ordinal, row in enumerate(read_trade_rows(path), start=2):
        grouped[(str(row["entry_time"]), str(row["direction"]).upper())].append((ordinal, row))

    signals: list[dict[str, Any]] = []
    for (entry_text, direction), trades in grouped.items():
        entry_time = parse_dt(entry_text)
        pnl = sum(parse_money(row.get("profit_aed")) for _ordinal, row in trades)
        lots = sum(float(row.get("volume") or 0.0) for _ordinal, row in trades)
        signals.append(
            {
                "source_id": meta["source_id"],
                "family_group": meta["family_group"],
                "source_priority": int(meta["source_priority"]),
                "entry_time": entry_time,
                "entry_date": entry_time.date(),
                "direction": direction,
                "pnl_usd": round(pnl, 2),
                "tickets": len(trades),
                "lots": round(lots, 4),
                "component": meta["component"],
                "component_priority": int(meta["component_priority"]),
                "cell_id": meta["cell_id"],
                "variant_name": meta["variant_name"],
                "source_csv": str(path),
                "source_row": min(ordinal for ordinal, _row in trades),
                "upstream_source_id": meta["source_id"],
            }
        )
    return signals


def trade_signals(result: dict[str, Any], meta: dict[str, Any]) -> list[dict[str, Any]]:
    path = Path(result["trade_csv"])
    signals: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_trade_rows(path), start=2):
        entry_time = parse_dt(str(row["entry_time"]))
        signals.append(
            {
                "source_id": meta["source_id"],
                "family_group": meta["family_group"],
                "source_priority": int(meta["source_priority"]),
                "entry_time": entry_time,
                "entry_date": entry_time.date(),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": parse_money(row.get("profit_aed")),
                "tickets": 1,
                "lots": float(row.get("volume") or 0.0),
                "component": meta["component"],
                "component_priority": 0,
                "cell_id": "",
                "variant_name": meta["variant_name"],
                "source_csv": str(path),
                "source_row": ordinal,
                "upstream_source_id": meta["source_id"],
            }
        )
    return signals


def dedupe_split_cell(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    by_direction: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_direction[row["direction"]].append(row)

    for direction_rows in by_direction.values():
        ordered = sorted(direction_rows, key=lambda item: item["entry_time"])
        index = 0
        while index < len(ordered):
            cluster = [ordered[index]]
            start = ordered[index]["entry_time"]
            index += 1
            while index < len(ordered) and (ordered[index]["entry_time"] - start).total_seconds() <= 240:
                cluster.append(ordered[index])
                index += 1
            winner = sorted(cluster, key=lambda item: (item["component_priority"], item["entry_time"], item["component"]))[0]
            kept.append(winner)
            for row in cluster:
                if row is winner:
                    continue
                blocked = dict(row)
                blocked["drop_reason"] = f"split_cell_priority_kept_{winner['component']}"
                blocked["duplicate_of_source_id"] = winner["source_id"]
                blocked["duplicate_of_entry_time"] = winner["entry_time"].isoformat(sep=" ")
                dropped.append(blocked)
    return (
        sorted(kept, key=lambda item: (item["entry_time"], item["component_priority"], item["component"])),
        sorted(dropped, key=lambda item: (item["entry_time"], item["component_priority"], item["component"])),
    )


def load_components(payload: dict[str, Any], metadata: dict[str, dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    raw_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    internal_dropped: list[dict[str, Any]] = []
    for result in payload["variants"]:
        meta = metadata[result["name"]]
        rows = grouped_split_signals(result, meta) if meta["loader"] == "split" else trade_signals(result, meta)
        raw_by_source[meta["source_id"]].extend(rows)

    components: dict[str, list[dict[str, Any]]] = {}
    for source_id, rows in raw_by_source.items():
        split_rows = [row for row in rows if row.get("cell_id")]
        if split_rows:
            kept, dropped = dedupe_split_cell(split_rows)
            components[source_id] = kept
            internal_dropped.extend(dropped)
        else:
            components[source_id] = sorted(rows, key=lambda item: (item["entry_time"], item["source_row"]))
    return components, internal_dropped


def as_frequency_frontier(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows, start=1):
        item = dict(row)
        item["upstream_source_id"] = row["source_id"]
        item["upstream_component"] = row.get("component", "")
        item["source_id"] = "freq_step3_frontier"
        item["family_group"] = "frequency_frontier"
        item["source_priority"] = 10
        item["component"] = "freq_step3_frontier"
        item["source_row"] = ordinal
        converted.append(item)
    return converted


def decision(metrics: dict[str, Any]) -> str:
    wr = float(metrics.get("win_rate_pct") or 0.0)
    wl = float(metrics.get("avg_win_loss") or 0.0)
    active = float(metrics.get("active_weekday_pct") or 0.0)
    net = float(metrics.get("net_usd") or 0.0)
    if net <= 0:
        return "EXACT_REJECT_NET"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "EXACT_OWNER_GOAL_HIT_REVIEW_REQUIRED"
    if wr >= 50.0 and wl >= 2.0 and active >= 85.0:
        return "EXACT_CORE_NEAR_ACTIVITY_REVIEW_CANDIDATE"
    if wr >= 50.0 and wl >= 1.95 and active >= 85.0:
        return "EXACT_NEAR_PAYOUT_NO_REVIEW"
    if wr >= 50.0 and wl < 2.0:
        return "EXACT_FAIL_WIN_LOSS"
    if wr < 50.0 and wl >= 2.0:
        return "EXACT_FAIL_WIN_RATE"
    return "EXACT_FAIL_OWNER_SHAPE"


def evaluate(components: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    frequency_raw: list[dict[str, Any]] = []
    for source_id in ("step1_f67_r20_be_tp1", "v8_compress_h1_long_rr2p0", "orrev_london_firm_stop15"):
        frequency_raw.extend(components.get(source_id, []))
    frequency_kept, frequency_dropped = dedupe_signals(frequency_raw)

    hybrid_raw = as_frequency_frontier(frequency_kept)
    for source_id in ("step1_f33_r30_be_never", "h4_d1_long_best_box2_atr80", "h4_d1_long_broad_box3_atr60"):
        hybrid_raw.extend(components.get(source_id, []))
    hybrid_kept, hybrid_dropped = dedupe_signals(hybrid_raw)

    metrics = summary_metrics(hybrid_kept, market_days=MARKET_DAYS)
    last12 = summary_metrics(
        [row for row in hybrid_kept if row["entry_date"] >= LAST12_START],
        market_days=LAST12_MARKET_DAYS,
    )
    stress_010 = summary_metrics(hybrid_kept, cost_per_ticket=0.10, market_days=MARKET_DAYS)
    stress_030 = summary_metrics(hybrid_kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    metrics.update(
        {
            "decision": decision(metrics),
            "frequency_raw_signals": len(frequency_raw),
            "frequency_kept_signals": len(frequency_kept),
            "frequency_dropped_signals": len(frequency_dropped),
            "hybrid_raw_signals": len(hybrid_raw),
            "hybrid_dropped_signals": len(hybrid_dropped),
            "last12_signals": last12["signals"],
            "last12_win_rate_pct": last12["win_rate_pct"],
            "last12_avg_win_loss": last12["avg_win_loss"],
            "last12_active_weekday_pct": last12["active_weekday_pct"],
            "last12_net_usd": last12["net_usd"],
            "stress_010_net_usd": stress_010["net_usd"],
            "stress_010_avg_win_loss": stress_010["avg_win_loss"],
            "stress_030_net_usd": stress_030["net_usd"],
            "stress_030_avg_win_loss": stress_030["avg_win_loss"],
        }
    )
    return {
        "metrics": metrics,
        "frequency_raw": frequency_raw,
        "frequency_kept": frequency_kept,
        "frequency_dropped": frequency_dropped,
        "hybrid_raw": hybrid_raw,
        "hybrid_kept": hybrid_kept,
        "hybrid_dropped": hybrid_dropped,
    }


def csv_safe(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for key in ("entry_time",):
        if isinstance(output.get(key), datetime):
            output[key] = output[key].strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(output.get("entry_date"), "isoformat"):
        output["entry_date"] = output["entry_date"].isoformat()
    return output


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
            writer.writerow(csv_safe(row))


def render(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# A1 XAU Hybrid LH3/10/13/14 Exact MT5 Replay",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester replay in isolated root plus manual signal-level portfolio composition. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"MT5 replay report: `{rel(Path(payload['mt5_report_md']))}`",
        "",
        "## Final Hybrid Metrics",
        "",
        "| Signals | WR% | W/L | Active% | PF | Net USD | Max DD | Last12 WR/WL/Active | Stress -0.30 W/L | Decision |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
        (
            f"| {metrics['signals']} | {metrics['win_rate_pct']} | {metrics['avg_win_loss']} | "
            f"{metrics['active_weekday_pct']} | {metrics['profit_factor']} | {metrics['net_usd']} | "
            f"{metrics['max_closed_drawdown_usd']} | {metrics['last12_win_rate_pct']}/"
            f"{metrics['last12_avg_win_loss']}/{metrics['last12_active_weekday_pct']} | "
            f"{metrics['stress_030_avg_win_loss']} | `{metrics['decision']}` |"
        ),
        "",
        "## Composition Counts",
        "",
        f"- Frequency raw/kept/dropped: `{metrics['frequency_raw_signals']}` / `{metrics['frequency_kept_signals']}` / `{metrics['frequency_dropped_signals']}`",
        f"- Hybrid raw/kept/dropped: `{metrics['hybrid_raw_signals']}` / `{metrics['signals']}` / `{metrics['hybrid_dropped_signals']}`",
        f"- Split internal dropped: `{payload['split_internal_dropped_signals']}`",
        "",
        "## Source Contributions",
        "",
        "| Source | Signals | Net USD |",
        "| --- | ---: | ---: |",
    ]
    for source_id, row in metrics.get("source_contributions", {}).items():
        lines.append(f"| `{source_id}` | {row['signals']} | {row['net_usd']} |")

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            payload["interpretation"],
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 replay for the best hybrid long-hour diagnostic.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    variants, metadata = build_variants()
    a1.VARIANTS = variants

    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_report_json = mt5_report_md.with_suffix(".json")
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

    components, split_internal_dropped = load_components(mt5_payload, metadata)
    evaluated = evaluate(components)
    metrics = evaluated["metrics"]
    status = metrics["decision"]
    if status == "EXACT_OWNER_GOAL_HIT_REVIEW_REQUIRED":
        interpretation = "Exact replay crossed all owner metrics. Freeze this package and spend the reviewer token before any demo-spec drafting."
    elif status == "EXACT_CORE_NEAR_ACTIVITY_REVIEW_CANDIDATE":
        interpretation = "Exact replay crossed WR and W/L with near-owner activity. This is review-worthy if the owner accepts that activity is still below 90%."
    elif status == "EXACT_NEAR_PAYOUT_NO_REVIEW":
        interpretation = "Exact replay stayed close but did not preserve W/L 2.0. Keep as frontier context; do not spend the reviewer token yet."
    else:
        interpretation = "Exact replay did not preserve the owner core shape. Do not spend reviewer tokens on this branch."

    outputs = {
        "frequency_raw_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_FREQUENCY_RAW.csv"),
        "frequency_kept_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_FREQUENCY_KEPT.csv"),
        "frequency_dropped_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_FREQUENCY_DROPPED.csv"),
        "hybrid_raw_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_HYBRID_RAW.csv"),
        "hybrid_kept_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_HYBRID_KEPT.csv"),
        "hybrid_dropped_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_HYBRID_DROPPED.csv"),
        "split_internal_dropped_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_SPLIT_INTERNAL_DROPPED.csv"),
        "json": str(REPORTS_DIR / f"{OUTPUT_STEM}.json"),
        "md": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"),
    }
    write_signal_csv(Path(outputs["frequency_raw_csv"]), evaluated["frequency_raw"])
    write_signal_csv(Path(outputs["frequency_kept_csv"]), evaluated["frequency_kept"])
    write_signal_csv(Path(outputs["frequency_dropped_csv"]), evaluated["frequency_dropped"])
    write_signal_csv(Path(outputs["hybrid_raw_csv"]), evaluated["hybrid_raw"])
    write_signal_csv(Path(outputs["hybrid_kept_csv"]), evaluated["hybrid_kept"])
    write_signal_csv(Path(outputs["hybrid_dropped_csv"]), evaluated["hybrid_dropped"])
    write_signal_csv(Path(outputs["split_internal_dropped_csv"]), split_internal_dropped)

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "period": f"{FROM_DATE} -> {TO_DATE}",
        "boundary": "exact_mt5_strategy_tester_replay_plus_manual_signal_level_composition",
        "blocked_long_hours": list(BLOCKED_LONG_HOURS),
        "mt5_report_md": str(mt5_report_md),
        "mt5_report_json": str(mt5_report_json),
        "variant_metadata": metadata,
        "component_counts": {source_id: len(rows) for source_id, rows in sorted(components.items())},
        "split_internal_dropped_signals": len(split_internal_dropped),
        "metrics": metrics,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    Path(outputs["json"]).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    Path(outputs["md"]).write_text(render(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "signals": metrics["signals"],
                "win_rate_pct": metrics["win_rate_pct"],
                "avg_win_loss": metrics["avg_win_loss"],
                "active_weekday_pct": metrics["active_weekday_pct"],
                "net_usd": metrics["net_usd"],
                "report": outputs["md"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
