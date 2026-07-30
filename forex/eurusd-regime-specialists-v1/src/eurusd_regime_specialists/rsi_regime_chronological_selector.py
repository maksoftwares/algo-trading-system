from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from . import frequency_edge_frontier as metrics

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT / "config" / "preregistered_rsi_regime_chronological_selector_v1.json"
)
M15_TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if (
        config["status"]
        != "PREREGISTERED_CHRONOLOGICAL_REGIME_SELECTION_RESEARCH_ONLY"
    ):
        raise RuntimeError("unexpected RSI regime-selector boundary")
    if config["result_can_count_as_forward_evidence"] is not False:
        raise RuntimeError("RSI regime selector permits forward credit")
    if config["demo_order_authorized"] is not False:
        raise RuntimeError("RSI regime selector permits demo orders")
    if len(config["rsi_contract"]["regimes_in_fixed_order"]) != 5:
        raise RuntimeError("RSI causal-regime family drift")
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
                "rsi_trade_ledger",
                "rsi_trade_ledger",
                "rsi_trade_ledger_sha256",
            ),
            (
                "protected_m15_trade_ledger",
                "protected_m15_trade_ledger",
                "protected_m15_trade_ledger_sha256",
            ),
            (
                "metric_source",
                "metric_source",
                "metric_source_sha256",
            ),
        )
    }
    actual = {
        name: metrics.sha256(path) for name, (path, _) in pairs.items()
    }
    expected = {name: expected for name, (_, expected) in pairs.items()}
    if actual != expected:
        raise RuntimeError(
            f"RSI regime-selector source mismatch: {actual} != {expected}"
        )
    return actual


