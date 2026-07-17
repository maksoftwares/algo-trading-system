from __future__ import annotations

import pandas as pd

from portability import ema_trend_stack


def test_ema_trend_stack_requires_price_order_and_both_positive_slopes():
    close = pd.Series([100.0 + index for index in range(120)])
    frame = pd.DataFrame({"bid_close": close})

    result = ema_trend_stack(frame, 20, 50, 5)

    assert result.iloc[-1]["trend_up"]
    assert result.iloc[-1]["supportive_up"]


def test_ema_trend_stack_rejects_falling_market():
    close = pd.Series([220.0 - index for index in range(120)])
    frame = pd.DataFrame({"bid_close": close})

    result = ema_trend_stack(frame, 20, 50, 5)

    assert not result.iloc[-1]["trend_up"]
    assert not result.iloc[-1]["supportive_up"]
