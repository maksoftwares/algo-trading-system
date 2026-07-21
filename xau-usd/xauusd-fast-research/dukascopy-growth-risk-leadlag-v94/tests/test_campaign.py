from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lock_contract import expected_months
import run_research
from src.campaign import (
    HORIZON_NAMES,
    MECHANICS,
    generate_manifest,
    parameter_space,
    prepare_features,
    prepare_source_m5,
    signal_mask_direction,
    source_event_mask_direction,
)


ROOT = Path(__file__).resolve().parents[1]


def source_frame(rows: int = 1_400) -> pd.DataFrame:
    opens = pd.date_range("2022-01-03T00:00:00Z", periods=rows, freq="5min")
    frame = pd.DataFrame(
        {"bar_open_timestamp_ms": opens.as_unit("ms").astype("int64")}
    )
    alternating = np.resize([0.01, -0.01], rows)
    values = {"spx": -alternating, "copper": -alternating, "usdcnh": alternating}
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_available_timestamp_ms"] = (
            opens + pd.Timedelta(minutes=5)
        ).as_unit("ms").astype("int64")
        frame[f"{prefix}_tick_count"] = 100
        for name in HORIZON_NAMES.values():
            frame[f"{prefix}_return_{name}"] = values[prefix]
    return frame


def config() -> dict:
    return {
        "features": {
            "m5_atr_period": 3,
            "source_normalization_lookbacks": [12, 24, 48],
        }
    }


def policy_params() -> dict:
    return {
        "source_horizon": 1,
        "source_lookback": 12,
        "source_threshold_z": 0.5,
        "minimum_tick_count": 5,
        "maximum_source_staleness_minutes": 0,
        "session": "ALL",
        "maximum_response_atr": 0.75,
        "minimum_opposite_response_atr": 0.5,
        "minimum_agreeing_legs": 1,
        "sequence_multiplier": 2,
        "channel_bars": 6,
        "breakout_buffer_atr": 0.0,
    }


def test_source_m5_is_available_only_at_completed_bar_close() -> None:
    result = prepare_source_m5(source_frame(100), config())
    assert result.loc[0, "bar_end_utc"] == pd.Timestamp("2022-01-03T00:05:00Z")
    assert result.loc[0, "spx_staleness_minutes"] == 0.0
    assert result.loc[0, "copper_tick_count"] == 100


def test_source_preparation_rejects_future_availability() -> None:
    frame = source_frame(100)
    frame.loc[0, "spx_available_timestamp_ms"] += 1
    try:
        prepare_source_m5(frame, config())
    except ValueError as exc:
        assert "Future spx" in str(exc)
    else:
        raise AssertionError("future source availability was accepted")


def test_source_event_gate_needs_no_xau_column() -> None:
    frame = prepare_source_m5(source_frame(), config())
    params = policy_params()
    for mechanic in MECHANICS:
        mask, direction = source_event_mask_direction(frame, mechanic, params)
        assert set(direction.loc[mask].unique()).issubset({-1, 1})


def test_xau_features_do_not_bridge_missing_m5_bars() -> None:
    starts = pd.to_datetime(
        [
            "2022-01-03T00:00:00Z",
            "2022-01-03T00:05:00Z",
            "2022-01-03T00:15:00Z",
            "2022-01-03T00:20:00Z",
        ]
    )
    close = np.array([100.0, 100.2, 100.4, 100.6])
    xau = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "mid_open": close - 0.05,
            "mid_high": close + 0.1,
            "mid_low": close - 0.1,
            "mid_close": close,
        }
    )
    source = source_frame(10)
    result = prepare_features(xau, source, config())
    assert pd.isna(result.loc[2, "impulse_1_atr"])


