from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, rel, summary_metrics
from analyze_a1_xau_previous_month_source_health_gate import LONG_PLUS_V2
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import BASELINE_RAW, write_signal_csv
from run_a1_h4_d1_review_repair_exact import (
    COMPONENTS,
    guard_counts,
    read_raw_rows,
    remove_f33_and_h4_sources,
    replacement_rows,
    require_file,
    sha256_file,
    source_contributions,
)
from run_a1_h4_previous_month_health_gate_exact import SHORT_V2_DROPPED, SHORT_V2_KEPT, short_v2_raw_rows


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606"
SUPPORTIVE_COMPONENTS_JSON = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_MT5_COMPONENTS.json"
PREV_HEALTH_COMPONENTS_JSON = REPORTS_DIR / "A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606_MT5_COMPONENTS.json"


def load_json(path: Path) -> dict[str, Any]:
    require_file(path)
    return json.loads(path.read_text(encoding="utf-8"))


def variant_by_name(payload: dict[str, Any], name: str) -> dict[str, Any]:
    for item in payload.get("variants", []):
        if item.get("name") == name:
            return item
    raise KeyError(f"{name} missing from {payload}")


def meta(source_key: str, probe: str) -> dict[str, Any]:
    component = COMPONENTS[source_key]
    return {
        "probe": probe,
        "component_key": source_key,
        "source_id": component["source_id"],
        "source_priority": component["source_priority"],
        "family_group": "h4_d1_core_shape",
        "label": probe,
    }


