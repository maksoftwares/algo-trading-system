from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


A1_ORDER_LOG = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/"
    "D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files/a1_920101_evening_order_log.csv"
)
A2_ORDER_LOG = Path("C:/MT5PortableTier1BestEA/MQL5/Files/a2_920101_evening_order_log.csv")
DEFAULT_PATH_LOG_DIR = Path("C:/MT5PortablePositionPathObserver/MQL5/Files")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "XAU_920101_PROTECTION_REPLAY_2026_06_30.json"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "XAU_920101_PROTECTION_REPLAY_2026_06_30.csv"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "XAU_920101_PROTECTION_REPLAY_2026_06_30.md"

SYMBOL = "XAUUSD"
MAGIC = "920101"
VARIANTS = (
    "CHASE_GUARD_030R",
    "CHASE_GUARD_050R",
    "BE_AFTER_075R",
    "BE_AFTER_080R",
    "PARTIAL_075R_BE",
    "GIVEBACK_075_TO_020R",
    "LOCK_080_TO_030R",
)

TRADE_COLUMNS = [
    "lane",
    "account_login",
    "position_ticket",
    "entry_time_broker",
    "entry_time_local",
    "run_id",
    "direction",
    "signal_entry_price",
    "fill_price",
    "sl",
    "tp",
    "risk_points",
    "planned_chase_points",
    "planned_chase_r",
    "estimated_cost_r",
    "path_rows",
    "path_closed",
    "path_first_time_broker",
    "path_last_time_broker",
    "max_unrealized_r",
    "min_unrealized_r",
    "max_unrealized_aed",
    "min_unrealized_aed",
    "control_r",
    "control_aed",
    "control_status",
    "best_variant",
    "best_delta_aed",
]

for variant in VARIANTS:
    TRADE_COLUMNS.extend([f"{variant}_r", f"{variant}_aed", f"{variant}_delta_aed", f"{variant}_status", f"{variant}_exit_time"])


@dataclass(frozen=True)
class OrderTrade:
    lane: str
    account_login: str
    ticket: str
    entry_time_broker: str
    entry_time_local: str
    run_id: str
    direction: str
    signal_entry: float
    fill_price: float
    sl: float
    tp: float
    estimated_cost_r: float

    @property
    def risk_points(self) -> float:
        if math.isnan(self.fill_price) or math.isnan(self.sl):
            return math.nan
        return abs(self.fill_price - self.sl) * 100.0

    @property
    def risk_price(self) -> float:
        if math.isnan(self.fill_price) or math.isnan(self.sl):
            return math.nan
        return abs(self.fill_price - self.sl)

    @property
    def is_long(self) -> bool:
        return self.direction.upper() in {"BUY", "LONG"}


@dataclass(frozen=True)
class PathPoint:
    ts_broker: str
    row_type: str
    unrealized_r: float
    unrealized_aed: float


@dataclass(frozen=True)
class VariantResult:
    final_r: float
    status: str
    exit_time: str = ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay offline protection variants for A1/A2 XAU 920101 trades.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--path-log-dir", type=Path, default=DEFAULT_PATH_LOG_DIR)
    parser.add_argument("--a1-order-log", type=Path, default=A1_ORDER_LOG)
    parser.add_argument("--a2-order-log", type=Path, default=A2_ORDER_LOG)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args(argv)


def run_replay(
    phase1_root: Path,
    path_log_dir: Path = DEFAULT_PATH_LOG_DIR,
    order_logs: list[tuple[str, Path]] | None = None,
    output_json: Path | None = None,
    output_csv: Path | None = None,
    output_md: Path | None = None,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_csv = (output_csv or phase1_root / DEFAULT_OUTPUT_CSV).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    for path in (output_json, output_csv, output_md):
        path.parent.mkdir(parents=True, exist_ok=True)

    order_logs = order_logs or [("A1", A1_ORDER_LOG), ("A2", A2_ORDER_LOG)]
    trades = load_order_trades(order_logs)
    paths = load_position_paths(path_log_dir, {trade.ticket for trade in trades})
    rows = [replay_trade(trade, paths.get(trade.ticket, [])) for trade in trades]

    covered_rows = [row for row in rows if int(row["path_rows"]) > 0]
    closed_rows = [row for row in covered_rows if row["path_closed"] == "true"]
    payload: dict[str, Any] = {
        "status": "PASS_REPORT_GENERATED",
        "created_at_utc": utc_now(),
        "scope": {
            "symbol": SYMBOL,
            "magic": MAGIC,
            "order_logs": [{"lane": lane, "path": str(path)} for lane, path in order_logs],
            "path_log_dir": str(path_log_dir),
            "order_send_rows": len(trades),
            "path_covered_rows": len(covered_rows),
            "closed_path_rows": len(closed_rows),
            "no_path_rows": len(trades) - len(covered_rows),
            "boundary": "Offline replay only. Reads order/path CSV logs and writes reports. No MT5 runtime, preset, chart, order, or EA behavior is changed.",
        },
        "coverage_by_lane": coverage_by_lane(rows),
        "variant_summary_closed_path": summarize_variants(closed_rows),
        "trade_rows": rows,
    }

    write_csv(output_csv, rows, TRADE_COLUMNS)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload, output_csv), encoding="utf-8")
    return payload


