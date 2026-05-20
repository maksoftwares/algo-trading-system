from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.backtester import run_backtest
from phase0.config import ProjectConfig
from phase0.matrix import load_cell_data_context
from phase0.run_context import (
    context_with_symbol_metadata,
    filter_context_by_time,
    guarded_or_trimmed_period,
    split_period,
)
from phase0.strategies.registry import enabled_strategy_names, get_strategy
from phase0.synthetic import synthetic_context_for_expert


DECILE_COLUMNS = (
    "expert",
    "decile_id",
    "start_utc",
    "end_utc",
    "trade_count",
    "profit_factor",
    "total_return_pct",
    "max_drawdown_pct",
    "avg_trade_R",
    "verdict",
)


@dataclass(frozen=True)
class DecileRunOutput:
    expert: str
    results_path: Path


def run_decile_tests(
    config: ProjectConfig,
    expert: str,
    synthetic_sample: bool = False,
    unlock_true_holdout: bool = False,
) -> list[DecileRunOutput]:
    start, end = guarded_or_trimmed_period(
        config,
        "decile_start",
        "decile_end",
        unlock_true_holdout=unlock_true_holdout,
    )
    outputs: list[DecileRunOutput] = []
    for expert_name in enabled_strategy_names(expert):
        rows = _run_expert_deciles(config, expert_name, start, end, synthetic_sample)
        output_dir = config.root / "outputs" / "decile_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{expert_name}_decile_results.csv"
        pd.DataFrame(rows, columns=DECILE_COLUMNS).to_csv(path, index=False)
        outputs.append(DecileRunOutput(expert_name, path))
    return outputs


def _run_expert_deciles(
    config: ProjectConfig,
    expert: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    synthetic_sample: bool,
) -> list[dict[str, object]]:
    strategy = get_strategy(expert)
    rows: list[dict[str, object]] = []
    base_context = None
    if not synthetic_sample:
        base_context = context_with_symbol_metadata(
            config,
            load_cell_data_context(
                config,
                "capital_com",
                "XAUUSD",
                required_start=start,
                required_end=end,
            ),
            "XAUUSD",
        )

    for decile_id, decile_start, decile_end in split_period(start, end, 10):
        if synthetic_sample:
            context = synthetic_context_for_expert(expert)
        else:
            context = filter_context_by_time(base_context or {}, decile_start, decile_end)

        result = run_backtest(
            config=config,
            strategy=strategy,
            data_context=context,
            broker="capital_com",
            cost_model="median",
            period_start=decile_start,
            period_end=decile_end,
        )
        rows.append(_decile_row(config, expert, decile_id, decile_start, decile_end, result.metrics))
    return rows


def _decile_row(
    config: ProjectConfig,
    expert: str,
    decile_id: int,
    start: pd.Timestamp,
    end: pd.Timestamp,
    metrics: dict[str, object],
) -> dict[str, object]:
    min_pf = float(config.phase0["gates"]["decile_min_pf"])
    min_trades = int(config.phase0["gates"]["decile_min_trades"])
    trade_count = int(metrics["trade_count"])
    profit_factor = float(metrics["profit_factor"])
    verdict = "PASS" if trade_count >= min_trades and profit_factor >= min_pf else "FAIL"
    return {
        "expert": expert,
        "decile_id": decile_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "trade_count": trade_count,
        "profit_factor": profit_factor,
        "total_return_pct": metrics["total_return_pct"],
        "max_drawdown_pct": metrics["max_drawdown_pct"],
        "avg_trade_R": metrics["avg_trade_R"],
        "verdict": verdict,
    }
