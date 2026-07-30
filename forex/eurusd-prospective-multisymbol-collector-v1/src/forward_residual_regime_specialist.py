from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from . import forward_selective_learner as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    ROOT / "config" / "frozen_forward_residual_regime_specialist_v1.json"
)
LOCK_PATH = ROOT / "EURUSD_FORWARD_RESIDUAL_REGIME_LOCK_2026_07_30.sha256.json"
TIME_FORMAT = base.TIME_FORMAT


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
        "locked_with_zero_residual_decisions": True,
        "historical_backtest_allowed": False,
        "demo_order_authorized": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("residual-regime lock boundary is incomplete")
    for relative, expected in lock["files"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"residual-regime implementation drift: {relative}")
    return lock


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["campaign_id"] != "EURUSD_FORWARD_RESIDUAL_REGIME_V1":
        raise ValueError("unexpected residual-regime campaign")
    if config["demo_order_authorized"]:
        raise ValueError("residual-regime config unexpectedly authorizes orders")
    return config


def _resolve_contract_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_m15_module(config: dict[str, Any]):
    path = _resolve_contract_path(
        config["residual_ownership"]["m15_forward_module"]
    )
    name = "frozen_m15_forward_for_residual_ownership"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen M15 ownership module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_upstream_owned_dates(config: dict[str, Any]) -> set[str]:
    ownership = config["residual_ownership"]
    m15_csv = _resolve_contract_path(ownership["m15_signal_csv"])
    daily_path = _resolve_contract_path(ownership["daily_learner_decisions"])
    m15_config_path = _resolve_contract_path(ownership["m15_forward_config"])
    if not m15_csv.is_file() or not daily_path.is_file():
        raise FileNotFoundError(
            "required upstream ledger is missing; residual specialist fails cash"
        )
    module = _load_m15_module(config)
    m15_config = module.load_config(m15_config_path)
    m15_dates = {
        signal.entry_time.date().isoformat()
        for signal in module.load_signals(m15_csv, m15_config)
    }
    daily_records = json.loads(daily_path.read_text(encoding="utf-8"))
    if not isinstance(daily_records, list):
        raise TypeError("daily learner decision ledger is not a list")
    daily_dates = {
        str(record["decision_date"])
        for record in daily_records
        if record.get("eligible_side") in ("LONG", "SHORT")
    }
    return m15_dates | daily_dates


def classify_regime(
    context: dict[str, float],
    config: dict[str, Any],
) -> str:
    rules = config["causal_regimes"]
    strength_240 = float(context["strength_240"])
    agreement_240 = float(context["agreement_240"])
    strength_15 = float(context["strength_15"])
    if (
        abs(strength_240)
        <= float(rules["compression_max_abs_strength_240"])
        and abs(agreement_240)
        <= float(rules["compression_max_abs_agreement_240"])
    ):
        return "CROSSPAIR_COMPRESSION"
    if (
        strength_240 >= float(rules["broad_trend_min_abs_strength_240"])
        and agreement_240
        >= float(rules["broad_trend_min_abs_agreement_240"])
    ):
        return "BROAD_EUR_UP"
    if (
        strength_240 <= -float(rules["broad_trend_min_abs_strength_240"])
        and agreement_240
        <= -float(rules["broad_trend_min_abs_agreement_240"])
    ):
        return "BROAD_EUR_DOWN"
    if (
        strength_15 * strength_240 < 0.0
        and abs(strength_15)
        >= float(rules["disagreement_min_abs_strength_15"])
    ):
        return "SHORT_LONG_DISAGREEMENT"
    return "MIXED_TRANSITION"


