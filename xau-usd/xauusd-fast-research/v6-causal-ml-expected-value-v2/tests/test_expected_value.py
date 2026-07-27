from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.expected_value import (
    annual_training_rows,
    clipped_target,
    rank_correlation,
    verify_sources,
)


def test_clipped_target_limits_tail_winners_and_losses():
    values = clipped_target(np.array([-3.0, -1.0, 1.0, 8.0]), -1.25, 3.0)
    assert values.tolist() == [-1.25, -1.0, 1.0, 3.0]


def test_clipped_target_requires_bounds_around_zero():
    with pytest.raises(ValueError, match="straddle zero"):
        clipped_target(np.array([1.0]), 0.0, 3.0)


def test_annual_training_rows_obey_exit_purge():
    corpus = pd.DataFrame(
        {
            "exit_time": pd.to_datetime(
                ["2021-12-29 23:00", "2021-12-30 01:00", "2022-01-01 00:00"],
                utc=True,
            )
        }
    )
    train = annual_training_rows(corpus, 2022, 48)
    assert train["exit_time"].tolist() == [
        pd.Timestamp("2021-12-29 23:00", tz="UTC")
    ]


def test_rank_correlation_recognizes_ordering():
    actual = np.array([-1.0, 0.0, 2.0, 3.0])
    assert rank_correlation(actual, actual) == pytest.approx(1.0)
    assert rank_correlation(actual, -actual) == pytest.approx(-1.0)


def test_verify_sources_fails_closed(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("changed", encoding="utf-8")
    config = {
        "sources": {
            "source": {"path": str(source), "sha256": "0" * 64}
        }
    }
    with pytest.raises(ValueError, match="Locked source drift"):
        verify_sources(config)
