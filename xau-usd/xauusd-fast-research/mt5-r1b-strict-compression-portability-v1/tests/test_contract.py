from __future__ import annotations

import json
from pathlib import Path


def test_r1b_signal_contract_is_the_fixed_three_day_variant():
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "config" / "mt5_r1b_strict_compression_portability_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert config["signal"]["d1_box_days"] == 3
    assert config["signal"]["d1_atr_percentile_max"] == 60.0
    assert config["signal"]["d1_box_average_to_median_max"] == 1.25
    assert config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"] == {
        "maximum_concurrent_positions": 2,
        "maximum_entries_per_utc_day": 1,
        "eligible_for_decision": True,
    }
