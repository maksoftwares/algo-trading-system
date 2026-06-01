from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "h4_cme_cvol_skew_reversal_v0"
EXPERT_NAMES = (EXPERT_NAME,)
CME_CVOL_GOLD_FRAME_KEY = "cme_cvol_gold"
CME_CVOL_GOLD_REFERENCE_PATH = Path("data/reference/options/cme_cvol_gold_daily.csv")


def load_cme_cvol_gold_context(
    config: ProjectConfig,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    path = config.root / CME_CVOL_GOLD_REFERENCE_PATH
    if not path.exists():
        raise ConfigError(
            f"{EXPERT_NAME} requires licensed CME Gold CVOL/skew history at {path}. "
            "Expected columns: timestamp_utc, gold_cvol, gold_upvar, gold_downvar, "
            "gold_skew, gold_atm, gold_convexity. Do not run a partial matrix until "
            "the file covers the full required window."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ConfigError(f"Failed to read {EXPERT_NAME} CME CVOL file {path}: {exc}") from exc

    required_columns = {
        "timestamp_utc",
        "gold_cvol",
        "gold_upvar",
        "gold_downvar",
        "gold_skew",
        "gold_atm",
        "gold_convexity",
    }
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ConfigError(
            f"{path} missing required CME CVOL column(s): {', '.join(sorted(missing))}."
        )

    output = frame.copy()
    output["timestamp_utc"] = pd.to_datetime(output["timestamp_utc"], utc=True, errors="coerce")
    for column in (
        "gold_cvol",
        "gold_upvar",
        "gold_downvar",
        "gold_skew",
        "gold_atm",
        "gold_convexity",
    ):
        output[column] = pd.to_numeric(output[column], errors="coerce")
    output = output.dropna(subset=["timestamp_utc", "gold_cvol", "gold_upvar", "gold_downvar"])
    output = output.sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(
        drop=True
    )
    if output.empty:
        raise ConfigError(f"{path} has no usable CME Gold CVOL rows.")

    _assert_coverage(output, path, required_start, required_end)
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
    allowed_end_gap = pd.Timedelta(days=5)
    if coverage_start > needed_start and coverage_start - needed_start > allowed_start_gap:
        raise ConfigError(
            f"{EXPERT_NAME} CME Gold CVOL data in {source} start "
            f"{coverage_start.isoformat()}, but required {needed_start.isoformat()}."
        )
    if coverage_end < needed_end and needed_end - coverage_end > allowed_end_gap:
        raise ConfigError(
            f"{EXPERT_NAME} CME Gold CVOL data in {source} end "
            f"{coverage_end.isoformat()}, but required {needed_end.isoformat()}."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
