from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.backtester import run_backtest
from phase0.config import ProjectConfig
from phase0.constants import COMPARISON_SYMBOLS
from phase0.matrix import load_cell_data_context
from phase0.run_context import (
    context_with_symbol_metadata,
    filter_context_by_time,
    guarded_or_trimmed_period,
)
from phase0.strategies.registry import enabled_strategy_names, get_strategy
from phase0.synthetic import synthetic_context_for_expert
from phase0.trades import trades_to_dataframe


MULTISYMBOL_SUMMARY_COLUMNS = (
    "expert",
    "symbol",
    "broker",
    "cost_model",
    "trade_count",
    "profit_factor",
    "total_return_pct",
    "max_drawdown_pct",
    "avg_trade_R",
    "verdict",
)


@dataclass(frozen=True)
class MultisymbolRunOutput:
    expert: str
    summary_path: Path
    trades_paths: tuple[Path, ...]


def run_multisymbol_checks(
    config: ProjectConfig,
    expert: str,
    synthetic_sample: bool = False,
    broker: str = "capital_com",
    cost_model: str = "median",
    unlock_true_holdout: bool = False,
) -> list[MultisymbolRunOutput]:
    start, end = guarded_or_trimmed_period(
        config,
        "multisymbol_start",
        "multisymbol_end",
        unlock_true_holdout=unlock_true_holdout,
    )
    output_dir = config.root / "outputs" / "multisymbol_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[MultisymbolRunOutput] = []
    for expert_name in enabled_strategy_names(expert):
        summary_rows: list[dict[str, object]] = []
        trade_paths: list[Path] = []
        for symbol in COMPARISON_SYMBOLS:
            result = _run_symbol_check(
                config,
                expert_name,
                symbol,
                broker,
                cost_model,
                start,
                end,
                synthetic_sample,
            )
            summary_rows.append(_summary_row(config, expert_name, symbol, broker, cost_model, result.metrics))
            trades_path = output_dir / f"{expert_name}_{symbol}_trades.csv"
            trades_to_dataframe(result.trades).to_csv(trades_path, index=False)
            trade_paths.append(trades_path)

        summary_path = output_dir / f"{expert_name}_multisymbol_summary.csv"
        pd.DataFrame(summary_rows, columns=MULTISYMBOL_SUMMARY_COLUMNS).to_csv(
            summary_path,
            index=False,
        )
        outputs.append(MultisymbolRunOutput(expert_name, summary_path, tuple(trade_paths)))
    return outputs


def _run_symbol_check(
    config: ProjectConfig,
    expert: str,
    symbol: str,
    broker: str,
    cost_model: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    synthetic_sample: bool,
):
    strategy = get_strategy(expert)
    if synthetic_sample:
        context = context_with_symbol_metadata(config, synthetic_context_for_expert(expert), symbol)
    else:
        context = context_with_symbol_metadata(
            config,
            load_cell_data_context(
                config,
                broker,
                symbol,
                required_start=start,
                required_end=end,
            ),
            symbol,
        )
        context = filter_context_by_time(context, start, end)

    return run_backtest(
        config=config,
        strategy=strategy,
        data_context=context,
        broker=broker,
        cost_model=cost_model,
        period_start=start,
        period_end=end,
    )


def _summary_row(
    config: ProjectConfig,
    expert: str,
    symbol: str,
    broker: str,
    cost_model: str,
    metrics: dict[str, object],
) -> dict[str, object]:
    min_pf = float(config.phase0["gates"]["multisymbol_min_pf"])
    profit_factor = float(metrics["profit_factor"])
    return {
        "expert": expert,
        "symbol": symbol,
        "broker": broker,
        "cost_model": cost_model,
        "trade_count": int(metrics["trade_count"]),
        "profit_factor": profit_factor,
        "total_return_pct": metrics["total_return_pct"],
        "max_drawdown_pct": metrics["max_drawdown_pct"],
        "avg_trade_R": metrics["avg_trade_R"],
        "verdict": "PASS" if profit_factor >= min_pf else "FAIL",
    }
