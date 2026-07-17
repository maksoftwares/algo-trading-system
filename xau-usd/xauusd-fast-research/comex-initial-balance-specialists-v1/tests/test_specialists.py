from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from specialists import EXPANSION, generate_candidates  # noqa: E402


def test_initial_balance_expansion_uses_completed_first_hour() -> None:
    config = json.loads(
        (ROOT / "config" / "comex_initial_balance_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )
    periods = 24
    times = pd.date_range("2024-01-02T13:25:00Z", periods=periods, freq="5min")
    spot = pd.DataFrame(
        {
            "timestamp_utc": times,
            "mid_open": [2000.0] * periods,
            "mid_high": [2002.0] * periods,
            "mid_low": [1998.0] * periods,
            "mid_close": [2000.0] * periods,
        }
    )
    local = times.tz_convert("America/New_York").strftime("%H:%M")
    close = [2000.0] * periods
    close[-1] = 2002.0
    futures = pd.DataFrame(
        {
            "available_time_utc": times,
            "session_date": ["2024-01-02"] * periods,
            "available_local_time": local,
            "open": [2000.0] * periods,
            "high": [2001.0] * (periods - 1) + [2002.1],
            "low": [1999.0] * periods,
            "close": close,
            "running_poc": [2000.0] * (periods - 1) + [2000.5],
            "cumulative_delta_ratio": [0.2] * periods,
            "cumulative_volume_ratio": [1.0] * periods,
        }
    )

    candidates = generate_candidates(spot, futures, config)

    result = candidates.loc[candidates["family_id"].eq(EXPANSION)]
    assert len(result) == 1
    assert result.iloc[0]["direction"] == "LONG"
    assert result.iloc[0]["signal_time"] == times[-1]
