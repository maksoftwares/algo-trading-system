from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from . import dense_residual_family as dense
from . import frozen_residual_history_diagnostic as base

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT / "config" / "preregistered_online_dense_residual_router_v1.json"
)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["status"] != "PREREGISTERED_CAUSAL_HISTORICAL_RESEARCH_ONLY":
        raise RuntimeError("unexpected online residual research boundary")
    if config["result_can_count_as_forward_evidence"] is not False:
        raise RuntimeError("online residual research permits forward credit")
    if config["demo_order_authorized"] is not False:
        raise RuntimeError("online residual research permits demo orders")
    router = config["online_router"]
    if router["current_day_outcome_may_enter_current_selection"] is not False:
        raise RuntimeError("online router permits current-outcome leakage")
    if router["no_cash_after_context_and_path_resolve"] is not True:
        raise RuntimeError("online router is not the preregistered dense test")
    return config


def _source_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def verify_sources(config: dict[str, Any]) -> dict[str, str]:
    source = config["source"]
    pairs = {
        "dense_family_config": (
            _source_path(source["dense_family_config"]),
            source["dense_family_config_sha256"],
        ),
        "dense_family_source": (
            _source_path(source["dense_family_source"]),
            source["dense_family_source_sha256"],
        ),
    }
    actual = {name: base.sha256(path) for name, (path, _) in pairs.items()}
    expected = {name: expected for name, (_, expected) in pairs.items()}
    if actual != expected:
        raise RuntimeError(
            f"online residual source mismatch: {actual} != {expected}"
        )
    return actual


def _stressed_profit_factor(values: list[float], stress_r: float) -> float:
    return base.profit_factor([value - stress_r for value in values])


def rule_statistics(
    values: list[float],
    config: dict[str, Any],
    stress_r: float,
) -> dict[str, float | int]:
    router = config["online_router"]
    window = int(router["recent_window_observations_per_rule"])
    prior = float(router["zero_expectancy_prior_strength"])
    recent = values[-window:]
    stressed = [value - stress_r for value in recent]
    return {
        "observations": len(values),
        "window_observations": len(recent),
        "shrunk_stressed_mean_r": sum(stressed) / (len(stressed) + prior),
        "stressed_profit_factor": _stressed_profit_factor(recent, stress_r),
    }


def select_rule(
    histories: dict[str, list[float]],
    rules: list[dict[str, Any]],
    config: dict[str, Any],
    stress_r: float,
) -> tuple[dict[str, Any], dict[str, dict[str, float | int]], str]:
    router = config["online_router"]
    statistics = {
        str(rule["id"]): rule_statistics(
            histories[str(rule["id"])],
            config,
            stress_r,
        )
        for rule in rules
    }
    prior_observations = len(histories[str(rules[0]["id"])])
    if prior_observations < int(
        router["minimum_prior_regime_observations_before_routing"]
    ):
        warmup_id = str(router["warmup_rule_id"])
        chosen = next(rule for rule in rules if rule["id"] == warmup_id)
        return chosen, statistics, "FIXED_WARMUP_RULE"
    indexed = list(enumerate(rules))
    _, chosen = max(
        indexed,
        key=lambda item: (
            float(
                statistics[str(item[1]["id"])]["shrunk_stressed_mean_r"]
            ),
            float(
                statistics[str(item[1]["id"])]["stressed_profit_factor"]
            ),
            -item[0],
        ),
    )
    return chosen, statistics, "PRIOR_OUTCOME_ROUTER"


