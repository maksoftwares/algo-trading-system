from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "h4_gvz_volatility_panic_reversal_v0"
GVZ_FRAME_KEY = "gvz_volatility"
GVZ_RAW_DIR = Path("data/raw/options")
GVZ_FILE = "FRED_GVZCLS.csv"


def load_gvz_volatility_context(
    config: ProjectConfig,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    path = config.root / GVZ_RAW_DIR / GVZ_FILE
    if not path.exists():
        raise ConfigError(
            f"{EXPERT_NAME} requires {path}. Fetch the public FRED GVZCLS CSV before "
            "any real matrix run."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ConfigError(f"Failed to read {EXPERT_NAME} GVZ file {path}: {exc}") from exc

    required = {"observation_date", "GVZCLS"}
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
            "gvz_close": pd.to_numeric(frame["GVZCLS"], errors="coerce"),
        }
    )
    output = output.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    if output.empty:
        raise ConfigError(f"{path} has no usable GVZCLS observations.")

    _assert_gvz_coverage(output, path, required_start, required_end)
    return output


def _assert_gvz_coverage(
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
            f"{EXPERT_NAME} GVZ data in {source} start {coverage_start.isoformat()}, "
            f"but required {needed_start.isoformat()}."
        )
    if coverage_end < needed_end and needed_end - coverage_end > allowed_boundary_gap:
        raise ConfigError(
            f"{EXPERT_NAME} GVZ data in {source} end {coverage_end.isoformat()}, "
            f"but required {needed_end.isoformat()}."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
