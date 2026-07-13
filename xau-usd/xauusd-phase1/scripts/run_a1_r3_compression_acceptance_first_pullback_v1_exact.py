from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as metrics
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_PREREG_2026_07_10.md"
)
OUTPUT_STEM = "A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710"
SOURCE_ID = "r3_compression_acceptance_first_pullback_v1"
HISTORICAL_RUN_AUTHORIZED = True


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()

WINDOWS = {
    "prehistory_2016_2021": ("2016.01.01", "2021.12.31"),
    "current_2022_2026": ("2022.07.01", "2026.06.30"),
}

SIGNAL_PREFIXES = {
    "R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK_LONG",
    "R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK_SHORT",
}
LIFECYCLE_STAGES = {
    "registered": "R3_EVENT_REGISTERED",
    "accepted": "R3_H1_ACCEPTED",
    "consumed": "R3_EVENT_CONSUMED",
}

R3_INPUTS = {
    "InpSignalMode": "25",
    "InpDirectionMode": "0",
    "InpRegimeRouterMode": "5",
    "InpRegimeSnapshotLogEnabled": "true",
    "InpR3CompressionAtrPeriod": "14",
    "InpR3CompressionAtrPercentileLookback": "252",
    "InpR3CompressionAtrPercentileMax": "30.00",
    "InpR3CompressionBoxDays": "5",
    "InpR3CompressionRangeMedianLookback": "20",
    "InpR3CompressionRangeMedianMax": "1.00",
    "InpR3SetupLifetimeH1Bars": "24",
    "InpR3AcceptBreakMarginH1Atr": "0.10",
    "InpR3AcceptMinBodyFraction": "0.50",
    "InpR3AcceptLongCloseLocationMin": "0.75",
    "InpR3AcceptShortCloseLocationMax": "0.25",
    "InpR3RetestWindowM15Bars": "12",
    "InpR3RetestTouchM15Atr": "0.25",
    "InpR3InvalidationH1Atr": "0.10",
    "InpR3RejectDistanceM15Atr": "0.10",
    "InpR3RejectMinBodyFraction": "0.50",
    "InpR3RejectLongCloseLocationMin": "0.75",
    "InpR3RejectShortCloseLocationMax": "0.25",
    "InpR3StopBufferM15Atr": "0.20",
    "InpR3MaxStopH1Atr": "1.00",
    "InpR3ConsumeOnFirstTouch": "true",
    "InpRiskReward": "2.00",
    "InpStopFloorPoints": "0",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
    "InpMaxEstimatedCostR": "0.15",
    "InpUseRiskNormalizedLots": "true",
    "InpRiskAmountUsd": "50.00",
    "InpMaxRiskLots": "0.50",
    "InpRejectRiskOvershootEnabled": "true",
    "InpMaxRiskOvershootPct": "0.00",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpMaxTradesPerDay": "0",
    "InpCooldownMinutes": "0",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpUseDirectionalSessionFilter": "false",
    "InpLongSessionStartHour": "0",
    "InpLongSessionEndHour": "24",
    "InpShortSessionStartHour": "0",
    "InpShortSessionEndHour": "24",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpFeatureLossFilterEnabled": "false",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpH4D1SupportiveStateGuardEnabled": "false",
    "InpD1SupportStateGateMode": "0",
    "InpD1StructuralDownGateEnabled": "false",
    "InpPortfolioDailyGuardEnabled": "false",
    "InpH4D1WeeklyLossGovernorEnabled": "false",
    "InpH4D1PrevMonthHealthGateEnabled": "false",
    "InpH4D1NegativeStackGuardEnabled": "false",
    "InpH4D1ThirdEntryQualityGateEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpEarlyAdverseExitEnabled": "false",
}

FROZEN_INPUTS_SHA256 = stable_hash(R3_INPUTS)

REQUIRED_EA_TOKENS = (
    "SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK = 25",
    "TryR3CompressionH1AcceptM15FirstPullbackSignal",
    "InpSignalMode != SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK",
    "R3TransitionHardRiskAllowed",
    "OrderCalcProfit",
    "r3_normalized_entry_to_stop_risk_overshoot",
    "InpR3CompressionAtrPercentileLookback",
    "InpR3SetupLifetimeH1Bars",
    "InpR3RetestWindowM15Bars",
    "g_r3_setup_h1_bars_elapsed",
    "g_r3_pullback_m15_bars_elapsed",
    "InpR3ConsumeOnFirstTouch",
    "R3_EVENT_REGISTERED",
    "R3_H1_ACCEPTED",
    "R3_EVENT_CONSUMED",
    "window_end_incomplete",
)

