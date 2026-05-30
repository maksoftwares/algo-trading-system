from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "h4_credit_spread_stress_momentum_v0"
EXPERT_NAMES = (
    "h4_credit_spread_stress_momentum_v0",
    "h1_credit_spread_shock_reversal_v0",
    "h1_credit_spread_shock_followthrough_v0",
)
CREDIT_SPREAD_FRAME_KEY = "credit_spread"
CREDIT_SPREAD_RAW_DIR = Path("data/raw/credit_spread")
BAA10Y_FILE = "FRED_BAA10Y.csv"
AAA10Y_FILE = "FRED_AAA10Y.csv"


def load_credit_spread_context(
    config: ProjectConfig,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    directory = config.root / CREDIT_SPREAD_RAW_DIR
    baa10y = _load_fred_series(directory / BAA10Y_FILE, "BAA10Y", "baa10y")
    aaa10y = _load_fred_series(directory / AAA10Y_FILE, "AAA10Y", "aaa10y")
    frame = (
        baa10y.merge(aaa10y, on="timestamp_utc", how="outer")
        .sort_values("timestamp_utc")
        .ffill()
        .dropna(subset=["baa10y", "aaa10y"])
        .reset_index(drop=True)
    )
    _assert_credit_spread_coverage(frame, directory, required_start, required_end)
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


def _assert_credit_spread_coverage(
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
