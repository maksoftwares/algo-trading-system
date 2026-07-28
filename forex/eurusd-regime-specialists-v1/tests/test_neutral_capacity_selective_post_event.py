from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_capacity_selective_post_event import (  # noqa: E402
    choose_capacity_threshold,
    threshold_counts,
)


def config() -> dict:
    return {
        "capacity_calibration": {
            "threshold_ladder_descending": [0.42, 0.41, 0.4],
            "minimum_candidates_each_forward_window": 2,
        },
        "forward_windows": ["a", "b"],
        "windows": {
            "a": [
                "2023-01-01T00:00:00Z",
                "2023-12-31T23:59:59Z",
            ],
            "b": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ],
        },
    }


def scored() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2023-01-01T12:00:00Z",
                    "2023-02-01T12:00:00Z",
                    "2023-03-01T12:00:00Z",
                    "2024-01-01T12:00:00Z",
                    "2024-02-01T12:00:00Z",
                    "2024-03-01T12:00:00Z",
                ],
                utc=True,
            ),
            "model_selection_probability": [
                0.43,
                0.415,
                0.405,
                0.425,
                0.405,
                0.395,
            ],
        }
    )


def test_capacity_ladder_uses_highest_threshold_meeting_all_windows() -> None:
    counts = threshold_counts(scored(), config())
    assert counts["0.42"] == {"a": 1, "b": 1}
    assert counts["0.41"] == {"a": 2, "b": 1}
    assert counts["0.4"] == {"a": 3, "b": 2}
    assert choose_capacity_threshold(counts, config()) == 0.4


def test_capacity_ladder_returns_none_when_no_threshold_has_capacity() -> None:
    cfg = config()
    cfg["capacity_calibration"][
        "minimum_candidates_each_forward_window"
    ] = 4
    counts = threshold_counts(scored(), cfg)
    assert choose_capacity_threshold(counts, cfg) is None
