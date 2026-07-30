from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from . import frozen_residual_history_diagnostic as base

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "preregistered_dense_residual_family_v1.json"
TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if (
        config["status"]
        != "PREREGISTERED_RETROSPECTIVE_CHRONOLOGICAL_RESEARCH_ONLY"
    ):
        raise RuntimeError("unexpected dense residual research boundary")
    if config["result_can_count_as_forward_evidence"] is not False:
        raise RuntimeError("dense residual research permits forward credit")
    if config["demo_order_authorized"] is not False:
        raise RuntimeError("dense residual research permits demo orders")
    if len(config["candidate_rules_in_fixed_order"]) != 12:
        raise RuntimeError("dense residual candidate family drift")
    return config


def _source_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def verify_sources(config: dict[str, Any]) -> dict[str, str]:
    source = config["source"]
    pairs = {
        "frozen_residual_history_config": (
            _source_path(source["frozen_residual_history_config"]),
            source["frozen_residual_history_config_sha256"],
        ),
        "frozen_residual_history_source": (
            _source_path(source["frozen_residual_history_source"]),
            source["frozen_residual_history_source_sha256"],
        ),
    }
    actual = {name: base.sha256(path) for name, (path, _) in pairs.items()}
    expected = {name: expected for name, (_, expected) in pairs.items()}
    if actual != expected:
        raise RuntimeError(
            f"dense residual source mismatch: {actual} != {expected}"
        )
    return actual


def _sign(value: float) -> int:
    return 1 if value > 0.0 else -1 if value < 0.0 else 0


def rule_signal(rule: dict[str, Any], context: dict[str, float]) -> float:
    signal_name = str(rule["signal"])
    if signal_name == "majority_strength_15_60_240":
        signal = float(
            sum(
                _sign(float(context[f"strength_{horizon}"]))
                for horizon in (15, 60, 240)
            )
        )
    else:
        signal = float(context[signal_name])
    if signal == 0.0 and rule.get("zero_tie_break_signal"):
        signal = float(context[str(rule["zero_tie_break_signal"])])
    return signal


def rule_side(rule: dict[str, Any], context: dict[str, float]) -> str:
    momentum_long = rule_signal(rule, context) >= 0.0
    if rule["orientation"] == "FADE":
        momentum_long = not momentum_long
    return "LONG" if momentum_long else "SHORT"


def _record_result(record: dict[str, Any], side: str) -> float:
    outcome = record[f"{side.lower()}_outcome"]
    return float(outcome["result_r"])


def _records_in_window(
    records: list[dict[str, Any]],
    start: str,
    end: str,
    *,
    resolved_only: bool = False,
    regime: str | None = None,
) -> list[dict[str, Any]]:
    selected = [
        record
        for record in records
        if start <= str(record["decision_date"]) < end
    ]
    if resolved_only:
        selected = [
            record for record in selected if record["status"] == "RESOLVED"
        ]
    if regime is not None:
        selected = [
            record for record in selected if record.get("regime") == regime
        ]
    return selected


def rule_values(
    records: list[dict[str, Any]],
    rule: dict[str, Any],
) -> list[float]:
    return [
        _record_result(record, rule_side(rule, record["context"]))
        for record in records
    ]


def metrics(
    values: list[float],
    denominator: int,
    stress_r: float,
) -> dict[str, Any]:
    return base.value_metrics(
        values,
        [value - stress_r for value in values],
        denominator,
    )


