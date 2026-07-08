from __future__ import annotations

import csv
import heapq
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_weekly_exit_anatomy import week_start
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, parse_dt, rel, summary_metrics
from run_a1_h4_d1_geometry_v2_weekly_shape import write_signal_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_SOURCE_MONTHLY_FIREWALL_PREREG_2026_07_08.md"
SUPPORTIVE_LONG = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
LONG_PLUS_V2 = REPORTS_DIR / "A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv"
OUTPUT_STEM = "A1_XAU_SOURCE_MONTHLY_FIREWALL_202207_202606"

START_DATE = date(2022, 7, 1)
END_DATE = date(2026, 6, 30)

H4_SOURCES = {"h4_d1_long_best_box2_atr80", "h4_d1_long_broad_box3_atr60"}
FREQUENCY_SOURCES = {"freq_step3_frontier"}


@dataclass(frozen=True)
class SourceRule:
    group: str
    loss_count_stop: int | None = None
    pnl_stop: float | None = None


@dataclass(frozen=True)
class Variant:
    name: str
    rules: tuple[SourceRule, ...]


def all_week_starts() -> list[date]:
    current = week_start(START_DATE)
    end = week_start(END_DATE)
    weeks: list[date] = []
    while current <= end:
        weeks.append(current)
        current += timedelta(days=7)
    return weeks


ALL_WEEK_STARTS = all_week_starts()


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def maybe_dt(value: Any, fallback: datetime) -> datetime:
    text = str(value or "").strip()
    if not text:
        return fallback
    return parse_dt(text)


def read_ledger(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle), start=2):
            entry_time = parse_dt(row["entry_time"])
            exit_time = maybe_dt(row.get("exit_time"), entry_time)
            rows.append(
                {
                    **row,
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
                    "exit_time": exit_time,
                    "exit_date": exit_time.date(),
                    "direction": str(row.get("direction", "")).upper(),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(row.get("tickets") or 1),
                    "lots": float(row.get("lots") or 0.0),
                    "source_csv": row.get("source_csv", str(path)),
                    "source_row": int(row.get("source_row") or ordinal),
                }
            )
    return rows


def source_group(row: dict[str, Any]) -> str:
    source_id = str(row.get("source_id", ""))
    if source_id in H4_SOURCES:
        return "h4_core"
    if source_id in FREQUENCY_SOURCES:
        return "frequency"
    if source_id == "short_hedge_v2_breakdown_retest":
        return "short_hedge"
    return "other"


def max_closed_drawdown(rows: list[dict[str, Any]]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for row in sorted(rows, key=lambda item: (item["exit_time"], item["entry_time"], item["source_priority"])):
        equity += float(row["pnl_usd"])
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return round(max_dd, 2)


def month_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_month: dict[str, float] = defaultdict(float)
    for row in rows:
        by_month[month_key(row["exit_date"])] += float(row["pnl_usd"])
    values = list(by_month.items())
    positive = sum(1 for _month, pnl in values if pnl > 0.0)
    negative = sum(1 for _month, pnl in values if pnl < 0.0)
    flat = sum(1 for _month, pnl in values if abs(pnl) <= 0.0000001)
    worst = min(values, key=lambda item: item[1]) if values else ("", 0.0)
    best = max(values, key=lambda item: item[1]) if values else ("", 0.0)
    return {
        "closing_months": len(values),
        "positive_months": positive,
        "negative_months": negative,
        "flat_months": flat,
        "positive_month_pct": round(100.0 * positive / len(values), 2) if values else 0.0,
        "worst_month": worst[0],
        "worst_month_net": round(worst[1], 2),
        "best_month": best[0],
        "best_month_net": round(best[1], 2),
    }


def weekly_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_week: dict[date, float] = defaultdict(float)
    for row in rows:
        by_week[week_start(row["exit_date"])] += float(row["pnl_usd"])
    positive = sum(1 for week in ALL_WEEK_STARTS if by_week.get(week, 0.0) > 0.0)
    return {
        "positive_week_pct": round(100.0 * positive / len(ALL_WEEK_STARTS), 2),
        "worst_week": round(min((by_week.get(week, 0.0) for week in ALL_WEEK_STARTS), default=0.0), 2),
    }


def rule_triggered(rule: SourceRule, state: dict[str, Any]) -> str:
    if rule.loss_count_stop is not None and state["losses"] >= rule.loss_count_stop:
        return f"{rule.group}_monthly_loss_count_{rule.loss_count_stop}"
    if rule.pnl_stop is not None and state["pnl"] <= -rule.pnl_stop:
        return f"{rule.group}_monthly_pnl_stop_{rule.pnl_stop:g}"
    return ""


def apply_firewall(rows: list[dict[str, Any]], variant: Variant) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rules_by_group: dict[str, list[SourceRule]] = defaultdict(list)
    for rule in variant.rules:
        rules_by_group[rule.group].append(rule)

    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    state: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"pnl": 0.0, "losses": 0})
    pending: list[tuple[datetime, int, str, str, float]] = []
    counter = 0

    for row in sorted(rows, key=lambda item: (item["entry_time"], item["source_priority"], item["source_id"])):
        entry_time = row["entry_time"]
        while pending and pending[0][0] <= entry_time:
            _exit_time, _counter, group, close_month, pnl = heapq.heappop(pending)
            bucket = state[(group, close_month)]
            bucket["pnl"] += pnl
            if pnl < 0.0:
                bucket["losses"] += 1

        group = source_group(row)
        entry_month = month_key(row["entry_date"])
        bucket = state[(group, entry_month)]
        reason = ""
        for rule in rules_by_group.get(group, []):
            reason = rule_triggered(rule, bucket)
            if reason:
                break

        if reason:
            item = dict(row)
            item["drop_reason"] = reason
            item["source_group"] = group
            item["closed_source_month_pnl_before_entry"] = round(bucket["pnl"], 2)
            item["closed_source_month_losses_before_entry"] = bucket["losses"]
            dropped.append(item)
            continue

        kept.append(row)
        counter += 1
        heapq.heappush(
            pending,
            (row["exit_time"], counter, group, month_key(row["exit_date"]), float(row["pnl_usd"])),
        )

    return kept, dropped


