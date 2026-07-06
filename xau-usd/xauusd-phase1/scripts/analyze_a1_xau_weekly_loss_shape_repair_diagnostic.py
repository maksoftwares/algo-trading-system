from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
PREREG_PATH = PHASE1_ROOT / "docs" / "A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_PREREG_2026_07_05.md"
BASE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
OUTPUT_STEM = "A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05"

WINDOW_START = date(2022, 7, 1)
WINDOW_END = date(2026, 6, 30)
JUNE_START = date(2026, 6, 1)
JUNE_END = date(2026, 6, 30)
H4_SOURCES = {"h4_d1_long_best_box2_atr80", "h4_d1_long_broad_box3_atr60"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def market_days(start: date, end: date) -> list[str]:
    days: list[str] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def market_weeks(start: date, end: date) -> list[str]:
    weeks: list[str] = []
    seen: set[str] = set()
    current = start
    while current <= end:
        if current.weekday() < 5:
            monday = current - timedelta(days=current.weekday())
            key = monday.isoformat()
            if key not in seen:
                seen.add(key)
                weeks.append(key)
        current += timedelta(days=1)
    return weeks


MARKET_DAYS = market_days(WINDOW_START, WINDOW_END)
MARKET_WEEKS = market_weeks(WINDOW_START, WINDOW_END)
JUNE_MARKET_DAYS = market_days(JUNE_START, JUNE_END)
JUNE_MARKET_WEEKS = market_weeks(JUNE_START, JUNE_END)


def week_key(value: date) -> str:
    return (value - timedelta(days=value.weekday())).isoformat()


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def load_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with BASE_KEPT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=2):
            entry_time = parse_time(row["entry_time"])
            item = dict(row)
            item["entry_time_dt"] = entry_time
            item["entry_date_obj"] = entry_time.date()
            item["entry_week"] = week_key(entry_time.date())
            item["pnl_value"] = float(row["pnl_usd"])
            item["original_pnl_value"] = float(row["pnl_usd"])
            item["ledger_row"] = index
            rows.append(item)
    return sorted(rows, key=lambda item: (item["entry_time_dt"], item["source_priority"], item["component_priority"]))


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def profit_factor(values: list[float]) -> float | None:
    wins = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses <= 0:
        return None
    return wins / losses


def summarize(rows: list[dict[str, Any]], market_day_list: list[str], market_week_list: list[str]) -> dict[str, Any]:
    values = [float(row["pnl_value"]) for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    day_set = set(market_day_list)
    week_set = set(market_week_list)
    active_days = {row["entry_date_obj"].isoformat() for row in rows if row["entry_date_obj"].isoformat() in day_set}
    weekly_net = {week: 0.0 for week in market_week_list}
    for row in rows:
        week = str(row["entry_week"])
        if week in week_set:
            weekly_net[week] += float(row["pnl_value"])
    positive_weeks = sum(1 for value in weekly_net.values() if value > 0)
    negative_weeks = sum(1 for value in weekly_net.values() if value < 0)
    flat_weeks = len(weekly_net) - positive_weeks - negative_weeks
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = -sum(losses) / len(losses) if losses else 0.0
    return {
        "signals": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": 100.0 * len(wins) / len(rows) if rows else 0.0,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_win_loss": avg_win / avg_loss if avg_loss else None,
        "profit_factor": profit_factor(values),
        "net_usd": sum(values),
        "max_dd_usd": max_drawdown(values),
        "active_weekdays": len(active_days),
        "active_weekday_pct": 100.0 * len(active_days) / len(market_day_list) if market_day_list else 0.0,
        "positive_weeks": positive_weeks,
        "negative_weeks": negative_weeks,
        "flat_weeks": flat_weeks,
        "positive_week_pct": 100.0 * positive_weeks / len(market_week_list) if market_week_list else 0.0,
        "worst_week_usd": min(weekly_net.values()) if weekly_net else 0.0,
        "best_week_usd": max(weekly_net.values()) if weekly_net else 0.0,
    }


def june_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if JUNE_START <= row["entry_date_obj"] <= JUNE_END]


