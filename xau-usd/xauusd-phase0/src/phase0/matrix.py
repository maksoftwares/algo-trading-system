from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.backtester import matrix_output_stem, run_backtest, write_backtest_outputs
from phase0.config import ConfigError, ProjectConfig, build_cell_configs
from phase0.data_loader import processed_bars_dir
from phase0.run_context import context_with_symbol_metadata
from phase0.strategies.registry import enabled_strategy_names, get_strategy
from phase0.synthetic import synthetic_context_for_expert


@dataclass(frozen=True)
class MatrixRunOutput:
    expert: str
    cell_id: int
    summary_path: Path
    trades_path: Path
    equity_path: Path


def run_phase0_matrix(
    config: ProjectConfig,
    expert: str,
    synthetic_sample: bool = False,
) -> list[MatrixRunOutput]:
    outputs: list[MatrixRunOutput] = []
    for expert_name in enabled_strategy_names(expert):
        strategy = get_strategy(expert_name)
        cells = build_cell_configs(config, symbol="XAUUSD")
        for cell in cells:
            if synthetic_sample:
                data_context = synthetic_context_for_expert(expert_name)
            else:
                data_context = context_with_symbol_metadata(
                    config,
                    load_cell_data_context(config, cell.broker, cell.symbol),
                    cell.symbol,
                )

            result = run_backtest(
                config=config,
                strategy=strategy,
                data_context=data_context,
                broker=cell.broker,
                cost_model=cell.cost_model,
                starting_equity=config.phase0["project"]["starting_equity_usd"],
                risk_per_trade_pct=config.phase0["project"]["phase0_risk_per_trade_pct"],
                period_start=cell.start_utc,
                period_end=cell.end_utc,
            )
            result.metrics.update(
                {
                    "cell_id": cell.cell_id,
                    "time_window": f"{cell.start_utc.isoformat()} to {cell.end_utc.isoformat()}",
                    "tick_source": cell.broker,
                    "time_window_start": cell.start_utc.isoformat(),
                    "time_window_end": cell.end_utc.isoformat(),
                }
            )
            output_dir = config.root / "outputs" / "matrix_results" / expert_name
            stem = matrix_output_stem(cell.cell_id, expert_name, cell.broker, cell.cost_model)
            summary_path, trades_path, equity_path = write_backtest_outputs(result, output_dir, stem)
            outputs.append(
                MatrixRunOutput(
                    expert=expert_name,
                    cell_id=cell.cell_id,
                    summary_path=summary_path,
                    trades_path=trades_path,
                    equity_path=equity_path,
                )
            )
    return outputs


def load_cell_data_context(config: ProjectConfig, broker: str, symbol: str) -> dict:
    bars_root = processed_bars_dir(config, broker, symbol)
    if not bars_root.exists():
        raise ConfigError(
            f"Processed bars not found at {bars_root}. "
            "Run normalize-data and build-bars first, or use --synthetic-sample for a smoke test."
        )

    context: dict[str, object] = {"symbol": symbol}
    for timeframe in ("M5", "M15", "H1", "H4", "D1"):
        timeframe_dir = bars_root / timeframe
        files = sorted(timeframe_dir.glob("*.csv")) if timeframe_dir.exists() else []
        if not files:
            raise ConfigError(f"Missing processed {timeframe} bars in {timeframe_dir}.")
        context[timeframe] = pd.read_csv(files[-1])
    return context
