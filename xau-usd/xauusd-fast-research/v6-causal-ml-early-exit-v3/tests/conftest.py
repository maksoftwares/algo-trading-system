import json
import sys
from pathlib import Path

import pytest


LANE_ROOT = Path(__file__).resolve().parents[1]
if str(LANE_ROOT) not in sys.path:
    sys.path.insert(0, str(LANE_ROOT))


@pytest.fixture
def config():
    return json.loads(
        (
            LANE_ROOT / "config" / "v6_causal_ml_early_exit_v3.json"
        ).read_text(encoding="utf-8")
    )


@pytest.fixture
def stress():
    return {
        "base_fee_usd": 0.30,
        "additional_fixed_cost_usd": 0.30,
        "holding_cost_usd_per_24h": 0.35,
        "slippage_r": 0.05,
    }
