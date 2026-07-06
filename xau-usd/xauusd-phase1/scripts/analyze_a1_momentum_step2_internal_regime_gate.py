from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"

IN_KEPT = REPORTS / "A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_KEPT_SIGNALS_2026_07_05.csv"
OUT_MD = REPORTS / "A1_XAU_M5_MOMENTUM_STEP2_INTERNAL_REGIME_GATE_2026_07_05.md"
OUT_JSON = OUT_MD.with_suffix(".json")
OUT_CSV = OUT_MD.with_suffix(".csv")
ANALYSIS_TITLE = "A1 XAU M5 Momentum Step 2 Internal Regime Gate"
ANALYSIS_SCOPE = "offline causal gate screen over exact MT5 Strategy Tester Step 1 signal ledgers and MT5 WOULD_SIGNAL rows"

FROM_DATE = date(2022, 7, 1)
TO_DATE = date(2026, 6, 30)
SPLIT_DATE = date(2024, 7, 1)
LAST12_START = date(2025, 7, 1)

CANDIDATE_CELLS = (
    "f33_r30_be_1r",
    "f33_r30_be_never",
    "f33_r25_be_never",
    "f50_r25_be_never",
    "f67_r25_be_never",
    "f67_r30_be_never",
)

EARLY_ADVERSE_CELLS = (
    "eae30_r035",
    "eae60_r035",
    "eae30_r050",
    "eae60_r050",
)

FEATURES = (
    "spread_points",
    "atr",
    "body_fraction",
    "close_location",
    "directional_close_location",
    "three_bar_move_atr",
    "abs_three_bar_move_atr",
    "directional_three_bar_move_atr",
    "break_distance_atr",
    "estimated_cost_r",
    "signal_range",
    "recent_range",
    "recent_range_atr",
    "close_to_recent_extreme",
    "against_wick_points",
    "against_wick_body_ratio",
    "server_hour",
)

QUANTILES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.70, 0.75, 0.80, 0.85, 0.90)
DIRECTIONS = ("ANY", "LONG", "SHORT")
OPS = ("<=", ">=")


@dataclass(frozen=True)
class Gate:
    feature: str
    direction: str
    op: str
    threshold: float

    def label(self) -> str:
        return f"block_{self.direction}_{self.feature}_{self.op}_{self.threshold:g}"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def mt5_time(value: str) -> str:
    return parse_time(value).strftime("%Y.%m.%d %H:%M:%S")


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def signal_csv_for_trade_csv(path: str) -> Path:
    trade_path = Path(path)
    return trade_path.with_name(trade_path.name.replace("_trades.csv", "_signals.csv"))


def source_variant(path: str) -> str:
    name = Path(path).name
    marker = "_XAUUSD_M5_"
    if marker not in name:
        return name
    return name.split(marker, 1)[1].replace("_trades.csv", "")


def load_step1_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with IN_KEPT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("cell_id") not in CANDIDATE_CELLS:
                continue
            copied: dict[str, Any] = dict(row)
            copied["entry_dt"] = parse_time(row["entry_time"])
            copied["entry_date_obj"] = parse_date(row["entry_date"])
            copied["signal_pnl"] = as_float(row.get("signal_pnl") or row.get("signal_pnl_usd"), 0.0)
            copied["tickets"] = int(float(row.get("tickets") or 0))
            copied["variant"] = source_variant(row["source_csv"])
            rows.append(copied)
    return rows