def load_order_trades(order_logs: list[tuple[str, Path]]) -> list[OrderTrade]:
    trades: list[OrderTrade] = []
    for lane, path in order_logs:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("action") != "ORDER_SEND_OK":
                    continue
                if row.get("symbol") != SYMBOL or row.get("magic") != MAGIC:
                    continue
                ticket = row.get("order_ticket", "").strip()
                if not ticket:
                    continue
                trades.append(
                    OrderTrade(
                        lane=lane,
                        account_login=row.get("account_login", ""),
                        ticket=ticket,
                        entry_time_broker=row.get("timestamp_broker", ""),
                        entry_time_local=row.get("timestamp_local", ""),
                        run_id=row.get("run_id", ""),
                        direction=normalize_direction(row.get("direction", "")),
                        signal_entry=fnum(row.get("signal_entry_price")),
                        fill_price=fnum(row.get("result_price")),
                        sl=fnum(row.get("sl")),
                        tp=fnum(row.get("tp")),
                        estimated_cost_r=fnum(row.get("estimated_cost_R"), 0.0),
                    )
                )
    trades.sort(key=lambda trade: (trade.entry_time_broker, trade.lane, trade.ticket))
    return trades


def load_position_paths(path_log_dir: Path, tickets: set[str]) -> dict[str, list[PathPoint]]:
    paths: dict[str, list[PathPoint]] = defaultdict(list)
    if not path_log_dir.exists():
        return paths
    for path in sorted(path_log_dir.glob("position_path_log_*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                ticket = row.get("position_ticket", "")
                if ticket not in tickets or row.get("symbol") != SYMBOL:
                    continue
                unrealized_r = fnum(row.get("unrealized_R"))
                unrealized_aed = fnum(row.get("unrealized_pnl_aed"))
                if math.isnan(unrealized_r) or math.isnan(unrealized_aed):
                    continue
                paths[ticket].append(
                    PathPoint(
                        ts_broker=row.get("ts_broker", ""),
                        row_type=row.get("row_type", ""),
                        unrealized_r=unrealized_r,
                        unrealized_aed=unrealized_aed,
                    )
                )
    for ticket in paths:
        paths[ticket].sort(key=lambda point: point.ts_broker)
    return paths


def replay_trade(trade: OrderTrade, path: list[PathPoint]) -> dict[str, Any]:
    path_closed = bool(path and path[-1].row_type == "CLOSE_DETECTED")
    control_r = path[-1].unrealized_r if path else math.nan
    control_aed = path[-1].unrealized_aed if path else math.nan
    aed_per_r = estimate_aed_per_r(path)
    max_r = max((point.unrealized_r for point in path), default=math.nan)
    min_r = min((point.unrealized_r for point in path), default=math.nan)
    max_aed = max((point.unrealized_aed for point in path), default=math.nan)
    min_aed = min((point.unrealized_aed for point in path), default=math.nan)
    chase_r = planned_chase_r(trade)

    row: dict[str, Any] = {
        "lane": trade.lane,
        "account_login": trade.account_login,
        "position_ticket": trade.ticket,
        "entry_time_broker": trade.entry_time_broker,
        "entry_time_local": trade.entry_time_local,
        "run_id": trade.run_id,
        "direction": trade.direction,
        "signal_entry_price": round_or_blank(trade.signal_entry, 5),
        "fill_price": round_or_blank(trade.fill_price, 5),
        "sl": round_or_blank(trade.sl, 5),
        "tp": round_or_blank(trade.tp, 5),
        "risk_points": round_or_blank(trade.risk_points, 2),
        "planned_chase_points": round_or_blank(planned_chase_points(trade) * 100.0, 2),
        "planned_chase_r": round_or_blank(chase_r, 6),
        "estimated_cost_r": round_or_blank(trade.estimated_cost_r, 6),
        "path_rows": len(path),
        "path_closed": "true" if path_closed else "false",
        "path_first_time_broker": path[0].ts_broker if path else "",
        "path_last_time_broker": path[-1].ts_broker if path else "",
        "max_unrealized_r": round_or_blank(max_r, 6),
        "min_unrealized_r": round_or_blank(min_r, 6),
        "max_unrealized_aed": round_or_blank(max_aed, 2),
        "min_unrealized_aed": round_or_blank(min_aed, 2),
        "control_r": round_or_blank(control_r, 6),
        "control_aed": round_or_blank(control_aed, 2),
        "control_status": "CLOSED_PATH" if path_closed else ("PATH_OPEN_OR_PARTIAL" if path else "NO_PATH"),
    }

    variant_results = {
        "CHASE_GUARD_030R": replay_chase_guard(chase_r, 0.30, control_r),
        "CHASE_GUARD_050R": replay_chase_guard(chase_r, 0.50, control_r),
        "BE_AFTER_075R": replay_break_even(path, control_r, 0.75),
        "BE_AFTER_080R": replay_break_even(path, control_r, 0.80),
        "PARTIAL_075R_BE": replay_partial_be(path, control_r, 0.75),
        "GIVEBACK_075_TO_020R": replay_giveback(path, control_r, 0.75, 0.20),
        "LOCK_080_TO_030R": replay_giveback(path, control_r, 0.80, 0.30),
    }

    best_variant = ""
    best_delta = -math.inf
    for variant, result in variant_results.items():
        replay_aed = result.final_r * aed_per_r if not math.isnan(result.final_r) and not math.isnan(aed_per_r) else math.nan
        delta = replay_aed - control_aed if not math.isnan(replay_aed) and not math.isnan(control_aed) else math.nan
        row[f"{variant}_r"] = round_or_blank(result.final_r, 6)
        row[f"{variant}_aed"] = round_or_blank(replay_aed, 2)
        row[f"{variant}_delta_aed"] = round_or_blank(delta, 2)
        row[f"{variant}_status"] = result.status
        row[f"{variant}_exit_time"] = result.exit_time
        if not math.isnan(delta) and delta > best_delta:
            best_delta = delta
            best_variant = variant

    row["best_variant"] = best_variant
    row["best_delta_aed"] = round_or_blank(best_delta, 2)
    return row


def replay_chase_guard(chase_r: float, threshold: float, control_r: float) -> VariantResult:
    if math.isnan(control_r):
        return VariantResult(math.nan, "NO_PATH")
    if not math.isnan(chase_r) and chase_r > threshold:
        return VariantResult(0.0, f"SKIPPED_CHASE_GT_{threshold:.2f}R")
    return VariantResult(control_r, "UNCHANGED")


def replay_break_even(path: list[PathPoint], control_r: float, trigger_r: float) -> VariantResult:
    if not path or math.isnan(control_r):
        return VariantResult(math.nan, "NO_PATH")
    armed = False
    arm_time = ""
    for point in path:
        if not armed and point.unrealized_r >= trigger_r:
            armed = True
            arm_time = point.ts_broker
            continue
        if armed and point.unrealized_r <= 0.0:
            return VariantResult(0.0, f"BE_EXIT_AFTER_{trigger_r:.2f}R_ARMED_AT_{arm_time}", point.ts_broker)
    return VariantResult(control_r, "UNCHANGED_NO_BE_EXIT")


def replay_partial_be(path: list[PathPoint], control_r: float, trigger_r: float) -> VariantResult:
    if not path or math.isnan(control_r):
        return VariantResult(math.nan, "NO_PATH")
    locked_partial_r = 0.5 * trigger_r
    armed = False
    arm_time = ""
    for point in path:
        if not armed and point.unrealized_r >= trigger_r:
            armed = True
            arm_time = point.ts_broker
            continue
        if armed and point.unrealized_r <= 0.0:
            return VariantResult(locked_partial_r, f"PARTIAL_LOCK_RUNNER_BE_ARMED_AT_{arm_time}", point.ts_broker)
    if armed:
        return VariantResult(locked_partial_r + 0.5 * control_r, "PARTIAL_LOCK_RUNNER_ACTUAL_EXIT")
    return VariantResult(control_r, "UNCHANGED_NO_PARTIAL_ARM")


def replay_giveback(path: list[PathPoint], control_r: float, trigger_r: float, floor_r: float) -> VariantResult:
    if not path or math.isnan(control_r):
        return VariantResult(math.nan, "NO_PATH")
    armed = False
    arm_time = ""
    for point in path:
        if not armed and point.unrealized_r >= trigger_r:
            armed = True
            arm_time = point.ts_broker
            continue
        if armed and point.unrealized_r <= floor_r:
            return VariantResult(floor_r, f"LOCK_EXIT_{floor_r:.2f}R_AFTER_{trigger_r:.2f}R_ARMED_AT_{arm_time}", point.ts_broker)
    return VariantResult(control_r, "UNCHANGED_NO_LOCK_EXIT")


def summarize_variants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = [summarize_control(rows)]
    for variant in VARIANTS:
        summary.append(summarize_variant(rows, variant))
    return summary


def summarize_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [fnum(row.get("control_aed")) for row in rows if not math.isnan(fnum(row.get("control_aed")))]
    return {
        "variant": "CONTROL",
        "rows": len(values),
        "net_aed": round(sum(values), 2),
        "delta_aed": 0.0,
        "win_rate_pct": pct(sum(1 for value in values if value > 0), len(values)),
        "profit_factor": profit_factor(values),
        "changed_rows": 0,
        "saved_losers": 0,
        "winner_drag_rows": 0,
    }


def summarize_variant(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    control_values: list[float] = []
    replay_values: list[float] = []
    changed = 0
    saved_losers = 0
    winner_drag = 0
    skipped = 0
    for row in rows:
        control = fnum(row.get("control_aed"))
        replay = fnum(row.get(f"{variant}_aed"))
        if math.isnan(control) or math.isnan(replay):
            continue
        control_values.append(control)
        replay_values.append(replay)
        delta = replay - control
        if abs(delta) > 0.005:
            changed += 1
        if control < 0 and replay >= 0 and delta > 0:
            saved_losers += 1
        if control > 0 and replay < control:
            winner_drag += 1
        if str(row.get(f"{variant}_status", "")).startswith("SKIPPED_"):
            skipped += 1
    return {
        "variant": variant,
        "rows": len(replay_values),
        "net_aed": round(sum(replay_values), 2),
        "delta_aed": round(sum(replay_values) - sum(control_values), 2),
        "win_rate_pct": pct(sum(1 for value in replay_values if value > 0), len(replay_values)),
        "profit_factor": profit_factor(replay_values),
        "changed_rows": changed,
        "saved_losers": saved_losers,
        "winner_drag_rows": winner_drag,
        "skipped_rows": skipped,
    }


def coverage_by_lane(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("lane", ""))].append(row)
    output: list[dict[str, Any]] = []
    for lane in sorted(grouped):
        lane_rows = grouped[lane]
        output.append(
            {
                "lane": lane,
                "order_send_rows": len(lane_rows),
                "path_covered_rows": sum(1 for row in lane_rows if int(row.get("path_rows", 0)) > 0),
                "closed_path_rows": sum(1 for row in lane_rows if row.get("path_closed") == "true"),
                "no_path_rows": sum(1 for row in lane_rows if int(row.get("path_rows", 0)) == 0),
            }
        )
    return output


def planned_chase_points(trade: OrderTrade) -> float:
    if math.isnan(trade.signal_entry) or math.isnan(trade.fill_price):
        return math.nan
    if trade.is_long:
        return max(0.0, trade.fill_price - trade.signal_entry)
    return max(0.0, trade.signal_entry - trade.fill_price)


def planned_chase_r(trade: OrderTrade) -> float:
    chase = planned_chase_points(trade)
    risk = trade.risk_price
    if math.isnan(chase) or math.isnan(risk) or risk <= 0.0:
        return math.nan
    return chase / risk


def estimate_aed_per_r(path: list[PathPoint]) -> float:
    ratios = [
        abs(point.unrealized_aed / point.unrealized_r)
        for point in path
        if not math.isnan(point.unrealized_aed) and not math.isnan(point.unrealized_r) and abs(point.unrealized_r) > 0.05
    ]
    if not ratios:
        return math.nan
    ratios.sort()
    mid = len(ratios) // 2
    if len(ratios) % 2:
        return ratios[mid]
    return (ratios[mid - 1] + ratios[mid]) / 2.0


def render_markdown(payload: dict[str, Any], output_csv: Path) -> str:
    scope = payload["scope"]
    summary = payload["variant_summary_closed_path"]
    scored_rows = [row for row in payload["trade_rows"] if row.get("path_closed") == "true"]
    latest = max(scored_rows, key=lambda row: str(row.get("entry_time_broker", "")), default=None)
    variant_rows = [row for row in summary if row["variant"] != "CONTROL"]
    best_overall = max(variant_rows, key=lambda row: fnum(row.get("delta_aed"), -math.inf), default={})
    management_rows = [row for row in variant_rows if not str(row["variant"]).startswith("CHASE_GUARD")]
    best_management = max(management_rows, key=lambda row: fnum(row.get("delta_aed"), -math.inf), default={})
    be_row = next((row for row in variant_rows if row["variant"] == "BE_AFTER_080R"), {})
    partial_row = next((row for row in variant_rows if row["variant"] == "PARTIAL_075R_BE"), {})
    lock_row = next((row for row in variant_rows if row["variant"] == "LOCK_080_TO_030R"), {})
    top_delta_rows = sorted(
        scored_rows,
        key=lambda row: fnum(row.get("best_delta_aed"), -math.inf),
        reverse=True,
    )[:5]
    lines = [
        "# XAU 920101 Offline Protection Replay - 2026-06-30",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline replay only. The script reads order logs and the 10-second position-path observer logs, then writes this report. It does not open MT5, change charts, edit presets, compile EAs, place orders, or modify runtime state.",
        "",
        "## Input Coverage",
        "",
        f"- Symbol / magic: `{scope['symbol']}` / `{scope['magic']}`",
        f"- Order-send rows: `{scope['order_send_rows']}`",
        f"- Path-covered rows: `{scope['path_covered_rows']}`",
        f"- Closed path rows scored: `{scope['closed_path_rows']}`",
        f"- Rows without path: `{scope['no_path_rows']}`",
        f"- Position path dir: `{scope['path_log_dir']}`",
        "",
        "| Lane | Orders | Path covered | Closed/scored | No path |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["coverage_by_lane"]:
        lines.append(
            f"| {row['lane']} | {row['order_send_rows']} | {row['path_covered_rows']} | {row['closed_path_rows']} | {row['no_path_rows']} |"
        )
    lines.extend(
        [
            "",
            "Important limitation: the current position-path observer has exact path coverage for A1 only in this sample. A2 rows are retained in the CSV as `NO_PATH`, but they are not scored until a path observer covers A2.",
            "",
            "## Replay Variants",
            "",
            "| Variant | Rows | Net AED | Delta AED | Win rate | PF | Changed | Saved losers | Winner drag | Skipped |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary:
        lines.append(
            f"| {row['variant']} | {row['rows']} | {row['net_aed']:.2f} | {row['delta_aed']:.2f} | "
            f"{row['win_rate_pct']:.2f}% | {fmt_float(row['profit_factor'])} | {row['changed_rows']} | "
            f"{row['saved_losers']} | {row['winner_drag_rows']} | {row.get('skipped_rows', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Actionable Read",
            "",
            f"- Best sample-level improvement: `{best_overall.get('variant', 'n/a')}`, which changed the closed A1 path-covered book by `{best_overall.get('delta_aed', 0.0):+.2f} AED` and skipped `{best_overall.get('skipped_rows', 0)}` trades.",
            f"- Best pure management idea: `{best_management.get('variant', 'n/a')}`, which changed the sample by `{best_management.get('delta_aed', 0.0):+.2f} AED` without skipping entries.",
            f"- Plain break-even and partial-BE both helped the latest loss, but across the scored sample they changed PnL by `{be_row.get('delta_aed', 0.0):+.2f} AED` and `{partial_row.get('delta_aed', 0.0):+.2f} AED` because they also dragged winners.",
            f"- `LOCK_080_TO_030R` changed the full sample by `{lock_row.get('delta_aed', 0.0):+.2f} AED`; do not prioritize it unless a larger sample contradicts this.",
            "- This is not promotion evidence yet: the scored sample is only 11 closed A1 rows and A2 path coverage is still missing.",
            "",
        ]
    )
    if latest:
        lines.extend(
            [
                "## Latest Scored Trade",
                "",
                "| Field | Value |",
                "| --- | ---: |",
                f"| Ticket | `{latest['position_ticket']}` |",
                f"| Entry broker / local | `{latest['entry_time_broker']}` / `{latest['entry_time_local']}` |",
                f"| Direction | `{latest['direction']}` |",
                f"| Planned chase | `{latest['planned_chase_r']}R` |",
                f"| Max favorable | `{latest['max_unrealized_r']}R` / `{latest['max_unrealized_aed']} AED` |",
                f"| Actual result | `{latest['control_r']}R` / `{latest['control_aed']} AED` |",
                f"| Best replayed variant | `{latest['best_variant']}` / delta `{latest['best_delta_aed']} AED` |",
                f"| Chase 0.50R delta | `{latest['CHASE_GUARD_050R_delta_aed']} AED` |",
                f"| BE after 0.80R delta | `{latest['BE_AFTER_080R_delta_aed']} AED` |",
                f"| Partial 0.75R + BE delta | `{latest['PARTIAL_075R_BE_delta_aed']} AED` |",
                f"| Giveback 0.75->0.20R delta | `{latest['GIVEBACK_075_TO_020R_delta_aed']} AED` |",
                "",
            ]
        )
    lines.extend(
        [
            "## Top Saved/Harmed Closed Path Rows",
            "",
            "| Entry | Ticket | Side | Control AED | Max R | Chase R | Best variant | Best delta AED |",
            "| --- | ---: | --- | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for row in top_delta_rows:
        lines.append(
            f"| {row['entry_time_broker']} | {row['position_ticket']} | {row['direction']} | "
            f"{row['control_aed']} | {row['max_unrealized_r']} | {row['planned_chase_r']} | "
            f"{row['best_variant']} | {row['best_delta_aed']} |"
        )
    lines.extend(
        [
            "",
            "## Variant Definitions",
            "",
            "- `CHASE_GUARD_030R`: skip if actual fill is more than `0.30R` beyond planned signal entry.",
            "- `CHASE_GUARD_050R`: skip if actual fill is more than `0.50R` beyond planned signal entry.",
            "- `BE_AFTER_075R`: move stop to break-even after `+0.75R`; close at `0R` if path returns to break-even.",
            "- `BE_AFTER_080R`: same as above, but arm at `+0.80R`.",
            "- `PARTIAL_075R_BE`: take half off at `+0.75R`, move runner to break-even.",
            "- `GIVEBACK_075_TO_020R`: after `+0.75R`, exit if open profit falls back to `+0.20R`.",
            "- `LOCK_080_TO_030R`: after `+0.80R`, exit if open profit falls back to `+0.30R`.",
            "",
            "## Trade-Level Detail",
            "",
            f"CSV: `{output_csv}`",
            "",
            "## Interpretation Rule",
            "",
            "Treat this as evidence only for rows with `path_closed=true`. A rule should not be promoted unless it improves closed/path-covered PnL, avoids full-stop losses, does not heavily drag winners, and later survives a larger forward sample with both A1 and A2 covered.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_direction(value: str) -> str:
    value = (value or "").upper()
    if value == "LONG":
        return "BUY"
    if value == "SHORT":
        return "SELL"
    return value


def fnum(value: object, default: float = math.nan) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def pct(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 2) if denominator else 0.0


def profit_factor(values: list[float]) -> float:
    gross_win = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss <= 0:
        return math.inf if gross_win > 0 else 0.0
    return round(gross_win / gross_loss, 6)


def fmt_float(value: float) -> str:
    if math.isinf(value):
        return "inf"
    if math.isnan(value):
        return "n/a"
    return f"{value:.4f}"


def round_or_blank(value: float, digits: int) -> str | float:
    if value is None or math.isnan(float(value)) or math.isinf(float(value)):
        return ""
    return round(float(value), digits)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = run_replay(
        phase1_root=args.phase1_root,
        path_log_dir=args.path_log_dir,
        order_logs=[("A1", args.a1_order_log), ("A2", args.a2_order_log)],
        output_json=args.output_json,
        output_csv=args.output_csv,
        output_md=args.output_md,
    )
    print(f"XAU 920101 protection replay: {payload['status']}")
    print(json.dumps(payload["scope"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
