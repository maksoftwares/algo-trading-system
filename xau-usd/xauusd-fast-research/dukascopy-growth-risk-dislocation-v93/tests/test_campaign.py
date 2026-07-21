from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from lock_contract import expected_months
from src.campaign import (
    MECHANICS,
    _causal_ridge_prediction,
    generate_manifest,
    parameter_space,
    prepare_source_h1,
    signal_mask_direction,
    source_event_mask_direction,
)


ROOT = Path(__file__).resolve().parents[1]


def source_m5() -> pd.DataFrame:
    opens = pd.to_datetime(
        ["2024-01-02T13:00:00Z", "2024-01-02T13:05:00Z"]
    )
    frame = pd.DataFrame(
        {"bar_open_timestamp_ms": opens.as_unit("ms").astype("int64")}
    )
    for offset, prefix in enumerate(("spx", "copper", "usdcnh")):
        close = np.array([100.0 + offset, 100.2 + offset])
        frame[f"{prefix}_available_timestamp_ms"] = (
            opens + pd.Timedelta(minutes=5)
        ).as_unit("ms").astype("int64")
        frame[f"{prefix}_source_last_timestamp_ms"] = (
            opens + pd.Timedelta(minutes=4)
        ).as_unit("ms").astype("int64")
        frame[f"{prefix}_mid_open"] = close
        frame[f"{prefix}_mid_high"] = close + 0.1
        frame[f"{prefix}_mid_low"] = close - 0.1
        frame[f"{prefix}_mid_close"] = close
        frame[f"{prefix}_tick_count"] = [10, 11]
    return frame


def test_source_h1_uses_only_completed_m5_rows() -> None:
    config = {
        "features": {"source_normalization_lookbacks": [2]},
    }
    result = prepare_source_h1(source_m5(), config)
    assert len(result) == 1
    assert result.loc[0, "bar_end_utc"] == pd.Timestamp("2024-01-02T14:00:00Z")
    assert result.loc[0, "spx_source_last_available_utc"] == pd.Timestamp(
        "2024-01-02T13:10:00Z"
    )
    assert result.loc[0, "spx_source_last_tick_utc"] == pd.Timestamp(
        "2024-01-02T13:09:00Z"
    )
    assert result.loc[0, "spx_staleness_minutes"] == 51.0
    assert result.loc[0, "copper_active_m5"] == 2


def test_source_h1_rejects_tick_at_or_after_availability() -> None:
    frame = source_m5()
    frame.loc[0, "spx_source_last_timestamp_ms"] = frame.loc[
        0, "spx_available_timestamp_ms"
    ]
    config = {"features": {"source_normalization_lookbacks": [2]}}
    try:
        prepare_source_h1(frame, config)
    except ValueError as exc:
        assert "Noncausal spx" in str(exc)
    else:
        raise AssertionError("noncausal source tick was accepted")


def test_causal_ridge_prediction_never_uses_current_or_future_target() -> None:
    features = np.array(
        [[index, index * 0.5, -index * 0.25] for index in range(300)], dtype=float
    )
    target = np.linspace(-1.0, 1.0, 300)
    altered = target.copy()
    altered[250:] = 1_000_000.0
    first = _causal_ridge_prediction(features, target, 240, 0.1)
    second = _causal_ridge_prediction(features, altered, 240, 0.1)
    assert np.allclose(first[:251], second[:251], equal_nan=True)


def test_source_event_gate_does_not_require_any_xau_column() -> None:
    frame = pd.DataFrame(
        {
            "risk_score_1h_120": [2.0, -2.0],
            "growth_score_1h_120": [2.0, -2.0],
            "source_energy_1h_120": [2.0, 2.0],
            "session_slot": ["LONDON", "NY"],
        }
    )
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_active_m5"] = 12
        frame[f"{prefix}_staleness_minutes"] = 0.0
    params = {
        "source_horizon": 1,
        "source_lookback": 120,
        "source_threshold_z": 1.0,
        "minimum_active_m5": 6,
        "maximum_source_staleness_minutes": 15,
        "session": "ALL",
    }
    for mechanic in MECHANICS:
        mask, direction = source_event_mask_direction(frame, mechanic, params)
        assert mask.all()
        assert direction.tolist() == [1, -1]


