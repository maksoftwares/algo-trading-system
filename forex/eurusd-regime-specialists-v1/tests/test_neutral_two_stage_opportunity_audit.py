from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from eurusd_regime_specialists.neutral_two_stage_opportunity_audit import (
    assert_development_only,
    success_score,
)


def test_success_score_requires_opportunity_and_side_confidence() -> None:
    scores = success_score(
        np.array([0.8, 0.8, 0.4]),
        np.array([0.5, 0.9, 0.9]),
    )
    assert scores.tolist() == pytest.approx([0.4, 0.72, 0.36])


def test_development_guard_rejects_forward_row() -> None:
    cfg = {
        "forward_policy": {
            "forward_start_utc": "2023-01-01T00:00:00Z"
        }
    }
    points = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-12-30T00:00:00Z", "2023-01-02T00:00:00Z"],
                utc=True,
            )
        }
    )
    with pytest.raises(RuntimeError, match="Forward outcome"):
        assert_development_only(points, cfg)


def test_development_guard_accepts_pre_forward_rows() -> None:
    cfg = {
        "forward_policy": {
            "forward_start_utc": "2023-01-01T00:00:00Z"
        }
    }
    points = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-12-30T00:00:00Z"], utc=True
            )
        }
    )
    assert_development_only(points, cfg)
