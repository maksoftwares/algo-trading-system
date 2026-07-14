from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from data_gate import raw_schema, tick_coverage_complete


def test_bar_ohlc_plus_single_spread_is_not_promotion_grade(tmp_path: Path) -> None:
    path = tmp_path / "bars.csv"
    path.write_text("<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<SPREAD>\n", encoding="utf-8")
    result = raw_schema(path)
    assert result["execution_source_kind"] == "BAR_OHLC_PLUS_SINGLE_SPREAD_FIELD"
    assert result["promotion_grade"] is False


def test_late_first_tick_fails_full_period_coverage() -> None:
    required = datetime(2016, 7, 1, tzinfo=timezone.utc)
    late = int(datetime(2025, 3, 11, tzinfo=timezone.utc).timestamp() * 1000)
    assert tick_coverage_complete(late, required) is False


def test_frozen_config_has_zero_search_and_all_four_symbols() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "config" / "london_breakout_v1.json").read_text(encoding="utf-8"))
    assert config["parameter_search_count"] == 0
    assert config["symbols"] == ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
    assert config["timezone"] == "Europe/London"
    assert config["data_gate"]["bar_spread_reconstruction_sufficient"] is False
