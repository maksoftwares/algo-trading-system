from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from phase0.config import load_project_config
from phase0.costs import (
    apply_entry_slippage,
    apply_exit_slippage,
    commission_usd,
    load_cost_model,
    price_from_mid,
)


def test_load_configured_cost_model(project_root):
    config = load_project_config(project_root)

    model = load_cost_model(config, "XAUUSD", "capital_com", "p95")

    assert model.spread_points == 35
    assert model.spread_price == pytest.approx(0.35)
    assert model.entry_slippage_price == pytest.approx(0.02)
    assert model.exit_slippage_price == pytest.approx(0.02)


def test_measured_cost_model_prefers_hour_bucket(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_measured_cost_model(root)
    config = load_project_config(root)

    model = load_cost_model(
        config,
        "XAUUSD",
        "capital_com",
        "p95",
        timestamp_utc=datetime(2026, 1, 5, 10, 30, tzinfo=timezone.utc),
    )

    assert model.spread_points == pytest.approx(44.0)
    assert model.spread_price == pytest.approx(0.44)


def test_measured_cost_model_falls_back_to_day_then_configured(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_measured_cost_model(root)
    config = load_project_config(root)

    day_model = load_cost_model(
        config,
        "XAUUSD",
        "capital_com",
        "median",
        timestamp_utc=datetime(2026, 1, 5, 11, 30, tzinfo=timezone.utc),
    )
    configured_model = load_cost_model(
        config,
        "XAUUSD",
        "pepperstone",
        "p95",
        timestamp_utc=datetime(2026, 1, 5, 11, 30, tzinfo=timezone.utc),
    )

    assert day_model.spread_points == pytest.approx(20.0)
    assert configured_model.spread_points == pytest.approx(35.0)


def test_pending_measured_cost_model_does_not_override_config(project_root, tmp_path):
    root = _copy_config(project_root, tmp_path)
    _write_measured_cost_model(root, status="PENDING")
    config = load_project_config(root)

    model = load_cost_model(config, "XAUUSD", "capital_com", "p95")

    assert model.spread_points == pytest.approx(35.0)


def test_mid_price_spread_application():
    assert price_from_mid(100.0, "LONG", "entry", 0.20) == pytest.approx(100.10)
    assert price_from_mid(100.0, "LONG", "exit", 0.20) == pytest.approx(99.90)
    assert price_from_mid(100.0, "SHORT", "entry", 0.20) == pytest.approx(99.90)
    assert price_from_mid(100.0, "SHORT", "exit", 0.20) == pytest.approx(100.10)


def test_adverse_slippage_application():
    assert apply_entry_slippage(100.0, "LONG", 0.02) == pytest.approx(100.02)
    assert apply_entry_slippage(100.0, "SHORT", 0.02) == pytest.approx(99.98)
    assert apply_exit_slippage(100.0, "LONG", 0.02) == pytest.approx(99.98)
    assert apply_exit_slippage(100.0, "SHORT", 0.02) == pytest.approx(100.02)


def test_commission_is_round_turn_per_lot():
    assert commission_usd(0.25, 7.0) == pytest.approx(1.75)


def _copy_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root


def _write_measured_cost_model(root: Path, status: str = "PASS") -> None:
    path = root / "outputs" / "reports" / "cost_model_measured.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "MEASURED_COST_MODEL.md").write_text(
        f"# Measured Cost Model\n\nOverall status: {status}\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "scope": "global",
                "bucket": "all",
                "broker": "capital_com",
                "symbol": "XAUUSD",
                "observations": 100,
                "median_spread_points": 22.0,
                "p95_spread_points": 55.0,
                "max_spread_points": 80.0,
            },
            {
                "scope": "hour_utc",
                "bucket": "10",
                "broker": "capital_com",
                "symbol": "XAUUSD",
                "observations": 25,
                "median_spread_points": 18.0,
                "p95_spread_points": 44.0,
                "max_spread_points": 70.0,
            },
            {
                "scope": "day_of_week_utc",
                "bucket": "Monday",
                "broker": "capital_com",
                "symbol": "XAUUSD",
                "observations": 40,
                "median_spread_points": 20.0,
                "p95_spread_points": 50.0,
                "max_spread_points": 75.0,
            },
        ]
    ).to_csv(path, index=False)
