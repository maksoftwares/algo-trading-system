from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROMOTION_NET_R_FLOOR = 0.15
OBSERVER_NET_R_FLOOR = 0.10
MAX_COST_R_P95 = 0.15
MIN_PROMOTION_TRADES = 150

STREAMS = {
    "full_diluted_portfolio": "Full diluted portfolio",
    "breakout_retest_only": "breakout_retest only",
    "wr50_wst12": "WideStop 1.2R",
    "wr50_wst15": "WideStop 1.5R",
    "wr50_e1r0": "Exit1R control",
    "wr50_pbe0": "PartialBE reserved",
}

MAGIC_TO_STREAM = {
    "930200": "wr50_e1r0",
    "930300": "wr50_wst12",
    "930400": "wr50_wst15",
    "930500": "wr50_pbe0",
}


@dataclass
class Trade:
    stream: str
    entry_time: str
    exit_time: str
    symbol: str
    direction: str
    magic: str
    profit: float
    r_value: float
    cost_r: float
    duplicate_key: str


@dataclass
class StreamMetrics:
    stream: str
    label: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    payoff: float
    expectancy_r_after_cost: float
    profit_factor: float
    cost_r_median: float
    cost_r_p95: float
    max_drawdown_r: float
    trades_per_day: float
    overlap_vs_breakout_retest: float
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


def _is_closed(row: dict[str, str]) -> bool:
    state = row.get("state", "").upper()
    if state:
        return state == "CLOSED"
    return bool(row.get("exit_time") or row.get("exit_time_broker") or row.get("exit_price"))


def _is_duplicate_hidden(row: dict[str, str]) -> bool:
    if row.get("is_duplicate", "").strip().lower() == "true":
        return False
    role = row.get("duplicate_role", "").strip().lower()
    return role in {"", "unique", "kept"}


def _price_r(row: dict[str, str]) -> float:
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


def _row_time(row: dict[str, str]) -> str:
    return row.get("entry_time") or row.get("entry_time_broker") or row.get("timestamp_broker") or ""


def _dedupe_key(row: dict[str, str]) -> str:
    key = row.get("duplicate_key", "")
    if key:
        return key
    entry_time = _row_time(row)[:16]
    return "|".join([entry_time, row.get("symbol", ""), row.get("direction", ""), row.get("volume") or row.get("lot", "")])


def _actual_trade_to_base_trade(row: dict[str, str], stream: str, measured_cost_r: float) -> Trade:
    return Trade(
        stream=stream,
        entry_time=_row_time(row),
        exit_time=row.get("exit_time") or row.get("exit_time_broker") or "",
        symbol=row.get("symbol", ""),
        direction=row.get("direction", ""),
        magic=row.get("magic", ""),
        profit=_float(row.get("profit_aed") or row.get("profit_account_currency")),
        r_value=_price_r(row),
        cost_r=_float(row.get("cost_r"), measured_cost_r),
        duplicate_key=_dedupe_key(row),
    )


def load_actual_control_trades(path: Path, measured_cost_r: float) -> list[Trade]:
    trades: list[Trade] = []
    for row in _read_csv(path):
        if not _is_closed(row) or not _is_duplicate_hidden(row):
            continue
        magic = str(row.get("magic", "")).strip()
        if magic.startswith("920"):
            trades.append(_actual_trade_to_base_trade(row, "full_diluted_portfolio", measured_cost_r))
        if row.get("candidate", "") == "breakout_retest":
            trades.append(_actual_trade_to_base_trade(row, "breakout_retest_only", measured_cost_r))
        stream = MAGIC_TO_STREAM.get(magic)
        if stream:
            trades.append(_actual_trade_to_base_trade(row, stream, measured_cost_r))
    return trades


def load_wr50_ledgers(paths: list[Path], measured_cost_r: float) -> list[Trade]:
    trades: list[Trade] = []
    for path in paths:
        for row in _read_csv(path):
            if not _is_closed(row):
                continue
            magic = str(row.get("magic", "")).strip()
            stream = MAGIC_TO_STREAM.get(magic)
            if not stream:
                continue
            trades.append(
                Trade(
                    stream=stream,
                    entry_time=row.get("entry_time_broker") or row.get("timestamp_broker", ""),
                    exit_time=row.get("exit_time_broker", ""),
                    symbol=row.get("symbol", ""),
                    direction=row.get("direction", ""),
                    magic=magic,
                    profit=_float(row.get("profit_account_currency")),
                    r_value=_float(row.get("net_r") or row.get("gross_r")),
                    cost_r=_float(row.get("cost_r"), measured_cost_r),
                    duplicate_key=_dedupe_key(row),
                )
            )
    return trades


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, math.ceil(len(values) * 0.95) - 1)]


