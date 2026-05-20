from __future__ import annotations

from datetime import datetime, timedelta, timezone
import shutil
from pathlib import Path

import pandas as pd
import pytest

import phase0.matrix as matrix_module
import phase0.backtester as backtester_module
from phase0.backtester import BacktestResult, matrix_output_stem, run_backtest, write_backtest_outputs
from phase0.cli import main
from phase0.config import ConfigError, load_project_config
from phase0.aggregation import aggregate_matrix_results
from phase0.data_contracts import Signal, Trade, TradePlan
from phase0.data_validator import BAR_REQUIRED_COLUMNS
from phase0.hashing import register_hypotheses
from phase0.matrix import load_cell_data_context, run_phase0_matrix
from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


TIMEFRAME_DELTAS = {
    "M5": pd.Timedelta(minutes=5),
    "M15": pd.Timedelta(minutes=15),
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
    "D1": pd.Timedelta(days=1),
}


def test_run_backtest_synthetic_trend_pullback(project_root):
    config = load_project_config(project_root)
    strategy = get_strategy("trend_pullback")

    result = run_backtest(
        config=config,
        strategy=strategy,
        data_context=synthetic_context_for_expert("trend_pullback"),
        broker="capital_com",
        cost_model="median",
    )

    assert result.expert == "trend_pullback"
    assert len(result.trades) == 1
    assert result.metrics["trade_count"] == 1
    assert result.equity_curve.iloc[-1]["equity"] != result.equity_curve.iloc[0]["equity"]
    assert set(result.diagnostics["status"]) == {"traded"}


def test_write_backtest_outputs(project_root, tmp_path):
    config = load_project_config(project_root)
    result = run_backtest(
        config=config,
        strategy=get_strategy("trend_pullback"),
        data_context=synthetic_context_for_expert("trend_pullback"),
        broker="capital_com",
        cost_model="median",
    )

    summary_path, trades_path, equity_path = write_backtest_outputs(result, tmp_path, "sample")

    assert summary_path.exists()
    assert trades_path.exists()
    assert equity_path.exists()
    assert pd.read_csv(summary_path).loc[0, "trade_count"] == 1
    assert len(pd.read_csv(trades_path)) == 1
    assert len(pd.read_csv(equity_path)) == 2


def test_run_backtest_filters_signals_to_requested_period(project_root, monkeypatch):
    config = load_project_config(project_root)
    simulated_times: list[datetime] = []

    def fake_simulate_trade(
        config,
        bars,
        plan,
        broker,
        cost_model_name,
        current_equity,
        risk_per_trade_pct,
    ):
        del config, broker, cost_model_name, current_equity, risk_per_trade_pct
        assert pd.to_datetime(bars["timestamp_utc"], utc=True).max() <= pd.Timestamp(
            "2019-12-31T23:59:00Z"
        )
        simulated_times.append(plan.signal_time_utc)
        return _probe_trade(plan.signal_time_utc)

    monkeypatch.setattr(backtester_module, "simulate_trade", fake_simulate_trade)

    result = run_backtest(
        config=config,
        strategy=PeriodProbeStrategy(),
        data_context={"symbol": "XAUUSD", "M5": _window_probe_bars()},
        broker="capital_com",
        cost_model="median",
        period_start=datetime(2019, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2019, 12, 31, 23, 59, tzinfo=timezone.utc),
    )

    assert [time.isoformat() for time in simulated_times] == ["2019-06-01T00:05:00+00:00"]
    assert result.metrics["trade_count"] == 1


