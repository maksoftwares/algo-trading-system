from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adapter import load_adapter_config, load_ticks, load_v30_module, v30_root  # noqa: E402


def source_frame(time_utc: str, time_msc: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_version": "xauusd_c02_multiacct_202607030845_g0a9823b0_c9221d066",
                "account_scope": 1025742,
                "account_label": "A1",
                "symbol": "XAUUSD",
                "time_utc": time_utc,
                "time_msc": time_msc,
                "bid": 3999.50,
                "ask": 4000.00,
                "spread_price": 0.50,
            }
        ]
    )


def test_same_second_millisecond_timestamp_is_accepted(tmp_path: Path) -> None:
    adapter_config = load_adapter_config()
    v30 = load_v30_module(adapter_config)
    config = deepcopy(v30.load_config(v30_root(adapter_config)))
    timestamp = pd.Timestamp("2026-06-05T00:00:00.248Z")
    path = tmp_path / "ticks.csv"
    source_frame("2026-06-05T00:00:00Z", timestamp.value // 1_000_000).to_csv(
        path, index=False
    )
    ticks, audit, _ = load_ticks([path], config, v30)
    assert len(ticks) == 1
    assert audit["maximum_timestamp_representation_difference_ms"] == 248


def test_cross_second_timestamp_is_rejected(tmp_path: Path) -> None:
    adapter_config = load_adapter_config()
    v30 = load_v30_module(adapter_config)
    config = deepcopy(v30.load_config(v30_root(adapter_config)))
    timestamp = pd.Timestamp("2026-06-05T00:00:01.001Z")
    path = tmp_path / "ticks.csv"
    source_frame("2026-06-05T00:00:00Z", timestamp.value // 1_000_000).to_csv(
        path, index=False
    )
    with pytest.raises(ValueError, match="cross-second"):
        load_ticks([path], config, v30)
