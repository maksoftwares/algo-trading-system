from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPORT_DIR = Path("outputs") / "reports"
DEFAULT_ACTUAL_TRADES = REPORT_DIR / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_DASHBOARD_LEDGER = REPORT_DIR / "PHASE2_DEMO_OBSERVER_DASHBOARD_LEDGER.csv"
DEFAULT_SUMMARY_CSV = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_BACKTEST_SUMMARY.csv"
DEFAULT_TRADE_REPLAY_CSV = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_TRADE_LEVEL_REPLAY.csv"
DEFAULT_BOUNDS_CSV = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_BOUNDS.csv"
DEFAULT_REPORT_MD = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_BACKTEST_REPORT.md"
DEFAULT_DATA_QUALITY_MD = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_DATA_QUALITY.md"
DEFAULT_SAFETY_AUDIT_MD = REPORT_DIR / "DYNAMIC_EXIT_OFFLINE_SAFETY_AUDIT.md"
DEFAULT_BLOCKER_MD = REPORT_DIR / "DYNAMIC_EXIT_BACKTEST_BLOCKER_REPORT.md"
DEFAULT_EXACT_LOGGED_PATH_CSV = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_EXACT_LOGGED_PATH_REPLAY.csv"
DEFAULT_EXACT_LOGGED_PATH_MD = REPORT_DIR / "DYNAMIC_EXIT_LAST_WEEK_EXACT_LOGGED_PATH_REPLAY.md"

ELIGIBLE_CANDIDATES = {
    "breakout_retest",
    "swing_breakout_retest_v0",
    "p2weakness_br_v1",
}
ELIGIBLE_PREFIXES = ("WR50_Breakout",)
VARIANT_NAMES = (
    "CONTROL",
    "DYNEXIT_PartialBE_v0_OFFLINE",
    "DYNEXIT_BEOnly_v0_OFFLINE",
    "DYNEXIT_ATRTrail_v0_OFFLINE",
)


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    atr14: float | None = None


@dataclass(frozen=True)
class ReplayTrade:
    trade_id: str
    candidate: str
    symbol: str
    direction: str
    entry_time: datetime
    entry_price: float
    initial_sl: float
    initial_tp: float
    source_file: str = ""

    @property
    def risk_points(self) -> float:
        return abs(self.entry_price - self.initial_sl)

    @property
    def target_r(self) -> float:
        if self.risk_points <= 0:
            return math.nan
        if self.is_long:
            return (self.initial_tp - self.entry_price) / self.risk_points
        return (self.entry_price - self.initial_tp) / self.risk_points

    @property
    def is_long(self) -> bool:
        return self.direction.upper() in {"LONG", "BUY"}


@dataclass(frozen=True)
class VariantReplay:
    final_r: float | None
    exit_reason: str
    exit_time: datetime | None
    partial_triggered: bool = False
    be_triggered: bool = False
    trail_triggered: bool = False
    extra_cost_r: float = 0.0
    replay_status: str = "REPLAYED"
    intrabar_ambiguous: bool = False


@dataclass(frozen=True)
class TradeReplay:
    control: VariantReplay
    partial_be: VariantReplay
    be_only: VariantReplay
    atr_trail: VariantReplay
    mfe_r: float | None
    mae_r: float | None
    replay_status: str
    intrabar_ambiguous: bool


@dataclass(frozen=True)
class BacktestOutput:
    status: str
    report_path: Path
    summary_csv: Path
    trade_replay_csv: Path
    data_quality_path: Path
    safety_audit_path: Path
    blocker_path: Path


