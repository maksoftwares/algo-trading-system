from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from . import dense_residual_family as dense
from . import frozen_residual_history_diagnostic as base

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT / "config" / "preregistered_compression_own_price_family_v1.json"
)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if (
        config["status"]
        != "PREREGISTERED_REGIME_SPECIALIST_CHRONOLOGICAL_RESEARCH_ONLY"
    ):
        raise RuntimeError("unexpected compression-specialist boundary")
    if config["owned_regime"] != "CROSSPAIR_COMPRESSION":
        raise RuntimeError("compression-specialist regime drift")
    if config["result_can_count_as_forward_evidence"] is not False:
        raise RuntimeError("compression research permits forward credit")
    if config["demo_order_authorized"] is not False:
        raise RuntimeError("compression research permits demo orders")
    if len(config["candidate_rules_in_fixed_order"]) != 6:
        raise RuntimeError("compression candidate family drift")
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
            (
                "frozen_residual_history_config",
                "frozen_residual_history_config",
                "frozen_residual_history_config_sha256",
            ),
            (
                "frozen_residual_history_source",
                "frozen_residual_history_source",
                "frozen_residual_history_source_sha256",
            ),
            (
                "eurusd_m5_bidask",
                "eurusd_m5_bidask",
                "eurusd_m5_bidask_sha256",
            ),
        )
    }
    actual = {name: base.sha256(path) for name, (path, _) in pairs.items()}
    expected = {name: expected for name, (_, expected) in pairs.items()}
    if actual != expected:
        raise RuntimeError(
            f"compression specialist source mismatch: {actual} != {expected}"
        )
    return actual


