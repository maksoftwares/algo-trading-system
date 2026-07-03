from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
BACKTEST_DIR = (
    REPORTS
    / "mt5_backtests"
    / "a1_momentum_variants_freq_first_v4_four_year_2022_07_2026_06_20260701"
)
BASE_NAME = (
    "A1XauM5Momentum_FREQ_FIRST_V4_FOUR_YEAR_2022_07_2026_06_XAUUSD_M5_"
    "freq_h1_h4_long_rr0p7_v4_combo_rank1"
)
TRADE_CSV = BACKTEST_DIR / f"{BASE_NAME}_trades.csv"
ORDER_CSV = BACKTEST_DIR / f"{BASE_NAME}_orders.csv"
SIGNAL_CSV = BACKTEST_DIR / f"{BASE_NAME}_signals.csv"
VERDICT_JSON = REPORTS / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.json"
DEFAULT_OUTPUT_MD = REPORTS / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_REVIEW_PACKET_2026_07_02.md"
DEFAULT_OUTPUT_JSON = REPORTS / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_REVIEW_PACKET_2026_07_02.json"
DEFAULT_PROMPT = REPO_ROOT / "CLAUDE_REVIEW_PROMPT_A1_MOMENTUM_FREQUENCY_FIRST_2026_07_02.md"
SPEC_DOC = PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_LONG_RR0P7_V4_COMBO_RANK1_FORWARD_2026_07_02.md"
SPEC_HASH = PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_LONG_RR0P7_V4_COMBO_RANK1_FORWARD_2026_07_02.sha256.json"


def read_comma_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_tab_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(" ", ""))
    except ValueError:
        return default


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def aggregate(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    items = list(rows)
    pnl = [fnum(item.get("profit_usd", item.get("profit_aed", 0.0))) for item in items]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "trades": len(items),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(items), 2) if items else 0.0,
        "net_usd": round(sum(pnl), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "avg_usd": round(sum(pnl) / len(items), 4) if items else 0.0,
    }


def bucket(value: float, ranges: list[tuple[float | None, float | None, str]]) -> str:
    for lower, upper, label in ranges:
        if lower is not None and value < lower:
            continue
        if upper is not None and value > upper:
            continue
        return label
    return "unbucketed"


