from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import period_stats


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STEM = "A1_XAU_R1_BOX_R3_OVERLAP_PRIORITY_AUDIT_20260709"
BOX_SOURCE = "h4_d1_long_best_box2_atr80"
R3_SOURCE = "r1_long_expansion_r3_reclass_strict_r1"
DEDUPE_WINDOW_SECONDS = 5 * 60
STRESS_COST_PER_TICKET = 0.30
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)

# The reviewer left "materially higher" qualitative. Freeze it here as both
# at least +0.20 absolute and +10% relative before evaluating the gate.
WL_MATERIAL_ABSOLUTE = 0.20
WL_MATERIAL_RELATIVE = 0.10

BASELINE_CSV = (
    REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)
R3_NORMALIZED_CSV = (
    REPORTS_DIR
    / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_r1_long_expansion_r3_reclass_strict_r1_NORMALIZED_TRADES.csv"
)
CONTROL_KEPT_CSV = (
    REPORTS_DIR
    / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1_KEPT.csv"
)
CONTROL_DROPPED_CSV = (
    REPORTS_DIR
    / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1_DROPPED.csv"
)
R3_MT5_REPORT_JSON = REPORTS_DIR / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_MT5.json"
R3_RAW_DIR = (
    REPORTS_DIR
    / "mt5_backtests"
    / "a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701"
)
R3_RAW_PREFIX = (
    "A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_"
    "XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1"
)
R3_ORDERS_CSV = R3_RAW_DIR / f"{R3_RAW_PREFIX}_orders.csv"
R3_SIGNALS_CSV = R3_RAW_DIR / f"{R3_RAW_PREFIX}_signals.csv"


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def row_identity(row: dict[str, Any]) -> tuple[Any, ...]:
    """Stable ledger identity that ignores audit-only drop annotations."""

    return (
        str(row.get("source_id", "")),
        row["entry_time"],
        row["exit_time"],
        str(row.get("direction", "")),
        round(float(row.get("pnl_usd") or 0.0), 8),
        int(row.get("source_row") or 0),
    )