def load_eurusd_bars(config: dict[str, Any]) -> pd.DataFrame:
    path = _source_path(config["source"]["eurusd_m5_bidask"])
    frame = pd.read_parquet(
        path,
        columns=[
            "timestamp_ms",
            "bid_open",
            "bid_close",
            "ask_open",
            "ask_close",
        ],
    )
    frame["time"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame["mid_open"] = (
        frame["bid_open"].astype(float) + frame["ask_open"].astype(float)
    ) / 2.0
    frame["mid_close"] = (
        frame["bid_close"].astype(float) + frame["ask_close"].astype(float)
    ) / 2.0
    return frame.set_index("time")[["mid_open", "mid_close"]].sort_index()


def completed_return(
    bars: pd.DataFrame,
    decision_time: pd.Timestamp,
    horizon_minutes: int,
) -> float | None:
    opens = pd.date_range(
        decision_time - pd.Timedelta(minutes=horizon_minutes),
        decision_time - pd.Timedelta(minutes=5),
        freq="5min",
        tz="UTC",
    )
    if len(opens) != horizon_minutes // 5:
        raise RuntimeError("invalid compression feature horizon")
    selected = bars.reindex(opens)
    if selected.isna().any().any():
        return None
    start = float(selected.iloc[0]["mid_open"])
    end = float(selected.iloc[-1]["mid_close"])
    if start <= 0.0 or end <= 0.0:
        return None
    return math.log(end / start)


def feature_records(
    records: list[dict[str, Any]],
    bars: pd.DataFrame,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    owned_regime = str(config["owned_regime"])
    horizons = config["mechanism"]["feature_horizons_minutes"]
    output: list[dict[str, Any]] = []
    for record in records:
        if (
            record["status"] != "RESOLVED"
            or record.get("regime") != owned_regime
        ):
            continue
        decision_time = pd.to_datetime(
            record["decision_time_utc"],
            format=dense.TIME_FORMAT,
            utc=True,
        )
        features = {
            f"own_return_{horizon}": completed_return(
                bars,
                decision_time,
                int(horizon),
            )
            for horizon in horizons
        }
        if any(value is None for value in features.values()):
            continue
        output.append({**record, "own_price_features": features})
    return output


def rule_side(rule: dict[str, Any], record: dict[str, Any]) -> str:
    value = float(record["own_price_features"][str(rule["feature"])])
    momentum_long = value >= 0.0
    if rule["orientation"] == "FADE":
        momentum_long = not momentum_long
    return "LONG" if momentum_long else "SHORT"


def rule_values(
    records: list[dict[str, Any]],
    rule: dict[str, Any],
) -> list[float]:
    return [
        dense._record_result(record, rule_side(rule, record))
        for record in records
    ]


def _in_window(
    records: list[dict[str, Any]],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if start <= str(record["decision_date"]) < end
    ]


def development_table(
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> pd.DataFrame:
    start, end = config["windows"]["development"]
    selected = _in_window(records, start, end)
    execution = config["execution_inherited_unchanged"]
    stress_r = float(execution["additional_round_trip_stress_usd"]) / float(
        execution["initial_risk_usd"]
    )
    rows: list[dict[str, Any]] = []
    for index, rule in enumerate(config["candidate_rules_in_fixed_order"]):
        values = rule_values(selected, rule)
        rows.append(
            {
                "rule_id": rule["id"],
                "rule_index": index,
                **dense.metrics(values, len(values), stress_r),
            }
        )
    return pd.DataFrame(rows)


def candidate_passes(
    row: pd.Series | dict[str, Any],
    config: dict[str, Any],
) -> bool:
    gate = config["development_selection"]
    return bool(
        int(row["trades"]) >= int(gate["minimum_observations"])
        and float(row["stressed_profit_factor"])
        >= float(gate["minimum_stressed_profit_factor"])
        and float(row["best_5pct_removed_profit_factor"])
        >= float(
            gate["minimum_best_five_percent_removed_profit_factor"]
        )
        and all(
            float(value)
            >= float(gate["minimum_each_trade_sequence_half_profit_factor"])
            for value in row["trade_sequence_half_profit_factors"]
        )
        and float(row["net"]) > float(gate["minimum_net_r_exclusive"])
    )


def select_rule(
    table: pd.DataFrame,
    config: dict[str, Any],
) -> str | None:
    candidates = table[
        table.apply(lambda row: candidate_passes(row, config), axis=1)
    ].copy()
    if candidates.empty:
        return None
    candidates = candidates.sort_values(
        [
            "stressed_profit_factor",
            "best_5pct_removed_profit_factor",
            "net",
            "rule_index",
        ],
        ascending=[False, False, False, True],
    )
    return str(candidates.iloc[0]["rule_id"])


def trade_frame(
    records: list[dict[str, Any]],
    rule_id: str | None,
    config: dict[str, Any],
) -> pd.DataFrame:
    columns = [
        "entry_time",
        "exit_time",
        "decision_date",
        "component",
        "regime",
        "rule_id",
        "side",
        "outcome",
        "result_r",
        "pnl_usd",
        "stressed_pnl_usd",
    ]
    if rule_id is None:
        return pd.DataFrame(columns=columns)
    rule = next(
        rule
        for rule in config["candidate_rules_in_fixed_order"]
        if rule["id"] == rule_id
    )
    execution = config["execution_inherited_unchanged"]
    risk_usd = float(execution["initial_risk_usd"])
    stress_usd = float(execution["additional_round_trip_stress_usd"])
    rows: list[dict[str, Any]] = []
    for record in records:
        side = rule_side(rule, record)
        outcome = record[f"{side.lower()}_outcome"]
        result_r = float(outcome["result_r"])
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
                "component": "COMPRESSION_OWN_PRICE_RESEARCH",
                "regime": config["owned_regime"],
                "rule_id": rule_id,
                "side": side,
                "outcome": outcome["outcome"],
                "result_r": result_r,
                "pnl_usd": result_r * risk_usd,
                "stressed_pnl_usd": result_r * risk_usd - stress_usd,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def specialist_metrics(
    trades: pd.DataFrame,
    complete_weekdays: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    execution = config["execution_inherited_unchanged"]
    stress_r = float(execution["additional_round_trip_stress_usd"]) / float(
        execution["initial_risk_usd"]
    )
    values = (
        trades["result_r"].astype(float).tolist()
        if not trades.empty
        else []
    )
    result = dense.metrics(values, complete_weekdays, stress_r)
    active = (
        int(trades["decision_date"].nunique()) if not trades.empty else 0
    )
    result["active_weekdays"] = active
    result["weekday_coverage"] = (
        active / complete_weekdays if complete_weekdays else 0.0
    )
    return result


def _validation_checks(
    validation: dict[str, Any],
    latest: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, bool]:
    gate = config["locked_validation_gates"]
    payoff = validation["payoff_ratio"]
    return {
        "minimum_trades": validation["trades"]
        >= int(gate["minimum_trades"]),
        "minimum_trades_per_weekday": validation["trades_per_weekday"]
        >= float(gate["minimum_trades_per_weekday"]),
        "minimum_win_rate": validation["win_rate"]
        >= float(gate["minimum_win_rate"]),
        "maximum_win_rate": validation["win_rate"]
        <= float(gate["maximum_win_rate"]),
        "minimum_payoff_ratio": payoff is not None
        and payoff >= float(gate["minimum_payoff_ratio"]),
        "minimum_profit_factor": validation["profit_factor"]
        >= float(gate["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": validation[
            "stressed_profit_factor"
        ]
        >= float(gate["minimum_stressed_profit_factor"]),
        "minimum_best_removed_profit_factor": validation[
            "best_5pct_removed_profit_factor"
        ]
        >= float(
            gate["minimum_best_five_percent_removed_profit_factor"]
        ),
        "minimum_each_half_profit_factor": all(
            float(value)
            > float(
                gate[
                    "minimum_each_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in validation["trade_sequence_half_profit_factors"]
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
        "minimum_net_r": validation["net"]
        > float(gate["minimum_net_r_exclusive"]),
    }


def evaluate(
    all_records: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    m15: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    table = development_table(feature_rows, config)
    rule_id = select_rule(table, config)
    trades = trade_frame(feature_rows, rule_id, config)
    windows = config["windows"]
    validation_start, validation_end = windows["locked_validation"]
    latest_start, latest_end = windows["latest_12_months"]
    portfolio_start, portfolio_end = windows["combined_broker_window"]
    split = str(windows["combined_broker_split"])
    validation_trades = trades[
        trades["decision_date"].ge(validation_start)
        & trades["decision_date"].lt(validation_end)
    ]
    latest_trades = trades[
        trades["decision_date"].ge(latest_start)
        & trades["decision_date"].lt(latest_end)
    ]
    validation_days = len(
        dense._records_in_window(all_records, validation_start, validation_end)
    )
    latest_days = len(
        dense._records_in_window(all_records, latest_start, latest_end)
    )
    validation = specialist_metrics(
        validation_trades,
        validation_days,
        config,
    )
    latest = specialist_metrics(latest_trades, latest_days, config)
    checks = _validation_checks(validation, latest, config)
    portfolio_days = len(
        dense._records_in_window(all_records, portfolio_start, portfolio_end)
    )
    combined, combined_metrics = dense.combined_portfolio(
        trades,
        m15,
        portfolio_start,
        portfolio_end,
        portfolio_days,
    )
    _, first = dense.combined_portfolio(
        trades,
        m15,
        portfolio_start,
        split,
        len(dense._records_in_window(all_records, portfolio_start, split)),
    )
    _, second = dense.combined_portfolio(
        trades,
        m15,
        split,
        portfolio_end,
        len(dense._records_in_window(all_records, split, portfolio_end)),
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
    selected_development = None
    if rule_id is not None:
        row = table[table["rule_id"].eq(rule_id)].iloc[0]
        selected_development = {
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
    result = {
        "schema_version": config["schema_version"],
        "status": (
            "HISTORICAL_VALIDATION_SUPPORTS_FORWARD_SPECIALIST_REBUILD"
            if rule_id is not None and all(checks.values())
            else "HISTORICAL_VALIDATION_REJECTED"
        ),
        "research_boundary": config["status"],
        "owned_regime": config["owned_regime"],
        "variants_evaluated": len(config["candidate_rules_in_fixed_order"]),
        "selected_rule_id": rule_id,
        "selected_development_metrics": selected_development,
        "feature_complete_owned_records": len(feature_rows),
        "locked_validation": validation,
        "latest_12_months": latest,
        "validation_checks": checks,
        "combined_broker_window": {
            "full": combined_metrics,
            "first_12_months": first,
            "second_12_months": second,
        },
        "result_can_count_as_forward_evidence": False,
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    return result, table, validation_trades.reset_index(drop=True), monthly


def run() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    config = load_config()
    verified = verify_sources(config)
    records, _, _, _ = base.run()
    bars = load_eurusd_bars(config)
    features = feature_records(records, bars, config)
    base_config = base.load_config()
    m15, _ = base.load_m15_trades(base_config)
    result, table, trades, monthly = evaluate(
        records,
        features,
        m15,
        config,
    )
    result["verified_source_sha256"] = verified
    result["compression_config_sha256"] = base.sha256(CONFIG_PATH)
    result["compression_source_sha256"] = base.sha256(Path(__file__))
    return result, table, trades, monthly


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
    validation = result["locked_validation"]
    latest = result["latest_12_months"]
    combined = result["combined_broker_window"]["full"]
    failed = [
        name for name, passed in result["validation_checks"].items() if not passed
    ]
    return "\n".join(
        [
            "# Compression own-price specialist",
            "",
            f"Status: **{result['status']}**",
            "",
            f"Selected development rule: `{result['selected_rule_id']}`",
            "",
            "## Locked specialist validation",
            "",
            "| Metric | Full validation | Latest 12 months |",
            "|---|---:|---:|",
            f"| Trades | {validation['trades']:,} | {latest['trades']:,} |",
            (
                f"| Trades/weekday | {validation['trades_per_weekday']:.4f} | "
                f"{latest['trades_per_weekday']:.4f} |"
            ),
            (
                f"| Win rate | {validation['win_rate']:.2%} | "
                f"{latest['win_rate']:.2%} |"
            ),
            (
                f"| Payoff | {validation['payoff_ratio']} | "
                f"{latest['payoff_ratio']} |"
            ),
            (
                f"| PF | {validation['profit_factor']:.4f} | "
                f"{latest['profit_factor']:.4f} |"
            ),
            (
                f"| Stressed PF | {validation['stressed_profit_factor']:.4f} | "
                f"{latest['stressed_profit_factor']:.4f} |"
            ),
            "",
            "## With protected M15, two-year broker window",
            "",
            f"- Trades: `{combined['trades']}`",
            f"- Trades/weekday: `{combined['trades_per_weekday']:.4f}`",
            f"- PF: `{combined['profit_factor']:.4f}`",
            f"- Stressed PF: `{combined['stressed_profit_factor']:.4f}`",
            f"- Net P&L: `${combined['net']:.2f}`",
            "",
            "Failed specialist gates:",
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
    table: pd.DataFrame,
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
    candidate_output = table.copy()
    candidate_output["trade_sequence_half_profit_factors"] = candidate_output[
        "trade_sequence_half_profit_factors"
    ].map(json.dumps)
    candidate_output.to_csv(
        output_dir / "DEVELOPMENT_CANDIDATES.csv",
        index=False,
    )
    trades.to_csv(output_dir / "VALIDATION_TRADES.csv", index=False)
    monthly.to_csv(output_dir / "MONTHLY.csv", index=False)


__all__ = [
    "candidate_passes",
    "completed_return",
    "development_table",
    "evaluate",
    "feature_records",
    "load_config",
    "load_eurusd_bars",
    "rule_side",
    "run",
    "select_rule",
    "trade_frame",
    "verify_sources",
    "write_outputs",
]
