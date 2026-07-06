from __future__ import annotations

import csv
import itertools
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
MT5_DIR = (
    REPORTS
    / "mt5_backtests"
    / "a1_momentum_variants_four_year_rr2_long_only_2022_07_2026_06_momentum_usd_20260701"
)
PREFIX = "A1XauM5Momentum_FOUR_YEAR_RR2_LONG_ONLY_2022_07_2026_06_MOMENTUM_USD_XAUUSD_M5_rr_2p0_long_only_h1_h4_atr15_no0910"
TRADES_CSV = MT5_DIR / f"{PREFIX}_trades.csv"
ORDERS_CSV = MT5_DIR / f"{PREFIX}_orders.csv"
SIGNALS_CSV = MT5_DIR / f"{PREFIX}_signals.csv"

OUT_MD = REPORTS / "A1_XAU_M5_RR2_LONG_ONLY_CAUSAL_FILTER_DIAGNOSTIC_2026_07_05.md"
OUT_JSON = OUT_MD.with_suffix(".json")
OUT_CSV = OUT_MD.with_suffix(".csv")

FROM_DATE = date(2022, 7, 1)
TO_DATE = date(2026, 6, 30)
SPLIT_DATE = date(2024, 7, 1)
LAST12_START = date(2025, 7, 1)

QUANTILES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90)
NUMERIC_FEATURES = (
    "entry_hour",
    "spread_points",
    "estimated_cost_r",
    "stop_points",
    "atr",
    "body_fraction",
    "close_location",
    "three_bar_move_atr",
    "break_distance_atr",
    "signal_range",
    "recent_range",
    "recent_range_atr",
    "upper_wick_body_ratio",
    "lower_wick_body_ratio",
)
MIN_REPORT_TRADES = 100
MIN_CREDIBLE_TRADES = 200


@dataclass(frozen=True)
class Gate:
    feature: str
    op: str
    value: float | str
    label: str


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if value in (None, ""):
            return default
        return float(str(value).replace(" ", ""))
    except (TypeError, ValueError):
        return default


def parse_money(value: str) -> float:
    return float((value or "0").replace(" ", ""))


def parse_mt5_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def finite(*values: float) -> bool:
    return all(not math.isnan(value) for value in values)


def market_days(start: date = FROM_DATE, end: date = TO_DATE) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    return days