def variants() -> list[Variant]:
    out = [
        Variant("long_plus_short_v2_no_monthly_firewall", ()),
    ]
    for count in (1, 2, 3):
        out.append(Variant(f"h4_loss_count_stop_{count}", (SourceRule("h4_core", loss_count_stop=count),)))
    for stop in (50.0, 75.0, 100.0, 150.0, 200.0):
        out.append(Variant(f"h4_pnl_stop_{int(stop)}", (SourceRule("h4_core", pnl_stop=stop),)))
    out.extend(
        [
            Variant("h4_loss2_or_pnl100", (SourceRule("h4_core", loss_count_stop=2), SourceRule("h4_core", pnl_stop=100.0))),
            Variant("h4_loss2_or_pnl150", (SourceRule("h4_core", loss_count_stop=2), SourceRule("h4_core", pnl_stop=150.0))),
            Variant("h4_loss3_or_pnl150", (SourceRule("h4_core", loss_count_stop=3), SourceRule("h4_core", pnl_stop=150.0))),
        ]
    )
    for stop in (75.0, 100.0, 150.0, 200.0):
        out.append(Variant(f"freq_pnl_stop_{int(stop)}", (SourceRule("frequency", pnl_stop=stop),)))
    out.extend(
        [
            Variant("h4_pnl100_freq_pnl150", (SourceRule("h4_core", pnl_stop=100.0), SourceRule("frequency", pnl_stop=150.0))),
            Variant(
                "h4_loss2_or_pnl100_freq_pnl150",
                (SourceRule("h4_core", loss_count_stop=2), SourceRule("h4_core", pnl_stop=100.0), SourceRule("frequency", pnl_stop=150.0)),
            ),
            Variant("h4_pnl150_freq_pnl200", (SourceRule("h4_core", pnl_stop=150.0), SourceRule("frequency", pnl_stop=200.0))),
        ]
    )
    return out


def blocked_by_group(dropped: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("source_group", source_group(row))) for row in dropped))


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
    review_ok = (
        row["positive_months"] >= 32
        and row["net"] >= 18000.0
        and row["wr"] >= 48.0
        and wl >= 2.0
        and stress_wl >= 1.90
        and row["active_weekday_pct"] >= 84.0
        and row["max_closed_dd"] <= baseline["max_closed_dd"] * 0.85
    )
    if review_ok:
        return "MONTHLY_FIREWALL_REVIEW_CANDIDATE"
    if row["positive_months"] >= baseline["positive_months"] + 2 and core_ok:
        return "MONTHLY_FIREWALL_WATCHLIST"
    if row["positive_months"] > baseline["positive_months"] and not core_ok:
        return "MONTHLY_IMPROVES_CORE_BREAKS"
    return "REJECT_NO_MONTHLY_REPAIR"


