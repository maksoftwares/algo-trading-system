from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import csv
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def time_msc(value: Any) -> int:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Replay timestamp is not timezone-aware: {value}")
    return int(round(parsed.astimezone(UTC).timestamp() * 1000.0))


@dataclass(frozen=True)
class ExitFill:
    exit_time_msc: int
    volume_lots: float
    pnl_usd: float


@dataclass(frozen=True)
class FrozenTrade:
    candidate_id: str
    entry_time_msc: int
    exit_time_msc: int
    direction: str
    volume_lots: float
    entry_price: float
    entry_cost_usd: float
    final_pnl_usd: float
    would_veto: bool
    exit_fills: tuple[ExitFill, ...]


def trades_from_evidence(records: Sequence[Mapping[str, Any]]) -> list[FrozenTrade]:
    grouped: dict[str, dict[str, Mapping[str, Any]]] = {}
    for record in records:
        payload = record["payload"]
        candidate_id = str(payload["candidate_id"])
        event_type = str(record["event_type"])
        candidate_events = grouped.setdefault(candidate_id, {})
        if event_type in candidate_events:
            raise ValueError(
                f"Duplicate replay evidence event: {candidate_id}: {event_type}"
            )
        candidate_events[event_type] = payload
    trades: list[FrozenTrade] = []
    for candidate_id, events in sorted(grouped.items()):
        required = {
            "BASELINE_EXECUTION_DECISION",
            "BROKER_EXECUTION",
            "BROKER_OUTCOME",
        }
        if not required.issubset(events):
            continue
        decision = events["BASELINE_EXECUTION_DECISION"]
        execution = events["BROKER_EXECUTION"]
        outcome = events["BROKER_OUTCOME"]
        direction = str(execution["direction"]).upper()
        if direction not in ("LONG", "SHORT"):
            raise ValueError(f"Unsupported replay direction: {candidate_id}: {direction}")
        entry = time_msc(execution["broker_entry_time_utc"])
        exit_ = time_msc(outcome["broker_exit_time_utc"])
        if exit_ <= entry:
            raise ValueError(f"Replay exit does not follow entry: {candidate_id}")
        volume = float(execution["volume_lots"])
        if volume <= 0.0:
            raise ValueError(f"Replay volume is not positive: {candidate_id}")
        fills = tuple(
            ExitFill(
                exit_time_msc=time_msc(fill["exit_time_utc"]),
                volume_lots=float(fill["volume_lots"]),
                pnl_usd=float(fill["pnl_usd"]),
            )
            for fill in outcome.get("exit_fills", [])
        )
        if not fills:
            raise ValueError(f"Replay trade lacks immutable exit fills: {candidate_id}")
        if any(fill.exit_time_msc <= entry for fill in fills):
            raise ValueError(f"Replay exit fill does not follow entry: {candidate_id}")
        if max(fill.exit_time_msc for fill in fills) != exit_:
            raise ValueError(f"Replay final exit time does not reconcile: {candidate_id}")
        fill_volume = sum(fill.volume_lots for fill in fills)
        if abs(fill_volume - volume) > 1e-8:
            raise ValueError(f"Replay exit volume does not reconcile: {candidate_id}")
        final_pnl = float(outcome["broker_pnl_usd"])
        lifecycle_pnl = float(execution["entry_cost_usd"]) + sum(
            fill.pnl_usd for fill in fills
        )
        if abs(lifecycle_pnl - final_pnl) > 1e-8:
            raise ValueError(f"Replay lifecycle P/L does not reconcile: {candidate_id}")
        trades.append(
            FrozenTrade(
                candidate_id=candidate_id,
                entry_time_msc=entry,
                exit_time_msc=exit_,
                direction=direction,
                volume_lots=volume,
                entry_price=float(execution["entry_price"]),
                entry_cost_usd=float(execution["entry_cost_usd"]),
                final_pnl_usd=final_pnl,
                would_veto=bool(decision["would_veto"]),
                exit_fills=fills,
            )
        )
    return sorted(trades, key=lambda trade: (trade.entry_time_msc, trade.candidate_id))


class EquityState:
    def __init__(self, contract_units_per_lot: float) -> None:
        self.contract_units_per_lot = float(contract_units_per_lot)
        self.realized = 0.0
        self.long_units = 0.0
        self.long_entry_notional = 0.0
        self.short_units = 0.0
        self.short_entry_notional = 0.0

    def enter(self, trade: FrozenTrade) -> None:
        units = trade.volume_lots * self.contract_units_per_lot
        self.realized += trade.entry_cost_usd
        if trade.direction == "LONG":
            self.long_units += units
            self.long_entry_notional += trade.entry_price * units
        else:
            self.short_units += units
            self.short_entry_notional += trade.entry_price * units

    def exit_fill(self, trade: FrozenTrade, fill: ExitFill) -> None:
        units = fill.volume_lots * self.contract_units_per_lot
        if trade.direction == "LONG":
            self.long_units -= units
            self.long_entry_notional -= trade.entry_price * units
        else:
            self.short_units -= units
            self.short_entry_notional -= trade.entry_price * units
        self.realized += fill.pnl_usd

    def mark(self, bid: float, ask: float) -> float:
        return (
            self.realized
            + bid * self.long_units
            - self.long_entry_notional
            + self.short_entry_notional
            - ask * self.short_units
        )