def max_closed_drawdown(pnl: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in pnl:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def load_orders() -> dict[str, dict[str, str]]:
    orders: dict[str, dict[str, str]] = {}
    with ORDERS_CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("action") != "ORDER_SEND_OK":
                continue
            deal = row.get("deal_ticket", "")
            if deal:
                orders[deal] = row
    return orders


def decision_features(row: dict[str, str]) -> dict[str, float]:
    open_ = as_float(row.get("signal_open"))
    high = as_float(row.get("signal_high"))
    low = as_float(row.get("signal_low"))
    close = as_float(row.get("signal_close"))
    recent_high = as_float(row.get("recent_high"))
    recent_low = as_float(row.get("recent_low"))
    atr = as_float(row.get("atr"))
    body = abs(close - open_) if finite(close, open_) else math.nan
    signal_range = high - low if finite(high, low) else math.nan
    recent_range = recent_high - recent_low if finite(recent_high, recent_low) else math.nan
    upper_wick = high - max(open_, close) if finite(high, open_, close) else math.nan
    lower_wick = min(open_, close) - low if finite(low, open_, close) else math.nan
    return {
        "spread_points": as_float(row.get("spread_points")),
        "estimated_cost_r_signal": as_float(row.get("estimated_cost_r")),
        "atr": atr,
        "body_fraction": as_float(row.get("body_fraction")),
        "close_location": as_float(row.get("close_location")),
        "three_bar_move_atr": as_float(row.get("three_bar_move_atr")),
        "break_distance_atr": as_float(row.get("break_distance_atr")),
        "signal_range": signal_range,
        "recent_range": recent_range,
        "recent_range_atr": recent_range / atr if finite(recent_range, atr) and atr > 0 else math.nan,
        "upper_wick_body_ratio": upper_wick / body if finite(upper_wick, body) and body > 0 else math.nan,
        "lower_wick_body_ratio": lower_wick / body if finite(lower_wick, body) and body > 0 else math.nan,
    }


def load_signals() -> dict[tuple[str, str], dict[str, float]]:
    signals: dict[tuple[str, str], dict[str, float]] = {}
    with SIGNALS_CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("stage") != "WOULD_SIGNAL":
                continue
            if row.get("direction") != "LONG":
                continue
            key = (row.get("timestamp_broker", ""), row.get("direction", ""))
            signals[key] = decision_features(row)
    return signals


def session_for_hour(hour: int) -> str:
    if hour < 6:
        return "overnight"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def load_trades() -> list[dict[str, Any]]:
    orders = load_orders()
    signals = load_signals()
    rows: list[dict[str, Any]] = []
    missing_orders = 0
    missing_signals = 0
    with TRADES_CSV.open(newline="", encoding="utf-8-sig") as handle:
        for trade in csv.DictReader(handle):
            entry_dt = parse_mt5_datetime(trade["entry_time"])
            row: dict[str, Any] = dict(trade)
            row["entry_dt"] = entry_dt
            row["entry_date_obj"] = entry_dt.date()
            row["entry_hour"] = float(entry_dt.hour)
            row["entry_weekday"] = entry_dt.weekday()
            row["entry_weekday_name"] = entry_dt.strftime("%A")
            row["entry_session_norm"] = session_for_hour(entry_dt.hour)
            row["profit_aed_float"] = parse_money(trade["profit_aed"])

            order = orders.get(trade.get("entry_deal", ""))
            if order:
                row["stop_points"] = as_float(order.get("stop_points"))
                row["estimated_cost_r"] = as_float(order.get("estimated_cost_r"))
                row["order_spread_points"] = as_float(order.get("spread_points"))
            else:
                missing_orders += 1
                row["stop_points"] = math.nan
                row["estimated_cost_r"] = math.nan
                row["order_spread_points"] = math.nan

            signal = signals.get((trade["entry_time"], trade["direction"]))
            if signal:
                row.update(signal)
            else:
                missing_signals += 1

            rows.append(row)

    rows.sort(key=lambda item: item["entry_dt"])
    if missing_orders or missing_signals:
        print(f"join_warnings missing_orders={missing_orders} missing_signals={missing_signals}")
    return rows


def metrics(rows: list[dict[str, Any]], *, start: date = FROM_DATE, end: date = TO_DATE) -> dict[str, Any]:
    pnl = [float(row["profit_aed_float"]) for row in rows]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    weekdays = market_days(start, end)
    active_dates = {row["entry_date_obj"] for row in rows}
    sorted_pnl = sorted(pnl, reverse=True)
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(rows) * 100.0) if rows else 0.0, 2),
        "net_aed": round(sum(pnl), 2),
        "gross_profit_aed": round(gross_profit, 2),
        "gross_loss_aed": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else 0.0,
        "avg_win_aed": round(gross_profit / len(wins), 2) if wins else 0.0,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else 0.0,
        "win_loss_ratio": round((gross_profit / len(wins)) / (gross_loss / len(losses)), 4) if wins and losses else 0.0,
        "active_days": len(active_dates),
        "market_weekdays": len(weekdays),
        "active_day_pct": round((len(active_dates) / len(weekdays) * 100.0) if weekdays else 0.0, 2),
        "max_closed_dd_aed": round(max_closed_drawdown(pnl), 2),
        "top10_removed_net_aed": round(sum(sorted_pnl[10:]) if len(sorted_pnl) > 10 else sum(sorted_pnl), 2),
        "top25_removed_net_aed": round(sum(sorted_pnl[25:]) if len(sorted_pnl) > 25 else sum(sorted_pnl), 2),
    }


