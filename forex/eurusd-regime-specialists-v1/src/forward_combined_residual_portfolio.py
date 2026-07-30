from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import forward_combined_frequency_portfolio as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "frozen_forward_combined_residual_portfolio_v2.json"
LOCK_PATH = (
    ROOT
    / "EURUSD_FORWARD_COMBINED_RESIDUAL_PORTFOLIO_V2_LOCK_2026_07_30.sha256.json"
)


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
        "locked_with_zero_portfolio_decisions": True,
        "historical_backtest_allowed": False,
        "demo_order_authorized": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("combined-residual lock boundary is incomplete")
    for relative, expected in lock["files"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"combined-residual implementation drift: {relative}")
    return lock


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = base.load_config(path)
    if config.get("campaign_id") != "EURUSD_FORWARD_COMBINED_RESIDUAL_PORTFOLIO_V2":
        raise ValueError("unexpected combined-residual campaign")
    if config.get("demo_order_authorized"):
        raise ValueError("combined-residual config unexpectedly authorizes orders")
    return config


def normalize_residual_decisions(
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[base.Trade]:
    component = config["components"]["RESIDUAL_REGIME"]
    warmup = int(component["warmup_resolved_residual_days"])
    risk_usd = (
        float(component["fixed_lots"])
        * float(component["fixed_stop_pips"])
        * float(component["pip_value_usd_per_standard_lot"])
    )
    stress_r = float(component["stress_r_per_trade"])
    floor = base.parse_time(str(config["forward_floor_utc"]))
    allowed_regimes = {
        "CROSSPAIR_COMPRESSION",
        "BROAD_EUR_UP",
        "BROAD_EUR_DOWN",
        "SHORT_LONG_DISAGREEMENT",
        "MIXED_TRANSITION",
    }
    trades: list[base.Trade] = []
    seen_ids: set[str] = set()
    for record in records:
        if (
            record.get("status") != "RESOLVED"
            or record.get("eligible_side") not in ("LONG", "SHORT")
            or record.get("eligible_result_r") is None
        ):
            continue
        if int(record.get("training_days_before", -1)) < warmup:
            raise ValueError("residual eligible trade appeared before frozen warmup")
        regime = str(record.get("regime", ""))
        if regime not in allowed_regimes:
            raise ValueError(f"unknown residual regime: {regime}")
        side = str(record["eligible_side"])
        outcome_key = "long_outcome" if side == "LONG" else "short_outcome"
        outcome = record.get(outcome_key)
        if not isinstance(outcome, dict) or outcome.get("side") != side:
            raise ValueError("residual eligible outcome does not match selected side")
        entry_time = base.parse_time(str(record["decision_time_utc"]))
        exit_time = base.parse_time(str(outcome["exit_time"]))
        if entry_time < floor or exit_time < entry_time:
            raise ValueError("residual input has invalid time geometry")
        trade_id = f"RESIDUAL:{record['decision_date']}:{regime}:{side}"
        if trade_id in seen_ids:
            raise ValueError(f"duplicate residual trade id: {trade_id}")
        seen_ids.add(trade_id)
        result_r = float(record["eligible_result_r"])
        trades.append(
            base.Trade(
                trade_id=trade_id,
                component="RESIDUAL_REGIME",
                source="RESIDUAL_REGIME",
                entry_time=entry_time,
                exit_time=exit_time,
                initial_risk_usd=risk_usd,
                pnl_usd=result_r * risk_usd,
                stressed_pnl_usd=(result_r - stress_r) * risk_usd,
            )
        )
    return trades


def validation_start_time(
    daily_records: list[dict[str, Any]],
    residual_records: list[dict[str, Any]],
    config: dict[str, Any],
) -> datetime | None:
    daily_warmup = int(
        config["components"]["DAILY_CROSSPAIR"]["warmup_resolved_days"]
    )
    residual_warmup = int(
        config["components"]["RESIDUAL_REGIME"][
            "warmup_resolved_residual_days"
        ]
    )
    daily_candidates = [
        base.parse_time(str(record["decision_time_utc"]))
        for record in daily_records
        if record.get("status") == "RESOLVED"
        and int(record.get("training_days_before", -1)) >= daily_warmup
        and record.get("decision_time_utc")
    ]
    residual_candidates = [
        base.parse_time(str(record["decision_time_utc"]))
        for record in residual_records
        if record.get("status") == "RESOLVED"
        and int(record.get("training_days_before", -1)) >= residual_warmup
        and record.get("decision_time_utc")
    ]
    if not daily_candidates or not residual_candidates:
        return None
    return max(min(daily_candidates), min(residual_candidates))


def finalized_validation_days(
    complete_days: list[date],
    daily_records: list[dict[str, Any]],
    residual_records: list[dict[str, Any]],
    cutoff: datetime | None,
) -> list[date]:
    daily_terminal = {
        date.fromisoformat(str(record["decision_date"]))
        for record in daily_records
        if record.get("status") in ("RESOLVED", "MISSING_CONTEXT")
        and record.get("decision_date")
    }
    residual_terminal = {
        date.fromisoformat(str(record["decision_date"]))
        for record in residual_records
        if record.get("status")
        in ("RESOLVED", "MISSING_CONTEXT", "UPSTREAM_OWNED")
        and record.get("decision_date")
    }
    result: list[date] = []
    for day in complete_days:
        if cutoff is not None and day >= cutoff.date():
            break
        if day not in daily_terminal or day not in residual_terminal:
            break
        result.append(day)
    return result


def apply_causal_risk(
    trades: list[base.Trade],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    risk = config["causal_portfolio_risk"]
    priority = {
        source: index for index, source in enumerate(risk["same_timestamp_priority"])
    }
    required_sources = {
        "M15_CHOP",
        "M15_COMPRESSION",
        "DAILY_CROSSPAIR",
        "RESIDUAL_REGIME",
    }
    if set(priority) != required_sources:
        raise ValueError("combined-residual risk priority differs from frozen sources")
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
        value
        for name, value in checks.items()
        if name not in ("mt5_signal_parity", "shadow_soak")
    ]
    allowed = set(
        config["components"]["M15_REGIME"]["required_economic_statuses"]
    )
    return bool(automated) and all(bool(value) for value in automated) and (
        admission.get("status") in allowed
    )


def _residual_economic(
    summary: dict[str, Any],
    config: dict[str, Any],
) -> bool:
    admission = summary.get("admission", {})
    allowed = set(
        config["components"]["RESIDUAL_REGIME"]["required_economic_statuses"]
    )
    return admission.get("status") in allowed


def _daily_economic(
    summary: dict[str, Any],
    participates: bool,
) -> bool:
    if not participates:
        return True
    return bool(
        summary.get("admission", {}).get("research_economic_gates_pass", False)
    )


def admission_metrics(
    ledger: list[dict[str, Any]],
    validation_days: list[date],
    m15_summary: dict[str, Any],
    daily_summary: dict[str, Any],
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
    components = ("M15_REGIME", "DAILY_CROSSPAIR", "RESIDUAL_REGIME")
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
    daily_participates = bool(component_values["DAILY_CROSSPAIR"])
    m15_checks = m15_summary.get("admission", {}).get("checks", {})
    daily_admission = daily_summary.get("admission", {})
    residual_checks = residual_summary.get("admission", {}).get("checks", {})
    gates = config["final_admission"]
    half_pfs = base._sequence_half_pfs(accepted)
    checks = {
        "minimum_complete_validation_weekdays": complete_days
        >= int(gates["minimum_complete_validation_weekdays"]),
        "minimum_combined_trades": len(accepted)
        >= int(gates["minimum_combined_trades"]),
        "minimum_residual_component_trades": len(
            component_values["RESIDUAL_REGIME"]
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
        "minimum_daily_component_profit_factor_when_participating": (
            not daily_participates
            or component_pfs["DAILY_CROSSPAIR"]
            >= float(
                gates[
                    "minimum_daily_component_profit_factor_when_participating"
                ]
            )
        ),
        "minimum_residual_component_profit_factor": (
            component_pfs["RESIDUAL_REGIME"]
            >= float(gates["minimum_residual_component_profit_factor"])
        ),
        "maximum_risk_cap_rejection_share": rejection_share
        <= float(
            config["causal_portfolio_risk"][
                "maximum_risk_cap_rejection_share"
            ]
        ),
        "component_economic_admissions": (
            _m15_economic(m15_summary, config)
            and _residual_economic(residual_summary, config)
            and _daily_economic(daily_summary, daily_participates)
        ),
        "all_participating_component_mt5_parity": bool(
            m15_checks.get("mt5_signal_parity", False)
        )
        and bool(
            residual_checks.get("mt5_signal_and_outcome_parity", False)
        )
        and (
            not daily_participates
            or bool(daily_admission.get("mt5_parity_complete", False))
        ),
        "all_participating_component_shadow_soak": bool(
            m15_checks.get("shadow_soak", False)
        )
        and bool(residual_checks.get("shadow_demo_soak", False))
        and (
            not daily_participates
            or bool(daily_admission.get("shadow_demo_soak_complete", False))
        ),
        "combined_mt5_ordering_parity": False,
        "combined_demo_soak": False,
    }
    external = {
        "all_participating_component_mt5_parity",
        "all_participating_component_shadow_soak",
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
        status = "WAITING_MINIMUM_EVIDENCE"
    elif not all(checks[name] for name in automated):
        status = "REJECTED_FORWARD_PORTFOLIO"
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
        "daily_component_participates": daily_participates,
        "checks": checks,
        "demo_order_authorized": False,
    }


def process(
    m15_records: list[dict[str, Any]],
    m15_summary: dict[str, Any],
    daily_records: list[dict[str, Any]],
    daily_summary: dict[str, Any],
    residual_records: list[dict[str, Any]],
    residual_summary: dict[str, Any],
    feature_csv: Path,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if int(m15_summary.get("terminal_outcomes", -1)) != len(m15_records):
        raise ValueError("M15 summary/outcome count mismatch")
    if int(residual_summary.get("records", -1)) != len(residual_records):
        raise ValueError("residual summary/decision count mismatch")
    start_time = validation_start_time(
        daily_records,
        residual_records,
        config,
    )
    complete_days = base.load_complete_weekdays(
        feature_csv,
        config,
        start_time,
    )
    cutoff = base.pending_cutoff(m15_summary, daily_records)
    final_days = finalized_validation_days(
        complete_days,
        daily_records,
        residual_records,
        cutoff,
    )
    final_day_set = set(final_days)
    m15_trades = base.normalize_m15_outcomes(m15_records, config)
    daily_trades = base.normalize_daily_decisions(daily_records, config)
    residual_trades = normalize_residual_decisions(residual_records, config)
    trades = [
        trade
        for trade in m15_trades + daily_trades + residual_trades
        if start_time is not None
        and trade.entry_time >= start_time
        and trade.entry_time.date() in final_day_set
    ]
    ledger = apply_causal_risk(trades, config)
    admission = admission_metrics(
        ledger,
        final_days,
        m15_summary,
        daily_summary,
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
        "pending_causal_cutoff_utc": (
            cutoff.isoformat() if cutoff else None
        ),
        "causally_unfinalized_complete_weekdays": (
            len(complete_days) - len(final_days)
        ),
        "normalized_m15_trades": len(m15_trades),
        "normalized_daily_trades": len(daily_trades),
        "normalized_residual_trades": len(residual_trades),
        "portfolio_decisions": len(ledger),
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
        raise ValueError("combined-residual forward portfolio ledger shrank")
    for index, prior in enumerate(existing):
        if prior != safe[index]:
            raise ValueError(
                "combined-residual portfolio mutation refused "
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
    ledger_path = output_dir / "FORWARD_PORTFOLIO_LEDGER.json"
    if enforce_append_only and ledger_path.is_file():
        existing = base.load_records(ledger_path)
        validate_append_only(existing, ledger)
    base.atomic_write(
        ledger_path,
        json.dumps(base.json_safe(ledger), indent=2, sort_keys=True) + "\n",
    )
    base.atomic_write(
        output_dir / "FORWARD_SUMMARY.json",
        json.dumps(base.json_safe(summary), indent=2, sort_keys=True) + "\n",
    )
    admission = summary["admission"]
    base.atomic_write(
        output_dir / "FORWARD_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD combined residual forward portfolio v2",
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
                "- Demo-order authorization: `false`",
                "",
            ]
        ),
    )