def online_trades(
    records: list[dict[str, Any]],
    config: dict[str, Any],
    dense_config: dict[str, Any],
) -> pd.DataFrame:
    rules = list(dense_config["candidate_rules_in_fixed_order"])
    regimes = list(dense_config["regimes_in_fixed_order"])
    histories: dict[str, dict[str, list[float]]] = {
        regime: {str(rule["id"]): [] for rule in rules}
        for regime in regimes
    }
    execution = dense_config["execution_inherited_unchanged"]
    risk_usd = float(execution["initial_risk_usd"])
    stress_usd = float(execution["additional_round_trip_stress_usd"])
    stress_r = stress_usd / risk_usd
    rows: list[dict[str, Any]] = []
    ordered = sorted(records, key=lambda record: record["decision_date"])
    for record in ordered:
        if record["status"] != "RESOLVED":
            continue
        regime = str(record["regime"])
        chosen, statistics, reason = select_rule(
            histories[regime],
            rules,
            config,
            stress_r,
        )
        rule_id = str(chosen["id"])
        side = dense.rule_side(chosen, record["context"])
        outcome = record[f"{side.lower()}_outcome"]
        result_r = float(outcome["result_r"])
        chosen_stats = statistics[rule_id]
        rows.append(
            {
                "entry_time": pd.to_datetime(
                    record["decision_time_utc"],
                    format=dense.TIME_FORMAT,
                    utc=True,
                ),
                "exit_time": pd.to_datetime(
                    outcome["exit_time"],
                    format=dense.TIME_FORMAT,
                    utc=True,
                ),
                "decision_date": str(record["decision_date"]),
                "component": "ONLINE_DENSE_RESIDUAL_RESEARCH",
                "regime": regime,
                "rule_id": rule_id,
                "selection_reason": reason,
                "prior_regime_observations": int(
                    chosen_stats["observations"]
                ),
                "selection_score": float(
                    chosen_stats["shrunk_stressed_mean_r"]
                ),
                "selection_stressed_profit_factor": float(
                    chosen_stats["stressed_profit_factor"]
                ),
                "side": side,
                "outcome": outcome["outcome"],
                "result_r": result_r,
                "pnl_usd": result_r * risk_usd,
                "stressed_pnl_usd": result_r * risk_usd - stress_usd,
            }
        )
        for rule in rules:
            shadow_side = dense.rule_side(rule, record["context"])
            histories[regime][str(rule["id"])].append(
                dense._record_result(record, shadow_side)
            )
    return pd.DataFrame(rows)


def _selection_diagnostics(
    trades: pd.DataFrame,
    dense_config: dict[str, Any],
    start: str,
    end: str,
) -> dict[str, Any]:
    selected = trades[
        trades["decision_date"].ge(start)
        & trades["decision_date"].lt(end)
    ]
    result: dict[str, Any] = {}
    for regime in dense_config["regimes_in_fixed_order"]:
        frame = selected[selected["regime"].eq(regime)]
        rule_counts = Counter(frame["rule_id"].astype(str).tolist())
        changes = (
            int((frame["rule_id"] != frame["rule_id"].shift()).sum() - 1)
            if not frame.empty
            else 0
        )
        result[regime] = {
            "trades": len(frame),
            "rule_changes": max(changes, 0),
            "rule_trade_counts": dict(sorted(rule_counts.items())),
        }
    return result


