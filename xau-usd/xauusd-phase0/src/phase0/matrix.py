from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.backtester import matrix_output_stem, run_backtest, write_backtest_outputs
from phase0.config import ConfigError, ProjectConfig, build_cell_configs, resolve_symbol
from phase0.cot_gold_data import COT_FRAME_KEY
from phase0.cot_gold_data import EXPERT_NAME as COT_GOLD_EXPERT_NAME
from phase0.cot_gold_data import load_cot_gold_context
from phase0.data_loader import processed_bars_dir
from phase0.data_validator import (
    MAX_ALLOWED_BAR_GAPS,
    bar_identity_issues,
    largest_bar_gap_issue,
    validate_bars,
)
from phase0.gold_fx_proxy_data import EXPERT_NAME as GOLD_FX_PROXY_EXPERT_NAME
from phase0.gold_fx_proxy_data import check_gold_fx_proxy_data
from phase0.gold_fx_proxy_data import load_gold_fx_proxy_h1_context
from phase0.macro_real_yield_data import EXPERT_NAME as MACRO_REAL_YIELD_EXPERT_NAME
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.macro_real_yield_data import load_macro_real_yield_context
from phase0.run_context import context_with_symbol_metadata
from phase0.strategies.registry import enabled_strategy_names, get_strategy
from phase0.synthetic import synthetic_context_for_expert
from phase0.xau_xag_relative_data import EXPERT_NAME as XAU_XAG_RELATIVE_EXPERT_NAME
from phase0.xau_xag_relative_data import check_xau_xag_relative_data
from phase0.xau_xag_relative_data import load_xau_xag_relative_h1_context

XAG_LEAD_XAU_FOLLOWTHROUGH_EXPERT_NAME = "xag_lead_xau_followthrough_v0"
XAU_XAG_FX_COMPOSITE_EXPERT_NAME = "xau_xag_fx_composite_reversion_v0"


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
    allow_research_candidate: bool = False,
) -> list[MatrixRunOutput]:
    outputs: list[MatrixRunOutput] = []
    context_cache: dict[tuple[str, str, pd.Timestamp, pd.Timestamp], dict[str, Any]] = {}
    for expert_name in enabled_strategy_names(expert, allow_research_candidate=allow_research_candidate):
        strategy = get_strategy(expert_name, allow_research_candidate=allow_research_candidate)
        if expert_name == GOLD_FX_PROXY_EXPERT_NAME and not synthetic_sample:
            _assert_gold_fx_proxy_data_ready(config)
        if expert_name == XAU_XAG_RELATIVE_EXPERT_NAME and not synthetic_sample:
            _assert_xau_xag_relative_data_ready(config)
        if expert_name == XAU_XAG_FX_COMPOSITE_EXPERT_NAME and not synthetic_sample:
            _assert_gold_fx_proxy_data_ready(config)
            _assert_xau_xag_relative_data_ready(config)
        if expert_name == XAG_LEAD_XAU_FOLLOWTHROUGH_EXPERT_NAME and not synthetic_sample:
            _assert_xau_xag_relative_data_ready(config)
        if expert_name == MACRO_REAL_YIELD_EXPERT_NAME and not synthetic_sample:
            _assert_macro_real_yield_data_ready(config)
        if expert_name == COT_GOLD_EXPERT_NAME and not synthetic_sample:
            _assert_cot_gold_data_ready(config)
        cells = build_cell_configs(config, symbol="XAUUSD")
        for cell in cells:
            if synthetic_sample:
                data_context = synthetic_context_for_expert(expert_name)
            else:
                cache_key = (cell.broker, cell.symbol, cell.start_utc, cell.end_utc)
                if cache_key not in context_cache:
                    context_cache[cache_key] = context_with_symbol_metadata(
                        config,
                        load_cell_data_context(
                            config,
                            cell.broker,
                            cell.symbol,
                            required_start=cell.start_utc,
                            required_end=cell.end_utc,
                        ),
                        cell.symbol,
                    )
                data_context = context_cache[cache_key]
                if expert_name == GOLD_FX_PROXY_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "intermarket_proxy": load_gold_fx_proxy_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == XAU_XAG_RELATIVE_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "relative_value": load_xau_xag_relative_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == XAG_LEAD_XAU_FOLLOWTHROUGH_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "relative_value": load_xau_xag_relative_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == XAU_XAG_FX_COMPOSITE_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "intermarket_proxy": load_gold_fx_proxy_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        "relative_value": load_xau_xag_relative_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == MACRO_REAL_YIELD_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        MACRO_FRAME_KEY: load_macro_real_yield_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == COT_GOLD_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        COT_FRAME_KEY: load_cot_gold_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }

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


def _assert_gold_fx_proxy_data_ready(config: ProjectConfig) -> None:
    missing = [check for check in check_gold_fx_proxy_data(config) if not check.available]
    if not missing:
        return
    lines = [
        f"- broker={check.broker}, symbol={check.symbol}, timeframe={check.timeframe}, "
        f"dir={check.directory}, first_issue={check.issues[0] if check.issues else 'no candidate CSV files'}"
        for check in missing
    ]
    raise ConfigError(
        f"{GOLD_FX_PROXY_EXPERT_NAME} research matrix is blocked by missing proxy data:\n"
        + "\n".join(lines)
        + "\nRun generate-gold-fx-proxy-data-readiness for the exact acquisition checklist."
    )


