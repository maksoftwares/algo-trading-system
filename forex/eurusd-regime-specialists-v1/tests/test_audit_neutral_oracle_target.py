from __future__ import annotations

from pathlib import Path

import pandas as pd

from audit_neutral_oracle_target import build_target_audit


def test_target_audit_exposes_chronological_scan_concentration(
    tmp_path: Path,
) -> None:
    path = tmp_path / "oracle.csv"
    pd.DataFrame(
        {
            "entry_time_utc": [
                "2026-01-02T00:00:00Z",
                "2026-01-02T00:05:00Z",
                "2026-01-02T00:10:00Z",
                "2026-01-02T00:15:00Z",
            ],
            "side": ["LONG", "SHORT", "LONG", "SHORT"],
            "regime": ["NEUTRAL"] * 4,
            "risk_tier_pips": [4.0] * 4,
            "fallback_risk_tier": [False] * 4,
        }
    ).to_csv(path, index=False)
    result = build_target_audit(
        path,
        anchor_time_utc="12:45",
        windows_minutes=(240,),
    )
    assert result["neutral_oracle_rows"] == 4
    assert result["neutral_rows_at_0000_through_0015"] == 4
    assert result["neutral_rows_before_0100_share"] == 1.0
    metric = result["fixed_event_anchor_proximity"][
        "plus_minus_240_minutes"
    ]
    assert metric["oracle_rows"] == 0
    assert metric["maximum_fixed_anchor_precision_if_side_known"] == 0.0
