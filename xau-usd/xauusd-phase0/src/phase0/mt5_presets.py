from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ProjectConfig
from phase0.data_availability import (
    REQUIRED_BACKTEST_TIMEFRAMES,
    required_broker_symbols,
    required_coverage_windows,
)


MT5_PRESET_MANIFEST_COLUMNS = (
    "broker",
    "symbol",
    "preset_path",
    "timeframes",
    "start_server_time",
    "end_server_time",
    "server_to_utc_offset_hours",
    "raw_dir",
)


@dataclass(frozen=True)
class Mt5BarPresetOutput:
    preset_paths: tuple[Path, ...]
    manifest_path: Path


def generate_mt5_bar_export_presets(
    config: ProjectConfig,
    include_multisymbol: bool = True,
    server_to_utc_offset_hours: int = 0,
) -> Mt5BarPresetOutput:
    output_dir = config.root / "outputs" / "mt5_bar_export_presets"
    output_dir.mkdir(parents=True, exist_ok=True)
    coverage = _coverage_by_broker_symbol(config, include_multisymbol)
    rows: list[dict[str, str]] = []
    preset_paths: list[Path] = []

    for broker, symbol in required_broker_symbols(config, include_multisymbol):
        start_utc, end_utc = _coverage_bounds(coverage[(broker, symbol)])
        start_server = start_utc + pd.Timedelta(hours=server_to_utc_offset_hours)
        end_server = end_utc + pd.Timedelta(hours=server_to_utc_offset_hours)
        preset_path = output_dir / f"{symbol}_{broker}_bar_export.set"
        preset_path.write_text(
            _render_preset(
                broker=broker,
                symbol=symbol,
                start_server=start_server,
                end_server=end_server,
                server_to_utc_offset_hours=server_to_utc_offset_hours,
            ),
            encoding="utf-8",
        )
        preset_paths.append(preset_path)
        rows.append(
            {
                "broker": broker,
                "symbol": symbol,
                "preset_path": preset_path.relative_to(config.root).as_posix(),
                "timeframes": ",".join(REQUIRED_BACKTEST_TIMEFRAMES),
                "start_server_time": _mt5_datetime_text(start_server),
                "end_server_time": _mt5_datetime_text(end_server),
                "server_to_utc_offset_hours": str(server_to_utc_offset_hours),
                "raw_dir": str(config.root / str(config.broker_sources["brokers"][broker]["raw_dir"])),
            }
        )

    manifest_path = output_dir / "PHASE0_MT5_BAR_EXPORT_PRESETS.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MT5_PRESET_MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return Mt5BarPresetOutput(tuple(preset_paths), manifest_path)


def _render_preset(
    broker: str,
    symbol: str,
    start_server: pd.Timestamp,
    end_server: pd.Timestamp,
    server_to_utc_offset_hours: int,
) -> str:
    lines = [
        f"InpSymbol={symbol}",
        f"InpBrokerLabel={broker}",
        f"InpTimeframes={','.join(REQUIRED_BACKTEST_TIMEFRAMES)}",
        f"InpStartServerTime={_mt5_datetime_text(start_server)}",
        f"InpEndServerTime={_mt5_datetime_text(end_server)}",
        f"InpServerToUtcOffsetHours={server_to_utc_offset_hours}",
        "InpUseCommonFiles=true",
        "InpPrintToExpertsTab=true",
    ]
    return "\n".join(lines) + "\n"


def _coverage_by_broker_symbol(
    config: ProjectConfig,
    include_multisymbol: bool,
) -> dict[tuple[str, str], list]:
    coverage: dict[tuple[str, str], list] = {}
    for window in required_coverage_windows(config, include_multisymbol):
        coverage.setdefault((window.broker, window.symbol), []).append(window)
    return coverage


def _coverage_bounds(windows: list) -> tuple[pd.Timestamp, pd.Timestamp]:
    return (
        min(window.start_utc for window in windows),
        max(window.end_utc for window in windows),
    )


def _mt5_datetime_text(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%Y.%m.%d %H:%M")