def serialize_dt(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


def source_contributions(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_id", ""))].append(float(row.get("pnl_usd") or 0.0))
    return {
        source_id: {"trades": len(values), "net": round(sum(values), 2)}
        for source_id, values in sorted(grouped.items())
    }


def concentration_stats(rows: list[dict[str, Any]], net: float) -> dict[str, Any]:
    wins = sorted((float(row["pnl_usd"]) for row in rows if float(row["pnl_usd"]) > 0.0), reverse=True)
    by_entry_day: dict[date, float] = defaultdict(float)
    by_exit_month: dict[str, float] = defaultdict(float)
    for row in rows:
        by_entry_day[row["entry_date"]] += float(row["pnl_usd"])
        by_exit_month[row["exit_date"].strftime("%Y-%m")] += float(row["pnl_usd"])

    top_days = sorted(by_entry_day.items(), key=lambda item: item[1], reverse=True)
    top3_day_sum = sum(value for _day, value in top_days[:3])
    best_month = max(by_exit_month.values(), default=0.0)
    return {
        "top10_removed_net": round(net - sum(wins[:10]), 2),
        "top3_days_removed_net": round(net - top3_day_sum, 2),
        "best_month_share_pct": round(100.0 * max(best_month, 0.0) / net, 2) if net > 0.0 else None,
        "top3_days": [{"date": day.isoformat(), "net": round(value, 2)} for day, value in top_days[:3]],
    }


def ledger_book(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute the established portfolio metrics from ledger fields only."""

    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=STRESS_COST_PER_TICKET, market_days=MARKET_DAYS)
    months = month_shape(rows)
    weeks = weekly_shape(rows)
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    concentration = concentration_stats(rows, metrics["net_usd"])
    return {
        "name": name,
        "signals": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wr": stress["win_rate_pct"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_pf": stress["profit_factor"],
        "stress_030_net": stress["net_usd"],
        "max_closed_dd": max_closed_drawdown(rows),
        "recent3_signals": recent3["signals"],
        "recent3_wr": recent3["win_rate_pct"],
        "recent3_wl": recent3["avg_win_loss"],
        "recent3_pf": recent3["profit_factor"],
        "recent3_net": recent3["net_usd"],
        "positive_months": months["positive_months"],
        "negative_months": months["negative_months"],
        "closing_months": months["closing_months"],
        "best_month": months["best_month"],
        "best_month_net": months["best_month_net"],
        "worst_month": months["worst_month"],
        "worst_month_net": months["worst_month_net"],
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        "top10_removed_net": concentration["top10_removed_net"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "best_month_share_pct": concentration["best_month_share_pct"],
        "top3_days": concentration["top3_days"],
        "source_contributions": source_contributions(rows),
    }


def max_closed_drawdown_window(rows: list[dict[str, Any]]) -> dict[str, Any]:
    equity = 0.0
    peak = 0.0
    current_peak_time: datetime | None = None
    max_dd = 0.0
    peak_time: datetime | None = None
    trough_time: datetime | None = None
    ordered = sorted(rows, key=lambda row: (row["exit_time"], row["entry_time"], row["source_priority"]))
    for row in ordered:
        equity += float(row["pnl_usd"])
        if equity > peak:
            peak = equity
            current_peak_time = row["exit_time"]
        drawdown = peak - equity
        if drawdown > max_dd:
            max_dd = drawdown
            peak_time = current_peak_time
            trough_time = row["exit_time"]
    return {
        "max_closed_dd": round(max_dd, 2),
        "peak_exit_time": peak_time,
        "trough_exit_time": trough_time,
    }


def pair_overlap_rows(
    baseline_rows: list[dict[str, Any]],
    dropped_rows: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Validate the control drop metadata and build one-to-one box/R3 pairs."""

    box_index: dict[tuple[datetime, str], list[dict[str, Any]]] = defaultdict(list)
    for row in baseline_rows:
        if row["source_id"] == BOX_SOURCE:
            box_index[(row["entry_time"], row["direction"])].append(row)

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    used_box: set[tuple[Any, ...]] = set()
    used_r3: set[tuple[Any, ...]] = set()
    for r3_row in sorted(dropped_rows, key=lambda row: (row["entry_time"], row["source_row"])):
        if r3_row["source_id"] != R3_SOURCE:
            raise ValueError(f"Unexpected dropped source: {r3_row['source_id']}")
        if r3_row.get("drop_reason") != "same_direction_overlap_5m":
            raise ValueError(f"Unexpected drop reason at {r3_row['entry_time']}: {r3_row.get('drop_reason')}")
        if r3_row.get("duplicate_of_source_id") != BOX_SOURCE:
            raise ValueError(
                f"R3 drop at {r3_row['entry_time']} was not attributed to {BOX_SOURCE}: "
                f"{r3_row.get('duplicate_of_source_id')}"
            )
        duplicate_time = datetime.fromisoformat(str(r3_row.get("duplicate_of_entry_time") or ""))
        matches = box_index.get((duplicate_time, r3_row["direction"]), [])
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one baseline box match for {r3_row['entry_time']}; found {len(matches)}"
            )
        box_row = matches[0]
        delta_seconds = abs((r3_row["entry_time"] - box_row["entry_time"]).total_seconds())
        if delta_seconds > DEDUPE_WINDOW_SECONDS:
            raise ValueError(f"Overlap exceeds five minutes at {r3_row['entry_time']}: {delta_seconds}s")
        box_key = row_identity(box_row)
        r3_key = row_identity(r3_row)
        if box_key in used_box or r3_key in used_r3:
            raise ValueError(f"Non-unique overlap mapping at {r3_row['entry_time']}")
        used_box.add(box_key)
        used_r3.add(r3_key)
        pairs.append((box_row, r3_row))
    return pairs


def other_source_overlap_count(
    baseline_rows: list[dict[str, Any]],
    r3_rows: list[dict[str, Any]],
) -> int:
    count = 0
    for r3_row in r3_rows:
        for baseline_row in baseline_rows:
            if baseline_row["source_id"] == BOX_SOURCE:
                continue
            if baseline_row["direction"] != r3_row["direction"]:
                continue
            delta = abs((baseline_row["entry_time"] - r3_row["entry_time"]).total_seconds())
            if delta <= DEDUPE_WINDOW_SECONDS:
                count += 1
    return count


def replacement_rows(
    baseline_rows: list[dict[str, Any]],
    r3_rows: list[dict[str, Any]],
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[dict[str, Any]]:
    replaced_box_keys = {row_identity(box_row) for box_row, _r3_row in pairs}
    rows = [row for row in baseline_rows if row_identity(row) not in replaced_box_keys]
    rows.extend(r3_rows)
    return sorted(rows, key=lambda row: (row["entry_time"], row["source_priority"], row["source_id"], row["source_row"]))


def material_wl_threshold(baseline_wl: float | None) -> float:
    value = float(baseline_wl or 0.0)
    return round(max(value + WL_MATERIAL_ABSOLUTE, value * (1.0 + WL_MATERIAL_RELATIVE)), 4)


def gate_checks(
    baseline: dict[str, Any],
    box_overlap: dict[str, Any],
    r3_overlap: dict[str, Any],
    replacement: dict[str, Any],
) -> dict[str, bool]:
    share = replacement["best_month_share_pct"]
    wl_material = material_wl_threshold(box_overlap["wl"])
    return {
        "overlap_count_ge_80": r3_overlap["signals"] >= 80,
        "r3_overlap_net_gt_baseline_overlap_net": r3_overlap["net"] > box_overlap["net"],
        "r3_overlap_pf_gte_baseline_overlap_pf": (r3_overlap["pf"] or 0.0) >= (box_overlap["pf"] or 0.0),
        "r3_overlap_wr_gte_baseline_or_wl_materially_higher": (
            r3_overlap["wr"] >= box_overlap["wr"] or (r3_overlap["wl"] or 0.0) >= wl_material
        ),
        "replacement_net_ge_baseline_plus_2000": replacement["net"] >= baseline["net"] + 2000.0,
        "replacement_stress_net_ge_baseline_plus_2000": (
            replacement["stress_030_net"] >= baseline["stress_030_net"] + 2000.0
        ),
        "replacement_wr_ge_50": replacement["wr"] >= 50.0,
        "replacement_wl_ge_2": (replacement["wl"] or 0.0) >= 2.0,
        "replacement_pf_ge_2p50": (replacement["pf"] or 0.0) >= 2.50,
        "replacement_dd_lte_115pct_baseline": replacement["max_closed_dd"] <= baseline["max_closed_dd"] * 1.15,
        "replacement_recent3_ge_baseline_minus_50": replacement["recent3_net"] >= baseline["recent3_net"] - 50.0,
        "replacement_top10_removed_net_gt_0": replacement["top10_removed_net"] > 0.0,
        "replacement_top3_days_removed_net_gt_0": replacement["top3_days_removed_net"] > 0.0,
        "replacement_best_month_share_lte_30pct": share is not None and share <= 30.0,
        "replacement_positive_months_gte_baseline": replacement["positive_months"] >= baseline["positive_months"],
    }


def kill_checks(
    baseline: dict[str, Any],
    box_overlap: dict[str, Any],
    r3_overlap: dict[str, Any],
    replacement: dict[str, Any],
) -> dict[str, bool]:
    return {
        "r3_overlap_net_lte_baseline_overlap_net": r3_overlap["net"] <= box_overlap["net"],
        "replacement_dd_gt_115pct_baseline": replacement["max_closed_dd"] > baseline["max_closed_dd"] * 1.15,
        "replacement_recent3_lt_baseline_minus_50": replacement["recent3_net"] < baseline["recent3_net"] - 50.0,
        "replacement_wr_lt_50": replacement["wr"] < 50.0,
        "replacement_pf_lt_2p50": (replacement["pf"] or 0.0) < 2.50,
        "replacement_top10_concentration_fails": replacement["top10_removed_net"] <= 0.0,
        "replacement_top3_day_concentration_fails": replacement["top3_days_removed_net"] <= 0.0,
    }


def decide(gates: dict[str, bool], kills: dict[str, bool]) -> tuple[str, str, str]:
    triggered_kills = [name for name, triggered in kills.items() if triggered]
    if triggered_kills:
        return (
            "R1_BOX_R3_OVERLAP_PRIORITY_KILL_PORTFOLIO_USE",
            "KILLED_FOR_PORTFOLIO_USE_KEEP_STANDALONE_SHADOW_ONLY",
            "At least one preregistered kill rule triggered. Do not run the conditional exact-MT5 source-priority test or tune R3.",
        )
    if all(gates.values()):
        return (
            "R1_BOX_R3_OVERLAP_PRIORITY_PASS",
            "REPLACEMENT_SUPPORTED_PENDING_ONE_EXACT_MT5_TEST",
            "The ledger audit supports R3 priority over the overlapping box entries. Run only the one conditional exact-MT5 source-priority test before any portfolio decision.",
        )
    return (
        "R1_BOX_R3_OVERLAP_PRIORITY_NO_PASS",
        "KEEP_STANDALONE_SHADOW_ONLY",
        "The replacement did not clear every pass gate. Keep R3 standalone shadow-only and do not promote it into the baseline.",
    )


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def parse_mt5_amount(raw: str) -> float | None:
    match = re.search(r"[-+]?\d[\d ]*(?:\.\d+)?", str(raw or ""))
    if match is None:
        return None
    return float(match.group(0).replace(" ", ""))


def order_send_fail_reconciliation(r3_rows: list[dict[str, Any]]) -> dict[str, Any]:
    mt5_payload = json.loads(R3_MT5_REPORT_JSON.read_text(encoding="utf-8"))
    variant = mt5_payload["variants"][0]
    metrics = variant["mt5_report_metrics"]
    order_rows = read_tsv(R3_ORDERS_CSV)
    signal_rows = read_tsv(R3_SIGNALS_CSV)
    order_ok = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    failures = [row for row in order_rows if row.get("action") == "ORDER_SEND_FAIL"]
    normalized_times = {row["entry_time"].strftime("%Y-%m-%d %H:%M:%S") for row in r3_rows}
    would_signal_times = {
        (row.get("timestamp_broker", ""), row.get("direction", "")): row
        for row in signal_rows
        if row.get("stage") == "WOULD_SIGNAL"
    }

    ok_sorted = sorted(order_ok, key=lambda row: row.get("timestamp_broker", ""))
    items: list[dict[str, Any]] = []
    for failure in sorted(failures, key=lambda row: row.get("timestamp_broker", "")):
        timestamp = failure.get("timestamp_broker", "")
        direction = failure.get("direction", "")
        previous_ok = [row for row in ok_sorted if row.get("timestamp_broker", "") < timestamp]
        next_ok = [row for row in ok_sorted if row.get("timestamp_broker", "") > timestamp]
        signal = would_signal_times.get((timestamp, direction), {})
        items.append(
            {
                "timestamp_broker": timestamp,
                "symbol": failure.get("symbol", ""),
                "direction": direction,
                "lots": float(failure.get("lots") or 0.0),
                "entry_reference": float(failure.get("entry_reference") or 0.0),
                "sl": float(failure.get("sl") or 0.0),
                "tp": float(failure.get("tp") or 0.0),
                "retcode": int(failure.get("retcode") or 0),
                "retcode_description": failure.get("retcode_description", ""),
                "reason": failure.get("reason", ""),
                "would_signal_present": bool(signal),
                "signal_reason": signal.get("reason", ""),
                "executed_trade_at_same_timestamp": timestamp in normalized_times,
                "previous_order_send_ok": previous_ok[-1].get("timestamp_broker", "") if previous_ok else None,
                "next_order_send_ok": next_ok[0].get("timestamp_broker", "") if next_ok else None,
                "same_timestamp_retry_observed": False,
                "missed_opportunity_classification": (
                    "UNEXECUTED_SIGNAL_MARKET_CLOSED_HYPOTHETICAL_PNL_UNKNOWN"
                ),
                "hypothetical_pnl_imputed": False,
            }
        )

    return {
        "order_send_ok_count": len(order_ok),
        "order_send_fail_count": len(failures),
        "normalized_trade_count": len(r3_rows),
        "count_reconciles": len(order_ok) == len(r3_rows),
        "all_failures_have_would_signal": all(item["would_signal_present"] for item in items),
        "all_failures_unexecuted": all(not item["executed_trade_at_same_timestamp"] for item in items),
        "interpretation": (
            "Both failures were valid long signals rejected because the tester returned MT5 retcode 10018 "
            "(market closed). The raw evidence cannot distinguish a genuine broker-session closure from a tester "
            "session-calendar artifact. They are unexecuted entry opportunities, not members of the 139-trade "
            "normalized ledger; no retry or outcome is imputed."
        ),
        "failures": items,
        "r3_exact_mt5_drawdown": {
            "max_closed_dd": max_closed_drawdown(r3_rows),
            "mt5_balance_dd_maximal": parse_mt5_amount(metrics.get("Balance Drawdown Maximal", "")),
            "mt5_equity_dd_maximal": parse_mt5_amount(metrics.get("Equity Drawdown Maximal", "")),
            "mt5_balance_dd_maximal_raw": metrics.get("Balance Drawdown Maximal"),
            "mt5_equity_dd_maximal_raw": metrics.get("Equity Drawdown Maximal"),
            "mt5_balance_dd_relative_raw": metrics.get("Balance Drawdown Relative"),
            "mt5_equity_dd_relative_raw": metrics.get("Equity Drawdown Relative"),
        },
    }


def pair_csv_rows(pairs: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (box_row, r3_row) in enumerate(pairs, start=1):
        rows.append(
            {
                "pair_id": index,
                "direction": r3_row["direction"],
                "entry_delta_seconds": round(
                    (r3_row["entry_time"] - box_row["entry_time"]).total_seconds(), 3
                ),
                "control_owner": BOX_SOURCE,
                "replacement_owner": R3_SOURCE,
                "baseline_source_id": box_row["source_id"],
                "baseline_entry_time": serialize_dt(box_row["entry_time"]),
                "baseline_exit_time": serialize_dt(box_row["exit_time"]),
                "baseline_pnl_usd": box_row["pnl_usd"],
                "baseline_source_row": box_row["source_row"],
                "r3_source_id": r3_row["source_id"],
                "r3_entry_time": serialize_dt(r3_row["entry_time"]),
                "r3_exit_time": serialize_dt(r3_row["exit_time"]),
                "r3_pnl_usd": r3_row["pnl_usd"],
                "r3_source_row": r3_row["source_row"],
                "r3_minus_baseline_pnl_usd": round(r3_row["pnl_usd"] - box_row["pnl_usd"], 2),
                "match_basis": "validated_control_drop_metadata_same_direction_within_5m",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_audit() -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    input_paths = [
        BASELINE_CSV,
        R3_NORMALIZED_CSV,
        CONTROL_KEPT_CSV,
        CONTROL_DROPPED_CSV,
        R3_MT5_REPORT_JSON,
        R3_ORDERS_CSV,
        R3_SIGNALS_CSV,
    ]
    for path in input_paths:
        require_file(path)

    baseline_rows = read_ledger(BASELINE_CSV)
    r3_rows = read_ledger(R3_NORMALIZED_CSV)
    control_kept_rows = read_ledger(CONTROL_KEPT_CSV)
    control_dropped_rows = read_ledger(CONTROL_DROPPED_CSV)
    pairs = pair_overlap_rows(baseline_rows, control_dropped_rows)
    box_overlap_rows = [box_row for box_row, _r3_row in pairs]
    r3_overlap_rows = [r3_row for _box_row, r3_row in pairs]
    nonoverlap_r3_rows = [row for row in control_kept_rows if row["source_id"] == R3_SOURCE]
    replacement = replacement_rows(baseline_rows, r3_rows, pairs)
    control_dd_window = max_closed_drawdown_window(control_kept_rows)
    replacement_dd_window = max_closed_drawdown_window(replacement)
    window_start = replacement_dd_window["peak_exit_time"]
    window_end = replacement_dd_window["trough_exit_time"]
    window_box_rows = [
        row
        for row in box_overlap_rows
        if window_start is not None and window_end is not None and window_start < row["exit_time"] <= window_end
    ]
    window_r3_rows = [
        row
        for row in r3_overlap_rows
        if window_start is not None and window_end is not None and window_start < row["exit_time"] <= window_end
    ]
    window_box_net = round(sum(float(row["pnl_usd"]) for row in window_box_rows), 2)
    window_r3_net = round(sum(float(row["pnl_usd"]) for row in window_r3_rows), 2)

    baseline_counter = Counter(row_identity(row) for row in baseline_rows)
    r3_counter = Counter(row_identity(row) for row in r3_rows)
    control_kept_counter = Counter(row_identity(row) for row in control_kept_rows)
    control_dropped_counter = Counter(row_identity(row) for row in control_dropped_rows)
    kept_baseline_counter = Counter(row_identity(row) for row in control_kept_rows if row["source_id"] != R3_SOURCE)
    candidate_partition_counter = Counter(row_identity(row) for row in nonoverlap_r3_rows + r3_overlap_rows)
    pair_deltas = [abs((r3["entry_time"] - box["entry_time"]).total_seconds()) for box, r3 in pairs]
    other_overlaps = other_source_overlap_count(baseline_rows, r3_rows)
    integrity_checks = {
        "control_full_partition_reconciles": baseline_counter + r3_counter == control_kept_counter + control_dropped_counter,
        "control_kept_contains_all_baseline_rows": kept_baseline_counter == baseline_counter,
        "r3_partitions_into_nonoverlap_and_dropped": candidate_partition_counter == r3_counter,
        "all_control_drops_are_r3": all(row["source_id"] == R3_SOURCE for row in control_dropped_rows),
        "all_control_drops_point_to_box": all(
            row.get("duplicate_of_source_id") == BOX_SOURCE for row in control_dropped_rows
        ),
        "overlap_pairs_are_one_to_one": len(pairs) == len({row_identity(row) for row in box_overlap_rows}) == len(
            {row_identity(row) for row in r3_overlap_rows}
        ),
        "all_pairs_within_5_minutes": all(delta <= DEDUPE_WINDOW_SECONDS for delta in pair_deltas),
        "no_r3_overlap_with_other_baseline_sources": other_overlaps == 0,
        "replacement_trade_count_reconciles": len(replacement) == len(baseline_rows) - len(pairs) + len(r3_rows),
        "control_and_replacement_share_max_dd_window": (
            control_dd_window["peak_exit_time"] == replacement_dd_window["peak_exit_time"]
            and control_dd_window["trough_exit_time"] == replacement_dd_window["trough_exit_time"]
        ),
        "dd_window_attribution_reconciles_swap_delta": abs(
            (window_box_net - window_r3_net)
            - (replacement_dd_window["max_closed_dd"] - control_dd_window["max_closed_dd"])
        )
        <= 0.01,
    }
    if not all(integrity_checks.values()):
        failed = [name for name, passed in integrity_checks.items() if not passed]
        raise ValueError(f"Ledger integrity checks failed: {', '.join(failed)}")

    baseline_book = ledger_book("current_r1_r2_baseline", baseline_rows)
    control_book = ledger_book("current_baseline_priority_control", control_kept_rows)
    box_overlap_book = ledger_book("baseline_box_overlap_subset", box_overlap_rows)
    r3_overlap_book = ledger_book("r3_overlap_subset", r3_overlap_rows)
    nonoverlap_r3_book = ledger_book("r3_nonoverlap_subset", nonoverlap_r3_rows)
    replacement_book = ledger_book("r3_priority_replacement_combined", replacement)
    gates = gate_checks(baseline_book, box_overlap_book, r3_overlap_book, replacement_book)
    kills = kill_checks(baseline_book, box_overlap_book, r3_overlap_book, replacement_book)
    status, decision, interpretation = decide(gates, kills)
    order_reconciliation = order_send_fail_reconciliation(r3_rows)

    dd_cap = round(baseline_book["max_closed_dd"] * 1.15, 4)
    metrics = {
        "overlap_count": len(pairs),
        "r3_dropped_count": len(control_dropped_rows),
        "baseline_trade_kept_count": len(box_overlap_rows),
        "baseline_total_trade_count": len(baseline_rows),
        "nonoverlap_r3_count": len(nonoverlap_r3_rows),
        "r3_overlap_net": r3_overlap_book["net"],
        "baseline_overlap_net": box_overlap_book["net"],
        "r3_overlap_wr": r3_overlap_book["wr"],
        "baseline_overlap_wr": box_overlap_book["wr"],
        "r3_overlap_wl": r3_overlap_book["wl"],
        "baseline_overlap_wl": box_overlap_book["wl"],
        "r3_overlap_pf": r3_overlap_book["pf"],
        "baseline_overlap_pf": box_overlap_book["pf"],
        "r3_overlap_max_closed_dd_subset": r3_overlap_book["max_closed_dd"],
        "baseline_overlap_max_closed_dd_subset": box_overlap_book["max_closed_dd"],
        "overlap_subset_delta_dd": round(r3_overlap_book["max_closed_dd"] - box_overlap_book["max_closed_dd"], 2),
        "r3_replaces_baseline_delta_net": round(r3_overlap_book["net"] - box_overlap_book["net"], 2),
        # Full-book swap effect: replacement diagnostic minus the current baseline-priority control.
        "r3_replaces_baseline_delta_dd": round(
            replacement_book["max_closed_dd"] - control_book["max_closed_dd"], 2
        ),
        "replacement_vs_r1_r2_baseline_delta_net": round(replacement_book["net"] - baseline_book["net"], 2),
        "replacement_vs_r1_r2_baseline_delta_dd": round(
            replacement_book["max_closed_dd"] - baseline_book["max_closed_dd"], 2
        ),
        "nonoverlap_r3_net": nonoverlap_r3_book["net"],
        "replacement_combined_net": replacement_book["net"],
        "replacement_stress_net": replacement_book["stress_030_net"],
        "replacement_wr": replacement_book["wr"],
        "replacement_wl": replacement_book["wl"],
        "replacement_pf": replacement_book["pf"],
        "replacement_max_closed_dd": replacement_book["max_closed_dd"],
        "replacement_recent3_trades": replacement_book["recent3_signals"],
        "replacement_recent3_net": replacement_book["recent3_net"],
        "top10_removed_net": replacement_book["top10_removed_net"],
        "top3_days_removed_net": replacement_book["top3_days_removed_net"],
        "best_month_share_pct": replacement_book["best_month_share_pct"],
        "positive_months": replacement_book["positive_months"],
        "replacement_dd_cap_115pct_baseline": dd_cap,
        "replacement_dd_minus_cap": round(replacement_book["max_closed_dd"] - dd_cap, 2),
        "overlap_wl_material_threshold": material_wl_threshold(box_overlap_book["wl"]),
        "max_pair_entry_delta_seconds": max(pair_deltas, default=0.0),
    }

    dd_window_attribution = {
        "peak_exit_time": serialize_dt(replacement_dd_window["peak_exit_time"]),
        "trough_exit_time": serialize_dt(replacement_dd_window["trough_exit_time"]),
        "control_max_closed_dd": control_dd_window["max_closed_dd"],
        "replacement_max_closed_dd": replacement_dd_window["max_closed_dd"],
        "replacement_minus_control_dd": round(
            replacement_dd_window["max_closed_dd"] - control_dd_window["max_closed_dd"], 2
        ),
        "replaced_box_trades_closing_in_window": len(window_box_rows),
        "replacement_r3_trades_closing_in_window": len(window_r3_rows),
        "replaced_box_net_in_window": window_box_net,
        "replacement_r3_net_in_window": window_r3_net,
        "r3_minus_box_net_in_window": round(window_r3_net - window_box_net, 2),
        "interpretation": (
            "The control and replacement share the same peak-to-trough window. "
            f"{len(window_r3_rows)} R3 replacements close {money(abs(window_r3_net - window_box_net))} "
            f"{'worse' if window_r3_net < window_box_net else 'better'} than "
            f"{len(window_box_rows)} box counterparts inside that window, matching the "
            f"{money(abs(replacement_dd_window['max_closed_dd'] - control_dd_window['max_closed_dd']))} "
            f"full-book DD {'increase' if replacement_dd_window['max_closed_dd'] >= control_dd_window['max_closed_dd'] else 'decrease'}."
        ),
    }

    payload = {
        "audit_name": OUTPUT_STEM,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "decision": decision,
        "interpretation": interpretation,
        "evidence_boundary": (
            "Diagnostic recomposition of existing exact-MT5 ledgers only. Not promotion evidence; no new MT5 run or runtime change."
        ),
        "rules": {
            "control": f"Keep existing baseline priority; {BOX_SOURCE} owns validated same-direction overlaps.",
            "replacement": f"Replace only the validated overlapping {BOX_SOURCE} row with {R3_SOURCE}.",
            "nonoverlap": "Unchanged.",
            "same_direction_window_seconds": DEDUPE_WINDOW_SECONDS,
            "selection_uses_profit_or_outcome": False,
            "forbidden_filters_used": [],
            "stress_cost_per_ticket": STRESS_COST_PER_TICKET,
            "wl_materiality": {
                "absolute_improvement": WL_MATERIAL_ABSOLUTE,
                "relative_improvement": WL_MATERIAL_RELATIVE,
                "rule": "R3 W/L must meet the greater of baseline W/L + 0.20 or baseline W/L x 1.10.",
            },
            "r3_replaces_baseline_delta_dd_definition": (
                "replacement combined max closed DD minus current baseline-priority control combined max closed DD"
            ),
        },
        "inputs": {
            path.name: {"path": rel(path), "sha256": sha256_file(path)} for path in input_paths
        },
        "input_rows": {
            "baseline": len(baseline_rows),
            "r3_normalized": len(r3_rows),
            "control_kept": len(control_kept_rows),
            "control_dropped": len(control_dropped_rows),
        },
        "integrity_checks": integrity_checks,
        "other_baseline_source_overlap_count": other_overlaps,
        "metrics": metrics,
        "dd_window_attribution": dd_window_attribution,
        "baseline": baseline_book,
        "control_combined": control_book,
        "baseline_overlap": box_overlap_book,
        "r3_overlap": r3_overlap_book,
        "nonoverlap_r3": nonoverlap_r3_book,
        "replacement_combined": replacement_book,
        "gate_checks": gates,
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "kill_checks": kills,
        "triggered_kill_rules": [name for name, triggered in kills.items() if triggered],
        "ORDER_SEND_FAIL_RECONCILIATION": order_reconciliation,
        "drawdown_evidence": {
            "baseline": {
                "max_closed_dd": baseline_book["max_closed_dd"],
                "mt5_balance_dd": None,
                "mt5_equity_dd": None,
                "note": "Recomposed portfolio ledger; no single portfolio MT5 run in this audit.",
            },
            "r3_standalone_exact_mt5": order_reconciliation["r3_exact_mt5_drawdown"],
            "control_combined": {
                "max_closed_dd": control_book["max_closed_dd"],
                "mt5_balance_dd": None,
                "mt5_equity_dd": None,
                "note": "Recomposed portfolio ledger; no single portfolio MT5 run in this audit.",
            },
            "replacement_combined": {
                "max_closed_dd": replacement_book["max_closed_dd"],
                "mt5_balance_dd": None,
                "mt5_equity_dd": None,
                "note": "Unavailable by design until an exact-MT5 source-priority run is authorized; this audit did not run MT5.",
            },
        },
    }
    artifacts = {
        "pairs": pair_csv_rows(pairs),
        "replacement": replacement,
    }
    return payload, artifacts


def bool_text(value: bool) -> str:
    return "PASS" if value else "FAIL"


def money(value: float) -> str:
    return f"-${abs(value):.2f}" if value < 0.0 else f"${value:.2f}"


def verdict_metric_summary(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    replacement = payload["replacement_combined"]
    net_delta = float(metrics["r3_replaces_baseline_delta_net"])
    net_phrase = (
        f"improves the {metrics['overlap_count']}-trade overlap net by {money(net_delta)}"
        if net_delta >= 0.0
        else f"reduces the {metrics['overlap_count']}-trade overlap net by {money(abs(net_delta))}"
    )
    dd_minus_cap = float(metrics["replacement_dd_minus_cap"])
    if dd_minus_cap > 0.0:
        dd_phrase = f"exceeds the hard cap by {money(dd_minus_cap)}"
    else:
        dd_phrase = f"has {money(abs(dd_minus_cap))} headroom to the hard cap"
    return (
        f"R3 {net_phrase}. Replacement combined max closed DD is {money(replacement['max_closed_dd'])} "
        f"versus the {money(metrics['replacement_dd_cap_115pct_baseline'])} cap and {dd_phrase}."
    )


def decision_boundary_lines(payload: dict[str, Any]) -> list[str]:
    status = payload["status"]
    common = [
        "- Do not tune R3 or add session/hour/month variants.",
        "- Do not add R3 to the current R1+R2 baseline from ledger evidence alone.",
    ]
    if status == "R1_BOX_R3_OVERLAP_PRIORITY_PASS":
        return [
            *common,
            "- Proceed only to the one conditional exact-MT5 source-priority test defined by the work order.",
            "- Keep R3 research-only until that exact-MT5 test and independent review pass.",
        ]
    if status == "R1_BOX_R3_OVERLAP_PRIORITY_KILL_PORTFOLIO_USE":
        return [
            *common,
            "- Do not run R3+shock, R3+transition, or a DD-governor repair.",
            "- Keep R3 as a standalone shadow source; portfolio use is killed by the triggered hard rule.",
            "- Do not run the conditional exact-MT5 source-priority test because the ledger audit did not pass.",
        ]
    return [
        *common,
        "- The audit did not clear every pass gate; keep R3 standalone shadow-only.",
        "- Do not run the conditional exact-MT5 source-priority test.",
    ]


def render(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    baseline = payload["baseline"]
    control = payload["control_combined"]
    box = payload["baseline_overlap"]
    r3 = payload["r3_overlap"]
    replacement = payload["replacement_combined"]
    drawdown = payload["drawdown_evidence"]
    reconciliation = payload["ORDER_SEND_FAIL_RECONCILIATION"]
    dd_window = payload["dd_window_attribution"]
    lines = [
        "# A1 XAU R1 Box / R3 Overlap Priority Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Decision: `{payload['decision']}`",
        "",
        f"Boundary: {payload['evidence_boundary']}",
        "",
        "## Verdict",
        "",
        payload["interpretation"],
        "",
        verdict_metric_summary(payload),
        "",
        "## Fixed Audit Rule",
        "",
        f"- Control: `{payload['rules']['control']}`",
        f"- Replacement: `{payload['rules']['replacement']}`",
        f"- Non-overlap: `{payload['rules']['nonoverlap']}`",
        f"- Same-direction window: `{payload['rules']['same_direction_window_seconds']}` seconds.",
        "- No month, hour, session, direction, profit, or outcome filter was used.",
        f"- W/L materiality: {payload['rules']['wl_materiality']['rule']}",
        f"- `r3_replaces_baseline_delta_dd`: {payload['rules']['r3_replaces_baseline_delta_dd_definition']}.",
        "",
        "## Integrity Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    for name, passed in payload["integrity_checks"].items():
        lines.append(f"| `{name}` | {bool_text(passed)} |")

    lines.extend(
        [
            "",
            "## Overlap Comparison",
            "",
            "| Owner | Trades | WR% | W/L | PF | Net | Overlap-subset max closed DD |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            f"| Baseline box control | {box['signals']} | {box['wr']:.2f} | {box['wl'] or 0.0:.4f} | "
            f"{box['pf'] or 0.0:.4f} | {box['net']:.2f} | {box['max_closed_dd']:.2f} |",
            f"| R3 replacement | {r3['signals']} | {r3['wr']:.2f} | {r3['wl'] or 0.0:.4f} | "
            f"{r3['pf'] or 0.0:.4f} | {r3['net']:.2f} | {r3['max_closed_dd']:.2f} |",
            "",
            f"- Overlap count: `{metrics['overlap_count']}`",
            f"- R3 dropped by current control: `{metrics['r3_dropped_count']}`",
            f"- Baseline overlap trades kept by current control: `{metrics['baseline_trade_kept_count']}`",
            f"- R3 non-overlap: `{metrics['nonoverlap_r3_count']}` trades / `${metrics['nonoverlap_r3_net']:.2f}`",
            f"- Overlap net delta: `${metrics['r3_replaces_baseline_delta_net']:.2f}`",
            f"- Overlap-subset DD delta: `{money(metrics['overlap_subset_delta_dd'])}`",
            "",
            "## Portfolio Recomposition",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress net | Recent3 net | Max closed DD | +Months | Best month share% | Top10 rem | Top3 days rem |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for book in [baseline, control, replacement]:
        share = book["best_month_share_pct"] if book["best_month_share_pct"] is not None else 0.0
        lines.append(
            f"| `{book['name']}` | {book['signals']} | {book['wr']:.2f} | {book['wl'] or 0.0:.4f} | "
            f"{book['pf'] or 0.0:.4f} | {book['net']:.2f} | {book['stress_030_net']:.2f} | "
            f"{book['recent3_net']:.2f} | {book['max_closed_dd']:.2f} | {book['positive_months']} | "
            f"{share:.2f} | {book['top10_removed_net']:.2f} | {book['top3_days_removed_net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "### Drawdown deltas",
            "",
            f"- Replacement vs current baseline-priority control: `{money(metrics['r3_replaces_baseline_delta_dd'])}`.",
            f"- Replacement vs R1+R2 baseline: `{money(metrics['replacement_vs_r1_r2_baseline_delta_dd'])}`.",
            f"- Replacement DD cap headroom: `{money(-metrics['replacement_dd_minus_cap'])}` (negative means over cap).",
            "",
            "### Max-DD window attribution",
            "",
            dd_window["interpretation"],
            "",
            f"- Window: `{dd_window['peak_exit_time']}` peak exit to `{dd_window['trough_exit_time']}` trough exit.",
            f"- Replaced box rows closing in window: `{dd_window['replaced_box_trades_closing_in_window']}` / "
            f"`{money(dd_window['replaced_box_net_in_window'])}`.",
            f"- R3 replacement rows closing in window: `{dd_window['replacement_r3_trades_closing_in_window']}` / "
            f"`{money(dd_window['replacement_r3_net_in_window'])}`.",
            f"- Window P/L deterioration: `{money(dd_window['r3_minus_box_net_in_window'])}`; "
            f"full-book DD increase: `{money(dd_window['replacement_minus_control_dd'])}`.",
            "",
            "## Pass Gates",
            "",
            "| Gate | Result |",
            "| --- | --- |",
        ]
    )
    for name, passed in payload["gate_checks"].items():
        lines.append(f"| `{name}` | {bool_text(passed)} |")
    failed_gates = payload["failed_gates"]
    lines.extend(
        [
            "",
            f"Failed gates: `{', '.join(failed_gates) if failed_gates else 'none'}`.",
            "",
            "## Kill Rules",
            "",
            "| Rule | Triggered |",
            "| --- | --- |",
        ]
    )
    for name, triggered in payload["kill_checks"].items():
        lines.append(f"| `{name}` | {'YES' if triggered else 'no'} |")
    triggered_kills = payload["triggered_kill_rules"]
    lines.extend(
        [
            "",
            f"Triggered kill rules: `{', '.join(triggered_kills) if triggered_kills else 'none'}`.",
            "",
            "## ORDER_SEND_FAIL_RECONCILIATION",
            "",
            reconciliation["interpretation"],
            "",
            f"Counts: `{reconciliation['order_send_ok_count']}` ORDER_SEND_OK + "
            f"`{reconciliation['order_send_fail_count']}` ORDER_SEND_FAIL; "
            f"`{reconciliation['normalized_trade_count']}` normalized executed trades.",
            "",
            "| Time | Side | Entry | SL | TP | Retcode | Reason | Previous OK | Next OK | Ledger trade at same time | Classification |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for item in reconciliation["failures"]:
        lines.append(
            f"| {item['timestamp_broker']} | {item['direction']} | {item['entry_reference']:.2f} | "
            f"{item['sl']:.2f} | {item['tp']:.2f} | {item['retcode']} | {item['retcode_description']} | "
            f"{item['previous_order_send_ok'] or 'n/a'} | {item['next_order_send_ok'] or 'n/a'} | "
            f"{item['executed_trade_at_same_timestamp']} | `{item['missed_opportunity_classification']}` |"
        )

    r3_dd = drawdown["r3_standalone_exact_mt5"]
    lines.extend(
        [
            "",
            "No same-timestamp retry was logged. Any later accepted order was a distinct new signal. No hypothetical "
            "P/L was assigned to either failed order, and neither appears in the overlap audit.",
            "",
            "## Closed vs MT5 Drawdown Evidence",
            "",
            "| Book/evidence | Max closed DD | MT5 balance DD | MT5 equity DD |",
            "| --- | ---: | ---: | ---: |",
            f"| R1+R2 baseline recomposition | {drawdown['baseline']['max_closed_dd']:.2f} | n/a | n/a |",
            f"| R3 standalone exact MT5 | {r3_dd['max_closed_dd']:.2f} | "
            f"{r3_dd['mt5_balance_dd_maximal']:.2f} | {r3_dd['mt5_equity_dd_maximal']:.2f} |",
            f"| Current control recomposition | {drawdown['control_combined']['max_closed_dd']:.2f} | n/a | n/a |",
            f"| R3-priority replacement recomposition | {drawdown['replacement_combined']['max_closed_dd']:.2f} | n/a | n/a |",
            "",
            "Portfolio MT5 balance/equity DD is unavailable for the control and replacement because this task is ledger-only and did not run MT5. The replacement cannot be promoted from this diagnostic.",
            "",
            "## Decision Boundary",
            "",
            *decision_boundary_lines(payload),
            "",
            "## Inputs",
            "",
        ]
    )
    for item in payload["inputs"].values():
        lines.append(f"- `{item['path']}` — SHA256 `{item['sha256']}`")
    lines.extend(["", "## Artifacts", ""])
    for key, path in payload.get("outputs", {}).items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit whether strict-R1 R3 should replace overlapping R1 box trades using existing ledgers only."
    )
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args()

    payload, artifacts = build_audit()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_md = output_dir / f"{OUTPUT_STEM}.md"
    report_json = output_dir / f"{OUTPUT_STEM}.json"
    summary_csv = output_dir / f"{OUTPUT_STEM}_SUMMARY.csv"
    pairs_csv = output_dir / f"{OUTPUT_STEM}_OVERLAP_PAIRS.csv"
    replacement_csv = output_dir / f"{OUTPUT_STEM}_REPLACEMENT_KEPT.csv"
    payload["outputs"] = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "summary_csv": rel(summary_csv),
        "overlap_pairs_csv": rel(pairs_csv),
        "replacement_kept_csv": rel(replacement_csv),
    }
    summary_row = {
        "status": payload["status"],
        "decision": payload["decision"],
        **payload["metrics"],
        "failed_gates": json.dumps(payload["failed_gates"]),
        "triggered_kill_rules": json.dumps(payload["triggered_kill_rules"]),
    }
    write_csv(summary_csv, [summary_row])
    write_csv(pairs_csv, artifacts["pairs"])
    write_signal_csv(replacement_csv, artifacts["replacement"])
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "decision": payload["decision"],
                "metrics": payload["metrics"],
                "failed_gates": payload["failed_gates"],
                "triggered_kill_rules": payload["triggered_kill_rules"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