def test_run_phase0_matrix_synthetic_writes_nine_cells(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    outputs = run_phase0_matrix(config, "trend_pullback", synthetic_sample=True)

    assert len(outputs) == 9
    first = outputs[0]
    assert first.summary_path.name == matrix_output_stem(
        1,
        "trend_pullback",
        "capital_com",
        "best_case",
    ) + ".csv"
    assert first.summary_path.exists()
    assert first.trades_path.exists()
    assert first.equity_path.exists()


def test_run_phase0_matrix_passes_full_context_and_cell_window(project_root, tmp_path, monkeypatch):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    observed_windows: list[tuple[str, str, tuple[str, ...], str, str]] = []

    def fake_load_cell_data_context(config, broker, symbol, required_start=None, required_end=None):
        del config, broker, symbol, required_start, required_end
        bars = _window_probe_bars()
        return {timeframe: bars.copy() for timeframe in ("M5", "M15", "H1", "H4", "D1")}

    def fake_run_backtest(
        config,
        strategy,
        data_context,
        broker,
        cost_model,
        starting_equity=None,
        risk_per_trade_pct=None,
        period_start=None,
        period_end=None,
    ):
        del config, starting_equity, risk_per_trade_pct
        timestamps = tuple(data_context["M5"]["timestamp_utc"].astype(str).tolist())
        observed_windows.append(
            (
                broker,
                cost_model,
                timestamps,
                pd.Timestamp(period_start).isoformat(),
                pd.Timestamp(period_end).isoformat(),
            )
        )
        return BacktestResult(
            expert=strategy.name,
            broker=broker,
            cost_model=cost_model,
            symbol="XAUUSD",
            trades=[],
            equity_curve=pd.DataFrame(),
            metrics={"trade_count": len(timestamps)},
            diagnostics=pd.DataFrame(),
        )

    monkeypatch.setattr(matrix_module, "load_cell_data_context", fake_load_cell_data_context)
    monkeypatch.setattr(matrix_module, "run_backtest", fake_run_backtest)

    outputs = run_phase0_matrix(config, "trend_pullback", synthetic_sample=False)

    assert len(outputs) == 9
    assert observed_windows[0][2] == tuple(_window_probe_bars()["timestamp_utc"].tolist())
    assert observed_windows[0][3].startswith("2016-01-01")
    assert observed_windows[3][3].startswith("2019-01-01")
    assert observed_windows[6][3].startswith("2022-01-01")


def test_run_matrix_cli_synthetic(project_root, tmp_path, capsys):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    exit_code = main(
        [
            "--root",
            str(root),
            "run-matrix",
            "--expert",
            "trend_pullback",
            "--synthetic-sample",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Matrix run complete: 9 cell output set" in captured.out


def test_load_cell_data_context_rejects_insufficient_coverage(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    for timeframe in ("M5", "M15", "H1", "H4", "D1"):
        directory = root / "data" / "processed" / "bars" / "capital_com" / "XAUUSD" / timeframe
        directory.mkdir(parents=True, exist_ok=True)
        _short_coverage_bars(timeframe).to_csv(
            directory / f"XAUUSD_capital_com_{timeframe}_sample.csv",
            index=False,
        )

    with pytest.raises(ConfigError, match="but required"):
        load_cell_data_context(
            config,
            "capital_com",
            "XAUUSD",
            required_start="2016-01-01T00:00:00Z",
            required_end="2024-12-31T23:59:59Z",
        )


def test_load_cell_data_context_combines_split_timeframe_files(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    _write_split_coverage_bars(root)
    config = load_project_config(root)

    context = load_cell_data_context(
        config,
        "capital_com",
        "XAUUSD",
        required_start="2016-01-01T00:00:00Z",
        required_end="2025-06-30T23:59:59Z",
    )

    m5_timestamps = pd.to_datetime(context["M5"]["timestamp_utc"], utc=True)
    assert len(context["M5"]) > 500
    assert m5_timestamps.is_monotonic_increasing
    assert pd.to_datetime(context["M5"]["bar_start_utc"], utc=True).min() <= pd.Timestamp(
        "2016-01-01T00:00:00Z"
    )
    assert pd.to_datetime(context["M5"]["bar_end_utc"], utc=True).max() >= pd.Timestamp(
        "2025-06-30T23:59:59Z"
    )


def test_load_cell_data_context_rejects_split_files_with_large_gap(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    directory = root / "data" / "processed" / "bars" / "capital_com" / "XAUUSD" / "M5"
    directory.mkdir(parents=True, exist_ok=True)
    _write_bar_rows(
        directory / "XAUUSD_capital_com_M5_part1.csv",
        "M5",
        [pd.Timestamp("2016-01-01T00:00:00Z")],
    )
    _write_bar_rows(
        directory / "XAUUSD_capital_com_M5_part2.csv",
        "M5",
        [_last_required_bar_start("M5")],
    )
    config = load_project_config(root)

    with pytest.raises(ConfigError, match="continuity check"):
        load_cell_data_context(
            config,
            "capital_com",
            "XAUUSD",
            required_start="2016-01-01T00:00:00Z",
            required_end="2025-06-30T23:59:59Z",
        )


def test_aggregate_matrix_results(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    run_phase0_matrix(config, "trend_pullback", synthetic_sample=True)

    outputs = aggregate_matrix_results(config, "trend_pullback")

    assert len(outputs) == 1
    assert outputs[0].metrics_path.exists()
    assert outputs[0].gates_path.exists()
    assert "sample_size" in outputs[0].gates_path.read_text(encoding="utf-8")


def test_aggregate_results_cli(project_root, tmp_path, capsys):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    run_phase0_matrix(config, "trend_pullback", synthetic_sample=True)

    exit_code = main(["--root", str(root), "aggregate-results", "--expert", "trend_pullback"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Aggregated matrix results for 1 expert" in captured.out


def _copy_minimal_project(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    shutil.copytree(project_root / "docs", root / "docs")
    (root / "outputs" / "hashes").mkdir(parents=True)
    return root


class PeriodProbeStrategy:
    name = "period_probe"

    def prepare_features(self, data_context):
        return data_context

    def generate_signals(self, data_context):
        return [
            Signal(
                expert=self.name,
                timestamp_utc=pd.Timestamp(timestamp).to_pydatetime(),
                symbol="XAUUSD",
                direction="LONG",
                reason_code="PERIOD_PROBE",
            )
            for timestamp in data_context["M5"]["timestamp_utc"]
        ]

    def build_trade_plan(self, signal, data_context):
        del data_context
        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction=signal.direction,
            signal_time_utc=signal.timestamp_utc,
            entry_type="MARKET",
            entry_price=None,
            stop_loss=99.0,
            take_profit=101.0,
            invalidation_level=99.0,
            risk_reward=1.0,
            reason_code=signal.reason_code,
        )


def _probe_trade(signal_time: datetime) -> Trade:
    exit_time = signal_time + timedelta(minutes=5)
    return Trade(
        expert="period_probe",
        symbol="XAUUSD",
        direction="LONG",
        entry_time_utc=signal_time,
        exit_time_utc=exit_time,
        entry_price=100.0,
        exit_price=101.0,
        stop_loss=99.0,
        take_profit=101.0,
        lots=0.1,
        gross_pnl_usd=10.0,
        costs_usd=0.0,
        net_pnl_usd=10.0,
        r_multiple=1.0,
        exit_reason="take_profit",
    )


def _window_probe_bars() -> pd.DataFrame:
    timestamps = [
        "2015-12-31T23:55:00Z",
        "2016-06-01T00:05:00Z",
        "2019-06-01T00:05:00Z",
        "2022-06-01T00:05:00Z",
        "2025-01-01T00:05:00Z",
    ]
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "bar_start_utc": [
                "2015-12-31T23:50:00Z",
                "2016-06-01T00:00:00Z",
                "2019-06-01T00:00:00Z",
                "2022-06-01T00:00:00Z",
                "2025-01-01T00:00:00Z",
            ],
            "open": [100.0] * 5,
            "high": [101.0] * 5,
            "low": [99.0] * 5,
            "close": [100.5] * 5,
        }
    )


def _write_split_coverage_bars(root: Path) -> None:
    for timeframe in ("M5", "M15", "H1", "H4", "D1"):
        directory = root / "data" / "processed" / "bars" / "capital_com" / "XAUUSD" / timeframe
        directory.mkdir(parents=True, exist_ok=True)
        starts = _bar_start_samples(timeframe)
        split_index = len(starts) // 2
        _write_bar_rows(
            directory / f"XAUUSD_capital_com_{timeframe}_part1.csv",
            timeframe,
            starts[:split_index],
        )
        _write_bar_rows(
            directory / f"XAUUSD_capital_com_{timeframe}_part2.csv",
            timeframe,
            starts[split_index:],
        )


def _write_bar_rows(path: Path, timeframe: str, starts: list[pd.Timestamp]) -> None:
    pd.DataFrame(
        [_valid_bar_row(timeframe, start) for start in starts],
        columns=BAR_REQUIRED_COLUMNS,
    ).to_csv(path, index=False)


def _bar_start_samples(timeframe: str) -> list[pd.Timestamp]:
    first_bar_start = pd.Timestamp("2016-01-01T00:00:00Z")
    last_bar_start = _last_required_bar_start(timeframe)
    starts = list(pd.date_range(first_bar_start, last_bar_start, freq="6D"))
    if starts[-1] != last_bar_start:
        starts.append(last_bar_start)
    return starts


def _last_required_bar_start(timeframe: str) -> pd.Timestamp:
    return pd.Timestamp("2025-07-01T00:00:00Z") - TIMEFRAME_DELTAS[timeframe]


def _short_coverage_bars(timeframe: str) -> pd.DataFrame:
    return pd.DataFrame(
        [_valid_bar_row(timeframe, pd.Timestamp("2020-01-01T00:00:00Z"))],
        columns=BAR_REQUIRED_COLUMNS,
    )


def _valid_bar_row(timeframe: str, bar_start_utc: pd.Timestamp) -> dict[str, object]:
    bar_start = pd.Timestamp(bar_start_utc)
    bar_end = bar_start + TIMEFRAME_DELTAS[timeframe]
    return {
        "timestamp_utc": _format_utc(bar_end),
        "bar_start_utc": _format_utc(bar_start),
        "bar_end_utc": _format_utc(bar_end),
        "broker": "capital_com",
        "symbol": "XAUUSD",
        "timeframe": timeframe,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "mid_open": 100.0,
        "mid_high": 101.0,
        "mid_low": 99.0,
        "mid_close": 100.5,
        "bid_open": 99.9,
        "bid_high": 100.9,
        "bid_low": 98.9,
        "bid_close": 100.4,
        "ask_open": 100.1,
        "ask_high": 101.1,
        "ask_low": 99.1,
        "ask_close": 100.6,
        "spread_open_points": 20.0,
        "spread_close_points": 20.0,
        "spread_median_points": 20.0,
        "spread_p95_points": 22.0,
        "tick_count": 10,
        "volume_sum": 100,
    }


def _format_utc(timestamp: pd.Timestamp) -> str:
    return pd.Timestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%SZ")