def split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    older = [row for row in rows if row["entry_date_obj"] < SPLIT_DATE]
    newer = [row for row in rows if row["entry_date_obj"] >= SPLIT_DATE]
    last12 = [row for row in rows if row["entry_date_obj"] >= LAST12_START]
    older_m = metrics(older, start=FROM_DATE, end=date(2024, 6, 30))
    newer_m = metrics(newer, start=SPLIT_DATE, end=TO_DATE)
    last12_m = metrics(last12, start=LAST12_START, end=TO_DATE)
    return {
        "older_trades": older_m["trades"],
        "older_wr": older_m["win_rate_pct"],
        "older_wl": older_m["win_loss_ratio"],
        "older_pf": older_m["profit_factor"],
        "older_net_aed": older_m["net_aed"],
        "newer_trades": newer_m["trades"],
        "newer_wr": newer_m["win_rate_pct"],
        "newer_wl": newer_m["win_loss_ratio"],
        "newer_pf": newer_m["profit_factor"],
        "newer_net_aed": newer_m["net_aed"],
        "last12_trades": last12_m["trades"],
        "last12_wr": last12_m["win_rate_pct"],
        "last12_wl": last12_m["win_loss_ratio"],
        "last12_pf": last12_m["profit_factor"],
        "last12_net_aed": last12_m["net_aed"],
    }


def quantile_thresholds(values: list[float]) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 50:
        return []
    thresholds: list[float] = []
    for quantile in QUANTILES:
        index = round((len(clean) - 1) * quantile)
        thresholds.append(round(clean[index], 6))
    return sorted(set(thresholds))


def gate_keeps(row: dict[str, Any], gate: Gate) -> bool:
    if gate.op == "session":
        return row.get("entry_session_norm") == gate.value
    if gate.op == "weekday":
        return row.get("entry_weekday_name") == gate.value
    if gate.op == "block_hour":
        return int(row.get("entry_hour", -1)) not in gate.value  # type: ignore[arg-type]
    value = as_float(row.get(gate.feature))
    if math.isnan(value):
        return False
    if gate.op == ">=":
        return value >= float(gate.value)
    if gate.op == "<=":
        return value <= float(gate.value)
    raise ValueError(f"unknown gate op: {gate.op}")


def apply_gates(rows: list[dict[str, Any]], gates: tuple[Gate, ...]) -> tuple[list[dict[str, Any]], int]:
    kept = [row for row in rows if all(gate_keeps(row, gate) for gate in gates)]
    return kept, len(rows) - len(kept)


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < MIN_REPORT_TRADES:
        return "FAIL_SAMPLE_TOO_SMALL"
    if row["trades"] < MIN_CREDIBLE_TRADES:
        return "DIAGNOSTIC_TINY_CLUE_ONLY"
    if row["win_rate_pct"] >= 50.0 and row["win_loss_ratio"] >= 2.0:
        if row["active_day_pct"] >= 90.0:
            return "DIAGNOSTIC_FULL_GOAL_HIT_REQUIRES_MT5_RERUN"
        return "DIAGNOSTIC_WR_WL_HIT_ACTIVITY_FAIL_REQUIRES_MT5_RERUN"
    if row["win_rate_pct"] >= 48.0 and row["win_loss_ratio"] >= 1.9:
        return "DIAGNOSTIC_NEAR_WR_WL_REQUIRES_MT5_RERUN"
    return "FAIL_WR_WL"


def score(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["decision"] == "DIAGNOSTIC_FULL_GOAL_HIT_REQUIRES_MT5_RERUN",
        row["decision"] == "DIAGNOSTIC_WR_WL_HIT_ACTIVITY_FAIL_REQUIRES_MT5_RERUN",
        row["decision"] == "DIAGNOSTIC_NEAR_WR_WL_REQUIRES_MT5_RERUN",
        row["win_rate_pct"] >= 50.0,
        row["win_loss_ratio"] >= 2.0,
        row["win_rate_pct"],
        row["win_loss_ratio"],
        row["active_day_pct"],
        row["trades"],
        row["profit_factor"],
        row["net_aed"],
    )


