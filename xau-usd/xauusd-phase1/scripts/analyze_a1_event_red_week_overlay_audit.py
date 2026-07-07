from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times, week_start
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, rel, summary_metrics
from run_a1_h4_d1_geometry_v2_weekly_shape import read_composition_csv, weekly_exit_shape, write_signal_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
EVENT_REPORT_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_EVENT_REACTION_V0_202207_202606.json"
OUTPUT_STEM = "A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606"

EVENT_PRIORITY = 90
EVENT_FAMILY = "event_reaction_red_week_overlay"

COMBOS = {
    "event_impulse_fomc_rr2_only": ["event_impulse_fomc_rr2"],
    "event_fade_cpi_rr2_only": ["event_fade_cpi_rr2"],
    "event_fomc_impulse_plus_cpi_fade": ["event_impulse_fomc_rr2", "event_fade_cpi_rr2"],
    "event_all_v0_positive_net": [
        "event_impulse_nfp_rr2",
        "event_impulse_cpi_rr2",
        "event_fade_cpi_rr2",
        "event_impulse_fomc_rr2",
        "event_fade_fomc_rr2",
    ],
    "event_all_v0_including_negative_control": [
        "event_impulse_nfp_rr2",
        "event_fade_nfp_rr2",
        "event_impulse_cpi_rr2",
        "event_fade_cpi_rr2",
        "event_impulse_fomc_rr2",
        "event_fade_fomc_rr2",
    ],
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


def read_trade_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def event_variant_paths() -> dict[str, Path]:
    payload = json.loads(EVENT_REPORT_JSON.read_text(encoding="utf-8"))
    return {item["name"]: Path(item["trade_csv"]) for item in payload["variants"]}


def event_rows(name: str, trade_csv: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_trade_rows(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        exit_time = parse_dt(row["exit_time"]) if row.get("exit_time") else entry_time
        rows.append(
            {
                "component": name,
                "source_id": name,
                "upstream_source_id": name,
                "upstream_component": "event_reaction_v0_exact_mt5",
                "family_group": EVENT_FAMILY,
                "source_priority": EVENT_PRIORITY,
                "cell_id": name,
                "component_priority": 0,
                "variant_name": name,
                "entry_time": entry_time,
                "entry_date": entry_time.date(),
                "exit_time": exit_time,
                "exit_date": exit_time.date(),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": parse_money(row.get("profit_float") or row.get("profit_aed")),
                "tickets": 1,
                "lots": float(row.get("volume") or 0.0),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def weekly_pnl(rows: list[dict[str, Any]]) -> dict[date, float]:
    enriched, _stats = enrich_exit_times(rows)
    by_week: dict[date, float] = defaultdict(float)
    for row in enriched:
        by_week[week_start(row["exit_date"])] += float(row["pnl_usd"])
    return {key: round(value, 2) for key, value in by_week.items()}


def source_rows(rows: list[dict[str, Any]], source_ids: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("source_id") in source_ids]


def red_week_score(
    baseline_weekly: dict[date, float],
    combined_weekly: dict[date, float],
    kept_events: list[dict[str, Any]],
) -> dict[str, Any]:
    event_weekly = weekly_pnl(kept_events)
    red_weeks = {week for week, pnl in baseline_weekly.items() if pnl < 0.0}
    green_weeks = {week for week, pnl in baseline_weekly.items() if pnl > 0.0}
    touched_red = {week for week in red_weeks if abs(event_weekly.get(week, 0.0)) > 0.0}
    flipped = {week for week in red_weeks if baseline_weekly[week] < 0.0 and combined_weekly.get(week, 0.0) > 0.0}
    worsened = {week for week in red_weeks if combined_weekly.get(week, 0.0) < baseline_weekly[week]}
    return {
        "baseline_red_weeks": len(red_weeks),
        "baseline_green_weeks": len(green_weeks),
        "red_weeks_touched": len(touched_red),
        "red_weeks_flipped": len(flipped),
        "red_weeks_worsened": len(worsened),
        "event_net_in_red_weeks": round(sum(event_weekly.get(week, 0.0) for week in red_weeks), 2),
        "event_net_in_green_weeks": round(sum(event_weekly.get(week, 0.0) for week in green_weeks), 2),
        "event_net_in_nonbaseline_weeks": round(
            sum(value for week, value in event_weekly.items() if week not in red_weeks and week not in green_weeks), 2
        ),
        "flipped_weeks": [week.isoformat() for week in sorted(flipped)],
        "worsened_weeks": [week.isoformat() for week in sorted(worsened)],
    }


def row_for(name: str, kept: list[dict[str, Any]], baseline_shape: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(kept)
    decision = "REJECT_NO_RED_WEEK_IMPACT"
    if score["red_weeks_flipped"] > 0 and score["red_weeks_worsened"] == 0 and shape["positive_week_pct"] > baseline_shape["positive_week_pct"]:
        decision = "WATCHLIST_RED_WEEK_CLUE"
    if shape["positive_week_pct"] <= baseline_shape["positive_week_pct"]:
        decision = "REJECT_WEEKLY_NOT_IMPROVED"
    if (metrics["avg_win_loss"] or 0.0) < 2.0 or metrics["win_rate_pct"] < 50.0:
        decision = "REJECT_BREAKS_CORE_SHAPE"
    return {
        "combo": name,
        "signals": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "active": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "positive_week_pct": shape["positive_week_pct"],
        "positive_week_delta_pp": round(shape["positive_week_pct"] - baseline_shape["positive_week_pct"], 2),
        "worst_week": shape["worst_week_usd"],
        "event_trades_kept": score["event_trades_kept"],
        "event_net_kept": score["event_net_kept"],
        "red_weeks_touched": score["red_weeks_touched"],
        "red_weeks_flipped": score["red_weeks_flipped"],
        "red_weeks_worsened": score["red_weeks_worsened"],
        "event_net_in_red_weeks": score["event_net_in_red_weeks"],
        "event_net_in_green_weeks": score["event_net_in_green_weeks"],
        "decision": decision,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Event Red-Week Overlay Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: offline recomposition of already-generated exact-MT5 event-reaction V0 ledgers onto the corrected supportive-guard book. No new MT5 run, tuning sweep, live/demo runtime, chart, preset, order, position, or broker state change.",
        "",
        f"Baseline: `{payload['baseline_name']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Results",
        "",
        "| Combo | Signals | WR% | W/L | Active% | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Event kept | Event net | Red touched | Red flipped | Red worsened | Event red net | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['combo']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['positive_week_pct']:.2f} | {row['positive_week_delta_pp']:.2f} | {row['worst_week']:.2f} | "
            f"{row['event_trades_kept']} | {row['event_net_kept']:.2f} | {row['red_weeks_touched']} | "
            f"{row['red_weeks_flipped']} | {row['red_weeks_worsened']} | {row['event_net_in_red_weeks']:.2f} | `{row['decision']}` |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    require_file(BASELINE_KEPT)
    require_file(EVENT_REPORT_JSON)
    baseline = read_composition_csv(BASELINE_KEPT)
    baseline_shape = weekly_exit_shape(baseline)
    baseline_weekly = weekly_pnl(baseline)
    paths = event_variant_paths()
    event_by_name = {name: event_rows(name, path) for name, path in paths.items()}

    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    outputs = {
        "md": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"),
        "json": str(REPORTS_DIR / f"{OUTPUT_STEM}.json"),
        "results_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"),
    }
    for combo_name, names in COMBOS.items():
        additions = [row for name in names for row in event_by_name[name]]
        kept, dropped = dedupe_signals(baseline + additions)
        kept_events = source_rows(kept, set(names))
        combined_weekly = weekly_pnl(kept)
        score = red_week_score(baseline_weekly, combined_weekly, kept_events)
        score.update(
            {
                "event_trades_raw": len(additions),
                "event_trades_kept": len(kept_events),
                "event_trades_dropped": len([row for row in dropped if row.get("source_id") in set(names)]),
                "event_net_kept": round(sum(float(row["pnl_usd"]) for row in kept_events), 2),
            }
        )
        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_DROPPED.csv"
        write_signal_csv(kept_csv, kept)
        write_signal_csv(dropped_csv, dropped)
        outputs[f"{combo_name}_kept_csv"] = str(kept_csv)
        outputs[f"{combo_name}_dropped_csv"] = str(dropped_csv)
        row = row_for(combo_name, kept, baseline_shape, score)
        rows.append(row)
        details.append({"combo": combo_name, "event_names": names, "score": score, "row": row})

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    clues = [row for row in rows if row["decision"] == "WATCHLIST_RED_WEEK_CLUE"]
    status = "EVENT_OVERLAY_RED_WEEK_CLUE" if clues else "NO_EVENT_OVERLAY_RED_WEEK_SURVIVOR"
    if clues:
        best = max(clues, key=lambda row: (row["red_weeks_flipped"], -row["red_weeks_worsened"], row["positive_week_delta_pp"]))
        interpretation = (
            f"`{best['combo']}` produced a small red-week clue. It is sparse and not demo-ready; only exact-MT5 follow-up "
            "with preregistered pass/fail should be considered."
        )
    else:
        interpretation = (
            "The exact-MT5 event V0 ledgers are too sparse to repair weekly shape. They do not flip enough red weeks and "
            "do not move the corrected supportive-guard book toward the 70-80% weekly target. This weakens the event-overlay path."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "baseline_name": "supportive_guard_session_parity",
        "baseline_csv": str(BASELINE_KEPT),
        "event_report_json": str(EVENT_REPORT_JSON),
        "baseline_shape": baseline_shape,
        "rows": rows,
        "details": details,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    Path(outputs["json"]).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    Path(outputs["md"]).write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "rows": rows, "report": outputs["md"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