def test_registered_signal_mechanics_emit_only_long_or_short() -> None:
    frame = pd.DataFrame(
        {
            "risk_score_1h_120": [2.0, -2.0],
            "growth_score_1h_120": [2.0, -2.0],
            "source_energy_1h_120": [2.0, 2.0],
            "session_slot": ["LONDON", "NY"],
            "impulse_1_atr": [0.0, 0.0],
            "body_atr": [0.1, -0.1],
            "mid_close": [101.0, 99.0],
            "prior_high_6": [100.0, 100.0],
            "prior_low_6": [100.0, 100.0],
            "atr14": [1.0, 1.0],
            "ridge_prediction_h1_s120_m240_r0p1": [0.5, -0.5],
        }
    )
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_active_m5"] = 12
        frame[f"{prefix}_staleness_minutes"] = 0.0
    params = {
        "source_horizon": 1,
        "source_lookback": 120,
        "source_threshold_z": 1.0,
        "minimum_active_m5": 6,
        "maximum_source_staleness_minutes": 15,
        "session": "ALL",
        "maximum_response_atr": 0.75,
        "model_lookback": 240,
        "ridge_penalty": 0.1,
        "minimum_prediction_atr": 0.1,
        "channel_bars": 6,
        "breakout_buffer_atr": 0.0,
    }
    for mechanic in MECHANICS:
        mask, direction = signal_mask_direction(frame, mechanic, params)
        assert set(direction.loc[mask].unique()).issubset({-1, 1})


def test_policy_spaces_are_bounded_and_contain_execution_geometry() -> None:
    for mechanic in MECHANICS:
        space = parameter_space(mechanic)
        assert 1_000 < len(space) <= 200_000
        assert {"stop_atr", "target_r", "hold_hours"}.issubset(space[0])


def test_manifest_is_sequential_unique_and_constructed_from_source_only() -> None:
    rows = 1_200
    frame = pd.DataFrame(
        {
            "bar_end_utc": pd.date_range(
                "2022-07-01T01:00:00Z", periods=rows, freq="h"
            ),
            "session_slot": np.resize(["ASIA", "LONDON", "NY"], rows),
        }
    )
    alternating = np.resize([3.0, -3.0], rows)
    for horizon in (1, 3, 6):
        for lookback in (120, 240, 480):
            frame[f"risk_score_{horizon}h_{lookback}"] = alternating
            frame[f"growth_score_{horizon}h_{lookback}"] = alternating
            frame[f"source_energy_{horizon}h_{lookback}"] = 3.0
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_active_m5"] = 12
        frame[f"{prefix}_staleness_minutes"] = 0.0

    manifest = generate_manifest(
        frame,
        pd.Timestamp("2022-07-01T00:00:00Z"),
        pd.Timestamp("2023-01-01T00:00:00Z"),
        attempt_first=124001,
        policies_per_mechanic=2,
        minimum_raw_signals=60,
    )

    assert len(manifest) == 10
    assert manifest["attempt_no"].tolist() == list(range(124001, 124011))
    assert manifest["policy_id"].is_unique
    assert manifest.groupby("mechanic").size().eq(2).all()


def test_windows_and_attempts_target_two_per_day_not_v60_milestone() -> None:
    config = json.loads(
        (ROOT / "config" / "dukascopy_growth_risk_dislocation_v93.json").read_text()
    )
    assert config["windows"]["discovery"] == [
        "2022-07-01T00:00:00Z",
        "2024-07-01T00:00:00Z",
    ]
    assert config["shared_account"]["minimum_combined_trades_per_weekday"] == 2.0
    assert config["research_controls"]["attempt_first"] == 124001
    assert config["research_controls"]["attempt_last"] == 125000
    assert config["research_controls"]["registered_policy_count"] == 1000
    assert config["research_controls"]["v59_v60_modification_authorized"] is False


def test_expected_months_requires_exact_consecutive_source_range() -> None:
    assert expected_months(
        "2022-01-01T00:00:00Z", "2022-04-01T00:00:00Z"
    ) == ["2022-01", "2022-02", "2022-03"]
