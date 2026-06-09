from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DAY_3_5_PF_FLOOR = 1.10
DAY_3_5_PNL_BASELINE_FRACTION = 0.50
FRESH_TRADE_OBSERVER_ONLY_SAMPLE = 50
IMMEDIATE_NET_R_FLOOR = 0.0


@dataclass
class RepairKillMetrics:
    repair_closed_trades: int
    repair_pnl: float
    repair_pf: float
    repair_net_r_after_cost: float
    baseline_pnl: float
    baseline_closed_trades: int
    verdict: str


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _float(value: str | None, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def _closed(row: dict[str, str]) -> bool:
    state = row.get("state", "").upper()
    if state:
        return state == "CLOSED"
    return bool(row.get("exit_time") or row.get("exit_price"))


def _duplicate_hidden(row: dict[str, str]) -> bool:
    if row.get("is_duplicate", "").strip().lower() == "true":
        return False
    role = row.get("duplicate_role", "").strip().lower()
    return role in {"", "unique", "kept"}


def _r_value(row: dict[str, str]) -> float:
    entry = _float(row.get("entry_price"))
    exit_price = _float(row.get("exit_price"))
    sl = _float(row.get("sl") or row.get("sl_price"))
    direction = (row.get("direction") or "").upper()
    if entry <= 0.0 or exit_price <= 0.0 or sl <= 0.0:
        return _float(row.get("net_r") or row.get("gross_r"))
    risk = abs(entry - sl)
    if risk <= 0.0:
        return _float(row.get("net_r") or row.get("gross_r"))
    if direction in {"BUY", "LONG"}:
        return (exit_price - entry) / risk
    if direction in {"SELL", "SHORT"}:
        return (entry - exit_price) / risk
    return _float(row.get("net_r") or row.get("gross_r"))


def _pf(values: list[float]) -> float:
    wins = sum(value for value in values if value > 0.0)
    losses = abs(sum(value for value in values if value < 0.0))
    if losses == 0.0:
        return float("inf") if wins > 0.0 else 0.0
    return wins / losses


def compute_repair_kill_metrics(rows: list[dict[str, str]], measured_cost_r: float, elapsed_days: float) -> RepairKillMetrics:
    closed = [row for row in rows if _closed(row) and _duplicate_hidden(row)]
    repairs = [row for row in closed if "_repair_v1" in row.get("candidate", "")]
    baseline = [row for row in closed if "_repair_v1" not in row.get("candidate", "")]

    repair_values = [_r_value(row) for row in repairs]
    repair_pnl = sum(_float(row.get("profit_aed") or row.get("profit_account_currency")) for row in repairs)
    baseline_pnl = sum(_float(row.get("profit_aed") or row.get("profit_account_currency")) for row in baseline)
    repair_pf = _pf(repair_values)
    expectancy = (sum(repair_values) / len(repair_values) if repair_values else 0.0) - measured_cost_r

    verdict = "PENDING_NO_REPAIR_CLOSED_TRADES"
    if repairs:
        verdict = "WATCH_KEEP_COLLECTING"
    if len(repairs) >= FRESH_TRADE_OBSERVER_ONLY_SAMPLE and expectancy < IMMEDIATE_NET_R_FLOOR:
        verdict = "IMMEDIATE_OBSERVER_ONLY_REPAIR_NET_R_LT_0_AFTER_50_TRADES"
    elif elapsed_days >= 3.5:
        baseline_floor = baseline_pnl * DAY_3_5_PNL_BASELINE_FRACTION
        if repair_pf < DAY_3_5_PF_FLOOR or repair_pnl < baseline_floor:
            verdict = "REJECT_REPAIR_V1_DAY_3_5_KILL_RULE"
        else:
            verdict = "DAY_3_5_RULE_SURVIVED_KEEP_COLLECTING"

    return RepairKillMetrics(
        repair_closed_trades=len(repairs),
        repair_pnl=repair_pnl,
        repair_pf=repair_pf,
        repair_net_r_after_cost=expectancy,
        baseline_pnl=baseline_pnl,
        baseline_closed_trades=len(baseline),
        verdict=verdict,
    )


def _fmt(value: float) -> str:
    if value == float("inf"):
        return "inf"
    return f"{value:.4f}"


def write_report(metrics: RepairKillMetrics, output: Path, elapsed_days: float, measured_cost_r: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 2 Demo Repair Kill-Condition Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Status: REPORT_ONLY",
        "",
        "This report does not touch MT5 and does not authorize canonical Phase 2.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Repair closed trades | {metrics.repair_closed_trades} |",
        f"| Repair PnL | {metrics.repair_pnl:.2f} |",
        f"| Repair PF | {_fmt(metrics.repair_pf)} |",
        f"| Repair net R after measured cost | {_fmt(metrics.repair_net_r_after_cost)} |",
        f"| Baseline duplicate-hidden closed trades | {metrics.baseline_closed_trades} |",
        f"| Baseline duplicate-hidden PnL | {metrics.baseline_pnl:.2f} |",
        f"| Elapsed forward days | {elapsed_days:.2f} |",
        f"| Measured cost R used | {measured_cost_r:.4f} |",
        f"| Verdict | {metrics.verdict} |",
        "",
        "## Pre-Committed Kill Rules",
        "",
        "- At day 3.5, reject repair_v1 if repair PF is below 1.10 or repair PnL is below 50% of the duplicate-hidden baseline.",
        "- After 50 fresh closed repair trades, move repair_v1 observer-only immediately if repair net R after cost is below 0.00R.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate Phase 2 demo repair kill-condition report.")
    parser.add_argument("--actual-trades", type=Path, default=root / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv")
    parser.add_argument("--elapsed-days", type=float, default=0.0)
    parser.add_argument("--measured-cost-r", type=float, default=0.15)
    parser.add_argument("--output", type=Path, default=root / "outputs" / "reports" / "PHASE2_DEMO_REPAIR_KILL_CONDITION_REPORT.md")
    args = parser.parse_args(argv)

    metrics = compute_repair_kill_metrics(_read_csv(args.actual_trades), args.measured_cost_r, args.elapsed_days)
    write_report(metrics, args.output, args.elapsed_days, args.measured_cost_r)
    print(f"Phase 2 repair kill report: {args.output}")
    print(f"Verdict: {metrics.verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
