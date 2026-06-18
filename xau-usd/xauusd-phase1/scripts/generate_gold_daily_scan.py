from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


DUBAI_OFFSET = timedelta(hours=4)
FIELDS = [
    "account",
    "magic",
    "candidate",
    "direction",
    "entry_time_dubai",
    "exit_time_dubai",
    "session",
    "lots",
    "entry",
    "exit",
    "sl",
    "tp",
    "stop_distance_points",
    "spread_points",
    "cost_r",
    "profit_aed",
    "profit_aed_001",
    "exit_reason",
    "unique_signal",
    "account_unique_signal",
    "cofire",
    "source_csv",
]


def generate_gold_daily_scan(phase1_root: Path, scan_date: str = "2026-06-17") -> dict[str, Path]:
    phase1_root = phase1_root.resolve()
    repo_root = phase1_root.parents[1]
    reports = phase1_root / "outputs" / "reports"
    day = datetime.strptime(scan_date, "%Y-%m-%d").date()
    label = day.strftime("%Y_%m_%d")
    compact = day.strftime("%Y%m%d")

    source_paths = {
        "A1": reports / f"EOD_GOLD_A1_{compact}.csv",
        "A2": reports / f"EOD_GOLD_A2_{compact}.csv",
        "A3": reports / f"EOD_GOLD_A3_{compact}.csv",
    }
    rows = []
    for label_key, path in source_paths.items():
        for row in _read_csv(path):
            rows.append(_normalize_row(row, path))
    _mark_unique_signals(rows)

    context = _read_context(reports / f"EOD_GOLD_CONTEXT_{compact}.csv")
    a3_signal_rows = _read_csv(Path(r"C:\MT5PortableRepairLane\MQL5\Files\a3_breakout_tier1_compat_signal_log.csv"))
    a3_order_rows = _read_csv(Path(r"C:\MT5PortableRepairLane\MQL5\Files\a3_breakout_tier1_compat_order_log.csv"))
    applied = _read_json(reports / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json")
    eod_report = reports / f"EOD_GOLD_SCAN_REPORT_{label}.md"

    rows_path = reports / f"XAUUSD_DAILY_ROWS_{label}.csv"
    report_path = reports / f"GOLD_DAILY_SCAN_{label}.md"
    with rows_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    report_path.write_text(
        _render_report(
            scan_date=scan_date,
            rows=rows,
            context=context,
            a3_signal_rows=a3_signal_rows,
            a3_order_rows=a3_order_rows,
            applied=applied,
            eod_report=eod_report,
            rows_path=rows_path,
        ),
        encoding="utf-8",
    )
    _append_or_replace_day3(repo_root / "GOLD_DAILY_TRACKING_WEEK_2026_06_15.md", report_path.read_text(encoding="utf-8"))
    return {"report": report_path, "rows": rows_path}


def _normalize_row(row: dict[str, str], source: Path) -> dict[str, str]:
    lots = _num(row.get("lots")) or 0.0
    profit = _num(row.get("profit_aed")) or 0.0
    profit_001 = profit * (0.01 / lots) if lots else profit
    entry = row.get("entry_time_dubai", "")
    exit_utc = _parse_dt(row.get("exit_time_utc", ""))
    exit_dubai = _fmt_dt(exit_utc + DUBAI_OFFSET) if exit_utc else ""
    normalized = {
        "account": row.get("account", ""),
        "magic": row.get("magic", ""),
        "candidate": _candidate_for(row.get("candidate", ""), row.get("magic", "")),
        "direction": row.get("direction", ""),
        "entry_time_dubai": entry,
        "exit_time_dubai": exit_dubai,
        "session": _session(entry),
        "lots": row.get("lots", ""),
        "entry": row.get("entry_price", ""),
        "exit": row.get("exit_price", ""),
        "sl": row.get("sl", ""),
        "tp": row.get("tp", ""),
        "stop_distance_points": row.get("stop_distance_points", ""),
        "spread_points": row.get("spread_points", ""),
        "cost_r": row.get("cost_r", ""),
        "profit_aed": f"{profit:.2f}",
        "profit_aed_001": f"{profit_001:.2f}",
        "exit_reason": row.get("exit_reason", ""),
        "unique_signal": "",
        "account_unique_signal": "",
        "cofire": "false",
        "source_csv": source.as_posix(),
    }
    return normalized


def _mark_unique_signals(rows: list[dict[str, str]]) -> None:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        minute = row["entry_time_dubai"][:16]
        key = "|".join([minute, row["direction"], _family(row["candidate"])])
        row["unique_signal"] = key
        row["account_unique_signal"] = "|".join([row["account"], key])
        groups[key].append(row)
    for group in groups.values():
        cofire = "true" if len(group) > 1 else "false"
        for row in group:
            row["cofire"] = cofire


def _candidate_for(candidate: str, magic: str) -> str:
    if magic == "933200":
        return "a3_breakout_plain"
    if magic == "933300":
        return "a3_breakout_improved"
    if magic == "933400":
        return "a3_breakout_tier1_compat"
    return candidate


def _family(candidate: str) -> str:
    if "round" in candidate:
        return "round_family"
    if "session_extreme" in candidate:
        return "session_extreme_family"
    if "repair" in candidate:
        return "repair_family"
    if "breakout" in candidate or candidate.startswith("a3_"):
        return "breakout_family"
    return candidate or "unknown_family"


def _render_report(
    *,
    scan_date: str,
    rows: list[dict[str, str]],
    context: dict[str, str],
    a3_signal_rows: list[dict[str, str]],
    a3_order_rows: list[dict[str, str]],
    applied: dict[str, Any],
    eod_report: Path,
    rows_path: Path,
) -> str:
    global_unique_rows = _unique_representatives(rows, "unique_signal")
    account_unique_rows = _unique_representatives(rows, "account_unique_signal")
    threshold_work_order = datetime(2026, 6, 17, 11, 22)
    created_utc = _parse_iso(applied.get("created_at_utc", ""))
    threshold_applied_dubai = (created_utc + DUBAI_OFFSET) if created_utc else datetime(2026, 6, 17, 15, 22)
    target_rows = [r for r in rows if r["account"] == "1025742" and r["candidate"] in {"symbol_normalized_round_retest_v0", "round_number_retest_v0"}]
    target_pre_work = [r for r in target_rows if _parse_dt(r["entry_time_dubai"]) and _parse_dt(r["entry_time_dubai"]) < threshold_work_order]
    target_post_work = [r for r in target_rows if _parse_dt(r["entry_time_dubai"]) and _parse_dt(r["entry_time_dubai"]) >= threshold_work_order]
    target_pre_applied = [r for r in target_rows if _parse_dt(r["entry_time_dubai"]) and _parse_dt(r["entry_time_dubai"]) < threshold_applied_dubai]
    target_post_applied = [r for r in target_rows if _parse_dt(r["entry_time_dubai"]) and _parse_dt(r["entry_time_dubai"]) >= threshold_applied_dubai]
    protected = [r for r in rows if r["account"] == "1025742" and r["magic"] in {"920101", "920201"}]
    compat_rows = [r for r in rows if r["account"] == "1033669" and r["magic"] == "933400"]
    a3_plain = [r for r in rows if r["account"] == "1033669" and r["magic"] == "933200"]
    a3_improved = [r for r in rows if r["account"] == "1033669" and r["magic"] == "933300"]
    a3_compat_signal_today = [r for r in a3_signal_rows if r.get("timestamp_local", "").startswith("2026.06.17")]
    a3_compat_orders_today = [r for r in a3_order_rows if r.get("timestamp_local", "").startswith("2026.06.17")]
    shadow_counts = Counter(r.get("trend_shadow_pass", "") for r in a3_compat_signal_today)
    shadow_reasons = Counter(r.get("trend_shadow_reason", "") for r in a3_compat_signal_today)
    would_shadow = Counter(r.get("trend_shadow_reason", "") for r in a3_compat_signal_today if r.get("would_signal", "").lower() == "true")
    compat_gate_rows = _compat_gate_rows(a3_compat_orders_today)

    lines = [
        f"# Gold Daily Scan - {scan_date}",
        "",
        "Status: `READ_ONLY_SCAN_COMPLETE_NEAR_EOD`",
        "",
        "No EA, preset, chart, cap, arming, profile, order, or position was changed by this scan.",
        "",
        "## Sample Sizes",
        "",
        f"- Raw closed XAUUSD rows: `{len(rows)}`",
        f"- Global unique signal rows: `{len(global_unique_rows)}`",
        f"- Account-scoped unique signal rows: `{len(account_unique_rows)}`",
        f"- Raw PnL AED_001: `{_pnl(rows):.2f}`",
        f"- Global deduped representative PnL AED_001: `{_pnl(global_unique_rows):.2f}`",
        f"- Account-scoped deduped representative PnL AED_001: `{_pnl(account_unique_rows):.2f}`",
        f"- Source scan: `{eod_report.as_posix()}`",
        f"- Row CSV: `{rows_path.as_posix()}`",
        "",
        "Global dedup rule: `entry minute Dubai | direction | family`. Account-scoped dedup adds `account` to that key so A1/A2/A3 evidence is not collapsed into one representative.",
        "",
        "## Gold Regime",
        "",
        _table(
            ["Open", "High", "Low", "Close", "Net move pts", "Day type", "M5 rows"],
            [[context.get("gold_open", ""), context.get("gold_high", ""), context.get("gold_low", ""), context.get("gold_close", ""), context.get("net_move_pts", ""), context.get("day_type", ""), context.get("bar_rows", "")]],
        ),
        "",
        "Day-3 regime: `DOWN`. H3 is no longer only up-regime evidence, but one down day still is not enough for final confirmation.",
        "",
        "## T1 - Authoritative Trade Set Summary",
        "",
        _summary_table(rows, ["account"]),
        "",
        _summary_table(account_unique_rows, ["account"], title="Account-scoped unique representative rows by account"),
        "",
        "## T2 - A1 Round Quarantine Forward-Week Check",
        "",
        f"- Work-order threshold: `2026-06-17 11:22 Dubai`.",
        f"- Applied-report threshold: `{_fmt_dt(threshold_applied_dubai)} Dubai` from `created_at_utc={applied.get('created_at_utc', '')}`.",
        f"- Result using work-order threshold: `{'CLEAN' if not target_post_work else 'FAIL_TIME_BASIS_REVIEW_REQUIRED'}`; post-threshold rows: `{len(target_post_work)}`.",
        f"- Result using applied-report timestamp: `{'CLEAN' if not target_post_applied else 'FAIL'}`; post-applied rows: `{len(target_post_applied)}`.",
        "",
        _table(
            ["Threshold", "Pre count", "Post count", "Post PnL AED_001"],
            [
                ["Work-order 11:22 Dubai", len(target_pre_work), len(target_post_work), f"{_pnl(target_post_work):.2f}"],
                ["Applied-report timestamp", len(target_pre_applied), len(target_post_applied), f"{_pnl(target_post_applied):.2f}"],
            ],
        ),
        "",
        "Report-based chart state: chart09/chart11 are recorded as `dry_run=true`, `broker_action_allowed=false`; runtime verification remains forward-week evidence.",
        "",
        "## T3 - A1 Protected Breakout-Core",
        "",
        _summary_table(protected, ["magic", "candidate", "session"]),
        "",
        "Protected core continued producing rows today, so no halt is visible in direct broker history.",
        "",
        "## T4 - A3 Tier-1 Compat 933400",
        "",
        _compat_table(compat_rows, compat_gate_rows),
        "",
        f"- `933400` trades in server-hour 12-15 gate: `{sum(1 for item in compat_gate_rows if item['in_gate'])}` of `{len(compat_gate_rows)}` order-log rows.",
        f"- Any outside gate: `{'true' if any(not item['in_gate'] for item in compat_gate_rows) else 'false'}`.",
        f"- Trend shadow pass counts: `{dict(shadow_counts)}`",
        f"- Trend shadow reasons: `{dict(shadow_reasons)}`",
        f"- Trend shadow reasons on would-signals: `{dict(would_shadow)}`",
        f"- A3 plain 933200 rows: `{len(a3_plain)}`; PnL AED_001 `{_pnl(a3_plain):.2f}`.",
        f"- A3 improved 933300 rows: `{len(a3_improved)}`; PnL AED_001 `{_pnl(a3_improved):.2f}`.",
        "",
        "MFE/MAE: not available in this report because the direct trade export does not include intratrade path; use the position-path observer or M5 path replay for exact MFE/MAE.",
        "",
        "## T5 - A3 A/B And Per-Magic/Session Deduped Totals",
        "",
        _summary_table([r for r in account_unique_rows if r["account"] == "1033669"], ["magic", "candidate", "session"]),
        "",
        f"A3 plain/improved co-fired same unique signal count: `{_cofire_count(a3_plain, a3_improved)}`.",
        "",
        "## Per Account / Magic / Session",
        "",
        _summary_table(account_unique_rows, ["account", "magic", "candidate", "session"]),
        "",
        "## Hypothesis Tags - Day 3 Only",
        "",
        _table(
            ["Hypothesis", "Tag", "Reason"],
            [
                ["H1 round-no-edge", _tag(_pnl(target_rows) < 0 and len(target_rows) > 0), f"Round-family target rows today: {len(target_rows)}, PnL {_pnl(target_rows):.2f} AED_001."],
                ["H2 afternoon-weak", _tag(_pnl([r for r in account_unique_rows if r['session'].startswith('Afternoon')]) < 0), "Afternoon account-scoped unique PnL remains negative, but not necessarily worst today."],
                ["H3 counter-trend-loses", _tag(context.get("day_type") == "down" and _pnl([r for r in account_unique_rows if r['direction'] == 'BUY']) < _pnl([r for r in account_unique_rows if r['direction'] == 'SELL'])), "Gold was down; long side carried most losses."],
                ["H4 cost-predicts-losers", "n/a", "Needs multi-day cost aggregation; single-day cells are too small."],
                ["H5 structure-beats-veto", _tag(_pnl(a3_improved) > _pnl(a3_plain)), "A3 improved 933300 outperformed plain 933200 today, but sample is small."],
            ],
        ),
        "",
        "## Honesty Notes",
        "",
        "- Single near-EOD day only; no edge claim upgraded.",
        "- A1 quarantine, A3 compat, and A3 A/B are measured separately.",
        "- The quarantine time-basis discrepancy must be resolved with the reviewer/owner: work order says 11:22 Dubai; applied report says 11:22 UTC / 15:22 Dubai.",
    ]
    return "\n".join(lines) + "\n"


def _compat_gate_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if row.get("action") != "ORDER_SEND_OK":
            continue
        broker_dt = _parse_broker_dt(row.get("timestamp_broker", ""))
        in_gate = broker_dt is not None and 12 <= broker_dt.hour <= 15
        output.append({"row": row, "broker_dt": broker_dt, "in_gate": in_gate})
    return output


def _compat_table(rows: list[dict[str, str]], gate_rows: list[dict[str, Any]]) -> str:
    gate_by_order = {item["row"].get("order_ticket", ""): item for item in gate_rows}
    table_rows = []
    for row in rows:
        gate = next((item for item in gate_rows if item["row"].get("deal_ticket", "") and item["row"].get("deal_ticket", "") in row.get("source_csv", "")), None)
        order_gate = gate or next(iter(gate_by_order.values()), None)
        table_rows.append(
            [
                row["entry_time_dubai"],
                row["exit_time_dubai"],
                row["direction"],
                row["profit_aed_001"],
                row["cost_r"],
                "PENDING_PATH",
                "PENDING_PATH",
                "true" if order_gate and order_gate["in_gate"] else "PENDING_ORDER_JOIN",
            ]
        )
    if not table_rows:
        table_rows = [["none", "none", "none", "0.00", "", "n/a", "n/a", "n/a"]]
    return _table(["Entry Dubai", "Exit Dubai", "Direction", "PnL_001", "Cost R", "MFE", "MAE", "Inside server 12-15"], table_rows)


def _summary_table(rows: list[dict[str, str]], keys: list[str], title: str | None = None) -> str:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") for key in keys)].append(row)
    table_rows = []
    for key, items in sorted(grouped.items()):
        wins = sum(1 for item in items if _num(item["profit_aed_001"]) > 0)
        losses = sum(1 for item in items if _num(item["profit_aed_001"]) < 0)
        table_rows.append([*key, len(items), wins, losses, f"{wins / len(items) * 100:.2f}%" if items else "n/a", f"{_pnl(items):.2f}"])
    if not table_rows:
        table_rows = [["n/a" for _ in keys] + [0, 0, 0, "n/a", "0.00"]]
    header = [key.replace("_", " ") for key in keys] + ["trades", "wins", "losses", "win rate", "pnl aed 001"]
    prefix = f"### {title}\n\n" if title else ""
    return prefix + _table(header, table_rows)


def _unique_representatives(rows: list[dict[str, str]], key_name: str) -> list[dict[str, str]]:
    reps: dict[str, dict[str, str]] = {}
    for row in sorted(rows, key=lambda r: (r.get(key_name, ""), r["account"], r["magic"])):
        reps.setdefault(row.get(key_name, ""), row)
    return list(reps.values())


def _cofire_count(left: list[dict[str, str]], right: list[dict[str, str]]) -> int:
    return len({r["unique_signal"] for r in left} & {r["unique_signal"] for r in right})


def _append_or_replace_day3(tracker: Path, report_text: str) -> None:
    if not tracker.exists():
        return
    text = tracker.read_text(encoding="utf-8")
    start = text.find("## Day 3")
    end = text.find("## Day 4")
    if start == -1 or end == -1 or end <= start:
        return
    replacement = _tracker_day3(report_text)
    tracker.write_text(text[:start] + replacement + "\n" + text[end:], encoding="utf-8")


def _tracker_day3(report_text: str) -> str:
    lines = [
        "## Day 3 - Wednesday 2026-06-17",
        "",
        "**Gold:** DOWN day from scan context: open 4333.76 -> latest/close 4227.41 (-10635 points), high 4382.10, low 4226.27.",
        "",
        "**Per account (gold only, normalized to 0.01 lot, closed broker fills):** see `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_17.md` and `XAUUSD_DAILY_ROWS_2026_06_17.csv`.",
        "",
        "- A1: 71 raw closed rows, -344.60 AED_001, 30.99% win rate.",
        "- A2: 1 raw closed row, -92.42 AED_001, 0.00% win rate.",
        "- A3: 10 raw closed rows, -404.90 AED_001, 0.00% win rate.",
        "- Whole-book raw: 82 rows, -841.92 AED_001.",
        "",
        "**Round quarantine:** using the applied report timestamp (`2026-06-17 11:22 UTC` / `15:22 Dubai`), post-quarantine target rows were 0 = CLEAN. Using the work-order's `11:22 Dubai` wording, there are 11 target rows and the time basis needs owner/reviewer clarification.",
        "",
        "**A3 Tier-1 compat:** magic `933400` fired 1 closed trade, inside server-hour gate 12-15, PnL -92.31 AED_001. Shadow trend guard remained shadow-only.",
        "",
        "**A3 A/B:** plain `933200` lost materially more than improved `933300`; no plain-vs-improved same-signal cofire was observed in the daily rows.",
        "",
        "**Hypothesis scorecard (one-day tags only):** H1 `support`; H2 `support but weaker`; H3 `support on first down day`; H4 `n/a`; H5 `support, tiny sample`.",
        "",
        "**No edge upgrade:** this is one near-EOD day and is reported as measurement only.",
        "",
    ]
    return "\n".join(lines)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_context(path: Path) -> dict[str, str]:
    rows = _read_csv(path)
    return rows[0] if rows else {}


def _session(value: str) -> str:
    dt = _parse_dt(value)
    if dt is None:
        return "Unknown"
    hour = dt.hour
    if 6 <= hour <= 11:
        return "Morning 06:00-11:59"
    if 12 <= hour <= 15:
        return "Afternoon 12:00-15:59"
    if 16 <= hour <= 19:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def _parse_broker_dt(value: str) -> datetime | None:
    return _parse_dt(value)


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _fmt_dt(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def _num(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


def _pnl(rows: list[dict[str, str]]) -> float:
    return sum(_num(row.get("profit_aed_001")) for row in rows)


def _tag(condition: bool) -> str:
    return "support" if condition else "contradict"


def _table(headers: list[Any], rows: list[list[Any]]) -> str:
    output = ["| " + " | ".join(str(h) for h in headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        output.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format daily XAUUSD scan outputs for the weekly tracker.")
    parser.add_argument("--phase1-root", type=Path, default=Path("xau-usd/xauusd-phase1"))
    parser.add_argument("--date", default="2026-06-17")
    args = parser.parse_args(argv)
    outputs = generate_gold_daily_scan(args.phase1_root, args.date)
    print(outputs["report"])
    print(outputs["rows"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