def summarize(name: str, gate_type: str, rows: list[dict[str, Any]], gates: tuple[Gate, ...], blocked: int) -> dict[str, Any]:
    result = {
        "name": name,
        "gate_type": gate_type,
        "gates": " AND ".join(gate.label for gate in gates) if gates else "baseline",
        "blocked_trades": blocked,
        "blocked_pct": round((blocked / (blocked + len(rows)) * 100.0) if rows or blocked else 0.0, 2),
        **metrics(rows),
    }
    result.update(split_metrics(rows))
    result["decision"] = decision(result)
    return result


def single_gates(rows: list[dict[str, Any]]) -> list[Gate]:
    gates: list[Gate] = []
    for feature in NUMERIC_FEATURES:
        thresholds = quantile_thresholds([as_float(row.get(feature)) for row in rows])
        for threshold in thresholds:
            gates.append(Gate(feature, ">=", threshold, f"keep_{feature}_>=_{threshold:g}"))
            gates.append(Gate(feature, "<=", threshold, f"keep_{feature}_<=_{threshold:g}"))

    for session in ("overnight", "morning", "afternoon", "evening"):
        gates.append(Gate("entry_session_norm", "session", session, f"keep_session_{session}"))

    for weekday in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
        gates.append(Gate("entry_weekday_name", "weekday", weekday, f"keep_weekday_{weekday}"))

    hours = sorted({int(row["entry_hour"]) for row in rows})
    for size in (1, 2, 3):
        for combo in itertools.combinations(hours, size):
            gates.append(Gate("entry_hour", "block_hour", tuple(combo), "block_hours_" + "_".join(str(hour) for hour in combo)))
    return gates