def build_component_rows() -> dict[str, list[dict[str, Any]]]:
    supportive = load_json(SUPPORTIVE_COMPONENTS_JSON)
    prev_health = load_json(PREV_HEALTH_COMPONENTS_JSON)
    specs = {
        "supportive_box2": (supportive, "supportive_guard_box2", meta("box2", "supportive_guard")),
        "supportive_broad": (supportive, "supportive_guard_broad", meta("broad", "supportive_guard")),
        "prevhealth_box2": (prev_health, "h4_prev_month_health_gate_box2", meta("box2", "h4_prev_month_health_gate")),
        "prevhealth_broad": (prev_health, "h4_prev_month_health_gate_broad", meta("broad", "h4_prev_month_health_gate")),
    }
    return {
        key: replacement_rows(variant_by_name(payload, variant), metadata)
        for key, (payload, variant, metadata) in specs.items()
    }


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
    core_ok = (
        row["net"] >= 19000.0
        and row["wr"] >= 48.0
        and wl >= 2.0
        and stress_wl >= 1.90
        and row["active_weekday_pct"] >= 84.0
    )
    month_repair = row["positive_months"] >= baseline["positive_months"] + 2
    dd_ok = row["max_closed_dd"] <= baseline["max_closed_dd"]
    worst_month_ok = row["worst_month_net"] >= baseline["worst_month_net"]
    if month_repair and core_ok and dd_ok and worst_month_ok:
        return "H4_COMPOSITION_REVIEW_CANDIDATE"
    if month_repair and core_ok:
        return "H4_COMPOSITION_WATCHLIST_DD_OR_MONTH_RISK"
    if core_ok and dd_ok:
        return "H4_COMPOSITION_CORE_ONLY"
    return "REJECT_CORE_OR_SHAPE"


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_rows", "dropped_rows"}}


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(strip_heavy(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(strip_heavy(row))


def compose(
    filtered_raw: list[dict[str, Any]],
    short_raw: list[dict[str, Any]],
    component_rows: dict[str, list[dict[str, Any]]],
    source_keys: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw = list(filtered_raw)
    for key in source_keys:
        raw.extend(component_rows[key])
    raw.extend(short_raw)
    return dedupe_signals(raw)


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4 Box2 Health Gate / Broad Quarantine",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: recomposition of existing exact-MT5 H4 component ledgers with unchanged frequency and V2 short ledgers. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
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
    for row in [payload["baseline"], *payload["results"]]:
        lines.append(
            f"| `{row['name']}` | `{row['decision']}` | {row['signals']} | {row['blocked_signals']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {row['positive_week_pct']:.2f} | "
            f"`{row['worst_month']}` | {row['worst_month_net']:.2f} | {row['worst_week']:.2f} |"
        )

    lines.extend(["", "## Best Source Contributions", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
    for source, contribution in payload["best_source_contributions"].items():
        lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")

    lines.extend(
        [
            "",
            "## MT5 Component Guard Counts",
            "",
            "| Component | Trades | Orders | Health blocks | Support blocks | Other guard blocks |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["component_details"]:
        reasons = item["guard_counts"]["guard_reasons"]
        health = reasons.get("h4_d1_previous_month_health_gate", 0)
        support = reasons.get("h4_d1_supportive_state_guard", 0)
        other = sum(count for reason, count in reasons.items() if reason not in {"h4_d1_previous_month_health_gate", "h4_d1_supportive_state_guard"})
        lines.append(f"| `{item['name']}` | {item['rows']} | {item['guard_counts']['order_rows']} | {health} | {support} | {other} |")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    for path in (PREREG, BASELINE_RAW, LONG_PLUS_V2, SHORT_V2_KEPT, SHORT_V2_DROPPED, SUPPORTIVE_COMPONENTS_JSON, PREV_HEALTH_COMPONENTS_JSON):
        require_file(path)

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_f33_and_h4_sources(raw)
    short_raw = short_v2_raw_rows()
    component_rows = build_component_rows()

    baseline = evaluate("long_plus_short_v2_no_source_health_gate", read_ledger(LONG_PLUS_V2), [], None)
    variant_specs = [
        ("control_supportive_box2_supportive_broad", ["supportive_box2", "supportive_broad"]),
        ("prevhealth_box2_supportive_broad", ["prevhealth_box2", "supportive_broad"]),
        ("prevhealth_box2_broad_quarantined", ["prevhealth_box2"]),
        ("supportive_box2_broad_quarantined", ["supportive_box2"]),
        ("prevhealth_box2_prevhealth_broad", ["prevhealth_box2", "prevhealth_broad"]),
    ]

    results: list[dict[str, Any]] = []
    kept_paths: dict[str, Path] = {}
    dropped_paths: dict[str, Path] = {}
    for name, sources in variant_specs:
        kept, dropped = compose(filtered_raw, short_raw, component_rows, sources)
        row = evaluate(name, kept, dropped, baseline)
        results.append(row)
        kept_path = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_KEPT.csv"
        dropped_path = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_DROPPED.csv"
        write_signal_csv(kept_path, row["kept_rows"])
        write_signal_csv(dropped_path, dropped)
        kept_paths[name] = kept_path
        dropped_paths[name] = dropped_path

    rank_order = {
        "H4_COMPOSITION_REVIEW_CANDIDATE": 0,
        "H4_COMPOSITION_WATCHLIST_DD_OR_MONTH_RISK": 1,
        "H4_COMPOSITION_CORE_ONLY": 2,
        "REJECT_CORE_OR_SHAPE": 3,
    }
    best = sorted(
        results,
        key=lambda row: (
            rank_order.get(row["decision"], 9),
            -row["positive_months"],
            row["negative_months"],
            row["max_closed_dd"],
            -row["net"],
        ),
    )[0]
    status = best["decision"]
    if status == "H4_COMPOSITION_REVIEW_CANDIDATE":
        interpretation = "A broad-quarantine/box2-health composition repaired monthly consistency without worsening drawdown or worst month. It is still research-only, but this is now a reviewer-grade candidate."
    elif status == "H4_COMPOSITION_WATCHLIST_DD_OR_MONTH_RISK":
        interpretation = "At least one composition repaired monthly consistency, but it still worsened drawdown or worst month. Keep watchlist-only; do not demo."
    else:
        interpretation = "No composition repaired monthly consistency and risk shape together. The broad-H4 issue is diagnostic, not solved."

    supportive_payload = load_json(SUPPORTIVE_COMPONENTS_JSON)
    prev_health_payload = load_json(PREV_HEALTH_COMPONENTS_JSON)
    component_details: list[dict[str, Any]] = []
    for payload, names in (
        (supportive_payload, ["supportive_guard_box2", "supportive_guard_broad"]),
        (prev_health_payload, ["h4_prev_month_health_gate_box2", "h4_prev_month_health_gate_broad"]),
    ):
        for name in names:
            result = variant_by_name(payload, name)
            component_details.append({"name": name, "rows": len(component_rows[name.replace("h4_prev_month_health_gate", "prevhealth").replace("supportive_guard", "supportive")]), "guard_counts": guard_counts(result)})

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "inputs": {
            "baseline_raw": rel(BASELINE_RAW),
            "baseline_long_plus_v2": rel(LONG_PLUS_V2),
            "supportive_components_json": rel(SUPPORTIVE_COMPONENTS_JSON),
            "prev_health_components_json": rel(PREV_HEALTH_COMPONENTS_JSON),
            "short_v2_kept": rel(SHORT_V2_KEPT),
            "short_v2_dropped": rel(SHORT_V2_DROPPED),
        },
        "removal_counts": removal_counts,
        "short_v2_raw_rows": len(short_raw),
        "component_row_counts": {key: len(rows) for key, rows in component_rows.items()},
        "baseline": strip_heavy(baseline),
        "results": [strip_heavy(row) for row in results],
        "best": strip_heavy(best),
        "best_source_contributions": source_contributions(best["kept_rows"]),
        "component_details": component_details,
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "results_csv": rel(results_csv),
            **{f"{name}_kept_csv": rel(path) for name, path in kept_paths.items()},
            **{f"{name}_dropped_csv": rel(path) for name, path in dropped_paths.items()},
        },
    }
    write_results(results_csv, [baseline, *results])
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "best": best["name"],
                "signals": best["signals"],
                "wr": best["wr"],
                "wl": best["wl"],
                "stress_030_wl": best["stress_030_wl"],
                "net": best["net"],
                "max_closed_dd": best["max_closed_dd"],
                "positive_months": best["positive_months"],
                "negative_months": best["negative_months"],
                "worst_month": best["worst_month"],
                "worst_month_net": best["worst_month_net"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

