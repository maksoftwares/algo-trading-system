from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_session_frequency_expansion import (
    apply_causal_risk_cap,
    transferred_candidate,
)


def test_transfer_changes_only_identity_clock_and_evidence() -> None:
    template = {
        "specialist_id": "BASE",
        "owned_regime": "chop",
        "reference_hours_utc": [0, 1, 2, 3, 4, 5],
        "decision_hours_utc": [6, 7, 8, 9],
        "direction": "SHORT",
        "body_fraction_minimum": 0.35,
        "stop_atr_multiple": 1.75,
        "target_r_multiple": 1.25,
        "maximum_hold_hours": 12,
        "prior_evidence": "old",
    }
    transferred = transferred_candidate(
        template,
        "NEW_YORK",
        {
            "reference_hours_utc": [6, 7, 8, 9, 10, 11],
            "decision_hours_utc": [12, 13, 14, 15],
        },
    )
    protected = {
        "owned_regime",
        "direction",
        "body_fraction_minimum",
        "stop_atr_multiple",
        "target_r_multiple",
        "maximum_hold_hours",
    }
    assert all(transferred[key] == template[key] for key in protected)
    assert transferred["reference_hours_utc"] == [6, 7, 8, 9, 10, 11]
    assert transferred["decision_hours_utc"] == [12, 13, 14, 15]


def test_risk_cap_uses_only_positions_open_at_entry() -> None:
    trades = pd.DataFrame(
        {
            "specialist_id": ["A", "B", "C"],
            "portfolio_sleeve": [
                "BASELINE_CHOP",
                "NEW_YORK_CHOP",
                "LATE_US_CHOP",
            ],
            "entry_time_utc": pd.to_datetime(
                ["2026-01-05T07:00Z", "2026-01-05T08:00Z", "2026-01-05T10:00Z"],
                utc=True,
            ),
            "exit_time_utc": pd.to_datetime(
                ["2026-01-05T09:00Z", "2026-01-05T11:00Z", "2026-01-05T12:00Z"],
                utc=True,
            ),
            "portfolio_risk_weight": [1.0, 1.5, 1.0],
        }
    )
    accepted, diagnostics = apply_causal_risk_cap(
        trades,
        maximum_risk=2.0,
        priority=[
            "BASELINE_CHOP",
            "NEW_YORK_CHOP",
            "LATE_US_CHOP",
        ],
    )
    assert accepted["specialist_id"].tolist() == ["A", "C"]
    assert diagnostics["risk_cap_rejections"] == 1