def analyze() -> dict[str, Any]:
    rows = load_trades()
    baseline = summarize("baseline", "baseline", rows, tuple(), 0)

    evaluated: list[dict[str, Any]] = []
    gate_objects: dict[str, Gate] = {}
    for gate in single_gates(rows):
        kept, blocked = apply_gates(rows, (gate,))
        if len(kept) < MIN_REPORT_TRADES:
            continue
        evaluated.append(summarize(gate.label, "single", kept, (gate,), blocked))
        gate_objects[gate.label] = gate

    top_singles = [
        gate_objects[row["name"]]
        for row in sorted(evaluated, key=score, reverse=True)
        if row["trades"] >= MIN_CREDIBLE_TRADES
    ][:12]

    for first, second in itertools.combinations(top_singles, 2):
        if first.feature == second.feature:
            continue
        kept, blocked = apply_gates(rows, (first, second))
        if len(kept) < MIN_REPORT_TRADES:
            continue
        name = f"{first.label}__AND__{second.label}"
        evaluated.append(summarize(name, "two_gate_limited", kept, (first, second), blocked))

    ranked = sorted(evaluated, key=score, reverse=True)
    hits = [row for row in ranked if "HIT" in row["decision"]]
    near = [row for row in ranked if row["decision"] == "DIAGNOSTIC_NEAR_WR_WL_REQUIRES_MT5_RERUN"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "DIAGNOSTIC_HIT_FOUND_REQUIRES_MT5_RERUN" if hits else "NO_DIAGNOSTIC_WR_WL_HIT",
        "scope": {
            "label": "A1 RR2 long-only causal filter diagnostic",
            "source": "exact MT5 Strategy Tester trade/order/signal CSVs; offline filtering only",
            "period": "2022-07-01 -> 2026-06-30",
            "no_live_runtime_change": True,
            "caveat": "Skipping a trade offline can change later MT5 sequencing, equity, open-position timing, and daily frequency. Any interesting row is only a clue until rerun as a frozen MT5 variant.",
        },
        "inputs": {
            "trades_csv": str(TRADES_CSV),
            "orders_csv": str(ORDERS_CSV),
            "signals_csv": str(SIGNALS_CSV),
        },
        "baseline": baseline,
        "top_rows": ranked[:60],
        "hits": hits[:25],
        "near": near[:25],
    }
    write_csv(OUT_CSV, ranked)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def table(rows: list[dict[str, Any]], limit: int = 12) -> list[str]:
    headers = [
        "Gate",
        "Trades",
        "WR%",
        "W/L",
        "Active%",
        "PF",
        "Net",
        "2022-24 WR/WL",
        "2024-26 WR/WL",
        "Last12 WR/WL",
        "Decision",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['gates']}`",
                    str(row["trades"]),
                    f"{row['win_rate_pct']:.2f}",
                    f"{row['win_loss_ratio']:.4f}",
                    f"{row['active_day_pct']:.2f}",
                    f"{row['profit_factor']:.4f}",
                    f"{row['net_aed']:.2f}",
                    f"{row['older_wr']:.2f}/{row['older_wl']:.2f}",
                    f"{row['newer_wr']:.2f}/{row['newer_wl']:.2f}",
                    f"{row['last12_wr']:.2f}/{row['last12_wl']:.2f}",
                    f"`{row['decision']}`",
                ]
            )
            + " |"
        )
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    rows = payload["top_rows"]
    hit_rows = payload["hits"]
    near_rows = payload["near"]
    lines = [
        "# A1 XAU M5 RR2 Long-Only Causal Filter Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: diagnostic-only offline filter screen over an already completed exact MT5 Strategy Tester ledger. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Caveat: offline filtering can change later Strategy Tester sequencing because skipped trades may alter open-position timing and equity path. Any interesting row must be frozen and rerun in exact MT5 before becoming evidence.",
        "",
        "## Inputs",
        "",
        f"- Trades: `{payload['inputs']['trades_csv']}`",
        f"- Orders: `{payload['inputs']['orders_csv']}`",
        f"- Signals: `{payload['inputs']['signals_csv']}`",
        "",
        "## Baseline",
        "",
        "| Trades | WR% | W/L | Active% | PF | Net AED | Max DD AED | Last12 WR/WL |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| {baseline['trades']} | {baseline['win_rate_pct']:.2f} | {baseline['win_loss_ratio']:.4f} | {baseline['active_day_pct']:.2f} | {baseline['profit_factor']:.4f} | {baseline['net_aed']:.2f} | {baseline['max_closed_dd_aed']:.2f} | {baseline['last12_wr']:.2f}/{baseline['last12_wl']:.2f} |",
        "",
        "## Diagnostic Hits",
        "",
    ]
    if hit_rows:
        lines.extend(table(hit_rows, 12))
    else:
        lines.append("No diagnostic row with at least 200 trades reached both WR `>=50%` and W/L `>=2.0`.")
    lines.extend(
        [
            "",
            "## Near Rows",
            "",
        ]
    )
    if near_rows:
        lines.extend(table(near_rows, 12))
    else:
        lines.append("No diagnostic row with at least 200 trades reached WR `>=48%` and W/L `>=1.9`.")
    lines.extend(
        [
            "",
            "## Top Frontier Rows",
            "",
            *table(rows, 20),
            "",
            "## Verdict",
            "",
        ]
    )
    if hit_rows:
        lines.append("Diagnostic clue found. It is not a headline result; preregister one frozen exact-MT5 rerun only if the split/read is not obviously unstable.")
    else:
        lines.append("No credible causal filter was found on this RR2 long-only ledger. Do not spend reviewer tokens; this branch needs a new high-hit-rate entry family rather than more threshold filtering.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = analyze()
    print(json.dumps({"status": payload["status"], "report": str(OUT_MD)}, indent=2))


if __name__ == "__main__":
    main()