def _profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    if gross_loss <= 0.0:
        return math.inf if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def _payoff_ratio(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / (sum(losses) / len(losses))


def side_statistics(
    values: list[float],
    config: dict[str, Any],
) -> dict[str, Any]:
    selector = config["online_regime_selector"]
    stress_r = (
        float(config["admission"]["additional_round_trip_stress_pips"])
        / float(config["execution"]["stop_pips"])
    )
    recent_window = int(selector["recent_window_observations"])
    shrunk_ev = sum(values) / (
        len(values) + float(selector["zero_expectancy_prior_strength"])
    )
    metrics = {
        "observations": len(values),
        "net_r": sum(values),
        "profit_factor": _profit_factor(values),
        "stressed_profit_factor": _profit_factor(
            [value - stress_r for value in values]
        ),
        "recent_profit_factor": _profit_factor(values[-recent_window:]),
        "shrunk_expectancy_r": shrunk_ev,
    }
    metrics["admitted"] = bool(
        len(values)
        >= int(selector["minimum_prior_observations_per_regime_side"])
        and shrunk_ev >= float(selector["minimum_shrunk_expectancy_r"])
        and metrics["profit_factor"]
        >= float(selector["minimum_profit_factor"])
        and metrics["stressed_profit_factor"]
        >= float(selector["minimum_plus_0_5_pip_profit_factor"])
        and metrics["recent_profit_factor"]
        >= float(selector["minimum_recent_profit_factor"])
    )
    return metrics


def select_side(
    histories: dict[str, dict[str, list[float]]],
    regime: str,
    resolved_residual_days: int,
    context: dict[str, float],
    config: dict[str, Any],
) -> tuple[str, str, dict[str, dict[str, Any]]]:
    selector = config["online_regime_selector"]
    statistics = {
        side: side_statistics(histories[regime][side], config)
        for side in ("LONG", "SHORT")
    }
    if resolved_residual_days < int(
        selector["global_warmup_resolved_residual_days"]
    ):
        return "CASH", "GLOBAL_WARMUP", statistics
    admitted = [
        side for side in ("LONG", "SHORT") if statistics[side]["admitted"]
    ]
    if not admitted:
        return "CASH", "NO_REGIME_SIDE_ADMITTED", statistics
    chosen = max(
        admitted,
        key=lambda side: (
            statistics[side]["shrunk_expectancy_r"],
            statistics[side]["stressed_profit_factor"],
            side == "LONG",
        ),
    )
    return chosen, "REGIME_SIDE_ADMITTED", statistics


def decision_datetime(day: date, config: dict[str, Any]) -> datetime:
    return datetime.combine(day, time.fromisoformat(config["decision_clock_utc"]))


def _sequence_halves(values: list[float]) -> list[list[float]]:
    split = len(values) // 2
    return [values[:split], values[split:]]


def admission_metrics(
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    resolved = [record for record in records if record["status"] == "RESOLVED"]
    eligible = [
        record
        for record in resolved
        if record["eligible_side"] in ("LONG", "SHORT")
    ]
    results = [float(record["eligible_result_r"]) for record in eligible]
    complete_weekdays = len(
        {
            record["decision_date"]
            for record in records
            if record["status"] in ("RESOLVED", "UPSTREAM_OWNED")
        }
    )
    residual_decisions = len(resolved)
    stress_r = (
        float(config["admission"]["additional_round_trip_stress_pips"])
        / float(config["execution"]["stop_pips"])
    )
    stressed = [value - stress_r for value in results]
    removal_count = math.ceil(len(results) * 0.05) if results else 0
    removed = sorted(results, reverse=True)[removal_count:]
    halves = _sequence_halves(results)
    monthly: dict[str, float] = defaultdict(float)
    for record in eligible:
        monthly[str(record["decision_date"])[:7]] += float(
            record["eligible_result_r"]
        )
    positive_months = {key: value for key, value in monthly.items() if value > 0}
    gross_positive = sum(positive_months.values())
    largest_month_share = (
        max(positive_months.values()) / gross_positive
        if gross_positive > 0.0
        else 1.0
    )
    payoff = _payoff_ratio(results)
    metrics = {
        "complete_weekdays": complete_weekdays,
        "residual_decisions": residual_decisions,
        "eligible_trades": len(eligible),
        "incremental_weekday_coverage": (
            len(eligible) / complete_weekdays if complete_weekdays else 0.0
        ),
        "profit_factor": _profit_factor(results),
        "payoff_ratio": payoff,
        "stressed_profit_factor": _profit_factor(stressed),
        "best_five_percent_removed_profit_factor": _profit_factor(removed),
        "trade_sequence_half_profit_factors": [
            _profit_factor(half) for half in halves
        ],
        "maximum_single_month_gross_profit_share": largest_month_share,
        "net_r": sum(results),
    }
    gates = config["admission"]
    checks = {
        "minimum_complete_weekdays": complete_weekdays
        >= int(gates["minimum_complete_weekdays"]),
        "minimum_residual_decisions": residual_decisions
        >= int(gates["minimum_residual_decisions"]),
        "minimum_eligible_trades": len(eligible)
        >= int(gates["minimum_eligible_trades"]),
        "minimum_incremental_weekday_coverage": metrics[
            "incremental_weekday_coverage"
        ]
        >= float(gates["minimum_incremental_weekday_coverage"]),
        "minimum_profit_factor": metrics["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_payoff_ratio": payoff is not None
        and payoff >= float(gates["minimum_payoff_ratio"]),
        "minimum_stressed_profit_factor": metrics["stressed_profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "minimum_best_five_percent_removed_profit_factor": metrics[
            "best_five_percent_removed_profit_factor"
        ]
        >= float(gates["minimum_best_five_percent_removed_profit_factor"]),
        "both_trade_sequence_halves_profitable": all(
            value
            > float(
                gates[
                    "minimum_each_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in metrics["trade_sequence_half_profit_factors"]
        ),
        "maximum_single_month_gross_profit_share": largest_month_share
        <= float(gates["maximum_single_month_gross_profit_share"]),
        "combined_portfolio_frequency_and_coverage": False,
        "mt5_signal_and_outcome_parity": False,
        "shadow_demo_soak": False,
    }
    metrics["checks"] = checks
    metrics["status"] = (
        "WAITING_COMBINED_PORTFOLIO_AND_EXECUTION_PROOF"
        if all(
            value
            for key, value in checks.items()
            if key
            not in {
                "combined_portfolio_frequency_and_coverage",
                "mt5_signal_and_outcome_parity",
                "shadow_demo_soak",
            }
        )
        else "WAITING_MINIMUM_EVIDENCE"
    )
    metrics["demo_order_authorized"] = False
    return metrics


def process(
    grouped: dict[datetime, dict[str, base.Bar]],
    upstream_owned_dates: set[str],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    histories: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"LONG": [], "SHORT": []}
    )
    records: list[dict[str, Any]] = []
    resolved_residual_days = 0
    latest_interval = max(grouped) if grouped else None
    maximum_hold = int(config["execution"]["maximum_hold_minutes"])
    for day in base.available_weekdays(grouped):
        decision_time = decision_datetime(day, config)
        final_required_open = decision_time + timedelta(
            minutes=maximum_hold - 5
        )
        if latest_interval is None or latest_interval < final_required_open:
            continue
        day_text = day.isoformat()
        if day_text in upstream_owned_dates:
            records.append(
                {
                    "decision_date": day_text,
                    "decision_time_utc": decision_time.strftime(TIME_FORMAT),
                    "status": "UPSTREAM_OWNED",
                    "regime": None,
                    "eligible_side": "CASH",
                    "eligibility_reason": "DUPLICATE_OPPORTUNITY_VETO",
                    "training_days_before": resolved_residual_days,
                }
            )
            continue
        context = base.build_context(grouped, decision_time, config)
        if context is None:
            records.append(
                {
                    "decision_date": day_text,
                    "decision_time_utc": decision_time.strftime(TIME_FORMAT),
                    "status": "MISSING_CONTEXT",
                    "regime": None,
                    "eligible_side": "CASH",
                    "eligibility_reason": "MISSING_CONTEXT",
                    "training_days_before": resolved_residual_days,
                }
            )
            continue
        long_outcome = base.resolve_side(grouped, decision_time, "LONG", config)
        short_outcome = base.resolve_side(
            grouped, decision_time, "SHORT", config
        )
        if long_outcome is None or short_outcome is None:
            continue
        regime = classify_regime(context, config)
        eligible_side, reason, statistics = select_side(
            histories,
            regime,
            resolved_residual_days,
            context,
            config,
        )
        shadow_side = "LONG" if context["strength_60"] >= 0.0 else "SHORT"
        outcomes = {"LONG": long_outcome, "SHORT": short_outcome}
        selected = outcomes[eligible_side] if eligible_side != "CASH" else None
        record = {
            "decision_date": day_text,
            "decision_time_utc": decision_time.strftime(TIME_FORMAT),
            "status": "RESOLVED",
            "regime": regime,
            "context": context,
            "training_days_before": resolved_residual_days,
            "side_statistics_before": statistics,
            "shadow_side": shadow_side,
            "eligible_side": eligible_side,
            "eligibility_reason": reason,
            "long_outcome": base.asdict(long_outcome),
            "short_outcome": base.asdict(short_outcome),
            "eligible_result_r": (
                selected.result_r if selected is not None else None
            ),
        }
        records.append(record)
        histories[regime]["LONG"].append(long_outcome.result_r)
        histories[regime]["SHORT"].append(short_outcome.result_r)
        resolved_residual_days += 1
        record["training_days_after"] = resolved_residual_days

    admission = admission_metrics(records, config)
    summary = {
        "schema_version": "eurusd_forward_residual_regime_summary_v1",
        "campaign_id": config["campaign_id"],
        "status": (
            "WAITING_FORWARD_DATA" if not records else "FORWARD_ONLY_SHADOW"
        ),
        "records": len(records),
        "resolved_residual_days": resolved_residual_days,
        "upstream_owned_days": sum(
            record["status"] == "UPSTREAM_OWNED" for record in records
        ),
        "regime_resolved_days": {
            regime: sum(
                record.get("regime") == regime
                and record["status"] == "RESOLVED"
                for record in records
            )
            for regime in config["causal_regimes"]["ordered_rules"]
        },
        "admission": admission,
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    return base.json_safe(records), base.json_safe(summary)


def write_outputs(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
    *,
    enforce_append_only: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "FORWARD_RESIDUAL_DECISIONS.json"
    if enforce_append_only and records_path.is_file():
        existing = json.loads(records_path.read_text(encoding="utf-8"))
        base.validate_append_only(existing, records)
    records_path.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "FORWARD_RESIDUAL_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    admission = summary["admission"]
    lines = [
        "# EURUSD forward residual-regime specialist",
        "",
        f"Status: **{summary['status']}**",
        "",
        f"- Complete weekdays: {admission['complete_weekdays']}",
        f"- Residual decisions: {admission['residual_decisions']}",
        f"- Eligible trades: {admission['eligible_trades']}",
        (
            "- Incremental weekday coverage: "
            f"{admission['incremental_weekday_coverage']:.2%}"
        ),
        f"- Profit factor: {admission['profit_factor']}",
        f"- Stressed profit factor: {admission['stressed_profit_factor']}",
        f"- Admission: {admission['status']}",
        "- Demo-order authorization: false",
        "",
    ]
    (output_dir / "FORWARD_RESIDUAL_SUMMARY.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
