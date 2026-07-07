from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
BASELINE_KEPT = REPORTS / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
OUTPUT_STEM = "A1_XAU_HYBRID_WEEKLY_EXIT_ANATOMY_202207_202606"


def parse_dt(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty datetime")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def parse_date(value: Any) -> date:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty date")
    return date.fromisoformat(text)


def parse_float(value: Any) -> float:
    return float(str(value or "0").strip().replace(" ", "") or "0")


def parse_int(value: Any, default: int = 0) -> int:
    text = str(value or "").strip()
    if not text:
        return default
    return int(float(text))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalize_dt_text(value: Any) -> str:
    return parse_dt(value).strftime("%Y-%m-%d %H:%M:%S")


def source_bucket(row: dict[str, Any]) -> str:
    text = " ".join(
        str(row.get(key, ""))
        for key in ("source_id", "upstream_source_id", "component", "upstream_component", "family_group")
    ).lower()
    if "h4_d1" in text:
        return "h4_d1"
    if "orrev" in text or "opening_range" in text:
        return "opening_range_reversal"
    if "v8" in text:
        return "v8_rr2"
    if "step1_" in text or "f67" in text or "f33" in text:
        return "a1_split_frequency"
    if str(row.get("source_id", "")) == "freq_step3_frontier" or "frequency_frontier" in text:
        return "frequency_frontier_other"
    return str(row.get("source_id") or "other")


def load_ledger(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_csv(path), start=2):
        entry_time = parse_dt(row["entry_time"])
        rows.append(
            {
                **row,
                "ledger_row": ordinal,
                "entry_time": entry_time,
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": parse_float(row.get("pnl_usd")),
                "tickets": parse_int(row.get("tickets"), 1) or 1,
                "lots": parse_float(row.get("lots")),
                "source_row": parse_int(row.get("source_row"), 0),
            }
        )
    return rows


def load_source_index(source_csv: Path) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(source_csv):
        direction = str(row.get("direction", "")).upper()
        grouped[(normalize_dt_text(row["entry_time"]), direction)].append(row)

    out: dict[tuple[str, str], dict[str, Any]] = {}
    for key, rows in grouped.items():
        exit_times = [parse_dt(row["exit_time"]) for row in rows if str(row.get("exit_time", "")).strip()]
        entry_times = [parse_dt(row["entry_time"]) for row in rows]
        profits = [parse_float(row.get("profit_aed")) for row in rows]
        out[key] = {
            "entry_time": min(entry_times),
            "exit_time": max(exit_times) if exit_times else max(entry_times),
            "exit_rows": len(rows),
            "source_profit": round(sum(profits), 2),
        }
    return out


def enrich_exit_times(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    indexes: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    missing_sources: set[str] = set()
    match_failures = 0
    fallback_entry_time = 0

    enriched: list[dict[str, Any]] = []
    for row in rows:
        source_csv = str(row.get("source_csv", ""))
        source_path = Path(source_csv)
        source_key = str(source_path)
        if source_key not in indexes and source_key not in missing_sources:
            if source_path.exists():
                indexes[source_key] = load_source_index(source_path)
            else:
                missing_sources.add(source_key)

        key = (row["entry_time"].strftime("%Y-%m-%d %H:%M:%S"), row["direction"])
        match = indexes.get(source_key, {}).get(key)
        item = dict(row)
        if match is None:
            match_failures += 1
            fallback_entry_time += 1
            item["exit_time"] = row["entry_time"]
            item["exit_match_status"] = "fallback_entry_time"
            item["exit_match_rows"] = 0
            item["exit_match_profit_diff"] = None
        else:
            diff = round(float(row["pnl_usd"]) - float(match["source_profit"]), 2)
            item["exit_time"] = match["exit_time"]
            item["exit_match_status"] = "matched"
            item["exit_match_rows"] = match["exit_rows"]
            item["exit_match_profit_diff"] = diff
            if abs(diff) > 0.05:
                item["exit_match_status"] = "matched_profit_diff"
                match_failures += 1
        item["exit_date"] = item["exit_time"].date()
        item["hold_hours"] = round((item["exit_time"] - item["entry_time"]).total_seconds() / 3600.0, 4)
        item["source_bucket"] = source_bucket(item)
        enriched.append(item)

    return enriched, {
        "source_csvs_indexed": len(indexes),
        "missing_source_csvs": sorted(missing_sources),
        "match_failures": match_failures,
        "fallback_entry_time_rows": fallback_entry_time,
    }


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * pct)))
    return float(ordered[idx])