def june_week_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nets = {week: 0.0 for week in JUNE_MARKET_WEEKS}
    trades = {week: 0 for week in JUNE_MARKET_WEEKS}
    wins = {week: 0 for week in JUNE_MARKET_WEEKS}
    losses = {week: 0 for week in JUNE_MARKET_WEEKS}
    for row in june_rows(rows):
        week = str(row["entry_week"])
        if week not in nets:
            continue
        value = float(row["pnl_value"])
        nets[week] += value
        trades[week] += 1
        if value > 0:
            wins[week] += 1
        elif value < 0:
            losses[week] += 1
    return [
        {
            "week": week,
            "trades": trades[week],
            "wins": wins[week],
            "losses": losses[week],
            "net_usd": round(nets[week], 4),
        }
        for week in JUNE_MARKET_WEEKS
    ]


def round_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in metrics.items():
        out[key] = round(value, 4) if isinstance(value, float) else value
    return out


def apply_h4_day_cap(rows: list[dict[str, Any]], cap: int) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    kept: list[dict[str, Any]] = []
    for row in rows:
        source = str(row["upstream_source_id"])
        if source in H4_SOURCES:
            key = (source, row["entry_date_obj"].isoformat())
            if counts.get(key, 0) >= cap:
                continue
            counts[key] = counts.get(key, 0) + 1
        kept.append(deepcopy(row))
    return kept


def apply_h4_week_cap(rows: list[dict[str, Any]], cap: int) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    kept: list[dict[str, Any]] = []
    for row in rows:
        source = str(row["upstream_source_id"])
        if source in H4_SOURCES:
            key = (source, str(row["entry_week"]))
            if counts.get(key, 0) >= cap:
                continue
            counts[key] = counts.get(key, 0) + 1
        kept.append(deepcopy(row))
    return kept


def apply_h4_day_week_cap(rows: list[dict[str, Any]], day_cap: int, week_cap: int) -> list[dict[str, Any]]:
    day_counts: dict[tuple[str, str], int] = {}
    week_counts: dict[tuple[str, str], int] = {}
    kept: list[dict[str, Any]] = []
    for row in rows:
        source = str(row["upstream_source_id"])
        if source in H4_SOURCES:
            day_key = (source, row["entry_date_obj"].isoformat())
            week_key_value = (source, str(row["entry_week"]))
            if day_counts.get(day_key, 0) >= day_cap or week_counts.get(week_key_value, 0) >= week_cap:
                continue
            day_counts[day_key] = day_counts.get(day_key, 0) + 1
            week_counts[week_key_value] = week_counts.get(week_key_value, 0) + 1
        kept.append(deepcopy(row))
    return kept


def apply_loss_cap(rows: list[dict[str, Any]], cap: float, scope: str) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for row in rows:
        item = deepcopy(row)
        source = str(item["upstream_source_id"])
        applies = scope == "all" or source in H4_SOURCES
        if applies and float(item["pnl_value"]) < -cap:
            item["pnl_value"] = -cap
            item["pnl_usd"] = f"{-cap:.2f}"
        kept.append(item)
    return kept


def decide(row: dict[str, Any], baseline: dict[str, Any], kind: str) -> str:
    if kind == "sensitivity":
        return "SENSITIVITY_ONLY_NOT_EXECUTABLE"
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    pos_improvement = float(row.get("positive_week_pct") or 0.0) - float(baseline.get("positive_week_pct") or 0.0)
    worst_improved = float(row.get("worst_week_usd") or 0.0) >= 0.75 * float(baseline.get("worst_week_usd") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 86.0 and pos_improvement >= 5.0 and worst_improved:
        return "REPAIR_CANDIDATE_REQUIRES_EXACT_MT5"
    if (pos_improvement > 0 or worst_improved) and not (wr >= 50.0 and wl >= 2.0 and active >= 86.0):
        return "LOSS_SHAPE_IMPROVES_CORE_BREAKS"
    return "REJECT_NO_WEEKLY_REPAIR"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 250
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.2) * 250
        + min(float(row.get("active_weekday_pct") or 0.0) / 86.0, 1.2) * 150
        + min(float(row.get("positive_week_pct") or 0.0) / 70.0, 1.2) * 250
        + min((float(row.get("worst_week_usd") or 0.0) + 700.0) / 700.0, 1.2) * 100,
        4,
    )