ALLOWED_CONSUMPTION_OUTCOMES = {
    "entry",
    "first_touch_failed",
    "invalidated",
    "expired",
    "shock",
    "established_trend_handoff",
    "ambiguous",
    "window_end_incomplete",
}


def require_ready() -> None:
    for path in (EA_SOURCE, PREREG):
        if not path.exists():
            raise FileNotFoundError(path)
    source = EA_SOURCE.read_text(encoding="utf-8")
    missing = [token for token in REQUIRED_EA_TOKENS if token not in source]
    if missing:
        raise RuntimeError(
            "R3 acceptance/pullback infrastructure is not implemented; missing EA tokens: "
            + ", ".join(missing)
        )


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=SOURCE_ID,
            label=(
                "R3 completed-D1 compression, H1 acceptance, first M15 pullback; "
                "symmetric, shock-blocked, one position, $50 risk, 2R"
            ),
            run_id="BT_A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1",
            tester_inputs=dict(R3_INPUTS),
        )
    ]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def parse_reason(reason: str) -> tuple[str, dict[str, str]]:
    parts = [part.strip() for part in str(reason or "").split("|") if part.strip()]
    prefix = parts[0] if parts and "=" not in parts[0] else ""
    fields: dict[str, str] = {}
    for part in parts[1 if prefix else 0 :]:
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return prefix, fields


def lifecycle_audit(
    signal_rows: list[dict[str, str]], order_rows: list[dict[str, str]]
) -> dict[str, Any]:
    registered: Counter[str] = Counter()
    accepted: Counter[str] = Counter()
    consumed: Counter[str] = Counter()
    would_signal: Counter[str] = Counter()
    signal_by_timestamp: dict[str, list[dict[str, str]]] = defaultdict(list)
    unexpected_signal_reasons: list[str] = []
    native_signal_failures: list[str] = []
    invalid_consumption_outcomes: list[str] = []
    window_end_incomplete: Counter[str] = Counter()

    for row in signal_rows:
        stage = str(row.get("stage") or "")
        prefix, fields = parse_reason(str(row.get("reason") or ""))
        event_id = fields.get("event_id", "")
        if stage == LIFECYCLE_STAGES["registered"] and event_id:
            registered[event_id] += 1
        elif stage == LIFECYCLE_STAGES["accepted"] and event_id:
            accepted[event_id] += 1
        elif stage == LIFECYCLE_STAGES["consumed"] and event_id:
            consumed[event_id] += 1
            outcome = fields.get("outcome")
            if outcome not in ALLOWED_CONSUMPTION_OUTCOMES:
                invalid_consumption_outcomes.append(event_id)
            elif outcome == "window_end_incomplete":
                window_end_incomplete[event_id] += 1
        elif stage == "WOULD_SIGNAL":
            if prefix not in SIGNAL_PREFIXES or not event_id:
                unexpected_signal_reasons.append(str(row.get("reason") or ""))
                continue
            would_signal[event_id] += 1
            if not (
                fields.get("setup") == "COMPRESSED"
                and fields.get("phase") == "TRANSITION"
                and fields.get("shock") == "0"
                and fields.get("established") == "0"
            ):
                native_signal_failures.append(event_id)
            signal_by_timestamp[str(row.get("timestamp_broker") or "")].append(
                {"event_id": event_id, "direction": str(row.get("direction") or "").upper(), **fields}
            )

    duplicate_registrations = sorted(event_id for event_id, count in registered.items() if count != 1)
    duplicate_consumptions = sorted(event_id for event_id, count in consumed.items() if count != 1)
    duplicate_acceptances = sorted(event_id for event_id, count in accepted.items() if count > 1)
    duplicate_signals = sorted(event_id for event_id, count in would_signal.items() if count > 1)
    missing_consumptions = sorted(set(registered) - set(consumed))
    consumed_without_registration = sorted(set(consumed) - set(registered))
    accepted_without_registration = sorted(set(accepted) - set(registered))

    executed_rows = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    executed_event_ids: list[str] = []
    missing_executed_matches: list[str] = []
    impure_executed_matches: list[str] = []
    for row in executed_rows:
        timestamp = str(row.get("timestamp_broker") or "")
        direction = str(row.get("direction") or "").upper()
        matches = [item for item in signal_by_timestamp.get(timestamp, []) if item["direction"] == direction]
        if len(matches) != 1:
            missing_executed_matches.append(f"{timestamp}|{direction}")
            continue
        match = matches[0]
        executed_event_ids.append(match["event_id"])
        if not (
            match.get("setup") == "COMPRESSED"
            and match.get("phase") == "TRANSITION"
            and match.get("shock") == "0"
            and match.get("established") == "0"
        ):
            impure_executed_matches.append(match["event_id"])

    return {
        "registered_events": len(registered),
        "accepted_events": len(accepted),
        "consumed_events": len(consumed),
        "would_signal_events": len(would_signal),
        "duplicate_registrations": duplicate_registrations,
        "duplicate_consumptions": duplicate_consumptions,
        "duplicate_acceptances": duplicate_acceptances,
        "duplicate_signals": duplicate_signals,
        "missing_consumptions": missing_consumptions,
        "consumed_without_registration": consumed_without_registration,
        "accepted_without_registration": accepted_without_registration,
        "invalid_consumption_outcomes": sorted(set(invalid_consumption_outcomes)),
        "window_end_incomplete_events": sum(window_end_incomplete.values()),
        "window_end_incomplete_event_ids": sorted(window_end_incomplete),
        "unexpected_signal_reasons": unexpected_signal_reasons,
        "native_signal_failures": sorted(set(native_signal_failures)),
        "executed_event_ids": executed_event_ids,
        "missing_executed_matches": missing_executed_matches,
        "impure_executed_matches": impure_executed_matches,
        "event_by_timestamp": {
            timestamp: items[0]["event_id"]
            for timestamp, items in signal_by_timestamp.items()
            if len(items) == 1
        },
    }


