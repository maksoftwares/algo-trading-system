from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from src.foundation import (
    BAR_WIDTH_MS,
    add_causal_features,
    aggregate_m5,
    decode_vol_payload,
    validate_curated,
)


@dataclass
class Tick:
    timestamp_ms: int
    bid: float
    ask: float


def test_aggregate_m5_is_side_correct_and_available_at_bar_end() -> None:
    ticks = [
        Tick(1_000, 20.0, 20.2),
        Tick(2_000, 20.3, 20.5),
        Tick(BAR_WIDTH_MS + 1_000, 19.9, 20.1),
    ]
    result = aggregate_m5(ticks)
    assert len(result) == 2
    assert result.loc[0, "vol_bid_open"] == pytest.approx(20.0)
    assert result.loc[0, "vol_ask_close"] == pytest.approx(20.5)
    assert result.loc[0, "vol_mid_high"] == pytest.approx(20.4)
    assert result.loc[0, "available_timestamp_ms"] == BAR_WIDTH_MS
    assert result.loc[0, "source_last_timestamp_ms"] == 2_000


def test_causal_returns_do_not_bridge_missing_bars() -> None:
    ticks = [
        Tick(1_000, 20.0, 20.2),
        Tick(BAR_WIDTH_MS + 1_000, 20.2, 20.4),
        Tick(3 * BAR_WIDTH_MS + 1_000, 20.4, 20.6),
    ]
    result = add_causal_features(aggregate_m5(ticks))
    assert pd.notna(result.loc[1, "vol_return_5m"])
    assert pd.isna(result.loc[2, "vol_return_5m"])


def test_validation_rejects_outcomes_duplicates_and_bad_availability() -> None:
    result = aggregate_m5([Tick(1_000, 20.0, 20.2)])
    with_outcome = result.assign(pnl=1.0)
    with pytest.raises(ValueError, match="Outcome-bearing"):
        validate_curated(with_outcome)
    duplicate = pd.concat([result, result], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_curated(duplicate)
    bad = result.copy()
    bad["available_timestamp_ms"] -= 1
    with pytest.raises(ValueError, match="noncausal"):
        validate_curated(bad)


def test_crossed_quotes_are_counted_and_bounded() -> None:
    raw = b'{"timestamp":1000,"multiplier":1,"bid":20,"ask":21,"times":[1,1],"bids":[0,2],"asks":[0,0],"bidVolumes":[1,1],"askVolumes":[1,1]}'
    ticks, quality = decode_vol_payload(raw, maximum_invalid_fraction=0.5)
    assert len(ticks) == 1
    assert quality["invalid_tick_count"] == 1
    with pytest.raises(ValueError, match="invalid quote fraction"):
        decode_vol_payload(raw, maximum_invalid_fraction=0.49)