def evaluate(
    records: list[dict[str, Any]],
    m15: pd.DataFrame,
    config: dict[str, Any],
    dense_config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    trades = online_trades(records, config, dense_config)
    windows = dense_config["windows"]
    validation_start, validation_end = windows["locked_validation"]
    portfolio_start, portfolio_end = windows["combined_broker_window"]
    latest_start, latest_end = windows["latest_12_months"]
    split = str(windows["combined_broker_split"])
    validation_metrics = dense.residual_metrics(
        trades,
        records,
        validation_start,
        validation_end,
        dense_config,
    )
    portfolio_residual = dense.residual_metrics(
        trades,
        records,
        portfolio_start,
        portfolio_end,
        dense_config,
    )
    portfolio_days = len(
        dense._records_in_window(records, portfolio_start, portfolio_end)
    )
    first_days = len(
        dense._records_in_window(records, portfolio_start, split)
    )
    second_days = len(
        dense._records_in_window(records, split, portfolio_end)
    )
    latest_days = len(
        dense._records_in_window(records, latest_start, latest_end)
    )
    combined, combined_metrics = dense.combined_portfolio(
        trades,
        m15,
        portfolio_start,
        portfolio_end,
        portfolio_days,
    )
    _, first_metrics = dense.combined_portfolio(
        trades,
        m15,
        portfolio_start,
        split,
        first_days,
    )
    _, second_metrics = dense.combined_portfolio(
        trades,
        m15,
        split,
        portfolio_end,
        second_days,
    )
    _, latest_metrics = dense.combined_portfolio(
        trades,
        m15,
        latest_start,
        latest_end,
        latest_days,
    )
    protected = m15[
        m15["decision_date"].ge(portfolio_start)
        & m15["decision_date"].lt(portfolio_end)
    ]
    protected_metrics = base.portfolio_metrics(protected, portfolio_days)
    checks = dense._gate_checks(
        validation_metrics,
        combined_metrics,
        latest_metrics,
        dense_config,
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
    )
    result = {
        "schema_version": config["schema_version"],
        "status": (
            "HISTORICAL_VALIDATION_SUPPORTS_FORWARD_REBUILD"
            if all(checks.values())
            else "HISTORICAL_VALIDATION_REJECTED"
        ),
        "research_boundary": config["status"],
        "router_variants_evaluated": 1,
        "online_selection_uses_current_outcome": False,
        "locked_validation_residual": validation_metrics,
        "locked_validation_router_activity": _selection_diagnostics(
            trades,
            dense_config,
            validation_start,
            validation_end,
        ),
        "combined_broker_window": {
            "full": combined_metrics,
            "first_12_months": first_metrics,
            "second_12_months": second_metrics,
            "latest_12_months": latest_metrics,
            "components": {
                "M15_REGIME": protected_metrics,
                "ONLINE_DENSE_RESIDUAL_RESEARCH": portfolio_residual,
            },
            "checks": checks,
        },
        "result_can_count_as_forward_evidence": False,
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    validation_trades = trades[
        trades["decision_date"].ge(validation_start)
        & trades["decision_date"].lt(validation_end)
    ].reset_index(drop=True)
    return result, validation_trades, monthly


def run() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    config = load_config()
    verified = verify_sources(config)
    dense_config = dense.load_config()
    records, _, _, _ = base.run()
    base_config = base.load_config()
    m15, _ = base.load_m15_trades(base_config)
    result, trades, monthly = evaluate(
        records,
        m15,
        config,
        dense_config,
    )
    result["verified_source_sha256"] = verified
    result["online_router_config_sha256"] = base.sha256(CONFIG_PATH)
    result["online_router_source_sha256"] = base.sha256(Path(__file__))
    return result, trades, monthly


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
    return "\n".join(
        [
            "# Online dense residual regime router",
            "",
            f"Status: **{result['status']}**",
            "",
            "The router used only completed prior outcomes in the same causal",
            "regime. The current outcome entered history after selection.",
            "This is retrospective research and cannot authorize an order.",
            "",
            "## Locked residual validation",
            "",
            "| Metric | Result |",
            "|---|---:|",
            f"| Trades | {residual['trades']:,} |",
            f"| Trades/weekday | {residual['trades_per_weekday']:.4f} |",
            f"| Weekday coverage | {residual['weekday_coverage']:.2%} |",
            f"| Win rate | {residual['win_rate']:.2%} |",
            f"| Payoff | {residual['payoff_ratio']} |",
            f"| PF | {residual['profit_factor']:.4f} |",
            f"| Stressed PF | {residual['stressed_profit_factor']:.4f} |",
            (
                "| Best-5%-removed PF | "
                f"{residual['best_5pct_removed_profit_factor']:.4f} |"
            ),
            "",
            "## Protected M15 plus online residual",
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
    trades.to_csv(output_dir / "VALIDATION_TRADES.csv", index=False)
    monthly.to_csv(output_dir / "MONTHLY.csv", index=False)


__all__ = [
    "evaluate",
    "load_config",
    "online_trades",
    "rule_statistics",
    "run",
    "select_rule",
    "verify_sources",
    "write_outputs",
]