def replay_ticks(
    trades: Sequence[FrozenTrade],
    ticks: Iterable[Mapping[str, Any]],
    *,
    contract_units_per_lot: float,
) -> dict[str, Any]:
    if not trades:
        raise ValueError("Exact tick replay requires at least one resolved trade")
    events = [(trade.entry_time_msc, 1, "ENTRY", trade, None, False) for trade in trades]
    for trade in trades:
        for index, fill in enumerate(trade.exit_fills):
            events.append(
                (
                    fill.exit_time_msc,
                    0,
                    "EXIT",
                    trade,
                    fill,
                    index == len(trade.exit_fills) - 1,
                )
            )
    events.sort(key=lambda item: (item[0], item[1], item[3].candidate_id))
    first_entry = min(trade.entry_time_msc for trade in trades)
    final_exit = max(trade.exit_time_msc for trade in trades)
    baseline = EquityState(contract_units_per_lot)
    challenger = EquityState(contract_units_per_lot)
    active: set[str] = set()
    seen_active: set[str] = set()
    event_index = 0
    last_tick = None
    tick_count = 0
    baseline_peak = 0.0
    challenger_peak = 0.0
    baseline_drawdown = 0.0
    challenger_drawdown = 0.0
    baseline_worst_time = None
    challenger_worst_time = None

    def apply_event(
        kind: str,
        trade: FrozenTrade,
        fill: ExitFill | None,
        final_fill: bool,
    ) -> None:
        if kind == "ENTRY":
            baseline.enter(trade)
            if not trade.would_veto:
                challenger.enter(trade)
            active.add(trade.candidate_id)
        else:
            if trade.candidate_id not in active:
                raise ValueError(f"Replay exit before entry: {trade.candidate_id}")
            if fill is None:
                raise ValueError(f"Replay exit lacks fill: {trade.candidate_id}")
            baseline.exit_fill(trade, fill)
            if not trade.would_veto:
                challenger.exit_fill(trade, fill)
            if final_fill:
                active.remove(trade.candidate_id)

    def observe(at_msc: int, bid: float, ask: float) -> None:
        nonlocal baseline_peak, challenger_peak
        nonlocal baseline_drawdown, challenger_drawdown
        nonlocal baseline_worst_time, challenger_worst_time
        baseline_value = baseline.mark(bid, ask)
        challenger_value = challenger.mark(bid, ask)
        baseline_peak = max(baseline_peak, baseline_value)
        challenger_peak = max(challenger_peak, challenger_value)
        baseline_current_dd = baseline_peak - baseline_value
        challenger_current_dd = challenger_peak - challenger_value
        if baseline_current_dd > baseline_drawdown:
            baseline_drawdown = baseline_current_dd
            baseline_worst_time = at_msc
        if challenger_current_dd > challenger_drawdown:
            challenger_drawdown = challenger_current_dd
            challenger_worst_time = at_msc

    for tick in ticks:
        tick_msc = int(tick["tick_time_msc"])
        if tick_msc < first_entry:
            continue
        if last_tick is not None and tick_msc < last_tick:
            raise ValueError("Tick replay input is not chronological")
        last_tick = tick_msc
        while event_index < len(events) and events[event_index][0] <= tick_msc:
            _, _, kind, trade, fill, final_fill = events[event_index]
            apply_event(kind, trade, fill, final_fill)
            event_index += 1
        seen_active.update(active)
        observe(tick_msc, float(tick["bid"]), float(tick["ask"]))
        tick_count += 1
        if tick_msc >= final_exit and event_index == len(events):
            break

    if last_tick is None or last_tick < final_exit or event_index != len(events):
        raise ValueError("Tick replay does not cover every broker exit")
    missing = sorted({trade.candidate_id for trade in trades} - seen_active)
    if missing:
        raise ValueError(f"Trades have no active tick coverage: {missing}")
    expected_baseline = sum(trade.final_pnl_usd for trade in trades)
    expected_challenger = sum(
        trade.final_pnl_usd for trade in trades if not trade.would_veto
    )
    if abs(baseline.realized - expected_baseline) > 1e-9:
        raise ValueError("Baseline final P/L does not reconcile")
    if abs(challenger.realized - expected_challenger) > 1e-9:
        raise ValueError("Challenger final P/L does not reconcile")
    return {
        "schema_version": "v60_v2_exact_tick_equity_replay_v1",
        "trades": len(trades),
        "vetoed_trades": sum(trade.would_veto for trade in trades),
        "ticks_evaluated": tick_count,
        "first_entry_time_msc": first_entry,
        "final_exit_time_msc": final_exit,
        "baseline_v60_net_pnl_usd": expected_baseline,
        "challenger_v2_net_pnl_usd": expected_challenger,
        "delta_net_pnl_usd": expected_challenger - expected_baseline,
        "baseline_v60_equity_drawdown_usd": baseline_drawdown,
        "challenger_v2_equity_drawdown_usd": challenger_drawdown,
        "delta_equity_drawdown_usd": challenger_drawdown - baseline_drawdown,
        "baseline_worst_drawdown_time_msc": baseline_worst_time,
        "challenger_worst_drawdown_time_msc": challenger_worst_time,
        "all_trades_have_tick_coverage": True,
    }


def iter_tick_files(
    paths: Sequence[Path],
    *,
    first_time_msc: int,
    final_time_msc: int,
) -> Iterable[dict[str, Any]]:
    for path in sorted(paths):
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"tick_time_msc", "bid", "ask"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"Tick file lacks required columns: {path}")
            for row in reader:
                tick_msc = int(row["tick_time_msc"])
                if tick_msc < first_time_msc:
                    continue
                if tick_msc > final_time_msc:
                    break
                yield {
                    "tick_time_msc": tick_msc,
                    "bid": float(row["bid"]),
                    "ask": float(row["ask"]),
                }
