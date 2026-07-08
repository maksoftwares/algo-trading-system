from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import (
    LONG_PLUS_V2,
    PREREG as _MONTHLY_FIREWALL_PREREG,
    max_closed_drawdown,
    month_key,
    month_shape,
    read_ledger,
    source_group,
    weekly_shape,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import write_signal_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_202207_202606"


@dataclass(frozen=True)
class Variant:
    name: str
    group: str
    lookback_months: int
    net_lt: float | None = None
    losses_ge: int | None = None


def previous_month(value: str) -> str:
    year, month = (int(part) for part in value.split("-"))
    month -= 1
    if month == 0:
        year -= 1
        month = 12
    return f"{year:04d}-{month:02d}"


def lookback_months(entry_month: str, count: int) -> list[str]:
    months: list[str] = []
    current = entry_month
    for _ in range(count):
        current = previous_month(current)
        months.append(current)
    return months


def variants() -> list[Variant]:
    out = [Variant("long_plus_short_v2_no_source_health_gate", "none", 1)]
    for threshold in (-1.0, -25.0, -50.0, -75.0, -100.0, -150.0, -200.0):
        out.append(Variant(f"h4_prev1_net_lt_{abs(int(threshold))}", "h4_core", 1, net_lt=threshold))
    for losses in (1, 2, 3, 4, 5, 8, 10):
        out.append(Variant(f"h4_prev1_losses_ge_{losses}", "h4_core", 1, losses_ge=losses))
    for threshold in (-25.0, -50.0, -100.0):
        out.append(Variant(f"h4_prev2_net_lt_{abs(int(threshold))}", "h4_core", 2, net_lt=threshold))
    for threshold in (-75.0, -100.0, -150.0, -200.0):
        out.append(Variant(f"freq_prev1_net_lt_{abs(int(threshold))}", "frequency", 1, net_lt=threshold))
    for threshold in (-25.0, -50.0, -100.0):
        out.append(Variant(f"freq_prev2_net_lt_{abs(int(threshold))}", "frequency", 2, net_lt=threshold))
    return out


def apply_gate(rows: list[dict[str, Any]], variant: Variant) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if variant.group == "none":
        return list(rows), []

    state: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"pnl": 0.0, "losses": 0})
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []

    # The rule is month-to-month, so closed trades from earlier rows can be recorded immediately
    # by their close month; entries later in the same month never inspect that same month.
    for row in sorted(rows, key=lambda item: (item["entry_time"], item["source_priority"], item["source_id"])):
        group = source_group(row)
        entry_month = month_key(row["entry_date"])
        block = False
        observed_months = lookback_months(entry_month, variant.lookback_months)
        if group == variant.group:
            net = sum(float(state[(group, item)]["pnl"]) for item in observed_months)
            losses = sum(int(state[(group, item)]["losses"]) for item in observed_months)
            if variant.net_lt is not None and net < variant.net_lt:
                block = True
            if variant.losses_ge is not None and losses >= variant.losses_ge:
                block = True
        if block:
            item = dict(row)
            item["source_group"] = group
            item["drop_reason"] = variant.name
            dropped.append(item)
            continue

        kept.append(row)
        close_month = month_key(row["exit_date"])
        bucket = state[(group, close_month)]
        pnl = float(row["pnl_usd"])
        bucket["pnl"] += pnl
        if pnl < 0.0:
            bucket["losses"] += 1

    return kept, dropped


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
        and core_ok
        and row["max_closed_dd"] <= baseline["max_closed_dd"] * 0.90
    )
    if review_ok:
        return "SOURCE_HEALTH_REVIEW_CANDIDATE"
    if row["positive_months"] >= baseline["positive_months"] + 2 and core_ok:
        return "SOURCE_HEALTH_WATCHLIST"
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
        "# A1 XAU Previous-Month Source Health Gate Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: causal previous-month source-health gates over existing exact-MT5 ledgers only. No MT5 launch, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        "",
        "## Best Rows",
        "",
        "| Rank | Rule | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {index} | `{row['name']}` | `{row['decision']}` | {row['signals']} | {row['blocked_signals']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {row['positive_week_pct']:.2f} | "
            f"`{row['worst_month']}` | {row['worst_month_net']:.2f} |"
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
    if not LONG_PLUS_V2.exists():
        raise FileNotFoundError(LONG_PLUS_V2)
    if not _MONTHLY_FIREWALL_PREREG.exists():
        raise FileNotFoundError(_MONTHLY_FIREWALL_PREREG)

    combo = read_ledger(LONG_PLUS_V2)
    baseline_rows, baseline_dropped = apply_gate(combo, variants()[0])
    baseline = evaluate("long_plus_short_v2_no_source_health_gate", baseline_rows, baseline_dropped, None)

    rows = [baseline]
    for variant in variants()[1:]:
        kept, dropped = apply_gate(combo, variant)
        rows.append(evaluate(variant.name, kept, dropped, baseline))

    rank_order = {
        "SOURCE_HEALTH_REVIEW_CANDIDATE": 0,
        "SOURCE_HEALTH_WATCHLIST": 1,
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
            -row["net"],
        ),
    )
    best = ranked[0]
    if best["decision"] == "SOURCE_HEALTH_REVIEW_CANDIDATE":
        status = "SOURCE_HEALTH_REVIEW_CANDIDATE"
        interpretation = "A previous-month source-health gate reached the review-candidate gate. It needs exact-MT5 implementation and review before any demo discussion."
    elif best["decision"] == "SOURCE_HEALTH_WATCHLIST":
        status = "SOURCE_HEALTH_WATCHLIST"
        interpretation = "A previous-month source-health gate improved monthly consistency while preserving the profitable core. This is the next exact-MT5 implementation candidate."
    elif best["decision"] == "MONTHLY_IMPROVES_CORE_BREAKS":
        status = "SOURCE_HEALTH_SMOOTHING_ONLY"
        interpretation = "Monthly consistency improved, but core/net/activity broke. Treat it as a clue only."
    else:
        status = "NO_SOURCE_HEALTH_GATE_SURVIVOR"
        interpretation = "No previous-month source-health gate improved monthly consistency while preserving the profitable core."

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
        "input": rel(LONG_PLUS_V2),
        "baseline": strip_heavy(baseline),
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
