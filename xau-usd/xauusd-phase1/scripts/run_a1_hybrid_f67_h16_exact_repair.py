from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_hybrid_lh3_10_13_14_exact_replay as base
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_PREREG_2026_07_05.md"
PREVIOUS_MT5_COMPONENTS = (
    REPORTS_DIR / "A1_XAU_HYBRID_LH3_10_13_14_EXACT_REPLAY_202207_202606_MT5_COMPONENTS.json"
)
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "HYBRID_F67_H16_EXACT_202207_202606"
OUTPUT_STEM = "A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606"
F67_NAMES = {"f67_v6_lh", "f67_weak_lh", "f67_v13_lh"}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def add_general_hour_16(variant: a1.Variant) -> a1.Variant:
    inputs = dict(variant.tester_inputs)
    inputs["InpBlockedEntryHoursCsv"] = base.merge_hours(inputs.get("InpBlockedEntryHoursCsv", ""), (16,))
    return a1.Variant(
        name=variant.name,
        label=f"{variant.label}; f67 repair blocks all directions at server hour 16",
        run_id=f"{variant.run_id}_F67_H16",
        tester_inputs=inputs,
    )


def build_repair_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    variants, metadata = base.build_variants()
    repair_variants = [add_general_hour_16(variant) for variant in variants if variant.name in F67_NAMES]
    for variant in repair_variants:
        metadata[variant.name]["blocked_entry_hours_csv"] = variant.tester_inputs.get("InpBlockedEntryHoursCsv", "")
        metadata[variant.name]["repair"] = "block_f67_all_directions_server_hour_16"
    return repair_variants, metadata


def combine_payloads(previous: dict[str, Any], rerun: dict[str, Any]) -> dict[str, Any]:
    replacement = {item["name"]: item for item in rerun["variants"]}
    combined = dict(previous)
    combined["variants"] = [replacement.get(item["name"], item) for item in previous["variants"]]
    combined["scope"] = dict(previous.get("scope", {}))
    combined["scope"]["repair"] = "f67_block_all_directions_server_hour_16"
    combined["scope"]["replayed_component_names"] = sorted(replacement)
    combined["scope"]["reused_component_names"] = [
        item["name"] for item in previous["variants"] if item["name"] not in replacement
    ]
    return combined


def render(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# A1 XAU Hybrid F67 Hour-16 Exact Repair",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester replay for the three changed f67 components plus manual signal-level composition with the unchanged exact component ledgers from the prior LH3/10/13/14 replay. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"F67 component MT5 replay report: `{rel(Path(payload['mt5_f67_report_md']))}`",
        f"Previous exact component report reused: `{rel(Path(payload['previous_mt5_components']))}`",
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
        f"- Replayed exact MT5 components: `{', '.join(payload['replayed_component_names'])}`",
        f"- Reused exact MT5 components: `{', '.join(payload['reused_component_names'])}`",
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
    lines.extend(["", "## Verdict", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 f67 hour-16 repair for the current hybrid frontier.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(PREVIOUS_MT5_COMPONENTS)
    previous = json.loads(PREVIOUS_MT5_COMPONENTS.read_text(encoding="utf-8"))
    repair_variants, metadata = build_repair_variants()
    a1.VARIANTS = repair_variants

    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_F67_COMPONENTS.md"
    mt5_report_json = mt5_report_md.with_suffix(".json")
    rerun_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )

    combined = combine_payloads(previous, rerun_payload)
    components, split_internal_dropped = base.load_components(combined, metadata)
    evaluated = base.evaluate(components)
    metrics = evaluated["metrics"]
    status = metrics["decision"]
    if status == "EXACT_OWNER_GOAL_HIT_REVIEW_REQUIRED":
        interpretation = "Exact repair crossed all owner metrics. Freeze this package and spend the reviewer token before demo-spec drafting."
    elif status == "EXACT_CORE_NEAR_ACTIVITY_REVIEW_CANDIDATE":
        interpretation = "Exact repair crossed WR and W/L while retaining near-owner activity. It is review-worthy only if the owner accepts the remaining activity gap below 90%."
    elif status == "EXACT_NEAR_PAYOUT_NO_REVIEW":
        interpretation = "Exact repair stayed close but did not preserve W/L 2.0. Keep as frontier context; do not spend the reviewer token."
    else:
        interpretation = "Exact repair did not preserve the owner core shape. Do not spend reviewer tokens on this branch."

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
    base.write_signal_csv(Path(outputs["frequency_raw_csv"]), evaluated["frequency_raw"])
    base.write_signal_csv(Path(outputs["frequency_kept_csv"]), evaluated["frequency_kept"])
    base.write_signal_csv(Path(outputs["frequency_dropped_csv"]), evaluated["frequency_dropped"])
    base.write_signal_csv(Path(outputs["hybrid_raw_csv"]), evaluated["hybrid_raw"])
    base.write_signal_csv(Path(outputs["hybrid_kept_csv"]), evaluated["hybrid_kept"])
    base.write_signal_csv(Path(outputs["hybrid_dropped_csv"]), evaluated["hybrid_dropped"])
    base.write_signal_csv(Path(outputs["split_internal_dropped_csv"]), split_internal_dropped)

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "period": f"{FROM_DATE} -> {TO_DATE}",
        "boundary": "exact_mt5_f67_component_replay_plus_manual_signal_level_composition",
        "repair": "block step1_f67_r20_be_tp1 all directions at server hour 16",
        "previous_mt5_components": str(PREVIOUS_MT5_COMPONENTS),
        "mt5_f67_report_md": str(mt5_report_md),
        "mt5_f67_report_json": str(mt5_report_json),
        "replayed_component_names": sorted(F67_NAMES),
        "reused_component_names": combined["scope"]["reused_component_names"],
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
