from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta, timezone
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
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STEM = "A1_XAU_M5_NEWS_HYGIENE_DIAGNOSTIC_2026_07_05"
PREREG_PATH = PHASE1_ROOT / "docs" / "A1_XAU_M5_NEWS_HYGIENE_DIAGNOSTIC_PREREG_2026_07_05.md"
STEP3_BEST_KEPT = REPORTS_DIR / "A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_2026_07_05_BEST_KEPT_SIGNALS.csv"

WINDOWS = {
    "BASELINE": None,
    "event_m30_p60": (-30, 60),
    "event_m60_p180": (-60, 180),
    "event_day": "event_day",
}


def parse_dt(value: str) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def read_step3_best_kept() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with STEP3_BEST_KEPT.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for ordinal, row in enumerate(reader, start=2):
            entry_time = parse_dt(str(row["entry_time"]))
            rows.append(
                {
                    "source_id": str(row.get("source_id") or "step3_best_frequency_frontier"),
                    "family_group": str(row.get("family_group") or "step3_best"),
                    "source_priority": int(float(row.get("source_priority") or 0)),
                    "entry_time": entry_time,
                    "entry_date": entry_time.date(),
                    "direction": str(row.get("direction", "")).upper(),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(float(row.get("tickets") or 1)),
                    "lots": float(row.get("lots") or 0.0),
                    "component": str(row.get("component") or ""),
                    "source_csv": str(row.get("source_csv") or STEP3_BEST_KEPT),
                    "source_row": ordinal,
                }
            )
    return rows


def build_portfolios() -> dict[str, list[dict[str, Any]]]:
    specs = build_source_specs()
    sources, _inventory = load_sources(specs)
    portfolios: dict[str, list[dict[str, Any]]] = {
        "step3_best_frequency_frontier": read_step3_best_kept(),
        "step1_compromise_f33_r30_be_1r": sources["step1_f33_r30_be_1r"],
        "step1_high_wr_f67_r20_be_tp1": sources["step1_f67_r20_be_tp1"],
    }
    high_payout_raw: list[dict[str, Any]] = []
    for source_id in (
        "step1_f33_r30_be_never",
        "v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning",
        "orrev_london_firm_stop10",
    ):
        high_payout_raw.extend(sources[source_id])
    portfolios["step3_high_payout_v13_orrev"], _dropped = dedupe_signals(high_payout_raw)
    return portfolios


def build_events(start: date, end: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in range(start.year - 1, end.year + 2):
        for month in range(1, 13):
            rows.append(_event_row(_nth_weekday(year, month, 4, 1), 8, 30, "NFP_FIRST_FRIDAY"))
            rows.append(_event_row(_nth_weekday(year, month, 2, 2), 8, 30, "CPI_SECOND_WEDNESDAY"))
        for month in (1, 3, 5, 6, 7, 9, 11, 12):
            rows.append(_event_row(_nth_weekday(year, month, 2, 3), 14, 0, "FOMC_THIRD_WEDNESDAY"))
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    return [row for row in sorted(rows, key=lambda item: item["timestamp_utc"]) if start_dt <= row["timestamp_utc"] <= end_dt]


def _event_row(local_day: date, hour: int, minute: int, event_type: str) -> dict[str, Any]:
    return {
        "timestamp_utc": _eastern_wall_time_to_utc(local_day, hour, minute).replace(tzinfo=None),
        "event_type": event_type,
        "local_date": local_day.isoformat(),
        "local_time_et": f"{hour:02d}:{minute:02d}",
    }


def _nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (occurrence - 1))


def _eastern_wall_time_to_utc(local_day: date, hour: int, minute: int) -> datetime:
    utc_offset_hours = 4 if _is_us_dst(local_day) else 5
    return datetime(local_day.year, local_day.month, local_day.day, hour, minute, tzinfo=timezone.utc) + timedelta(
        hours=utc_offset_hours
    )


def _is_us_dst(local_day: date) -> bool:
    dst_start = _nth_weekday(local_day.year, 3, 6, 2)
    dst_end = _nth_weekday(local_day.year, 11, 6, 1)
    return dst_start <= local_day < dst_end


