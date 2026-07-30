from __future__ import annotations

import importlib
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from . import forward_learner_history_diagnostic as daily_diagnostic

ROOT = Path(__file__).resolve().parents[2]
FOREX_ROOT = ROOT.parent
COLLECTOR_ROOT = FOREX_ROOT / "eurusd-prospective-multisymbol-collector-v1"
CONFIG_PATH = ROOT / "config" / "frozen_residual_history_diagnostic_v1.json"
M15_TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


def sha256(path: Path) -> str:
    return daily_diagnostic.sha256(path)


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["status"] != "POST_FREEZE_RETROSPECTIVE_FALSIFICATION_ONLY":
        raise RuntimeError("unexpected residual diagnostic boundary")
    if config["candidate_parameters_may_change"] is not False:
        raise RuntimeError("diagnostic permits candidate changes")
    if config["result_can_count_as_forward_evidence"] is not False:
        raise RuntimeError("diagnostic permits forward evidence credit")
    if config["demo_order_authorized"] is not False:
        raise RuntimeError("diagnostic permits demo orders")
    return config


def _source_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def verify_sources(config: dict[str, Any]) -> dict[str, str]:
    source = config["source"]
    pairs = {
        name: (
            _source_path(str(source[path_key])),
            str(source[hash_key]),
        )
        for name, path_key, hash_key in (
            ("residual_lock", "residual_lock", "residual_lock_sha256"),
            (
                "publisher_config",
                "publisher_config",
                "publisher_config_sha256",
            ),
            (
                "historical_bar_contract",
                "historical_bar_contract",
                "historical_bar_contract_sha256",
            ),
            (
                "protected_m15_trades",
                "protected_m15_trades",
                "protected_m15_trades_sha256",
            ),
        )
    }
    actual = {name: sha256(path) for name, (path, _) in pairs.items()}
    expected = {name: expected for name, (_, expected) in pairs.items()}
    if actual != expected:
        raise RuntimeError(
            f"residual diagnostic source mismatch: {actual} != {expected}"
        )
    return actual


def load_residual_engine():
    collector_text = str(COLLECTOR_ROOT)
    if collector_text not in sys.path:
        sys.path.insert(0, collector_text)
    module = importlib.import_module("src.forward_residual_regime_specialist")
    module.verify_lock()
    return module


def _weekdays(start: date, end: date) -> list[date]:
    result: list[date] = []
    cursor = start
    while cursor < end:
        if cursor.weekday() < 5:
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def load_m15_trades(
    config: dict[str, Any],
) -> tuple[pd.DataFrame, set[str]]:
    path = _source_path(config["source"]["protected_m15_trades"])
    frame = pd.read_csv(path)
    frame["entry_time"] = pd.to_datetime(
        frame["entry_time"],
        format=M15_TIME_FORMAT,
        utc=True,
    )
    frame["exit_time"] = pd.to_datetime(
        frame["exit_time"],
        format=M15_TIME_FORMAT,
        utc=True,
    )
    frame["pnl_usd"] = frame["profit"].astype(float)
    frame["stressed_pnl_usd"] = frame["pnl_usd"] - (
        float(config["execution"]["additional_round_trip_stress_usd_per_trade"])
        * frame["volume"].astype(float)
        / float(config["execution"]["residual_lots"])
    )
    frame["component"] = "M15_REGIME"
    frame["side"] = "SHORT"
    frame["decision_date"] = frame["entry_time"].dt.date.astype(str)
    return frame, set(frame["decision_date"])


