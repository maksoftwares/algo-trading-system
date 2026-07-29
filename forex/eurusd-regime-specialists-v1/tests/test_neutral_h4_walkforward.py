from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_h4_walkforward import enforce_nonoverlap


def test_nonoverlap_keeps_first_trade_and_next_strictly_after_exit() -> None:
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T04:00:00Z",
                    "2026-01-01T08:00:00Z",
                ],
                utc=True,
            ),
            "entry_index": [10, 12, 21],
            "exit_index": [20, 18, 25],
        }
    )
    kept, rejected = enforce_nonoverlap(frame)
    assert kept["entry_index"].tolist() == [10, 21]
    assert rejected == 1
