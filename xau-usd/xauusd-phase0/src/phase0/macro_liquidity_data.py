from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "d1_macro_liquidity_regime_v0"
EXPERT_NAMES = (EXPERT_NAME,)
MACRO_LIQUIDITY_FRAME_KEY = "macro_liquidity"
LIQUIDITY_RAW_DIR = Path("data/raw/liquidity")
MACRO_RAW_DIR = Path("data/raw/macro")
WALCL_FILE = "FRED_WALCL.csv"
DOLLAR_INDEX_FILE = "FRED_DTWEXBGS.csv"


def load_macro_liquidity_context(
    config: ProjectConfig,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    liquidity_dir = config.root / LIQUIDITY_RAW_DIR
    macro_dir = config.root / MACRO_RAW_DIR
    walcl = _load_fred_series(liquidity_dir / WALCL_FILE, "WALCL", "fed_total_assets")
    dollar = _load_fred_series(macro_dir / DOLLAR_INDEX_FILE, "DTWEXBGS", "dollar_index_broad")
    frame = (
        walcl.merge(dollar, on="timestamp_utc", how="outer")
        .sort_values("timestamp_utc")
        .ffill()
        .dropna(subset=["fed_total_assets", "dollar_index_broad"])
        .reset_index(drop=True)
    )
    _assert_coverage(frame, liquidity_dir, required_start, required_end)
    return frame


def _load_fred_series(path: Path, fred_column: str, output_column: str) -> pd.DataFrame:
    if not path.exists():
        raise ConfigError(
            f"{EXPERT_NAME} requires {path}. Fetch the public FRED CSV before any real matrix run."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ConfigError(f"Failed to read {EXPERT_NAME} FRED file {path}: {exc}") from exc

    required = {"observation_date", fred_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ConfigError(f"{path} missing required FRED column(s): {', '.join(sorted(missing))}.")

    output = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
            output_column: pd.to_numeric(frame[fred_column], errors="coerce"),
        }
    )
    output = output.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    if output.empty:
        raise ConfigError(f"{path} has no usable {fred_column} observations.")
    return output


def _assert_coverage(
    frame: pd.DataFrame,
    source: Path,
    required_start: object,
    required_end: object,
) -> None:
    coverage_start = pd.Timestamp(frame["timestamp_utc"].min())
    coverage_end = pd.Timestamp(frame["timestamp_utc"].max())
    needed_start = _utc_timestamp(required_start)
    needed_end = _utc_timestamp(required_end)
    allowed_start_gap = pd.Timedelta(days=10)
    allowed_end_gap = pd.Timedelta(days=10)
    if coverage_start > needed_start and coverage_start - needed_start > allowed_start_gap:
        raise ConfigError(
            f"{EXPERT_NAME} macro-liquidity data in {source} start {coverage_start.isoformat()}, "
            f"but required {needed_start.isoformat()}."
        )
    if coverage_end < needed_end and needed_end - coverage_end > allowed_end_gap:
        raise ConfigError(
            f"{EXPERT_NAME} macro-liquidity data in {source} end {coverage_end.isoformat()}, "
            f"but required {needed_end.isoformat()}."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
