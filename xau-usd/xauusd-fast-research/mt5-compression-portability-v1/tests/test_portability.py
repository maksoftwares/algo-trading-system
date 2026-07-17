from __future__ import annotations

import pandas as pd

from portability import aggregate_calendar_bars, apply_policy, evaluate_gate


def _m5(starts: list[str]) -> pd.DataFrame:
    timestamps = pd.to_datetime(starts, utc=True)
    frame = pd.DataFrame(
        {
            "bar_start_utc": timestamps,
            "timestamp_utc": timestamps + pd.Timedelta(minutes=5),
        }
    )
    for side, offset in (("bid", 0.0), ("ask", 0.2), ("mid", 0.1)):
        frame[f"{side}_open"] = 100.0 + offset
        frame[f"{side}_high"] = 101.0 + offset
        frame[f"{side}_low"] = 99.0 + offset
        frame[f"{side}_close"] = 100.5 + offset
    return frame


def test_calendar_aggregation_retains_scheduled_gap_bucket():
    starts = [
        f"2026-01-05 {hour:02d}:{minute:02d}:00"
        for hour in (20, 22, 23)
        for minute in range(0, 60, 5)
    ]
    result = aggregate_calendar_bars(_m5(starts), 240, "H4", 12)

    assert len(result) == 1
    assert result.iloc[0]["source_rows"] == 36
    assert result.iloc[0]["timestamp_utc"] == pd.Timestamp("2026-01-06T00:00:00Z")


def test_policy_enforces_concurrency_and_daily_caps():
    trades = pd.DataFrame(
        {
            "candidate_id": [0, 1, 2, 3],
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05T08:00:00Z",
                    "2026-01-05T12:00:00Z",
                    "2026-01-06T08:00:00Z",
                    "2026-01-07T08:00:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-08T00:00:00Z",
                    "2026-01-05T18:00:00Z",
                    "2026-01-08T00:00:00Z",
                    "2026-01-07T12:00:00Z",
                ]
            ),
        }
    )
    result = apply_policy(
        trades,
        "PRIMARY",
        {"maximum_concurrent_positions": 2, "maximum_entries_per_utc_day": 1},
    )

    assert result["candidate_id"].tolist() == [0, 2]
    assert result["policy_id"].eq("PRIMARY").all()


def test_gate_requires_winner_removal_and_all_thresholds():
    value = {
        "trades": 100,
        "stress_pf": 1.4,
        "average_stress_r": 0.08,
        "closed_drawdown_r": 8.0,
        "positive_active_year_share": 0.75,
        "top_winners_removed_stress_net_r": 1.0,
    }
    gate = {
        "minimum_trades": 60,
        "minimum_stress_pf": 1.15,
        "minimum_average_stress_r": 0.02,
        "maximum_closed_drawdown_r": 20.0,
        "minimum_positive_active_year_share": 0.5,
    }

    passed, checks = evaluate_gate(value, gate)
    assert passed
    assert all(checks.values())

    value["top_winners_removed_stress_net_r"] = -0.01
    assert not evaluate_gate(value, gate)[0]


def test_aggregation_rejects_too_sparse_bucket():
    result = aggregate_calendar_bars(
        _m5(["2026-01-05T20:00:00Z", "2026-01-05T20:05:00Z"]),
        240,
        "H4",
        12,
    )

    assert result.empty
