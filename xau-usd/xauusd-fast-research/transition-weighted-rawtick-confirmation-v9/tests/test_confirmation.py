from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from confirmation import component_candidates, simulate_components  # noqa: E402


class Campaign:
    @staticmethod
    def signal_mask_direction(frame, mechanic, params):
        return pd.Series([True], index=frame.index), pd.Series([1], index=frame.index)


def test_candidate_maps_through_full_execution_index() -> None:
    times = pd.date_range("2024-01-02T00:15:00Z", periods=6, freq="15min")
    execution = pd.DataFrame(
        {
            "timestamp_utc": times,
            "bar_start_utc": times - pd.Timedelta(minutes=15),
        }
    )
    decisions = pd.DataFrame(
        {"timestamp_utc": [times[3]], "execution_index": [3], "atr14": [2.0]}
    )
    source = SimpleNamespace(
        attempt_no=1,
        variant_id="v",
        regime_owner="TRANSITION",
        mechanic="M",
        geometry_id="G",
        parameters_json="{}",
        raw_signal_count=1,
    )
    source_config = {
        "geometries": {
            "TRANSITION": {
                "G": {
                    "stop_atr": 1.0,
                    "target_r": 2.0,
                    "maximum_hold_hours": 1.0,
                }
            }
        }
    }
    confirmation = {
        "source": {"end_exclusive_utc": "2024-02-01T00:00:00Z"},
        "execution": {"maximum_entry_gap_minutes": 20},
    }
    result = component_candidates(
        decisions, execution, source, Campaign, source_config, confirmation
    )
    assert result["scheduled_entry_time"].iat[0] == execution["bar_start_utc"].iat[4]


def test_component_overlap_is_isolated_by_attempt() -> None:
    time = pd.Timestamp("2024-01-02T10:00:00Z")
    candidates = pd.DataFrame(
        {
            "candidate_id": ["a", "b"],
            "origin_attempt": [1, 2],
            "scheduled_entry_time": [time, time],
        }
    )

    def execute(candidate, tick_store, quote_type, execution):
        return (
            {
                "candidate_id": candidate.candidate_id,
                "entry_time": time,
                "exit_time": time + pd.Timedelta(hours=1),
            },
            None,
        )

    result, _ = simulate_components(
        candidates,
        object(),
        object(),
        {"maximum_trades_per_component_utc_day": 4},
        execute,
    )
    assert result["attempt_no"].tolist() == [1, 2]