def wanted_keys(rows: list[dict[str, Any]]) -> dict[Path, set[tuple[str, str]]]:
    wanted: dict[Path, set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        wanted[signal_csv_for_trade_csv(row["source_csv"])].add((mt5_time(row["entry_time"]), row["direction"]))
    return wanted


def decision_features(row: dict[str, str]) -> dict[str, float]:
    open_ = as_float(row.get("signal_open"))
    high = as_float(row.get("signal_high"))
    low = as_float(row.get("signal_low"))
    close = as_float(row.get("signal_close"))
    recent_high = as_float(row.get("recent_high"))
    recent_low = as_float(row.get("recent_low"))
    atr = as_float(row.get("atr"))
    direction = row.get("direction", "")
    three_bar = as_float(row.get("three_bar_move_atr"))
    close_location = as_float(row.get("close_location"))

    body = abs(close - open_) if finite(open_, close) else math.nan
    upper_wick = high - max(open_, close) if finite(high, open_, close) else math.nan
    lower_wick = min(open_, close) - low if finite(low, open_, close) else math.nan
    against_wick = upper_wick if direction == "LONG" else lower_wick if direction == "SHORT" else math.nan
    close_to_extreme = (
        close - recent_high
        if direction == "LONG" and finite(close, recent_high)
        else recent_low - close
        if direction == "SHORT" and finite(recent_low, close)
        else math.nan
    )
    signal_range = high - low if finite(high, low) else math.nan
    recent_range = recent_high - recent_low if finite(recent_high, recent_low) else math.nan
    directional_close = (
        close_location
        if direction == "LONG"
        else 1.0 - close_location
        if direction == "SHORT" and not math.isnan(close_location)
        else math.nan
    )
    directional_three_bar = (
        three_bar
        if direction == "LONG"
        else -three_bar
        if direction == "SHORT" and not math.isnan(three_bar)
        else math.nan
    )
    timestamp = row.get("timestamp_broker", "")
    hour = float(datetime.strptime(timestamp, "%Y.%m.%d %H:%M:%S").hour) if timestamp else math.nan

    return {
        "spread_points": as_float(row.get("spread_points")),
        "atr": atr,
        "body_fraction": as_float(row.get("body_fraction")),
        "close_location": close_location,
        "directional_close_location": directional_close,
        "three_bar_move_atr": three_bar,
        "abs_three_bar_move_atr": abs(three_bar) if not math.isnan(three_bar) else math.nan,
        "directional_three_bar_move_atr": directional_three_bar,
        "break_distance_atr": as_float(row.get("break_distance_atr")),
        "estimated_cost_r": as_float(row.get("estimated_cost_r")),
        "signal_range": signal_range,
        "recent_range": recent_range,
        "recent_range_atr": recent_range / atr if finite(recent_range, atr) and atr > 0 else math.nan,
        "close_to_recent_extreme": close_to_extreme,
        "against_wick_points": against_wick,
        "against_wick_body_ratio": against_wick / body if finite(against_wick, body) and body > 0 else math.nan,
        "server_hour": hour,
    }


def finite(*values: float) -> bool:
    return all(not math.isnan(value) for value in values)


def load_feature_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, float]]:
    wanted = wanted_keys(rows)
    features: dict[tuple[str, str, str], dict[str, float]] = {}
    for signal_path, keys in sorted(wanted.items()):
        if not signal_path.exists():
            continue
        with signal_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                if row.get("stage") != "WOULD_SIGNAL":
                    continue
                key = (row.get("timestamp_broker", ""), row.get("direction", ""))
                if key not in keys:
                    continue
                features[(str(signal_path), key[0], key[1])] = decision_features(row)
    return features


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_map = load_feature_map(rows)
    enriched: list[dict[str, Any]] = []
    missing = 0
    for row in rows:
        copied = dict(row)
        signal_path = signal_csv_for_trade_csv(row["source_csv"])
        key = (str(signal_path), mt5_time(row["entry_time"]), row["direction"])
        found = feature_map.get(key, {})
        if not found:
            missing += 1
        copied.update(found)
        copied["feature_join_missing"] = 1 if not found else 0
        enriched.append(copied)
    if missing:
        print(f"feature_join_missing={missing}")
    return enriched


def market_days(start: date = FROM_DATE, end: date = TO_DATE) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    return days


