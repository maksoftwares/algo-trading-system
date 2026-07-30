from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "deployed_specialist_monitor",
    ROOT / "deployed_specialist_monitor.py",
)
assert SPEC is not None and SPEC.loader is not None
MONITOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MONITOR
SPEC.loader.exec_module(MONITOR)


def test_every_deployed_source_has_an_operational_feed_mapping() -> None:
    config = MONITOR.read_json(MONITOR.CONFIG_PATH)
    source_ids = {str(row["source_id"]) for row in config["sources"]}

    assert len(source_ids) == 9
    assert set(MONITOR.FEED_BY_SOURCE) == source_ids


def test_monitor_is_read_only() -> None:
    text = (ROOT / "deployed_specialist_monitor.py").read_text(encoding="utf-8")

    assert "MetaTrader5" not in text
    assert "order_send" not in text
    assert "broker_action_added" in text
