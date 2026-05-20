from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, get_broker_details, resolve_symbol


def raw_data_dir(config: ProjectConfig, broker: str) -> Path:
    details = get_broker_details(config, broker)
    return config.root / str(details["raw_dir"])


def processed_ticks_dir(config: ProjectConfig, broker: str, symbol: str) -> Path:
    canonical = resolve_symbol(config, symbol)
    return config.root / "data" / "processed" / "ticks" / broker / canonical


def processed_bars_dir(config: ProjectConfig, broker: str, symbol: str, timeframe: str | None = None) -> Path:
    canonical = resolve_symbol(config, symbol)
    path = config.root / "data" / "processed" / "bars" / broker / canonical
    if timeframe is not None:
        path = path / timeframe
    return path


def find_raw_tick_files(config: ProjectConfig, broker: str, symbol: str) -> list[Path]:
    directory = raw_data_dir(config, broker)
    if not directory.exists():
        raise ConfigError(f"Raw data directory does not exist: {directory}. Create it and add CSV files.")

    canonical = resolve_symbol(config, symbol)
    aliases = {
        canonical.lower(),
        *(str(alias).lower() for alias in config.symbols["symbols"][canonical].get("aliases", [])),
    }
    files = sorted(path for path in directory.rglob("*.csv") if _matches_symbol(path, aliases))
    if not files:
        files = sorted(directory.rglob("*.csv"))
    if not files:
        raise ConfigError(f"No raw CSV files found in {directory} for broker={broker}, symbol={canonical}.")
    return files


def find_raw_bar_files(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframe: str,
    require_timeframe_token: bool = False,
) -> list[Path]:
    directory = raw_data_dir(config, broker)
    if not directory.exists():
        raise ConfigError(f"Raw data directory does not exist: {directory}. Create it and add CSV files.")

    canonical = resolve_symbol(config, symbol)
    aliases = {
        canonical.lower(),
        *(str(alias).lower() for alias in config.symbols["symbols"][canonical].get("aliases", [])),
    }
    timeframe_token = timeframe.lower()
    symbol_files = sorted(path for path in directory.rglob("*.csv") if _matches_symbol(path, aliases))
    files = [path for path in symbol_files if timeframe_token in path.name.lower()]
    if not files and not require_timeframe_token:
        files = symbol_files
    if not files:
        raise ConfigError(
            f"No raw bar CSV files found in {directory} for broker={broker}, "
            f"symbol={canonical}, timeframe={timeframe}."
        )
    return files


def latest_normalized_tick_file(config: ProjectConfig, broker: str, symbol: str) -> Path:
    directory = processed_ticks_dir(config, broker, symbol)
    files = sorted(directory.glob("*_ticks_*.csv"))
    if not files:
        raise ConfigError(
            f"No normalized tick files found in {directory}. "
            f"Run `python -m phase0 normalize-data --broker {broker} --symbol {symbol}` first."
        )
    return files[-1]


def read_csv(path: str | Path) -> pd.DataFrame:
    resolved = Path(path)
    if not resolved.exists():
        raise ConfigError(f"CSV file not found: {resolved}.")
    try:
        return pd.read_csv(resolved)
    except Exception as exc:  # pandas exposes several parser-specific exceptions
        raise ConfigError(f"Failed to read CSV file {resolved}: {exc}") from exc


def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(resolved, index=False)
    return resolved


def _matches_symbol(path: Path, aliases: set[str]) -> bool:
    name = path.name.lower()
    return any(alias and alias in name for alias in aliases)
