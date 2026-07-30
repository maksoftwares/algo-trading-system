from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists import compression_failed_auction as module


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def _bars(
    rows: list[tuple[float, float, float, float]],
) -> pd.DataFrame:
    index = pd.date_range(
        "2025-01-02T19:45:00Z",
        periods=3,
        freq="5min",
    )
    data = []
    for open_, high, low, close in rows:
        data.append(
            {
                "bid_open": open_,
                "bid_high": high,
                "bid_low": low,
                "bid_close": close,
                "ask_open": open_,
                "ask_high": high,
                "ask_low": low,
                "ask_close": close,
            }
        )
    return pd.DataFrame(data, index=index)


def test_long_signal_requires_completed_failed_downside_auction() -> None:
    bars = _bars(
        [
            (1.1000, 1.1001, 1.0995, 1.0997),
            (1.0997, 1.0999, 1.0994, 1.0998),
            (1.0998, 1.1001, 1.0997, 1.1000),
        ]
    )
    result = module.signal_at_decision(
        bars,
        pd.Timestamp("2025-01-02T20:00:00Z"),
        _config(),
    )
    assert result is not None
    assert result["side"] == "LONG"


def test_short_signal_is_symmetric() -> None:
    bars = _bars(
        [
            (1.1000, 1.1005, 1.0999, 1.1003),
            (1.1003, 1.1006, 1.1001, 1.1002),
            (1.1002, 1.1003, 1.0999, 1.1000),
        ]
    )
    result = module.signal_at_decision(
        bars,
        pd.Timestamp("2025-01-02T20:00:00Z"),
        _config(),
    )
    assert result is not None
    assert result["side"] == "SHORT"


def test_missing_observation_bar_fails_cash() -> None:
    bars = _bars(
        [
            (1.1000, 1.1001, 1.0995, 1.0997),
            (1.0997, 1.0999, 1.0994, 1.0998),
            (1.0998, 1.1001, 1.0997, 1.1000),
        ]
    ).drop(pd.Timestamp("2025-01-02T19:50:00Z"))
    assert (
        module.signal_at_decision(
            bars,
            pd.Timestamp("2025-01-02T20:00:00Z"),
            _config(),
        )
        is None
    )


def test_capacity_gate_is_outcome_independent() -> None:
    config = _config()
    candidates = [
        {
            "decision_date": "2019-01-02",
            "failed_auction_signal": {"side": "LONG"},
            "long_outcome": {"result_r": 1000.0},
        },
        {
            "decision_date": "2025-01-02",
            "failed_auction_signal": {"side": "SHORT"},
            "short_outcome": {"result_r": -1000.0},
        },
    ]
    metrics, _ = module.capacity(candidates, config)
    candidates[0]["long_outcome"]["result_r"] = -1000.0
    candidates[1]["short_outcome"]["result_r"] = 1000.0
    changed, _ = module.capacity(candidates, config)
    assert changed == metrics


def test_config_is_research_only_and_never_authorizes_orders() -> None:
    config = module.load_config()
    assert config["owned_regime"] == "CROSSPAIR_COMPRESSION"
    assert config["result_can_count_as_forward_evidence"] is False
    assert config["demo_order_authorized"] is False
    assert "NO_THRESHOLD_GRID" in config["prohibitions"]
    assert "NO_ORDER_AUTHORIZATION" in config["prohibitions"]
