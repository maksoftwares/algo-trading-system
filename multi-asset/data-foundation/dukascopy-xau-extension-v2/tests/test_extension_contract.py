from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from acquire_xau_extension import month_keys  # noqa: E402


def test_extension_has_78_ordered_months() -> None:
    months = month_keys("2010-01", "2016-07")
    assert len(months) == 78
    assert months[0] == "2010-01"
    assert months[-1] == "2016-06"


def test_extension_is_xau_only_and_free_source_only() -> None:
    config = json.loads(
        (ROOT / "config" / "xau_extension_v2.json").read_text(encoding="utf-8")
    )
    assert config["symbol"] == "XAUUSD"
    assert config["paid_data_authorized"] is False
    assert config["strategy_scoring_authorized"] is False
    assert config["broker_action_authorized"] is False
