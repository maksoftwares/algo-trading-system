from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median


@dataclass
class EaMetrics:
    ea_id: str
    magic: str
    trades: int
    open_trades: int
    win_rate: float
    profit_factor: float
    net_r: float
    pnl: float
    avg_win_r: float
    avg_loss_r: float
    cost_r: float
    commission: float
    swap: float
    entry_spread_median: float
    entry_spread_p95: float
    max_consecutive_losses: int
    largest_trade_contribution: float
    top5_trade_contribution: float
    status: str
    notes: str


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_trade_rows(root: Path, ledger_paths: list[Path] | None = None) -> list[dict[str, str]]:
    paths = ledger_paths or [
        *(root / "outputs" / "ledgers").glob("*.csv"),
        root / "outputs" / "logs" / "wr50_trade_ledger.csv",
    ]
    rows: list[dict[str, str]] = []
    for path in paths:
        for row in _read_csv(path):
            row["_source_file"] = str(path)
            rows.append(row)
    return rows


def _float(row: dict[str, str], field: str, default: float = 0.0) -> float:
    try:
        value = row.get(field, "")
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def _closed(row: dict[str, str]) -> bool:
    return bool(row.get("exit_time_broker") or row.get("exit_price") or row.get("deal_ticket"))


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, math.ceil(0.95 * len(sorted_values)) - 1)
    return sorted_values[index]


def _max_consecutive_losses(values: list[float]) -> int:
    best = 0
    current = 0
    for value in values:
        if value < 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def compute_metrics(rows: list[dict[str, str]]) -> list[EaMetrics]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row.get("ea_id") or row.get("ea_short_code") or "UNKNOWN", row.get("magic", "UNKNOWN"))
        grouped[key].append(row)

    metrics: list[EaMetrics] = []
    for (ea_id, magic), group_rows in sorted(grouped.items()):
        closed_rows = [row for row in group_rows if _closed(row)]
        open_trades = len(group_rows) - len(closed_rows)
        net_rs = [_float(row, "net_r") for row in closed_rows]
        pnls = [_float(row, "profit_account_currency") for row in closed_rows]
        wins = [value for value in net_rs if value > 0]
        losses = [value for value in net_rs if value < 0]
        gross_win = sum(wins)
        gross_loss_abs = abs(sum(losses))
        profit_factor = gross_win / gross_loss_abs if gross_loss_abs > 0 else (float("inf") if gross_win > 0 else 0.0)
        win_rate = len(wins) / len(closed_rows) if closed_rows else 0.0
        net_r = sum(net_rs)
        pnl = sum(pnls)
        cost_r = sum(_float(row, "cost_r") for row in closed_rows)
        commission = sum(_float(row, "commission") for row in closed_rows)
        swap = sum(_float(row, "swap") for row in closed_rows)
        spreads = [_float(row, "entry_spread_points") for row in group_rows if row.get("entry_spread_points")]
        sorted_abs_pnls = sorted((abs(value) for value in pnls), reverse=True)
        total_abs_pnl = sum(sorted_abs_pnls)
        largest_contribution = sorted_abs_pnls[0] / total_abs_pnl if total_abs_pnl else 0.0
        top5_contribution = sum(sorted_abs_pnls[:5]) / total_abs_pnl if total_abs_pnl else 0.0
        if len(closed_rows) < 100:
            status = "REVIEW_READY_LOW_SAMPLE"
            notes = "Minimum 100 closed trades not reached."
        elif win_rate >= 0.50 and profit_factor >= 1.20 and (net_r / len(closed_rows)) >= 0.15:
            status = "CANDIDATE_FOR_PHASE0R_REVALIDATION"
            notes = "Demo gates met; formal Phase 0R hypothesis required."
        else:
            status = "REJECTED_EXPERIMENTAL"
            notes = "One or more WR50 gates failed."
        metrics.append(
            EaMetrics(
                ea_id=ea_id,
                magic=magic,
                trades=len(closed_rows),
                open_trades=open_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                net_r=net_r,
                pnl=pnl,
                avg_win_r=sum(wins) / len(wins) if wins else 0.0,
                avg_loss_r=sum(losses) / len(losses) if losses else 0.0,
                cost_r=cost_r,
                commission=commission,
                swap=swap,
                entry_spread_median=median(spreads) if spreads else 0.0,
                entry_spread_p95=_p95(spreads),
                max_consecutive_losses=_max_consecutive_losses(net_rs),
                largest_trade_contribution=largest_contribution,
                top5_trade_contribution=top5_contribution,
                status=status,
                notes=notes,
            )
        )
    return metrics