def _max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def _trades_per_day(trades: list[Trade]) -> float:
    days = {trade.entry_time[:10] for trade in trades if len(trade.entry_time) >= 10}
    if not days:
        return 0.0
    return len(trades) / len(days)


def _verdict(stream: str, trades: int, expectancy: float, cost_p95: float, win_rate: float, control: StreamMetrics | None) -> str:
    if trades == 0:
        return "NO_DATA"
    if trades < MIN_PROMOTION_TRADES:
        prefix = "CHECKPOINT_ONLY_SAMPLE_LT_150"
    else:
        prefix = "PROMOTION_SAMPLE_OK"

    if expectancy < OBSERVER_NET_R_FLOOR:
        return f"{prefix}: REJECT_THIS_VARIANT"
    if expectancy < PROMOTION_NET_R_FLOOR:
        return f"{prefix}: OBSERVER_ONLY_KEEP_COLLECTING"
    if cost_p95 > MAX_COST_R_P95:
        return f"{prefix}: OBSERVER_ONLY_COST_P95_GT_0_15R"

    if stream in {"wr50_wst12", "wr50_wst15"} and control is not None:
        if expectancy < control.expectancy_r_after_cost or win_rate < control.win_rate:
            return f"{prefix}: OBSERVER_ONLY_DID_NOT_BEAT_TIGHT_CONTROL"
    if expectancy >= 0.20:
        return f"{prefix}: STRONGER_CANDIDATE_CONTINUE_EXTEND"
    return f"{prefix}: CONTINUE_EXTEND"


def compute_metrics(trades: list[Trade]) -> list[StreamMetrics]:
    grouped: dict[str, list[Trade]] = defaultdict(list)
    for trade in trades:
        grouped[trade.stream].append(trade)
    breakout_keys = {trade.duplicate_key for trade in grouped.get("breakout_retest_only", [])}

    provisional: dict[str, StreamMetrics] = {}
    for stream in STREAMS:
        rows = grouped.get(stream, [])
        values = [row.r_value for row in rows]
        wins = [value for value in values if value > 0]
        losses = [value for value in values if value < 0]
        costs = [row.cost_r for row in rows]
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        win_rate = len(wins) / len(values) if values else 0.0
        expectancy = (sum(values) / len(values) if values else 0.0) - (_median(costs) if costs else 0.0)
        gross_win = sum(wins)
        gross_loss_abs = abs(sum(losses))
        pf = gross_win / gross_loss_abs if gross_loss_abs else (float("inf") if gross_win > 0 else 0.0)
        overlap = (
            len({row.duplicate_key for row in rows} & breakout_keys) / len(rows)
            if rows and breakout_keys
            else 0.0
        )
        provisional[stream] = StreamMetrics(
            stream=stream,
            label=STREAMS[stream],
            trades=len(rows),
            wins=len(wins),
            losses=len(losses),
            win_rate=win_rate,
            avg_win_r=avg_win,
            avg_loss_r=avg_loss,
            payoff=(avg_win / abs(avg_loss)) if avg_loss < 0 else 0.0,
            expectancy_r_after_cost=expectancy,
            profit_factor=pf,
            cost_r_median=_median(costs),
            cost_r_p95=_p95(costs),
            max_drawdown_r=_max_drawdown(values),
            trades_per_day=_trades_per_day(rows),
            overlap_vs_breakout_retest=overlap,
            verdict="PENDING",
        )
    control = provisional.get("breakout_retest_only")
    final: list[StreamMetrics] = []
    for stream, item in provisional.items():
        final.append(
            StreamMetrics(
                **{**item.__dict__, "verdict": _verdict(stream, item.trades, item.expectancy_r_after_cost, item.cost_r_p95, item.win_rate, control)}
            )
        )
    return final


