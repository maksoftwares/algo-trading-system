from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_a1_xau_extended_horizon_exact.py"


def load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("run_a1_xau_extended_horizon_exact", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = load_module()


def test_horizons_are_fixed_and_end_at_development_cutoff() -> None:
    assert [(item.name, item.from_date, item.to_date) for item in R.HORIZONS] == [
        ("five_year", "2021.07.01", "2026.06.30"),
        ("ten_year", "2016.07.01", "2026.06.30"),
    ]


def test_source_priorities_reproduce_frozen_portfolio_contract() -> None:
    assert R.SOURCE_PRIORITY == {
        "r1_h1_pullback_long_v1": 71,
        "h4_d1_long_best_box2_atr80": 80,
        "r2_pullback_rejection_short_v1": 92,
        "r2_continuation_short_v1": 123,
    }


def test_dedupe_is_five_minute_same_direction_cross_source_only() -> None:
    rows = [
        {"source_id": "a", "source_priority": 1, "trade_id": "a", "entry_time": "2024-01-01 10:00:00", "exit_time": "2024-01-01 11:00:00", "direction": "LONG", "position_id": "1", "pnl_usd": "1"},
        {"source_id": "b", "source_priority": 2, "trade_id": "b", "entry_time": "2024-01-01 10:05:00", "exit_time": "2024-01-01 11:00:00", "direction": "LONG", "position_id": "1", "pnl_usd": "2"},
        {"source_id": "c", "source_priority": 3, "trade_id": "c", "entry_time": "2024-01-01 10:05:00", "exit_time": "2024-01-01 11:00:00", "direction": "SHORT", "position_id": "1", "pnl_usd": "3"},
    ]
    kept, dropped = R.dedupe_portfolio(rows)
    assert [row["trade_id"] for row in kept] == ["a", "c"]
    assert [row["trade_id"] for row in dropped] == ["b"]


def test_metrics_and_rolling_months_are_deterministic() -> None:
    rows = [
        {"pnl_usd": "10", "tickets": 1, "exit_time": "2024-01-02 00:00:00", "entry_time": "2024-01-01 00:00:00", "source_priority": 1, "source_id": "a", "position_id": "1"},
        {"pnl_usd": "-5", "tickets": 1, "exit_time": "2024-02-02 00:00:00", "entry_time": "2024-02-01 00:00:00", "source_priority": 1, "source_id": "a", "position_id": "2"},
    ]
    shape = R.metrics(rows)
    assert shape["net_usd"] == 5.0
    assert shape["profit_factor"] == 2.0
    assert shape["max_closed_drawdown_usd"] == 5.0
    rolling = R.rolling_months([{"month": "2024-01", "net_usd": 10}, {"month": "2024-02", "net_usd": -5}], 2)
    assert rolling == [{"months": 2, "start_month": "2024-01", "end_month": "2024-02", "net_usd": 5.0}]


def test_cli_has_no_runtime_attachment_or_live_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.isdisjoint({"live", "demo", "account", "server", "attach", "profile"})