def max_closed_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def metrics(rows: list[dict[str, Any]], *, market_start: date = FROM_DATE, market_end: date = TO_DATE) -> dict[str, Any]:
    pnl = [float(row["signal_pnl"]) for row in rows]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    active_dates = {row["entry_date_obj"] for row in rows}
    weekdays = market_days(market_start, market_end)
    sorted_pnl = sorted(pnl, reverse=True)
    return {
        "signals": len(rows),
        "tickets": sum(int(row.get("tickets") or 0) for row in rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(rows) * 100.0) if rows else 0.0, 2),
        "net": round(sum(pnl), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else 0.0,
        "avg_win": round(gross_profit / len(wins), 2) if wins else 0.0,
        "avg_loss": round(gross_loss / len(losses), 2) if losses else 0.0,
        "win_loss_ratio": round((gross_profit / len(wins)) / (gross_loss / len(losses)), 4) if wins and losses else 0.0,
        "active_days": len(active_dates),
        "market_weekdays": len(weekdays),
        "active_day_pct": round((len(active_dates) / len(weekdays) * 100.0) if weekdays else 0.0, 2),
        "max_closed_dd": round(max_closed_drawdown(pnl), 2),
        "top25_removed": round(sum(sorted_pnl[25:]) if len(sorted_pnl) > 25 else sum(sorted_pnl), 2),
        "top100_removed": round(sum(sorted_pnl[100:]) if len(sorted_pnl) > 100 else sum(sorted_pnl), 2),
    }


def quantile_thresholds(values: list[float]) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 100:
        return []
    thresholds: list[float] = []
    for quantile in QUANTILES:
        index = round((len(clean) - 1) * quantile)
        thresholds.append(round(clean[index], 6))
    return sorted(set(thresholds))


def gate_blocks(row: dict[str, Any], gate: Gate) -> bool:
    if gate.direction != "ANY" and row.get("direction") != gate.direction:
        return False
    value = as_float(row.get(gate.feature))
    if math.isnan(value):
        return False
    return value <= gate.threshold if gate.op == "<=" else value >= gate.threshold


def apply_gates(rows: list[dict[str, Any]], gates: tuple[Gate, ...]) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    blocked = 0
    for row in rows:
        if any(gate_blocks(row, gate) for gate in gates):
            blocked += 1
        else:
            kept.append(row)
    return kept, blocked


def decision(row: dict[str, Any]) -> str:
    if row["signals"] < 700:
        return "FAIL_SAMPLE"
    if row["active_days"] < 300:
        return "FAIL_ACTIVITY_MINIMUM"
    if row["win_rate_pct"] >= 50.0 and row["win_loss_ratio"] >= 2.0:
        if row["active_day_pct"] >= 90.0:
            return "IN_SAMPLE_FULL_GOAL_HIT_REQUIRES_RETEST"
        return "IN_SAMPLE_WR_WL_HIT_ACTIVITY_FAIL"
    if row["win_rate_pct"] >= 49.0 and row["win_loss_ratio"] >= 1.8:
        return "IN_SAMPLE_NEAR_WR_WL"
    return "FAIL_WR_WL"


def score(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["decision"].startswith("IN_SAMPLE_WR_WL"),
        row["decision"] == "IN_SAMPLE_NEAR_WR_WL",
        row["win_rate_pct"] >= 50.0,
        row["win_loss_ratio"],
        row["win_rate_pct"],
        row["active_day_pct"],
        row["signals"],
        row["net"],
    )


def split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    older = [row for row in rows if row["entry_date_obj"] < SPLIT_DATE]
    newer = [row for row in rows if row["entry_date_obj"] >= SPLIT_DATE]
    last12 = [row for row in rows if row["entry_date_obj"] >= LAST12_START]
    older_metrics = metrics(older, market_start=FROM_DATE, market_end=date(2024, 6, 30))
    newer_metrics = metrics(newer, market_start=SPLIT_DATE, market_end=TO_DATE)
    last12_metrics = metrics(last12, market_start=LAST12_START, market_end=TO_DATE)
    return {
        "older_signals": older_metrics["signals"],
        "older_wr": older_metrics["win_rate_pct"],
        "older_wl": older_metrics["win_loss_ratio"],
        "older_net": older_metrics["net"],
        "newer_signals": newer_metrics["signals"],
        "newer_wr": newer_metrics["win_rate_pct"],
        "newer_wl": newer_metrics["win_loss_ratio"],
        "newer_net": newer_metrics["net"],
        "last12_signals": last12_metrics["signals"],
        "last12_wr": last12_metrics["win_rate_pct"],
        "last12_wl": last12_metrics["win_loss_ratio"],
        "last12_net": last12_metrics["net"],
    }


