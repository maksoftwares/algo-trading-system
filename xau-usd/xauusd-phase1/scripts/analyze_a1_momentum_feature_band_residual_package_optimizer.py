from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, day_tail_stats, top_removed_usd
from analyze_a1_momentum_feature_band_day_state_search import month_stats
from analyze_a1_momentum_feature_band_reliability_residual_search import as_float, enrich_base_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02"
SPLIT_DATE = datetime(2024, 7, 1)


def residual_filter(row: dict[str, Any]) -> bool:
    if row.get("direction") == "LONG" and row.get("entry_hour") == 18:
        return True
    if row.get("direction") == "SHORT" and as_float(row.get("close_to_recent_extreme")) >= -0.92:
        return True
    return False


def residual_raw_trades(base_trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in base_trades:
        if residual_filter(row):
            blocked.append(row)
        else:
            kept.append(row)
    return kept, blocked


def day_count_distribution(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, int] = defaultdict(int)
    for row in trades:
        by_day[row["entry_date"]] += 1
    active_days = len(by_day)
    return {
        "one_trade_days": sum(1 for count in by_day.values() if count == 1),
        "two_trade_days": sum(1 for count in by_day.values() if count == 2),
        "three_trade_days": sum(1 for count in by_day.values() if count == 3),
        "four_trade_days": sum(1 for count in by_day.values() if count == 4),
        "five_trade_days": sum(1 for count in by_day.values() if count == 5),
        "six_plus_trade_days": sum(1 for count in by_day.values() if count >= 6),
        "two_plus_trade_day_pct": round(
            100.0 * sum(1 for count in by_day.values() if count >= 2) / active_days, 2
        )
        if active_days
        else 0.0,
        "three_plus_trade_day_pct": round(
            100.0 * sum(1 for count in by_day.values() if count >= 3) / active_days, 2
        )
        if active_days
        else 0.0,
    }


def evaluate(
    raw_trades: list[dict[str, Any]],
    *,
    state_rule: str,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
    cooldown_after_loss_minutes: int,
    early_trade_count: int,
    early_pnl_threshold: float,
) -> dict[str, Any]:
    selected, guard_stats = apply_state_guard(
        raw_trades,
        state_rule=state_rule,
        profit_target_usd=profit_target_usd,
        loss_stop_usd=loss_stop_usd,
        max_trades_per_day=max_trades_per_day,
        max_losses_per_day=max_losses_per_day,
        cooldown_after_loss_minutes=cooldown_after_loss_minutes,
        early_trade_count=early_trade_count,
        early_pnl_threshold=early_pnl_threshold,
    )
    name = (
        f"residual|target={profit_target_usd}|loss={loss_stop_usd}|max_trades={max_trades_per_day}|"
        f"max_losses={max_losses_per_day}|cooldown={cooldown_after_loss_minutes}|state={state_rule}|"
        f"early={early_trade_count}:{early_pnl_threshold}"
    )
    older = window_summary("older", selected, None, SPLIT_DATE)
    newer = window_summary("newer", selected, SPLIT_DATE, None)
    summary = summarize(name, selected)
    summary.update(daily_metrics(selected))
    summary.update(day_tail_stats(selected))
    summary.update(month_stats(selected))
    summary.update(day_count_distribution(selected))
    summary.update(guard_stats)
    summary.update(
        {
            "state_rule": state_rule,
            "profit_target_usd": profit_target_usd,
            "loss_stop_usd": loss_stop_usd,
            "max_trades_per_day_guard": max_trades_per_day,
            "max_losses_per_day_guard": max_losses_per_day,
            "cooldown_after_loss_minutes": cooldown_after_loss_minutes,
            "early_trade_count": early_trade_count,
            "early_pnl_threshold": early_pnl_threshold,
            "base_trades": len(raw_trades),
            "retention_pct": round(100.0 * len(selected) / len(raw_trades), 2) if raw_trades else 0.0,
            "older_trades": older.get("trades", 0),
            "older_net_usd": older.get("net_usd", 0.0),
            "older_profit_factor": older.get("profit_factor") or 0.0,
            "newer_trades": newer.get("trades", 0),
            "newer_net_usd": newer.get("net_usd", 0.0),
            "newer_profit_factor": newer.get("profit_factor") or 0.0,
            "top10_removed_usd": top_removed_usd(selected, 10),
            "top25_removed_usd": top_removed_usd(selected, 25),
            "top50_removed_usd": top_removed_usd(selected, 50),
            "top100_removed_usd": top_removed_usd(selected, 100),
            "top200_removed_usd": top_removed_usd(selected, 200),
        }
    )
    summary["decision"] = decision(summary)
    summary["score"] = round(score(summary), 2)
    return summary


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < 1800:
        return "FAIL_SAMPLE"
    if row["active_days"] < 560:
        return "FAIL_ACTIVE_DAYS"
    if row["trades_per_active_day"] < 2.0:
        return "FAIL_SPARSE_STRATEGY_BUSINESS_REQUIREMENT"
    if row["trades_per_active_day"] < 3.0:
        return "FAIL_PREFERRED_DAILY_CADENCE"
    if row["three_plus_trade_day_pct"] < 50.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if row["win_rate_pct"] < 65.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.45:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1700.0:
        return "FAIL_NET"
    if row["positive_day_pct"] < 60.0:
        return "FAIL_POSITIVE_DAY_RATE"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["older_net_usd"] <= 0 or row["newer_net_usd"] <= 0:
        return "FAIL_OLDER_NEWER_SPLIT"
    if row["top200_removed_usd"] <= 0:
        return "REVIEW_TOP200_ROBUSTNESS"
    if row["max_closed_drawdown_usd"] > 110.0:
        return "REVIEW_DRAWDOWN"
    if row["positive_day_pct"] >= 63.0:
        return "RESIDUAL_PACKAGE_UPGRADE_REVIEW_CANDIDATE"
    return "RESIDUAL_PACKAGE_REVIEW_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    cadence = min(float(row.get("trades_per_active_day") or 0.0), 5.0)
    return (
        pf * 1000.0
        + split_pf * 700.0
        + float(row.get("win_rate_pct") or 0.0) * 9.0
        + float(row.get("positive_day_pct") or 0.0) * 65.0
        + float(row.get("three_plus_trade_day_pct") or 0.0) * 12.0
        + cadence * 150.0
        + float(row.get("net_usd") or 0.0) / max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0) * 120.0
        + float(row.get("top100_removed_usd") or 0.0) / 35.0
        + float(row.get("top200_removed_usd") or 0.0) / 30.0
        - max(0.0, -float(row.get("worst_month_usd") or 0.0)) * 0.75
        - max(0.0, float(row.get("max_closed_drawdown_usd") or 0.0) - 90.0) * 2.0
    )