def evaluate(name: str, kind: str, rows: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    metrics = round_metrics(summarize(rows, MARKET_DAYS, MARKET_WEEKS))
    june = round_metrics(summarize(june_rows(rows), JUNE_MARKET_DAYS, JUNE_MARKET_WEEKS))
    dropped = len(BASE_ROWS) - len(rows)
    out = {
        "name": name,
        "kind": kind,
        **metrics,
        "dropped_signals": dropped,
        "june_signals": june["signals"],
        "june_win_rate_pct": june["win_rate_pct"],
        "june_avg_win_loss": june["avg_win_loss"],
        "june_active_weekday_pct": june["active_weekday_pct"],
        "june_net_usd": june["net_usd"],
        "june_positive_week_pct": june["positive_week_pct"],
        "june_worst_week_usd": june["worst_week_usd"],
    }
    out["decision"] = "BASELINE" if kind == "baseline" else decide(out, baseline, kind)
    out["score"] = score(out)
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def serializable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["entry_time"] = item["entry_time_dt"].strftime("%Y-%m-%d %H:%M:%S")
        item["entry_date"] = item["entry_date_obj"].isoformat()
        item["pnl_usd"] = f"{float(item['pnl_value']):.2f}"
        item.pop("entry_time_dt", None)
        item.pop("entry_date_obj", None)
        item.pop("pnl_value", None)
        item.pop("original_pnl_value", None)
        return_keys = [
            "component",
            "source_id",
            "upstream_source_id",
            "variant_name",
            "entry_time",
            "entry_date",
            "entry_week",
            "direction",
            "pnl_usd",
            "tickets",
            "lots",
            "source_csv",
            "source_row",
            "ledger_row",
        ]
        out.append({key: item.get(key, "") for key in return_keys})
    return out


def format_metric(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"
    return str(value)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    global BASE_ROWS
    BASE_ROWS = load_rows()
    baseline = round_metrics(summarize(BASE_ROWS, MARKET_DAYS, MARKET_WEEKS))

    variants: list[tuple[str, str, list[dict[str, Any]]]] = [("baseline", "baseline", deepcopy(BASE_ROWS))]
    for cap in (1, 2):
        variants.append((f"h4_max_{cap}_per_day", "causal_entry_count", apply_h4_day_cap(BASE_ROWS, cap)))
    for cap in (1, 2, 3):
        variants.append((f"h4_max_{cap}_per_week", "causal_entry_count", apply_h4_week_cap(BASE_ROWS, cap)))
    for day_cap, week_cap in ((1, 1), (1, 2), (1, 3), (2, 2), (2, 3)):
        variants.append(
            (
                f"h4_max_{day_cap}_per_day_and_{week_cap}_per_week",
                "causal_entry_count",
                apply_h4_day_week_cap(BASE_ROWS, day_cap, week_cap),
            )
        )
    for cap in (50.0, 75.0, 100.0):
        variants.append((f"h4_loss_cap_{cap:.0f}_sensitivity", "sensitivity", apply_loss_cap(BASE_ROWS, cap, "h4")))
    for cap in (50.0, 75.0, 100.0):
        variants.append((f"all_loss_cap_{cap:.0f}_sensitivity", "sensitivity", apply_loss_cap(BASE_ROWS, cap, "all")))

    results: list[dict[str, Any]] = []
    rows_by_name: dict[str, list[dict[str, Any]]] = {}
    june_weeks_by_name: dict[str, list[dict[str, Any]]] = {}
    for name, kind, rows in variants:
        row = evaluate(name, kind, rows, baseline)
        results.append(row)
        rows_by_name[name] = rows
        june_weeks_by_name[name] = june_week_rows(rows)

    results.sort(key=lambda row: (row["decision"] == "BASELINE", float(row["score"])), reverse=True)
    causal = [row for row in results if row["kind"] == "causal_entry_count"]
    sensitivities = [row for row in results if row["kind"] == "sensitivity"]
    best_causal = max(causal, key=lambda row: float(row["score"])) if causal else {}
    best_sensitivity = max(sensitivities, key=lambda row: float(row["score"])) if sensitivities else {}

    csv_path = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    kept_path = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_CAUSAL_KEPT.csv"
    june_week_path = REPORTS_DIR / f"{OUTPUT_STEM}_JUNE_WEEK_TABLE.csv"

    write_csv(csv_path, results)
    write_csv(kept_path, serializable_rows(rows_by_name.get(str(best_causal.get("name")), [])))
    week_rows: list[dict[str, Any]] = []
    for row_name in ("baseline", str(best_causal.get("name")), str(best_sensitivity.get("name"))):
        if not row_name or row_name == "None":
            continue
        for item in june_weeks_by_name.get(row_name, []):
            out = dict(item)
            out["row"] = row_name
            week_rows.append(out)
    write_csv(june_week_path, week_rows)

    verdict = "NO_CAUSAL_WEEKLY_REPAIR"
    if any(row["decision"] == "REPAIR_CANDIDATE_REQUIRES_EXACT_MT5" for row in causal):
        verdict = "CAUSAL_WEEKLY_REPAIR_CANDIDATE_FOUND"

    payload = {
        "status": verdict,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "prereg": rel(PREREG_PATH),
        "base_kept": rel(BASE_KEPT),
        "baseline": next(row for row in results if row["name"] == "baseline"),
        "best_causal": best_causal,
        "best_sensitivity": best_sensitivity,
        "reports": {
            "md": rel(md_path),
            "json": rel(json_path),
            "csv": rel(csv_path),
            "best_causal_kept_csv": rel(kept_path),
            "june_week_csv": rel(june_week_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def table_rows(rows: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        for rank, row in enumerate(rows, start=1):
            lines.append(
                "| {rank} | `{decision}` | `{kind}` | `{name}` | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {positive_week_pct:.2f} | {worst_week_usd:.2f} | {net_usd:.2f} | {june_net_usd:.2f} | {june_worst_week_usd:.2f} |".format(
                    rank=rank,
                    **row,
                )
            )
        return lines

    top_causal = sorted(causal, key=lambda row: float(row["score"]), reverse=True)[:8]
    top_sensitivity = sorted(sensitivities, key=lambda row: float(row["score"]), reverse=True)[:8]
    baseline_row = next(row for row in results if row["name"] == "baseline")
    md_lines = [
        "# A1 XAU Weekly Loss-Shape Repair Diagnostic - 2026-07-05",
        "",
        f"Status: `{verdict}`",
        "",
        "Scope: exact-ledger diagnostic only. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{rel(PREREG_PATH)}`",
        f"Base kept ledger: `{rel(BASE_KEPT)}`",
        "",
        "## Baseline Weekly Problem",
        "",
        "| Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {positive_week_pct:.2f} | {worst_week_usd:.2f} | {net_usd:.2f} | {june_net_usd:.2f} | {june_worst_week_usd:.2f} |".format(
            **baseline_row
        ),
        "",
        "## Best Causal Entry-Count Row",
        "",
        "| Decision | Row | Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| `{decision}` | `{name}` | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {positive_week_pct:.2f} | {worst_week_usd:.2f} | {net_usd:.2f} | {june_net_usd:.2f} | {june_worst_week_usd:.2f} |".format(
            **best_causal
        ),
        "",
        "## Causal Rows",
        "",
        "| Rank | Decision | Kind | Row | Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        *table_rows(top_causal),
        "",
        "## Loss-Cap Sensitivity Rows",
        "",
        "These rows are not executable claims and cannot justify promotion. They show how much loss geometry would need to change.",
        "",
        "| Rank | Decision | Kind | Row | Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        *table_rows(top_sensitivity),
        "",
        "## June Week Table",
        "",
        "| Row | Week | Trades | Wins | Losses | Net |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in week_rows:
        md_lines.append(
            "| `{row}` | {week} | {trades} | {wins} | {losses} | {net_usd:.2f} |".format(**row)
        )
    md_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{verdict}`",
            "- Causal H4/D1 entry-count caps are implementable in principle, but only qualify if they preserve the owner core metrics and materially improve weekly loss shape.",
            "- Loss-cap rows are sensitivity-only; they point toward stop/risk geometry work, not a deployable rule.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- CSV: `{rel(csv_path)}`",
            f"- Best causal kept CSV: `{rel(kept_path)}`",
            f"- June week CSV: `{rel(june_week_path)}`",
            f"- Report: `{rel(md_path)}`",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"wrote {md_path}", flush=True)


BASE_ROWS: list[dict[str, Any]] = []


if __name__ == "__main__":
    main()
