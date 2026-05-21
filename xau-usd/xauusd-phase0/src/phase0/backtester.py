from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ConfigError, ProjectConfig
from phase0.data_contracts import Signal, Trade
from phase0.execution import ExecutionError, prepare_execution_bars, simulate_trade
from phase0.metrics import equity_curve_from_trades, metrics_row
from phase0.strategies.base import StrategyBase
from phase0.trades import trades_to_dataframe


@dataclass(frozen=True)
class BacktestResult:
    expert: str
    broker: str
    cost_model: str
    symbol: str
    trades: list[Trade]
    equity_curve: pd.DataFrame
    metrics: dict[str, object]
    diagnostics: pd.DataFrame


def run_backtest(
    config: ProjectConfig,
    strategy: StrategyBase,
    data_context: dict[str, Any],
    broker: str,
    cost_model: str,
    starting_equity: float | None = None,
    risk_per_trade_pct: float | None = None,
    period_start: object | None = None,
    period_end: object | None = None,
) -> BacktestResult:
    if "M5" not in data_context:
        raise ConfigError("Backtest data_context must include M5 bars.")
    symbol = str(data_context.get("symbol", "XAUUSD"))
    starting_equity = float(starting_equity or config.phase0["project"]["starting_equity_usd"])
    risk_per_trade_pct = float(
        risk_per_trade_pct or config.phase0["project"]["phase0_risk_per_trade_pct"]
    )

    strategy_context = _data_context_for_period_end(data_context, period_end)
    signals = sorted(
        (
            signal
            for signal in strategy.generate_signals(strategy_context)
            if _signal_in_period(signal, period_start, period_end)
        ),
        key=lambda signal: pd.Timestamp(signal.timestamp_utc),
    )
    trades: list[Trade] = []
    diagnostics: list[dict[str, object]] = []
    current_equity = starting_equity
    open_until: pd.Timestamp | None = None
    execution_bars = prepare_execution_bars(
        _execution_bars_for_period(strategy_context["M5"], period_end)
    )

    for signal in signals:
        signal_time = pd.Timestamp(signal.timestamp_utc)
        if open_until is not None and signal_time <= open_until:
            diagnostics.append(_diagnostic(signal, "ignored", "open_position_exists"))
            continue

        try:
            plan = strategy.build_trade_plan(signal, strategy_context)
            trade = simulate_trade(
                config=config,
                bars=execution_bars,
                plan=plan,
                broker=broker,
                cost_model_name=cost_model,
                current_equity=current_equity,
                risk_per_trade_pct=risk_per_trade_pct,
            )
        except (ConfigError, ExecutionError) as exc:
            diagnostics.append(_diagnostic(signal, "rejected", str(exc)))
            continue

        trades.append(trade)
        current_equity += trade.net_pnl_usd
        open_until = pd.Timestamp(trade.exit_time_utc)
        diagnostics.append(_diagnostic(signal, "traded", trade.exit_reason))

    equity = equity_curve_from_trades(trades, starting_equity)
    metrics = metrics_row(
        trades,
        starting_equity,
        period_start=period_start,
        period_end=period_end,
        extra={"expert": strategy.name, "broker": broker, "cost_model": cost_model, "symbol": symbol},
    )
    return BacktestResult(
        expert=strategy.name,
        broker=broker,
        cost_model=cost_model,
        symbol=symbol,
        trades=trades,
        equity_curve=equity,
        metrics=metrics,
        diagnostics=pd.DataFrame(diagnostics),
    )


def write_backtest_outputs(
    result: BacktestResult,
    output_dir: str | Path,
    stem: str,
) -> tuple[Path, Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    summary_path = directory / f"{stem}.csv"
    trades_path = directory / f"{stem}_trades.csv"
    equity_path = directory / f"{stem}_equity.csv"

    pd.DataFrame([result.metrics]).to_csv(summary_path, index=False)
    trades_to_dataframe(result.trades).to_csv(trades_path, index=False)
    result.equity_curve.to_csv(equity_path, index=False)
    return summary_path, trades_path, equity_path


def matrix_output_stem(cell_id: int, expert: str, broker: str, cost_model: str) -> str:
    return f"cell_{cell_id}_{expert}_{broker}_{cost_model}"


def _diagnostic(signal: Signal, status: str, reason: str) -> dict[str, object]:
    return {
        "expert": signal.expert,
        "signal_time_utc": signal.timestamp_utc,
        "symbol": signal.symbol,
        "direction": signal.direction,
        "reason_code": signal.reason_code,
        "status": status,
        "detail": reason,
    }


def _signal_in_period(
    signal: Signal,
    period_start: object | None,
    period_end: object | None,
) -> bool:
    signal_time = pd.Timestamp(signal.timestamp_utc)
    if signal_time.tzinfo is None:
        signal_time = signal_time.tz_localize("UTC")
    else:
        signal_time = signal_time.tz_convert("UTC")

    if period_start is not None and signal_time < _period_timestamp(period_start):
        return False
    if period_end is not None and signal_time > _period_timestamp(period_end):
        return False
    return True


def _period_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _data_context_for_period_end(
    data_context: dict[str, Any],
    period_end: object | None,
) -> dict[str, Any]:
    if period_end is None:
        return data_context

    bounded: dict[str, Any] = {}
    end = _period_timestamp(period_end)
    for key, value in data_context.items():
        if isinstance(value, pd.DataFrame) and "timestamp_utc" in value.columns:
            timestamps = pd.to_datetime(value["timestamp_utc"], utc=True, errors="coerce")
            bounded[key] = value.loc[timestamps <= end].reset_index(drop=True).copy()
        else:
            bounded[key] = value
    return bounded


def _execution_bars_for_period(bars: pd.DataFrame, period_end: object | None) -> pd.DataFrame:
    if period_end is None:
        return bars
    if "timestamp_utc" not in bars.columns:
        return bars
    timestamps = pd.to_datetime(bars["timestamp_utc"], utc=True, errors="coerce")
    return bars.loc[timestamps <= _period_timestamp(period_end)].reset_index(drop=True).copy()