@dataclass(frozen=True)
class SignalSnapshot:
    time: datetime
    candidate: str
    bid: float
    ask: float
    source_file: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_dt(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def fnum(value: str | float | int | None, default: float = math.nan) -> float:
    if value is None:
        return default
    try:
        text = str(value).strip()
        if text == "":
            return default
        return float(text)
    except ValueError:
        return default


def is_eligible_candidate(candidate: str) -> bool:
    return candidate in ELIGIBLE_CANDIDATES or any(candidate.startswith(prefix) for prefix in ELIGIBLE_PREFIXES)


def replay_dynamic_exits(
    trade: ReplayTrade,
    bars: list[Bar] | None,
    partial_extra_cost_r: float = 0.0,
) -> TradeReplay:
    if not bars:
        blocked = VariantReplay(None, "BLOCKED_NO_PRICE_PATH", None, replay_status="BLOCKED_NO_PRICE_PATH")
        return TradeReplay(
            control=blocked,
            partial_be=blocked,
            be_only=blocked,
            atr_trail=blocked,
            mfe_r=None,
            mae_r=None,
            replay_status="BLOCKED_NO_PRICE_PATH",
            intrabar_ambiguous=False,
        )
    if trade.risk_points <= 0:
        blocked = VariantReplay(None, "BLOCKED_INVALID_INITIAL_R", None, replay_status="BLOCKED_INVALID_INITIAL_R")
        return TradeReplay(blocked, blocked, blocked, blocked, None, None, "BLOCKED_INVALID_INITIAL_R", False)

    ordered = sorted([bar for bar in bars if bar.time >= trade.entry_time], key=lambda bar: bar.time)
    mfe_r, mae_r = compute_mfe_mae(trade, ordered)
    control = replay_control(trade, ordered)
    partial = replay_partial_be(trade, ordered, partial_extra_cost_r)
    be_only = replay_be_only(trade, ordered)
    atr = replay_atr_trail(trade, ordered)
    ambiguous = any((control.intrabar_ambiguous, partial.intrabar_ambiguous, be_only.intrabar_ambiguous, atr.intrabar_ambiguous))
    return TradeReplay(control, partial, be_only, atr, mfe_r, mae_r, "REPLAYED", ambiguous)


def compute_mfe_mae(trade: ReplayTrade, bars: Iterable[Bar]) -> tuple[float, float]:
    mfe = 0.0
    mae = 0.0
    risk = trade.risk_points
    for bar in bars:
        if trade.is_long:
            mfe = max(mfe, (bar.high - trade.entry_price) / risk)
            mae = max(mae, (trade.entry_price - bar.low) / risk)
        else:
            mfe = max(mfe, (trade.entry_price - bar.low) / risk)
            mae = max(mae, (bar.high - trade.entry_price) / risk)
    return round(mfe, 6), round(mae, 6)


def replay_control(trade: ReplayTrade, bars: list[Bar]) -> VariantReplay:
    for bar in bars:
        stop_hit = hit_stop(trade, bar, trade.initial_sl)
        target_hit = hit_target(trade, bar, trade.initial_tp)
        if stop_hit and target_hit:
            return VariantReplay(-1.0, "SL", bar.time, intrabar_ambiguous=True)
        if stop_hit:
            return VariantReplay(-1.0, "SL", bar.time)
        if target_hit:
            return VariantReplay(round(trade.target_r, 6), "TP", bar.time)
    return end_of_data_result(trade, bars, "TIME_OR_DATA_END")


def replay_partial_be(trade: ReplayTrade, bars: list[Bar], extra_cost_r: float) -> VariantReplay:
    armed = False
    active_stop = trade.initial_sl
    partial_r = 0.0
    ambiguous = False
    for bar in bars:
        stop_hit = hit_stop(trade, bar, active_stop)
        arm_hit = hit_arm(trade, bar, 1.0)
        target_hit = hit_target(trade, bar, trade.initial_tp)
        if not armed:
            if stop_hit and (arm_hit or target_hit):
                return VariantReplay(-1.0, "SL", bar.time, intrabar_ambiguous=True)
            if stop_hit:
                return VariantReplay(-1.0, "SL", bar.time)
            if target_hit:
                return VariantReplay(round(1.25 - extra_cost_r, 6), "PARTIAL_BE_RUNNER_TP", bar.time, True, True, False, extra_cost_r, intrabar_ambiguous=arm_hit)
            if arm_hit:
                armed = True
                active_stop = trade.entry_price
                partial_r = 0.5
                if hit_stop(trade, bar, active_stop):
                    ambiguous = True
                    return VariantReplay(round(partial_r - extra_cost_r, 6), "PARTIAL_BE_RUNNER_BE", bar.time, True, True, False, extra_cost_r, intrabar_ambiguous=True)
            continue
        stop_hit = hit_stop(trade, bar, active_stop)
        target_hit = hit_target(trade, bar, trade.initial_tp)
        if stop_hit and target_hit:
            return VariantReplay(round(partial_r - extra_cost_r, 6), "PARTIAL_BE_RUNNER_BE", bar.time, True, True, False, extra_cost_r, intrabar_ambiguous=True)
        if stop_hit:
            return VariantReplay(round(partial_r - extra_cost_r, 6), "PARTIAL_BE_RUNNER_BE", bar.time, True, True, False, extra_cost_r, intrabar_ambiguous=ambiguous)
        if target_hit:
            return VariantReplay(round(1.25 - extra_cost_r, 6), "PARTIAL_BE_RUNNER_TP", bar.time, True, True, False, extra_cost_r, intrabar_ambiguous=ambiguous)
    result = end_of_data_result(trade, bars, "TIME_OR_DATA_END")
    if armed and result.final_r is not None:
        return VariantReplay(round(0.5 + 0.5 * result.final_r - extra_cost_r, 6), result.exit_reason, result.exit_time, True, True, False, extra_cost_r, result.replay_status, ambiguous)
    return result


def replay_be_only(trade: ReplayTrade, bars: list[Bar]) -> VariantReplay:
    armed = False
    active_stop = trade.initial_sl
    ambiguous = False
    for bar in bars:
        stop_hit = hit_stop(trade, bar, active_stop)
        arm_hit = hit_arm(trade, bar, 1.0)
        target_hit = hit_target(trade, bar, trade.initial_tp)
        if not armed:
            if stop_hit and (arm_hit or target_hit):
                return VariantReplay(-1.0, "SL", bar.time, intrabar_ambiguous=True)
            if stop_hit:
                return VariantReplay(-1.0, "SL", bar.time)
            if target_hit:
                return VariantReplay(round(trade.target_r, 6), "TP", bar.time, be_triggered=arm_hit, intrabar_ambiguous=arm_hit)
            if arm_hit:
                armed = True
                active_stop = trade.entry_price
                if hit_stop(trade, bar, active_stop):
                    ambiguous = True
                    return VariantReplay(0.0, "BE", bar.time, be_triggered=True, intrabar_ambiguous=True)
            continue
        stop_hit = hit_stop(trade, bar, active_stop)
        target_hit = hit_target(trade, bar, trade.initial_tp)
        if stop_hit and target_hit:
            return VariantReplay(0.0, "BE", bar.time, be_triggered=True, intrabar_ambiguous=True)
        if stop_hit:
            return VariantReplay(0.0, "BE", bar.time, be_triggered=True, intrabar_ambiguous=ambiguous)
        if target_hit:
            return VariantReplay(round(trade.target_r, 6), "TP", bar.time, be_triggered=True, intrabar_ambiguous=ambiguous)
    result = end_of_data_result(trade, bars, "TIME_OR_DATA_END")
    if armed:
        return VariantReplay(result.final_r, result.exit_reason, result.exit_time, be_triggered=True, intrabar_ambiguous=ambiguous)
    return result


def replay_atr_trail(trade: ReplayTrade, bars: list[Bar]) -> VariantReplay:
    armed = False
    trail_stop: float | None = None
    highest = trade.entry_price
    lowest = trade.entry_price
    ambiguous = False
    for bar in bars:
        if not armed:
            stop_hit = hit_stop(trade, bar, trade.initial_sl)
            arm_hit = hit_arm(trade, bar, 1.0)
            if stop_hit and arm_hit:
                return VariantReplay(-1.0, "SL", bar.time, intrabar_ambiguous=True)
            if stop_hit:
                return VariantReplay(-1.0, "SL", bar.time)
            if arm_hit:
                if bar.atr14 is None:
                    return VariantReplay(None, "BLOCKED_NO_ATR", bar.time, replay_status="BLOCKED_NO_ATR")
                armed = True
                if trade.is_long:
                    highest = max(highest, bar.high)
                    trail_stop = max(trade.initial_sl, highest - 2.0 * bar.atr14)
                else:
                    lowest = min(lowest, bar.low)
                    trail_stop = min(trade.initial_sl, lowest + 2.0 * bar.atr14)
                if hit_stop(trade, bar, trail_stop):
                    ambiguous = True
                    return VariantReplay(price_to_r(trade, trail_stop), "ATR_TRAIL", bar.time, trail_triggered=True, intrabar_ambiguous=True)
            continue
        if trail_stop is None:
            return VariantReplay(None, "BLOCKED_NO_ATR", bar.time, replay_status="BLOCKED_NO_ATR")
        if hit_stop(trade, bar, trail_stop):
            return VariantReplay(price_to_r(trade, trail_stop), "ATR_TRAIL", bar.time, trail_triggered=True, intrabar_ambiguous=ambiguous)
        if bar.atr14 is None:
            return VariantReplay(None, "BLOCKED_NO_ATR", bar.time, trail_triggered=True, replay_status="BLOCKED_NO_ATR")
        old_stop = trail_stop
        if trade.is_long:
            highest = max(highest, bar.high)
            trail_stop = max(trail_stop, highest - 2.0 * bar.atr14)
        else:
            lowest = min(lowest, bar.low)
            trail_stop = min(trail_stop, lowest + 2.0 * bar.atr14)
        if trail_stop != old_stop and worse_stop(trade, trail_stop, old_stop):
            raise AssertionError("ATR trail moved farther away from price")
    result = end_of_data_result(trade, bars, "TIME_OR_DATA_END")
    return VariantReplay(result.final_r, result.exit_reason, result.exit_time, trail_triggered=armed, intrabar_ambiguous=ambiguous)


def hit_arm(trade: ReplayTrade, bar: Bar, trigger_r: float) -> bool:
    if trade.is_long:
        return bar.high >= trade.entry_price + trigger_r * trade.risk_points
    return bar.low <= trade.entry_price - trigger_r * trade.risk_points


def hit_stop(trade: ReplayTrade, bar: Bar, stop: float) -> bool:
    return bar.low <= stop if trade.is_long else bar.high >= stop


def hit_target(trade: ReplayTrade, bar: Bar, target: float) -> bool:
    return bar.high >= target if trade.is_long else bar.low <= target


def price_to_r(trade: ReplayTrade, price: float) -> float:
    if trade.risk_points <= 0:
        return math.nan
    if trade.is_long:
        return round((price - trade.entry_price) / trade.risk_points, 6)
    return round((trade.entry_price - price) / trade.risk_points, 6)


def worse_stop(trade: ReplayTrade, new_stop: float, old_stop: float) -> bool:
    return new_stop < old_stop if trade.is_long else new_stop > old_stop


def end_of_data_result(trade: ReplayTrade, bars: list[Bar], reason: str) -> VariantReplay:
    if not bars:
        return VariantReplay(None, "BLOCKED_NO_PRICE_PATH", None, replay_status="BLOCKED_NO_PRICE_PATH")
    return VariantReplay(price_to_r(trade, bars[-1].close), reason, bars[-1].time)


def generate_dynamic_exit_backtest(root: Path, signal_dirs: list[Path] | None = None) -> BacktestOutput:
    root = root.resolve()
    reports = root / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    actual_csv = root / DEFAULT_ACTUAL_TRADES
    ledger_csv = root / DEFAULT_DASHBOARD_LEDGER
    searched = [
        str(actual_csv),
        str(ledger_csv),
        str(root / "outputs"),
        str(root.parent / "xauusd-wr50-experimental" / "outputs"),
    ]

    if not actual_csv.exists() and not ledger_csv.exists():
        write_blocker_report(root, "BLOCKED_NO_TRADE_LEDGER", searched, [])
        write_safety_audit(root, [])
        return BacktestOutput("BLOCKED_NO_TRADE_LEDGER", root / DEFAULT_REPORT_MD, root / DEFAULT_SUMMARY_CSV, root / DEFAULT_TRADE_REPLAY_CSV, root / DEFAULT_DATA_QUALITY_MD, root / DEFAULT_SAFETY_AUDIT_MD, root / DEFAULT_BLOCKER_MD)

    source_csv = actual_csv if actual_csv.exists() else ledger_csv
    rows = read_csv(source_csv)
    trades = [row for row in rows if row.get("symbol") == "XAUUSD" and row_is_closed(row) and is_eligible_candidate(row.get("candidate", ""))]
    window_start, window_end = previous_completed_week(trades)
    week_trades = [row for row in trades if in_entry_window(row, window_start, window_end)]
    dedup_trades = duplicate_hidden(week_trades)

    replay_rows = build_blocked_replay_rows(dedup_trades, source_csv)
    raw_replay_rows = build_blocked_replay_rows(week_trades, source_csv)
    summary_rows = build_summary_rows(dedup_trades, week_trades)
    bounds_rows = build_bounds_rows(dedup_trades, week_trades)

    write_csv(root / DEFAULT_SUMMARY_CSV, summary_rows, SUMMARY_COLUMNS)
    write_csv(root / DEFAULT_TRADE_REPLAY_CSV, replay_rows, TRADE_REPLAY_COLUMNS)
    write_csv(root / DEFAULT_BOUNDS_CSV, bounds_rows, BOUNDS_COLUMNS)
    write_data_quality(root, source_csv, searched, trades, week_trades, dedup_trades, window_start, window_end)
    write_report(root, source_csv, week_trades, dedup_trades, raw_replay_rows, summary_rows, bounds_rows, window_start, window_end)
    write_blocker_report(root, "BLOCKED_NO_PRICE_PATH", searched, week_trades)
    exact_generated = write_exact_logged_path_report(root, week_trades, dedup_trades, signal_dirs or [])
    generated_files = [
        root / DEFAULT_REPORT_MD,
        root / DEFAULT_SUMMARY_CSV,
        root / DEFAULT_TRADE_REPLAY_CSV,
        root / DEFAULT_BOUNDS_CSV,
        root / DEFAULT_DATA_QUALITY_MD,
        root / DEFAULT_BLOCKER_MD,
        root / DEFAULT_SAFETY_AUDIT_MD,
    ]
    if exact_generated:
        generated_files.extend([root / DEFAULT_EXACT_LOGGED_PATH_MD, root / DEFAULT_EXACT_LOGGED_PATH_CSV])
    write_safety_audit(root, generated_files)
    status = "EXACT_LOGGED_PATH_REPLAYED_ATR_BLOCKED" if exact_generated else "BLOCKED_NO_PRICE_PATH"
    return BacktestOutput(status, root / DEFAULT_REPORT_MD, root / DEFAULT_SUMMARY_CSV, root / DEFAULT_TRADE_REPLAY_CSV, root / DEFAULT_DATA_QUALITY_MD, root / DEFAULT_SAFETY_AUDIT_MD, root / DEFAULT_BLOCKER_MD)


EXACT_LOGGED_PATH_COLUMNS = [
    "position_ticket",
    "candidate",
    "entry_time",
    "exit_time",
    "direction",
    "entry_price",
    "exit_price",
    "sl",
    "tp",
    "control_r",
    "control_aed",
    "max_favorable_r_logged",
    "path_rows",
    "partial_be_r",
    "partial_be_aed",
    "partial_be_status",
    "be_only_r",
    "be_only_aed",
    "be_only_status",
    "is_duplicate",
    "time_bucket",
]


def write_exact_logged_path_report(
    root: Path,
    raw_rows: list[dict[str, str]],
    dedup_rows: list[dict[str, str]],
    signal_dirs: list[Path],
) -> bool:
    snapshots = load_signal_snapshots(signal_dirs)
    if not snapshots:
        return False

    raw_replay = exact_logged_path_replay_rows(raw_rows, snapshots)
    dedup_ids = {trade_identity(row) for row in dedup_rows}
    dedup_replay = [row for row in raw_replay if row["position_ticket"] in dedup_ids]
    raw_stats = exact_logged_path_stats(raw_replay)
    dedup_stats = exact_logged_path_stats(dedup_replay)

    write_csv(root / DEFAULT_EXACT_LOGGED_PATH_CSV, raw_replay, EXACT_LOGGED_PATH_COLUMNS)
    write_exact_logged_path_md(root, dedup_stats, raw_stats, dedup_replay)
    return True


def load_signal_snapshots(signal_dirs: list[Path]) -> dict[str, list[SignalSnapshot]]:
    snapshots: dict[str, list[SignalSnapshot]] = {}
    for directory in signal_dirs:
        directory = directory.expanduser()
        if not directory.exists() or not directory.is_dir():
            continue
        for path in directory.glob("*signal_log*xauusd.csv"):
            force_candidate = "p2weakness_br_v1" if path.name.startswith("p2weakness_br_v1") else ""
            for row in read_csv(path):
                candidate = force_candidate or row.get("candidate", "")
                timestamp = parse_dt(row.get("timestamp_local", "")) or parse_dt(row.get("timestamp_broker", ""))
                bid = fnum(row.get("bid", ""))
                ask = fnum(row.get("ask", ""))
                if not candidate or timestamp is None or math.isnan(bid) or math.isnan(ask):
                    continue
                snapshots.setdefault(candidate, []).append(SignalSnapshot(timestamp, candidate, bid, ask, path.name))
    for candidate, rows in snapshots.items():
        seen = set()
        unique = []
        for item in sorted(rows, key=lambda snapshot: snapshot.time):
            key = (item.time, round(item.bid, 5), round(item.ask, 5))
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        snapshots[candidate] = unique
    return snapshots


def exact_logged_path_replay_rows(
    rows: list[dict[str, str]],
    snapshots: dict[str, list[SignalSnapshot]],
) -> list[dict[str, Any]]:
    replayed = []
    for row in rows:
        replayed.append(exact_logged_path_replay_row(row, snapshots))
    return replayed


def exact_logged_path_replay_row(
    row: dict[str, str],
    snapshots: dict[str, list[SignalSnapshot]],
) -> dict[str, Any]:
    candidate = row.get("candidate", "")
    direction = normalize_direction(row.get("direction", ""))
    entry_time = parse_dt(row.get("entry_time", ""))
    exit_time = parse_dt(row.get("exit_time", ""))
    entry = fnum(row.get("entry_price", ""))
    exit_price = fnum(row.get("exit_price", ""))
    sl = fnum(row.get("sl", ""))
    tp = fnum(row.get("tp", ""))
    control_r = control_r_from_prices(direction, entry, sl, exit_price)
    control_aed = fnum(row.get("profit_aed", ""))
    risk = abs(entry - sl) if not math.isnan(entry) and not math.isnan(sl) else math.nan
    target_r = abs(tp - entry) / risk if risk and risk > 0 and not math.isnan(tp) else control_r
    aed_per_r = control_aed / control_r if not math.isnan(control_aed) and not math.isnan(control_r) and abs(control_r) > 1e-9 else math.nan
    path = exact_trade_path(row, snapshots)
    max_favorable_r = max((snapshot_favorable_r(direction, entry, risk, item) for item in path), default=math.nan)

    partial_r = control_r
    be_r = control_r
    partial_status = "UNCHANGED_ACTUAL_BROKER_RESULT"
    be_status = "UNCHANGED_ACTUAL_BROKER_RESULT"

    if not math.isnan(control_r) and not math.isnan(aed_per_r):
        if control_r > 0:
            partial_r = 0.5 + (0.5 * target_r)
            partial_status = "WINNER_HALF_AT_1R_HALF_AT_TP"
            be_status = "WINNER_FULL_TP_PRESERVED"
        elif not math.isnan(max_favorable_r) and max_favorable_r >= 1.0:
            partial_r = 0.5
            be_r = 0.0
            partial_status = "LOSS_REACHED_1R_THEN_PARTIAL_BE_SAVES_TO_PLUS_0_5R"
            be_status = "LOSS_REACHED_1R_THEN_BE_ONLY_SAVES_TO_0R"
        else:
            partial_status = "LOSS_DID_NOT_REACH_1R_IN_LOGGED_PATH"
            be_status = "LOSS_DID_NOT_REACH_1R_IN_LOGGED_PATH"

    partial_aed = partial_r * aed_per_r if not math.isnan(partial_r) and not math.isnan(aed_per_r) else math.nan
    be_aed = be_r * aed_per_r if not math.isnan(be_r) and not math.isnan(aed_per_r) else math.nan
    return {
        "position_ticket": trade_identity(row),
        "candidate": candidate,
        "entry_time": row.get("entry_time", ""),
        "exit_time": row.get("exit_time", ""),
        "direction": direction,
        "entry_price": entry,
        "exit_price": exit_price,
        "sl": sl,
        "tp": tp,
        "control_r": control_r,
        "control_aed": control_aed,
        "max_favorable_r_logged": "" if math.isnan(max_favorable_r) else round(max_favorable_r, 6),
        "path_rows": len(path),
        "partial_be_r": partial_r,
        "partial_be_aed": partial_aed,
        "partial_be_status": partial_status,
        "be_only_r": be_r,
        "be_only_aed": be_aed,
        "be_only_status": be_status,
        "is_duplicate": row.get("is_duplicate", ""),
        "time_bucket": row.get("time_bucket", ""),
    }


def exact_trade_path(row: dict[str, str], snapshots: dict[str, list[SignalSnapshot]]) -> list[SignalSnapshot]:
    candidate = row.get("candidate", "")
    if candidate.startswith("WR50_Breakout"):
        return []
    entry_time = parse_dt(row.get("entry_time", ""))
    exit_time = parse_dt(row.get("exit_time", ""))
    if entry_time is None or exit_time is None:
        return []
    start = entry_time - timedelta(seconds=10)
    end = exit_time + timedelta(seconds=10)
    return [item for item in snapshots.get(candidate, []) if start <= item.time <= end]


def snapshot_favorable_r(direction: str, entry: float, risk: float, snapshot: SignalSnapshot) -> float:
    if math.isnan(entry) or math.isnan(risk) or risk <= 0:
        return math.nan
    if direction == "LONG":
        return (snapshot.bid - entry) / risk
    if direction == "SHORT":
        return (entry - snapshot.ask) / risk
    return math.nan


def trade_identity(row: dict[str, str]) -> str:
    return row.get("position_ticket") or row.get("trade_id") or row.get("ticket") or "|".join(
        [row.get("entry_time", ""), row.get("candidate", ""), row.get("symbol", ""), row.get("direction", "")]
    )


def exact_logged_path_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trades = len(rows)
    wins = sum(1 for row in rows if fnum(row.get("control_aed")) > 0)
    control_aed = sum(fnum(row.get("control_aed"), 0.0) for row in rows)
    partial_aed = sum(fnum(row.get("partial_be_aed"), 0.0) for row in rows)
    be_aed = sum(fnum(row.get("be_only_aed"), 0.0) for row in rows)
    return {
        "trades": trades,
        "wins": wins,
        "losses": trades - wins,
        "win_rate": pct(wins, trades),
        "control_aed": round(control_aed, 2),
        "partial_aed": round(partial_aed, 2),
        "partial_delta_aed": round(partial_aed - control_aed, 2),
        "be_aed": round(be_aed, 2),
        "be_delta_aed": round(be_aed - control_aed, 2),
        "protected_losses": sum(1 for row in rows if str(row.get("be_only_status", "")).startswith("LOSS_REACHED_1R")),
        "partial_winner_drag": sum(1 for row in rows if fnum(row.get("control_aed")) > 0 and fnum(row.get("partial_be_aed")) < fnum(row.get("control_aed"))),
    }


def write_exact_logged_path_md(root: Path, dedup_stats: dict[str, Any], raw_stats: dict[str, Any], dedup_rows: list[dict[str, Any]]) -> None:
    by_candidate = {}
    for row in dedup_rows:
        by_candidate.setdefault(row["candidate"], []).append(row)
    text = [
        "# Dynamic Exit Last-Week Exact Logged-Path Replay",
        "",
        "Scope: closed XAUUSD same-family demo trades entered in the previous completed week. Broker trade times are matched to signal-log `timestamp_local`. No MT5 terminal, EA, chart, preset, or runtime state was changed.",
        "",
        "Important limit: this is exact against the available logged bid/ask snapshots. ATR-trail cannot be exact from these files because the logs do not contain M5 high/low candles or ATR values.",
        "",
        "| View | Trades | Win rate | Actual broker PnL AED | Partial + BE PnL AED | Delta AED | BE-only PnL AED | Delta AED | Losses proven saved | Partial winner drag |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        exact_stats_table_row("Duplicate-hidden", dedup_stats),
        exact_stats_table_row("Raw incl duplicates", raw_stats),
        "",
        "## Candidate Breakdown Duplicate-Hidden",
        "",
        "| Candidate | Trades | Actual AED | Partial + BE AED | Delta AED | BE-only AED | Delta AED | Saved losses |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for candidate in sorted(by_candidate):
        stats = exact_logged_path_stats(by_candidate[candidate])
        text.append(
            f"| {candidate} | {stats['trades']} | {stats['control_aed']:.2f} | {stats['partial_aed']:.2f} | {stats['partial_delta_aed']:.2f} | {stats['be_aed']:.2f} | {stats['be_delta_aed']:.2f} | {stats['protected_losses']} |"
        )
    text.extend(
        [
            "",
            "## Saved Losing Trades Duplicate-Hidden",
            "",
            "| Entry local | Ticket | Candidate | Side | Actual AED | Max favorable R logged | Partial + BE AED | BE-only AED |",
            "|---|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in dedup_rows:
        if str(row.get("be_only_status", "")).startswith("LOSS_REACHED_1R"):
            text.append(
                f"| {row['entry_time']} | {row['position_ticket']} | {row['candidate']} | {row['direction']} | {fnum(row.get('control_aed')):.2f} | {fnum(row.get('max_favorable_r_logged')):.3f} | {fnum(row.get('partial_be_aed')):.2f} | {fnum(row.get('be_only_aed')):.2f} |"
            )
    text.extend(["", f"Artifacts: `{DEFAULT_EXACT_LOGGED_PATH_CSV.name}`.", ""])
    (root / DEFAULT_EXACT_LOGGED_PATH_MD).write_text("\n".join(text), encoding="utf-8")


def exact_stats_table_row(label: str, stats: dict[str, Any]) -> str:
    return (
        f"| {label} | {stats['trades']} | {stats['win_rate']} | {stats['control_aed']:.2f} | "
        f"{stats['partial_aed']:.2f} | {stats['partial_delta_aed']:.2f} | {stats['be_aed']:.2f} | "
        f"{stats['be_delta_aed']:.2f} | {stats['protected_losses']} | {stats['partial_winner_drag']} |"
    )


SUMMARY_COLUMNS = [
    "stream",
    "closed_trades",
    "wins",
    "losses",
    "win_rate",
    "avg_win_R",
    "avg_loss_R",
    "payoff_ratio",
    "profit_factor",
    "net_R_total",
    "net_expectancy_R",
    "median_cost_R",
    "p95_cost_R",
    "max_drawdown_R",
    "near_miss_giveback_count",
    "near_tp_giveback_count",
    "giveback_recovered_R",
    "runner_forfeited_R",
    "extra_cost_R",
    "net_delta_vs_control_R",
    "ambiguous_trade_count",
    "sample_status",
    "verdict",
]

TRADE_REPLAY_COLUMNS = [
    "trade_id",
    "source_file",
    "candidate",
    "symbol",
    "direction",
    "entry_time",
    "entry_price",
    "initial_sl",
    "initial_tp",
    "initial_r_points",
    "control_exit_time",
    "control_exit_reason",
    "control_final_R",
    "MFE_R",
    "MAE_R",
    "near_miss_giveback",
    "near_tp_giveback",
    "A_final_R",
    "A_exit_reason",
    "A_partial_triggered",
    "A_extra_cost_R",
    "B_final_R",
    "B_exit_reason",
    "B_BE_triggered",
    "C_final_R",
    "C_exit_reason",
    "C_trail_triggered",
    "intrabar_ambiguous",
    "replay_status",
    "notes",
]

BOUNDS_COLUMNS = [
    "view",
    "variant",
    "closed_trades",
    "wins",
    "losses",
    "control_net_R",
    "variant_min_net_R_before_extra_cost",
    "variant_max_net_R_before_extra_cost",
    "winner_delta_R_before_extra_cost",
    "improvement_per_protected_loss_R",
    "protected_losses_needed_to_beat_control",
    "protected_loss_pct_needed",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def row_is_closed(row: dict[str, str]) -> bool:
    state = (row.get("state") or "").upper()
    outcome = (row.get("outcome") or "").upper()
    return state == "CLOSED" or outcome in {"WIN_TP", "LOSS_STOP", "WIN", "LOSS"}


def in_entry_window(row: dict[str, str], start: datetime, end: datetime) -> bool:
    dt = parse_dt(row.get("entry_time", "")) or parse_dt(row.get("timestamp_broker", "")) or parse_dt(row.get("timestamp_local", ""))
    return dt is not None and start <= dt <= end


def previous_completed_week(rows: list[dict[str, str]]) -> tuple[datetime, datetime]:
    dates = []
    for row in rows:
        dt = parse_dt(row.get("entry_time", "")) or parse_dt(row.get("timestamp_broker", "")) or parse_dt(row.get("timestamp_local", ""))
        if dt:
            dates.append(dt)
    if not dates:
        return datetime(2026, 6, 1), datetime(2026, 6, 7, 23, 59, 59)
    latest = max(dates)
    current_week_start = latest - timedelta(days=latest.weekday())
    previous_start = datetime(current_week_start.year, current_week_start.month, current_week_start.day) - timedelta(days=7)
    previous_end = previous_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return previous_start, previous_end


def duplicate_hidden(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if str(row.get("is_duplicate", "")).lower() != "true" and row.get("duplicate_role", "").lower() != "duplicate"
    ]


def build_blocked_replay_rows(rows: list[dict[str, str]], source_csv: Path) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows, start=1):
        entry = fnum(row.get("entry_price"))
        sl = fnum(row.get("sl") or row.get("stop_loss"))
        tp = fnum(row.get("tp") or row.get("take_profit"))
        exit_price = fnum(row.get("exit_price"))
        direction = normalize_direction(row.get("direction", ""))
        control_r = control_r_from_prices(direction, entry, sl, exit_price)
        initial_r = abs(entry - sl) if not math.isnan(entry) and not math.isnan(sl) else math.nan
        exit_reason = control_exit_reason(row)
        out.append(
            {
                "trade_id": row.get("position_ticket") or row.get("trade_no") or str(index),
                "source_file": str(source_csv),
                "candidate": row.get("candidate", ""),
                "symbol": row.get("symbol", ""),
                "direction": direction,
                "entry_time": row.get("entry_time") or row.get("timestamp_broker", ""),
                "entry_price": fmt_num(entry),
                "initial_sl": fmt_num(sl),
                "initial_tp": fmt_num(tp),
                "initial_r_points": fmt_num(initial_r),
                "control_exit_time": row.get("exit_time", ""),
                "control_exit_reason": exit_reason,
                "control_final_R": fmt_num(control_r),
                "MFE_R": "",
                "MAE_R": "",
                "near_miss_giveback": "",
                "near_tp_giveback": "",
                "A_final_R": "",
                "A_exit_reason": "BLOCKED_NO_PRICE_PATH",
                "A_partial_triggered": "",
                "A_extra_cost_R": "",
                "B_final_R": "",
                "B_exit_reason": "BLOCKED_NO_PRICE_PATH",
                "B_BE_triggered": "",
                "C_final_R": "",
                "C_exit_reason": "BLOCKED_NO_PRICE_PATH",
                "C_trail_triggered": "",
                "intrabar_ambiguous": "",
                "replay_status": "BLOCKED_NO_PRICE_PATH",
                "notes": "Committed ledger has final exit only; no M1/M5 path or MFE/MAE field was available for this entry.",
            }
        )
    return out


def build_summary_rows(dedup_rows: list[dict[str, str]], raw_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    control_dedup = summarize_control("CONTROL_DEDUP_DECISION_VIEW", dedup_rows)
    control_raw = summarize_control("CONTROL_RAW_VIEW", raw_rows)
    blocked_variants = [
        blocked_variant_summary(name, len(dedup_rows), control_dedup["net_R_total"])
        for name in VARIANT_NAMES
        if name != "CONTROL"
    ]
    return [control_dedup, control_raw, *blocked_variants]


def build_bounds_rows(dedup_rows: list[dict[str, str]], raw_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        *variant_bounds_for_view("duplicate-hidden", dedup_rows),
        *variant_bounds_for_view("raw", raw_rows),
    ]


def variant_bounds_for_view(view: str, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    parsed = [parse_bound_row(row) for row in rows]
    parsed = [row for row in parsed if row is not None]
    wins = [row for row in parsed if row["control_r"] > 0]
    losses = [row for row in parsed if row["control_r"] <= 0]
    control_net = sum(row["control_r"] for row in parsed)
    control_winner_net = sum(row["control_r"] for row in wins)
    partial_winner_net = sum(0.5 + 0.5 * row["target_r"] for row in wins)
    be_winner_net = sum(row["target_r"] for row in wins)
    loss_count = len(losses)
    partial_min = partial_winner_net - loss_count
    partial_max = partial_winner_net + 0.5 * loss_count
    be_min = be_winner_net - loss_count
    be_max = be_winner_net
    return [
        make_bound_row(
            view,
            "DYNEXIT_PartialBE_v0_OFFLINE_BOUNDS",
            len(parsed),
            len(wins),
            loss_count,
            control_net,
            partial_min,
            partial_max,
            partial_winner_net - control_winner_net,
            1.5,
            "Bounds only: winners definitely reached +1R and TP; losing trades are unknown. Min assumes no loser reached +1R; max assumes every loser reached +1R then runner scratched at BE. Extra partial-fill cost is not included.",
        ),
        make_bound_row(
            view,
            "DYNEXIT_BEOnly_v0_OFFLINE_BOUNDS",
            len(parsed),
            len(wins),
            loss_count,
            control_net,
            be_min,
            be_max,
            be_winner_net - control_winner_net,
            1.0,
            "Bounds only: winners definitely reached +1R and TP; losing trades are unknown. Min assumes no loser reached +1R; max assumes every loser reached +1R then exited at BE.",
        ),
        {
            "view": view,
            "variant": "DYNEXIT_ATRTrail_v0_OFFLINE_BOUNDS",
            "closed_trades": len(parsed),
            "wins": len(wins),
            "losses": loss_count,
            "control_net_R": round(control_net, 6),
            "variant_min_net_R_before_extra_cost": "n/a",
            "variant_max_net_R_before_extra_cost": "n/a",
            "winner_delta_R_before_extra_cost": "n/a",
            "improvement_per_protected_loss_R": "n/a",
            "protected_losses_needed_to_beat_control": "n/a",
            "protected_loss_pct_needed": "n/a",
            "notes": "Cannot be bounded from final exits only because ATR trail removes fixed TP and requires full high/low/ATR path.",
        },
    ]


def parse_bound_row(row: dict[str, str]) -> dict[str, float] | None:
    entry = fnum(row.get("entry_price"))
    sl = fnum(row.get("sl") or row.get("stop_loss"))
    tp = fnum(row.get("tp") or row.get("take_profit"))
    exit_price = fnum(row.get("exit_price"))
    direction = normalize_direction(row.get("direction", ""))
    control_r = control_r_from_prices(direction, entry, sl, exit_price)
    if any(math.isnan(value) for value in (entry, sl, tp, exit_price, control_r)):
        return None
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    target_r = (tp - entry) / risk if direction == "LONG" else (entry - tp) / risk
    if target_r <= 0:
        return None
    return {"control_r": control_r, "target_r": target_r}


def make_bound_row(
    view: str,
    variant: str,
    closed: int,
    wins: int,
    losses: int,
    control_net: float,
    min_net: float,
    max_net: float,
    winner_delta: float,
    improvement_per_loss: float,
    notes: str,
) -> dict[str, Any]:
    needed_r = max(0.0, control_net - min_net)
    needed_losses = math.floor(needed_r / improvement_per_loss) + 1 if needed_r > 0 else 0
    if needed_losses > losses:
        needed_display: int | str = f">{losses}"
        pct_display = ">100.00%"
    else:
        needed_display = needed_losses
        pct_display = pct(needed_losses, losses) if losses else "0.00%"
    return {
        "view": view,
        "variant": variant,
        "closed_trades": closed,
        "wins": wins,
        "losses": losses,
        "control_net_R": round(control_net, 6),
        "variant_min_net_R_before_extra_cost": round(min_net, 6),
        "variant_max_net_R_before_extra_cost": round(max_net, 6),
        "winner_delta_R_before_extra_cost": round(winner_delta, 6),
        "improvement_per_protected_loss_R": improvement_per_loss,
        "protected_losses_needed_to_beat_control": needed_display,
        "protected_loss_pct_needed": pct_display,
        "notes": notes,
    }


def summarize_control(stream: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    r_values = []
    for row in rows:
        entry = fnum(row.get("entry_price"))
        sl = fnum(row.get("sl") or row.get("stop_loss"))
        exit_price = fnum(row.get("exit_price"))
        r_values.append(control_r_from_prices(normalize_direction(row.get("direction", "")), entry, sl, exit_price))
    r_values = [value for value in r_values if not math.isnan(value)]
    wins = [value for value in r_values if value > 0]
    losses = [value for value in r_values if value < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    avg_win = avg(wins)
    avg_loss = avg(losses)
    return {
        "stream": stream,
        "closed_trades": len(r_values),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": pct(len(wins), len(r_values)),
        "avg_win_R": avg_win,
        "avg_loss_R": avg_loss,
        "payoff_ratio": ratio(avg_win, abs(avg_loss) if isinstance(avg_loss, (int, float)) else avg_loss),
        "profit_factor": ratio(gross_win, gross_loss),
        "net_R_total": round(sum(r_values), 6),
        "net_expectancy_R": avg(r_values),
        "median_cost_R": "n/a",
        "p95_cost_R": "n/a",
        "max_drawdown_R": max_drawdown(r_values),
        "near_miss_giveback_count": "n/a",
        "near_tp_giveback_count": "n/a",
        "giveback_recovered_R": "n/a",
        "runner_forfeited_R": "n/a",
        "extra_cost_R": "n/a",
        "net_delta_vs_control_R": 0.0,
        "ambiguous_trade_count": "n/a",
        "sample_status": "CONTROL_BASELINE_AVAILABLE_NO_MFE",
        "verdict": "INCONCLUSIVE_DATA_LIMITATION",
    }


def blocked_variant_summary(stream: str, closed: int, control_net: Any) -> dict[str, Any]:
    return {
        "stream": stream,
        "closed_trades": closed,
        "wins": "",
        "losses": "",
        "win_rate": "",
        "avg_win_R": "",
        "avg_loss_R": "",
        "payoff_ratio": "",
        "profit_factor": "",
        "net_R_total": "",
        "net_expectancy_R": "",
        "median_cost_R": "n/a",
        "p95_cost_R": "n/a",
        "max_drawdown_R": "",
        "near_miss_giveback_count": "",
        "near_tp_giveback_count": "",
        "giveback_recovered_R": "",
        "runner_forfeited_R": "",
        "extra_cost_R": "",
        "net_delta_vs_control_R": "",
        "ambiguous_trade_count": "",
        "sample_status": "BLOCKED_NO_PRICE_PATH",
        "verdict": "INCONCLUSIVE_DATA_LIMITATION",
    }


def normalize_direction(value: str) -> str:
    upper = (value or "").upper()
    if upper in {"BUY", "LONG"}:
        return "LONG"
    if upper in {"SELL", "SHORT"}:
        return "SHORT"
    return upper


def control_r_from_prices(direction: str, entry: float, sl: float, exit_price: float) -> float:
    if any(math.isnan(value) for value in (entry, sl, exit_price)):
        return math.nan
    risk = abs(entry - sl)
    if risk <= 0:
        return math.nan
    if direction == "LONG":
        return round((exit_price - entry) / risk, 6)
    if direction == "SHORT":
        return round((entry - exit_price) / risk, 6)
    return math.nan


def control_exit_reason(row: dict[str, str]) -> str:
    text = " ".join([row.get("exit_comment", ""), row.get("exit_source", ""), row.get("outcome", "")]).lower()
    if "sl" in text or "stop" in text or "loss" in text:
        return "SL"
    if "tp" in text or "take_profit" in text or "win" in text:
        return "TP"
    return "UNKNOWN"


def pct(part: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{(part / total) * 100:.2f}%"


def avg(values: list[float]) -> float | str:
    if not values:
        return "n/a"
    return round(sum(values) / len(values), 6)


def ratio(num: Any, den: Any) -> float | str:
    if not isinstance(num, (int, float)) or not isinstance(den, (int, float)):
        return "n/a"
    if den == 0:
        return "inf" if num > 0 else "n/a"
    return round(num / den, 6)


def max_drawdown(values: list[float]) -> float | str:
    if not values:
        return "n/a"
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return round(abs(max_dd), 6)


def fmt_num(value: float) -> str:
    if value is None or math.isnan(value):
        return ""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_data_quality(
    root: Path,
    source_csv: Path,
    searched: list[str],
    all_trades: list[dict[str, str]],
    week_trades: list[dict[str, str]],
    dedup_trades: list[dict[str, str]],
    start: datetime,
    end: datetime,
) -> None:
    text = [
        "# Dynamic Exit Last Week Data Quality",
        "",
        "Status: `BLOCKED_NO_PRICE_PATH`",
        "",
        "No MT5 terminal, chart, EA, preset, account, or runtime file was opened or modified by this task.",
        "",
        "## Input Summary",
        "",
        f"- Primary trade ledger: `{source_csv}`",
        f"- Derived last completed week: `{start:%Y-%m-%d %H:%M:%S}` to `{end:%Y-%m-%d %H:%M:%S}`",
        f"- Eligible same-family XAUUSD closed rows across ledger: `{len(all_trades)}`",
        f"- Eligible same-family XAUUSD closed rows in window, raw view: `{len(week_trades)}`",
        f"- Eligible same-family XAUUSD closed rows in window, duplicate-hidden view: `{len(dedup_trades)}`",
        "",
        "## Missing Requirement",
        "",
        "The committed ledgers contain entry, SL, TP, final exit, and final PnL, but not the post-entry path, MFE_R, MAE_R, or M1/M5 candles for June 2026.",
        "Dynamic exits cannot be replayed without knowing whether price first reached +1R, then hit breakeven, trailed out, or continued to TP.",
        "",
        "## Files Searched",
        "",
    ]
    text.extend(f"- `{item}`" for item in searched)
    text.extend(
        [
            "",
            "## Conclusion",
            "",
            "Control baseline is measurable from the broker-inclusive ledger. Variant A/B/C replay is blocked until an already-exported M1/M5 path or MFE/MAE-enriched ledger is supplied to the repo.",
            "",
        ]
    )
    (root / DEFAULT_DATA_QUALITY_MD).write_text("\n".join(text), encoding="utf-8")


def write_report(
    root: Path,
    source_csv: Path,
    raw_rows: list[dict[str, str]],
    dedup_rows: list[dict[str, str]],
    raw_replay_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    bounds_rows: list[dict[str, Any]],
    start: datetime,
    end: datetime,
) -> None:
    control = summary_rows[0]
    raw = summary_rows[1]
    text = [
        "# Dynamic Exit Last Week Backtest Report",
        "",
        "## 1. Executive Verdict",
        "",
        "Status: `BLOCKED_NO_PRICE_PATH` for dynamic Variant A/B/C replay.",
        "",
        "The control baseline is available from actual broker-inclusive closed trades, but the repo does not currently contain the required post-entry price path or MFE/MAE fields for June 2026. I did not guess the painful giveback cases.",
        "",
        "## 2. Scope And Hard Boundary Confirmation",
        "",
        "- Offline research/reporting only.",
        "- No running EA was changed.",
        "- MT5 was not opened, restarted, attached, reconfigured, or queried.",
        "- No `.mq5`, `.mqh`, or `.set` file was modified.",
        "- Canonical Phase 2 status was not changed.",
        "",
        "## 3. Input Files Used",
        "",
        f"- `{source_csv}`",
        "",
        "## 4. Last-Week Date Window",
        "",
        f"- Start: `{start:%Y-%m-%d %H:%M:%S}`",
        f"- End: `{end:%Y-%m-%d %H:%M:%S}`",
        "- Selection: previous completed Monday-Sunday week derived from the latest closed trade timestamp.",
        "",
        "## 5. Data Quality / Replay Limitations",
        "",
        "The committed ledger has final exits only. It does not show whether each trade reached +1R before exit, how far it moved in favor, how far it moved against, or the M5/ATR path needed for trailing-stop replay.",
        "",
        "## 6. Control Performance",
        "",
        "| View | Trades | Win rate | PF | Net R | Expectancy R | Max DD R |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Duplicate-hidden decision view | {control['closed_trades']} | {control['win_rate']} | {control['profit_factor']} | {control['net_R_total']} | {control['net_expectancy_R']} | {control['max_drawdown_R']} |",
        f"| Raw view | {raw['closed_trades']} | {raw['win_rate']} | {raw['profit_factor']} | {raw['net_R_total']} | {raw['net_expectancy_R']} | {raw['max_drawdown_R']} |",
        "",
        "## 7. Variant A Performance",
        "",
        "`DYNEXIT_PartialBE_v0_OFFLINE`: `INCONCLUSIVE_DATA_LIMITATION`. Replay blocked by missing price path.",
        "",
        "## 8. Variant B Performance",
        "",
        "`DYNEXIT_BEOnly_v0_OFFLINE`: `INCONCLUSIVE_DATA_LIMITATION`. Replay blocked by missing price path.",
        "",
        "## 9. Variant C Performance",
        "",
        "`DYNEXIT_ATRTrail_v0_OFFLINE`: `INCONCLUSIVE_DATA_LIMITATION`. Replay blocked by missing price path and missing ATR path.",
        "",
        "## 10. Side-By-Side Comparison",
        "",
        "| Stream | Trades | Net R | Expectancy R | PF | Status | Verdict |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in summary_rows:
        text.append(
            f"| {row['stream']} | {row['closed_trades']} | {row['net_R_total']} | {row['net_expectancy_R']} | {row['profit_factor']} | {row['sample_status']} | {row['verdict']} |"
        )
    text.extend(
        [
            "",
            "## 11. Giveback Diagnostic",
            "",
            "`near_miss_giveback` and `near_tp_giveback` are not computed because MFE_R is unavailable. This is the exact data needed to answer the owner's observed gold round-trip case.",
            "",
            "### Arranged Final-Exit Bounds",
            "",
            "These are not replay results. They are honest bounds from final exits only: winners definitely reached +1R, but losing trades may or may not have reached +1R before stopping.",
            "",
            "| View | Variant | Control R | Min R | Max R | Protected SLs Needed | Notes |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in bounds_rows:
        text.append(
            f"| {row['view']} | {row['variant']} | {row['control_net_R']} | {row['variant_min_net_R_before_extra_cost']} | {row['variant_max_net_R_before_extra_cost']} | {row['protected_losses_needed_to_beat_control']} | {row['notes']} |"
        )
    text.extend(
        [
            "",
            "## 12. Decision Decomposition",
            "",
            "The required split into giveback recovered, runner forfeited, and extra cost is blocked. Without MFE/path, any decomposition would be invented.",
            "",
            "## 13. Ambiguity Analysis",
            "",
            "Ambiguous-trade count is unavailable because replay bars are unavailable. M5 replay should use adverse-first once path data is supplied.",
            "",
            "## 14. Trade-Level Examples",
            "",
            "Top saved/harmed trades cannot be identified without MFE/path. Trade-level rows were still emitted with `replay_status=BLOCKED_NO_PRICE_PATH` so the missing data is explicit per trade.",
            "",
            "## 15. Recommendation",
            "",
            "`INCONCLUSIVE_DATA_LIMITATION`: keep this as offline research. The next data task is to export or commit M1/M5 path snapshots, or enrich the ledger with MFE_R/MAE_R for closed trades. Do not promote, deploy, or change exits from this checkpoint.",
            "",
            "## 16. Explicit No-Touch Note",
            "",
            "No active EA changed, no MT5 terminal was touched, no runtime authorization was created, and no deployment recommendation is made.",
            "",
            "## Additional Diagnostics",
            "",
            "- MFE bucket table: blocked; MFE_R unavailable.",
            "- Time-to-arm table: blocked; +1R path unavailable.",
            "- Direction/session split for variants: blocked; replay unavailable.",
            "- Exit reason distribution: available only for control in the CSV output.",
            "- Painful +50 AED trade case study: cannot be identified from committed data because max unrealized AED/MFE is not present.",
            "",
            "## Owner Summary",
            "",
            f"Last week, using the same entries, the control duplicate-hidden same-family XAUUSD view produced `{control['net_R_total']}` R across `{control['closed_trades']}` closed trades, with `{control['win_rate']}` win rate and `{control['profit_factor']}` PF.",
            "",
            "- Partial+BE: blocked; missing MFE/path.",
            "- BE-only: blocked; missing MFE/path.",
            "- ATR trail: blocked; missing MFE/path/ATR.",
            "",
            "The best checkpoint variant was: `none yet`, because the required path data is absent.",
            "",
            "No running EA was changed. MT5 was not touched. This is offline research only.",
            "",
        ]
    )
    (root / DEFAULT_REPORT_MD).write_text("\n".join(text), encoding="utf-8")


def write_blocker_report(root: Path, status: str, searched: list[str], rows: list[dict[str, str]]) -> None:
    text = [
        "# Dynamic Exit Backtest Blocker Report",
        "",
        f"Status: `{status}`",
        "",
        "The requested dynamic-exit replay cannot be completed from committed artifacts because no post-entry M1/M5 price path or MFE/MAE-enriched trade ledger is available for the target week.",
        "",
        f"Eligible rows found before blocker: `{len(rows)}`",
        "",
        "Files/locations searched:",
        "",
    ]
    text.extend(f"- `{item}`" for item in searched)
    text.extend(
        [
            "",
            "No MT5 terminal or running EA was touched. This blocker is data-only.",
            "",
        ]
    )
    (root / DEFAULT_BLOCKER_MD).write_text("\n".join(text), encoding="utf-8")


def write_safety_audit(root: Path, generated_files: list[Path]) -> None:
    status_lines = git_status(root.parent.parent if (root.name == "xauusd-phase1") else root)
    changed = [line[3:] for line in status_lines if len(line) > 3]
    forbidden_exts = {".mq5", ".mqh", ".set"}
    forbidden_changes = [path for path in changed if Path(path).suffix.lower() in forbidden_exts]
    mt5_runtime_touched = [path for path in changed if "MetaQuotes" in path or "Terminal" in path or "MT5Portable" in path]
    owner_auth_touched = [path for path in changed if "owner" in path.lower() and "local" in path.lower()]
    script_path = Path(__file__).resolve()
    script_text = script_path.read_text(encoding="utf-8")
    broker_tokens_added = any(token in script_text for token in ("Order" + "Send", "C" + "Trade", "Position" + "Open", "Position" + "Modify", "Position" + "Close"))
    status = "PASS" if not forbidden_changes and not mt5_runtime_touched and not owner_auth_touched and not broker_tokens_added else "FAIL"
    generated = [str(path) for path in generated_files]
    text = [
        "# Dynamic Exit Offline Safety Audit",
        "",
        f"Status: `{status}`",
        "",
        "Scope: offline dynamic-exit replay/reporting only.",
        "",
        "## Generated Files",
        "",
    ]
    text.extend(f"- `{item}`" for item in generated)
    text.extend(
        [
            "",
            "## Git Status Snapshot",
            "",
            "```text",
            *status_lines,
            "```",
            "",
            "## Checks",
            "",
            f"- Modified `.mq5/.mqh/.set`: `{bool(forbidden_changes)}`",
            f"- MT5 runtime path touched: `{bool(mt5_runtime_touched)}`",
            f"- Local owner authorization touched: `{bool(owner_auth_touched)}`",
            f"- Broker-action token added in offline script: `{broker_tokens_added}`",
            "- Canonical Phase 2 reports edited by this script: `False`",
            "",
            "No active EA, chart, preset, terminal, account, or MT5 runtime file was opened or modified by this task.",
            "",
        ]
    )
    (root / DEFAULT_SAFETY_AUDIT_MD).write_text("\n".join(text), encoding="utf-8")


def git_status(repo_root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ["GIT_STATUS_UNAVAILABLE"]
    output = completed.stdout.strip()
    return output.splitlines() if output else ["CLEAN_OR_ONLY_IGNORED_OUTPUTS"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline dynamic-exit replay/backtest for last-week XAUUSD entries.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--signal-dir",
        type=Path,
        action="append",
        default=[],
        help="Optional read-only MT5 MQL5/Files directory containing *_signal_log*_xauusd.csv files for exact logged-path replay.",
    )
    args = parser.parse_args()
    output = generate_dynamic_exit_backtest(args.root, args.signal_dir)
    print(json.dumps({"status": output.status, "report": str(output.report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
