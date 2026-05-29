from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig


EXPERT_NAME = "cot_gold_positioning_reversal_v0"
EXPERT_NAMES = (
    "cot_gold_positioning_reversal_v0",
    "h1_cot_positioning_continuation_v0",
)
COT_FRAME_KEY = "cot_gold"
COT_REFERENCE_PATH = Path("data/reference/cot/gold_disaggregated_futures_only_2016_2024.csv")


def load_cot_gold_context(config: ProjectConfig, required_start: object, required_end: object) -> pd.DataFrame:
    path = config.root / COT_REFERENCE_PATH
    if not path.exists():
        raise ConfigError(
            f"{EXPERT_NAME} requires {path}. Build the gold-only CFTC COT reference CSV "
            "from official disaggregated futures-only annual files before any real matrix run."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ConfigError(f"Failed to read {EXPERT_NAME} COT reference file {path}: {exc}") from exc

    required_columns = {
        "report_date",
        "cftc_contract_market_code",
        "open_interest_all",
        "producer_long_all",
        "producer_short_all",
        "managed_money_long_all",
        "managed_money_short_all",
    }
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ConfigError(f"{path} missing required COT column(s): {', '.join(sorted(missing))}.")

    frame = frame.copy()
    frame["report_date"] = pd.to_datetime(frame["report_date"], utc=True, errors="coerce")
    frame["cftc_contract_market_code"] = frame["cftc_contract_market_code"].astype(str).str.zfill(6)
    frame = frame[frame["cftc_contract_market_code"] == "088691"].copy()
    numeric_columns = [
        "open_interest_all",
        "producer_long_all",
        "producer_short_all",
        "managed_money_long_all",
        "managed_money_short_all",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["report_date", *numeric_columns]).sort_values("report_date")
    frame = frame.drop_duplicates("report_date").reset_index(drop=True)
    if frame.empty:
        raise ConfigError(f"{path} has no usable CFTC gold rows.")

    _assert_cot_coverage(frame, path, required_start, required_end)
    return frame


def _assert_cot_coverage(
    frame: pd.DataFrame,
    source: Path,
    required_start: object,
    required_end: object,
) -> None:
    coverage_start = pd.Timestamp(frame["report_date"].min())
    coverage_end = pd.Timestamp(frame["report_date"].max())
    needed_start = _utc_timestamp(required_start)
    needed_end = _utc_timestamp(required_end)
    allowed_start_gap = pd.Timedelta(days=14)
    allowed_end_gap = pd.Timedelta(days=14)
    if coverage_start > needed_start and coverage_start - needed_start > allowed_start_gap:
        raise ConfigError(
            f"{EXPERT_NAME} COT data in {source} start {coverage_start.isoformat()}, "
            f"but required {needed_start.isoformat()}."
        )
    if coverage_end < needed_end and needed_end - coverage_end > allowed_end_gap:
        raise ConfigError(
            f"{EXPERT_NAME} COT data in {source} end {coverage_end.isoformat()}, "
            f"but required {needed_end.isoformat()}."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