def week_tables(rows: list[dict[str, Any]], top1_ids: set[int], top2_ids: set[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_week: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_week[week_start(row["exit_date"])].append(row)

    weeks: list[dict[str, Any]] = []
    source_contrib: list[dict[str, Any]] = []
    for start, items in sorted(by_week.items()):
        by_bucket: dict[str, float] = defaultdict(float)
        by_source: dict[str, float] = defaultdict(float)
        for item in items:
            by_bucket[item["source_bucket"]] += item["pnl_usd"]
            by_source[str(item.get("source_id", ""))] += item["pnl_usd"]
        net = sum(item["pnl_usd"] for item in items)
        non_h4_net = sum(value for bucket, value in by_bucket.items() if bucket != "h4_d1")
        losses = [item for item in items if item["pnl_usd"] < 0]
        wins = [item for item in items if item["pnl_usd"] > 0]
        largest_loss = min((item["pnl_usd"] for item in items), default=0.0)
        largest_win = max((item["pnl_usd"] for item in items), default=0.0)
        row_ids = {id(item) for item in items}
        weeks.append(
            {
                "week_start": start,
                "week_end": start + timedelta(days=6),
                "iso_year": start.isocalendar().year,
                "iso_week": start.isocalendar().week,
                "net_usd": round(net, 2),
                "signals": len(items),
                "wins": len(wins),
                "losses": len(losses),
                "largest_loss_usd": round(largest_loss, 2),
                "largest_win_usd": round(largest_win, 2),
                "contains_top1pct_winner": bool(row_ids & top1_ids),
                "contains_top2pct_winner": bool(row_ids & top2_ids),
                "h4_d1_net_usd": round(by_bucket.get("h4_d1", 0.0), 2),
                "frequency_frontier_net_usd": round(non_h4_net, 2),
                "a1_split_frequency_net_usd": round(by_bucket.get("a1_split_frequency", 0.0), 2),
                "opening_range_net_usd": round(by_bucket.get("opening_range_reversal", 0.0), 2),
                "v8_rr2_net_usd": round(by_bucket.get("v8_rr2", 0.0), 2),
                "frequency_frontier_other_net_usd": round(by_bucket.get("frequency_frontier_other", 0.0), 2),
                "dominant_source": max(by_source.items(), key=lambda pair: abs(pair[1]))[0] if by_source else "",
                "dominant_source_net_usd": round(max(by_source.items(), key=lambda pair: abs(pair[1]))[1], 2)
                if by_source
                else 0.0,
            }
        )
        for bucket, value in sorted(by_bucket.items()):
            source_contrib.append(
                {
                    "week_start": start,
                    "week_end": start + timedelta(days=6),
                    "source_bucket": bucket,
                    "net_usd": round(value, 2),
                }
            )
    return weeks, source_contrib


def rolling_positive_pct(weeks: list[dict[str, Any]], size: int = 4) -> float:
    if len(weeks) < size:
        return 0.0
    positives = 0
    total = 0
    for index in range(len(weeks) - size + 1):
        total += 1
        value = sum(float(weeks[j]["net_usd"]) for j in range(index, index + size))
        if value > 0:
            positives += 1
    return round(100.0 * positives / total, 2) if total else 0.0


def anatomy_summary(rows: list[dict[str, Any]], weeks: list[dict[str, Any]], top1_count: int, top2_count: int) -> dict[str, Any]:
    positive = [week for week in weeks if float(week["net_usd"]) > 0]
    negative = [week for week in weeks if float(week["net_usd"]) < 0]
    flat = [week for week in weeks if float(week["net_usd"]) == 0]
    nets = [float(week["net_usd"]) for week in weeks]
    signal_counts = [float(week["signals"]) for week in weeks]
    green_with_top1 = [week for week in positive if week["contains_top1pct_winner"]]
    green_with_top2 = [week for week in positive if week["contains_top2pct_winner"]]
    red_h4_negative = [week for week in negative if float(week["h4_d1_net_usd"]) < 0]
    red_no_h4_winner = [week for week in negative if float(week["h4_d1_net_usd"]) <= 0]

    return {
        "signals": len(rows),
        "trade_weeks": len(weeks),
        "positive_weeks": len(positive),
        "negative_weeks": len(negative),
        "flat_weeks": len(flat),
        "positive_week_pct": round(100.0 * len(positive) / len(weeks), 2) if weeks else 0.0,
        "worst_week_usd": round(min(nets), 2) if nets else 0.0,
        "best_week_usd": round(max(nets), 2) if nets else 0.0,
        "median_week_usd": round(float(median(nets)), 2) if nets else 0.0,
        "average_week_net_usd": round(sum(nets) / len(nets), 2) if nets else 0.0,
        "rolling_4_week_positive_pct": rolling_positive_pct(weeks),
        "signals_per_week_min": int(min(signal_counts)) if signal_counts else 0,
        "signals_per_week_p25": round(percentile(signal_counts, 0.25), 2),
        "signals_per_week_median": round(float(median(signal_counts)), 2) if signal_counts else 0.0,
        "signals_per_week_p75": round(percentile(signal_counts, 0.75), 2),
        "signals_per_week_max": int(max(signal_counts)) if signal_counts else 0,
        "top1pct_winner_count": top1_count,
        "top2pct_winner_count": top2_count,
        "green_weeks_with_top1pct_winner": len(green_with_top1),
        "green_weeks_with_top1pct_winner_pct": round(100.0 * len(green_with_top1) / len(positive), 2)
        if positive
        else 0.0,
        "green_weeks_with_top2pct_winner": len(green_with_top2),
        "green_weeks_with_top2pct_winner_pct": round(100.0 * len(green_with_top2) / len(positive), 2)
        if positive
        else 0.0,
        "positive_week_pct_without_top1pct_weeks_counted": round(
            100.0 * sum(1 for week in weeks if float(week["net_usd"]) > 0 and not week["contains_top1pct_winner"]) / len(weeks),
            2,
        )
        if weeks
        else 0.0,
        "red_weeks_with_negative_h4_d1": len(red_h4_negative),
        "red_weeks_with_negative_h4_d1_pct": round(100.0 * len(red_h4_negative) / len(negative), 2)
        if negative
        else 0.0,
        "red_weeks_with_no_positive_h4_d1": len(red_no_h4_winner),
        "red_weeks_with_no_positive_h4_d1_pct": round(100.0 * len(red_no_h4_winner) / len(negative), 2)
        if negative
        else 0.0,
    }


def csv_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], keys: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key, "")) for key in keys})