def _fmt_float(value: float) -> str:
    if value == float("inf"):
        return "inf"
    return f"{value:.4f}"


def write_reports(root: Path, rows: list[dict[str, str]], metrics: list[EaMetrics]) -> None:
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    daily_lines = [
        "# WR50 Experimental Daily Report",
        "",
        "Overall status: RESEARCH_ONLY",
        "",
        "WR50 reports do not authorize canonical Phase 2, live trading, or reactivation of canonical breakout_retest execution.",
        "",
        "## Group Summary",
        "",
        "| EA | Magic | Trades | Win Rate | PF | Net R | PnL | Status | Notes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    if metrics:
        for item in metrics:
            daily_lines.append(
                f"| {item.ea_id} | {item.magic} | {item.trades} | {item.win_rate:.2%} | {_fmt_float(item.profit_factor)} | {item.net_r:.4f} | {item.pnl:.2f} | {item.status} | {item.notes} |"
            )
    else:
        daily_lines.append("| None |  | 0 | 0.00% | 0.0000 | 0.0000 | 0.00 | NO_DATA | No WR50 ledger rows found. |")
    daily_lines.extend(["", "## Source Rows", "", f"Rows loaded: {len(rows)}"])
    (reports / "WR50_EXPERIMENTAL_DAILY_REPORT.md").write_text("\n".join(daily_lines) + "\n", encoding="utf-8")

    summary_fields = ["ea_id", "magic", "trades", "open_trades", "win_rate", "profit_factor", "net_r", "pnl", "status", "notes"]
    with (reports / "WR50_EXPERIMENTAL_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_fields)
        writer.writeheader()
        for item in metrics:
            writer.writerow({field: getattr(item, field) for field in summary_fields})

    breakdown_lines = [
        "# WR50 EA Breakdown",
        "",
        "| EA | Magic | Closed | Open | Avg Win R | Avg Loss R | Gross/Net R | Cost R | Commission | Swap | Entry Spread Median | Entry Spread P95 | Max Consecutive Losses | Largest Trade Contribution | Top 5 Contribution |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in metrics:
        breakdown_lines.append(
            f"| {item.ea_id} | {item.magic} | {item.trades} | {item.open_trades} | {item.avg_win_r:.4f} | {item.avg_loss_r:.4f} | {item.net_r:.4f} | {item.cost_r:.4f} | {item.commission:.2f} | {item.swap:.2f} | {item.entry_spread_median:.1f} | {item.entry_spread_p95:.1f} | {item.max_consecutive_losses} | {item.largest_trade_contribution:.2%} | {item.top5_trade_contribution:.2%} |"
        )
    if not metrics:
        breakdown_lines.append("| None |  | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.00 | 0.0 | 0.0 | 0 | 0.00% | 0.00% |")
    (reports / "WR50_EA_BREAKDOWN.md").write_text("\n".join(breakdown_lines) + "\n", encoding="utf-8")

    audit_lines = [
        "# WR50 Magic Attribution Audit",
        "",
        "| Magic | EA | Rows | Comments Missing | Experiment IDs Missing | Run IDs Missing |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped_rows[(row.get("magic", ""), row.get("ea_id", row.get("ea_short_code", "UNKNOWN")))].append(row)
    for (magic, ea_id), group_rows in sorted(grouped_rows.items()):
        audit_lines.append(
            f"| {magic} | {ea_id} | {len(group_rows)} | {sum(not row.get('comment') for row in group_rows)} | {sum(not row.get('experiment_id') for row in group_rows)} | {sum(not row.get('run_id') for row in group_rows)} |"
        )
    if not grouped_rows:
        audit_lines.append("|  | None | 0 | 0 | 0 | 0 |")
    (reports / "WR50_MAGIC_ATTRIBUTION_AUDIT.md").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    root = default_root()
    parser = argparse.ArgumentParser(description="Build WR50 daily report.")
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--ledger", type=Path, action="append")
    args = parser.parse_args(argv)

    rows = load_trade_rows(args.root, args.ledger)
    metrics = compute_metrics(rows)
    write_reports(args.root, rows, metrics)
    print(f"WR50 daily report rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