def generate_rows(raw_trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profit_target in [None, 25.0, 50.0, 75.0, 100.0]:
        for loss_stop in [None, -20.0, -25.0, -30.0, -40.0]:
            for max_trades in [6, 8, 10, 12, None]:
                for max_losses in [None, 3, 4, 5]:
                    for cooldown in [0, 5, 10, 15, 20, 30, 45, 60]:
                        rows.append(
                            evaluate(
                                raw_trades,
                                state_rule="none",
                                profit_target_usd=profit_target,
                                loss_stop_usd=loss_stop,
                                max_trades_per_day=max_trades,
                                max_losses_per_day=max_losses,
                                cooldown_after_loss_minutes=cooldown,
                                early_trade_count=2,
                                early_pnl_threshold=0.0,
                            )
                        )
    for state_rule in [
        "first_trade_loss_stop",
        "two_consecutive_losses_stop",
        "first_two_net_negative_stop",
        "first_three_net_negative_stop",
        "early_window_net_negative_stop",
    ]:
        for profit_target in [None, 50.0, 75.0]:
            for max_trades in [6, 8, 10, None]:
                for cooldown in [0, 15, 30]:
                    for threshold in [0.0, -5.0, -10.0]:
                        rows.append(
                            evaluate(
                                raw_trades,
                                state_rule=state_rule,
                                profit_target_usd=profit_target,
                                loss_stop_usd=None,
                                max_trades_per_day=max_trades,
                                max_losses_per_day=None,
                                cooldown_after_loss_minutes=cooldown,
                                early_trade_count=2 if state_rule != "first_three_net_negative_stop" else 3,
                                early_pnl_threshold=threshold,
                            )
                        )
    rank = {
        "RESIDUAL_PACKAGE_UPGRADE_REVIEW_CANDIDATE": 0,
        "RESIDUAL_PACKAGE_REVIEW_CANDIDATE": 1,
        "REVIEW_TOP200_ROBUSTNESS": 2,
        "REVIEW_DRAWDOWN": 3,
    }
    rows.sort(key=lambda row: (rank.get(row["decision"], 9), -row["score"]))
    return rows


def is_frequency_valid(row: dict[str, Any]) -> bool:
    return (
        row.get("trades", 0) >= 1800
        and row.get("active_days", 0) >= 560
        and row.get("trades_per_active_day", 0) >= 3.0
        and row.get("three_plus_trade_day_pct", 0) >= 50.0
        and row.get("win_rate_pct", 0) >= 65.0
        and (row.get("profit_factor") or 0.0) >= 1.45
        and row.get("net_usd", 0) >= 1700.0
        and row.get("positive_day_pct", 0) >= 60.0
        and row.get("top100_removed_usd", 0) > 0
        and row.get("older_net_usd", 0) > 0
        and row.get("newer_net_usd", 0) > 0
    )


def choose_named_candidates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    valid = [row for row in rows if is_frequency_valid(row)]
    if not valid:
        return {}
    max_score = max(valid, key=lambda row: row["score"])
    max_positive_day = max(valid, key=lambda row: (row["positive_day_pct"], row["net_usd"], row["profit_factor"]))
    max_net = max(valid, key=lambda row: (row["net_usd"], row["positive_day_pct"], row["profit_factor"]))
    best_owner_target_50 = [
        row
        for row in valid
        if row.get("profit_target_usd") == 50.0
        and row.get("max_trades_per_day_guard") == 6
        and row.get("loss_stop_usd") is None
    ]
    owner_target_50 = max(
        best_owner_target_50 or valid,
        key=lambda row: (row["positive_day_pct"], row["net_usd"], row["profit_factor"]),
    )
    return {
        "max_score": max_score,
        "max_positive_day": max_positive_day,
        "max_net": max_net,
        "owner_target_50": owner_target_50,
    }


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "name",
        "decision",
        "score",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "two_plus_trade_day_pct",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "median_day_usd",
        "p25_day_usd",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "best_month_usd",
        "top10_removed_usd",
        "top25_removed_usd",
        "top50_removed_usd",
        "top100_removed_usd",
        "top200_removed_usd",
        "max_closed_drawdown_usd",
        "older_trades",
        "older_net_usd",
        "older_profit_factor",
        "newer_trades",
        "newer_net_usd",
        "newer_profit_factor",
        "state_rule",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "cooldown_after_loss_minutes",
        "early_trade_count",
        "early_pnl_threshold",
        "retention_pct",
        "skipped_trades",
        "profit_target_days",
        "loss_stop_days",
        "trade_cap_days",
        "loss_count_days",
        "state_stop_days",
        "cooldown_skipped_trades",
    ]
    return {key: row.get(key) for key in keys}


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = list(compact(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(compact(row))


def render(
    rows: list[dict[str, Any]],
    named: dict[str, dict[str, Any]],
    raw_count: int,
    blocked_count: int,
    output_json: Path,
    output_csv: Path,
) -> str:
    top = rows[:25]
    accepted = [row for row in rows if row["decision"] == "RESIDUAL_PACKAGE_UPGRADE_REVIEW_CANDIDATE"]
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Residual Package Optimizer - 2026-07-02",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: offline MT5 Strategy Tester trade CSV and signal-log analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner wants a frequent intraday engine, not a sparse high-PF system. This search keeps the residual-filtered signal base and varies only daily package controls to see if daily reliability can improve without starving trade count.",
        "",
        "Hard business-fit veto: fail any row below 2 trades per active day. Preferred cadence: at least 3 trades per active day and at least 50% 3+ trade active days.",
        "",
        "## Search Universe",
        "",
        f"- Residual-filtered raw trades before package guard: `{raw_count}`",
        f"- Raw trades blocked by residual filter before package guard: `{blocked_count}`",
        f"- Rows searched: `{len(rows)}`",
        f"- Upgrade review candidates: `{len(accepted)}`",
        "",
        "## Named Candidates",
        "",
        "| Role | Target | Max trades | Max losses | Cooldown | Trades | WR % | Net | PF | T/active | 3+ day % | Pos day % | Top100 | Top200 | DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    role_labels = {
        "max_score": "Best balanced score",
        "max_positive_day": "Best positive-day rate",
        "max_net": "Best net",
        "owner_target_50": "Best +50 target row",
    }
    for role, row in named.items():
        lines.append(
            "| {role} | {target} | {max_trades} | {max_losses} | {cooldown} | {trades} | {wr:.2f} | {net:.2f} | {pf} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {top100:.2f} | {top200:.2f} | {dd:.2f} |".format(
                role=role_labels.get(role, role),
                target=row.get("profit_target_usd"),
                max_trades=row.get("max_trades_per_day_guard"),
                max_losses=row.get("max_losses_per_day_guard"),
                cooldown=row.get("cooldown_after_loss_minutes"),
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                top100=row["top100_removed_usd"],
                top200=row["top200_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
            )
        )
    lines.extend(
        [
            "",
        "## Top Rows",
        "",
        "| Rank | Decision | Target | Loss stop | Max trades | Max losses | Cooldown | State | Trades | WR % | Net | PF | T/active | 2+ day % | 3+ day % | Pos day % | Top100 | Top200 | DD | Older PF/net | Newer PF/net |",
        "|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | {target} | {loss} | {max_trades} | {max_losses} | {cooldown} | `{state}` | {trades} | {wr:.2f} | {net:.2f} | {pf} | {tpa:.2f} | {two:.2f} | {three:.2f} | {pos:.2f} | {top100:.2f} | {top200:.2f} | {dd:.2f} | {opf:.2f}/{onet:.2f} | {npf:.2f}/{nnet:.2f} |".format(
                rank=index,
                decision=row["decision"],
                target=row.get("profit_target_usd"),
                loss=row.get("loss_stop_usd"),
                max_trades=row.get("max_trades_per_day_guard"),
                max_losses=row.get("max_losses_per_day_guard"),
                cooldown=row.get("cooldown_after_loss_minutes"),
                state=row.get("state_rule"),
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                tpa=row["trades_per_active_day"],
                two=row["two_plus_trade_day_pct"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                top100=row["top100_removed_usd"],
                top200=row["top200_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                opf=row["older_profit_factor"],
                onet=row["older_net_usd"],
                npf=row["newer_profit_factor"],
                nnet=row["newer_net_usd"],
            )
        )
    best = rows[0] if rows else {}
    lines.extend(
        [
            "",
            "## Current Best Interpretation",
            "",
            f"- Best decision: `{best.get('decision', 'MISSING')}`",
            f"- Best row: `{best.get('name', '')}`",
            f"- This is still a review candidate, not attachment approval.",
            "- If a row improves daily smoothness by reducing cadence below the owner's useful range, it is rejected even if PF improves.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{output_json}`",
            f"- CSV: `{output_csv}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base_trades = enrich_base_trades()
    residual_raw, blocked = residual_raw_trades(base_trades)
    rows = generate_rows(residual_raw)
    named = choose_named_candidates(rows)

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"

    payload = {
        "status": "RESIDUAL_PACKAGE_OPTIMIZER_COMPLETE",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "business_requirement": {
            "hard_min_trades_per_active_day": 2.0,
            "preferred_min_trades_per_active_day": 3.0,
            "preferred_min_three_plus_trade_day_pct": 50.0,
            "sparse_strategy_policy": "Fail any strategy that wins by becoming too selective.",
        },
        "raw_residual_trades_before_package_guard": len(residual_raw),
        "raw_trades_blocked_by_residual_filter": len(blocked),
        "searched_rows": len(rows),
        "best": compact(rows[0]) if rows else {},
        "named_candidates": {name: compact(row) for name, row in named.items()},
        "upgrade_review_candidates": [
            compact(row) for row in rows if row["decision"] == "RESIDUAL_PACKAGE_UPGRADE_REVIEW_CANDIDATE"
        ][:25],
        "top_rows": [compact(row) for row in rows[:50]],
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(rows, output_csv)
    output_md.write_text(render(rows, named, len(residual_raw), len(blocked), output_json, output_csv), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": payload["status"], "best": payload["best"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
