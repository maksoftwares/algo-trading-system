from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.h4_frequency_completion_portfolio import (
    build_fixed_followthrough_mask,
    deterministic_uniform_scale,
)


def test_followthrough_requires_exact_horizon_and_same_regime() -> None:
    times = pd.date_range(
        "2026-01-05T00:00:00Z", periods=29, freq="15min"
    )
    bars = pd.DataFrame(
        {
            "timestamp": times,
            "complete_bar": True,
            "mid_low": 1.1000,
            "mid_close": 1.1005,
            "body_fraction": 0.8,
            "regime": "chop",
            "atr": 0.001,
        }
    )
    bars.loc[24, ["mid_low", "mid_close"]] = [1.0990, 1.0995]
    bars.loc[27, "mid_close"] = 1.0994
    candidate = {
        "owned_regime": "chop",
        "body_fraction_minimum": 0.35,
    }
    mask = build_fixed_followthrough_mask(bars, candidate, 3)
    assert mask.sum() == 1
    assert bool(mask.iloc[27])
    bars.loc[27, "regime"] = "compression"
    assert not build_fixed_followthrough_mask(
        bars, candidate, 3
    ).any()


def test_deterministic_uniform_scale_uses_tighter_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trades = pd.DataFrame({"r": [2.0, -1.0]})
    monkeypatch.setattr(
        "eurusd_regime_specialists.h4_frequency_completion_portfolio."
        "concurrency_audit",
        lambda _: {"maximum_concurrent_initial_risk_units": 2.5},
    )
    monkeypatch.setattr(
        "eurusd_regime_specialists.h4_frequency_completion_portfolio."
        "_scenario_summary",
        lambda _: {"maximum_drawdown_r": 20.0},
    )
    scale, audit = deterministic_uniform_scale(trades, 1.5, 17.5)
    assert scale == pytest.approx(0.6)
    assert audit["drawdown_scale_ceiling"] == pytest.approx(0.875)
