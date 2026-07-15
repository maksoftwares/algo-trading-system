from __future__ import annotations

import numpy as np
import pytest

from conftest import bars
from xau_crossasset_residual.core import INSTRUMENTS, add_log_returns, synchronize_m5


def test_all_four_instruments_are_required_for_synchronization():
    with pytest.raises(ValueError, match="four"):
        synchronize_m5({"XAUUSD": bars([0])})


@pytest.mark.parametrize("missing", list(INSTRUMENTS))
def test_each_missing_instrument_excludes_the_common_bar(missing):
    frames = {symbol: bars([0, 300_000]) for symbol in INSTRUMENTS}
    frames[missing] = bars([0])
    synchronized, excluded = synchronize_m5(frames)
    assert synchronized.timestamp_ms.tolist() == [0]
    assert excluded.iloc[0].missing_instruments == missing


def test_synchronization_uses_exact_intersection_without_forward_fill():
    frames = {symbol: bars([0, 600_000]) for symbol in INSTRUMENTS}
    frames["XAGUSD"] = bars([0, 300_000, 600_000])
    synchronized, _ = synchronize_m5(frames)
    assert synchronized.timestamp_ms.tolist() == [0, 600_000]
    assert not synchronized.isna().any().any()


def test_log_returns_require_an_exact_previous_synchronized_m5_bar():
    frames = {symbol: bars([0, 300_000, 900_000], 10.0) for symbol in INSTRUMENTS}
    synchronized, _ = synchronize_m5(frames)
    result = add_log_returns(synchronized)
    assert np.isnan(result.at[0, "r_xau"])
    assert result.at[1, "r_xau"] == pytest.approx(np.log(11 / 10))
    assert np.isnan(result.at[2, "r_xau"])
