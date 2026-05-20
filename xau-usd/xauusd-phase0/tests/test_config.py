from __future__ import annotations

from datetime import timezone

import pytest

from phase0.config import (
    ConfigError,
    build_backtest_config,
    build_cell_configs,
    load_project_config,
    parse_utc_datetime,
    validate_true_holdout_access,
)


def test_load_project_config(project_root):
    config = load_project_config(project_root)

    assert config.phase0["project"]["name"] == "XAUUSD Master EA Phase 0"
    assert set(config.phase0["experts"]) == {"trend_pullback", "breakout_retest", "range_mr"}
    assert "XAUUSD" in config.symbols["symbols"]


def test_build_backtest_config(project_root):
    config = load_project_config(project_root)
    backtest_config = build_backtest_config(config)

    assert backtest_config.starting_equity_usd == 10000.0
    assert backtest_config.risk_per_trade_pct == 0.005
    assert backtest_config.one_trade_at_a_time is True


def test_build_cell_configs(project_root):
    config = load_project_config(project_root)
    cells = build_cell_configs(config)

    assert len(cells) == 9
    assert cells[0].broker == "capital_com"
    assert cells[2].cost_model == "p95"
    assert cells[8].broker == "dukascopy"


def test_parse_utc_datetime_requires_timezone():
    with pytest.raises(ConfigError):
        parse_utc_datetime("2025-01-01T00:00:00", "test value")


def test_true_holdout_guard_blocks_overlap(project_root):
    config = load_project_config(project_root)
    start = parse_utc_datetime("2025-07-01T00:00:00Z")
    end = parse_utc_datetime("2025-07-31T23:59:59Z")

    with pytest.raises(ConfigError):
        validate_true_holdout_access(config, start, end, unlock_flag=False)


def test_parse_utc_datetime_normalizes_to_utc():
    parsed = parse_utc_datetime("2025-01-01T04:00:00+04:00")

    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 0