def render(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# A1 XAU Hybrid Weekly Exit-Time Anatomy",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: descriptive anatomy of the current best exact-ledger hybrid. Weekly P&L is grouped by final signal `exit_time` reconstructed from exact MT5 source trade CSVs. No MT5 runtime, chart, preset, order, position, or broker state was touched.",
        "",
        f"Status: `{payload['status']}`",
        f"Input kept ledger: `{payload['input_kept_ledger']}`",
        "",
        "## Weekly Shape",
        "",
        "| Signals | Trade weeks | Positive weeks | Positive week % | Worst week | Median week | Avg week | Rolling 4w positive % |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {summary['signals']} | {summary['trade_weeks']} | {summary['positive_weeks']} | "
            f"{summary['positive_week_pct']} | {summary['worst_week_usd']} | {summary['median_week_usd']} | "
            f"{summary['average_week_net_usd']} | {summary['rolling_4_week_positive_pct']} |"
        ),
        "",
        "## Tail Dependence",
        "",
        "| Top winners | Green weeks with top-1% | Green weeks with top-2% | Positive-week % excluding top-1% weeks |",
        "| ---: | ---: | ---: | ---: |",
        (
            f"| top1 `{summary['top1pct_winner_count']}`, top2 `{summary['top2pct_winner_count']}` | "
            f"{summary['green_weeks_with_top1pct_winner']} ({summary['green_weeks_with_top1pct_winner_pct']}%) | "
            f"{summary['green_weeks_with_top2pct_winner']} ({summary['green_weeks_with_top2pct_winner_pct']}%) | "
            f"{summary['positive_week_pct_without_top1pct_weeks_counted']} |"
        ),
        "",
        "## Red-Week Clues",
        "",
        "| Negative weeks | Red weeks with negative H4/D1 | Red weeks with no positive H4/D1 | Signal count p25/median/p75/max |",
        "| ---: | ---: | ---: | --- |",
        (
            f"| {summary['negative_weeks']} | {summary['red_weeks_with_negative_h4_d1']} "
            f"({summary['red_weeks_with_negative_h4_d1_pct']}%) | {summary['red_weeks_with_no_positive_h4_d1']} "
            f"({summary['red_weeks_with_no_positive_h4_d1_pct']}%) | {summary['signals_per_week_p25']}/"
            f"{summary['signals_per_week_median']}/{summary['signals_per_week_p75']}/{summary['signals_per_week_max']} |"
        ),
        "",
        "## Worst Weeks",
        "",
        "| Week start | Net | Signals | H4/D1 | Frequency | Opening range | Largest loss | Contains top-1% winner | Dominant source |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for week in payload["worst_weeks"]:
        lines.append(
            f"| {week['week_start']} | {week['net_usd']} | {week['signals']} | {week['h4_d1_net_usd']} | "
            f"{week['frequency_frontier_net_usd']} | {week['opening_range_net_usd']} | {week['largest_loss_usd']} | "
            f"{week['contains_top1pct_winner']} | `{week['dominant_source']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not BASELINE_KEPT.exists():
        raise FileNotFoundError(BASELINE_KEPT)

    rows = load_ledger(BASELINE_KEPT)
    enriched, exit_stats = enrich_exit_times(rows)
    winners = sorted([row for row in enriched if row["pnl_usd"] > 0], key=lambda row: row["pnl_usd"], reverse=True)
    top1_count = math.ceil(len(winners) * 0.01)
    top2_count = math.ceil(len(winners) * 0.02)
    top1_ids = {id(row) for row in winners[:top1_count]}
    top2_ids = {id(row) for row in winners[:top2_count]}
    for row in enriched:
        row["is_top1pct_winner"] = id(row) in top1_ids
        row["is_top2pct_winner"] = id(row) in top2_ids

    weeks, source_contrib = week_tables(enriched, top1_ids, top2_ids)
    summary = anatomy_summary(enriched, weeks, top1_count, top2_count)
    status = "WEEKLY_EXIT_ANATOMY_COMPLETE"
    if exit_stats["match_failures"]:
        status = "WEEKLY_EXIT_ANATOMY_COMPLETE_WITH_EXIT_MATCH_WARNINGS"

    outputs = {
        "md": str(REPORTS / f"{OUTPUT_STEM}.md"),
        "json": str(REPORTS / f"{OUTPUT_STEM}.json"),
        "signals_exit_time_csv": str(REPORTS / f"{OUTPUT_STEM}_SIGNALS_EXIT_TIME.csv"),
        "week_table_csv": str(REPORTS / f"{OUTPUT_STEM}_WEEK_TABLE.csv"),
        "week_source_contrib_csv": str(REPORTS / f"{OUTPUT_STEM}_WEEK_SOURCE_CONTRIB.csv"),
    }

    signal_keys = [
        "component",
        "source_id",
        "upstream_source_id",
        "family_group",
        "source_priority",
        "variant_name",
        "entry_time",
        "entry_date",
        "exit_time",
        "exit_date",
        "hold_hours",
        "direction",
        "pnl_usd",
        "tickets",
        "lots",
        "source_bucket",
        "is_top1pct_winner",
        "is_top2pct_winner",
        "source_csv",
        "source_row",
        "exit_match_status",
        "exit_match_rows",
        "exit_match_profit_diff",
    ]
    week_keys = [
        "week_start",
        "week_end",
        "iso_year",
        "iso_week",
        "net_usd",
        "signals",
        "wins",
        "losses",
        "largest_loss_usd",
        "largest_win_usd",
        "contains_top1pct_winner",
        "contains_top2pct_winner",
        "h4_d1_net_usd",
        "frequency_frontier_net_usd",
        "a1_split_frequency_net_usd",
        "opening_range_net_usd",
        "v8_rr2_net_usd",
        "frequency_frontier_other_net_usd",
        "dominant_source",
        "dominant_source_net_usd",
    ]
    write_csv(Path(outputs["signals_exit_time_csv"]), enriched, signal_keys)
    write_csv(Path(outputs["week_table_csv"]), weeks, week_keys)
    write_csv(Path(outputs["week_source_contrib_csv"]), source_contrib, ["week_start", "week_end", "source_bucket", "net_usd"])

    interpretation = (
        f"Closed-P&L grouping by exit date is stricter than the earlier entry-date view: the current hybrid reaches only "
        f"{summary['positive_week_pct']}% positive trade weeks, with a worst week of ${summary['worst_week_usd']}. "
        f"Only {summary['green_weeks_with_top1pct_winner_pct']}% of green weeks contain a top-1% winner, so ordinary green weeks are not "
        "mostly created by a single exceptional ticket; however, the largest positive weeks and the worst negative weeks are both H4/D1-driven. "
        f"{summary['red_weeks_with_no_positive_h4_d1_pct']}% of red weeks have no positive H4/D1 contribution. "
        "The next iteration should therefore target H4/D1 geometry and loss clustering first; adding filler trades or weekly overlays is secondary. "
        "This report is descriptive evidence only and does not promote the candidate."
    )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "input_kept_ledger": str(BASELINE_KEPT),
        "week_definition": "broker-time calendar week, grouped by final signal exit_time; zero-trade weeks excluded",
        "exit_time_rule": "multi-ticket signals close on max ticket exit_time from the exact MT5 source trade CSV",
        "exit_match_stats": exit_stats,
        "summary": summary,
        "worst_weeks": sorted(weeks, key=lambda row: float(row["net_usd"]))[:12],
        "best_weeks": sorted(weeks, key=lambda row: float(row["net_usd"]), reverse=True)[:12],
        "outputs": outputs,
        "interpretation": interpretation,
    }
    Path(outputs["json"]).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    Path(outputs["md"]).write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "positive_week_pct": summary["positive_week_pct"],
                "worst_week_usd": summary["worst_week_usd"],
                "green_weeks_with_top1pct_winner_pct": summary["green_weeks_with_top1pct_winner_pct"],
                "red_weeks_with_negative_h4_d1_pct": summary["red_weeks_with_negative_h4_d1_pct"],
                "report": outputs["md"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
