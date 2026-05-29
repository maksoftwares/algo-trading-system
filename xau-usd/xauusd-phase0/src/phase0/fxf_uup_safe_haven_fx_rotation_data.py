from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0"
EXPERT_NAMES = ("h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0",)
FXF_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY = "fxf_uup_safe_haven_fx_rotation"
FXF_UUP_SAFE_HAVEN_FX_ROTATION_REFERENCE_PATH = Path("data/reference/etf/fxf_uup_daily_yahoo_2015_2025.csv")


def load_fxf_uup_safe_haven_fx_rotation_context(
    config: ProjectConfig,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    path = config.root / FXF_UUP_SAFE_HAVEN_FX_ROTATION_REFERENCE_PATH
    if not path.exists():
        raise ConfigError(
            f"{EXPERT_NAME} requires {path}. Run scripts/acquire_fxf_uup_safe_haven_fx_rotation_proxy.py "
            "before any real matrix run. This is a public FXF/UUP ETF daily OHLCV proxy, "
            "not primary FX spot, futures positioning, or order-flow data."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ConfigError(f"Failed to read {EXPERT_NAME} FXF/UUP proxy file {path}: {exc}") from exc

    required_columns = {
        "timestamp_utc",
        "fxf_close",
        "fxf_volume",
        "uup_close",
        "uup_volume",
        "source",
    }
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ConfigError(f"{path} missing required FXF/UUP column(s): {', '.join(sorted(missing))}.")

    frame = frame.copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("fxf_close", "fxf_volume", "uup_close", "uup_volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "fxf_close", "uup_close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    if frame.empty:
        raise ConfigError(f"{path} has no usable FXF/UUP rows.")

    _assert_coverage(frame, path, required_start, required_end)
    return frame


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
    allowed_start_gap = pd.Timedelta(days=370)
    allowed_end_gap = pd.Timedelta(days=5)
    if coverage_start > needed_start and coverage_start - needed_start > allowed_start_gap:
        raise ConfigError(
            f"{EXPERT_NAME} FXF/UUP data in {source} start {coverage_start.isoformat()}, "
            f"but required {needed_start.isoformat()}."
        )
    if coverage_end < needed_end and needed_end - coverage_end > allowed_end_gap:
        raise ConfigError(
            f"{EXPERT_NAME} FXF/UUP data in {source} end {coverage_end.isoformat()}, "
            f"but required {needed_end.isoformat()}."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
