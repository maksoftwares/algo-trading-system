from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists import rsi_regime_chronological_selector as module


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def _table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "causal_regime": "NEUTRAL",
                "regime_index": 0,
                "trades": 30,
                "profit_factor": 1.3,
                "plus_0_5_pip_profit_factor": 1.2,
                "top_5pct_removed_profit_factor": 1.1,
                "trade_sequence_half_profit_factors": [1.1, 1.1],
                "net_pnl_usd": 10.0,
            },
            {
                "causal_regime": "SHOCK",
                "regime_index": 1,
                "trades": 30,
                "profit_factor": 0.9,
                "plus_0_5_pip_profit_factor": 0.8,
                "top_5pct_removed_profit_factor": 0.7,
                "trade_sequence_half_profit_factors": [0.8, 1.0],
                "net_pnl_usd": -2.0,
            },
        ]
    )


def test_selects_only_regimes_passing_every_development_gate() -> None:
    config = _config()
    assert module.select_regimes(_table(), config) == ["NEUTRAL"]


def test_validation_outcomes_cannot_change_development_selection() -> None:
    config = _config()
    table = _table()
    before = module.select_regimes(table, config)
    validation = pd.DataFrame(
        {
            "causal_regime": ["NEUTRAL"],
            "pnl_usd": [-1000.0],
        }
    )
    changed = copy.deepcopy(validation)
    changed["pnl_usd"] = 1000.0
    assert module.select_regimes(table, config) == before


def test_sequence_halves_are_chronological_by_exit() -> None:
    frame = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2025-01-01T00:00:00Z",
                    "2025-01-02T00:00:00Z",
                    "2025-01-03T00:00:00Z",
                    "2025-01-04T00:00:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2025-01-01T01:00:00Z",
                    "2025-01-02T01:00:00Z",
                    "2025-01-03T01:00:00Z",
                    "2025-01-04T01:00:00Z",
                ]
            ),
            "pnl_usd": [2.0, -1.0, 3.0, -1.0],
        }
    )
    assert module.sequence_half_profit_factors(frame) == [2.0, 3.0]


def test_fixed_lot_normalization_is_linear() -> None:
    config = _config()
    fixed_lot = float(config["rsi_contract"]["fixed_lot"])
    assert 9.2 * fixed_lot / 0.1 == 0.9199999999999999


def test_config_is_research_only_and_never_authorizes_orders() -> None:
    config = module.load_config()
    assert config["result_can_count_as_forward_evidence"] is False
    assert config["demo_order_authorized"] is False
    assert "NO_VALIDATION_BASED_REGIME_SELECTION" in config["prohibitions"]
    assert "NO_ORDER_AUTHORIZATION" in config["prohibitions"]
