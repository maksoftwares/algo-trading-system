from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


@dataclass(frozen=True)
class Trade:
    trade_id: str
    component: str
    source: str
    entry_time: datetime
    exit_time: datetime
    initial_risk_usd: float
    pnl_usd: float
    stressed_pnl_usd: float


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("combined portfolio config is not an object")
    return value


def _load_json(path: Path, expected_type: type) -> Any:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, expected_type):
        raise TypeError(f"{path.name} has the wrong JSON type")
    return value


def load_records(path: Path) -> list[dict[str, Any]]:
    return _load_json(path, list)


def load_component_summary(
    path: Path,
    expected_campaign_id: str,
) -> dict[str, Any]:
    summary = _load_json(path, dict)
    if summary.get("campaign_id") != expected_campaign_id:
        raise ValueError(f"{path.name} campaign mismatch: {summary.get('campaign_id')}")
    return summary


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.strptime(value, TIME_FORMAT).replace(tzinfo=UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _forward_floor(config: dict[str, Any]) -> datetime:
    return parse_time(str(config["forward_floor_utc"]))


def _unique(trades: list[Trade]) -> list[Trade]:
    seen: set[str] = set()
    for trade in trades:
        if trade.trade_id in seen:
            raise ValueError(f"duplicate combined trade id: {trade.trade_id}")
        seen.add(trade.trade_id)
    return trades


def normalize_m15_outcomes(
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[Trade]:
    floor = _forward_floor(config)
    pip_value = float(
        config["components"]["M15_REGIME"]["pip_value_usd_per_standard_lot"]
    )
    trades: list[Trade] = []
    seen_signal_ids: set[str] = set()
    for record in records:
        signal_id = str(record.get("signal_id", ""))
        if not signal_id or signal_id in seen_signal_ids:
            raise ValueError("missing or duplicate M15 signal id")
        seen_signal_ids.add(signal_id)
        if record.get("status") != "RESOLVED":
            continue
        regime = str(record.get("regime", ""))
        if regime not in ("CHOP", "COMPRESSION"):
            raise ValueError(f"unknown M15 regime: {regime}")
        if record.get("side") != "SHORT":
            raise ValueError("M15 combined input is not the frozen SHORT side")
        entry_time = parse_time(str(record["entry_time_utc"]))
        exit_time = parse_time(str(record["exit_time_utc"]))
        if entry_time < floor or exit_time < entry_time:
            raise ValueError("M15 combined input has invalid time geometry")
        lots = float(record["lots"])
        stop_pips = float(record["stop_pips"])
        initial_risk = stop_pips * pip_value * lots
        if initial_risk <= 0.0:
            raise ValueError("M15 combined input has nonpositive initial risk")
        trades.append(
            Trade(
                trade_id=f"M15:{signal_id}",
                component="M15_REGIME",
                source=f"M15_{regime}",
                entry_time=entry_time,
                exit_time=exit_time,
                initial_risk_usd=initial_risk,
                pnl_usd=float(record["pnl_usd"]),
                stressed_pnl_usd=float(record["stressed_pnl_usd"]),
            )
        )
    return _unique(trades)


def normalize_daily_decisions(
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[Trade]:
    component = config["components"]["DAILY_CROSSPAIR"]
    warmup = int(component["warmup_resolved_days"])
    risk_usd = (
        float(component["fixed_lots"])
        * float(component["fixed_stop_pips"])
        * float(component["pip_value_usd_per_standard_lot"])
    )
    stress_r = float(component["stress_r_per_trade"])
    floor = _forward_floor(config)
    trades: list[Trade] = []
    seen_ids: set[str] = set()
    for record in records:
        if (
            record.get("status") != "RESOLVED"
            or record.get("eligible_side") not in ("LONG", "SHORT")
            or record.get("eligible_result_r") is None
        ):
            continue
        if int(record.get("training_days_before", -1)) < warmup:
            raise ValueError("daily eligible trade appeared before frozen warmup")
        side = str(record["eligible_side"])
        outcome_key = "long_outcome" if side == "LONG" else "short_outcome"
        outcome = record.get(outcome_key)
        if not isinstance(outcome, dict) or outcome.get("side") != side:
            raise ValueError("daily eligible outcome does not match selected side")
        entry_time = parse_time(str(record["decision_time_utc"]))
        exit_time = parse_time(str(outcome["exit_time"]))
        if entry_time < floor or exit_time < entry_time:
            raise ValueError("daily combined input has invalid time geometry")
        trade_id = f"DAILY:{record['decision_date']}:{side}"
        if trade_id in seen_ids:
            raise ValueError(f"duplicate daily combined trade id: {trade_id}")
        seen_ids.add(trade_id)
        result_r = float(record["eligible_result_r"])
        trades.append(
            Trade(
                trade_id=trade_id,
                component="DAILY_CROSSPAIR",
                source="DAILY_CROSSPAIR",
                entry_time=entry_time,
                exit_time=exit_time,
                initial_risk_usd=risk_usd,
                pnl_usd=result_r * risk_usd,
                stressed_pnl_usd=(result_r - stress_r) * risk_usd,
            )
        )
    return _unique(trades)


def validation_start_time(
    daily_records: list[dict[str, Any]],
    config: dict[str, Any],
) -> datetime | None:
    warmup = int(config["components"]["DAILY_CROSSPAIR"]["warmup_resolved_days"])
    candidates = [
        parse_time(str(record["decision_time_utc"]))
        for record in daily_records
        if record.get("status") == "RESOLVED"
        and int(record.get("training_days_before", -1)) >= warmup
        and record.get("decision_time_utc")
    ]
    return min(candidates) if candidates else None


def load_complete_weekdays(
    feature_csv: Path,
    config: dict[str, Any],
    start_time: datetime | None,
) -> list[date]:
    if start_time is None:
        return []
    denominator = config["frequency_denominator"]
    required_scope = str(denominator["required_evidence_scope"])
    required_symbol = str(denominator["source_symbol"])
    minimum_intervals = int(denominator["minimum_valid_m5_intervals_per_weekday"])
    floor = _forward_floor(config)
    intervals_by_day: dict[date, set[datetime]] = defaultdict(set)
    seen: set[datetime] = set()
    with feature_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("evidence_scope") != required_scope:
                raise ValueError("combined denominator refused non-forward data")
            timestamp = parse_time(str(row["interval_open_configured_utc"]))
            if timestamp < floor:
                raise ValueError("combined denominator refused pre-floor data")
            if row.get("source_symbol") != required_symbol:
                continue
            if timestamp in seen:
                raise ValueError("duplicate EURUSD denominator interval")
            seen.add(timestamp)
            valid_quotes = int(row.get("valid_two_sided_quote_count") or 0)
            if row.get("source_status") == "OK" and valid_quotes > 0:
                intervals_by_day[timestamp.date()].add(timestamp)
    return sorted(
        day
        for day, intervals in intervals_by_day.items()
        if day.weekday() < 5
        and day >= start_time.date()
        and len(intervals) >= minimum_intervals
    )


def pending_cutoff(
    m15_summary: dict[str, Any],
    daily_records: list[dict[str, Any]],
) -> datetime | None:
    candidates: list[datetime] = []
    pending_m15 = int(m15_summary.get("pending_signals", 0))
    m15_cutoff = m15_summary.get("earliest_pending_signal_entry_time_utc")
    if pending_m15:
        if not m15_cutoff:
            raise ValueError("M15 pending signals lack a causal cutoff timestamp")
        candidates.append(parse_time(str(m15_cutoff)))
    candidates.extend(
        parse_time(str(record["decision_time_utc"]))
        for record in daily_records
        if record.get("status") == "PENDING_OUTCOME" and record.get("decision_time_utc")
    )
    return min(candidates) if candidates else None


def finalized_validation_days(
    complete_days: list[date],
    daily_records: list[dict[str, Any]],
    cutoff: datetime | None,
) -> list[date]:
    terminal_daily_dates = {
        date.fromisoformat(str(record["decision_date"]))
        for record in daily_records
        if record.get("status") in ("RESOLVED", "MISSING_CONTEXT")
        and record.get("decision_date")
    }
    result: list[date] = []
    for day in complete_days:
        if cutoff is not None and day >= cutoff.date():
            break
        if day not in terminal_daily_dates:
            break
        result.append(day)
    return result


def apply_causal_risk(
    trades: list[Trade],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    risk = config["causal_portfolio_risk"]
    priority = {
        source: index for index, source in enumerate(risk["same_timestamp_priority"])
    }
    if set(priority) != {
        "M15_CHOP",
        "DAILY_CROSSPAIR",
        "M15_COMPRESSION",
    }:
        raise ValueError("combined risk priority differs from frozen sources")
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
    active: list[Trade] = []
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


def profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    return (
        gross_profit / gross_loss if gross_loss else math.inf if gross_profit else 0.0
    )


def payoff_ratio(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / (sum(losses) / len(losses))


def maximum_closed_trade_drawdown(rows: list[dict[str, Any]]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for row in sorted(
        rows,
        key=lambda item: (item["exit_time_utc"], item["trade_id"]),
    ):
        equity += float(row["pnl_usd"])
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def _best_removed_pf(values: list[float]) -> float:
    if not values:
        return 0.0
    count = max(1, math.ceil(len(values) * 0.05))
    removed = set(
        sorted(
            range(len(values)),
            key=lambda index: values[index],
            reverse=True,
        )[:count]
    )
    return profit_factor(
        [value for index, value in enumerate(values) if index not in removed]
    )


def _sequence_half_pfs(rows: list[dict[str, Any]]) -> list[float]:
    ordered = sorted(
        rows,
        key=lambda item: (item["entry_time_utc"], item["trade_id"]),
    )
    values = [float(row["pnl_usd"]) for row in ordered]
    if len(values) < 2:
        return [0.0, 0.0]
    midpoint = len(values) // 2
    return [
        profit_factor(values[:midpoint]),
        profit_factor(values[midpoint:]),
    ]


def _maximum_month_gross_share(rows: list[dict[str, Any]]) -> float:
    monthly: dict[str, float] = defaultdict(float)
    for row in rows:
        monthly[str(row["entry_time_utc"])[:7]] += max(0.0, float(row["pnl_usd"]))
    gross = sum(monthly.values())
    return max(monthly.values(), default=0.0) / gross if gross > 0.0 else 1.0


def _component_economic_checks(
    m15_summary: dict[str, Any],
    daily_summary: dict[str, Any],
    config: dict[str, Any],
) -> tuple[bool, bool]:
    m15_admission = m15_summary.get("admission", {})
    m15_checks = m15_admission.get("checks", {})
    m15_automated = [
        value
        for name, value in m15_checks.items()
        if name not in ("mt5_signal_parity", "shadow_soak")
    ]
    allowed_statuses = set(
        config["components"]["M15_REGIME"]["required_economic_statuses"]
    )
    m15_pass = (
        m15_admission.get("status") in allowed_statuses
        and bool(m15_automated)
        and all(bool(value) for value in m15_automated)
    )
    daily_pass = bool(
        daily_summary.get("admission", {}).get("research_economic_gates_pass", False)
    )
    return m15_pass, daily_pass


def admission_metrics(
    ledger: list[dict[str, Any]],
    validation_days: list[date],
    m15_summary: dict[str, Any],
    daily_summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    accepted = [row for row in ledger if row["accepted"]]
    rejected = [row for row in ledger if not row["accepted"]]
    values = [float(row["pnl_usd"]) for row in accepted]
    stressed = [float(row["stressed_pnl_usd"]) for row in accepted]
    base_pf = profit_factor(values)
    stressed_pf = profit_factor(stressed)
    half_pfs = _sequence_half_pfs(accepted)
    complete_day_count = len(validation_days)
    frequency = len(accepted) / complete_day_count if complete_day_count else 0.0
    coverage = (
        len({parse_time(row["entry_time_utc"]).date() for row in accepted})
        / complete_day_count
        if complete_day_count
        else 0.0
    )
    rejection_share = len(rejected) / len(ledger) if ledger else 0.0
    component_values = {
        name: [float(row["pnl_usd"]) for row in accepted if row["component"] == name]
        for name in ("M15_REGIME", "DAILY_CROSSPAIR")
    }
    component_pfs = {
        name: profit_factor(items) for name, items in component_values.items()
    }
    m15_economic, daily_economic = _component_economic_checks(
        m15_summary,
        daily_summary,
        config,
    )
    m15_checks = m15_summary.get("admission", {}).get("checks", {})
    daily_admission = daily_summary.get("admission", {})
    gates = config["final_admission"]
    checks = {
        "minimum_complete_validation_weekdays": complete_day_count
        >= int(gates["minimum_complete_validation_weekdays"]),
        "minimum_combined_trades": len(accepted)
        >= int(gates["minimum_combined_trades"]),
        "minimum_trades_per_complete_weekday": frequency
        >= float(gates["minimum_trades_per_complete_weekday"]),
        "maximum_trades_per_complete_weekday": frequency
        <= float(gates["maximum_trades_per_complete_weekday"]),
        "minimum_weekday_trade_coverage": coverage
        >= float(gates["minimum_weekday_trade_coverage"]),
        "minimum_combined_profit_factor": base_pf
        >= float(gates["minimum_combined_profit_factor"]),
        "minimum_combined_stressed_profit_factor": stressed_pf
        >= float(gates["minimum_combined_stressed_profit_factor"]),
        "minimum_best_5pct_removed_profit_factor": _best_removed_pf(values)
        >= float(gates["minimum_best_5pct_removed_profit_factor"]),
        "minimum_each_trade_sequence_half_profit_factor": all(
            value
            > float(gates["minimum_each_trade_sequence_half_profit_factor_exclusive"])
            for value in half_pfs
        ),
        "minimum_net_pnl_usd": sum(values)
        > float(gates["minimum_net_pnl_usd_exclusive"]),
        "maximum_closed_trade_drawdown_usd": maximum_closed_trade_drawdown(accepted)
        <= float(gates["maximum_closed_trade_drawdown_usd"]),
        "maximum_single_month_gross_profit_share": _maximum_month_gross_share(accepted)
        <= float(gates["maximum_single_month_gross_profit_share"]),
        "minimum_m15_component_profit_factor": component_pfs["M15_REGIME"]
        >= float(gates["minimum_m15_component_profit_factor"]),
        "minimum_daily_component_profit_factor": component_pfs["DAILY_CROSSPAIR"]
        >= float(gates["minimum_daily_component_profit_factor"]),
        "maximum_risk_cap_rejection_share": rejection_share
        <= float(config["causal_portfolio_risk"]["maximum_risk_cap_rejection_share"]),
        "both_component_economic_admissions": (m15_economic and daily_economic),
        "both_component_mt5_parity": bool(m15_checks.get("mt5_signal_parity", False))
        and bool(daily_admission.get("mt5_parity_complete", False)),
        "both_component_shadow_soak": bool(m15_checks.get("shadow_soak", False))
        and bool(daily_admission.get("shadow_demo_soak_complete", False)),
        "combined_mt5_ordering_parity": False,
        "combined_demo_soak": False,
    }
    external_names = {
        "both_component_mt5_parity",
        "both_component_shadow_soak",
        "combined_mt5_ordering_parity",
        "combined_demo_soak",
    }
    automated_names = [name for name in checks if name not in external_names]
    enough_evidence = (
        checks["minimum_complete_validation_weekdays"]
        and checks["minimum_combined_trades"]
    )
    if not enough_evidence:
        status = "WAITING_MINIMUM_EVIDENCE"
    elif not all(checks[name] for name in automated_names):
        status = "REJECTED_FORWARD_PORTFOLIO"
    elif not all(checks[name] for name in external_names):
        status = "WAITING_EXTERNAL_PARITY_AND_SOAK"
    else:
        status = "READY_FOR_GUARDED_DEMO_IMPLEMENTATION"
    return {
        "status": status,
        "complete_validation_weekdays": complete_day_count,
        "combined_trades": len(accepted),
        "risk_cap_rejections": len(rejected),
        "risk_cap_rejection_share": rejection_share,
        "trades_per_complete_weekday": frequency,
        "weekday_trade_coverage": coverage,
        "win_rate": (
            sum(value > 0.0 for value in values) / len(values) if values else 0.0
        ),
        "payoff_ratio": payoff_ratio(values),
        "profit_factor": base_pf,
        "stressed_profit_factor": stressed_pf,
        "best_5pct_removed_profit_factor": _best_removed_pf(values),
        "trade_sequence_half_profit_factors": half_pfs,
        "net_pnl_usd": sum(values),
        "maximum_closed_trade_drawdown_usd": maximum_closed_trade_drawdown(accepted),
        "maximum_single_month_gross_profit_share": _maximum_month_gross_share(accepted),
        "component_trade_counts": {
            name: len(items) for name, items in component_values.items()
        },
        "component_profit_factors": component_pfs,
        "checks": checks,
        "demo_order_authorized": False,
    }


def process(
    m15_records: list[dict[str, Any]],
    m15_summary: dict[str, Any],
    daily_records: list[dict[str, Any]],
    daily_summary: dict[str, Any],
    feature_csv: Path,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if int(m15_summary.get("terminal_outcomes", -1)) != len(m15_records):
        raise ValueError("M15 summary/outcome count mismatch")
    start_time = validation_start_time(daily_records, config)
    complete_days = load_complete_weekdays(feature_csv, config, start_time)
    cutoff = pending_cutoff(m15_summary, daily_records)
    final_days = finalized_validation_days(
        complete_days,
        daily_records,
        cutoff,
    )
    final_day_set = set(final_days)
    m15_trades = normalize_m15_outcomes(m15_records, config)
    daily_trades = normalize_daily_decisions(daily_records, config)
    trades = m15_trades + daily_trades
    trades = [
        trade
        for trade in trades
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
        config,
    )
    summary = {
        "schema_version": config["schema_version"],
        "campaign_id": config["campaign_id"],
        "validation_start_time_utc": (start_time.isoformat() if start_time else None),
        "raw_complete_validation_weekdays": len(complete_days),
        "complete_validation_weekdays": len(final_days),
        "complete_validation_dates": [day.isoformat() for day in final_days],
        "pending_causal_cutoff_utc": (cutoff.isoformat() if cutoff else None),
        "causally_unfinalized_complete_weekdays": (
            len(complete_days) - len(final_days)
        ),
        "normalized_m15_trades": len(m15_trades),
        "normalized_daily_trades": len(daily_trades),
        "portfolio_decisions": len(ledger),
        "admission": admission,
        "demo_order_authorized": False,
    }
    return ledger, summary


def json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def load_existing_ledger(output_dir: Path) -> list[dict[str, Any]]:
    path = output_dir / "FORWARD_PORTFOLIO_LEDGER.json"
    if not path.exists():
        return []
    return _load_json(path, list)


def validate_append_only(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> None:
    safe = json_safe(new)
    if len(safe) < len(existing):
        raise ValueError("combined forward portfolio ledger shrank")
    for index, prior in enumerate(existing):
        if prior != safe[index]:
            raise ValueError(
                "combined forward portfolio mutation refused "
                f"at index={index} trade_id={prior.get('trade_id')}"
            )


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_outputs(
    ledger: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
    *,
    enforce_append_only: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if enforce_append_only:
        validate_append_only(load_existing_ledger(output_dir), ledger)
    atomic_write(
        output_dir / "FORWARD_PORTFOLIO_LEDGER.json",
        json.dumps(json_safe(ledger), indent=2, sort_keys=True) + "\n",
    )
    atomic_write(
        output_dir / "FORWARD_SUMMARY.json",
        json.dumps(json_safe(summary), indent=2, sort_keys=True) + "\n",
    )
    admission = summary["admission"]
    atomic_write(
        output_dir / "FORWARD_SUMMARY.md",
        "\n".join(
            [
                "# EURUSD combined forward frequency portfolio",
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
                f"- Profit factor: `{admission['profit_factor']}`",
                (f"- Stressed profit factor: `{admission['stressed_profit_factor']}`"),
                f"- Net P&L: `${admission['net_pnl_usd']:.2f}`",
                "- Demo-order authorization: `false`",
                "",
            ]
        ),
    )
