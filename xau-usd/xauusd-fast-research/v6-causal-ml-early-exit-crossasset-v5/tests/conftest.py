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
            LANE_ROOT
            / "config"
            / "v6_causal_ml_early_exit_crossasset_v5.json"
        ).read_text(encoding="utf-8")
    )