def development_candidate_table(
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> pd.DataFrame:
    start, end = config["windows"]["development"]
    stress_r = (
        float(
            config["execution_inherited_unchanged"][
                "additional_round_trip_stress_usd"
            ]
        )
        / float(
            config["execution_inherited_unchanged"]["initial_risk_usd"]
        )
    )
    rows: list[dict[str, Any]] = []
    for regime in config["regimes_in_fixed_order"]:
        regime_records = _records_in_window(
            records,
            start,
            end,
            resolved_only=True,
            regime=regime,
        )
        for rule_index, rule in enumerate(
            config["candidate_rules_in_fixed_order"]
        ):
            values = rule_values(regime_records, rule)
            result = metrics(values, len(values), stress_r)
            rows.append(
                {
                    "regime": regime,
                    "rule_id": rule["id"],
                    "rule_index": rule_index,
                    **result,
                }
            )
    return pd.DataFrame(rows)


def candidate_passes(
    row: pd.Series | dict[str, Any],
    config: dict[str, Any],
) -> bool:
    gate = config["development_selection"]
    halves = row["trade_sequence_half_profit_factors"]
    return bool(
        int(row["trades"])
        >= int(gate["minimum_observations_per_regime_rule"])
        and float(row["stressed_profit_factor"])
        >= float(gate["minimum_stressed_profit_factor"])
        and float(row["best_5pct_removed_profit_factor"])
        >= float(
            gate["minimum_best_five_percent_removed_profit_factor"]
        )
        and all(
            float(value)
            >= float(
                gate["minimum_each_trade_sequence_half_profit_factor"]
            )
            for value in halves
        )
        and float(row["net"]) > float(gate["minimum_net_r_exclusive"])
    )


def select_rules(
    candidate_table: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, str | None]:
    selections: dict[str, str | None] = {}
    for regime in config["regimes_in_fixed_order"]:
        candidates = candidate_table[
            candidate_table["regime"].eq(regime)
        ].copy()
        candidates = candidates[
            candidates.apply(
                lambda row: candidate_passes(row, config),
                axis=1,
            )
        ]
        if candidates.empty:
            selections[regime] = None
            continue
        candidates = candidates.sort_values(
            [
                "stressed_profit_factor",
                "best_5pct_removed_profit_factor",
                "net",
                "rule_index",
            ],
            ascending=[False, False, False, True],
        )
        selections[regime] = str(candidates.iloc[0]["rule_id"])
    return selections


def _rules_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(rule["id"]): rule
        for rule in config["candidate_rules_in_fixed_order"]
    }


def selected_trades(
    records: list[dict[str, Any]],
    selections: dict[str, str | None],
    config: dict[str, Any],
    start: str,
    end: str,
) -> pd.DataFrame:
    rules = _rules_by_id(config)
    risk_usd = float(
        config["execution_inherited_unchanged"]["initial_risk_usd"]
    )
    stress_usd = float(
        config["execution_inherited_unchanged"][
            "additional_round_trip_stress_usd"
        ]
    )
    rows: list[dict[str, Any]] = []
    for record in _records_in_window(
        records,
        start,
        end,
        resolved_only=True,
    ):
        regime = str(record["regime"])
        rule_id = selections.get(regime)
        if rule_id is None:
            continue
        rule = rules[rule_id]
        side = rule_side(rule, record["context"])
        outcome = record[f"{side.lower()}_outcome"]
        result_r = float(outcome["result_r"])
        rows.append(
            {
                "entry_time": pd.to_datetime(
                    record["decision_time_utc"],
                    format=TIME_FORMAT,
                    utc=True,
                ),
                "exit_time": pd.to_datetime(
                    outcome["exit_time"],
                    format=TIME_FORMAT,
                    utc=True,
                ),
                "decision_date": str(record["decision_date"]),
                "component": "DENSE_RESIDUAL_RESEARCH",
                "regime": regime,
                "rule_id": rule_id,
                "side": side,
                "outcome": outcome["outcome"],
                "result_r": result_r,
                "pnl_usd": result_r * risk_usd,
                "stressed_pnl_usd": result_r * risk_usd - stress_usd,
            }
        )
    return pd.DataFrame(rows)


def residual_metrics(
    trades: pd.DataFrame,
    records: list[dict[str, Any]],
    start: str,
    end: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    denominator = len(_records_in_window(records, start, end))
    window_trades = (
        trades[
            trades["decision_date"].ge(start)
            & trades["decision_date"].lt(end)
        ]
        if not trades.empty
        else trades
    )
    stress_r = (
        float(
            config["execution_inherited_unchanged"][
                "additional_round_trip_stress_usd"
            ]
        )
        / float(
            config["execution_inherited_unchanged"]["initial_risk_usd"]
        )
    )
    values = (
        window_trades["result_r"].astype(float).tolist()
        if not window_trades.empty
        else []
    )
    result = metrics(values, denominator, stress_r)
    active = (
        int(window_trades["decision_date"].nunique())
        if not window_trades.empty
        else 0
    )
    result.update(
        {
            "complete_weekdays": denominator,
            "active_weekdays": active,
            "weekday_coverage": active / denominator if denominator else 0.0,
        }
    )
    return result


def _empty_trade_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "entry_time",
            "exit_time",
            "decision_date",
            "component",
            "side",
            "pnl_usd",
            "stressed_pnl_usd",
        ]
    )


