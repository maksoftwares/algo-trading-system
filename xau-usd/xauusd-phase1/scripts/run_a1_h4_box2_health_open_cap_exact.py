from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import BASELINE_RAW, FROM_DATE, TO_DATE, write_signal_csv
from run_a1_h4_d1_review_repair_exact import (
    BASE_H4_INPUTS,
    COMPONENTS,
    guard_counts,
    read_raw_rows,
    remove_f33_and_h4_sources,
    replacement_rows,
    require_file,
    sha256_file,
    source_contributions,
)
from run_a1_h4_previous_month_health_gate_exact import short_v2_raw_rows


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_BOX2_HEALTH_OPEN_CAP_EXACT_PREREG_2026_07_08.md"
BASE_CANDIDATE_KEPT = REPORTS_DIR / "A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_broad_quarantined_KEPT.csv"


def output_stem(cap: int) -> str:
    return f"A1_XAU_H4_BOX2_HEALTH_OPEN_CAP{cap}_EXACT_202207_202606"


def tag(cap: int) -> str:
    return f"OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP{cap}_EXACT_202207_202606"


def build_variant(cap: int) -> tuple[a1.Variant, dict[str, Any]]:
    component = COMPONENTS["box2"]
    inputs = {
        **BASE_H4_INPUTS,
        **component["inputs"],
        "InpOnePositionPerMagic": "false",
        "InpMaxOpenPositionsPerMagic": str(cap),
        "InpH4D1SupportiveStateGuardEnabled": "true",
        "InpH4D1SupportiveEmaPeriod": "20",
        "InpH4D1SupportiveSlopeLagBars": "5",
        "InpH4D1PrevMonthHealthGateEnabled": "true",
        "InpH4D1PrevMonthNetMinUsd": "-50.00",
        "InpH4D1WeeklyLossGovernorEnabled": "false",
    }
    variant = a1.Variant(
        name=f"prevhealth_box2_open_cap{cap}",
        label=f"H4/D1 box2 supportive + previous-month health gate + max {cap} open positions",
        run_id=f"BT_A1_XAU_H4_BOX2_HEALTH_OPEN_CAP{cap}",
        tester_inputs=inputs,
    )
    metadata = {
        "probe": f"prevhealth_open_cap{cap}",
        "component_key": "box2",
        "source_id": component["source_id"],
        "source_priority": component["source_priority"],
        "family_group": "h4_d1_core_shape",
        "label": variant.label,
    }
    return variant, metadata


