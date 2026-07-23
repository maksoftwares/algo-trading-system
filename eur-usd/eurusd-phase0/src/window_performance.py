from __future__ import annotations

import csv
import html
import json
import re
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from .evidence_audit import PACKAGE_ROOT, REPO_ROOT, load_json, maximum_drawdown, read_text_auto


MANIFEST_PATH = PACKAGE_ROOT / "outputs" / "mt5_parity" / "locked" / "PARITY_MANIFEST.json"
RUN_JSON_PATH = PACKAGE_ROOT / "outputs" / "mt5_parity" / "FOREX_MT5_FREQUENCY_SCOUT_EURUSD_PHASE0_PARITY_V1.json"
WINDOW_END_EXCLUSIVE = datetime(2026, 7, 1)
WINDOWS = {
    "3_months": datetime(2026, 4, 1),
    "6_months": datetime(2026, 1, 1),
    "1_year": datetime(2025, 7, 1),
}


def _number(value: str) -> float:
    text = value.replace(" ", "").replace(",", "").strip()
    return float(text) if text else 0.0


def _deal_net_by_id(report_path: Path) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    text = read_text_auto(report_path)
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = [
            html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ")
            for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        ]
        if len(cells) < 13 or cells[2] != "EURUSD" or cells[4] != "out":
            continue
        commission = _number(cells[8])
        swap = _number(cells[9])
        price_profit = _number(cells[10])
        rows[cells[1]] = {
            "commission": commission,
            "swap": swap,
            "price_profit": price_profit,
            "net": commission + swap + price_profit,
        }
    return rows


def _load_trades(trade_path: Path, report_path: Path) -> list[dict[str, Any]]:
    deals = _deal_net_by_id(report_path)
    rows: list[dict[str, Any]] = []
    with trade_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            exit_deal = row["exit_deal"]
            if exit_deal not in deals:
                raise ValueError(f"Exit deal {exit_deal} is missing from the MT5 report")
            rows.append(
                {
                    **row,
                    "entry_dt": datetime.strptime(row["entry_time"], "%Y.%m.%d %H:%M:%S"),
                    "exit_dt": datetime.strptime(row["exit_time"], "%Y.%m.%d %H:%M:%S"),
                    **deals[exit_deal],
                }
            )
    return rows


def _streak(values: list[float], positive: bool) -> int:
    best = 0
    current = 0
    for value in values:
        matches = value > 0 if positive else value < 0
        current = current + 1 if matches else 0
        best = max(best, current)
    return best


def _window_metrics(trades: list[dict[str, Any]], start: datetime) -> dict[str, Any]:
    selected = [row for row in trades if start <= row["exit_dt"] < WINDOW_END_EXCLUSIVE]
    values = [float(row["net"]) for row in selected]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    monthly: dict[str, float] = {}
    holding_hours = []
    for row in selected:
        month = row["exit_dt"].strftime("%Y-%m")
        monthly[month] = monthly.get(month, 0.0) + float(row["net"])
        holding_hours.append((row["exit_dt"] - row["entry_dt"]).total_seconds() / 3600.0)

    return {
        "start_inclusive": start.isoformat(),
        "end_exclusive": WINDOW_END_EXCLUSIVE.isoformat(),
        "trades": len(selected),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(selected), 2),
        "net_pnl_usd": round(sum(values), 2),
        "price_profit_usd": round(sum(float(row["price_profit"]) for row in selected), 2),
        "swap_usd": round(sum(float(row["swap"]) for row in selected), 2),
        "commission_usd": round(sum(float(row["commission"]) for row in selected), 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4),
        "average_trade_usd": round(statistics.mean(values), 4),
        "average_win_usd": round(statistics.mean(wins), 4),
        "average_loss_usd": round(statistics.mean(losses), 4),
        "realized_win_loss_ratio": round(statistics.mean(wins) / -statistics.mean(losses), 4),
        "best_trade_usd": round(max(values), 2),
        "worst_trade_usd": round(min(values), 2),
        "maximum_closed_drawdown_usd": round(maximum_drawdown(values), 2),
        "maximum_win_streak": _streak(values, True),
        "maximum_loss_streak": _streak(values, False),
        "positive_months": sum(value > 0 for value in monthly.values()),
        "active_months": len(monthly),
        "monthly_net_usd": {month: round(value, 2) for month, value in sorted(monthly.items())},
        "average_holding_hours": round(statistics.mean(holding_hours), 2),
        "median_holding_hours": round(statistics.median(holding_hours), 2),
    }