def _assert_xau_xag_relative_data_ready(config: ProjectConfig) -> None:
    missing = [check for check in check_xau_xag_relative_data(config) if not check.available]
    if not missing:
        return
    lines = [
        f"- broker={check.broker}, symbol={check.symbol}, timeframe={check.timeframe}, "
        f"dir={check.directory}, first_issue={check.issues[0] if check.issues else 'no candidate CSV files'}"
        for check in missing
    ]
    raise ConfigError(
        f"{XAU_XAG_RELATIVE_EXPERT_NAME} research matrix is blocked by missing XAGUSD data:\n"
        + "\n".join(lines)
        + "\nRun generate-xau-xag-relative-data-readiness for the exact acquisition checklist."
    )


def _assert_macro_real_yield_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_macro_real_yield_context(config, start, end)


def _assert_cot_gold_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_cot_gold_context(config, start, end)


def load_cell_data_context(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    required_start: object | None = None,
    required_end: object | None = None,
) -> dict:
    canonical_symbol = resolve_symbol(config, symbol)
    bars_root = processed_bars_dir(config, broker, canonical_symbol)
    if not bars_root.exists():
        raise ConfigError(
            f"Processed bars not found at {bars_root}. "
            "Run import-required-bars for direct OHLC bar exports, or use --synthetic-sample for a smoke test."
        )

    context: dict[str, Any] = {"symbol": canonical_symbol}
    for timeframe in ("M5", "M15", "H1", "H4", "D1"):
        timeframe_dir = bars_root / timeframe
        files = sorted(timeframe_dir.glob("*.csv")) if timeframe_dir.exists() else []
        if not files:
            raise ConfigError(f"Missing processed {timeframe} bars in {timeframe_dir}.")
        frame = _load_processed_timeframe_bars(files, broker, canonical_symbol, timeframe)
        _assert_bar_coverage(frame, timeframe_dir, timeframe, required_start, required_end)
        context[timeframe] = frame
    return context


def _load_processed_timeframe_bars(
    files: list[Path],
    broker: str,
    symbol: str,
    timeframe: str,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in files:
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            raise ConfigError(
                f"Failed to read processed {timeframe} bars in {path}: {exc}"
            ) from exc

    combined = pd.concat(frames, ignore_index=True)
    if "timestamp_utc" in combined.columns:
        timestamps = pd.to_datetime(combined["timestamp_utc"], utc=True, errors="coerce")
        combined = (
            combined.assign(_phase0_sort_timestamp=timestamps)
            .sort_values("_phase0_sort_timestamp", na_position="last")
            .drop(columns="_phase0_sort_timestamp")
            .reset_index(drop=True)
        )

    report = validate_bars(combined, name=f"{timeframe} processed bars", fail_on_error=False)
    if report.error_count:
        first_issue = next(issue for issue in report.issues if issue.severity == "ERROR")
        raise ConfigError(
            f"Processed {timeframe} bars failed validation after combining {len(files)} file(s): "
            f"{first_issue.column} {first_issue.message}"
        )

    identity_issues = bar_identity_issues(combined, broker, symbol, timeframe)
    if identity_issues:
        raise ConfigError(
            f"Processed {timeframe} bars failed identity check after combining "
            f"{len(files)} file(s): {identity_issues[0]}."
        )

    gap_issue = largest_bar_gap_issue(combined["bar_end_utc"], timeframe)
    if gap_issue:
        raise ConfigError(
            f"Processed {timeframe} bars failed continuity check after combining "
            f"{len(files)} file(s): {gap_issue}."
        )
    return combined


def _assert_bar_coverage(
    frame: pd.DataFrame,
    source: Path,
    timeframe: str,
    required_start: object | None,
    required_end: object | None,
) -> None:
    if required_start is None or required_end is None:
        return
    missing = [column for column in ("bar_start_utc", "bar_end_utc") if column not in frame.columns]
    if missing:
        raise ConfigError(
            f"Processed {timeframe} bars in {source} missing coverage column(s): "
            f"{', '.join(missing)}."
        )

    starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce").dropna()
    ends = pd.to_datetime(frame["bar_end_utc"], utc=True, errors="coerce").dropna()
    if starts.empty or ends.empty:
        raise ConfigError(
            f"Processed {timeframe} bars in {source} have no valid coverage timestamps."
        )

    coverage_start = pd.Timestamp(starts.min())
    coverage_end = pd.Timestamp(ends.max())
    needed_start = _utc_timestamp(required_start)
    needed_end = _utc_timestamp(required_end)
    allowed_boundary_gap = MAX_ALLOWED_BAR_GAPS[timeframe]
    starts_too_late = (
        coverage_start > needed_start and coverage_start - needed_start > allowed_boundary_gap
    )
    ends_too_early = coverage_end < needed_end and needed_end - coverage_end > allowed_boundary_gap
    if starts_too_late or ends_too_early:
        raise ConfigError(
            f"Processed {timeframe} bars in {source} cover "
            f"{coverage_start.isoformat()} to {coverage_end.isoformat()}, "
            f"but required {needed_start.isoformat()} to {needed_end.isoformat()}. "
            "Run import-required-bars for direct OHLC bar exports, or regenerate processed bars."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