def load_sources(
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = config["source"]
    start = pd.Timestamp(config["period"]["from_inclusive"])
    end = pd.Timestamp(config["period"]["to_exclusive"])
    contract = config["rsi_contract"]
    fixed_lot = float(contract["fixed_lot"])
    rsi = pd.read_csv(
        _source_path(source["rsi_trade_ledger"]),
        parse_dates=["entry_time", "exit_time"],
    )
    rsi = rsi[
        rsi["sleeve"].eq(contract["sleeve"])
        & rsi["entry_time"].ge(start)
        & rsi["entry_time"].lt(end)
        & ~rsi["quarantined"].astype(bool)
    ].copy()
    rsi["pnl_usd"] = (
        rsi["net_pnl_usd"].astype(float)
        * fixed_lot
        / rsi["volume"].astype(float)
    )
    rsi["component"] = "RSI_REGIME_RESEARCH"
    rsi = rsi.sort_values(["entry_time", "exit_time"]).reset_index(drop=True)

    protected = pd.read_csv(
        _source_path(source["protected_m15_trade_ledger"])
    )
    for column in ("entry_time", "exit_time"):
        protected[column] = pd.to_datetime(
            protected[column],
            format=M15_TIME_FORMAT,
            utc=True,
        )
    protected = protected[
        protected["entry_time"].ge(start)
        & protected["entry_time"].lt(end)
    ].copy()
    protected["pnl_usd"] = (
        protected["profit"].astype(float)
        * fixed_lot
        / protected["volume"].astype(float)
    )
    protected["component"] = "M15_REGIME"
    protected["side"] = "SHORT"
    protected = protected[
        ["entry_time", "exit_time", "component", "side", "pnl_usd"]
    ].sort_values(["entry_time", "exit_time"])
    return rsi, protected.reset_index(drop=True)


def sequence_half_profit_factors(frame: pd.DataFrame) -> list[float]:
    ordered = frame.sort_values(["exit_time", "entry_time"])
    split = len(ordered) // 2
    return [
        metrics.profit_factor(part["pnl_usd"])
        for part in (ordered.iloc[:split], ordered.iloc[split:])
    ]


def regime_metrics(
    frame: pd.DataFrame,
    denominator: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    extra_cost = (
        float(config["stress"]["extra_round_trip_pips"])
        * float(config["stress"]["usd_per_pip_at_0_01_lot"])
    )
    result = metrics.outcome_metrics(frame, denominator, extra_cost)
    result["trade_sequence_half_profit_factors"] = (
        sequence_half_profit_factors(frame)
    )
    return result


def development_table(
    rsi: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    start, end = (
        pd.Timestamp(value) for value in config["period"]["development"]
    )
    development = rsi[
        rsi["entry_time"].ge(start) & rsi["entry_time"].lt(end)
    ]
    denominator = int(config["period"]["development_weekdays"])
    rows: list[dict[str, Any]] = []
    for index, regime in enumerate(
        config["rsi_contract"]["regimes_in_fixed_order"]
    ):
        frame = development[development["causal_regime"].eq(regime)]
        rows.append(
            {
                "causal_regime": regime,
                "regime_index": index,
                **regime_metrics(frame, denominator, config),
            }
        )
    return pd.DataFrame(rows)


def development_row_passes(
    row: pd.Series | dict[str, Any],
    config: dict[str, Any],
) -> bool:
    gate = config["development_regime_admission"]
    return bool(
        int(row["trades"]) >= int(gate["minimum_trades"])
        and float(row["profit_factor"])
        >= float(gate["minimum_profit_factor"])
        and float(row["plus_0_5_pip_profit_factor"])
        >= float(gate["minimum_plus_0_5_pip_profit_factor"])
        and float(row["top_5pct_removed_profit_factor"])
        >= float(
            gate["minimum_best_five_percent_removed_profit_factor"]
        )
        and all(
            float(value)
            >= float(gate["minimum_each_trade_sequence_half_profit_factor"])
            for value in row["trade_sequence_half_profit_factors"]
        )
        and float(row["net_pnl_usd"])
        > float(gate["minimum_net_pnl_usd_exclusive"])
    )


def select_regimes(
    table: pd.DataFrame,
    config: dict[str, Any],
) -> list[str]:
    return [
        str(row["causal_regime"])
        for _, row in table.sort_values("regime_index").iterrows()
        if development_row_passes(row, config)
    ]


def _validation_frame(
    frame: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    start, end = (
        pd.Timestamp(value)
        for value in config["period"]["locked_validation"]
    )
    return frame[
        frame["entry_time"].ge(start) & frame["entry_time"].lt(end)
    ].copy()


def validation_regime_checks(
    selected_rsi: pd.DataFrame,
    selected_regimes: list[str],
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    denominator = int(config["period"]["locked_validation_weekdays"])
    gate = config["locked_validation_regime_gates"]
    results: dict[str, Any] = {}
    checks: dict[str, bool] = {}
    for regime in selected_regimes:
        result = regime_metrics(
            selected_rsi[selected_rsi["causal_regime"].eq(regime)],
            denominator,
            config,
        )
        results[regime] = result
        checks[f"{regime}_minimum_trades"] = result["trades"] >= int(
            gate["minimum_trades_each_selected_regime"]
        )
        checks[f"{regime}_minimum_profit_factor"] = result[
            "profit_factor"
        ] >= float(gate["minimum_profit_factor_each_selected_regime"])
        checks[f"{regime}_minimum_stressed_profit_factor"] = result[
            "plus_0_5_pip_profit_factor"
        ] >= float(
            gate[
                "minimum_plus_0_5_pip_profit_factor_each_selected_regime"
            ]
        )
    return results, checks


def portfolio_checks(
    result: dict[str, Any],
    combined: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, bool]:
    gate = config["locked_validation_portfolio_gates"]
    payoff = result["payoff_ratio"]
    same_entry = combined.groupby("entry_time").size()
    return {
        "minimum_trades_per_weekday": result["trades_per_weekday"]
        >= float(gate["minimum_trades_per_weekday"]),
        "maximum_trades_per_weekday": result["trades_per_weekday"]
        <= float(gate["maximum_trades_per_weekday"]),
        "minimum_weekday_coverage": result["weekday_coverage"]
        >= float(gate["minimum_weekday_coverage"]),
        "minimum_win_rate": result["win_rate"]
        >= float(gate["minimum_win_rate"]),
        "maximum_win_rate": result["win_rate"]
        <= float(gate["maximum_win_rate"]),
        "minimum_payoff_ratio": payoff is not None
        and payoff >= float(gate["minimum_payoff_ratio"]),
        "minimum_profit_factor": result["profit_factor"]
        >= float(gate["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": result[
            "plus_0_5_pip_profit_factor"
        ]
        >= float(gate["minimum_plus_0_5_pip_profit_factor"]),
        "minimum_best_removed_profit_factor": result[
            "top_5pct_removed_profit_factor"
        ]
        >= float(
            gate["minimum_best_five_percent_removed_profit_factor"]
        ),
        "minimum_net_pnl_usd": result["net_pnl_usd"]
        > float(gate["minimum_net_pnl_usd_exclusive"]),
        "maximum_concurrent_positions": metrics._maximum_concurrency(combined)
        <= int(gate["maximum_concurrent_positions"]),
        "maximum_same_entry_overlap_timestamps": int((same_entry > 1).sum())
        <= int(gate["maximum_same_entry_overlap_timestamps"]),
    }


def evaluate(
    rsi: pd.DataFrame,
    protected: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    table = development_table(rsi, config)
    selected_regimes = select_regimes(table, config)
    validation_rsi = _validation_frame(rsi, config)
    selected_rsi = validation_rsi[
        validation_rsi["causal_regime"].isin(selected_regimes)
    ].copy()
    validation_m15 = _validation_frame(protected, config)
    combined = pd.concat(
        [
            selected_rsi[
                ["entry_time", "exit_time", "component", "side", "pnl_usd"]
            ],
            validation_m15[
                ["entry_time", "exit_time", "component", "side", "pnl_usd"]
            ],
        ],
        ignore_index=True,
    ).sort_values(["entry_time", "component"])
    denominator = int(config["period"]["locked_validation_weekdays"])
    combined_metrics = regime_metrics(combined, denominator, config)
    regime_results, regime_checks = validation_regime_checks(
        selected_rsi,
        selected_regimes,
        config,
    )
    combined_checks = portfolio_checks(combined_metrics, combined, config)
    all_checks = {
        "minimum_one_selected_regime": bool(selected_regimes),
        **regime_checks,
        **combined_checks,
    }
    result = {
        "schema_version": config["schema_version"],
        "status": (
            "HISTORICAL_VALIDATION_SUPPORTS_FORWARD_REBUILD"
            if all(all_checks.values())
            else "HISTORICAL_VALIDATION_REJECTED"
        ),
        "research_boundary": config["status"],
        "selected_regimes_from_development_only": selected_regimes,
        "development_regimes_evaluated": len(table),
        "locked_validation": {
            "rsi_source_trades": len(validation_rsi),
            "selected_rsi_trades": len(selected_rsi),
            "protected_m15_trades": len(validation_m15),
            "selected_regime_metrics": regime_results,
            "combined": combined_metrics,
            "maximum_concurrent_positions": (
                metrics._maximum_concurrency(combined)
            ),
            "same_entry_overlap_timestamps": int(
                (combined.groupby("entry_time").size() > 1).sum()
            ),
            "checks": all_checks,
        },
        "result_can_count_as_forward_evidence": False,
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    return result, table, combined.reset_index(drop=True)


def run() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    config = load_config()
    verified = verify_sources(config)
    rsi, protected = load_sources(config)
    result, table, combined = evaluate(rsi, protected, config)
    result["verified_source_sha256"] = verified
    result["selector_config_sha256"] = metrics.sha256(CONFIG_PATH)
    result["selector_source_sha256"] = metrics.sha256(Path(__file__))
    monthly = (
        combined.assign(month=combined["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")
        .agg(
            trades=("pnl_usd", "size"),
            pnl_usd=("pnl_usd", "sum"),
        )
        .reset_index()
    )
    return result, table, combined, monthly


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
    combined = validation["combined"]
    failed = [
        name for name, passed in validation["checks"].items() if not passed
    ]
    return "\n".join(
        [
            "# RSI chronological regime selector",
            "",
            f"Status: **{result['status']}**",
            "",
            "Regimes were admitted using the first 12 months only. The second",
            "12 months were locked validation and did not alter selection.",
            "",
            "Selected regimes:",
            "",
            *(
                [
                    f"- `{regime}`"
                    for regime in result[
                        "selected_regimes_from_development_only"
                    ]
                ]
                or ["- None"]
            ),
            "",
            "## Locked last-12-month combined result",
            "",
            f"- RSI trades: `{validation['selected_rsi_trades']}`",
            f"- Protected M15 trades: `{validation['protected_m15_trades']}`",
            f"- Combined trades: `{combined['trades']}`",
            f"- Trades/weekday: `{combined['trades_per_weekday']:.4f}`",
            f"- Weekday coverage: `{combined['weekday_coverage']:.2%}`",
            f"- Win rate: `{combined['win_rate']:.2%}`",
            f"- Payoff: `{combined['payoff_ratio']}`",
            f"- PF: `{combined['profit_factor']:.4f}`",
            (
                "- PF after +0.5 pip: "
                f"`{combined['plus_0_5_pip_profit_factor']:.4f}`"
            ),
            (
                "- Best-5%-removed PF: "
                f"`{combined['top_5pct_removed_profit_factor']:.4f}`"
            ),
            f"- Net P&L: `${combined['net_pnl_usd']:.2f}`",
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
    table: pd.DataFrame,
    combined: pd.DataFrame,
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
    candidates = table.copy()
    candidates["trade_sequence_half_profit_factors"] = candidates[
        "trade_sequence_half_profit_factors"
    ].map(json.dumps)
    candidates.to_csv(
        output_dir / "DEVELOPMENT_REGIMES.csv",
        index=False,
    )
    combined.to_csv(
        output_dir / "LOCKED_VALIDATION_COMBINED_TRADES.csv",
        index=False,
    )
    monthly.to_csv(output_dir / "MONTHLY.csv", index=False)


__all__ = [
    "development_row_passes",
    "development_table",
    "evaluate",
    "load_config",
    "load_sources",
    "regime_metrics",
    "run",
    "select_regimes",
    "sequence_half_profit_factors",
    "verify_sources",
    "write_outputs",
]