def test_registered_mechanics_emit_only_declared_directions() -> None:
    frame = pd.DataFrame(
        {
            "risk_score_1b_12": [2.0, -2.0],
            "growth_score_1b_12": [2.0, -2.0],
            "risk_score_3b_12": [2.0, -2.0],
            "risk_agreeing_legs_1b_12": [3, 3],
            "growth_agreeing_legs_1b_12": [2, 2],
            "session_slot": ["LONDON", "NY"],
            "impulse_1_atr": [0.0, 0.0],
            "body_atr": [-1.0, 1.0],
            "mid_close": [101.0, 99.0],
            "prior_high_6": [100.0, 100.0],
            "prior_low_6": [100.0, 100.0],
            "atr_m5": [1.0, 1.0],
        }
    )
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_tick_count"] = 100
        frame[f"{prefix}_staleness_minutes"] = 0.0
    params = policy_params()
    for mechanic in MECHANICS:
        mask, direction = signal_mask_direction(frame, mechanic, params)
        assert set(direction.loc[mask].unique()).issubset({-1, 1})


def test_manifest_is_source_only_sequential_and_unique() -> None:
    manifest_config = {
        "features": {
            "m5_atr_period": 3,
            "source_normalization_lookbacks": [288, 576, 1152],
        }
    }
    frame = prepare_source_m5(source_frame(3_000), manifest_config)
    start = frame["bar_end_utc"].min()
    end = frame["bar_end_utc"].max() + pd.Timedelta(minutes=5)
    manifest = generate_manifest(
        frame,
        start,
        end,
        attempt_first=125001,
        policies_per_mechanic=2,
        minimum_raw_signals=30,
    )
    assert len(manifest) == 10
    assert manifest["attempt_no"].tolist() == list(range(125001, 125011))
    assert manifest["policy_id"].is_unique


def test_policy_spaces_are_bounded() -> None:
    for mechanic in MECHANICS:
        space = parameter_space(mechanic)
        assert 1_000 < len(space) <= 250_000


def test_v94_is_conditional_and_targets_two_per_day() -> None:
    value = json.loads(
        (ROOT / "config" / "dukascopy_growth_risk_leadlag_v94.json").read_text()
    )
    assert value["research_controls"]["attempt_first"] == 125001
    assert value["research_controls"]["attempt_last"] == 126000
    assert value["shared_account"]["minimum_combined_trades_per_weekday"] == 2.0
    assert value["research_controls"]["v59_v60_modification_authorized"] is False


def test_expected_months_is_exact() -> None:
    assert expected_months(
        "2022-01-01T00:00:00Z", "2022-04-01T00:00:00Z"
    ) == ["2022-01", "2022-02", "2022-03"]


def test_v94_requires_artifact_bound_terminal_v93_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_path = tmp_path / "V93_RESULT.json"
    shared_path = tmp_path / "V93_SHARED.json"
    manifest_path = tmp_path / "V93_ARTIFACT_MANIFEST.json"
    result = {
        "attempt_first": 124001,
        "attempt_last": 125000,
        "registered_policy_count": 1000,
        "contract_sha256": "locked-v93",
        "decision": "V93_DISCOVERY_FAIL_TERMINAL",
    }
    result_path.write_text(json.dumps(result), encoding="utf-8")
    manifest = {
        "contract_sha256": "locked-v93",
        "artifacts": {
            result_path.name: {"sha256": run_research._sha256(result_path)}
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(run_research, "V93_RESULT_PATH", result_path)
    monkeypatch.setattr(run_research, "V93_SHARED_RESULT_PATH", shared_path)
    monkeypatch.setattr(run_research, "V93_ARTIFACT_MANIFEST_PATH", manifest_path)
    evidence = run_research._verify_v93_terminal_failure()
    assert evidence["v93_terminal_reason"] == "V93_DISCOVERY_FAIL_TERMINAL"

    result["decision"] = "V93_DISCOVERY_PASS_ADVANCE"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    manifest["artifacts"][result_path.name]["sha256"] = run_research._sha256(
        result_path
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="remains sealed"):
        run_research._verify_v93_terminal_failure()
