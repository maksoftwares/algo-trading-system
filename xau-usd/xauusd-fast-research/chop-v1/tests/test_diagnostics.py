from __future__ import annotations

import pandas as pd

from diagnostics import _boundary_return_probabilities


def test_boundary_return_is_counted_before_one_atr_extension() -> None:
    frame = pd.DataFrame({
        "chop_active": [True] * 5,
        "chop_episode_id": [1] * 5,
        "mid_close": [100.0, 101.2, 100.8, 100.1, 100.0],
        "mid_high": [100.1, 101.3, 101.0, 100.3, 100.2],
        "mid_low": [99.9, 101.0, 100.5, 99.9, 99.8],
    })
    equilibrium = pd.Series([100.0] * 5)
    zscore = pd.Series([0.0, 1.2, 0.8, 0.1, 0.0])
    atr14 = pd.Series([1.0] * 5)

    result = _boundary_return_probabilities(frame, equilibrium, zscore, atr14, 60)

    assert result["boundary_events_1sd"] == 1
    assert result["equilibrium_return_before_1atr_extension_1sd_pct"] == 100.0
    assert result["boundary_events_1p5sd"] == 0
    assert result["equilibrium_return_before_1atr_extension_1p5sd_pct"] is None