def build_window_report() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    run_json = load_json(RUN_JSON_PATH)
    report_path = REPO_ROOT / manifest["artifacts"]["mt5_report"]["path"]
    trade_path = REPO_ROOT / manifest["artifacts"]["trade_csv"]["path"]
    trades = _load_trades(trade_path, report_path)
    full_net = round(sum(float(row["net"]) for row in trades), 2)
    expected_full_net = float(run_json["results"][0]["mt5_report_metrics"]["Total Net Profit"])
    if full_net != expected_full_net:
        raise ValueError(f"Deal net {full_net} does not reconcile to MT5 net {expected_full_net}")

    return {
        "schema_version": "eurusd_phase0_window_performance_v1",
        "candidate_id": "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1",
        "basis": {
            "fixed_lot": 0.01,
            "tester_deposit_usd": 1000.0,
            "window_end_inclusive": "2026-06-30",
            "incomplete_july_excluded": True,
            "net_includes": ["price_profit", "swap", "commission"],
            "full_ledger_trades": len(trades),
            "full_ledger_net_usd": full_net,
        },
        "windows": {name: _window_metrics(trades, start) for name, start in WINDOWS.items()},
    }


def render_markdown(report: dict[str, Any]) -> str:
    windows = report["windows"]
    rows = []
    for label, title in (("3_months", "3 months"), ("6_months", "6 months"), ("1_year", "1 year")):
        row = windows[label]
        rows.append(
            f"| {title} | {row['trades']} | {row['wins']} / {row['losses']} | "
            f"{row['win_rate_pct']:.2f}% | ${row['net_pnl_usd']:.2f} | "
            f"{row['profit_factor']:.4f} | ${row['maximum_closed_drawdown_usd']:.2f} |"
        )
    detail_rows = []
    metrics = (
        ("Gross profit", "gross_profit_usd", "$"),
        ("Gross loss", "gross_loss_usd", "-$"),
        ("Swap", "swap_usd", "$"),
        ("Average trade", "average_trade_usd", "$"),
        ("Average win", "average_win_usd", "$"),
        ("Average loss", "average_loss_usd", "$"),
        ("Realized win/loss", "realized_win_loss_ratio", ""),
        ("Best trade", "best_trade_usd", "$"),
        ("Worst trade", "worst_trade_usd", "$"),
        ("Positive months", "positive_months", ""),
    )
    for title, key, prefix in metrics:
        values = []
        for label in ("3_months", "6_months", "1_year"):
            value = windows[label][key]
            if title == "Positive months":
                values.append(f"{value}/{windows[label]['active_months']}")
            elif isinstance(value, float):
                values.append(f"{prefix}{value:.4f}" if "ratio" in key else f"{prefix}{value:.2f}")
            else:
                values.append(f"{prefix}{value}")
        detail_rows.append(f"| {title} | {values[0]} | {values[1]} | {values[2]} |")
    return f"""# EURUSD Completed-Window Performance

Basis: actual MT5 deal ledger, fixed `0.01` lot, USD 1,000 tester deposit.
Windows end on `2026-06-30`; incomplete July is excluded. Net P&L includes
price profit, swap, and commission.

| Window | Trades | Wins / Losses | Win rate | Net P&L | PF | Max closed DD |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

| Metric | 3 months | 6 months | 1 year |
|---|---:|---:|---:|
{chr(10).join(detail_rows)}

## Read

The strategy remains profitable in all three windows, but the edge is thin:
PF is `1.1010`, `1.1502`, and `1.1194`. The recent three-month result is only
USD `3.29`. Any improvement study must be preregistered and must not mine a new
set of hours or thresholds from these development outcomes.
"""


def write_window_report(report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = PACKAGE_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "EURUSD_WINDOW_PERFORMANCE.json"
    md_path = output_dir / "EURUSD_WINDOW_PERFORMANCE.md"
    with json_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    with md_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(report))
    return json_path, md_path
