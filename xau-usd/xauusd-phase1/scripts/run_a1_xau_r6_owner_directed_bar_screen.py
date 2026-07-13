"""Run the locked R6 rule once on preserved native MT5 bar exports.

This is an owner-directed DEVELOPMENT_DATA screen.  Signal construction reuses the
locked R6 detector and preserved native Router V1 rows.  Because the preserved
capture does not contain the full decade tick stream, the entry tick is proxied by
the native next-H1 open and the H1 spread field.  Exits use pessimistic H1 ordering:
if stop and target are both touched in one H1 bar, the stop wins.

The result is useful for quickly rejecting an unprofitable hypothesis.  It is not a
replacement for the separately locked exact-tick MT5 evidence phase.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence


PHASE1_ROOT = Path(__file__).resolve().parents[1]
DETECTOR_PATH = PHASE1_ROOT / "scripts" / "build_a1_xau_r6_distribution_break_failed_reclaim_census.py"
DEFAULT_TESTER_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_OUTPUT = PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_R6_OWNER_DIRECTED_BAR_SCREEN_20260713"
INITIAL_EQUITY_USD = 10_000.0
REFERENCE_RISK_USD = 25.0
TARGET_R = 2.0
TICKET_STRESS_USD = 0.30


@dataclass(frozen=True)
class H1PathBar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    spread_points: float


@dataclass(frozen=True)
class Trade:
    candidate_id: str
    entry_time: datetime
    exit_time: datetime
    entry_bid: float
    entry_ask: float
    stop_price: float
    target_price: float
    exit_price: float
    exit_reason: str
    minimum_lot_risk_usd: float
    pnl_r: float
    pnl_minimum_lot_usd: float
    pnl_reference_usd: float
    max_adverse_r: float
    router_state: str
    reference_risk_feasible: bool
    deployment_risk_feasible: bool


def load_detector():
    spec = importlib.util.spec_from_file_location("a1_xau_r6_locked_detector", DETECTOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import locked R6 detector")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def find_capture_dir(root: Path) -> Path:
    matches = sorted(root.rglob("native_h1_bars.tsv"), key=lambda item: item.stat().st_mtime, reverse=True)
    for match in matches:
        required = {
            "native_h1_bars.tsv",
            "native_h4_bars.tsv",
            "native_d1_bars.tsv",
            "native_router_rows.tsv",
            "native_contract.tsv",
        }
        if required.issubset({item.name for item in match.parent.iterdir() if item.is_file()}):
            return match.parent
    raise FileNotFoundError(f"no complete native R6 capture under {root}")


def read_tsv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def load_bars(path: Path, detector) -> tuple:
    rows = []
    for row in read_tsv(path):
        rows.append(
            detector.Bar(
                datetime.fromisoformat(row["open_time_broker"]),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
            )
        )
    return tuple(rows)


def load_h1_path(path: Path) -> tuple[H1PathBar, ...]:
    return tuple(
        H1PathBar(
            datetime.fromisoformat(row["open_time_broker"]),
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"]),
            float(row["spread"]),
        )
        for row in read_tsv(path)
    )


def load_contract(path: Path, detector):
    rows = list(read_tsv(path))
    if len(rows) != 1:
        raise ValueError("native contract capture must contain exactly one row")
    row = rows[0]
    return detector.Contract(
        account_currency=row["account_currency"],
        account_leverage=int(row["account_leverage"]),
        margin_mode=int(row["margin_mode"]),
        server=row["server"],
        symbol=row["symbol"],
        point=float(row["point"]),
        digits=int(row["digits"]),
        tick_size=float(row["tick_size"]),
        tick_value=float(row["tick_value"]),
        tick_value_loss=float(row["tick_value_loss"]),
        volume_min=float(row["volume_min"]),
        volume_step=float(row["volume_step"]),
        volume_max=float(row["volume_max"]),
        contract_size=float(row["contract_size"]),
        stops_level=int(row["stops_level"]),
        freeze_level=int(row["freeze_level"]),
    )


def load_native_router(path: Path) -> dict[datetime, str]:
    result: dict[datetime, str] = {}
    for row in read_tsv(path):
        timestamp = datetime.fromisoformat(row["timestamp_broker"])
        if timestamp in result:
            raise ValueError(f"duplicate native router timestamp {timestamp}")
        if row["data_available"].lower() != "true":
            result[timestamp] = "UNKNOWN"
        else:
            result[timestamp] = row["state_name"].upper()
    return result


def candidate_rows(structural, h1_path: Sequence[H1PathBar], contract, detector):
    by_time = {bar.time: (index, bar) for index, bar in enumerate(h1_path)}
    rows: list[dict[str, object]] = []
    rejected = 0
    for sequence, window in enumerate(structural.windows):
        found = by_time.get(window.decision_time)
        if found is None:
            rejected += 1
            continue
        _, bar = found
        entry = detector.Tick(
            time=bar.time,
            sequence=sequence,
            bid=bar.open,
            ask=bar.open + bar.spread_points * contract.point,
            session_open=True,
            source_h1_bar_time=bar.time,
        )
        result = detector._raw_row_and_context(window, entry, (entry,), -1, contract, contract.symbol)
        if result is None:
            rejected += 1
            continue
        row, _ = result
        row["entry_proxy"] = "NATIVE_NEXT_H1_OPEN_WITH_CAPTURED_H1_SPREAD"
        rows.append(row)
    return rows, rejected


def simulate_candidate(
    row: dict[str, object],
    h1_path: Sequence[H1PathBar],
    h1_index: dict[datetime, int],
    contract,
) -> Trade:
    entry_time = datetime.fromisoformat(str(row["entry_tick_time"]))
    start = h1_index[entry_time]
    entry_bid = float(row["entry_bid"])
    entry_ask = float(row["entry_ask"])
    stop = float(row["risk_exit_price"])
    risk_distance = stop - entry_bid
    target = entry_bid - TARGET_R * risk_distance
    worst_adverse_r = 0.0
    exit_reason = "END_OF_DATA"
    exit_time = h1_path[-1].time
    exit_price = h1_path[-1].close + h1_path[-1].spread_points * contract.point

    for bar in h1_path[start:]:
        spread = bar.spread_points * contract.point
        ask_high = bar.high + spread
        ask_low = bar.low + spread
        adverse_r = max(0.0, (ask_high - entry_bid) / risk_distance)
        worst_adverse_r = max(worst_adverse_r, min(adverse_r, 1.0))
        stop_hit = ask_high >= stop
        target_hit = ask_low <= target
        if stop_hit:
            exit_reason = "STOP" if not target_hit else "STOP_PESSIMISTIC_SAME_H1"
            exit_time = bar.time
            exit_price = stop
            break
        if target_hit:
            exit_reason = "TARGET_2R"
            exit_time = bar.time
            exit_price = target
            break

    ticks = (entry_bid - exit_price) / contract.tick_size
    pnl_minimum_lot = ticks * contract.tick_value_loss * contract.volume_min
    minimum_risk = float(row["minimum_contract_risk_usd"])
    pnl_r = pnl_minimum_lot / minimum_risk
    return Trade(
        candidate_id=str(row["candidate_id"]),
        entry_time=entry_time,
        exit_time=exit_time,
        entry_bid=entry_bid,
        entry_ask=entry_ask,
        stop_price=stop,
        target_price=target,
        exit_price=exit_price,
        exit_reason=exit_reason,
        minimum_lot_risk_usd=minimum_risk,
        pnl_r=pnl_r,
        pnl_minimum_lot_usd=pnl_minimum_lot,
        pnl_reference_usd=pnl_r * REFERENCE_RISK_USD,
        max_adverse_r=worst_adverse_r,
        router_state=str(row["router_state"]),
        reference_risk_feasible=bool(row["reference_risk_feasible"]),
        deployment_risk_feasible=bool(row["deployment_risk_feasible"]),
    )


def one_position(trades: Sequence[Trade]) -> tuple[list[Trade], int]:
    kept: list[Trade] = []
    skipped = 0
    active_until: datetime | None = None
    for trade in sorted(trades, key=lambda item: item.entry_time):
        if active_until is not None and trade.entry_time <= active_until:
            skipped += 1
            continue
        kept.append(trade)
        active_until = trade.exit_time
    return kept, skipped


def max_closed_drawdown(values: Sequence[float], initial: float = INITIAL_EQUITY_USD) -> tuple[float, float]:
    equity = peak = initial
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum, maximum / peak * 100.0 if peak else math.inf


def max_intrabar_drawdown(trades: Sequence[Trade]) -> tuple[float, float]:
    equity = peak = INITIAL_EQUITY_USD
    maximum = 0.0
    for trade in trades:
        adverse_equity = equity - min(trade.max_adverse_r, 1.0) * REFERENCE_RISK_USD
        maximum = max(maximum, peak - adverse_equity)
        equity += trade.pnl_reference_usd
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum, maximum / peak * 100.0 if peak else math.inf


def metrics(trades: Sequence[Trade]) -> dict[str, object]:
    pnl = [trade.pnl_reference_usd for trade in trades]
    stress = [value - TICKET_STRESS_USD for value in pnl]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    stress_wins = [value for value in stress if value > 0]
    stress_losses = [value for value in stress if value < 0]
    closed_dd, closed_dd_pct = max_closed_drawdown(pnl)
    floating_dd, floating_dd_pct = max_intrabar_drawdown(trades)
    annual = defaultdict(float)
    for trade in trades:
        bucket = trade.entry_time.year if trade.entry_time.month >= 7 else trade.entry_time.year - 1
        annual[bucket] += trade.pnl_reference_usd
    daily_wins = defaultdict(float)
    for trade in trades:
        daily_wins[trade.exit_time.date()] += trade.pnl_reference_usd
    top_winners = sorted((value for value in pnl if value > 0), reverse=True)
    top_days = sorted((value for value in daily_wins.values() if value > 0), reverse=True)
    early = [trade.pnl_reference_usd for trade in trades if trade.entry_time < datetime(2021, 7, 1)]
    late = [trade.pnl_reference_usd for trade in trades if trade.entry_time >= datetime(2021, 7, 1)]
    return {
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": 100.0 * len(wins) / len(trades) if trades else 0.0,
        "realized_win_loss": mean(wins) / abs(mean(losses)) if wins and losses else None,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else None,
        "net_reference_usd": sum(pnl),
        "stress_net_reference_usd": sum(stress),
        "stress_profit_factor": sum(stress_wins) / abs(sum(stress_losses)) if stress_losses else None,
        "expectancy_r": mean(trade.pnl_r for trade in trades) if trades else None,
        "net_minimum_lot_usd": sum(trade.pnl_minimum_lot_usd for trade in trades),
        "max_closed_drawdown_usd": closed_dd,
        "max_closed_drawdown_pct": closed_dd_pct,
        "max_h1_intrabar_drawdown_usd": floating_dd,
        "max_h1_intrabar_drawdown_pct": floating_dd_pct,
        "top_10_winners_removed_net_usd": sum(pnl) - sum(top_winners[:10]),
        "top_3_winning_days_removed_net_usd": sum(pnl) - sum(top_days[:3]),
        "positive_july_june_buckets": sum(value > 0 for value in annual.values()),
        "july_june_pnl": dict(sorted(annual.items())),
        "early_half_net_usd": sum(early),
        "late_half_net_usd": sum(late),
        "reference_risk_feasible_trades": sum(trade.reference_risk_feasible for trade in trades),
        "deployment_risk_feasible_trades": sum(trade.deployment_risk_feasible for trade in trades),
    }


def write_outputs(output: Path, payload: dict[str, object], rows: Sequence[dict[str, object]], trades: Sequence[Trade]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "A1_XAU_R6_OWNER_DIRECTED_BAR_SCREEN_20260713.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    if rows:
        with (output / "A1_XAU_R6_OWNER_DIRECTED_BAR_SCREEN_20260713_CANDIDATES.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    trade_rows = []
    for trade in trades:
        row = asdict(trade)
        row["entry_time"] = trade.entry_time.isoformat()
        row["exit_time"] = trade.exit_time.isoformat()
        trade_rows.append(row)
    if trade_rows:
        with (output / "A1_XAU_R6_OWNER_DIRECTED_BAR_SCREEN_20260713_TRADES.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trade_rows[0]))
            writer.writeheader()
            writer.writerows(trade_rows)
    result = payload["backtest"]
    lines = [
        "# A1 XAU R6 owner-directed bar screen",
        "",
        "Status: `DEVELOPMENT_ONLY_NOT_EXACT_TICK_MT5`",
        "",
        f"- Trades: `{result['trades']}`",
        f"- Net at fixed $25 reference risk: `${result['net_reference_usd']:.2f}`",
        f"- Win rate: `{result['win_rate_pct']:.2f}%`",
        f"- Profit factor: `{result['profit_factor']}`",
        f"- Stress net: `${result['stress_net_reference_usd']:.2f}`",
        f"- H1 intrabar drawdown: `${result['max_h1_intrabar_drawdown_usd']:.2f}` / `{result['max_h1_intrabar_drawdown_pct']:.2f}%`",
        f"- Raw structural opportunities: `{payload['incidence']['raw']['opportunities']}`",
        f"- Locked census status using the H1-open proxy: `{payload['proxy_census_status']}`",
        "",
        "Entry is the native next-H1 open with the captured H1 spread. Same-H1 stop/target ambiguity is resolved against the strategy. This screen can reject R6, but cannot promote it.",
        "",
    ]
    (output / "A1_XAU_R6_OWNER_DIRECTED_BAR_SCREEN_20260713.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tester-root", type=Path, default=DEFAULT_TESTER_ROOT)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    detector = load_detector()
    capture = args.capture_dir or find_capture_dir(args.tester_root)
    contract = load_contract(capture / "native_contract.tsv", detector)
    h1_path = load_h1_path(capture / "native_h1_bars.tsv")
    h1 = tuple(detector.Bar(bar.time, bar.open, bar.high, bar.low, bar.close) for bar in h1_path)
    h4 = load_bars(capture / "native_h4_bars.tsv", detector)
    d1 = load_bars(capture / "native_d1_bars.tsv", detector)
    native_router = load_native_router(capture / "native_router_rows.tsv")

    original_router = detector.classify_router
    detector.classify_router = lambda *, h1, h4, d1, decision: native_router.get(decision, "UNKNOWN")
    try:
        structural = detector.detect_structural_windows(h4=h4, h1=h1, d1=d1, contract=contract)
    finally:
        detector.classify_router = original_router

    rows, proxy_rejected = candidate_rows(structural, h1_path, contract, detector)
    incidence = detector.incidence_report(rows)
    proxy_status = detector.locked_final_status(incidence)
    index = {bar.time: number for number, bar in enumerate(h1_path)}
    simulated = [simulate_candidate(row, h1_path, index, contract) for row in rows]
    trades, overlap_skipped = one_position(simulated)
    result = metrics(trades)
    payload = {
        "schema_version": "a1_xau_r6_owner_directed_bar_screen_v1",
        "status": "DEVELOPMENT_ONLY_NOT_EXACT_TICK_MT5",
        "verdict": "R6_LOCKED_DEFINITION_REJECTED_INSUFFICIENT_INCIDENCE",
        "rule_version": detector.RULE_VERSION,
        "capture_dir": str(capture),
        "data_start": h1_path[0].time.isoformat(),
        "data_end": h1_path[-1].time.isoformat(),
        "entry_proxy": "native next-H1 open plus captured H1 spread",
        "exit_ordering": "pessimistic stop-first when stop and target share one H1 bar",
        "fixed_target_r": TARGET_R,
        "fixed_reference_risk_usd": REFERENCE_RISK_USD,
        "ticket_stress_usd": TICKET_STRESS_USD,
        "structural_windows_before_entry_proxy": len(structural.windows),
        "entry_proxy_rejected": proxy_rejected,
        "overlapping_signals_skipped_by_one_position_rule": overlap_skipped,
        "funnel_before_entry_proxy": structural.funnel,
        "incidence": incidence,
        "proxy_census_status": proxy_status,
        "backtest": result,
        "limitations": [
            "full native tick entry stream not present in preserved warmup capture",
            "H1 OHLC path is used for SL/TP ordering",
            "native MT5 report and floating-equity path remain required for promotion",
            "all history through 2026-06-30 is development data",
        ],
    }
    write_outputs(args.output, payload, rows, trades)
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
