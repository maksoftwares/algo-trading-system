from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    REPO_ROOT,
    build_source_specs,
    dedupe_signals,
    load_sources,
    rel,
    sha256_file,
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STEM = "A1_XAU_BEST_OF_EACH_HYBRID_FRONTIER_2026_07_05"
PREREG_PATH = PHASE1_ROOT / "docs" / "A1_XAU_M5_BEST_OF_EACH_HYBRID_FRONTIER_PREREG_2026_07_05.md"
STEP3_BEST_KEPT = REPORTS_DIR / "A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_2026_07_05_BEST_KEPT_SIGNALS.csv"
H4_D1_REPORT = REPORTS_DIR / "A1_XAU_H4_D1_LONG_ONLY_FREQUENCY_STRESS_202207_202606.json"

MAX_COMBO_SIZE = 5


def parse_dt(value: str) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def read_standard_kept(path: Path, component_id: str, priority: int, family_group: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for ordinal, row in enumerate(reader, start=2):
            entry_time = parse_dt(str(row["entry_time"]))
            rows.append(
                {
                    "source_id": component_id,
                    "family_group": family_group,
                    "source_priority": priority,
                    "entry_time": entry_time,
                    "entry_date": entry_time.date(),
                    "direction": str(row.get("direction", "")).upper(),
                    "pnl_usd": float(row.get("pnl_usd", row.get("signal_pnl", row.get("profit_aed", 0))) or 0.0),
                    "tickets": int(float(row.get("tickets") or 1)),
                    "lots": float(row.get("lots", row.get("volume", 0)) or 0.0),
                    "component": component_id,
                    "source_csv": str(row.get("source_csv") or path),
                    "source_row": ordinal,
                }
            )
    return rows


def read_trade_csv(path: Path, component_id: str, priority: int, family_group: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for ordinal, row in enumerate(reader, start=2):
            entry_time = parse_dt(str(row["entry_time"]))
            rows.append(
                {
                    "source_id": component_id,
                    "family_group": family_group,
                    "source_priority": priority,
                    "entry_time": entry_time,
                    "entry_date": entry_time.date(),
                    "direction": str(row.get("direction", "")).upper(),
                    "pnl_usd": float(row.get("profit_aed", row.get("pnl_usd", 0)) or 0.0),
                    "tickets": 1,
                    "lots": float(row.get("volume", 0) or 0.0),
                    "component": component_id,
                    "source_csv": str(path),
                    "source_row": ordinal,
                }
            )
    return rows


def h4_trade_csv(name: str) -> Path:
    data = json.loads(H4_D1_REPORT.read_text(encoding="utf-8"))
    for variant in data.get("variants", []):
        if variant.get("name") == name:
            return Path(variant["trade_csv"])
    raise KeyError(name)


def build_components() -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    specs = build_source_specs()
    sources, source_inventory = load_sources(specs)

    high_payout_raw: list[dict[str, Any]] = []
    for source_id in (
        "step1_f33_r30_be_never",
        "v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning",
        "orrev_london_firm_stop10",
    ):
        high_payout_raw.extend(sources[source_id])
    high_payout, _ = dedupe_signals(high_payout_raw)

    components: dict[str, list[dict[str, Any]]] = {
        "freq_step3_frontier": read_standard_kept(STEP3_BEST_KEPT, "freq_step3_frontier", 10, "frequency_frontier"),
        "hp_v13_orrev": high_payout,
        "split_compromise_f33_r30_be_1r": sources["step1_f33_r30_be_1r"],
        "split_high_wr_f67_r20_be_tp1": sources["step1_f67_r20_be_tp1"],
        "split_high_payout_f33_r30_be_never": sources["step1_f33_r30_be_never"],
        "h4_d1_long_best_box2_atr80": read_trade_csv(
            h4_trade_csv("long_box2_atr80_range150_body035"),
            "h4_d1_long_best_box2_atr80",
            80,
            "h4_d1_core_shape",
        ),
        "h4_d1_long_broad_box3_atr60": read_trade_csv(
            h4_trade_csv("long_broad_box3_atr60_range125_body035"),
            "h4_d1_long_broad_box3_atr60",
            81,
            "h4_d1_core_shape",
        ),
        "rr2_lock080_010": sources["rr2_lock080_010"],
        "orrev_london_firm_stop15": sources["orrev_london_firm_stop15"],
    }

    inventory: list[dict[str, Any]] = []
    for component_id, rows in components.items():
        paths = sorted({str(row.get("source_csv") or "") for row in rows if row.get("source_csv")})
        inventory.append(
            {
                "component_id": component_id,
                "rows": len(rows),
                "paths": paths[:8],
                "path_count": len(paths),
                "sha256": sha256_file(Path(paths[0])) if len(paths) == 1 and Path(paths[0]).exists() else "",
            }
        )
    return components, source_inventory + inventory


def decision(row: dict[str, Any]) -> str:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    pf = float(row.get("profit_factor") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    if net <= 0:
        return "FAIL_NET"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "OWNER_GOAL_HIT"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_FREQUENCY_GAP"
    if wr >= 48.0 and wl >= 1.8 and active >= 70.0 and pf >= 1.30:
        return "NEAR_OWNER_FRONTIER"
    if wr >= 50.0 and wl < 2.0:
        return "FAIL_WIN_LOSS"
    if wr < 50.0 and wl >= 2.0:
        return "FAIL_WIN_RATE"
    return "FAIL_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.25) * 350
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.5) * 325
        + min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.2) * 250
        + min(float(row.get("profit_factor") or 0.0) / 1.4, 1.5) * 100
        + min(float(row.get("net_usd") or 0.0) / 10000.0, 2.0) * 60,
        4,
    )


