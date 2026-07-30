from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import forward_combined_frequency_portfolio as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "frozen_forward_live_combined_portfolio_v3.json"
LOCK_PATH = (
    ROOT / "EURUSD_FORWARD_LIVE_COMBINED_PORTFOLIO_V3_LOCK_2026_07_30.sha256.json"
)
PUBLISHER_TERMINAL_STATUSES = {
    "PUBLISHED_SIGNAL",
    "PUBLISHED_CASH",
    "CASH_UPSTREAM_OWNED",
    "CASH_MISSING_CONTEXT",
    "CASH_MISSED_PUBLICATION_DEADLINE",
}
OUTCOME_TERMINAL_STATUSES = {
    "RESOLVED",
    "CASH_MARKET_CLOSURE",
    "CASH_NO_SHADOW_ENTRY",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_forward_floor": True,
        "locked_with_zero_forward_feature_rows": True,
        "locked_with_zero_live_component_outcomes": True,
        "locked_with_zero_portfolio_decisions": True,
        "historical_backtest_allowed": False,
        "demo_order_authorized": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("live-combined lock boundary is incomplete")
    for relative, expected in lock["files"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"live-combined implementation drift: {relative}")
    return lock


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = base.load_config(path)
    if config.get("campaign_id") != "EURUSD_FORWARD_LIVE_COMBINED_PORTFOLIO_V3":
        raise ValueError("unexpected live-combined campaign")
    if config.get("historical_backtest_allowed") is not False:
        raise ValueError("live-combined config permits historical input")
    if config.get("demo_order_authorized"):
        raise ValueError("live-combined config unexpectedly authorizes orders")
    if config["excluded_components"]["DAILY_CROSSPAIR"]["may_participate"]:
        raise ValueError("rejected daily learner may not enter the live portfolio")
    return config


def validate_signal_ledger(
    signals: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    campaign = config["components"]["RESIDUAL_LIVE"]["publisher_campaign_id"]
    floor = base.parse_time(str(config["forward_floor_utc"]))
    previous_date = ""
    seen_ids: set[str] = set()
    seen_dates: set[str] = set()
    for signal in signals:
        if signal.get("campaign_id") != campaign:
            raise ValueError("residual live signal campaign mismatch")
        decision_id = str(signal.get("decision_id", ""))
        day_text = str(signal.get("decision_date", ""))
        if not decision_id or decision_id in seen_ids:
            raise ValueError("missing or duplicate residual live decision id")
        if not day_text or day_text in seen_dates or day_text < previous_date:
            raise ValueError("residual live decision dates are duplicate or unordered")
        if signal.get("status") not in PUBLISHER_TERMINAL_STATUSES:
            raise ValueError("residual live signal has a nonterminal status")
        decision_time = base.parse_time(str(signal["decision_time_utc"]))
        if decision_time < floor or decision_time.date().isoformat() != day_text:
            raise ValueError("residual live signal violates the forward boundary")
        if signal.get("demo_order_authorized") is not False:
            raise ValueError("residual live signal contains order authorization")
        seen_ids.add(decision_id)
        seen_dates.add(day_text)
        previous_date = day_text


def validate_parity_ledger(
    parity_rows: list[dict[str, Any]],
    signal_ids: set[str],
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    campaign = config["components"]["RESIDUAL_LIVE"]["campaign_id"]
    by_id: dict[str, dict[str, Any]] = {}
    for row in parity_rows:
        if row.get("campaign_id") != campaign:
            raise ValueError("residual selection parity campaign mismatch")
        decision_id = str(row.get("decision_id", ""))
        if not decision_id or decision_id in by_id:
            raise ValueError("missing or duplicate selection parity decision id")
        if decision_id not in signal_ids:
            raise ValueError("selection parity has no published decision")
        if row.get("demo_order_authorized") is not False:
            raise ValueError("selection parity contains order authorization")
        by_id[decision_id] = row
    return by_id


def validate_outcome_ledger(
    outcomes: list[dict[str, Any]],
    signals_by_id: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    campaign = config["components"]["RESIDUAL_LIVE"]["campaign_id"]
    by_id: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        if outcome.get("campaign_id") != campaign:
            raise ValueError("residual live outcome campaign mismatch")
        decision_id = str(outcome.get("decision_id", ""))
        if not decision_id or decision_id in by_id:
            raise ValueError("missing or duplicate residual live outcome decision id")
        signal = signals_by_id.get(decision_id)
        if signal is None:
            raise ValueError("residual live outcome has no published decision")
        status = str(outcome.get("status", ""))
        if status not in OUTCOME_TERMINAL_STATUSES and not status.startswith(
            "INVALID_"
        ):
            raise ValueError(f"residual live outcome is not terminal: {status}")
        if outcome.get("decision_date") != signal.get("decision_date"):
            raise ValueError("residual live outcome date differs from signal")
        if outcome.get("eligible_side") != signal.get("eligible_side"):
            raise ValueError("residual live outcome side differs from signal")
        if outcome.get("demo_order_authorized") is not False:
            raise ValueError("residual live outcome contains order authorization")
        by_id[decision_id] = outcome
    return by_id


def validate_residual_summary_counts(
    signals: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    parity_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    resolved = sum(item.get("status") == "RESOLVED" for item in outcomes)
    invalid = sum(
        str(item.get("status", "")).startswith("INVALID_") for item in outcomes
    )
    mismatches = sum(item.get("parity_pass") is not True for item in parity_rows)
    expected = {
        "published_decisions": len(signals),
        "terminal_outcomes": len(outcomes),
        "resolved_live_outcomes": resolved,
        "invalid_outcomes": invalid,
        "selection_parity_rows": len(parity_rows),
        "selection_mismatches": mismatches,
        "pending_selection_parity": len(signals) - len(parity_rows),
        "order_api_calls": 0,
        "position_mutation_attempts": 0,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            raise ValueError(
                f"residual live summary mismatch: {field} "
                f"expected={value} actual={summary.get(field)}"
            )
    if summary.get("demo_order_authorized") is not False:
        raise ValueError("residual live summary contains order authorization")


def validation_start_time(
    signals: list[dict[str, Any]],
    config: dict[str, Any],
) -> datetime | None:
    warmup = int(
        config["components"]["RESIDUAL_LIVE"]["warmup_resolved_residual_days"]
    )
    candidates = [
        base.parse_time(str(signal["decision_time_utc"]))
        for signal in signals
        if signal.get("status") in ("PUBLISHED_SIGNAL", "PUBLISHED_CASH")
        and isinstance(signal.get("training_days_before"), int)
        and int(signal["training_days_before"]) >= warmup
    ]
    return min(candidates) if candidates else None


def m15_pending_cutoff(m15_summary: dict[str, Any]) -> datetime | None:
    pending = int(m15_summary.get("pending_signals", 0))
    cutoff = m15_summary.get("earliest_pending_signal_entry_time_utc")
    if pending and not cutoff:
        raise ValueError("M15 pending signals lack a causal cutoff timestamp")
    return base.parse_time(str(cutoff)) if pending else None


def finalized_validation_days(
    complete_days: list[date],
    signals_by_date: dict[str, dict[str, Any]],
    outcomes_by_id: dict[str, dict[str, Any]],
    parity_by_id: dict[str, dict[str, Any]],
    cutoff: datetime | None,
) -> list[date]:
    result: list[date] = []
    for day in complete_days:
        if cutoff is not None and day >= cutoff.date():
            break
        signal = signals_by_date.get(day.isoformat())
        if signal is None:
            break
        decision_id = str(signal["decision_id"])
        if decision_id not in parity_by_id:
            break
        if signal["status"] == "PUBLISHED_SIGNAL":
            outcome = outcomes_by_id.get(decision_id)
            if outcome is None:
                break
        result.append(day)
    return result


def normalize_residual_live_outcomes(
    outcomes: list[dict[str, Any]],
    signals_by_id: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> list[base.Trade]:
    component = config["components"]["RESIDUAL_LIVE"]
    floor = base.parse_time(str(config["forward_floor_utc"]))
    fixed_lots = float(component["fixed_lots"])
    stop_pips = float(component["fixed_stop_pips"])
    pip_value = float(component["pip_value_usd_per_standard_lot"])
    stress_pips = float(component["additional_round_trip_stress_pips"])
    risk_usd = fixed_lots * stop_pips * pip_value
    trades: list[base.Trade] = []
    seen: set[str] = set()
    for outcome in outcomes:
        if outcome.get("status") != "RESOLVED":
            continue
        decision_id = str(outcome["decision_id"])
        if decision_id in seen:
            raise ValueError(f"duplicate resolved residual live outcome: {decision_id}")
        seen.add(decision_id)
        signal = signals_by_id[decision_id]
        if signal.get("status") != "PUBLISHED_SIGNAL":
            raise ValueError("resolved residual outcome lacks a published signal")
        side = str(outcome.get("eligible_side", ""))
        if side not in ("LONG", "SHORT") or side != signal.get("eligible_side"):
            raise ValueError("resolved residual outcome side is invalid")
        if outcome.get("regime") != signal.get("regime"):
            raise ValueError("resolved residual outcome regime differs from signal")
        entry_time = base.parse_time(str(outcome["entry_time_utc"]))
        exit_time = base.parse_time(str(outcome["exit_time_utc"]))
        if entry_time < floor or exit_time < entry_time:
            raise ValueError("residual live outcome has invalid time geometry")
        lots = float(outcome["lots"])
        if not math.isclose(lots, fixed_lots, abs_tol=1e-12):
            raise ValueError("residual live outcome changed frozen lot size")
        result_pips = float(outcome["result_pips"])
        expected_pnl = result_pips * pip_value * lots
        expected_stressed = (result_pips - stress_pips) * pip_value * lots
        if not math.isclose(
            float(outcome["pnl_usd"]), expected_pnl, abs_tol=1e-9
        ):
            raise ValueError("residual live outcome P&L is inconsistent")
        if not math.isclose(
            float(outcome["stressed_pnl_usd"]),
            expected_stressed,
            abs_tol=1e-9,
        ):
            raise ValueError("residual live stressed P&L is inconsistent")
        if (
            int(outcome.get("entry_tick_match_count", 0)) != 1
            or int(outcome.get("raw_tick_count", 0)) <= 0
            or not outcome.get("raw_tick_sha256")
            or not outcome.get("raw_tick_file")
        ):
            raise ValueError("residual live outcome lacks unique raw-tick proof")
        trades.append(
            base.Trade(
                trade_id=f"RESIDUAL_LIVE:{decision_id}",
                component="RESIDUAL_LIVE",
                source="RESIDUAL_LIVE",
                entry_time=entry_time,
                exit_time=exit_time,
                initial_risk_usd=risk_usd,
                pnl_usd=expected_pnl,
                stressed_pnl_usd=expected_stressed,
            )
        )
    return trades


def apply_causal_risk(
    trades: list[base.Trade],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    risk = config["causal_portfolio_risk"]
    priority = {
        source: index for index, source in enumerate(risk["same_timestamp_priority"])
    }
    if set(priority) != {"M15_CHOP", "M15_COMPRESSION", "RESIDUAL_LIVE"}:
        raise ValueError("live-combined risk priority differs from frozen sources")
    maximum_positions = int(risk["maximum_concurrent_positions"])
    maximum_risk = float(risk["maximum_concurrent_initial_risk_usd"])
    ordered = sorted(
        trades,
        key=lambda trade: (
            trade.entry_time,
            priority[trade.source],
            trade.trade_id,
        ),
    )
    active: list[base.Trade] = []
    ledger: list[dict[str, Any]] = []
    for trade in ordered:
        active = [item for item in active if item.exit_time > trade.entry_time]
        risk_before = sum(item.initial_risk_usd for item in active)
        if len(active) >= maximum_positions:
            accepted = False
            decision = "REJECT_MAXIMUM_CONCURRENT_POSITIONS"
        elif risk_before + trade.initial_risk_usd > maximum_risk + 1e-12:
            accepted = False
            decision = "REJECT_MAXIMUM_CONCURRENT_INITIAL_RISK"
        else:
            accepted = True
            decision = "ACCEPT"
        row = {
            **asdict(trade),
            "entry_time_utc": trade.entry_time.isoformat(),
            "exit_time_utc": trade.exit_time.isoformat(),
            "accepted": accepted,
            "risk_decision": decision,
            "open_positions_before": len(active),
            "open_initial_risk_usd_before": risk_before,
            "open_initial_risk_usd_after": (
                risk_before + trade.initial_risk_usd if accepted else risk_before
            ),
        }
        row.pop("entry_time")
        row.pop("exit_time")
        ledger.append(row)
        if accepted:
            active.append(trade)
    return ledger


def _m15_economic(summary: dict[str, Any], config: dict[str, Any]) -> bool:
    admission = summary.get("admission", {})
    checks = admission.get("checks", {})
    automated = [
        bool(value)
        for name, value in checks.items()
        if name not in ("mt5_signal_parity", "shadow_soak")
    ]
    allowed = set(config["components"]["M15_REGIME"]["required_economic_statuses"])
    return (
        bool(automated)
        and all(automated)
        and admission.get("status") in allowed
    )


def _residual_live_economic(
    summary: dict[str, Any],
    config: dict[str, Any],
) -> bool:
    checks = summary.get("checks", {})
    automated = [
        bool(value)
        for name, value in checks.items()
        if name not in ("mt5_ordering_parity", "shadow_demo_soak")
    ]
    allowed = set(
        config["components"]["RESIDUAL_LIVE"]["required_economic_statuses"]
    )
    return (
        bool(automated)
        and all(automated)
        and summary.get("status") in allowed
    )


def admission_metrics(
    ledger: list[dict[str, Any]],
    validation_days: list[date],
    m15_summary: dict[str, Any],
    residual_summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    accepted = [row for row in ledger if row["accepted"]]
    rejected = [row for row in ledger if not row["accepted"]]
    values = [float(row["pnl_usd"]) for row in accepted]
    stressed = [float(row["stressed_pnl_usd"]) for row in accepted]
    complete_days = len(validation_days)
    frequency = len(accepted) / complete_days if complete_days else 0.0
    coverage = (
        len({base.parse_time(row["entry_time_utc"]).date() for row in accepted})
        / complete_days
        if complete_days
        else 0.0
    )
    win_rate = sum(value > 0.0 for value in values) / len(values) if values else 0.0
    payoff = base.payoff_ratio(values)
    rejection_share = len(rejected) / len(ledger) if ledger else 0.0
    components = ("M15_REGIME", "RESIDUAL_LIVE")
    component_values = {
        name: [
            float(row["pnl_usd"])
            for row in accepted
            if row["component"] == name
        ]
        for name in components
    }
    component_pfs = {
        name: base.profit_factor(items)
        for name, items in component_values.items()
    }
    m15_checks = m15_summary.get("admission", {}).get("checks", {})
    residual_checks = residual_summary.get("checks", {})
    gates = config["final_admission"]
    half_pfs = base._sequence_half_pfs(accepted)
    invalid_total = int(m15_summary.get("admission", {}).get("invalid_outcomes", 0))
    invalid_total += int(residual_summary.get("invalid_outcomes", 0))
    selection_mismatches = int(residual_summary.get("selection_mismatches", 0))
    checks = {
        "minimum_complete_validation_weekdays": complete_days
        >= int(gates["minimum_complete_validation_weekdays"]),
        "minimum_combined_trades": len(accepted)
        >= int(gates["minimum_combined_trades"]),
        "minimum_residual_component_trades": len(
            component_values["RESIDUAL_LIVE"]
        )
        >= int(gates["minimum_residual_component_trades"]),
        "minimum_trades_per_complete_weekday": frequency
        >= float(gates["minimum_trades_per_complete_weekday"]),
        "maximum_trades_per_complete_weekday": frequency
        <= float(gates["maximum_trades_per_complete_weekday"]),
        "minimum_weekday_trade_coverage": coverage
        >= float(gates["minimum_weekday_trade_coverage"]),
        "minimum_win_rate": win_rate >= float(gates["minimum_win_rate"]),
        "maximum_win_rate": win_rate <= float(gates["maximum_win_rate"]),
        "minimum_payoff_ratio": payoff is not None
        and payoff >= float(gates["minimum_payoff_ratio"]),
        "minimum_combined_profit_factor": base.profit_factor(values)
        >= float(gates["minimum_combined_profit_factor"]),
        "minimum_combined_stressed_profit_factor": base.profit_factor(stressed)
        >= float(gates["minimum_combined_stressed_profit_factor"]),
        "minimum_best_5pct_removed_profit_factor": base._best_removed_pf(values)
        >= float(gates["minimum_best_5pct_removed_profit_factor"]),
        "minimum_each_trade_sequence_half_profit_factor": all(
            value
            > float(
                gates[
                    "minimum_each_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in half_pfs
        ),
        "minimum_net_pnl_usd": sum(values)
        > float(gates["minimum_net_pnl_usd_exclusive"]),
        "maximum_closed_trade_drawdown_usd": (
            base.maximum_closed_trade_drawdown(accepted)
            <= float(gates["maximum_closed_trade_drawdown_usd"])
        ),
        "maximum_single_month_gross_profit_share": (
            base._maximum_month_gross_share(accepted)
            <= float(gates["maximum_single_month_gross_profit_share"])
        ),
        "minimum_m15_component_profit_factor": (
            component_pfs["M15_REGIME"]
            >= float(gates["minimum_m15_component_profit_factor"])
        ),
        "minimum_residual_component_profit_factor": (
            component_pfs["RESIDUAL_LIVE"]
            >= float(gates["minimum_residual_component_profit_factor"])
        ),
        "maximum_risk_cap_rejection_share": rejection_share
        <= float(
            config["causal_portfolio_risk"]["maximum_risk_cap_rejection_share"]
        ),
        "zero_invalid_component_outcomes": invalid_total == 0,
        "zero_residual_selection_mismatches": selection_mismatches == 0,
        "component_economic_admissions": (
            _m15_economic(m15_summary, config)
            and _residual_live_economic(residual_summary, config)
        ),
        "all_component_mt5_parity": bool(
            m15_checks.get("mt5_signal_parity", False)
        )
        and bool(residual_checks.get("mt5_ordering_parity", False)),
        "all_component_shadow_soak": bool(m15_checks.get("shadow_soak", False))
        and bool(residual_checks.get("shadow_demo_soak", False)),
        "combined_mt5_ordering_parity": False,
        "combined_demo_soak": False,
    }
    external = {
        "all_component_mt5_parity",
        "all_component_shadow_soak",
        "combined_mt5_ordering_parity",
        "combined_demo_soak",
    }
    automated = [name for name in checks if name not in external]
    enough_evidence = (
        checks["minimum_complete_validation_weekdays"]
        and checks["minimum_combined_trades"]
        and checks["minimum_residual_component_trades"]
    )
    if not enough_evidence:
        status = "WAITING_MINIMUM_LIVE_EVIDENCE"
    elif not all(checks[name] for name in automated):
        status = "REJECTED_LIVE_PORTFOLIO"
    elif not all(checks[name] for name in external):
        status = "WAITING_EXTERNAL_PARITY_AND_SOAK"
    else:
        status = "READY_FOR_GUARDED_DEMO_IMPLEMENTATION"
    return {
        "status": status,
        "complete_validation_weekdays": complete_days,
        "combined_trades": len(accepted),
        "risk_cap_rejections": len(rejected),
        "risk_cap_rejection_share": rejection_share,
        "trades_per_complete_weekday": frequency,
        "weekday_trade_coverage": coverage,
        "win_rate": win_rate,
        "payoff_ratio": payoff,
        "profit_factor": base.profit_factor(values),
        "stressed_profit_factor": base.profit_factor(stressed),
        "best_5pct_removed_profit_factor": base._best_removed_pf(values),
        "trade_sequence_half_profit_factors": half_pfs,
        "net_pnl_usd": sum(values),
        "maximum_closed_trade_drawdown_usd": (
            base.maximum_closed_trade_drawdown(accepted)
        ),
        "maximum_single_month_gross_profit_share": (
            base._maximum_month_gross_share(accepted)
        ),
        "component_trade_counts": {
            name: len(items) for name, items in component_values.items()
        },
        "component_profit_factors": component_pfs,
        "invalid_component_outcomes": invalid_total,
        "residual_selection_mismatches": selection_mismatches,
        "excluded_daily_component": True,
        "checks": checks,
        "demo_order_authorized": False,
    }


def process(
    m15_records: list[dict[str, Any]],
    m15_summary: dict[str, Any],
    live_signals: list[dict[str, Any]],
    live_outcomes: list[dict[str, Any]],
    selection_parity: list[dict[str, Any]],
    residual_summary: dict[str, Any],
    feature_csv: Path,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if int(m15_summary.get("terminal_outcomes", -1)) != len(m15_records):
        raise ValueError("M15 summary/outcome count mismatch")
    if int(residual_summary.get("terminal_outcomes", -1)) != len(live_outcomes):
        raise ValueError("residual live summary/outcome count mismatch")
    if int(residual_summary.get("selection_parity_rows", -1)) != len(
        selection_parity
    ):
        raise ValueError("residual live summary/parity count mismatch")
    validate_signal_ledger(live_signals, config)
    signals_by_id = {
        str(signal["decision_id"]): signal for signal in live_signals
    }
    signals_by_date = {
        str(signal["decision_date"]): signal for signal in live_signals
    }
    parity_by_id = validate_parity_ledger(
        selection_parity,
        set(signals_by_id),
        config,
    )
    outcomes_by_id = validate_outcome_ledger(
        live_outcomes,
        signals_by_id,
        config,
    )
    validate_residual_summary_counts(
        live_signals,
        live_outcomes,
        selection_parity,
        residual_summary,
    )
    start_time = validation_start_time(live_signals, config)
    complete_days = base.load_complete_weekdays(feature_csv, config, start_time)
    cutoff = m15_pending_cutoff(m15_summary)
    final_days = finalized_validation_days(
        complete_days,
        signals_by_date,
        outcomes_by_id,
        parity_by_id,
        cutoff,
    )
    final_day_set = set(final_days)
    m15_trades = base.normalize_m15_outcomes(m15_records, config)
    residual_trades = normalize_residual_live_outcomes(
        live_outcomes,
        signals_by_id,
        config,
    )
    trades = [
        trade
        for trade in m15_trades + residual_trades
        if start_time is not None
        and trade.entry_time >= start_time
        and trade.entry_time.date() in final_day_set
    ]
    ledger = apply_causal_risk(trades, config)
    admission = admission_metrics(
        ledger,
        final_days,
        m15_summary,
        residual_summary,
        config,
    )
    summary = {
        "schema_version": config["schema_version"],
        "campaign_id": config["campaign_id"],
        "validation_start_time_utc": (
            start_time.isoformat() if start_time else None
        ),
        "raw_complete_validation_weekdays": len(complete_days),
        "complete_validation_weekdays": len(final_days),
        "complete_validation_dates": [day.isoformat() for day in final_days],
        "pending_causal_cutoff_utc": cutoff.isoformat() if cutoff else None,
        "causally_unfinalized_complete_weekdays": (
            len(complete_days) - len(final_days)
        ),
        "published_residual_decisions": len(live_signals),
        "residual_selection_parity_rows": len(selection_parity),
        "normalized_m15_trades": len(m15_trades),
        "normalized_residual_live_trades": len(residual_trades),
        "portfolio_decisions": len(ledger),
        "research_residual_outcomes_consumed": 0,
        "daily_learner_trades_consumed": 0,
        "admission": admission,
        "demo_order_authorized": False,
    }
    return ledger, summary


def validate_append_only(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> None:
    safe = base.json_safe(new)
    if len(safe) < len(existing):
        raise ValueError("live-combined portfolio ledger shrank")
    for index, prior in enumerate(existing):
        if prior != safe[index]:
            raise ValueError(
                "live-combined portfolio mutation refused "
                f"at index={index} trade_id={prior.get('trade_id')}"
            )


def write_outputs(
    ledger: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
    *,
    enforce_append_only: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "FORWARD_LIVE_PORTFOLIO_LEDGER.json"
    if enforce_append_only and ledger_path.is_file():
        existing = base.load_records(ledger_path)
        validate_append_only(existing, ledger)
    base.atomic_write(
        ledger_path,
        json.dumps(base.json_safe(ledger), indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write(
        output_dir / "FORWARD_LIVE_SUMMARY.json",
        json.dumps(base.json_safe(summary), indent=2, sort_keys=True) + "\n",
    )
    admission = summary["admission"]
    base.atomic_write(
        output_dir / "FORWARD_LIVE_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD live-only combined forward portfolio v3",
                "",
                f"Status: **{admission['status']}**",
                "",
                (
                    "- Complete validation weekdays: "
                    f"`{admission['complete_validation_weekdays']}`"
                ),
                f"- Combined trades: `{admission['combined_trades']}`",
                (
                    "- Trades per complete weekday: "
                    f"`{admission['trades_per_complete_weekday']:.6f}`"
                ),
                (
                    "- Weekday trade coverage: "
                    f"`{admission['weekday_trade_coverage']:.6f}`"
                ),
                f"- Win rate: `{admission['win_rate']:.6f}`",
                f"- Payoff ratio: `{admission['payoff_ratio']}`",
                f"- Profit factor: `{admission['profit_factor']}`",
                (
                    "- Stressed profit factor: "
                    f"`{admission['stressed_profit_factor']}`"
                ),
                f"- Net P&L: `${admission['net_pnl_usd']:.2f}`",
                "- Research residual outcomes consumed: `0`",
                "- Daily learner trades consumed: `0`",
                "- Demo-order authorization: `false`",
                "",
            ]
        ),
    )