def replay_exact_candidate(
    frames: dict[str, pd.DataFrame],
    residual_config: dict[str, Any],
    learner_config: dict[str, Any],
    m15_owned_dates: set[str],
    start: date,
    end: date,
    residual,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    histories: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"LONG": [], "SHORT": []}
    )
    residual_records: list[dict[str, Any]] = []
    daily_records: list[dict[str, Any]] = []
    resolved_residual_days = 0
    weights = [0.0] * 9
    resolved_daily_days = 0
    for day in _weekdays(start, end):
        daily_grouped = daily_diagnostic.build_day_bars(
            day,
            frames,
            learner_config,
            residual.base,
        )
        daily_record, weights, resolved_daily_days = (
            daily_diagnostic.replay_day(
                day,
                daily_grouped,
                weights,
                resolved_daily_days,
                learner_config,
                residual.base,
            )
        )
        daily_records.append(residual.base.json_safe(daily_record))
        day_text = day.isoformat()
        decision_time = residual.decision_datetime(day, residual_config)
        base_record = {
            "decision_date": day_text,
            "decision_time_utc": decision_time.strftime(residual.TIME_FORMAT),
            "eligible_side": "CASH",
            "training_days_before": resolved_residual_days,
        }
        if day.weekday() == 4:
            residual_records.append(
                {
                    **base_record,
                    "status": "CASH_MARKET_CLOSURE",
                    "regime": None,
                    "eligibility_reason": "IMMUTABLE_CASH_MARKET_CLOSURE",
                    "training_days_before": None,
                }
            )
            continue
        daily_owned = daily_record.get("eligible_side") in ("LONG", "SHORT")
        if day_text in m15_owned_dates or daily_owned:
            residual_records.append(
                {
                    **base_record,
                    "status": "UPSTREAM_OWNED",
                    "regime": None,
                    "eligibility_reason": "DUPLICATE_OPPORTUNITY_VETO",
                    "upstream_owner": (
                        "M15_REGIME"
                        if day_text in m15_owned_dates
                        else "DAILY_CROSSPAIR"
                    ),
                }
            )
            continue
        grouped = daily_diagnostic.build_day_bars(
            day,
            frames,
            residual_config,
            residual.base,
        )
        context = residual.base.build_context(
            grouped,
            decision_time,
            residual_config,
        )
        if context is None:
            residual_records.append(
                {
                    **base_record,
                    "status": "MISSING_CONTEXT",
                    "regime": None,
                    "eligibility_reason": "MISSING_CONTEXT",
                }
            )
            continue
        long_outcome = residual.base.resolve_side(
            grouped,
            decision_time,
            "LONG",
            residual_config,
        )
        short_outcome = residual.base.resolve_side(
            grouped,
            decision_time,
            "SHORT",
            residual_config,
        )
        if long_outcome is None or short_outcome is None:
            residual_records.append(
                {
                    **base_record,
                    "status": "MISSING_OUTCOME_PATH",
                    "regime": None,
                    "eligibility_reason": "INCOMPLETE_SIX_HOUR_PATH",
                }
            )
            continue
        regime = residual.classify_regime(context, residual_config)
        side, reason, statistics = residual.select_side(
            histories,
            regime,
            resolved_residual_days,
            context,
            residual_config,
        )
        outcomes = {"LONG": long_outcome, "SHORT": short_outcome}
        selected = outcomes[side] if side != "CASH" else None
        record = {
            **base_record,
            "status": "RESOLVED",
            "regime": regime,
            "context": context,
            "side_statistics_before": statistics,
            "shadow_side": (
                "LONG" if float(context["strength_60"]) >= 0.0 else "SHORT"
            ),
            "eligible_side": side,
            "eligibility_reason": reason,
            "long_outcome": asdict(long_outcome),
            "short_outcome": asdict(short_outcome),
            "eligible_result_r": (
                float(selected.result_r) if selected is not None else None
            ),
        }
        residual_records.append(residual.base.json_safe(record))
        histories[regime]["LONG"].append(float(long_outcome.result_r))
        histories[regime]["SHORT"].append(float(short_outcome.result_r))
        resolved_residual_days += 1
        record["training_days_after"] = resolved_residual_days
    return residual_records, daily_records, resolved_residual_days


def profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    return (
        gross_profit / gross_loss
        if gross_loss
        else math.inf
        if gross_profit
        else 0.0
    )