def evaluate(name: str, rows: list[dict[str, Any]], dropped: list[dict[str, Any]], baseline: dict[str, Any] | None) -> dict[str, Any]:
    enriched, exit_stats = enrich_exit_times(rows)
    metrics = summary_metrics(enriched, market_days=MARKET_DAYS)
    stress = summary_metrics(enriched, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    months = month_shape(enriched)
    weeks = weekly_shape(enriched)
    row = {
        "name": name,
        "signals": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_net": stress["net_usd"],
        "active_weekday_pct": metrics["active_weekday_pct"],
        "max_closed_dd": max_closed_drawdown(enriched),
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        "blocked_signals": len(dropped),
        "exit_stats": exit_stats,
        "kept_rows": enriched,
        "dropped_rows": dropped,
        **months,
    }
    row["decision"] = "BASELINE" if baseline is None else decide(row, baseline)
    return row


def decide(row: dict[str, Any], baseline: dict[str, Any]) -> str:
    wl = row.get("wl") or 0.0
    stress_wl = row.get("stress_030_wl") or 0.0
    worst_week_target = baseline["worst_week"] * 0.80
    core_ok = (
        row["positive_months"] >= 31
        and row["net"] >= 19000.0
        and row["wr"] >= 48.0
        and wl >= 2.0
        and stress_wl >= 1.90
        and row["active_weekday_pct"] >= 84.0
    )
    risk_ok = (
        row["max_closed_dd"] <= baseline["max_closed_dd"]
        and row["worst_week"] >= worst_week_target
        and row["worst_month_net"] >= baseline["worst_month_net"]
    )
    if core_ok and risk_ok:
        return "H4_BOX2_OPEN_CAP_REVIEW_CANDIDATE"
    if core_ok and row["worst_week"] > baseline["worst_week"]:
        return "H4_BOX2_OPEN_CAP_WATCHLIST_PARTIAL_TAIL_REPAIR"
    if core_ok:
        return "H4_BOX2_OPEN_CAP_CORE_ONLY"
    return "REJECT_CORE_BREAK"


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_rows", "dropped_rows"}}


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(strip_heavy(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(strip_heavy(row))


def render(payload: dict[str, Any]) -> str:
    lines = [
        f"# A1 XAU H4 Box2 Health Gate + Open Cap {payload['cap']} Exact MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and open-position cap; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Results",
        "",
        "| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in [payload["baseline"], payload["result"]]:
        lines.append(
            f"| `{row['name']}` | `{row['decision']}` | {row['signals']} | {row['blocked_signals']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {row['positive_week_pct']:.2f} | "
            f"`{row['worst_month']}` | {row['worst_month_net']:.2f} | {row['worst_week']:.2f} |"
        )

    lines.extend(["", "## Source Contributions", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
    for source, contribution in payload["source_contributions"].items():
        lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")

    reasons = payload["guard_counts"]["guard_reasons"]
    lines.extend(
        [
            "",
            "## MT5 Guard Counts",
            "",
            f"- Orders: `{payload['guard_counts']['order_rows']}`",
            f"- Max-open-position blocks: `{reasons.get('max_open_positions_reached', 0)}`",
            f"- Previous-month health blocks: `{reasons.get('h4_d1_previous_month_health_gate', 0)}`",
            f"- Supportive-state blocks: `{reasons.get('h4_d1_supportive_state_guard', 0)}`",
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4 box2 previous-month health gate with an open-position cap.")
    parser.add_argument("--cap", type=int, choices=[1, 2], default=2)
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    for path in (PREREG, BASELINE_RAW, BASE_CANDIDATE_KEPT):
        require_file(path)

    stem = output_stem(args.cap)
    variant, metadata = build_variant(args.cap)
    a1.VARIANTS = [variant]
    report_md = REPORTS_DIR / f"{stem}.md"
    report_json = REPORTS_DIR / f"{stem}.json"
    results_csv = REPORTS_DIR / f"{stem}_RESULTS.csv"
    kept_csv = REPORTS_DIR / f"{stem}_KEPT.csv"
    dropped_csv = REPORTS_DIR / f"{stem}_DROPPED.csv"
    mt5_report_md = REPORTS_DIR / f"{stem}_MT5_COMPONENT.md"
    mt5_report_json = REPORTS_DIR / f"{stem}_MT5_COMPONENT.json"

    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(tag(args.cap)),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )

    baseline = evaluate("prevhealth_box2_broad_quarantined", read_ledger(BASE_CANDIDATE_KEPT), [], None)
    filtered_raw, removal_counts = remove_f33_and_h4_sources(read_raw_rows(BASELINE_RAW))
    short_raw = short_v2_raw_rows()
    box2_rows = replacement_rows(mt5_payload["variants"][0], metadata)
    kept, dropped = dedupe_signals(filtered_raw + box2_rows + short_raw)
    result = evaluate(f"prevhealth_box2_open_cap{args.cap}_broad_quarantined", kept, dropped, baseline)

    write_signal_csv(kept_csv, result["kept_rows"])
    write_signal_csv(dropped_csv, dropped)
    write_results(results_csv, [baseline, result])

    if result["decision"] == "H4_BOX2_OPEN_CAP_REVIEW_CANDIDATE":
        status = result["decision"]
        interpretation = "The open-position cap repaired the weekly tail without breaking the monthly/core candidate. Keep research-only and send for review."
    elif result["decision"] == "H4_BOX2_OPEN_CAP_WATCHLIST_PARTIAL_TAIL_REPAIR":
        status = result["decision"]
        interpretation = "The open-position cap partially improved the weekly tail but did not pass the full preregistered review gate. Keep watchlist-only."
    elif result["decision"] == "H4_BOX2_OPEN_CAP_CORE_ONLY":
        status = result["decision"]
        interpretation = "The open-position cap preserved the core but did not repair the weekly tail. The worst week is probably driven by another source or by exits already inside the cap."
    else:
        status = "NO_H4_BOX2_OPEN_CAP_SURVIVOR"
        interpretation = "The open-position cap broke the core candidate. Do not promote."

    payload = {
        "status": status,
        "cap": args.cap,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "inputs": {
            "baseline_candidate_kept": rel(BASE_CANDIDATE_KEPT),
            "baseline_raw": rel(BASELINE_RAW),
        },
        "removal_counts": removal_counts,
        "short_v2_raw_rows": len(short_raw),
        "box2_replacement_rows": len(box2_rows),
        "baseline": strip_heavy(baseline),
        "result": strip_heavy(result),
        "source_contributions": source_contributions(result["kept_rows"]),
        "guard_counts": guard_counts(mt5_payload["variants"][0]),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "results_csv": rel(results_csv),
            "kept_csv": rel(kept_csv),
            "dropped_csv": rel(dropped_csv),
            "mt5_component_md": rel(mt5_report_md),
            "mt5_component_json": rel(mt5_report_json),
        },
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "decision": result["decision"],
                "cap": args.cap,
                "signals": result["signals"],
                "wr": result["wr"],
                "wl": result["wl"],
                "stress_030_wl": result["stress_030_wl"],
                "net": result["net"],
                "max_closed_dd": result["max_closed_dd"],
                "positive_months": result["positive_months"],
                "negative_months": result["negative_months"],
                "worst_week": result["worst_week"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