def combined_portfolio(
    residual_trades: pd.DataFrame,
    m15: pd.DataFrame,
    start: str,
    end: str,
    denominator: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    residual = (
        residual_trades[
            residual_trades["decision_date"].ge(start)
            & residual_trades["decision_date"].lt(end)
        ].copy()
        if not residual_trades.empty
        else _empty_trade_frame()
    )
    protected = m15[
        m15["decision_date"].ge(start) & m15["decision_date"].lt(end)
    ].copy()
    overlap = len(
        set(residual["decision_date"]) & set(protected["decision_date"])
    )
    combined = pd.concat(
        [
            protected[
                [
                    "entry_time",
                    "exit_time",
                    "decision_date",
                    "component",
                    "side",
                    "pnl_usd",
                    "stressed_pnl_usd",
                ]
            ],
            residual[
                [
                    "entry_time",
                    "exit_time",
                    "decision_date",
                    "component",
                    "side",
                    "pnl_usd",
                    "stressed_pnl_usd",
                ]
            ],
        ],
        ignore_index=True,
    )
    if not combined.empty:
        combined = combined.sort_values(
            ["entry_time", "component"]
        ).reset_index(drop=True)
    result = base.portfolio_metrics(combined, denominator)
    result["m15_residual_owned_date_overlaps"] = overlap
    return combined, result


def _gate_checks(
    residual: dict[str, Any],
    combined: dict[str, Any],
    latest: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, bool]:
    gate = config["locked_validation_gates"]
    payoff = combined["payoff_ratio"]
    return {
        "minimum_residual_trades": residual["trades"]
        >= int(gate["minimum_residual_trades"]),
        "minimum_residual_trades_per_weekday": residual[
            "trades_per_weekday"
        ]
        >= float(gate["minimum_residual_trades_per_weekday"]),
        "minimum_residual_profit_factor": residual["profit_factor"]
        >= float(gate["minimum_residual_profit_factor"]),
        "minimum_residual_stressed_profit_factor": residual[
            "stressed_profit_factor"
        ]
        >= float(gate["minimum_residual_stressed_profit_factor"]),
        "minimum_residual_best_removed_profit_factor": residual[
            "best_5pct_removed_profit_factor"
        ]
        >= float(
            gate[
                "minimum_residual_best_five_percent_removed_profit_factor"
            ]
        ),
        "minimum_each_residual_half_profit_factor": all(
            float(value)
            > float(
                gate[
                    "minimum_each_residual_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in residual["trade_sequence_half_profit_factors"]
        ),
        "minimum_combined_trades_per_weekday": combined[
            "trades_per_weekday"
        ]
        >= float(gate["minimum_combined_trades_per_weekday"]),
        "maximum_combined_trades_per_weekday": combined[
            "trades_per_weekday"
        ]
        <= float(gate["maximum_combined_trades_per_weekday"]),
        "minimum_combined_weekday_coverage": combined["weekday_coverage"]
        >= float(gate["minimum_combined_weekday_coverage"]),
        "minimum_combined_win_rate": combined["win_rate"]
        >= float(gate["minimum_combined_win_rate"]),
        "maximum_combined_win_rate": combined["win_rate"]
        <= float(gate["maximum_combined_win_rate"]),
        "minimum_combined_payoff_ratio": payoff is not None
        and payoff >= float(gate["minimum_combined_payoff_ratio"]),
        "minimum_combined_profit_factor": combined["profit_factor"]
        >= float(gate["minimum_combined_profit_factor"]),
        "minimum_combined_stressed_profit_factor": combined[
            "stressed_profit_factor"
        ]
        >= float(gate["minimum_combined_stressed_profit_factor"]),
        "minimum_combined_best_removed_profit_factor": combined[
            "best_5pct_removed_profit_factor"
        ]
        >= float(
            gate[
                "minimum_combined_best_five_percent_removed_profit_factor"
            ]
        ),
        "minimum_each_combined_half_profit_factor": all(
            float(value)
            > float(
                gate[
                    "minimum_each_combined_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in combined["trade_sequence_half_profit_factors"]
        ),
        "minimum_latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gate["minimum_latest_12_month_profit_factor"]),
        "minimum_latest_12_month_best_removed_profit_factor": latest[
            "best_5pct_removed_profit_factor"
        ]
        >= float(
            gate[
                "minimum_latest_12_month_best_five_percent_removed_profit_factor"
            ]
        ),
        "minimum_net_pnl_usd": combined["net"]
        > float(gate["minimum_net_pnl_usd_exclusive"]),
        "zero_m15_residual_owned_date_overlap": combined[
            "m15_residual_owned_date_overlaps"
        ]
        == 0,
    }


def _selection_details(
    candidate_table: pd.DataFrame,
    selections: dict[str, str | None],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for regime, rule_id in selections.items():
        detail: dict[str, Any] = {"selected_rule_id": rule_id}
        if rule_id is not None:
            row = candidate_table[
                candidate_table["regime"].eq(regime)
                & candidate_table["rule_id"].eq(rule_id)
            ].iloc[0]
            detail["development_metrics"] = {
                key: row[key]
                for key in (
                    "trades",
                    "net",
                    "win_rate",
                    "payoff_ratio",
                    "profit_factor",
                    "stressed_profit_factor",
                    "best_5pct_removed_profit_factor",
                    "trade_sequence_half_profit_factors",
                )
            }
        result[regime] = detail
    return result


def evaluate(
    records: list[dict[str, Any]],
    m15: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidate_table = development_candidate_table(records, config)
    selections = select_rules(candidate_table, config)
    validation_start, validation_end = config["windows"][
        "locked_validation"
    ]
    portfolio_start, portfolio_end = config["windows"][
        "combined_broker_window"
    ]
    latest_start, latest_end = config["windows"]["latest_12_months"]
    split = str(config["windows"]["combined_broker_split"])
    validation_trades = selected_trades(
        records,
        selections,
        config,
        validation_start,
        validation_end,
    )
    validation_metrics = residual_metrics(
        validation_trades,
        records,
        validation_start,
        validation_end,
        config,
    )
    portfolio_residual_metrics = residual_metrics(
        validation_trades,
        records,
        portfolio_start,
        portfolio_end,
        config,
    )
    portfolio_denominator = len(
        _records_in_window(records, portfolio_start, portfolio_end)
    )
    half_one_denominator = len(
        _records_in_window(records, portfolio_start, split)
    )
    half_two_denominator = len(
        _records_in_window(records, split, portfolio_end)
    )
    combined, combined_metrics = combined_portfolio(
        validation_trades,
        m15,
        portfolio_start,
        portfolio_end,
        portfolio_denominator,
    )
    _, first_metrics = combined_portfolio(
        validation_trades,
        m15,
        portfolio_start,
        split,
        half_one_denominator,
    )
    _, second_metrics = combined_portfolio(
        validation_trades,
        m15,
        split,
        portfolio_end,
        half_two_denominator,
    )
    _, latest_metrics = combined_portfolio(
        validation_trades,
        m15,
        latest_start,
        latest_end,
        len(_records_in_window(records, latest_start, latest_end)),
    )
    protected_window = m15[
        m15["decision_date"].ge(portfolio_start)
        & m15["decision_date"].lt(portfolio_end)
    ]
    protected_metrics = base.portfolio_metrics(
        protected_window,
        portfolio_denominator,
    )
    checks = _gate_checks(
        validation_metrics,
        combined_metrics,
        latest_metrics,
        config,
    )
    monthly = (
        combined.assign(month=combined["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")
        .agg(
            trades=("pnl_usd", "size"),
            pnl_usd=("pnl_usd", "sum"),
            stressed_pnl_usd=("stressed_pnl_usd", "sum"),
        )
        .reset_index()
        if not combined.empty
        else pd.DataFrame(
            columns=["month", "trades", "pnl_usd", "stressed_pnl_usd"]
        )
    )
    result = {
        "schema_version": config["schema_version"],
        "status": (
            "HISTORICAL_VALIDATION_SUPPORTS_FORWARD_REBUILD"
            if all(checks.values())
            else "HISTORICAL_VALIDATION_REJECTED"
        ),
        "research_boundary": config["status"],
        "variants_evaluated": len(
            config["candidate_rules_in_fixed_order"]
        ),
        "selection_uses_locked_validation": False,
        "selected_regime_experts": _selection_details(
            candidate_table,
            selections,
        ),
        "locked_validation_residual": validation_metrics,
        "combined_broker_window": {
            "full": combined_metrics,
            "first_12_months": first_metrics,
            "second_12_months": second_metrics,
            "latest_12_months": latest_metrics,
            "components": {
                "M15_REGIME": protected_metrics,
                "DENSE_RESIDUAL_RESEARCH": portfolio_residual_metrics,
            },
            "checks": checks,
        },
        "result_can_count_as_forward_evidence": False,
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    return result, candidate_table, validation_trades, monthly


def run() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    config = load_config()
    verified_sources = verify_sources(config)
    records, _, _, _ = base.run()
    base_config = base.load_config()
    m15, _ = base.load_m15_trades(base_config)
    result, candidates, trades, monthly = evaluate(records, m15, config)
    result["verified_source_sha256"] = verified_sources
    result["dense_family_config_sha256"] = base.sha256(CONFIG_PATH)
    result["dense_family_source_sha256"] = base.sha256(Path(__file__))
    return result, candidates, trades, monthly


def _safe(value: Any) -> Any:
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return _safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def _candidate_output(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if "trade_sequence_half_profit_factors" in output:
        output["trade_sequence_half_profit_factors"] = output[
            "trade_sequence_half_profit_factors"
        ].map(json.dumps)
    return output


def render_report(result: dict[str, Any]) -> str:
    residual = result["locked_validation_residual"]
    combined = result["combined_broker_window"]["full"]
    latest = result["combined_broker_window"]["latest_12_months"]
    failed = [
        name
        for name, passed in result["combined_broker_window"][
            "checks"
        ].items()
        if not passed
    ]
    experts = [
        f"- `{regime}`: `{detail['selected_rule_id'] or 'CASH'}`"
        for regime, detail in result["selected_regime_experts"].items()
    ]
    return "\n".join(
        [
            "# Preregistered dense residual family",
            "",
            f"Status: **{result['status']}**",
            "",
            "Development selected one deterministic rule per causal regime.",
            "Locked validation did not participate in selection. This remains",
            "retrospective research and cannot authorize a demo order.",
            "",
            "## Selected regime experts",
            "",
            *experts,
            "",
            "## Locked residual validation",
            "",
            "| Metric | Result |",
            "|---|---:|",
            f"| Trades | {residual['trades']:,} |",
            f"| Trades/weekday | {residual['trades_per_weekday']:.4f} |",
            f"| Win rate | {residual['win_rate']:.2%} |",
            f"| Payoff | {residual['payoff_ratio']} |",
            f"| PF | {residual['profit_factor']:.4f} |",
            f"| Stressed PF | {residual['stressed_profit_factor']:.4f} |",
            (
                "| Best-5%-removed PF | "
                f"{residual['best_5pct_removed_profit_factor']:.4f} |"
            ),
            "",
            "## Protected M15 plus dense residual",
            "",
            "| Metric | Two years | Latest 12 months |",
            "|---|---:|---:|",
            f"| Trades | {combined['trades']:,} | {latest['trades']:,} |",
            (
                f"| Trades/weekday | {combined['trades_per_weekday']:.4f} | "
                f"{latest['trades_per_weekday']:.4f} |"
            ),
            (
                f"| Weekday coverage | {combined['weekday_coverage']:.2%} | "
                f"{latest['weekday_coverage']:.2%} |"
            ),
            (
                f"| Win rate | {combined['win_rate']:.2%} | "
                f"{latest['win_rate']:.2%} |"
            ),
            (
                f"| Payoff | {combined['payoff_ratio']} | "
                f"{latest['payoff_ratio']} |"
            ),
            (
                f"| PF | {combined['profit_factor']:.4f} | "
                f"{latest['profit_factor']:.4f} |"
            ),
            (
                f"| Stressed PF | {combined['stressed_profit_factor']:.4f} | "
                f"{latest['stressed_profit_factor']:.4f} |"
            ),
            f"| Net P&L | ${combined['net']:.2f} | ${latest['net']:.2f} |",
            "",
            "Failed gates:",
            "",
            *([f"- `{name}`" for name in failed] or ["- None"]),
            "",
            "Forward-evidence credit: `false`.",
            "",
            "Demo-order authorization: `false`.",
            "",
        ]
    )


def write_outputs(
    result: dict[str, Any],
    candidates: pd.DataFrame,
    trades: pd.DataFrame,
    monthly: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "RESULT.json").write_text(
        json.dumps(_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result),
        encoding="utf-8",
    )
    _candidate_output(candidates).to_csv(
        output_dir / "DEVELOPMENT_CANDIDATES.csv",
        index=False,
    )
    trades.to_csv(output_dir / "VALIDATION_TRADES.csv", index=False)
    monthly.to_csv(output_dir / "MONTHLY.csv", index=False)


__all__ = [
    "candidate_passes",
    "combined_portfolio",
    "development_candidate_table",
    "evaluate",
    "load_config",
    "metrics",
    "residual_metrics",
    "rule_side",
    "rule_signal",
    "run",
    "select_rules",
    "selected_trades",
    "verify_sources",
    "write_outputs",
]