def summarize_by(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    out = []
    for name, items in sorted(groups.items()):
        item = {"bucket": name, **aggregate(items)}
        out.append(item)
    return out


def top_rows(rows: list[dict[str, Any]], count: int, reverse: bool) -> list[dict[str, Any]]:
    return [
        {
            "entry_time": row["entry_time"],
            "exit_time": row["exit_time"],
            "profit_usd": round(row["profit_usd"], 2),
            "hour": row["entry_hour"],
            "session": row["entry_session"],
            "estimated_cost_r": row.get("estimated_cost_r"),
            "stop_points": row.get("stop_points"),
            "atr": row.get("atr"),
            "three_bar_move_atr": row.get("three_bar_move_atr"),
            "break_distance_atr": row.get("break_distance_atr"),
        }
        for row in sorted(rows, key=lambda item: item["profit_usd"], reverse=reverse)[:count]
    ]


def enrich_trades() -> list[dict[str, Any]]:
    trades = read_comma_csv(TRADE_CSV)
    orders = read_tab_csv(ORDER_CSV)
    signals = read_tab_csv(SIGNAL_CSV)

    order_by_deal = {
        row.get("deal_ticket", ""): row
        for row in orders
        if row.get("action") == "ORDER_SEND_OK" and row.get("deal_ticket")
    }
    signal_by_time = {
        row.get("timestamp_broker", ""): row
        for row in signals
        if row.get("stage") == "WOULD_SIGNAL"
    }

    enriched: list[dict[str, Any]] = []
    for trade in trades:
        order = order_by_deal.get(trade.get("entry_deal", ""), {})
        signal = signal_by_time.get(order.get("timestamp_broker", trade.get("entry_time", "")), {})
        entry = parse_dt(trade["entry_time"])
        exit_time = parse_dt(trade["exit_time"])
        duration_minutes = max(0.0, (exit_time - entry).total_seconds() / 60.0)
        row: dict[str, Any] = {
            **trade,
            "profit_usd": fnum(trade.get("profit_aed")),
            "entry_hour": int(trade.get("entry_hour", entry.hour)),
            "month": trade["entry_time"][:7],
            "year": trade["entry_time"][:4],
            "duration_minutes": duration_minutes,
            "duration_bucket": bucket(
                duration_minutes,
                [
                    (None, 15, "<=15m"),
                    (15, 30, "15-30m"),
                    (30, 60, "30-60m"),
                    (60, 180, "1-3h"),
                    (180, None, ">3h"),
                ],
            ),
            "spread_points": fnum(order.get("spread_points")),
            "stop_points": fnum(order.get("stop_points")),
            "estimated_cost_r": fnum(order.get("estimated_cost_r")),
            "atr": fnum(signal.get("atr")),
            "body_fraction": fnum(signal.get("body_fraction")),
            "close_location": fnum(signal.get("close_location")),
            "three_bar_move_atr": fnum(signal.get("three_bar_move_atr")),
            "break_distance_atr": fnum(signal.get("break_distance_atr")),
        }
        row["cost_bucket"] = bucket(
            row["estimated_cost_r"],
            [
                (None, 0.015, "<=0.015R"),
                (0.015, 0.03, "0.015-0.03R"),
                (0.03, 0.04, "0.03-0.04R"),
                (0.04, 0.05, "0.04-0.05R"),
                (0.05, None, ">0.05R"),
            ],
        )
        row["stop_bucket"] = bucket(
            row["stop_points"],
            [
                (None, 350, "<=350pt"),
                (350, 500, "350-500pt"),
                (500, 700, "500-700pt"),
                (700, 1000, "700-1000pt"),
                (1000, None, ">1000pt"),
            ],
        )
        row["atr_bucket"] = bucket(
            row["atr"],
            [
                (None, 1.2, "<=1.2"),
                (1.2, 1.8, "1.2-1.8"),
                (1.8, 2.5, "1.8-2.5"),
                (2.5, 3.5, "2.5-3.5"),
                (3.5, None, ">3.5"),
            ],
        )
        row["move_bucket"] = bucket(
            row["three_bar_move_atr"],
            [
                (None, 0.8, "<=0.8ATR"),
                (0.8, 1.2, "0.8-1.2ATR"),
                (1.2, 1.8, "1.2-1.8ATR"),
                (1.8, 2.5, "1.8-2.5ATR"),
                (2.5, None, ">2.5ATR"),
            ],
        )
        row["break_bucket"] = bucket(
            row["break_distance_atr"],
            [
                (None, 0.3, "<=0.3ATR"),
                (0.3, 0.6, "0.3-0.6ATR"),
                (0.6, 1.0, "0.6-1.0ATR"),
                (1.0, None, ">1.0ATR"),
            ],
        )
        enriched.append(row)
    return enriched


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def render_prompt(output_md: Path, output_json: Path) -> str:
    return f"""# Claude Review Request - A1 XAU M5 Momentum Frequency-First Candidate

Please independently review Codex's latest high-frequency XAUUSD M5 candidate. Be skeptical about overfitting, but keep the project objective in view: we need multiple trades per active day, win rate above 50%, and positive expectancy. Sparse two-trade-per-month strategies do not satisfy the business goal even if they look robust.

Primary review packet:
- `{output_md}`
- `{output_json}`
- `{PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md"}`
- `{SPEC_DOC}`
- `{SPEC_HASH}`

Primary source files:
- `{TRADE_CSV}`
- `{ORDER_CSV}`
- `{SIGNAL_CSV}`
- `{VERDICT_JSON}`

Candidate under review:
- `freq_h1_h4_long_rr0p7_v4_combo_rank1`
- LONG-only XAUUSD M5 momentum continuation
- H1+H4 EMA alignment required
- target `0.7R`
- `cost_R <= 0.05`
- blocked server hours `2,9,10,11,12,13,17,19,21,23`
- max `12` trades/day
- cooldown `5` minutes

Please do the following:
1. Recompute the headline numbers from the source CSVs: 1132 trades, 65.90% WR, +1042.07 USD, PF 1.45, 383 active entry days, 2.96 trades/active entry day, 36 positive months / 11 negative active months.
2. Verify the OOS split: older window `2022.07-2024.06` has 520 trades, 65.00% WR, +309.24, PF 1.40; recent window `2024.07-2026.06` has 612 trades, 66.67% WR, +732.83, PF 1.47.
3. Challenge whether blocking server hours `2,9,10,11,12,13,17,19,21,23` is justified, whether this is overfit from the hour-combination search, and whether V3's higher PF should be preferred over V4's higher frequency.
4. Review the loss anatomy: hours, months, duration, ATR, stop size, cost_R, break strength, and outlier dependence.
5. Tell us exactly what would make this candidate fail despite the attractive WR/frequency profile.
6. If you endorse it, provide the exact frozen forward-demo spec and kill rules. If you revise/reject, provide the next most promising repair path that preserves trade frequency.

Additional provenance/companion diagnostics:
- Hour-combination search: `{PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.md"}`
- Short-side companion diagnostic: `{PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_SHORT_COMPANION_DIAGNOSTIC_2026_07_02.md"}`
- Codex conclusion: V4 is the primary review candidate. Short-side companions should remain diagnostic-only because practical short variants failed the older OOS split.

Important boundary:
- Do not recommend live trading or real capital.
- Do not treat this as canonical Phase 2 approval.
- Demo forward test only, minimum lot, no mid-test tuning.
"""


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Momentum Frequency-First V4 Review Packet - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Purpose",
        "",
        "The owner clarified that sparse RR2-style results do not satisfy the project objective. "
        "This packet reviews the strongest high-frequency candidate found so far: multiple trades on active days, win rate above 50%, and positive net result across MT5 every-tick windows.",
        "",
        "No live/demo runtime was changed by this analysis.",
        "",
        "## Candidate",
        "",
        table(
            [
                {"Field": "Variant", "Value": payload["candidate"]["name"]},
                {"Field": "Direction", "Value": "LONG only"},
                {"Field": "Symbol / TF", "Value": "XAUUSD / M5"},
                {"Field": "Trend filter", "Value": "H1+H4 EMA20/50 aligned"},
                {"Field": "Target", "Value": "0.7R"},
                {"Field": "Cost cap", "Value": "<=0.05R"},
                {"Field": "Blocked hours", "Value": "2,9,10,11,12,13,17,19,21,23"},
                {"Field": "Max trades/day", "Value": "12"},
                {"Field": "Cooldown", "Value": "5 minutes"},
            ],
            ["Field", "Value"],
        ),
        "",
        "## Headline Results",
        "",
        table(payload["window_results"], ["window", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "## Four-Year Stability",
        "",
        table(
            [
                {"Metric": "Active days", "Value": payload["stability"]["active_days"]},
                {"Metric": "Avg trades / active day", "Value": payload["stability"]["avg_trades_active_day"]},
                {"Metric": "Positive days", "Value": payload["stability"]["positive_days"]},
                {"Metric": "Negative days", "Value": payload["stability"]["negative_days"]},
                {"Metric": "Positive months", "Value": payload["stability"]["positive_months"]},
                {"Metric": "Negative months", "Value": payload["stability"]["negative_months"]},
            ],
            ["Metric", "Value"],
        ),
        "",
        "## Outlier Dependence",
        "",
        table([payload["outliers"]], ["net_usd", "top_1", "top_5_sum", "top_10_sum", "net_ex_top_5", "net_ex_top_10"]),
        "",
        "## Loss Anatomy",
        "",
        "### By Entry Session",
        "",
        table(payload["by_session"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By Entry Hour",
        "",
        table(payload["by_hour"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By Duration",
        "",
        table(payload["by_duration"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By Estimated Cost R",
        "",
        table(payload["by_cost"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By Stop Size",
        "",
        table(payload["by_stop"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By M5 ATR",
        "",
        table(payload["by_atr"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By 3-Bar Momentum",
        "",
        table(payload["by_move"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "### By Break Distance",
        "",
        table(payload["by_break"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "## Worst Days",
        "",
        table(payload["worst_days"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "## Best Days",
        "",
        table(payload["best_days"], ["bucket", "trades", "win_rate_pct", "net_usd", "profit_factor", "avg_usd"]),
        "",
        "## Biggest Losses",
        "",
        table(payload["biggest_losses"], ["entry_time", "exit_time", "profit_usd", "hour", "session", "estimated_cost_r", "stop_points", "atr", "three_bar_move_atr", "break_distance_atr"]),
        "",
        "## Biggest Wins",
        "",
        table(payload["biggest_wins"], ["entry_time", "exit_time", "profit_usd", "hour", "session", "estimated_cost_r", "stop_points", "atr", "three_bar_move_atr", "break_distance_atr"]),
        "",
        "## Current Verdict",
        "",
        "- This candidate is much closer to the original goal than RR2 because it trades often and keeps win rate above 50%.",
        "- It is not promoted yet. V4 is a filter chosen from an offline hour-combination search and then rerun exactly in MT5, so independent review must challenge whether the hour mask is overfit and whether V3's higher PF is preferable.",
        "- The next valid step is independent review, then a frozen minimum-lot demo forward test if accepted.",
        "",
        "## Source Hashes",
        "",
        table(payload["source_hashes"], ["file", "sha256"]),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate review packet for A1 momentum frequency-first candidate.")
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--prompt-output", type=Path, default=DEFAULT_PROMPT)
    args = parser.parse_args()

    rows = enrich_trades()
    verdict = json.loads(VERDICT_JSON.read_text(encoding="utf-8"))
    profits = sorted([row["profit_usd"] for row in rows], reverse=True)
    net = sum(profits)

    by_day = summarize_by(rows, "date")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_PACKET_READY_NOT_PROMOTED",
        "candidate": verdict["repaired_variant"],
        "window_results": [
            {
                "window": result["period"],
                "trades": result["trades"],
                "win_rate_pct": result["win_rate_pct"],
                "net_usd": result["pnl_aed"],
                "profit_factor": result["profit_factor"],
                "avg_usd": round(result["pnl_aed"] / result["trades"], 4),
            }
            for result in verdict["window_results"]
        ],
        "stability": {
            "active_days": len(by_day),
            "avg_trades_active_day": round(len(rows) / len(by_day), 2),
            "positive_days": sum(1 for row in by_day if row["net_usd"] > 0),
            "negative_days": sum(1 for row in by_day if row["net_usd"] < 0),
            "positive_months": verdict["repaired_variant"]["positive_months"],
            "negative_months": verdict["repaired_variant"]["negative_months"],
        },
        "outliers": {
            "net_usd": round(net, 2),
            "top_1": round(profits[0], 2),
            "top_5_sum": round(sum(profits[:5]), 2),
            "top_10_sum": round(sum(profits[:10]), 2),
            "net_ex_top_5": round(net - sum(profits[:5]), 2),
            "net_ex_top_10": round(net - sum(profits[:10]), 2),
        },
        "by_session": summarize_by(rows, "entry_session"),
        "by_hour": summarize_by(rows, "entry_hour"),
        "by_duration": summarize_by(rows, "duration_bucket"),
        "by_cost": summarize_by(rows, "cost_bucket"),
        "by_stop": summarize_by(rows, "stop_bucket"),
        "by_atr": summarize_by(rows, "atr_bucket"),
        "by_move": summarize_by(rows, "move_bucket"),
        "by_break": summarize_by(rows, "break_bucket"),
        "worst_days": sorted(by_day, key=lambda item: item["net_usd"])[:10],
        "best_days": sorted(by_day, key=lambda item: item["net_usd"], reverse=True)[:10],
        "biggest_losses": top_rows(rows, 12, reverse=False),
        "biggest_wins": top_rows(rows, 12, reverse=True),
        "source_hashes": [
            {"file": str(path), "sha256": file_sha256(path)}
            for path in [TRADE_CSV, ORDER_CSV, SIGNAL_CSV, VERDICT_JSON]
        ],
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    args.prompt_output.write_text(render_prompt(args.output_md, args.output_json), encoding="utf-8")
    print(json.dumps({"md": str(args.output_md), "json": str(args.output_json), "prompt": str(args.prompt_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
