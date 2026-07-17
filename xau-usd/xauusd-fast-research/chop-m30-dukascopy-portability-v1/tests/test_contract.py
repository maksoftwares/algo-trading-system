from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from portability import ROTATION, adapt_m5


ROOT = Path(__file__).resolve().parents[1]
FAST_ROOT = ROOT.parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def config() -> dict:
    return json.loads((ROOT / "config" / "portability_v1.json").read_text())


def test_frozen_ancestry_hashes_match_corrected_source() -> None:
    ancestry = config()["ancestry"]
    source = FAST_ROOT / "chop-v1"
    assert digest(source / "config" / "chop_fast_discovery_v1.json") == ancestry["original_config_sha256"]
    assert digest(source / "src" / "regime.py") == ancestry["regime_sha256"]
    assert digest(source / "src" / "strategies.py") == ancestry["strategies_sha256"]
    assert digest(source / "src" / "backtest.py") == ancestry["backtest_sha256"]
    assert digest(source / "src" / "data_adapter.py") == ancestry["data_adapter_sha256"]


def test_frozen_rotation_parameters_match_original_config() -> None:
    original = json.loads((FAST_ROOT / "chop-v1" / "config" / "chop_fast_discovery_v1.json").read_text())
    current = config()
    assert ROTATION == "CHOP_RANGE_ROTATION_CONTINUATION_V1"
    assert current["regime"] == original["regime"]
    assert current["rotation"] == original["strategies"]["rotation"]
    assert current["execution"]["cooldown_hours"] == original["cooldown_hours"]
    assert current["execution"]["stress_slippage_r"] == original["stress_slippage_r"]


def test_adapter_preserves_native_spread_and_tick_max_stress() -> None:
    frame = pd.DataFrame(
        {
            "ask_open": [2000.50],
            "bid_open": [2000.10],
            "ask_close": [2000.60],
            "bid_close": [2000.20],
            "tick_spread_max": [0.75],
            "xau_tick_count": [42],
        }
    )
    adapted = adapt_m5(frame, 0.01)
    assert adapted.iloc[0]["spread_open_points"] == pytest.approx(40.0)
    assert adapted.iloc[0]["spread_p95_points"] == pytest.approx(75.0)
    assert adapted.iloc[0]["volume_sum"] == 42.0


def test_result_cannot_authorize_execution() -> None:
    controls = config()["research_controls"]
    assert controls["research_only"] is True
    assert controls["python_predictions_authorized"] is False
    assert controls["ea_consumption_authorized"] is False
    assert controls["broker_action_authorized"] is False
