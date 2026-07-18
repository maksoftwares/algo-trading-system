from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio import build_weighted_trades, generate_manifest  # noqa: E402


def _config() -> dict:
    return {
        "components": [
            {"attempt_no": 1, "weights": [0.75, 1.0]},
            {"attempt_no": 2, "weights": [0.0, 0.5]},
            {"attempt_no": 3, "weights": [0.75, 1.0]},
            {"attempt_no": 4, "weights": [0.25, 0.5]},
        ],
        "selection": {
            "attempt_first": 10,
            "attempt_last": 41,
            "attempt_count": 32,
            "tie_priorities": ["ATTEMPT_ASCENDING", "ATTEMPT_DESCENDING"],
        },
    }


def test_manifest_is_complete_and_contiguous() -> None:
    manifest = generate_manifest(_config())
    assert len(manifest) == 32
    assert manifest["attempt_no"].tolist() == list(range(10, 42))
    assert manifest["portfolio_id"].is_unique


def test_zero_weight_is_excluded_and_returns_are_scaled() -> None:
    start = pd.Timestamp("2024-01-02T10:00:00Z")
    trades = pd.DataFrame(
        {
            "attempt_no": [1, 2],
            "entry_time": [start, start + pd.Timedelta(hours=2)],
            "exit_time": [
                start + pd.Timedelta(hours=1),
                start + pd.Timedelta(hours=3),
            ],
            "stress_net_r": [2.0, 5.0],
            "gross_r": [2.1, 5.1],
        }
    )
    policy = SimpleNamespace(
        attempt_no=10,
        portfolio_id="p",
        weights_json='{"1":0.5,"2":0.0}',
        tie_priority="ATTEMPT_ASCENDING",
    )
    result = build_weighted_trades(trades, policy, 4)
    assert result["component_attempt_no"].tolist() == [1]
    assert result["component_stress_net_r"].tolist() == [2.0]
    assert result["stress_net_r"].tolist() == [1.0]
    assert result["risk_weight"].tolist() == [0.5]


def test_tie_priority_changes_selected_component() -> None:
    start = pd.Timestamp("2024-01-02T10:00:00Z")
    trades = pd.DataFrame(
        {
            "attempt_no": [1, 2],
            "entry_time": [start, start],
            "exit_time": [start + pd.Timedelta(hours=1)] * 2,
            "stress_net_r": [1.0, -1.0],
            "gross_r": [1.1, -0.9],
        }
    )
    first = SimpleNamespace(
        attempt_no=10,
        portfolio_id="a",
        weights_json='{"1":1.0,"2":1.0}',
        tie_priority="ATTEMPT_ASCENDING",
    )
    second = SimpleNamespace(
        attempt_no=11,
        portfolio_id="b",
        weights_json='{"1":1.0,"2":1.0}',
        tie_priority="ATTEMPT_DESCENDING",
    )
    assert build_weighted_trades(trades, first, 4)["component_attempt_no"].tolist() == [1]
    assert build_weighted_trades(trades, second, 4)["component_attempt_no"].tolist() == [2]