def _fmt(value: float) -> str:
    if value == float("inf"):
        return "inf"
    return f"{value:.4f}"


def _fmt_delta(item: StreamMetrics, control: StreamMetrics) -> str:
    if item.trades == 0 or control.trades == 0:
        return "n/a"
    return _fmt(item.expectancy_r_after_cost - control.expectancy_r_after_cost)


def write_report(metrics: list[StreamMetrics], output: Path, as_of_date: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    by_stream = {item.stream: item for item in metrics}
    full_control = by_stream["full_diluted_portfolio"]
    br_control = by_stream["breakout_retest_only"]

    lines = [
        "# EA Improvement Week 1 Comparison",
        "",
        f"Report date: {as_of_date}",
        "",
        "Status: CHECKPOINT_ONLY",
        "",
        "This report is research-only. It does not authorize canonical Phase 2, live trading, or removal of the `COST_SUSPENDED_CANONICAL` family lock.",
        "",
        "Primary KPI: net R after measured cost. Win rate is diagnostic only.",
        "",
        "| Stream | Closed Trades | Win Rate | Avg Win R | Avg Loss R | Payoff | Net R After Cost | PF | Cost R Median | Cost R P95 | Max DD R | Trades/Day | Same-Bar Overlap vs BR | Verdict |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in metrics:
        lines.append(
            f"| {item.label} | {item.trades} | {item.win_rate:.2%} | {_fmt(item.avg_win_r)} | {_fmt(item.avg_loss_r)} | {_fmt(item.payoff)} | {_fmt(item.expectancy_r_after_cost)} | {_fmt(item.profit_factor)} | {_fmt(item.cost_r_median)} | {_fmt(item.cost_r_p95)} | {_fmt(item.max_drawdown_r)} | {_fmt(item.trades_per_day)} | {item.overlap_vs_breakout_retest:.2%} | {item.verdict} |"
        )
    lines.extend(
        [
            "",
            "## Head To Head",
            "",
            "| Variant | Delta vs Full Portfolio | Delta vs Breakout Retest Only | Gate Verdict |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for stream in ("wr50_wst12", "wr50_wst15", "wr50_e1r0", "wr50_pbe0"):
        item = by_stream[stream]
        lines.append(
            f"| {item.label} | {_fmt_delta(item, full_control)} | {_fmt_delta(item, br_control)} | {item.verdict} |"
        )
    lines.extend(
        [
            "",
            "## Pre-Committed Logic",
            "",
            f"- Reject if net R after measured cost is below +{OBSERVER_NET_R_FLOOR:.2f}R.",
            f"- Keep observer-only between +{OBSERVER_NET_R_FLOOR:.2f}R and +{PROMOTION_NET_R_FLOOR:.2f}R.",
            f"- Continue/extend only when net R is at least +{PROMOTION_NET_R_FLOOR:.2f}R and cost R p95 is at most {MAX_COST_R_P95:.2f}R.",
            "- Wide-stop variants must beat or preserve the breakout-retest tight-stop control on both net R and win rate.",
            f"- No promotion is possible before {MIN_PROMOTION_TRADES} fresh closed trades; week 1 is a checkpoint.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    default_actual = root.parent / "xauusd-phase1" / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
    parser = argparse.ArgumentParser(description="Generate EA improvement week-1 comparison report.")
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--actual-trades", type=Path, default=default_actual)
    parser.add_argument("--wr50-ledger", type=Path, action="append")
    parser.add_argument("--measured-cost-r", type=float, default=0.15)
    parser.add_argument("--as-of-date", default=datetime.now().strftime("%Y_%m_%d"))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    output = args.output or args.root / "outputs" / "reports" / f"EA_IMPROVEMENT_WEEK1_COMPARISON_{args.as_of_date}.md"
    ledgers = args.wr50_ledger or [
        args.root / "outputs" / "logs" / "wr50_trade_ledger.csv",
        *(args.root / "outputs" / "ledgers").glob("*.csv"),
    ]
    trades = load_actual_control_trades(args.actual_trades, args.measured_cost_r)
    trades.extend(load_wr50_ledgers(list(ledgers), args.measured_cost_r))
    metrics = compute_metrics(trades)
    write_report(metrics, output, args.as_of_date)
    print(f"EA improvement comparison: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