def evaluate_combo(combo: tuple[str, ...], components: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    raw: list[dict[str, Any]] = []
    for component_id in combo:
        raw.extend(components[component_id])
    kept, dropped = dedupe_signals(raw)
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    stress_010 = summary_metrics(kept, cost_per_ticket=0.10, market_days=MARKET_DAYS)
    stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    metrics.update(
        {
            "portfolio_id": "__plus__".join(combo),
            "component_count": len(combo),
            "components": list(combo),
            "raw_signals": len(raw),
            "dropped_overlap_signals": len(dropped),
            "stress_010_net_usd": stress_010["net_usd"],
            "stress_010_win_rate_pct": stress_010["win_rate_pct"],
            "stress_010_avg_win_loss": stress_010["avg_win_loss"],
            "stress_030_net_usd": stress_030["net_usd"],
            "stress_030_win_rate_pct": stress_030["win_rate_pct"],
            "stress_030_avg_win_loss": stress_030["avg_win_loss"],
        }
    )
    metrics["decision"] = decision(metrics)
    metrics["score"] = score(metrics)
    return metrics, kept, dropped


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "decision",
        "score",
        "portfolio_id",
        "component_count",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "net_usd",
        "profit_factor",
        "max_closed_drawdown_usd",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
        "stress_010_net_usd",
        "stress_010_avg_win_loss",
        "stress_030_net_usd",
        "stress_030_avg_win_loss",
        "dropped_overlap_signals",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_signal_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "component",
        "source_id",
        "family_group",
        "source_priority",
        "entry_time",
        "entry_date",
        "direction",
        "pnl_usd",
        "tickets",
        "lots",
        "source_csv",
        "source_row",
        "drop_reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    best = payload["best_row"]
    lines = [
        "# A1 XAU Best-Of-Each Hybrid Frontier",
        "",
        "Generated: 2026-07-05",
        "",
        "Scope: offline exact-MT5 ledger composition only. No MT5 launch, runtime attach, charts, presets, orders, or broker state mutation.",
        "",
        f"Decision: **{payload['status']}**",
        "",
        "## Best Row",
        "",
        f"- Portfolio: `{best['portfolio_id']}`",
        f"- Decision: `{best['decision']}`",
        f"- Signals: {best['signals']}",
        f"- WR: {best['win_rate_pct']}%",
        f"- Avg win / avg loss: {best['avg_win_loss']}",
        f"- Active weekdays: {best['active_weekdays']} / {len(MARKET_DAYS)} ({best['active_weekday_pct']}%)",
        f"- Net: {best['net_usd']}",
        f"- PF: {best['profit_factor']}",
        f"- Stress -0.10/ticket: net {best['stress_010_net_usd']}, W/L {best['stress_010_avg_win_loss']}",
        f"- Stress -0.30/ticket: net {best['stress_030_net_usd']}, W/L {best['stress_030_avg_win_loss']}",
        "",
        "## Top Frontier Rows",
        "",
        "| Rank | Decision | Portfolio | Signals | WR % | W/L | Active % | Net | PF | Stress -0.30 W/L |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {rank} | `{row['decision']}` | `{row['portfolio_id']}` | {row['signals']} | "
            f"{row['win_rate_pct']} | {row['avg_win_loss']} | {row['active_weekday_pct']} | "
            f"{row['net_usd']} | {row['profit_factor']} | {row['stress_030_avg_win_loss']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            f"Results CSV: `{rel(Path(payload['outputs']['results_csv']))}`",
            f"Best kept CSV: `{rel(Path(payload['outputs']['best_kept_csv']))}`",
            f"JSON: `{rel(Path(payload['outputs']['json']))}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    components, inventory = build_components()
    rows: list[dict[str, Any]] = []
    combo_details: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {}
    component_ids = list(components)
    for size in range(1, min(MAX_COMBO_SIZE, len(component_ids)) + 1):
        for combo in itertools.combinations(component_ids, size):
            row, kept, dropped = evaluate_combo(combo, components)
            rows.append(row)
            combo_details[row["portfolio_id"]] = (kept, dropped)

    decision_rank = {
        "OWNER_GOAL_HIT": 5,
        "CORE_SHAPE_FREQUENCY_GAP": 4,
        "NEAR_OWNER_FRONTIER": 3,
        "FAIL_WIN_LOSS": 2,
        "FAIL_WIN_RATE": 1,
        "FAIL_OWNER_SHAPE": 0,
        "FAIL_NET": -1,
    }
    rows.sort(
        key=lambda row: (
            decision_rank.get(str(row.get("decision")), -2),
            row.get("score") or 0.0,
            row.get("active_weekday_pct") or 0.0,
            row.get("avg_win_loss") or 0.0,
            row.get("win_rate_pct") or 0.0,
        ),
        reverse=True,
    )
    best = rows[0]
    kept, dropped = combo_details[best["portfolio_id"]]

    status = "HYBRID_REJECT_NO_OWNER_GOAL_HIT"
    interpretation = (
        "The best-of-each hybrid improved the frontier but did not combine the three target corners. "
        "Frequency and WR still come from low-payoff components, while 2R components remain too sparse or low-WR. "
        "No reviewer or demo-spec spend is justified unless the owner relaxes one metric."
    )
    if best["decision"] == "OWNER_GOAL_HIT":
        status = "HYBRID_OWNER_GOAL_HIT_REVIEW_REQUIRED"
        interpretation = "Hybrid reached all owner metrics at diagnostic composition level. Reviewer reconstruction is required before any spec work."
    elif best["decision"] == "CORE_SHAPE_FREQUENCY_GAP":
        status = "HYBRID_CORE_SHAPE_FREQUENCY_GAP"
        interpretation = "Hybrid reached WR and W/L core shape but remains short of daily activity. Reviewer may be useful only if owner accepts frequency gap."
    elif best["decision"] == "NEAR_OWNER_FRONTIER":
        status = "HYBRID_NEAR_OWNER_FRONTIER"
        interpretation = "Hybrid reached a near-owner frontier but not the full target. Review only if owner wants to evaluate relaxing one metric."

    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT_SIGNALS.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED_SIGNALS.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    write_csv(results_csv, rows)
    write_signal_csv(best_kept_csv, kept)
    write_signal_csv(best_dropped_csv, dropped)
    payload = {
        "status": status,
        "generated": "2026-07-05",
        "boundary": "offline_exact_mt5_ledger_composition_only_no_mt5_launch",
        "preregistration": str(PREREG_PATH),
        "component_inventory": inventory,
        "searched_portfolios": len(rows),
        "best_row": best,
        "top_rows": rows[:30],
        "interpretation": interpretation,
        "outputs": {
            "results_csv": str(results_csv),
            "best_kept_csv": str(best_kept_csv),
            "best_dropped_csv": str(best_dropped_csv),
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": status, "best_decision": best["decision"], "report": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
