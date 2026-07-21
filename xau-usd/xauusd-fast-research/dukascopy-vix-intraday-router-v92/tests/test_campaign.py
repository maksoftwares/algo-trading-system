from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import run_research
from src.campaign import (
    MECHANICS,
    _causal_z,
    benjamini_hochberg,
    prepare_vix_h1,
    signal_mask_direction,
)
from lock_contract import expected_months


def test_prepare_vix_h1_uses_only_completed_m5_rows() -> None:
    opens = pd.to_datetime(
        ["2024-01-02T13:00:00Z", "2024-01-02T13:05:00Z", "2024-01-02T14:00:00Z"]
    )
    close = np.array([15.0, 15.2, 15.1])
    frame = pd.DataFrame(
        {
            "bar_open_timestamp_ms": opens.as_unit("ms").astype("int64"),
            "available_timestamp_ms": (opens + pd.Timedelta(minutes=5))
            .as_unit("ms")
            .astype("int64"),
            "source_last_timestamp_ms": (opens + pd.Timedelta(minutes=4))
            .as_unit("ms")
            .astype("int64"),
            "vol_mid_open": close,
            "vol_mid_high": close + 0.1,
            "vol_mid_low": close - 0.1,
            "vol_mid_close": close,
            "vol_tick_count": [10, 11, 12],
            "vol_spread_mean": [0.1, 0.1, 0.1],
        }
    )
    result = prepare_vix_h1(frame, lookbacks=[2])
    assert result.loc[0, "bar_end_utc"] == pd.Timestamp("2024-01-02T14:00:00Z")
    assert result.loc[0, "source_last_available_utc"] == pd.Timestamp(
        "2024-01-02T13:10:00Z"
    )
    assert result.loc[0, "vix_active_m5"] == 2
    assert result.loc[0, "vix_staleness_minutes"] == 50.0


def test_causal_z_uses_prior_observed_values_without_filling_gaps() -> None:
    values = pd.Series([1.0, 2.0, np.nan, 3.0, 4.0])
    result = _causal_z(values, lookback=2)
    assert pd.isna(result.iloc[2])
    assert result.iloc[3] == 3.0


def test_registered_mechanics_emit_only_declared_directions() -> None:
    frame = pd.DataFrame(
        {
            "vix_return_4h": [0.1, -0.1],
            "vix_return_1h": [0.1, -0.1],
            "vix_return_z_24": [2.0, -2.0],
            "vix_abs_return_z_24": [2.0, 2.0],
            "vix_level_z_24": [2.0, 2.0],
            "impulse_3_atr": [-0.5, 0.5],
            "body_atr": [0.5, -0.5],
            "mid_close": [101.0, 99.0],
            "prior_high_6": [100.0, 100.0],
            "prior_low_6": [100.0, 100.0],
            "atr14": [1.0, 1.0],
            "vix_active_m5": [12, 12],
            "vix_staleness_minutes": [0.0, 0.0],
            "session_slot": ["LONDON", "NY"],
        }
    )
    params = {
        "lookback": 24,
        "state_threshold_z": 1.0,
        "minimum_active_m5": 3,
        "maximum_vix_staleness_minutes": 15,
        "session": "BOTH",
        "channel_bars": 6,
        "breakout_buffer_atr": 0.0,
        "impulse_hours": 3,
        "impulse_min_atr": 0.2,
        "confirmation_min_atr": 0.1,
    }
    for mechanic in MECHANICS:
        mask, direction = signal_mask_direction(frame, mechanic, params)
        assert set(direction.loc[mask].unique()).issubset({-1, 1})


def test_shock_direction_uses_the_registered_one_hour_vix_move() -> None:
    frame = pd.DataFrame(
        {
            "vix_return_4h": [-0.1],
            "vix_return_1h": [0.1],
            "vix_return_z_24": [2.0],
            "vix_abs_return_z_24": [2.0],
            "vix_level_z_24": [2.0],
            "impulse_3_atr": [-0.5],
            "body_atr": [0.5],
            "mid_close": [101.0],
            "prior_high_6": [100.0],
            "prior_low_6": [99.0],
            "atr14": [1.0],
            "vix_active_m5": [12],
            "vix_staleness_minutes": [0.0],
            "session_slot": ["LONDON"],
        }
    )
    params = {
        "lookback": 24,
        "state_threshold_z": 1.0,
        "minimum_active_m5": 3,
        "maximum_vix_staleness_minutes": 15,
        "session": "BOTH",
        "channel_bars": 6,
        "breakout_buffer_atr": 0.0,
        "impulse_hours": 3,
        "impulse_min_atr": 0.2,
        "confirmation_min_atr": 0.1,
    }

    mask, direction = signal_mask_direction(frame, "VIX_SAFE_HAVEN_CATCHUP", params)

    assert mask.iloc[0]
    assert direction.iloc[0] == 1


def test_benjamini_hochberg_counts_full_family() -> None:
    adjusted = benjamini_hochberg(pd.Series([0.001, 0.02, 0.9]))
    assert adjusted.tolist() == [0.003, 0.03, 0.9]


def test_expected_months_requires_the_exact_registered_range() -> None:
    months = expected_months("2023-01-01T00:00:00Z", "2023-04-01T00:00:00Z")
    assert months == ["2023-01", "2023-02", "2023-03"]


def test_xau_source_config_satisfies_the_audited_loader_contract() -> None:
    config = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "config"
            / "dukascopy_vix_intraday_router_v92.json"
        ).read_text(encoding="utf-8")
    )
    required = {
        "storage_environment_variable",
        "default_storage_root",
        "feature_cache",
        "feature_manifest",
        "feature_sha256",
        "source_digest",
        "expected_rows",
        "start_utc",
        "end_exclusive_utc",
    }
    assert required.issubset(config["source"])


def test_advancement_lock_binds_the_selected_trade_ledger(
    tmp_path, monkeypatch
) -> None:
    metrics = tmp_path / "metrics.csv"
    trades = tmp_path / "trades.csv"
    advancement = tmp_path / "advancement.json"
    metrics.write_text("metric\n1\n", encoding="utf-8")
    trades.write_text("trade\n1\n", encoding="utf-8")
    body = {
        "contract_sha256": "contract",
        "metrics_sha256": run_research._sha256(metrics),
        "trades_sha256": run_research._sha256(trades),
    }
    payload = {**body, "advancement_sha256": run_research._canonical_hash(body)}
    advancement.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(run_research, "_advancement_path", lambda stage: advancement)
    monkeypatch.setattr(run_research, "_metrics_path", lambda stage: metrics)
    monkeypatch.setattr(run_research, "_trades_path", lambda stage: trades)

    run_research._verify_advancement("discovery", "contract")
    trades.write_text("trade\n2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="trades changed"):
        run_research._verify_advancement("discovery", "contract")