def event_lookup(events: list[dict[str, Any]]) -> tuple[list[datetime], set[date]]:
    timestamps = [row["timestamp_utc"] for row in events]
    event_days = {timestamp.date() for timestamp in timestamps}
    return timestamps, event_days


def blocked_by_window(entry_time: datetime, window: object, event_times: list[datetime], event_days: set[date]) -> bool:
    if window is None:
        return False
    if window == "event_day":
        return entry_time.date() in event_days
    before, after = window
    assert isinstance(before, int) and isinstance(after, int)
    for event_time in event_times:
        if event_time + timedelta(minutes=before) <= entry_time <= event_time + timedelta(minutes=after):
            return True
    return False


def apply_window(
    trades: list[dict[str, Any]],
    window: object,
    event_times: list[datetime],
    event_days: set[date],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in trades:
        if blocked_by_window(row["entry_time"], window, event_times, event_days):
            blocked.append(row)
        else:
            kept.append(row)
    return kept, blocked


def classify(row: dict[str, Any]) -> str:
    retention = float(row.get("retention_pct") or 0.0)
    wr = float(row.get("win_rate_pct") or 0.0)
    win_loss = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    pf = float(row.get("profit_factor") or 0.0)
    if retention < 50.0:
        return "FAIL_RETENTION"
    if net <= 0.0:
        return "FAIL_NET"
    if wr >= 50.0 and win_loss >= 2.0 and active >= 90.0:
        return "NEWS_HYGIENE_OWNER_HIT"
    if wr >= 50.0 and win_loss >= 2.0 and active >= 50.0:
        return "NEWS_HYGIENE_CORE_REPLAY_CANDIDATE"
    if wr >= 48.0 and win_loss >= 1.9 and active >= 50.0 and pf >= 1.30 and retention >= 70.0:
        return "NEWS_HYGIENE_NEAR_REPLAY_CANDIDATE"
    return "REJECT_NO_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 350
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.4) * 300
        + min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.1) * 225
        + min(float(row.get("profit_factor") or 0.0) / 1.3, 1.4) * 100
        + min(float(row.get("retention_pct") or 0.0) / 100.0, 1.0) * 50,
        4,
    )


