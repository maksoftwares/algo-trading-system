from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from composite import build_composite_trades, generate_manifest  # noqa: E402


def _config() -> dict:
    return {
        "component_pool": [
            {"attempt_no": value} for value in (1, 2, 3, 4)
        ],
        "selection": {
            "attempt_first": 10,
            "attempt_last": 31,
            "attempt_count": 22,
            "minimum_subset_size": 2,
            "maximum_subset_size": 4,
            "tie_priorities": ["ATTEMPT_ASCENDING", "ATTEMPT_DESCENDING"],
        },
    }


def test_manifest_contains_all_22_locked_policies() -> None:
    manifest = generate_manifest(_config())
    assert len(manifest) == 22
    assert manifest["attempt_no"].tolist() == list(range(10, 32))
    assert set(manifest["component_count"]) == {2, 3, 4}


def test_tie_priority_selects_one_overlapping_trade() -> None:
    start = pd.Timestamp("2024-01-02T10:00:00Z")
    trades = pd.DataFrame(
        {
            "attempt_no": [1, 2],
            "entry_time": [start, start],
            "exit_time": [start + pd.Timedelta(hours=1)] * 2,
            "stress_net_r": [1.0, -1.0],
        }
    )
    ascending = SimpleNamespace(
        attempt_no=10,
        composite_id="a",
        component_attempts_json="[1, 2]",
        tie_priority="ATTEMPT_ASCENDING",
    )
    descending = SimpleNamespace(
        attempt_no=11,
        composite_id="b",
        component_attempts_json="[1, 2]",
        tie_priority="ATTEMPT_DESCENDING",
    )
    first = build_composite_trades(trades, ascending, 4)
    second = build_composite_trades(trades, descending, 4)
    assert first["component_attempt_no"].tolist() == [1]
    assert second["component_attempt_no"].tolist() == [2]


def test_composite_rejects_overlaps_and_honors_daily_cap() -> None:
    start = pd.Timestamp("2024-01-02T10:00:00Z")
    entries = [start + pd.Timedelta(hours=value) for value in (0, 0.5, 2, 4)]
    trades = pd.DataFrame(
        {
            "attempt_no": [1, 2, 1, 2],
            "entry_time": entries,
            "exit_time": [value + pd.Timedelta(hours=1) for value in entries],
            "stress_net_r": [1.0] * 4,
        }
    )
    policy = SimpleNamespace(
        attempt_no=10,
        composite_id="a",
        component_attempts_json="[1, 2]",
        tie_priority="ATTEMPT_ASCENDING",
    )
    result = build_composite_trades(trades, policy, 2)
    assert len(result) == 2
    assert result["entry_time"].tolist() == [entries[0], entries[2]]

