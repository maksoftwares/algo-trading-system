from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "a3_ml_shared_account_replay_status_v1"
WINDOWS = (
    ("last_3_months", "2026-04-01T00:00:00Z", "2026-06-30T23:59:59Z"),
    ("last_6_months", "2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
    ("last_5_years", "2021-07-01T00:00:00Z", "2026-06-30T23:59:59Z"),
    ("last_10_years", "2016-07-01T00:00:00Z", "2026-06-30T23:59:59Z"),
)


def run_shared_account_replay(root: Path, contract_path: Path) -> Path:
    root = root.resolve()
    contract_path = contract_path.resolve()
    contract = _read_json(contract_path)
    _validate_contract(contract)
    start = _parse_time(contract["period_start"])
    end = _parse_time(contract["period_end"])
    mt5_path = _resolve(root, contract["mt5_portfolio_json"])
    mt5_payload = _read_json(mt5_path)
    candidates, source_audits = _load_candidates(root, mt5_payload, contract)
    bars, bar_audits = _load_bars(root, contract["bar_sources"], start, end)
    if not candidates or not bars:
        raise ValueError("shared-account replay requires candidates and M5 bars")

    bar_ends = [bar["end"] for bar in bars]
    profile_payloads: dict[str, Any] = {}
    all_decisions: list[dict[str, Any]] = []
    all_daily: list[dict[str, Any]] = []
    for profile in contract["profiles"]:
        decisions, accepted = _admit_candidates(candidates, profile, contract, bars, bar_ends)
        equity = _equity_replay(
            accepted,
            bars,
            initial_balance=float(contract["initial_balance_usd"]),
            contract_size=float(contract["contract_size"]),
            assumed_leverage=float(contract["assumed_leverage"]),
            exit_cost=float(contract["stress_cost_per_trade_usd"]),
        )
        stats = _profile_stats(accepted, bars, contract, equity)
        profile_payloads[profile["name"]] = {
            "contract": profile,
            "accepted": sum(1 for row in decisions if row["accepted"]),
            "rejected": sum(1 for row in decisions if not row["accepted"]),
            "rejection_reasons": _counts(row["decision_reason"] for row in decisions if not row["accepted"]),
            "statistics": stats,
            "equity": {key: value for key, value in equity.items() if key != "daily"},
        }
        all_decisions.extend({"profile": profile["name"], **row} for row in decisions)
        all_daily.extend({"profile": profile["name"], **row} for row in equity["daily"])

    calibration = _calibrate_components(candidates, source_audits, bars, contract)
    magic_audit = _magic_audit(source_audits)
    baseline = profile_payloads["unconstrained_shared_baseline"]
    controlled = profile_payloads["risk_controlled_shared_account"]
    expected_net = round(sum(row["profit_usd"] for row in candidates), 2)
    baseline_stats = baseline["statistics"]["windows"]["last_10_years"]
    controlled_stats = controlled["statistics"]["windows"]["last_10_years"]
    largest_component_dd = max((row["mt5_equity_drawdown_usd"] for row in source_audits), default=0.0)
    shared_dd = float(controlled["equity"]["max_equity_drawdown_usd"])
    conservative_dd = max(largest_component_dd, shared_dd)
    conservative_dd_pct = 100.0 * conservative_dd / float(contract["initial_balance_usd"])
    controlled["equity"]["largest_component_mt5_equity_drawdown_usd"] = round(largest_component_dd, 2)
    controlled["equity"]["conservative_drawdown_usd"] = round(conservative_dd, 2)
    controlled["equity"]["conservative_drawdown_pct_of_initial"] = round(conservative_dd_pct, 4)

    gates = {
        "baseline_trade_count_reconciles": baseline["accepted"] == len(candidates),
        "baseline_net_pnl_reconciles": abs(float(baseline_stats["net_usd"]) - expected_net) <= 0.01,
        "unique_specialist_magic_numbers": magic_audit["unique"],
        "component_equity_calibration": all(row["pass"] for row in calibration),
        "ten_year_stress_pf_ge_minimum": (controlled_stats["stress_profit_factor"] or 0.0)
        >= float(contract["minimum_stress_profit_factor"]),
        "conservative_equity_drawdown_lte_limit": conservative_dd_pct
        <= float(contract["equity_drawdown_limit_pct"]),
        "six_month_nonnegative_share_ge_minimum": controlled["statistics"]["six_month_nonnegative_share"]
        >= float(contract["minimum_nonnegative_six_month_share"]),
        "risk_admission_limits_respected": _risk_limits_respected(all_decisions, contract),
        "authorization_boundary_closed": _authorization_closed(contract),
    }
    outputs = contract["outputs"]
    report_json = _resolve(root, outputs["report_json"])
    report_md = _resolve(root, outputs["report_md"])
    decisions_csv = _resolve(root, outputs["decisions_csv"])
    daily_csv = _resolve(root, outputs["daily_csv"])
    preregistration = _resolve(root, contract["preregistration"])
    _write_rows(decisions_csv, all_decisions)
    _write_rows(daily_csv, all_daily)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "RESEARCH_GATES_PASS" if all(gates.values()) else "RESEARCH_GATES_FAIL",
        "created_at_utc": _format_time(datetime.now(timezone.utc)),
        "scope": {
            "symbol": contract["symbol"],
            "period_start": contract["period_start"],
            "period_end": contract["period_end"],
            "initial_balance_usd": contract["initial_balance_usd"],
            "contract_size": contract["contract_size"],
            "assumed_leverage": contract["assumed_leverage"],
            "stress_cost_per_trade_usd": contract["stress_cost_per_trade_usd"],
            "frequency_target_trades_per_market_day": contract["frequency_target_trades_per_market_day"],
        },
        "source_audits": source_audits,
        "bar_audits": bar_audits,
        "magic_audit": magic_audit,
        "component_calibration": calibration,
        "profiles": profile_payloads,
        "capital_required_for_fixed_lot_drawdown": {
            "at_10pct_usd": round(conservative_dd / 0.10, 2),
            "at_15pct_usd": round(conservative_dd / 0.15, 2),
        },
        "frequency_target_met": controlled_stats["trades_per_market_day"]
        >= float(contract["frequency_target_trades_per_market_day"]),
        "gates": gates,
        "authorization": {
            "research_only": True,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "limitations": [
            "Source trades come from isolated MT5 component tests; replay cannot reproduce broker margin calls, order rejection, or execution contention exactly.",
            "M5 bar extrema provide a conservative path estimate but do not preserve tick-level high/low ordering.",
            "Recent MT5 bars expose one spread value per bar, so ask OHLC is approximated from bid OHLC plus that spread.",
            "All history is development data, not an untouched final holdout.",
            "Frequency is measured, never manufactured; no candidate is added to satisfy the target.",
        ],
        "artifacts": {
            "contract": str(contract_path),
            "contract_sha256": _sha256_file(contract_path),
            "preregistration": str(preregistration),
            "preregistration_sha256": _sha256_file(preregistration),
            "mt5_portfolio_json": str(mt5_path),
            "mt5_portfolio_sha256": _sha256_file(mt5_path),
            "decisions_csv": str(decisions_csv),
            "decisions_sha256": _sha256_file(decisions_csv),
            "daily_csv": str(daily_csv),
            "daily_sha256": _sha256_file(daily_csv),
            "report_json": str(report_json),
            "report_md": str(report_md),
        },
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(_render(payload), encoding="utf-8")
    return report_json


def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_shared_account_replay_v1":
        raise ValueError("unsupported shared-account replay schema")
    names = [profile.get("name") for profile in contract.get("profiles", [])]
    if names != ["unconstrained_shared_baseline", "risk_controlled_shared_account"]:
        raise ValueError("shared-account replay requires the two frozen profiles in order")
    if not _authorization_closed(contract):
        raise ValueError("shared-account replay authorization boundary must remain closed")


def _load_candidates(
    root: Path, mt5_payload: dict[str, Any], contract: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    contract_size = float(contract["contract_size"])
    for result in mt5_payload.get("variants", []):
        source = str(result.get("name", ""))
        trade_path = _result_path(root, result.get("trade_csv"))
        order_path = _result_path(root, result.get("order_csv"))
        orders = _successful_orders(order_path)
        source_rows: list[dict[str, Any]] = []
        with trade_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                key = (row["entry_time"], row["direction"].upper(), str(row["entry_deal"]))
                matches = orders.get(key, [])
                if len(matches) != 1:
                    raise ValueError(f"{source} trade must join exactly one successful order: {key} matches={len(matches)}")
                order = matches[0]
                entry_price = float(row["entry_price"])
                stop_loss = float(order["sl"])
                volume = float(row["volume"])
                if stop_loss <= 0.0:
                    raise ValueError(f"{source} trade has no initial stop: {key}")
                candidate = {
                    "candidate_id": f"{source}:{row['entry_deal']}",
                    "source": source,
                    "assigned_regime": "R1_UPTREND_LONG" if row["direction"].upper() == "LONG" else "R2_DOWNTREND_SHORT",
                    "entry_time": row["entry_time"],
                    "entry_dt": _parse_time(row["entry_time"]),
                    "exit_time": row["exit_time"],
                    "exit_dt": _parse_time(row["exit_time"]),
                    "direction": row["direction"].upper(),
                    "entry_deal": str(row["entry_deal"]),
                    "exit_deal": str(row["exit_deal"]),
                    "magic": str(order["magic"]),
                    "volume": volume,
                    "entry_price": entry_price,
                    "exit_price": float(row["exit_price"]),
                    "stop_loss": stop_loss,
                    "take_profit": float(order["tp"]),
                    "initial_risk_usd": abs(entry_price - stop_loss) * contract_size * volume,
                    "notional_usd": entry_price * contract_size * volume,
                    "profit_usd": float(row["profit_aed"]),
                    "exit_comment": row.get("exit_comment", ""),
                }
                if candidate["exit_dt"] < candidate["entry_dt"]:
                    raise ValueError(f"candidate exits before entry: {candidate['candidate_id']}")
                source_rows.append(candidate)
        candidates.extend(source_rows)
        mt5_dd_raw = result.get("mt5_report_metrics", {}).get("Equity Drawdown Maximal")
        audits.append(
            {
                "source": source,
                "trades": len(source_rows),
                "trade_csv": str(trade_path),
                "trade_sha256": _sha256_file(trade_path),
                "order_csv": str(order_path),
                "order_sha256": _sha256_file(order_path),
                "magic_numbers": sorted({row["magic"] for row in source_rows}),
                "mt5_history_quality": result.get("mt5_report_metrics", {}).get("History Quality"),
                "mt5_equity_drawdown_raw": mt5_dd_raw,
                "mt5_equity_drawdown_usd": _parse_money(mt5_dd_raw),
            }
        )
    candidates.sort(key=lambda row: (row["entry_dt"], row["source"], _safe_int(row["entry_deal"])))
    keys = [row["candidate_id"] for row in candidates]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate candidate IDs")
    return candidates, audits


def _successful_orders(path: Path) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    output: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = handle.readline()
        delimiter = "\t" if "\t" in header else ","
        handle.seek(0)
        for row in csv.DictReader(handle, delimiter=delimiter):
            if row.get("action") != "ORDER_SEND_OK":
                continue
            key = (row["timestamp_broker"], row["direction"].upper(), str(row["deal_ticket"]))
            output[key].append(row)
    return output


def _load_bars(
    root: Path, sources: list[dict[str, Any]], start: datetime, end: datetime
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bars_by_start: dict[datetime, dict[str, Any]] = {}
    audits = []
    for source in sources:
        path = _resolve(root, source["path"])
        style = source["style"]
        rows = 0
        selected = 0
        overwritten = 0
        first: datetime | None = None
        last: datetime | None = None
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                rows += 1
                bar = _normalize_bar(row, style)
                if bar["end"] < start or bar["start"] > end:
                    continue
                selected += 1
                first = min(first, bar["start"]) if first else bar["start"]
                last = max(last, bar["end"]) if last else bar["end"]
                if bar["start"] in bars_by_start:
                    overwritten += 1
                bars_by_start[bar["start"]] = bar
        audits.append(
            {
                "path": str(path),
                "sha256": _sha256_file(path),
                "style": style,
                "rows": rows,
                "selected_rows": selected,
                "overwritten_boundary_rows": overwritten,
                "first_bar": _format_time(first) if first else "",
                "last_bar": _format_time(last) if last else "",
            }
        )
    bars = [bars_by_start[key] for key in sorted(bars_by_start)]
    if any(bars[index]["end"] > bars[index + 1]["end"] for index in range(len(bars) - 1)):
        raise ValueError("M5 bars are not chronological")
    return bars, audits


def _normalize_bar(row: dict[str, str], style: str) -> dict[str, Any]:
    start = _parse_time(row["bar_start_utc"])
    end = _parse_time(row["bar_end_utc"])
    if style == "capital_processed_bid_ask":
        values = {
            "bid_low": float(row["bid_low"]),
            "bid_high": float(row["bid_high"]),
            "bid_close": float(row["bid_close"]),
            "ask_low": float(row["ask_low"]),
            "ask_high": float(row["ask_high"]),
            "ask_close": float(row["ask_close"]),
        }
    elif style == "mt5_bid_plus_spread":
        spread = float(row["spread"]) * 0.01
        values = {
            "bid_low": float(row["low"]),
            "bid_high": float(row["high"]),
            "bid_close": float(row["close"]),
            "ask_low": float(row["low"]) + spread,
            "ask_high": float(row["high"]) + spread,
            "ask_close": float(row["close"]) + spread,
        }
    else:
        raise ValueError(f"unsupported M5 bar style: {style}")
    return {"start": start, "end": end, **values}


def _admit_candidates(
    candidates: list[dict[str, Any]],
    profile: dict[str, Any],
    contract: dict[str, Any],
    bars: list[dict[str, Any]],
    bar_ends: list[datetime],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    balance = float(contract["initial_balance_usd"])
    stress_cost = float(contract["stress_cost_per_trade_usd"])
    leverage = float(contract["assumed_leverage"])
    contract_size = float(contract["contract_size"])
    open_rows: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    daily_start: dict[str, float] = {}
    daily_realized: dict[str, float] = defaultdict(float)

    def close_until(timestamp: datetime) -> None:
        nonlocal balance, open_rows
        closing = sorted((row for row in open_rows if row["exit_dt"] <= timestamp), key=lambda row: row["exit_dt"])
        for row in closing:
            day = row["exit_dt"].date().isoformat()
            daily_start.setdefault(day, balance)
            pnl = row["profit_usd"] - stress_cost
            balance += pnl
            daily_realized[day] += pnl
        closed_ids = {row["candidate_id"] for row in closing}
        open_rows = [row for row in open_rows if row["candidate_id"] not in closed_ids]

    for candidate in candidates:
        close_until(candidate["entry_dt"])
        day = candidate["entry_dt"].date().isoformat()
        daily_start.setdefault(day, balance)
        bar = _bar_at_or_before(candidate["entry_dt"], bars, bar_ends)
        equity = _marked_equity(balance, open_rows, bar, contract_size)
        denominator = max(equity, 0.01)
        open_risk = sum(row["initial_risk_usd"] for row in open_rows)
        same_risk = sum(
            row["initial_risk_usd"] for row in open_rows if row["direction"] == candidate["direction"]
        )
        margin = sum(row["notional_usd"] / leverage for row in open_rows)
        candidate_margin = candidate["notional_usd"] / leverage
        trade_risk_pct = 100.0 * candidate["initial_risk_usd"] / denominator
        total_risk_pct = 100.0 * (open_risk + candidate["initial_risk_usd"]) / denominator
        same_risk_pct = 100.0 * (same_risk + candidate["initial_risk_usd"]) / denominator
        margin_pct = 100.0 * (margin + candidate_margin) / denominator
        daily_loss_pct = 100.0 * max(0.0, -daily_realized[day]) / max(daily_start[day], 0.01)
        reason = "ACCEPT"
        checks = (
            (len(open_rows) >= int(profile["max_concurrent_positions"]), "MAX_CONCURRENT_POSITIONS"),
            (trade_risk_pct > float(profile["max_trade_initial_risk_pct"]), "MAX_TRADE_INITIAL_RISK"),
            (total_risk_pct > float(profile["max_total_initial_risk_pct"]), "MAX_TOTAL_INITIAL_RISK"),
            (same_risk_pct > float(profile["max_same_direction_initial_risk_pct"]), "MAX_SAME_DIRECTION_RISK"),
            (margin_pct > float(profile["max_margin_utilization_pct"]), "MAX_MARGIN_UTILIZATION"),
            (daily_loss_pct >= float(profile["daily_realized_loss_halt_pct"]), "DAILY_REALIZED_LOSS_HALT"),
        )
        for failed, code in checks:
            if failed:
                reason = code
                break
        is_accepted = reason == "ACCEPT"
        decision = {
            "candidate_id": candidate["candidate_id"],
            "source": candidate["source"],
            "assigned_regime": candidate["assigned_regime"],
            "entry_time": candidate["entry_time"],
            "exit_time": candidate["exit_time"],
            "direction": candidate["direction"],
            "magic": candidate["magic"],
            "accepted": is_accepted,
            "decision_reason": reason,
            "balance_at_entry": round(balance, 4),
            "marked_equity_at_entry": round(equity, 4),
            "open_positions_before": len(open_rows),
            "trade_initial_risk_usd": round(candidate["initial_risk_usd"], 4),
            "trade_initial_risk_pct": round(trade_risk_pct, 6),
            "total_initial_risk_pct_after": round(total_risk_pct, 6),
            "same_direction_initial_risk_pct_after": round(same_risk_pct, 6),
            "margin_utilization_pct_after": round(margin_pct, 6),
            "daily_realized_loss_pct": round(daily_loss_pct, 6),
            "profit_usd_if_accepted": candidate["profit_usd"] if is_accepted else 0.0,
        }
        decisions.append(decision)
        if is_accepted:
            accepted.append(candidate)
            open_rows.append(candidate)
    close_until(datetime.max.replace(tzinfo=timezone.utc))
    return decisions, accepted


def _equity_replay(
    accepted: list[dict[str, Any]],
    bars: list[dict[str, Any]],
    *,
    initial_balance: float,
    contract_size: float,
    assumed_leverage: float,
    exit_cost: float,
) -> dict[str, Any]:
    events = []
    for row in accepted:
        events.append((row["entry_dt"], 1, "ENTRY", row))
        events.append((row["exit_dt"], 0, "EXIT", row))
    events.sort(key=lambda item: (item[0], item[1], item[3]["candidate_id"]))
    event_index = 0
    balance = initial_balance
    active: dict[str, dict[str, Any]] = {}
    peak = initial_balance
    max_dd = 0.0
    max_dd_pct = 0.0
    minimum_equity = initial_balance
    max_concurrent = 0
    max_long = 0
    max_short = 0
    max_open_risk = 0.0
    max_margin_pct = 0.0
    opposite_overlap_bars = 0
    daily: dict[str, dict[str, Any]] = {}

    def apply_until(timestamp: datetime) -> None:
        nonlocal event_index, balance, max_concurrent, max_long, max_short
        while event_index < len(events) and events[event_index][0] <= timestamp:
            _, _, kind, row = events[event_index]
            if kind == "EXIT":
                if row["candidate_id"] in active:
                    balance += row["profit_usd"] - exit_cost
                    active.pop(row["candidate_id"], None)
            else:
                active[row["candidate_id"]] = row
            event_index += 1
            longs = sum(1 for item in active.values() if item["direction"] == "LONG")
            shorts = len(active) - longs
            max_concurrent = max(max_concurrent, len(active))
            max_long = max(max_long, longs)
            max_short = max(max_short, shorts)

    def observe(value: float) -> None:
        nonlocal peak, max_dd, max_dd_pct, minimum_equity
        peak = max(peak, value)
        drawdown = peak - value
        max_dd = max(max_dd, drawdown)
        max_dd_pct = max(max_dd_pct, 100.0 * drawdown / peak if peak > 0.0 else math.inf)
        minimum_equity = min(minimum_equity, value)

    for bar in bars:
        apply_until(bar["start"])
        if active:
            low_equity = _equity_at_price(balance, active.values(), bar, contract_size, "low")
            high_equity = _equity_at_price(balance, active.values(), bar, contract_size, "high")
            observe(max(low_equity, high_equity))
            observe(min(low_equity, high_equity))
        else:
            observe(balance)
        apply_until(bar["end"])
        close_equity = _marked_equity(balance, list(active.values()), bar, contract_size)
        observe(close_equity)
        longs = sum(1 for item in active.values() if item["direction"] == "LONG")
        shorts = len(active) - longs
        if longs and shorts:
            opposite_overlap_bars += 1
        open_risk = sum(item["initial_risk_usd"] for item in active.values())
        margin = sum(item["notional_usd"] / assumed_leverage for item in active.values())
        max_open_risk = max(max_open_risk, open_risk)
        max_margin_pct = max(max_margin_pct, 100.0 * margin / max(close_equity, 0.01))
        day = bar["start"].date().isoformat()
        row = daily.setdefault(
            day,
            {
                "date": day,
                "equity_open": close_equity,
                "equity_high": close_equity,
                "equity_low": close_equity,
                "equity_close": close_equity,
                "balance_close": balance,
                "max_concurrent_positions": len(active),
            },
        )
        row["equity_high"] = max(row["equity_high"], close_equity)
        row["equity_low"] = min(row["equity_low"], close_equity)
        row["equity_close"] = close_equity
        row["balance_close"] = balance
        row["max_concurrent_positions"] = max(row["max_concurrent_positions"], len(active))
    apply_until(datetime.max.replace(tzinfo=timezone.utc))
    observe(balance)
    daily_rows = []
    for row in daily.values():
        daily_rows.append({key: round(value, 4) if isinstance(value, float) else value for key, value in row.items()})
    return {
        "final_stressed_balance_usd": round(balance, 2),
        "max_equity_drawdown_usd": round(max_dd, 2),
        "max_equity_drawdown_pct_of_peak": round(max_dd_pct, 4),
        "minimum_equity_usd": round(minimum_equity, 2),
        "max_concurrent_positions": max_concurrent,
        "max_concurrent_longs": max_long,
        "max_concurrent_shorts": max_short,
        "max_open_initial_risk_usd": round(max_open_risk, 2),
        "max_margin_utilization_pct": round(max_margin_pct, 4),
        "opposite_direction_overlap_bars": opposite_overlap_bars,
        "opposite_direction_overlap_hours": round(opposite_overlap_bars * 5.0 / 60.0, 2),
        "daily": daily_rows,
    }


def _profile_stats(
    accepted: list[dict[str, Any]],
    bars: list[dict[str, Any]],
    contract: dict[str, Any],
    equity: dict[str, Any],
) -> dict[str, Any]:
    market_days = sorted({_market_session_day(bar["start"]) for bar in bars})
    windows = {}
    for name, start_raw, end_raw in WINDOWS:
        start = _parse_time(start_raw)
        end = _parse_time(end_raw)
        rows = [row for row in accepted if start <= row["exit_dt"] <= end]
        days = [day for day in market_days if start.date().isoformat() <= day <= end.date().isoformat()]
        windows[name] = _closed_stats(rows, days, float(contract["stress_cost_per_trade_usd"]))
    blocks = _six_month_blocks(accepted, float(contract["stress_cost_per_trade_usd"]))
    nonnegative = sum(1 for row in blocks if row["stress_net_usd"] >= 0.0)
    return {
        "windows": windows,
        "six_month_blocks": blocks,
        "six_month_nonnegative_blocks": nonnegative,
        "six_month_total_blocks": len(blocks),
        "six_month_nonnegative_share": round(nonnegative / len(blocks), 6) if blocks else 0.0,
        "equity_daily_rows": len(equity["daily"]),
    }


def _closed_stats(rows: list[dict[str, Any]], market_days: list[str], cost: float) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: row["exit_dt"])
    raw = [row["profit_usd"] for row in ordered]
    stress = [value - cost for value in raw]
    gross_profit = sum(value for value in raw if value > 0.0)
    gross_loss = -sum(value for value in raw if value < 0.0)
    stress_gp = sum(value for value in stress if value > 0.0)
    stress_gl = -sum(value for value in stress if value < 0.0)
    by_day: dict[str, float] = defaultdict(float)
    by_week: dict[str, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    by_source: dict[str, float] = defaultdict(float)
    entries_by_day: dict[str, int] = defaultdict(int)
    for row, value in zip(ordered, stress):
        exit_day = _market_session_day(row["exit_dt"])
        exit_date = datetime.fromisoformat(exit_day).date()
        iso = exit_date.isocalendar()
        by_day[exit_day] += value
        by_week[f"{iso.year}-W{iso.week:02d}"] += value
        by_month[exit_day[:7]] += value
        by_source[row["source"]] += row["profit_usd"]
        entries_by_day[_market_session_day(row["entry_dt"])] += 1
    active_days = len(entries_by_day)
    positive_days = sum(1 for value in by_day.values() if value > 0.0)
    return {
        "trades": len(rows),
        "wins": sum(1 for value in raw if value > 0.0),
        "win_rate_pct": round(100.0 * sum(1 for value in raw if value > 0.0) / len(raw), 4) if raw else 0.0,
        "net_usd": round(sum(raw), 2),
        "stress_net_usd": round(sum(stress), 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "stress_profit_factor": round(stress_gp / stress_gl, 4) if stress_gl else None,
        "max_stressed_closed_drawdown_usd": round(_max_drawdown(stress), 2),
        "market_days": len(market_days),
        "active_entry_days": active_days,
        "trades_per_market_day": round(len(rows) / len(market_days), 6) if market_days else 0.0,
        "trades_per_active_day": round(len(rows) / active_days, 6) if active_days else 0.0,
        "positive_exit_days": positive_days,
        "positive_active_exit_day_pct": round(100.0 * positive_days / len(by_day), 4) if by_day else 0.0,
        "positive_market_day_pct": round(100.0 * positive_days / len(market_days), 4) if market_days else 0.0,
        "worst_day_usd": round(min(by_day.values()), 2) if by_day else 0.0,
        "worst_week_usd": round(min(by_week.values()), 2) if by_week else 0.0,
        "worst_month_usd": round(min(by_month.values()), 2) if by_month else 0.0,
        "pnl_by_source_usd": {key: round(value, 2) for key, value in sorted(by_source.items())},
    }


def _six_month_blocks(rows: list[dict[str, Any]], cost: float) -> list[dict[str, Any]]:
    output = []
    for year in range(2016, 2027):
        for half, start_month, end_month in (("H1", 1, 6), ("H2", 7, 12)):
            start = datetime(year, start_month, 1, tzinfo=timezone.utc)
            end = datetime(year + (1 if end_month == 12 else 0), 1 if end_month == 12 else end_month + 1, 1, tzinfo=timezone.utc)
            if start < datetime(2016, 7, 1, tzinfo=timezone.utc) or end > datetime(2026, 7, 1, tzinfo=timezone.utc):
                continue
            selected = [row for row in rows if start <= row["exit_dt"] < end]
            stress = sum(row["profit_usd"] - cost for row in selected)
            output.append({"block": f"{year}-{half}", "trades": len(selected), "stress_net_usd": round(stress, 2)})
    return output


def _calibrate_components(
    candidates: list[dict[str, Any]],
    audits: list[dict[str, Any]],
    bars: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    output = []
    for audit in audits:
        rows = [row for row in candidates if row["source"] == audit["source"]]
        replay = _equity_replay(
            rows,
            bars,
            initial_balance=float(contract["component_calibration_balance_usd"]),
            contract_size=float(contract["contract_size"]),
            assumed_leverage=float(contract["assumed_leverage"]),
            exit_cost=0.0,
        )
        exact = float(audit["mt5_equity_drawdown_usd"])
        estimated = float(replay["max_equity_drawdown_usd"])
        ratio = estimated / exact if exact > 0.0 else math.inf
        output.append(
            {
                "source": audit["source"],
                "mt5_equity_drawdown_usd": exact,
                "bar_replay_equity_drawdown_usd": estimated,
                "ratio": round(ratio, 6),
                "pass": float(contract["calibration_ratio_min"]) <= ratio <= float(contract["calibration_ratio_max"]),
            }
        )
    return output


def _magic_audit(audits: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = {audit["source"]: audit["magic_numbers"] for audit in audits}
    flattened = [magic for values in by_source.values() for magic in values]
    collisions = sorted({magic for magic in flattened if flattened.count(magic) > 1})
    return {"by_source": by_source, "collisions": collisions, "unique": not collisions}


def _risk_limits_respected(decisions: list[dict[str, Any]], contract: dict[str, Any]) -> bool:
    profile = next(row for row in contract["profiles"] if row["name"] == "risk_controlled_shared_account")
    accepted = [row for row in decisions if row["profile"] == profile["name"] and row["accepted"]]
    return all(
        row["open_positions_before"] < int(profile["max_concurrent_positions"])
        and row["trade_initial_risk_pct"] <= float(profile["max_trade_initial_risk_pct"]) + 1e-9
        and row["total_initial_risk_pct_after"] <= float(profile["max_total_initial_risk_pct"]) + 1e-9
        and row["same_direction_initial_risk_pct_after"] <= float(profile["max_same_direction_initial_risk_pct"]) + 1e-9
        and row["margin_utilization_pct_after"] <= float(profile["max_margin_utilization_pct"]) + 1e-9
        for row in accepted
    )


def _authorization_closed(contract: dict[str, Any]) -> bool:
    return bool(contract.get("research_only")) and all(
        contract.get(key) is False
        for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized")
    )


def _bar_at_or_before(timestamp: datetime, bars: list[dict[str, Any]], ends: list[datetime]) -> dict[str, Any]:
    index = bisect.bisect_right(ends, timestamp) - 1
    return bars[max(index, 0)]


def _marked_equity(
    balance: float, open_rows: list[dict[str, Any]], bar: dict[str, Any], contract_size: float
) -> float:
    equity = balance
    for row in open_rows:
        units = contract_size * row["volume"]
        if row["direction"] == "LONG":
            equity += (bar["bid_close"] - row["entry_price"]) * units
        else:
            equity += (row["entry_price"] - bar["ask_close"]) * units
    return equity


def _equity_at_price(
    balance: float,
    open_rows: Any,
    bar: dict[str, Any],
    contract_size: float,
    level: str,
) -> float:
    equity = balance
    for row in open_rows:
        units = contract_size * row["volume"]
        if row["direction"] == "LONG":
            equity += (bar[f"bid_{level}"] - row["entry_price"]) * units
        else:
            equity += (row["entry_price"] - bar[f"ask_{level}"]) * units
    return equity


def _max_drawdown(profits: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in profits:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def _market_session_day(value: datetime) -> str:
    # The UTC gold session opens late on the prior calendar date. A three-hour
    # shift groups Sunday evening with Monday and avoids counting it twice.
    return (value.astimezone(timezone.utc) + timedelta(hours=3)).date().isoformat()


def _counts(values: Any) -> dict[str, int]:
    output: dict[str, int] = defaultdict(int)
    for value in values:
        output[str(value)] += 1
    return dict(sorted(output.items()))


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _render(payload: dict[str, Any]) -> str:
    baseline = payload["profiles"]["unconstrained_shared_baseline"]
    controlled = payload["profiles"]["risk_controlled_shared_account"]
    baseline_ten_year = baseline["statistics"]["windows"]["last_10_years"]
    ten_year = controlled["statistics"]["windows"]["last_10_years"]
    equity = controlled["equity"]
    lines = [
        "# A3 ML Shared-Account Portfolio Replay",
        "",
        f"Status: `{payload['status']}`",
        "",
        "One-account historical research only. No demo or broker action is authorized.",
        "",
        "## Baseline Versus Risk Control",
        "",
        "| Profile | Accepted | Stress net USD | Stress PF | M5 equity DD USD | Max positions | Trades/market day |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Unconstrained | {baseline['accepted']} | {baseline_ten_year['stress_net_usd']:.2f} | "
        f"{baseline_ten_year['stress_profit_factor'] or 0.0:.4f} | {baseline['equity']['max_equity_drawdown_usd']:.2f} | "
        f"{baseline['equity']['max_concurrent_positions']} | {baseline_ten_year['trades_per_market_day']:.4f} |",
        f"| Risk controlled | {controlled['accepted']} | {ten_year['stress_net_usd']:.2f} | "
        f"{ten_year['stress_profit_factor'] or 0.0:.4f} | {equity['max_equity_drawdown_usd']:.2f} | "
        f"{equity['max_concurrent_positions']} | {ten_year['trades_per_market_day']:.4f} |",
        "",
        "## Risk-Controlled Result",
        "",
        f"- Accepted/rejected candidates: `{controlled['accepted']}/{controlled['rejected']}`",
        f"- Ten-year net/stress net: `${ten_year['net_usd']:.2f}` / `${ten_year['stress_net_usd']:.2f}`",
        f"- Ten-year PF/stress PF: `{ten_year['profit_factor']}` / `{ten_year['stress_profit_factor']}`",
        f"- Trades per market day: `{ten_year['trades_per_market_day']:.4f}`",
        f"- Trades per active day: `{ten_year['trades_per_active_day']:.4f}`",
        f"- Positive active exit days: `{ten_year['positive_active_exit_day_pct']:.2f}%`",
        f"- Shared M5 equity drawdown: `${equity['max_equity_drawdown_usd']:.2f}`",
        f"- Conservative drawdown: `${equity['conservative_drawdown_usd']:.2f}` (`{equity['conservative_drawdown_pct_of_initial']:.2f}%` of initial balance)",
        f"- Maximum concurrent positions: `{equity['max_concurrent_positions']}`",
        f"- Opposite-direction overlap: `{equity['opposite_direction_overlap_hours']:.2f}` hours",
        "",
        "## P/L Windows",
        "",
        "| Window | Trades | Net USD | Stress net USD | Stress PF | Trades/market day | Worst day USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, _, _ in WINDOWS:
        row = controlled["statistics"]["windows"][name]
        lines.append(
            f"| `{name}` | {row['trades']} | {row['net_usd']:.2f} | {row['stress_net_usd']:.2f} | "
            f"{row['stress_profit_factor'] or 0.0:.4f} | {row['trades_per_market_day']:.4f} | {row['worst_day_usd']:.2f} |"
        )
    lines.extend(["", "## Component Calibration", ""])
    for row in payload["component_calibration"]:
        lines.append(
            f"- `{row['source']}`: MT5 `${row['mt5_equity_drawdown_usd']:.2f}`, bar replay "
            f"`${row['bar_replay_equity_drawdown_usd']:.2f}`, ratio `{row['ratio']:.4f}`: "
            f"{'PASS' if row['pass'] else 'FAIL'}"
        )
    lines.extend(
        [
            "",
            "## Ownership Audit",
            "",
            f"- Magic numbers unique: `{'PASS' if payload['magic_audit']['unique'] else 'FAIL'}`",
            f"- Collisions: `{', '.join(payload['magic_audit']['collisions']) or 'none'}`",
            "",
            "## Capital Boundary",
            "",
            f"- Fixed-lot capital for 10% observed drawdown: `${payload['capital_required_for_fixed_lot_drawdown']['at_10pct_usd']:.2f}`",
            f"- Fixed-lot capital for 15% observed drawdown: `${payload['capital_required_for_fixed_lot_drawdown']['at_15pct_usd']:.2f}`",
            "",
            "## Gates",
            "",
        ]
    )
    for name, passed in payload["gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Frequency remains a measured research gap. No entries were created or loosened to reach the target.",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _result_path(root: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute() and path.exists():
        return path.resolve()
    return _resolve(root, path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_money(value: Any) -> float:
    match = re.search(r"[-+]?\d[\d ]*(?:\.\d+)?", str(value or ""))
    if not match:
        raise ValueError(f"cannot parse money value: {value!r}")
    return float(match.group(0).replace(" ", ""))


def _parse_time(value: str) -> datetime:
    text = str(value).strip()
    if "T" in text:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    return datetime.strptime(text, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc) if "." in text[:10] else datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
