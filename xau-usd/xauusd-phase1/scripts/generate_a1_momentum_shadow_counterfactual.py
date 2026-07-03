from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_OUTPUT_MD = PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_M5_MOMENTUM_RR2_SHADOW_COUNTERFACTUAL_2026_07_02.md"
RUN_ID = "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702"
ACCOUNT_LOGIN = "1025742"
SYMBOL = "XAUUSD"
MAGIC = 932200
LANE_START = datetime(2026, 7, 2, 4, 46, 42)
POINT = 0.01
RISK_REWARD = 2.0


def generate_a1_momentum_shadow_counterfactual(
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    output_md: Path = DEFAULT_OUTPUT_MD,
) -> dict[str, Any]:
    terminal_exe = terminal_exe.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    output_md = output_md.resolve()
    output_json = output_md.with_suffix(".json")
    output_csv = output_md.with_suffix(".csv")
    output_md.parent.mkdir(parents=True, exist_ok=True)

    files_dir = terminal_data_dir / "MQL5" / "Files"
    signal_rows = read_tsv(files_dir / "a1_xau_m5_momentum_signal_log.csv")
    order_rows = read_tsv(files_dir / "a1_xau_m5_momentum_order_log.csv")
    forward_signals = filter_forward(signal_rows)
    forward_orders = filter_forward(order_rows)
    bars = query_m5_bars(terminal_exe, forward_signals)
    replay_rows = build_replay_rows(forward_signals, forward_orders, bars)
    summary = summarize(replay_rows, forward_orders)

    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "timestamp_broker",
            "category",
            "direction",
            "signal_reason",
            "guard_reason",
            "entry_reference",
            "stop_points",
            "replay_status",
            "replay_r",
            "exit_time",
            "bars_checked",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(replay_rows)

    payload = {
        "status": summary["status"],
        "run_id": RUN_ID,
        "account": ACCOUNT_LOGIN,
        "symbol": SYMBOL,
        "magic": MAGIC,
        "lane_start_broker": LANE_START.strftime("%Y-%m-%d %H:%M:%S"),
        "output_md": str(output_md),
        "output_csv": str(output_csv),
        "signal_rows": len(forward_signals),
        "order_rows": len(forward_orders),
        "summary": summary,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload, replay_rows), encoding="utf-8")
    return payload


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def parse_time(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def filter_forward(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        if row.get("run_id") != RUN_ID:
            continue
        if str(row.get("account")) != ACCOUNT_LOGIN:
            continue
        if str(row.get("magic")) != str(MAGIC):
            continue
        ts = parse_time(row.get("timestamp_broker", ""))
        if ts is None or ts < LANE_START:
            continue
        row = dict(row)
        row["_ts"] = ts.isoformat(sep=" ")
        out.append(row)
    return out


def query_m5_bars(terminal_exe: Path, signal_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    if not signal_rows:
        return []
    times = [parse_time(row["timestamp_broker"]) for row in signal_rows if parse_time(row["timestamp_broker"])]
    if not times:
        return []
    start = min(times) - timedelta(minutes=10)
    end = datetime.now() + timedelta(days=1)
    script = f"""
import json
from datetime import datetime
import MetaTrader5 as mt5
path = r'{terminal_exe}'
if not mt5.initialize(path=path):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    mt5.symbol_select('{SYMBOL}', True)
    rates = mt5.copy_rates_range('{SYMBOL}', mt5.TIMEFRAME_M5, datetime({start.year},{start.month},{start.day},{start.hour},{start.minute},{start.second}), datetime({end.year},{end.month},{end.day},{end.hour},{end.minute},{end.second}))
    rows = []
    if rates is not None:
        for rate in rates:
            item = {{}}
            for name in rates.dtype.names:
                value = rate[name].item() if hasattr(rate[name], 'item') else rate[name]
                item[name] = value
            rows.append(item)
    print(json.dumps({{'bars': rows, 'last_error': str(mt5.last_error())}}, default=str))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(venv_python()), "-c", script], text=True, capture_output=True, timeout=45)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 M5 bar query failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    bars = payload.get("bars", [])
    for bar in bars:
        bar["dt"] = datetime.fromtimestamp(int(bar["time"]))
    return bars


def venv_python() -> Path:
    return PHASE1_ROOT.parent / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"


def build_replay_rows(
    signal_rows: list[dict[str, str]],
    order_rows: list[dict[str, str]],
    bars: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    orders_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for order in order_rows:
        orders_by_key[(order.get("timestamp_broker", ""), order.get("direction", ""))].append(order)

    out = []
    seen_signal_keys: set[tuple[str, str, str, str]] = set()
    for signal in signal_rows:
        if signal.get("stage") != "WOULD_SIGNAL":
            continue
        direction = signal.get("direction", "")
        timestamp = signal.get("timestamp_broker", "")
        order = first_order(orders_by_key.get((timestamp, direction), []))
        entry_for_key = order.get("entry_reference", "") if order else signal.get("signal_close", "")
        stop_for_key = order.get("stop_points", "") if order else signal.get("atr", "")
        signal_key = (direction, signal.get("reason", ""), entry_for_key, stop_for_key)
        if signal_key in seen_signal_keys:
            out.append(
                {
                    "timestamp_broker": timestamp,
                    "category": "DUPLICATE_SIGNAL_REATTACH_EXCLUDED",
                    "direction": direction,
                    "signal_reason": signal.get("reason", ""),
                    "guard_reason": order.get("reason", "") if order else "",
                    "entry_reference": entry_for_key,
                    "stop_points": stop_for_key,
                    "replay_status": "EXCLUDED_DUPLICATE_SIGNAL",
                    "replay_r": "",
                    "exit_time": "",
                    "bars_checked": 0,
                }
            )
            continue
        seen_signal_keys.add(signal_key)
        category = classify_counterfactual(signal, order)
        entry = as_float(order.get("entry_reference") if order else signal.get("signal_close"))
        stop_points = as_float(order.get("stop_points") if order else "")
        if stop_points <= 0:
            atr = as_float(signal.get("atr"))
            stop_points = max(2.5 * atr / POINT, 350.0)
        replay = replay_signal(parse_time(timestamp), direction, entry, stop_points, bars)
        out.append(
            {
                "timestamp_broker": timestamp,
                "category": category,
                "direction": direction,
                "signal_reason": signal.get("reason", ""),
                "guard_reason": order.get("reason", "") if order else "",
                "entry_reference": f"{entry:.2f}",
                "stop_points": f"{stop_points:.2f}",
                "replay_status": replay["status"],
                "replay_r": replay["r"],
                "exit_time": replay["exit_time"],
                "bars_checked": replay["bars_checked"],
            }
        )
    return out


def first_order(rows: list[dict[str, str]]) -> dict[str, str] | None:
    if not rows:
        return None
    return rows[0]


def classify_counterfactual(signal: dict[str, str], order: dict[str, str] | None) -> str:
    if order is None:
        return "WOULD_SIGNAL_NO_ORDER_ROW"
    action = order.get("action", "")
    reason = order.get("reason", "")
    if action == "ORDER_SEND_OK":
        return "ACTUAL_LANE_ORDER"
    if reason == "direction_mode_block":
        return "BLOCKED_SHORT_BY_LONG_ONLY_RULE"
    if reason == "blocked_entry_hour":
        return "BLOCKED_BY_09_10_HOUR_RULE"
    return f"OTHER_GUARD_BLOCK:{reason or action or 'UNKNOWN'}"


def as_float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


def replay_signal(
    signal_time: datetime | None,
    direction: str,
    entry: float,
    stop_points: float,
    bars: list[dict[str, Any]],
) -> dict[str, Any]:
    if signal_time is None or entry <= 0 or stop_points <= 0:
        return {"status": "UNRESOLVED_BAD_INPUT", "r": "", "exit_time": "", "bars_checked": 0}
    risk = stop_points * POINT
    if direction == "LONG":
        sl = entry - risk
        tp = entry + RISK_REWARD * risk
    elif direction == "SHORT":
        sl = entry + risk
        tp = entry - RISK_REWARD * risk
    else:
        return {"status": "UNRESOLVED_BAD_DIRECTION", "r": "", "exit_time": "", "bars_checked": 0}
    checked = 0
    for bar in bars:
        bar_time = bar["dt"]
        if bar_time <= signal_time:
            continue
        checked += 1
        high = float(bar["high"])
        low = float(bar["low"])
        if direction == "LONG":
            sl_hit = low <= sl
            tp_hit = high >= tp
        else:
            sl_hit = high >= sl
            tp_hit = low <= tp
        if sl_hit and tp_hit:
            return {"status": "REPLAY_ADVERSE_FIRST_SL", "r": -1.0, "exit_time": bar_time.isoformat(sep=" "), "bars_checked": checked}
        if sl_hit:
            return {"status": "REPLAY_SL", "r": -1.0, "exit_time": bar_time.isoformat(sep=" "), "bars_checked": checked}
        if tp_hit:
            return {"status": "REPLAY_TP", "r": RISK_REWARD, "exit_time": bar_time.isoformat(sep=" "), "bars_checked": checked}
    return {"status": "UNRESOLVED_OPEN_OR_NO_HIT", "r": "", "exit_time": "", "bars_checked": checked}


def summarize(replay_rows: list[dict[str, Any]], order_rows: list[dict[str, str]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, Any]] = {}
    for row in replay_rows:
        category = row["category"]
        item = by_category.setdefault(category, {"signals": 0, "resolved": 0, "sum_r": 0.0, "wins": 0, "losses": 0})
        item["signals"] += 1
        if row["replay_r"] != "":
            r_value = float(row["replay_r"])
            item["resolved"] += 1
            item["sum_r"] += r_value
            if r_value > 0:
                item["wins"] += 1
            elif r_value < 0:
                item["losses"] += 1
    for item in by_category.values():
        item["sum_r"] = round(item["sum_r"], 2)
        item["win_rate"] = round(item["wins"] / item["resolved"] * 100, 2) if item["resolved"] else 0.0
    order_reasons = Counter(row.get("reason", "") for row in order_rows if row.get("action") == "GUARD_BLOCK")
    status = "PASS_COUNTERFACTUAL_READY" if replay_rows else "PENDING_NO_FORWARD_WOULD_SIGNALS"
    return {
        "status": status,
        "by_category": dict(sorted(by_category.items())),
        "guard_block_reasons": dict(sorted(order_reasons.items())),
    }


def render_markdown(payload: dict[str, Any], replay_rows: list[dict[str, Any]]) -> str:
    summary = payload["summary"]
    lines = [
        "# A1 XAU M5 Momentum RR2 Shadow Counterfactual - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Purpose: compare the active RR2 long-only lane against the signals it deliberately blocks, without changing MT5 runtime.",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Account: `{ACCOUNT_LOGIN}`",
        f"- Symbol/magic: `{SYMBOL}` / `{MAGIC}`",
        f"- Forward start broker time: `{payload['lane_start_broker']}`",
        f"- CSV: `{payload['output_csv']}`",
        "",
        "Replay note: this is a diagnostic M5 replay using order-log entry references and adverse-first handling if TP and SL touch in the same M5 bar. Broker-joined fills remain stronger evidence than replayed blocked signals.",
        "",
        "## Category Scoreboard",
        "",
        "| Category | Signals | Resolved | Wins | Losses | Win rate | Sum R |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    by_category = summary.get("by_category") or {}
    if by_category:
        for category, item in by_category.items():
            lines.append(
                f"| `{category}` | {item['signals']} | {item['resolved']} | {item['wins']} | {item['losses']} | {item['win_rate']:.2f}% | {item['sum_r']:.2f} |"
            )
    else:
        lines.append("| `NO_FORWARD_WOULD_SIGNALS` | 0 | 0 | 0 | 0 | 0.00% | 0.00 |")
    lines.extend(["", "## Guard Blocks", "", "| Reason | Count |", "|---|---:|"])
    reasons = summary.get("guard_block_reasons") or {}
    if reasons:
        for reason, count in reasons.items():
            lines.append(f"| `{reason or 'EMPTY'}` | {count} |")
    else:
        lines.append("| `NONE` | 0 |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Report only; no chart, preset, order, position, or EA input was changed.",
            "- Blocked shorts and blocked `09/10` server-hour signals can be revisited later only from this frozen shadow evidence.",
            "- The active runtime rule remains RR2 long-only with server hours `09,10` blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()
    result = generate_a1_momentum_shadow_counterfactual(args.terminal_exe, args.terminal_data_dir, args.output_md)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
