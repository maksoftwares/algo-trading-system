from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd


def followthrough_mask(frame: pd.DataFrame, policy: Mapping[str, Any]) -> pd.Series:
    missing = {"ret_4h", "ret_24h"} - set(frame.columns)
    if missing:
        raise ValueError(f"Missing follow-through features: {sorted(missing)}")
    ret_4h = pd.to_numeric(frame["ret_4h"], errors="coerce")
    ret_24h = pd.to_numeric(frame["ret_24h"], errors="coerce")
    finite = np.isfinite(ret_4h) & np.isfinite(ret_24h)
    positive_anchor = ret_24h.gt(float(policy["minimum_ret_24h_exclusive"]))
    ratio = ret_4h / ret_24h
    return (
        finite
        & positive_anchor
        & ratio.lt(float(policy["maximum_ret_4h_to_ret_24h_exclusive"]))
    )
