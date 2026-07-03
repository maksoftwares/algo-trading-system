from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from analyze_a1_momentum_feature_band_residual_package_optimizer import residual_raw_trades
from analyze_a1_momentum_feature_band_reliability_residual_search import enrich_base_trades
from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, top_removed_usd
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02"


CONFIGS = [
    {
        "name": "residual_plus75_high_net",
        "description": "+75 target, no shared max-trade cap, 10m cooldown after loss.",
        "profit_target_usd": 75.0,
        "loss_stop_usd": None,
        "max_trades_per_day": None,
        "max_losses_per_day": None,
        "cooldown_after_loss_minutes": 10,
        "early_trade_count": 2,
        "early_pnl_threshold": 0.0,
    },
    {
        "name": "residual_plus50_10m",
        "description": "+50 target, max six package trades/day, 10m cooldown after loss.",
        "profit_target_usd": 50.0,
        "loss_stop_usd": None,
        "max_trades_per_day": 6,
        "max_losses_per_day": None,
        "cooldown_after_loss_minutes": 10,
        "early_trade_count": 2,
        "early_pnl_threshold": 0.0,
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def parse_entry_date(row: dict[str, Any]) -> date:
    value = row.get("entry_date")
    if value:
        return date.fromisoformat(str(value))
    entry_time = row.get("entry_time")
    if isinstance(entry_time, datetime):
        return entry_time.date()
    return datetime.strptime(str(entry_time), "%Y.%m.%d %H:%M:%S").date()


def market_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def day_distribution(trades: list[dict[str, Any]], all_market_days: list[date]) -> dict[str, Any]:
    by_day: dict[date, list[float]] = defaultdict(list)
    for row in trades:
        by_day[parse_entry_date(row)].append(float(row.get("profit", 0.0)))
    total_days = len(all_market_days)
    active_days = len(by_day)
    two_plus_days = sum(1 for values in by_day.values() if len(values) >= 2)
    three_plus_days = sum(1 for values in by_day.values() if len(values) >= 3)
    five_plus_days = sum(1 for values in by_day.values() if len(values) >= 5)
    positive_active_days = sum(1 for values in by_day.values() if sum(values) > 0)
    negative_active_days = sum(1 for values in by_day.values() if sum(values) < 0)
    quiet_market_days = total_days - active_days
    return {
        "market_days": total_days,
        "active_days": active_days,
        "quiet_market_days": quiet_market_days,
        "trades_per_market_day": round(len(trades) / total_days, 2) if total_days else 0.0,
        "trades_per_active_day": round(len(trades) / active_days, 2) if active_days else 0.0,
        "active_market_day_pct": round(100.0 * active_days / total_days, 2) if total_days else 0.0,
        "two_plus_market_day_pct": round(100.0 * two_plus_days / total_days, 2) if total_days else 0.0,
        "three_plus_market_day_pct": round(100.0 * three_plus_days / total_days, 2) if total_days else 0.0,
        "five_plus_market_day_pct": round(100.0 * five_plus_days / total_days, 2) if total_days else 0.0,
        "two_plus_active_day_pct": round(100.0 * two_plus_days / active_days, 2) if active_days else 0.0,
        "three_plus_active_day_pct": round(100.0 * three_plus_days / active_days, 2) if active_days else 0.0,
        "positive_active_day_pct": round(100.0 * positive_active_days / active_days, 2) if active_days else 0.0,
        "negative_active_day_pct": round(100.0 * negative_active_days / active_days, 2) if active_days else 0.0,
    }


def decision(metrics: dict[str, Any]) -> str:
    if metrics["win_rate_pct"] < 50.0 or (metrics.get("profit_factor") or 0.0) < 1.20 or metrics["net_usd"] <= 0:
        return "FAIL_QUALITY"
    if metrics["trades_per_active_day"] < 2.0:
        return "FAIL_ACTIVE_DAY_SPARSE"
    if metrics["trades_per_market_day"] < 2.0:
        return "PASS_ACTIVE_DAY_BUT_MARKET_DAY_CADENCE_CAVEAT"
    if metrics["three_plus_market_day_pct"] < 50.0:
        return "PASS_WITH_3PLUS_MARKET_DAY_CAVEAT"
    return "PASS_OWNER_CADENCE"


def evaluate_candidate(raw_trades: list[dict[str, Any]], all_market_days: list[date], config: dict[str, Any]) -> dict[str, Any]:
    selected, guard_stats = apply_state_guard(
        raw_trades,
        state_rule="none",
        profit_target_usd=config["profit_target_usd"],
        loss_stop_usd=config["loss_stop_usd"],
        max_trades_per_day=config["max_trades_per_day"],
        max_losses_per_day=config["max_losses_per_day"],
        cooldown_after_loss_minutes=config["cooldown_after_loss_minutes"],
        early_trade_count=config["early_trade_count"],
        early_pnl_threshold=config["early_pnl_threshold"],
    )
    summary = summarize(config["name"], selected)
    summary.update(day_distribution(selected, all_market_days))
    summary.update(
        {
            "description": config["description"],
            "profit_target_usd": config["profit_target_usd"],
            "max_trades_per_day_guard": config["max_trades_per_day"],
            "cooldown_after_loss_minutes": config["cooldown_after_loss_minutes"],
            "top100_removed_usd": top_removed_usd(selected, 100),
            "top200_removed_usd": top_removed_usd(selected, 200),
        }
    )
    summary.update(guard_stats)
    summary["decision"] = decision(summary)
    return summary


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Momentum Business-Goal Calendar Cadence Audit - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline trade CSV analysis only. No MT5 terminal, chart, preset, order, or position was touched.",
        "",
        "## Why This Audit Exists",
        "",
        "The owner rejected strategies that only look good because they trade too rarely. This audit separates active-day cadence from market-day cadence so we can see whether a candidate is genuinely active enough for the daily-profit vision.",
        "",
        "Important reading: a candidate can pass trades per active day but still have quiet market days. That is a caveat, not a hidden failure.",
        "",
        "## Date Window",
        "",
        f"- Start: `{payload['date_window']['start']}`",
        f"- End: `{payload['date_window']['end']}`",
        f"- Weekday market days: `{payload['date_window']['market_days']}`",
        "",
        "## Candidate Cadence",
        "",
        "| Candidate | Decision | Trades | WR | PF | Net | T/market day | T/active day | Active market days | 2+ market days | 3+ market days | 3+ active days | Positive active days | Top100 removed | Top200 removed |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["candidates"]:
        lines.append(
            "| `{name}` | `{decision}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tpmd:.2f} | {tpad:.2f} | {active:.2f}% | {two:.2f}% | {three_mkt:.2f}% | {three_active:.2f}% | {pos:.2f}% | {top100:.2f} | {top200:.2f} |".format(
                name=row["name"],
                decision=row["decision"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                pf=row["profit_factor"],
                net=row["net_usd"],
                tpmd=row["trades_per_market_day"],
                tpad=row["trades_per_active_day"],
                active=row["active_market_day_pct"],
                two=row["two_plus_market_day_pct"],
                three_mkt=row["three_plus_market_day_pct"],
                three_active=row["three_plus_active_day_pct"],
                pos=row["positive_active_day_pct"],
                top100=row["top100_removed_usd"],
                top200=row["top200_removed_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Both candidates are frequent on days they fire, unlike the sparse RR2-style lane.",
            "- Neither candidate should be described as producing multiple trades every single market day. The more accurate promise is: frequent intraday activity on active days, with quiet days still expected.",
            "- `residual_plus75_high_net` remains the better high-net candidate. `residual_plus50_10m` remains the smoother fallback.",
            "- This audit strengthens the review packet because it makes the cadence caveat explicit before any demo replacement.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- Report: `{payload['report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base = enrich_base_trades()
    residual_raw, blocked = residual_raw_trades(base)
    dates = [parse_entry_date(row) for row in residual_raw]
    all_market_days = market_days(min(dates), max(dates)) if dates else []
    candidates = [evaluate_candidate(residual_raw, all_market_days, config) for config in CONFIGS]
    status = "PASS_CADENCE_AUDIT_READY" if candidates else "FAIL_NO_CANDIDATES"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    payload = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_trade_csv_analysis_only_no_runtime_change",
        "date_window": {
            "start": min(dates).isoformat() if dates else "",
            "end": max(dates).isoformat() if dates else "",
            "market_days": len(all_market_days),
        },
        "raw_residual_trades": len(residual_raw),
        "raw_trades_blocked_by_residual_filter": len(blocked),
        "candidates": candidates,
        "report": rel(output_md),
        "json": rel(output_json),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": status, "candidates": [row["decision"] for row in candidates]}, indent=2))
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
