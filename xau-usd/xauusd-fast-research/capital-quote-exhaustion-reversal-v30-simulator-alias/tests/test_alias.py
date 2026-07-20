from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alias import add_simulator_aliases  # noqa: E402


def test_aliases_preserve_rows_and_values() -> None:
    source = pd.DataFrame(
        {
            "tick_time_msc": [1, 2],
            "candidate_side": ["LONG", "SHORT"],
            "impulse_update_imbalance": [-0.8, 0.9],
            "impulse_displacement_price": [-1.3, 1.4],
        }
    )
    result = add_simulator_aliases(source)
    assert result["tick_time_msc"].tolist() == [1, 2]
    assert result["candidate_side"].tolist() == ["LONG", "SHORT"]
    assert result["signed_update_imbalance"].tolist() == [-0.8, 0.9]
    assert result["displacement_price"].tolist() == [-1.3, 1.4]
