from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_body_frequency_ladder import (
    candidate_at_threshold,
)


def test_body_ladder_changes_only_identity_threshold_and_evidence() -> None:
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
    candidate = candidate_at_threshold(template, "L1", 0.25)
    protected = {
        "owned_regime",
        "reference_hours_utc",
        "decision_hours_utc",
        "direction",
        "stop_atr_multiple",
        "target_r_multiple",
        "maximum_hold_hours",
    }
    assert all(candidate[key] == template[key] for key in protected)
    assert candidate["body_fraction_minimum"] == 0.25
