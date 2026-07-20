from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from replication import execute_rule, select_rule  # noqa: E402


RULE = {
    "excluded_regime": "UNSAFE_SHOCK",
    "action_id": "SWING_2R_36H",
    "h1_adx_exclusive_minimum": 20.0,
    "h1_adx_inclusive_maximum": 30.0,
    "maximum_directional_return_1h_atr": -0.25,
    "maximum_open_positions": 1,
    "maximum_entries_per_utc_date": 2,
}


def action(event_id: str, entry: str, exit_time: str, adx: float = 25.0) -> dict[str, object]:
    return {
        "event_id": event_id,
        "signal_time": pd.Timestamp(entry) - pd.Timedelta(minutes=5),
        "entry_time": pd.Timestamp(entry),
        "exit_time": pd.Timestamp(exit_time),
        "direction": "LONG",
        "regime": "TREND_UP",
        "action_id": "SWING_2R_36H",
        "h1_adx": adx,
        "dir_return_1h_atr": -0.30,
        "stress_net_r": 1.0,
        "risk_usd": 5.0,
    }


def test_rule_boundaries_are_exact() -> None:
    frame = pd.DataFrame(
        [
            action("A", "2026-01-05T00:00:00Z", "2026-01-05T01:00:00Z", 20.0),
            action("B", "2026-01-05T02:00:00Z", "2026-01-05T03:00:00Z", 20.01),
            action("C", "2026-01-05T04:00:00Z", "2026-01-05T05:00:00Z", 30.0),
            action("D", "2026-01-05T06:00:00Z", "2026-01-05T07:00:00Z", 30.01),
        ]
    )
    selected = select_rule(frame, RULE)
    assert selected["event_id"].tolist() == ["B", "C"]


def test_one_open_position_allows_entry_at_prior_exit() -> None:
    frame = pd.DataFrame(
        [
            action("A", "2026-01-05T00:00:00Z", "2026-01-05T02:00:00Z"),
            action("B", "2026-01-05T01:00:00Z", "2026-01-05T03:00:00Z"),
            action("C", "2026-01-05T02:00:00Z", "2026-01-05T04:00:00Z"),
        ]
    )
    selected = select_rule(frame, RULE)
    executed = execute_rule(selected, RULE)
    assert executed["event_id"].tolist() == ["A", "C"]