def evaluate(name: str, rows: list[dict[str, Any]], dropped: list[dict[str, Any]], baseline: dict[str, Any] | None) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    months = month_shape(rows)
    weeks = weekly_shape(rows)
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
        "max_closed_dd": max_closed_drawdown(rows),
        "blocked_signals": len(dropped),
        "blocked_by_group": blocked_by_group(dropped),
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        "kept_rows": rows,
        "dropped_rows": dropped,
        **months,
    }
    row["decision"] = "BASELINE" if baseline is None else decide(row, baseline)
    return row


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
        "# A1 XAU Source-Level Monthly Firewall Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: causal source-level monthly firewall over existing exact-MT5 ledgers only. No MT5 launch, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        "",
        "## Best Rows",
        "",
        "| Rank | Rule | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {index} | `{row['name']}` | `{row['decision']}` | {row['signals']} | {row['blocked_signals']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {row['positive_week_pct']:.2f} | "
            f"`{row['worst_month']}` | {row['worst_month_net']:.2f} | {row['worst_week']:.2f} |"
        )

    best = payload["best_row"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"Best row: `{best['name']}` with `{best['positive_months']}` positive months, `{best['negative_months']}` negative months, net `{best['net']:.2f}`, and max closed drawdown `{best['max_closed_dd']:.2f}`.",
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
    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not SUPPORTIVE_LONG.exists():
        raise FileNotFoundError(SUPPORTIVE_LONG)
    if not LONG_PLUS_V2.exists():
        raise FileNotFoundError(LONG_PLUS_V2)

    supportive = read_ledger(SUPPORTIVE_LONG)
    combo = read_ledger(LONG_PLUS_V2)
    supportive_row = evaluate("baseline_supportive_guard_no_hedge", supportive, [], None)
    combo_baseline = evaluate("long_plus_short_v2_no_monthly_firewall", combo, [], None)

    rows: list[dict[str, Any]] = [supportive_row, combo_baseline]
    for variant in variants()[1:]:
        kept, dropped = apply_firewall(combo, variant)
        rows.append(evaluate(variant.name, kept, dropped, combo_baseline))

    rank_order = {
        "MONTHLY_FIREWALL_REVIEW_CANDIDATE": 0,
        "MONTHLY_FIREWALL_WATCHLIST": 1,
        "MONTHLY_IMPROVES_CORE_BREAKS": 2,
        "BASELINE": 3,
        "REJECT_NO_MONTHLY_REPAIR": 4,
    }
    ranked = sorted(
        rows,
        key=lambda row: (
            rank_order.get(row["decision"], 9),
            -row["positive_months"],
            row["negative_months"],
            row["max_closed_dd"],
            -row["net"],
        ),
    )
    best = ranked[0]
    if best["decision"] == "MONTHLY_FIREWALL_REVIEW_CANDIDATE":
        status = "MONTHLY_FIREWALL_REVIEW_CANDIDATE"
        interpretation = "A bounded source-level monthly firewall reached the review-candidate gate. It must still be implemented and rerun in exact MT5 before demo discussion."
    elif best["decision"] == "MONTHLY_FIREWALL_WATCHLIST":
        status = "MONTHLY_FIREWALL_WATCHLIST"
        interpretation = "A bounded source-level monthly firewall improved month consistency without breaking the core. Keep it as the next exact-MT5 implementation candidate."
    elif best["decision"] == "MONTHLY_IMPROVES_CORE_BREAKS":
        status = "MONTHLY_FIREWALL_SMOOTHING_ONLY"
        interpretation = "Monthly consistency improved, but only by breaking net, payoff, stress, or activity. This is not a usable repair as-is."
    else:
        status = "NO_MONTHLY_FIREWALL_SURVIVOR"
        interpretation = "No source-level monthly firewall materially improved monthly consistency while preserving the profitable book."

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv"
    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "results_csv": rel(results_csv),
        "best_kept_csv": rel(best_kept_csv),
        "best_dropped_csv": rel(best_dropped_csv),
    }
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "boundary": "existing_exact_mt5_ledgers_only_no_runtime_change",
        "inputs": {"supportive_long": rel(SUPPORTIVE_LONG), "long_plus_v2": rel(LONG_PLUS_V2)},
        "baseline_supportive": strip_heavy(supportive_row),
        "combo_baseline": strip_heavy(combo_baseline),
        "best_row": strip_heavy(best),
        "top_rows": [strip_heavy(row) for row in ranked[:20]],
        "all_rows": [strip_heavy(row) for row in ranked],
        "interpretation": interpretation,
        "outputs": outputs,
    }
    write_results(results_csv, ranked)
    write_signal_csv(best_kept_csv, best["kept_rows"])
    write_signal_csv(best_dropped_csv, best["dropped_rows"])
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "best": best["name"],
                "decision": best["decision"],
                "signals": best["signals"],
                "blocked": best["blocked_signals"],
                "wr": best["wr"],
                "wl": best["wl"],
                "stress_030_wl": best["stress_030_wl"],
                "net": best["net"],
                "max_closed_dd": best["max_closed_dd"],
                "positive_months": best["positive_months"],
                "negative_months": best["negative_months"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
