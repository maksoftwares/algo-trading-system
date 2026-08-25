from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.policy import followthrough_mask


POLICY = {
    "minimum_ret_24h_exclusive": 0.0,
    "maximum_ret_4h_to_ret_24h_exclusive": 0.7,
    "missing_feature_action": "RETAIN",
}


def test_weak_recent_followthrough_is_selected() -> None:
    frame = pd.DataFrame({"ret_4h": [6.0], "ret_24h": [10.0]})
    assert bool(followthrough_mask(frame, POLICY).iloc[0])


def test_boundary_and_strong_followthrough_retain() -> None:
    frame = pd.DataFrame({"ret_4h": [7.0, 8.0], "ret_24h": [10.0, 10.0]})
    assert followthrough_mask(frame, POLICY).tolist() == [False, False]


def test_missing_or_nonpositive_anchor_retains() -> None:
    frame = pd.DataFrame(
        {"ret_4h": [np.nan, 1.0, -1.0], "ret_24h": [10.0, 0.0, -2.0]}
    )
    assert followthrough_mask(frame, POLICY).tolist() == [False, False, False]


def test_required_columns_are_enforced() -> None:
    with pytest.raises(ValueError, match="Missing follow-through features"):
        followthrough_mask(pd.DataFrame({"ret_4h": [1.0]}), POLICY)