def summarize(cell_id: str, rows: list[dict[str, Any]], gates: tuple[Gate, ...], blocked: int, gate_type: str) -> dict[str, Any]:
    base = metrics(rows)
    result = {
        "cell_id": cell_id,
        "gate_type": gate_type,
        "gates": " AND ".join(gate.label() for gate in gates) if gates else "baseline",
        "blocked_signals": blocked,
        "blocked_pct": round((blocked / (blocked + len(rows)) * 100.0) if rows or blocked else 0.0, 2),
        **base,
    }
    result.update(split_metrics(rows))
    result["decision"] = decision(result)
    return result


def single_gate_rows(cell_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for feature in FEATURES:
        for direction in DIRECTIONS:
            scoped = [row for row in rows if direction == "ANY" or row.get("direction") == direction]
            thresholds = quantile_thresholds([as_float(row.get(feature)) for row in scoped])
            for op in OPS:
                for threshold in thresholds:
                    gate = Gate(feature, direction, op, threshold)
                    kept, blocked = apply_gates(rows, (gate,))
                    if blocked == 0:
                        continue
                    output.append(summarize(cell_id, kept, (gate,), blocked, "single"))
    return output


def two_gate_rows(cell_id: str, rows: list[dict[str, Any]], singles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gates: list[Gate] = []
    for row in sorted(singles, key=score, reverse=True)[:5]:
        gates.append(parse_gate(row["gates"]))
    output: list[dict[str, Any]] = []
    for i, first in enumerate(gates):
        for second in gates[i + 1 :]:
            if (first.feature, first.direction, first.op) == (second.feature, second.direction, second.op):
                continue
            kept, blocked = apply_gates(rows, (first, second))
            output.append(summarize(cell_id, kept, (first, second), blocked, "two_gate_limited"))
    return output


def parse_gate(label: str) -> Gate:
    prefix = "block_"
    if not label.startswith(prefix):
        raise ValueError(f"Cannot parse gate label: {label}")
    payload = label[len(prefix) :]
    direction, rest = payload.split("_", 1)
    op = "<=" if "_<=_" in rest else ">="
    feature, threshold = rest.rsplit(f"_{op}_", 1)
    return Gate(feature=feature, direction=direction, op=op, threshold=float(threshold))


def analyze() -> dict[str, Any]:
    rows = enrich_rows(load_step1_rows())
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cell[row["cell_id"]].append(row)

    baseline_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for cell_id in CANDIDATE_CELLS:
        cell_rows = by_cell[cell_id]
        baseline_rows.append(summarize(cell_id, cell_rows, tuple(), 0, "baseline"))
        singles = single_gate_rows(cell_id, cell_rows)
        gate_rows.extend(singles)
        gate_rows.extend(two_gate_rows(cell_id, cell_rows, singles))

    ranked = sorted(gate_rows, key=score, reverse=True)
    hits = [row for row in ranked if row["decision"].startswith("IN_SAMPLE_WR_WL")]
    near = [row for row in ranked if row["decision"] == "IN_SAMPLE_NEAR_WR_WL"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "IN_SAMPLE_HIT" if hits else "NO_IN_SAMPLE_WR_WL_HIT",
        "analysis_title": ANALYSIS_TITLE,
        "analysis_scope": ANALYSIS_SCOPE,
        "input_kept_signals_csv": str(IN_KEPT),
        "candidate_cells": list(CANDIDATE_CELLS),
        "features": list(FEATURES),
        "baseline": baseline_rows,
        "top_rows": ranked[:50],
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['analysis_title']}",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        f"Scope: {payload['analysis_scope']}. No live/demo runtime, chart, preset, order, or position was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Input kept signals: `{payload['input_kept_signals_csv']}`",
        f"- Candidate cells: `{', '.join(payload['candidate_cells'])}`",
        f"- Result CSV: `{OUT_CSV}`",
        "",
        "## Baselines",
        "",
        "| Cell | Signals | WR | W/L | Active days | PF | Net | DD | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["baseline"]:
        lines.append(result_line(row))

    if payload["hits"]:
        lines += ["", "## In-Sample WR/WL Hits", "", table_header()]
        for row in payload["hits"][:15]:
            lines.append(result_line(row, include_gate=True))
    else:
        lines += ["", "## In-Sample WR/WL Hits", "", "None."]

    if payload["near"]:
        lines += ["", "## Near Rows", "", table_header()]
        for row in payload["near"][:15]:
            lines.append(result_line(row, include_gate=True))

    lines += ["", "## Top Rows", "", table_header()]
    for row in payload["top_rows"][:20]:
        lines.append(result_line(row, include_gate=True))

    lines += [
        "",
        "## Interpretation",
        "",
        "- This is an in-sample diagnostic, not a survivor claim.",
        "- Any WR/WL hit still fails promotion unless implemented in MT5 and rerun exactly with frozen gates.",
        "- Daily activity remains an owner gate; filtered rows with active days below 90% require Step 3 portfolio work or a new family.",
    ]
    return "\n".join(lines) + "\n"


def table_header() -> str:
    return "| Cell | Gate | Blocked | Signals | WR | W/L | Active days | PF | Net | Splits W/L | Last12 W/L | Decision |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"


def result_line(row: dict[str, Any], include_gate: bool = False) -> str:
    if include_gate:
        return (
            f"| `{row['cell_id']}` | `{row['gates']}` | {row['blocked_signals']} ({row['blocked_pct']}%) | "
            f"{row['signals']} | {row['win_rate_pct']}% | {row['win_loss_ratio']} | {row['active_day_pct']}% | "
            f"{row['profit_factor']} | {row['net']} | {row['older_wl']}/{row['newer_wl']} | {row['last12_wl']} | `{row['decision']}` |"
        )
    return (
        f"| `{row['cell_id']}` | {row['signals']} | {row['win_rate_pct']}% | {row['win_loss_ratio']} | "
        f"{row['active_day_pct']}% | {row['profit_factor']} | {row['net']} | {row['max_closed_dd']} | `{row['decision']}` |"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze causal internal regime gates over exact MT5 kept signal ledgers.")
    parser.add_argument(
        "--early-adverse-exit",
        action="store_true",
        help="Analyze the early-adverse-exit exact probe kept signals instead of the Step 1 split grid.",
    )
    args = parser.parse_args()

    if args.early_adverse_exit:
        configure_early_adverse_exit()

    payload = analyze()
    print(OUT_MD)
    print(payload["status"])
    return 0


def configure_early_adverse_exit() -> None:
    global IN_KEPT, OUT_MD, OUT_JSON, OUT_CSV, CANDIDATE_CELLS, ANALYSIS_TITLE, ANALYSIS_SCOPE
    IN_KEPT = REPORTS / "A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_KEPT_SIGNALS_202207_202606.csv"
    OUT_MD = REPORTS / "A1_XAU_M5_EARLY_ADVERSE_EXIT_INTERNAL_GATE_DIAGNOSTIC_2026_07_05.md"
    OUT_JSON = OUT_MD.with_suffix(".json")
    OUT_CSV = OUT_MD.with_suffix(".csv")
    CANDIDATE_CELLS = EARLY_ADVERSE_CELLS
    ANALYSIS_TITLE = "A1 XAU M5 Early Adverse Exit Internal Gate Diagnostic"
    ANALYSIS_SCOPE = "offline causal gate diagnostic over exact MT5 early-adverse-exit signal ledgers and MT5 WOULD_SIGNAL rows"


if __name__ == "__main__":
    raise SystemExit(main())
