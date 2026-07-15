from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ml.a3_meta_v1.dukascopy_microstructure_regime import _sha256_file


DEFAULT_CONTRACT = Path("config/ml/a3_ml_shared_account_portfolio_v1.json")


class SharedAccountPortfolioError(RuntimeError):
    pass


def run_shared_account_portfolio(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    report_path = (root / contract["source_report"]).resolve()
    trades_path = (root / contract["source_trades"]).resolve()
    if not report_path.is_file() or not trades_path.is_file():
        raise SharedAccountPortfolioError("exact MT5 portfolio inputs are missing")
    source_report = json.loads(report_path.read_text(encoding="utf-8"))
    trades = _read_trades(trades_path, contract)
    overlap = _overlap_metrics(trades)
    simulation = _simulate_controls(trades, contract)
    unguarded = _portfolio_metrics(trades, contract)
    guarded_trades = [row for row in trades if simulation["accepted"][row["trade_id"]]]
    guarded = _portfolio_metrics(guarded_trades, contract)

    component_drawdowns = [
        float(row.get("mt5_equity_drawdown_usd") or 0.0) for row in source_report.get("source_audits", [])
    ]
    measured_closed_dd = float(unguarded["maximum_closed_drawdown_usd"])
    max_component_dd = max(component_drawdowns, default=0.0)
    conservative_upper_dd = max(measured_closed_dd, sum(component_drawdowns))
    starting_equity = float(contract["scope"]["starting_equity_usd"])
    hard_pct = float(contract["gates"]["maximum_conservative_drawdown_pct"])
    minimum_equity = conservative_upper_dd / hard_pct if hard_pct > 0 else math.inf
    conservative_pct = conservative_upper_dd / starting_equity if starting_equity > 0 else math.inf
    gates = {
        "stress_profit_factor": float(unguarded["stress_profit_factor"] or 0.0)
        >= float(contract["gates"]["minimum_stress_profit_factor"]),
        "severe_cost_profit_factor": float(unguarded["severe_cost_profit_factor"] or 0.0)
        >= float(contract["gates"]["minimum_severe_cost_profit_factor"]),
        "minimum_frequency": float(unguarded["annualized_trades_per_trading_day"])
        >= float(contract["gates"]["minimum_trades_per_trading_day"]),
        "six_month_stability": float(unguarded["nonnegative_six_month_share"])
        >= float(contract["gates"]["minimum_nonnegative_six_month_share"]),
        "conservative_drawdown": conservative_pct <= hard_pct,
        "top10_winners_removed": (
            not contract["gates"]["require_top10_winners_removed_net_positive"]
            or float(unguarded["top10_winners_removed_stress_net_usd"]) > 0
        ),
        "untouched_holdout": not bool(contract["gates"]["require_untouched_holdout"]),
        "no_emergency_halt": simulation["emergency_halt_time_utc"] is None,
    }
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(outputs["events_csv"], simulation["event_rows"])
    _write_csv(outputs["daily_csv"], guarded["daily_rows"])
    payload = {
        "schema_version": contract["schema_version"],
        "portfolio_id": contract["portfolio_id"],
        "classification": "SHARED_ACCOUNT_RESEARCH_PASS" if all(gates.values()) else "SHARED_ACCOUNT_RESEARCH_FAIL",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "inputs": {
            "source_report": str(report_path),
            "source_report_sha256": _sha256_file(report_path),
            "source_trades": str(trades_path),
            "source_trades_sha256": _sha256_file(trades_path),
        },
        "overlap": overlap,
        "drawdown_boundary": {
            "measured_shared_closed_trade_drawdown_usd": measured_closed_dd,
            "largest_component_mt5_equity_drawdown_usd": max_component_dd,
            "sum_component_mt5_equity_drawdown_upper_bound_usd": conservative_upper_dd,
            "starting_equity_usd": starting_equity,
            "conservative_drawdown_pct_of_starting_equity": conservative_pct,
            "minimum_starting_equity_for_15pct_upper_bound_usd": minimum_equity,
            "exact_shared_mark_to_market_drawdown_available": False,
        },
        "unguarded": {key: value for key, value in unguarded.items() if key != "daily_rows"},
        "controlled": {
            **{key: value for key, value in guarded.items() if key != "daily_rows"},
            "accepted_trades": simulation["accepted_count"],
            "blocked_trades": simulation["blocked_count"],
            "blocked_reasons": simulation["blocked_reasons"],
            "emergency_halt_time_utc": simulation["emergency_halt_time_utc"],
        },
        "gates": gates,
        "limitations": [
            "The combined ledger measures drawdown only at closed-trade exits.",
            "Exact shared-account mark-to-market equity requires synchronized intratrade equity paths that the source ledgers do not contain.",
            "The sum of component MT5 equity drawdowns is a conservative upper boundary, not a measured simultaneous drawdown.",
            "All source history is development data and is not an untouched holdout.",
        ],
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key != "report_json" and path.exists()
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _read_trades(path: Path, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for index, raw in enumerate(csv.DictReader(handle), start=1):
            source = str(raw["source"])
            if source not in contract["allowed_sources"]:
                raise SharedAccountPortfolioError(f"unexpected source: {source}")
            row = {
                **raw,
                "trade_id": f"T{index:05d}",
                "entry_dt": _parse_broker(raw["entry_time"]),
                "exit_dt": _parse_broker(raw["exit_time"]),
                "volume": float(raw["volume"]),
                "profit_usd": float(raw["profit_usd"]),
                "stress_profit_usd": float(raw["stress_profit_usd"]),
            }
            if row["exit_dt"] < row["entry_dt"]:
                raise SharedAccountPortfolioError("trade exits before entry")
            rows.append(row)
    if not rows:
        raise SharedAccountPortfolioError("portfolio trade ledger is empty")
    return sorted(rows, key=lambda row: (row["entry_dt"], row["source"], row["trade_id"]))


def _overlap_metrics(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    active: list[Mapping[str, Any]] = []
    maximum = 0
    maximum_gross_lots = 0.0
    same_direction_entries = 0
    opposite_direction_entries = 0
    overlap_entries = 0
    for trade in trades:
        entry = trade["entry_dt"]
        active = [row for row in active if row["exit_dt"] > entry]
        if active:
            overlap_entries += 1
            if any(row["direction"] == trade["direction"] for row in active):
                same_direction_entries += 1
            if any(row["direction"] != trade["direction"] for row in active):
                opposite_direction_entries += 1
        active.append(trade)
        maximum = max(maximum, len(active))
        maximum_gross_lots = max(maximum_gross_lots, sum(float(row["volume"]) for row in active))
    return {
        "maximum_concurrent_trades": maximum,
        "maximum_gross_lots": round(maximum_gross_lots, 4),
        "entries_while_another_trade_open": overlap_entries,
        "same_direction_overlap_entries": same_direction_entries,
        "opposite_direction_overlap_entries": opposite_direction_entries,
    }


def _simulate_controls(trades: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]) -> dict[str, Any]:
    controls = contract["controls"]
    equity = float(contract["scope"]["starting_equity_usd"])
    peak = equity
    day_start_equity = equity
    current_day = None
    daily_realized = 0.0
    active: dict[str, Mapping[str, Any]] = {}
    accepted = {row["trade_id"]: False for row in trades}
    blocked_reasons = Counter()
    event_rows = []
    emergency_halt = None
    events = []
    for row in trades:
        events.append((row["entry_dt"], 1, row["trade_id"], "ENTRY", row))
        events.append((row["exit_dt"], 0, row["trade_id"], "EXIT", row))
    events.sort(key=lambda item: (item[0], item[1], item[2]))
    for when, _, trade_id, event, trade in events:
        date = when.date()
        if date != current_day:
            current_day = date
            day_start_equity = equity
            daily_realized = 0.0
        if event == "EXIT":
            if accepted[trade_id]:
                active.pop(trade_id, None)
                pnl = float(trade["stress_profit_usd"])
                equity += pnl
                daily_realized += pnl
                peak = max(peak, equity)
                drawdown_pct = (peak - equity) / peak if peak > 0 else math.inf
                if drawdown_pct >= float(controls["emergency_closed_drawdown_pct"]) and emergency_halt is None:
                    emergency_halt = when
                event_rows.append(_event_row(when, event, trade, "ACCEPTED_EXIT", equity, active))
            continue
        reason = None
        if emergency_halt is not None:
            reason = "EMERGENCY_DRAWDOWN_HALT"
        elif daily_realized <= -float(controls["daily_realized_loss_limit_pct"]) * day_start_equity:
            reason = "DAILY_REALIZED_LOSS_LIMIT"
        elif len(active) >= int(controls["maximum_concurrent_trades"]):
            reason = "MAXIMUM_CONCURRENT_TRADES"
        elif sum(float(row["volume"]) for row in active.values()) + float(trade["volume"]) > float(
            controls["maximum_gross_lots"]
        ) + 1e-12:
            reason = "MAXIMUM_GROSS_LOTS"
        elif sum(
            float(row["volume"]) for row in active.values() if row["direction"] == trade["direction"]
        ) + float(trade["volume"]) > float(controls["maximum_directional_lots"]) + 1e-12:
            reason = "MAXIMUM_DIRECTIONAL_LOTS"
        if reason:
            blocked_reasons[reason] += 1
            event_rows.append(_event_row(when, event, trade, reason, equity, active))
        else:
            accepted[trade_id] = True
            active[trade_id] = trade
            event_rows.append(_event_row(when, event, trade, "ACCEPTED_ENTRY", equity, active))
    return {
        "accepted": accepted,
        "accepted_count": sum(accepted.values()),
        "blocked_count": len(trades) - sum(accepted.values()),
        "blocked_reasons": dict(blocked_reasons),
        "emergency_halt_time_utc": _iso(emergency_halt) if emergency_halt else None,
        "event_rows": event_rows,
    }


def _event_row(
    when: datetime,
    event: str,
    trade: Mapping[str, Any],
    decision: str,
    equity: float,
    active: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "time_utc": _iso(when),
        "event": event,
        "trade_id": trade["trade_id"],
        "source": trade["source"],
        "direction": trade["direction"],
        "decision": decision,
        "equity_usd": round(equity, 2),
        "active_trades": len(active),
        "active_gross_lots": round(sum(float(row["volume"]) for row in active.values()), 4),
    }


def _portfolio_metrics(trades: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda row: (row["exit_dt"], row["trade_id"]))
    baseline = np.asarray([float(row["profit_usd"]) for row in ordered], dtype=float)
    stress = np.asarray([float(row["stress_profit_usd"]) for row in ordered], dtype=float)
    severe_cost = float(contract["scope"]["severe_cost_per_trade_usd"])
    severe = baseline - severe_cost
    daily = defaultdict(lambda: {"trades": 0, "stress_pnl_usd": 0.0})
    by_source = defaultdict(float)
    for row, pnl in zip(ordered, stress):
        key = row["exit_dt"].date().isoformat()
        daily[key]["trades"] += 1
        daily[key]["stress_pnl_usd"] += float(pnl)
        by_source[row["source"]] += float(pnl)
    daily_rows = [
        {"date": date, "trades": values["trades"], "stress_pnl_usd": round(values["stress_pnl_usd"], 2)}
        for date, values in sorted(daily.items())
    ]
    start = _parse_iso(contract["scope"]["start_utc"])
    end = _parse_iso(contract["scope"]["end_exclusive_utc"])
    years = (end - start).total_seconds() / (365.2425 * 86_400)
    annualized_tpd = len(ordered) / years / 252.0 if years else 0.0
    six_month = _six_month_blocks(ordered, start, end)
    winners = sorted((float(value) for value in stress if value > 0), reverse=True)
    active_positive = sum(row["stress_pnl_usd"] > 0 for row in daily_rows)
    return {
        "trades": len(ordered),
        "baseline_net_usd": round(float(baseline.sum()), 2),
        "stress_net_usd": round(float(stress.sum()), 2),
        "severe_cost_net_usd": round(float(severe.sum()), 2),
        "stress_profit_factor": _profit_factor(stress),
        "severe_cost_profit_factor": _profit_factor(severe),
        "maximum_closed_drawdown_usd": round(_max_drawdown(stress), 2),
        "annualized_trades_per_trading_day": annualized_tpd,
        "active_days": len(daily_rows),
        "positive_active_day_share": active_positive / len(daily_rows) if daily_rows else 0.0,
        "worst_day_usd": min((row["stress_pnl_usd"] for row in daily_rows), default=0.0),
        "best_day_usd": max((row["stress_pnl_usd"] for row in daily_rows), default=0.0),
        "nonnegative_six_month_blocks": sum(row["stress_net_usd"] >= 0 for row in six_month),
        "six_month_blocks": len(six_month),
        "nonnegative_six_month_share": (
            sum(row["stress_net_usd"] >= 0 for row in six_month) / len(six_month) if six_month else 0.0
        ),
        "top10_winners_removed_stress_net_usd": round(float(stress.sum()) - sum(winners[:10]), 2),
        "stress_pnl_by_source_usd": {key: round(value, 2) for key, value in sorted(by_source.items())},
        "daily_rows": daily_rows,
    }


def _six_month_blocks(
    trades: Sequence[Mapping[str, Any]], start: datetime, end: datetime
) -> list[dict[str, Any]]:
    rows = []
    cursor = datetime(start.year, 1 if start.month <= 6 else 7, 1, tzinfo=UTC)
    if cursor < start:
        cursor = datetime(start.year, 7, 1, tzinfo=UTC)
    while cursor < end:
        next_cursor = (
            datetime(cursor.year + 1, 1, 1, tzinfo=UTC)
            if cursor.month == 7
            else datetime(cursor.year, 7, 1, tzinfo=UTC)
        )
        if next_cursor > end:
            break
        selected = [row for row in trades if cursor <= row["exit_dt"] < next_cursor]
        rows.append(
            {
                "start_utc": _iso(cursor),
                "end_exclusive_utc": _iso(next_cursor),
                "trades": len(selected),
                "stress_net_usd": round(sum(float(row["stress_profit_usd"]) for row in selected), 2),
            }
        )
        cursor = next_cursor
    return rows


def _profit_factor(values: np.ndarray) -> float | None:
    wins = float(values[values > 0].sum())
    losses = -float(values[values < 0].sum())
    return wins / losses if losses > 0 else None


def _max_drawdown(values: np.ndarray) -> float:
    if not len(values):
        return 0.0
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    return float((peaks[1:] - equity).max())


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    rows = list(rows)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            return
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _render(payload: Mapping[str, Any]) -> str:
    raw = payload["unguarded"]
    dd = payload["drawdown_boundary"]
    controlled = payload["controlled"]
    lines = [
        "# A3 ML Shared-Account Portfolio V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Unguarded: {raw['trades']} trades, {raw['annualized_trades_per_trading_day']:.3f}/trading day, stress PF {float(raw['stress_profit_factor'] or 0):.3f}, stress net ${raw['stress_net_usd']:.2f}.",
        f"Measured closed-trade drawdown: ${dd['measured_shared_closed_trade_drawdown_usd']:.2f}.",
        f"Conservative component-sum upper boundary: ${dd['sum_component_mt5_equity_drawdown_upper_bound_usd']:.2f}.",
        f"Minimum starting equity for that boundary to equal 15%: ${dd['minimum_starting_equity_for_15pct_upper_bound_usd']:.2f}.",
        f"$1,000 control simulation: {controlled['accepted_trades']} accepted, {controlled['blocked_trades']} blocked, emergency halt `{controlled['emergency_halt_time_utc']}`.",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- `{key}`: {'PASS' if value else 'FAIL'}" for key, value in payload["gates"].items())
    lines.extend(["", "Exact shared mark-to-market equity drawdown is unavailable from closed-trade ledgers. No demo or live action is authorized.", ""])
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_shared_account_portfolio_v1":
        raise SharedAccountPortfolioError("unexpected shared-account contract")
    if contract.get("scope", {}).get("fixed_lot_size") != 0.01:
        raise SharedAccountPortfolioError("fixed lot size changed")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only"):
        raise SharedAccountPortfolioError("portfolio must remain research only")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if authorization.get(key):
            raise SharedAccountPortfolioError(f"{key} must remain false")


def _parse_broker(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S").replace(tzinfo=UTC)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