def normalized_rows(result: dict[str, Any], event_by_timestamp: dict[str, str]) -> list[dict[str, Any]]:
    rows = metrics.mt5_rows(result, source_priority=90)
    for row in rows:
        entry_time = row.get("entry_time")
        timestamp = (
            entry_time.strftime("%Y.%m.%d %H:%M:%S")
            if isinstance(entry_time, datetime)
            else str(entry_time or "")
        )
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": result["name"],
                "family_group": "xau_r3_compression_transition",
                "cell_id": "r3_compression_acceptance_first_pullback_v1",
                "event_id": event_by_timestamp.get(timestamp, ""),
            }
        )
    return rows


def parse_maximal_dd(value: object) -> dict[str, float | None]:
    text = str(value or "").strip()
    match = re.search(r"([-+]?\d[\d\s,]*\.?\d*)\s*\(([-+]?\d+(?:\.\d+)?)%\)", text)
    if not match:
        return {"usd": None, "pct": None}
    return {
        "usd": float(match.group(1).replace(" ", "").replace(",", "")),
        "pct": float(match.group(2)),
    }


def parse_relative_dd(value: object) -> dict[str, float | None]:
    text = str(value or "").strip()
    match = re.search(r"([-+]?\d+(?:\.\d+)?)%\s*\(([-+]?\d[\d\s,]*\.?\d*)\)", text)
    if not match:
        return {"usd": None, "pct": None}
    return {
        "usd": float(match.group(2).replace(" ", "").replace(",", "")),
        "pct": float(match.group(1)),
    }