def evaluate(portfolio: str, window_name: str, base_count: int, kept: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    blocked_net = sum(float(row.get("pnl_usd") or 0.0) for row in blocked)
    metrics.update(
        {
            "portfolio": portfolio,
            "window": window_name,
            "blocked_signals": len(blocked),
            "blocked_net_usd": round(blocked_net, 2),
            "retention_pct": round(100.0 * len(kept) / base_count, 2) if base_count else 0.0,
        }
    )
    metrics["decision"] = classify(metrics)
    metrics["score"] = score(metrics)
    return metrics


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "decision",
        "score",
        "portfolio",
        "window",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "net_usd",
        "profit_factor",
        "retention_pct",
        "blocked_signals",
        "blocked_net_usd",
        "active_weekdays",
        "signals_per_active_day",
        "positive_months",
        "negative_months",
        "max_closed_drawdown_usd",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    best = payload["best_row"]
    lines = [
        "# A1 XAU M5 News-Hygiene Diagnostic",
        "",
        "Generated: 2026-07-05",
        "",
        "Scope: offline exact-MT5 trade/signal CSV diagnostic only. No MT5 launch, runtime attach, charts, presets, orders, or broker state mutation.",
        "",
        f"Decision: **{payload['status']}**",
        "",
        "Timezone caveat: MT5 tester timestamps are treated as UTC-like broker-server timestamps for this diagnostic. This is enough to reject weak hygiene effects, not enough for a final news deployment spec.",
        "",
        "## Best Row",
        "",
        f"- Portfolio: `{best.get('portfolio')}`",
        f"- Window: `{best.get('window')}`",
        f"- Decision: `{best.get('decision')}`",
        f"- Signals: {best.get('signals')}",
        f"- WR: {best.get('win_rate_pct')}%",
        f"- Avg win / avg loss: {best.get('avg_win_loss')}",
        f"- Active weekdays: {best.get('active_weekdays')} / {len(MARKET_DAYS)} ({best.get('active_weekday_pct')}%)",
        f"- Net: {best.get('net_usd')}",
        f"- PF: {best.get('profit_factor')}",
        f"- Retention: {best.get('retention_pct')}%",
        f"- Blocked: {best.get('blocked_signals')} signals / {best.get('blocked_net_usd')} USD",
        "",
        "## Rows",
        "",
        "| Rank | Decision | Portfolio | Window | Signals | WR % | W/L | Active % | Net | PF | Retention % | Blocked net |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(payload["rows"], start=1):
        lines.append(
            f"| {rank} | `{row['decision']}` | `{row['portfolio']}` | `{row['window']}` | {row['signals']} | "
            f"{row['win_rate_pct']} | {row['avg_win_loss']} | {row['active_weekday_pct']} | {row['net_usd']} | "
            f"{row['profit_factor']} | {row['retention_pct']} | {row['blocked_net_usd']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            f"CSV: `{rel(Path(payload['outputs']['csv']))}`",
            f"JSON: `{rel(Path(payload['outputs']['json']))}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    portfolios = build_portfolios()
    events = build_events(date(2022, 7, 1), date(2026, 6, 30))
    event_times, event_days = event_lookup(events)
    rows: list[dict[str, Any]] = []
    for portfolio, trades in portfolios.items():
        for window_name, window in WINDOWS.items():
            kept, blocked = apply_window(trades, window, event_times, event_days)
            rows.append(evaluate(portfolio, window_name, len(trades), kept, blocked))

    decision_rank = {
        "NEWS_HYGIENE_OWNER_HIT": 4,
        "NEWS_HYGIENE_CORE_REPLAY_CANDIDATE": 3,
        "NEWS_HYGIENE_NEAR_REPLAY_CANDIDATE": 2,
        "REJECT_NO_OWNER_SHAPE": 1,
        "FAIL_NET": 0,
        "FAIL_RETENTION": 0,
    }
    rows.sort(
        key=lambda row: (
            decision_rank.get(str(row.get("decision")), -1),
            row.get("score") or 0.0,
            row.get("win_rate_pct") or 0.0,
            row.get("avg_win_loss") or 0.0,
            row.get("active_weekday_pct") or 0.0,
        ),
        reverse=True,
    )
    candidates = [row for row in rows if str(row.get("decision", "")).endswith("CANDIDATE") or row.get("decision") == "NEWS_HYGIENE_OWNER_HIT"]
    status = "NEWS_HYGIENE_REJECT_NO_REPLAY_CANDIDATE"
    interpretation = (
        "The fixed deterministic macro-event hygiene windows did not move any tested exact-MT5 Gold portfolio "
        "into the owner or replay-candidate shape. Do not spend reviewer budget or implement a news blocker from this result."
    )
    if candidates:
        status = "NEWS_HYGIENE_REPLAY_CANDIDATE_FOUND"
        interpretation = (
            "At least one offline event-window block reached a replay threshold. This is not promotable by itself; "
            "it would require a real event-calendar spec and exact MT5 replay."
        )

    csv_path = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    payload = {
        "status": status,
        "generated": "2026-07-05",
        "boundary": "offline_exact_mt5_trade_signal_csv_news_hygiene_diagnostic_only_no_mt5_launch",
        "preregistration": str(PREREG_PATH),
        "timezone_caveat": "MT5 tester timestamps treated as UTC-like broker-server timestamps; final deployment would require stronger time/event provenance.",
        "event_count": len(events),
        "event_types": sorted({row["event_type"] for row in events}),
        "windows": WINDOWS,
        "best_row": rows[0],
        "candidate_rows": candidates,
        "rows": rows,
        "interpretation": interpretation,
        "outputs": {"csv": str(csv_path), "json": str(json_path), "markdown": str(md_path)},
    }
    write_csv(csv_path, rows)
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": status, "best_decision": rows[0].get("decision"), "report": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