def payoff_ratio(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / (sum(losses) / len(losses))


def maximum_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def best_removed_profit_factor(values: list[float]) -> float:
    if not values:
        return 0.0
    remove = max(1, math.ceil(len(values) * 0.05))
    indexes = set(
        sorted(
            range(len(values)),
            key=lambda index: values[index],
            reverse=True,
        )[:remove]
    )
    return profit_factor(
        [value for index, value in enumerate(values) if index not in indexes]
    )


def value_metrics(
    values: list[float],
    stressed: list[float],
    denominator: int,
) -> dict[str, Any]:
    midpoint = len(values) // 2
    return {
        "trades": len(values),
        "trades_per_weekday": len(values) / denominator if denominator else 0.0,
        "win_rate": (
            sum(value > 0.0 for value in values) / len(values)
            if values
            else 0.0
        ),
        "payoff_ratio": payoff_ratio(values),
        "profit_factor": profit_factor(values),
        "stressed_profit_factor": profit_factor(stressed),
        "best_5pct_removed_profit_factor": best_removed_profit_factor(values),
        "trade_sequence_half_profit_factors": (
            [
                profit_factor(values[:midpoint]),
                profit_factor(values[midpoint:]),
            ]
            if len(values) >= 2
            else [0.0, 0.0]
        ),
        "net": sum(values),
        "maximum_closed_trade_drawdown": maximum_drawdown(values),
    }


def residual_metrics(
    records: list[dict[str, Any]],
    start: str,
    end: str,
    stress_r: float,
) -> dict[str, Any]:
    terminal = [
        record
        for record in records
        if start <= str(record["decision_date"]) < end
    ]
    eligible = [
        record
        for record in terminal
        if record.get("eligible_side") in ("LONG", "SHORT")
        and record.get("eligible_result_r") is not None
    ]
    values = [float(record["eligible_result_r"]) for record in eligible]
    result = value_metrics(
        values,
        [value - stress_r for value in values],
        len(terminal),
    )
    result.update(
        {
            "complete_weekdays": len(terminal),
            "weekday_coverage": (
                len({record["decision_date"] for record in eligible})
                / len(terminal)
                if terminal
                else 0.0
            ),
            "friday_market_closure_cash": sum(
                record["status"] == "CASH_MARKET_CLOSURE"
                for record in terminal
            ),
            "upstream_owned_cash": sum(
                record["status"] == "UPSTREAM_OWNED" for record in terminal
            ),
            "missing_context": sum(
                record["status"] == "MISSING_CONTEXT" for record in terminal
            ),
            "missing_outcome_path": sum(
                record["status"] == "MISSING_OUTCOME_PATH"
                for record in terminal
            ),
        }
    )
    return result


def residual_trade_frame(
    records: list[dict[str, Any]],
    start: str,
    end: str,
    config: dict[str, Any],
) -> pd.DataFrame:
    risk = float(config["execution"]["residual_initial_risk_usd"])
    stress = float(
        config["execution"]["additional_round_trip_stress_usd_per_trade"]
    )
    rows: list[dict[str, Any]] = []
    for record in records:
        if not (start <= str(record["decision_date"]) < end):
            continue
        side = record.get("eligible_side")
        if side not in ("LONG", "SHORT"):
            continue
        outcome = record[
            "long_outcome" if side == "LONG" else "short_outcome"
        ]
        pnl = float(record["eligible_result_r"]) * risk
        rows.append(
            {
                "entry_time": pd.Timestamp(record["decision_time_utc"], tz="UTC"),
                "exit_time": pd.Timestamp(outcome["exit_time"], tz="UTC"),
                "decision_date": record["decision_date"],
                "component": "RESIDUAL_LIVE",
                "side": side,
                "pnl_usd": pnl,
                "stressed_pnl_usd": pnl - stress,
                "regime": record["regime"],
            }
        )
    return pd.DataFrame(rows)


def portfolio_metrics(frame: pd.DataFrame, denominator: int) -> dict[str, Any]:
    if frame.empty:
        return {
            **value_metrics([], [], denominator),
            "weekday_coverage": 0.0,
            "active_weekdays": 0,
            "maximum_single_month_gross_profit_share": 1.0,
        }
    ordered = frame.sort_values(["entry_time", "component"]).reset_index(drop=True)
    values = ordered["pnl_usd"].astype(float).tolist()
    stressed = ordered["stressed_pnl_usd"].astype(float).tolist()
    result = value_metrics(values, stressed, denominator)
    active = ordered["decision_date"].nunique()
    monthly = (
        ordered.assign(month=ordered["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")["pnl_usd"]
        .apply(lambda series: float(series[series > 0.0].sum()))
    )
    gross = float(monthly.sum())
    result.update(
        {
            "weekday_coverage": active / denominator if denominator else 0.0,
            "active_weekdays": int(active),
            "maximum_single_month_gross_profit_share": (
                float(monthly.max()) / gross if gross > 0.0 else 1.0
            ),
        }
    )
    return result


def evaluate(
    residual_records: list[dict[str, Any]],
    daily_records: list[dict[str, Any]],
    m15: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    period = config["period"]
    stress_r = (
        float(config["execution"]["additional_round_trip_stress_usd_per_trade"])
        / float(config["execution"]["residual_initial_risk_usd"])
    )
    full = residual_metrics(
        residual_records,
        str(period["standalone_from_inclusive"]),
        str(period["standalone_to_exclusive"]),
        stress_r,
    )
    blocks = {
        name: residual_metrics(residual_records, start, end, stress_r)
        for name, start, end in (
            ("B1_2016H2_2018", "2016-07-01", "2019-01-01"),
            ("B2_2019_2021", "2019-01-01", "2022-01-01"),
            ("B3_2022_2024", "2022-01-01", "2025-01-01"),
            ("B4_2025_2026H1", "2025-01-01", "2026-07-01"),
            ("LATEST_12_MONTHS", "2025-07-01", "2026-07-01"),
        )
    }
    regimes: dict[str, Any] = {}
    for regime in (
        "CROSSPAIR_COMPRESSION",
        "BROAD_EUR_UP",
        "BROAD_EUR_DOWN",
        "SHORT_LONG_DISAGREEMENT",
        "MIXED_TRANSITION",
    ):
        selected = [
            record
            for record in residual_records
            if record.get("regime") == regime
            and record.get("eligible_result_r") is not None
        ]
        values = [float(record["eligible_result_r"]) for record in selected]
        regimes[regime] = value_metrics(
            values,
            [value - stress_r for value in values],
            full["complete_weekdays"],
        )

    portfolio_start = str(period["portfolio_from_inclusive"])
    portfolio_end = str(period["portfolio_to_exclusive"])
    split = str(period["portfolio_split"])
    residual_frame = residual_trade_frame(
        residual_records,
        portfolio_start,
        portfolio_end,
        config,
    )
    m15_frame = m15[
        m15["decision_date"].ge(portfolio_start)
        & m15["decision_date"].lt(portfolio_end)
    ][
        [
            "entry_time",
            "exit_time",
            "decision_date",
            "component",
            "side",
            "pnl_usd",
            "stressed_pnl_usd",
        ]
    ].copy()
    combined = pd.concat([m15_frame, residual_frame], ignore_index=True)
    combined = combined.sort_values(["entry_time", "component"]).reset_index(
        drop=True
    )
    if combined.groupby(["decision_date", "component"]).size().empty:
        overlap_dates = 0
    else:
        overlap_dates = len(
            set(m15_frame["decision_date"])
            & set(residual_frame["decision_date"])
        )
    full_portfolio = portfolio_metrics(
        combined,
        int(period["portfolio_weekdays"]),
    )
    first = portfolio_metrics(
        combined[combined["decision_date"].lt(split)],
        int(period["portfolio_half_weekdays"]),
    )
    second = portfolio_metrics(
        combined[combined["decision_date"].ge(split)],
        int(period["portfolio_half_weekdays"]),
    )
    component_metrics = {
        component: portfolio_metrics(
            combined[combined["component"].eq(component)],
            int(period["portfolio_weekdays"]),
        )
        for component in ("M15_REGIME", "RESIDUAL_LIVE")
    }
    gates = config["portfolio_gates"]
    checks = {
        "minimum_trades_per_weekday": full_portfolio["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "maximum_trades_per_weekday": full_portfolio["trades_per_weekday"]
        <= float(gates["maximum_trades_per_weekday"]),
        "minimum_weekday_coverage": full_portfolio["weekday_coverage"]
        >= float(gates["minimum_weekday_coverage"]),
        "minimum_win_rate": full_portfolio["win_rate"]
        >= float(gates["minimum_win_rate"]),
        "maximum_win_rate": full_portfolio["win_rate"]
        <= float(gates["maximum_win_rate"]),
        "minimum_payoff_ratio": full_portfolio["payoff_ratio"] is not None
        and full_portfolio["payoff_ratio"]
        >= float(gates["minimum_payoff_ratio"]),
        "minimum_profit_factor": full_portfolio["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": full_portfolio[
            "stressed_profit_factor"
        ]
        >= float(gates["minimum_stressed_profit_factor"]),
        "minimum_best_5pct_removed_profit_factor": full_portfolio[
            "best_5pct_removed_profit_factor"
        ]
        >= float(gates["minimum_best_5pct_removed_profit_factor"]),
        "minimum_each_half_profit_factor": all(
            value
            > float(gates["minimum_each_half_profit_factor_exclusive"])
            for value in full_portfolio["trade_sequence_half_profit_factors"]
        ),
        "minimum_latest_12_month_profit_factor": second["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "minimum_latest_12_month_best_5pct_removed_profit_factor": second[
            "best_5pct_removed_profit_factor"
        ]
        >= float(
            gates["minimum_latest_12_month_best_5pct_removed_profit_factor"]
        ),
        "minimum_net_pnl_usd": full_portfolio["net"]
        > float(gates["minimum_net_pnl_usd_exclusive"]),
        "zero_m15_residual_owned_date_overlap": overlap_dates == 0,
        "zero_missing_residual_context": full["missing_context"] == 0,
        "zero_missing_residual_outcome_paths": full["missing_outcome_path"] == 0,
    }
    monthly = (
        combined.assign(month=combined["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")
        .agg(
            trades=("pnl_usd", "size"),
            pnl_usd=("pnl_usd", "sum"),
            stressed_pnl_usd=("stressed_pnl_usd", "sum"),
        )
        .reset_index()
    )
    result = {
        "schema_version": config["schema_version"],
        "status": (
            "HISTORICAL_SUPPORTS_FORWARD_CANDIDATE"
            if all(checks.values())
            else "HISTORICAL_FALSIFICATION_FAILED"
        ),
        "research_boundary": config["status"],
        "candidate_parameters_changed": False,
        "variants_evaluated": 1,
        "result_can_count_as_forward_evidence": False,
        "standalone_residual": {
            "full": full,
            "chronological_blocks": blocks,
            "by_regime": regimes,
        },
        "combined_portfolio": {
            "full": full_portfolio,
            "first_12_months": first,
            "second_12_months": second,
            "components": component_metrics,
            "m15_residual_owned_date_overlaps": overlap_dates,
            "checks": checks,
        },
        "daily_learner": {
            "records_replayed": len(daily_records),
            "eligible_dates": sum(
                record.get("eligible_side") in ("LONG", "SHORT")
                for record in daily_records
            ),
            "used_only_as_frozen_same_date_ownership_veto": True,
            "portfolio_trades_consumed": 0,
        },
        "prohibitions": config["prohibitions"],
        "demo_order_authorized": False,
    }
    return result, combined, monthly


def run() -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
]:
    config = load_config()
    verified_contracts = verify_sources(config)
    residual = load_residual_engine()
    residual_config = residual.load_config()
    learner_config, source_config = daily_diagnostic.load_contracts()
    symbols = [
        residual_config["execution_symbol"],
        *residual_config["predictor_symbols"],
    ]
    frames, verified_bars = daily_diagnostic.load_source_frames(
        source_config,
        symbols,
    )
    m15, m15_dates = load_m15_trades(config)
    period = config["period"]
    start = date.fromisoformat(str(period["standalone_from_inclusive"]))
    end = date.fromisoformat(str(period["standalone_to_exclusive"]))
    residual_records, daily_records, resolved = replay_exact_candidate(
        frames,
        residual_config,
        learner_config,
        m15_dates,
        start,
        end,
        residual,
    )
    result, combined, monthly = evaluate(
        residual_records,
        daily_records,
        m15,
        config,
    )
    result.update(
        {
            "campaign_under_test": residual_config["campaign_id"],
            "resolved_residual_training_days": resolved,
            "verified_contract_sha256": verified_contracts,
            "verified_historical_bar_sha256": verified_bars,
            "residual_config_sha256": sha256(residual.CONFIG_PATH),
            "residual_source_sha256": sha256(Path(residual.__file__)),
            "publisher_friday_action_verified": (
                json.loads(
                    _source_path(
                        config["source"]["publisher_config"]
                    ).read_text(encoding="utf-8")
                )["friday_utc_action"]
            ),
        }
    )
    return residual_records, result, combined, monthly


def _safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def render_report(result: dict[str, Any]) -> str:
    residual = result["standalone_residual"]["full"]
    combined = result["combined_portfolio"]["full"]
    second = result["combined_portfolio"]["second_12_months"]
    failed = [
        name
        for name, value in result["combined_portfolio"]["checks"].items()
        if not value
    ]
    return "\n".join(
        [
            "# Frozen residual specialist historical diagnostic",
            "",
            f"Status: **{result['status']}**",
            "",
            "This is one exact post-freeze falsification replay. No parameter,",
            "clock, side rule, stop, target, regime, or threshold was searched.",
            "It cannot count as forward evidence or authorize an order.",
            "",
            "## Standalone residual result",
            "",
            "| Metric | Result |",
            "|---|---:|",
            f"| Complete weekdays | {residual['complete_weekdays']:,} |",
            f"| Eligible trades | {residual['trades']:,} |",
            f"| Trades/weekday | {residual['trades_per_weekday']:.4f} |",
            f"| Weekday coverage | {residual['weekday_coverage']:.2%} |",
            f"| Win rate | {residual['win_rate']:.2%} |",
            f"| Payoff | {residual['payoff_ratio']} |",
            f"| PF | {residual['profit_factor']:.4f} |",
            f"| Stressed PF | {residual['stressed_profit_factor']:.4f} |",
            f"| Net R | {residual['net']:.4f} |",
            "",
            "## Protected M15 plus residual, two-year broker window",
            "",
            "| Metric | Full | Second 12 months |",
            "|---|---:|---:|",
            (
                f"| Trades | {combined['trades']:,} | "
                f"{second['trades']:,} |"
            ),
            (
                f"| Trades/weekday | {combined['trades_per_weekday']:.4f} | "
                f"{second['trades_per_weekday']:.4f} |"
            ),
            (
                f"| Weekday coverage | {combined['weekday_coverage']:.2%} | "
                f"{second['weekday_coverage']:.2%} |"
            ),
            (
                f"| Win rate | {combined['win_rate']:.2%} | "
                f"{second['win_rate']:.2%} |"
            ),
            (
                f"| Payoff | {combined['payoff_ratio']} | "
                f"{second['payoff_ratio']} |"
            ),
            (
                f"| PF | {combined['profit_factor']:.4f} | "
                f"{second['profit_factor']:.4f} |"
            ),
            (
                f"| Stressed PF | {combined['stressed_profit_factor']:.4f} | "
                f"{second['stressed_profit_factor']:.4f} |"
            ),
            (
                "| Best-5%-removed PF | "
                f"{combined['best_5pct_removed_profit_factor']:.4f} | "
                f"{second['best_5pct_removed_profit_factor']:.4f} |"
            ),
            (
                f"| Net P&L | ${combined['net']:.2f} | "
                f"${second['net']:.2f} |"
            ),
            "",
            "Failed frozen portfolio gates:",
            "",
            *([f"- `{name}`" for name in failed] or ["- None"]),
            "",
            "Demo-order authorization: `false`.",
            "",
        ]
    )


def write_outputs(
    records: list[dict[str, Any]],
    result: dict[str, Any],
    combined: pd.DataFrame,
    monthly: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    eligible = [
        record
        for record in records
        if record.get("eligible_result_r") is not None
    ]
    (output_dir / "ELIGIBLE_RESIDUAL_TRADES.json").write_text(
        json.dumps(_safe(eligible), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RESULT.json").write_text(
        json.dumps(_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result),
        encoding="utf-8",
    )
    combined.to_csv(output_dir / "COMBINED_TRADES.csv", index=False)
    monthly.to_csv(output_dir / "MONTHLY.csv", index=False)


__all__ = [
    "best_removed_profit_factor",
    "evaluate",
    "load_config",
    "portfolio_metrics",
    "profit_factor",
    "replay_exact_candidate",
    "residual_metrics",
    "run",
    "value_metrics",
    "verify_sources",
    "write_outputs",
]
