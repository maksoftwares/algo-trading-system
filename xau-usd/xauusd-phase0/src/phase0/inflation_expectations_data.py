from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "h4_breakeven_inflation_momentum_v0"
EXPERT_NAMES = (
    "h4_breakeven_inflation_momentum_v0",
    "h1_breakeven_inflation_shock_reversal_v0",
)
INFLATION_EXPECTATIONS_FRAME_KEY = "inflation_expectations"
INFLATION_EXPECTATIONS_RAW_DIR = Path("data/raw/inflation_expectations")
BREAKEVEN_5Y_FILE = "FRED_T5YIE.csv"
BREAKEVEN_10Y_FILE = "FRED_T10YIE.csv"


def load_inflation_expectations_context(
    config: ProjectConfig,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    directory = config.root / INFLATION_EXPECTATIONS_RAW_DIR
    breakeven_5y = _load_fred_series(directory / BREAKEVEN_5Y_FILE, "T5YIE", "breakeven_5y")
    breakeven_10y = _load_fred_series(
        directory / BREAKEVEN_10Y_FILE,
        "T10YIE",
        "breakeven_10y",
    )
    frame = (
        breakeven_5y.merge(breakeven_10y, on="timestamp_utc", how="outer")
        .sort_values("timestamp_utc")
        .ffill()
        .dropna(subset=["breakeven_5y", "breakeven_10y"])
        .reset_index(drop=True)
    )
    _assert_inflation_expectations_coverage(frame, directory, required_start, required_end)
    return frame


def _load_fred_series(path: Path, fred_column: str, output_column: str) -> pd.DataFrame:
    if not path.exists():
        raise ConfigError(
            f"{EXPERT_NAME} requires {path}. Fetch the public FRED CSV before any real matrix run."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ConfigError(f"Failed to read {EXPERT_NAME} file {path}: {exc}") from exc

    required = {"observation_date", fred_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ConfigError(f"{path} missing required FRED column(s): {', '.join(sorted(missing))}.")

    output = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                frame["observation_date"],
                utc=True,
                errors="coerce",
            ),
            output_column: pd.to_numeric(frame[fred_column], errors="coerce"),
        }
    )
    output = output.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    if output.empty:
        raise ConfigError(f"{path} has no usable {fred_column} observations.")
    return output


def _assert_inflation_expectations_coverage(
    frame: pd.DataFrame,
    source: Path,
    required_start: object,
    required_end: object,
) -> None:
    coverage_start = pd.Timestamp(frame["timestamp_utc"].min())
    coverage_end = pd.Timestamp(frame["timestamp_utc"].max())
    needed_start = _utc_timestamp(required_start)
    needed_end = _utc_timestamp(required_end)
    allowed_boundary_gap = pd.Timedelta(days=10)
    if coverage_start > needed_start and coverage_start - needed_start > allowed_boundary_gap:
        raise ConfigError(
            f"{EXPERT_NAME} data in {source} start {coverage_start.isoformat()}, "
            f"but required {needed_start.isoformat()}."
        )
    if coverage_end < needed_end and needed_end - coverage_end > allowed_boundary_gap:
        raise ConfigError(
            f"{EXPERT_NAME} data in {source} end {coverage_end.isoformat()}, "
            f"but required {needed_end.isoformat()}."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