def drawdown_payload(result: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    report = result.get("mt5_report_metrics", {})
    return {
        "balance_maximal": parse_maximal_dd(report.get("Balance Drawdown Maximal")),
        "balance_relative": parse_relative_dd(report.get("Balance Drawdown Relative")),
        "equity_maximal": parse_maximal_dd(report.get("Equity Drawdown Maximal")),
        "equity_relative": parse_relative_dd(report.get("Equity Drawdown Relative")),
    }


def execution_audit(result: dict[str, Any], order_rows: list[dict[str, str]]) -> dict[str, Any]:
    output = guard_counts(result)
    failures = []
    for row in order_rows:
        if row.get("action") != "ORDER_SEND_FAIL":
            continue
        failures.append(
            {
                "timestamp_broker": row.get("timestamp_broker", ""),
                "direction": row.get("direction", ""),
                "retcode": row.get("retcode", ""),
                "retcode_description": row.get("retcode_description", ""),
                "reason": row.get("reason", ""),
            }
        )
    output["order_send_failures"] = failures
    output["unexplained_failure_count"] = sum(
        1
        for row in failures
        if not str(row["timestamp_broker"]).strip()
        or not str(row["retcode"]).strip()
        or not str(row["retcode_description"]).strip()
    )
    actual_risks = []
    missing_actual_risk = 0
    for row in order_rows:
        if row.get("action") != "ORDER_SEND_OK":
            continue
        try:
            value = float(str(row.get("actual_risk_usd") or "").strip())
        except ValueError:
            missing_actual_risk += 1
            continue
        if value <= 0.0:
            missing_actual_risk += 1
            continue
        actual_risks.append(value)
    output["actual_initial_risk_usd"] = {
        "count": len(actual_risks),
        "missing_count": missing_actual_risk,
        "minimum": round(min(actual_risks), 6) if actual_risks else None,
        "maximum": round(max(actual_risks), 6) if actual_risks else None,
        "mean": round(sum(actual_risks) / len(actual_risks), 6) if actual_risks else None,
        "above_50_count": sum(1 for value in actual_risks if value > 50.0000001),
    }
    return output


def direction_shape(rows: list[dict[str, Any]], direction: str) -> dict[str, Any]:
    selected = [row for row in rows if str(row.get("direction") or "").upper() == direction]
    return metrics.strip_heavy(metrics.flat_shape(f"{SOURCE_ID}_{direction.lower()}", selected))


def calendar_years(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["entry_date"].year].append(row)
    output = []
    for year, items in sorted(grouped.items()):
        stats = metrics.period_stats(items, date(year, 1, 1), date(year, 12, 31))
        output.append({"year": year, **stats})
    return {
        "rows": output,
        "exposure_years": len(output),
        "positive_years": sum(1 for row in output if row["net_usd"] > 0.0),
    }


def event_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnl: dict[str, float] = defaultdict(float)
    for row in rows:
        pnl[str(row.get("event_id") or "MISSING")] += float(row.get("pnl_usd") or 0.0)
    total_net = sum(pnl.values())
    best_event_id, best_event_net = max(pnl.items(), key=lambda item: item[1], default=("", 0.0))
    share = 100.0 * max(best_event_net, 0.0) / total_net if total_net > 0.0 else None
    return {
        "event_count": len(pnl),
        "missing_event_trade_count": sum(1 for row in rows if not row.get("event_id")),
        "best_event_id": best_event_id,
        "best_event_net": round(best_event_net, 2),
        "best_event_share_pct": round(share, 2) if share is not None else None,
    }


FORBIDDEN_GUARD_REASONS = {
    "blocked_entry_hour",
    "blocked_entry_day_hour",
    "direction_blocked_entry_hour",
    "directional_session_filter_block",
    "portfolio_daily_profit_target",
    "portfolio_daily_loss_stop",
    "h4_d1_previous_month_health_gate",
    "h4_d1_weekly_loss_governor",
    "h4_d1_negative_stack_guard",
    "h4_d1_third_entry_quality_gate",
}


def window_checks(
    book: dict[str, Any],
    dd: dict[str, dict[str, float | None]],
    orders: dict[str, Any],
    lifecycle: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, bool]:
    report_trades = int(re.sub(r"\D", "", str(result.get("mt5_report_metrics", {}).get("Total Trades", "0"))) or 0)
    actions = orders["actions"]
    reasons = orders["guard_reasons"]
    equity_usd = dd["equity_maximal"]["usd"]
    closed_dd = float(book["max_closed_dd"] or 0.0)
    return {
        "trades_ge_100": book["signals"] >= 100,
        "stress_net_gt_0": book["stress_030_net"] > 0.0,
        "balance_relative_dd_lte_20pct": (
            dd["balance_relative"]["pct"] is not None and dd["balance_relative"]["pct"] <= 20.0
        ),
        "equity_relative_dd_lte_20pct": (
            dd["equity_relative"]["pct"] is not None and dd["equity_relative"]["pct"] <= 20.0
        ),
        "net_to_equity_dd_ge_2": equity_usd is not None and equity_usd > 0.0 and book["net"] / equity_usd >= 2.0,
        "equity_dd_lte_2x_closed_dd": (
            equity_usd is not None and closed_dd > 0.0 and equity_usd <= 2.0 * closed_dd
        ),
        "successful_sends_reconcile": (
            actions.get("ORDER_SEND_OK", 0) == report_trades == book["signals"]
        ),
        "open_at_end_zero": all(bool(row.get("exit_time")) for row in book["data"]),
        "forbidden_guard_blocks_zero": not any(reasons.get(reason, 0) for reason in FORBIDDEN_GUARD_REASONS),
        "event_registration_unique": not lifecycle["duplicate_registrations"],
        "event_acceptance_unique": not lifecycle["duplicate_acceptances"]
        and not lifecycle["accepted_without_registration"],
        "event_consumption_exact": not lifecycle["duplicate_consumptions"]
        and not lifecycle["missing_consumptions"]
        and not lifecycle["consumed_without_registration"]
        and not lifecycle["invalid_consumption_outcomes"],
        "window_end_incomplete_lte_one": lifecycle["window_end_incomplete_events"] <= 1,
        "one_signal_per_event": not lifecycle["duplicate_signals"],
        "native_state_purity_100pct": not lifecycle["unexpected_signal_reasons"]
        and not lifecycle["native_signal_failures"]
        and not lifecycle["missing_executed_matches"]
        and not lifecycle["impure_executed_matches"],
        "order_failures_explained": orders["unexplained_failure_count"] == 0,
        "actual_initial_risk_reconciles_and_lte_50": (
            orders["actual_initial_risk_usd"]["count"] == actions.get("ORDER_SEND_OK", 0)
            and orders["actual_initial_risk_usd"]["missing_count"] == 0
            and orders["actual_initial_risk_usd"]["above_50_count"] == 0
        ),
    }


def global_checks(
    book: dict[str, Any],
    long_shape: dict[str, Any],
    short_shape: dict[str, Any],
    years: dict[str, Any],
    events: dict[str, Any],
    windows: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    return {
        "each_window_passes": all(all(window["checks"].values()) for window in windows.values()),
        "wr_ge_50": book["wr"] >= 50.0,
        "wl_ge_2": (book["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (book["pf"] or 0.0) >= 2.0,
        "stress_pf_ge_1p75": (book["stress_030_pf"] or 0.0) >= 1.75,
        "stress_net_gt_0": book["stress_030_net"] > 0.0,
        "exposure_years_ge_3": years["exposure_years"] >= 3,
        "positive_years_ge_3": years["positive_years"] >= 3,
        "long_trades_ge_50": long_shape["signals"] >= 50,
        "long_stress_net_gt_0": long_shape["stress_030_net"] > 0.0,
        "short_trades_ge_50": short_shape["signals"] >= 50,
        "short_stress_net_gt_0": short_shape["stress_030_net"] > 0.0,
        "top10_removed_net_gt_0": book["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": book["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30pct": (
            book["best_month_share_pct"] is not None and book["best_month_share_pct"] <= 30.0
        ),
        "best_event_share_lte_50pct": (
            events["best_event_share_pct"] is not None and events["best_event_share_pct"] <= 50.0
        ),
        "all_trades_have_event_id": events["missing_event_trade_count"] == 0,
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            output = dict(row)
            for key, value in output.items():
                if isinstance(value, datetime):
                    output[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, date):
                    output[key] = value.isoformat()
            writer.writerow(output)


def strip_window(window: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in window.items() if key != "_rows"}


def render(payload: dict[str, Any]) -> str:
    book = payload["global"]
    failed = [name for name, passed in payload["checks"].items() if not passed]
    lines = [
        "# A1 XAU R3 Compression Acceptance / First Pullback V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Frozen inputs SHA256: `{payload['frozen_inputs_sha256']}`",
        "",
        "Two frozen exact windows; one identical symmetric compression-transition candidate.",
        "",
        "## Window Results",
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Balance DD rel% | Equity DD rel% | Passed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, window in payload["windows"].items():
        row = window["book"]
        bal = window["drawdown"]["balance_relative"]["pct"] or 0.0
        eq = window["drawdown"]["equity_relative"]["pct"] or 0.0
        lines.append(
            f"| `{name}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | "
            f"{row['net']:.2f} | {bal:.2f} | {eq:.2f} | {all(window['checks'].values())} |"
        )
    lines.extend(
        [
            "",
            "## Actual Initial Risk (`OrderCalcProfit`)",
            "",
            "| Window | Count | Min USD | Mean USD | Max USD | Missing | Above $50 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, window in payload["windows"].items():
        risk = window["orders"]["actual_initial_risk_usd"]
        lines.append(
            f"| `{name}` | {risk['count']} | {risk['minimum'] or 0.0:.6f} | "
            f"{risk['mean'] or 0.0:.6f} | {risk['maximum'] or 0.0:.6f} | "
            f"{risk['missing_count']} | {risk['above_50_count']} |"
        )
    lines.extend(
        [
            "",
            "## Global Result",
            "",
            f"Trades `{book['signals']}`, WR `{book['wr']:.2f}%`, W/L `{book['wl'] or 0.0:.4f}`, "
            f"PF `{book['pf'] or 0.0:.4f}`, stress PF `{book['stress_030_pf'] or 0.0:.4f}`, "
            f"net `{book['net']:.2f}`.",
            "",
            f"Failed checks: `{', '.join(failed) if failed else 'none'}`",
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def run_window(name: str, start: str, end: str, timeout: int) -> dict[str, Any]:
    variants = build_variants()
    mt5.VARIANTS = variants
    tag = mt5.safe_name(f"OWNER_GOAL_R3_ACCEPT_PULLBACK_V1_{name}")
    mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.md"
    mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.json"
    exact = mt5.run_variants(
        from_date=start,
        to_date=end,
        tag=tag,
        report_md=mt5_md,
        report_json=mt5_json,
        variant_timeout_seconds=timeout,
        deposit="10000",
        currency="USD",
    )
    result = exact["variants"][0]
    order_rows = read_tsv(Path(result["order_csv"]))
    signal_rows = read_tsv(Path(result["signal_csv"]))
    lifecycle = lifecycle_audit(signal_rows, order_rows)
    rows = normalized_rows(result, lifecycle["event_by_timestamp"])
    book = metrics.evaluate_book(f"{SOURCE_ID}_{name}", rows)
    dd = drawdown_payload(result)
    orders = execution_audit(result, order_rows)
    checks = window_checks(book, dd, orders, lifecycle, result)
    ledger = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_NORMALIZED_TRADES.csv"
    write_rows(ledger, rows)
    return {
        "period": {"from": start, "to": end},
        "book": metrics.strip_heavy(book),
        "drawdown": dd,
        "orders": orders,
        "lifecycle": {key: value for key, value in lifecycle.items() if key != "event_by_timestamp"},
        "checks": checks,
        "outputs": {"mt5_md": rel(mt5_md), "mt5_json": rel(mt5_json), "ledger": rel(ledger)},
        "_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen two-window R3 compression acceptance/first-pullback exam."
    )
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    if args.static_only:
        source = EA_SOURCE.read_text(encoding="utf-8") if EA_SOURCE.exists() else ""
        payload = {
            "source_id": SOURCE_ID,
            "frozen_inputs_sha256": FROZEN_INPUTS_SHA256,
            "implementation_readiness": {
                token: token in source for token in REQUIRED_EA_TOKENS
            },
            "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
        }
        print(json.dumps(payload, indent=2))
        return 0 if PREREG.exists() else 1

    require_ready()
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Historical run has not been authorized after implementation review")
    window_results = {
        name: run_window(name, start, end, args.variant_timeout_seconds)
        for name, (start, end) in WINDOWS.items()
    }
    all_rows = [row for window in window_results.values() for row in window["_rows"]]
    global_book = metrics.evaluate_book(SOURCE_ID, all_rows)
    long_shape = direction_shape(all_rows, "LONG")
    short_shape = direction_shape(all_rows, "SHORT")
    years = calendar_years(all_rows)
    events = event_concentration(all_rows)
    checks = global_checks(
        global_book,
        long_shape,
        short_shape,
        years,
        events,
        window_results,
    )
    status = (
        "R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_STANDALONE_SHADOW"
        if all(checks.values())
        else "R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_NO_SURVIVOR"
    )

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    global_csv = REPORTS_DIR / f"{OUTPUT_STEM}_GLOBAL_NORMALIZED_TRADES.csv"
    write_rows(global_csv, all_rows)
    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "global_ledger": rel(global_csv),
    }
    for name, window in window_results.items():
        for key, value in window["outputs"].items():
            outputs[f"{name}_{key}"] = value

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "source_id": SOURCE_ID,
        "frozen_inputs": R3_INPUTS,
        "frozen_inputs_sha256": FROZEN_INPUTS_SHA256,
        "windows": {name: strip_window(window) for name, window in window_results.items()},
        "global": metrics.strip_heavy(global_book),
        "direction": {"LONG": long_shape, "SHORT": short_shape},
        "calendar_years": years,
        "event_concentration": events,
        "checks": checks,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "checks": checks, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
