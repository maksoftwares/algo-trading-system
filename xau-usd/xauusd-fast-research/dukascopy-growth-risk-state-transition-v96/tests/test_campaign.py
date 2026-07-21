from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lock_contract import expected_months
import run_research
from src.campaign import (
    MECHANICS,
    _contiguous_lag,
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


def test_contiguous_lag_rejects_missing_h1_bar() -> None:
    frame = pd.DataFrame(
        {
            "bar_end_utc": pd.to_datetime(
                [
                    "2024-01-02T01:00:00Z",
                    "2024-01-02T02:00:00Z",
                    "2024-01-02T04:00:00Z",
                ]
            )
        }
    )
    assert _contiguous_lag(frame, 1).tolist() == [False, True, False]


def transition_frame(
    prior_risk: float,
    current_risk: float,
    prior_growth: float,
    current_growth: float,
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "bar_end_utc": pd.to_datetime(
                ["2024-01-02T12:00:00Z", "2024-01-02T13:00:00Z"]
            ),
            "risk_score_1h_120": [prior_risk, current_risk],
            "growth_score_1h_120": [prior_growth, current_growth],
            "session_slot": ["LONDON", "NY"],
        }
    )
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_active_m5"] = 12
        frame[f"{prefix}_staleness_minutes"] = 1.0
    return frame


def transition_params() -> dict:
    return {
        "source_horizon": 1,
        "source_lookback": 120,
        "current_threshold_z": 0.4,
        "prior_threshold_z": 0.4,
        "transition_lag_hours": 1,
        "minimum_active_m5": 6,
        "maximum_source_staleness_minutes": 15,
        "session": "ALL",
        "maximum_response_atr": 0.75,
        "acceleration_ratio": 1.5,
        "channel_bars": 6,
        "breakout_buffer_atr": 0.0,
    }


def test_source_event_gate_does_not_require_any_xau_column() -> None:
    params = transition_params()
    cases = {
        "RISK_SIGN_REVERSAL": (2.0, -2.0, 0.6, 0.6),
        "GROWTH_SIGN_REVERSAL": (0.6, 0.6, 2.0, -2.0),
        "RISK_STATE_ACCELERATION": (0.6, 1.2, 0.6, 0.6),
        "GROWTH_STATE_ACCELERATION": (0.6, 0.6, 0.6, 1.2),
    }
    for mechanic, values in cases.items():
        frame = transition_frame(*values)
        mask, direction = source_event_mask_direction(frame, mechanic, params)
        assert mask.iloc[1]
        assert direction.iloc[1] in {-1, 1}


def test_registered_signal_mechanics_emit_only_long_or_short() -> None:
    params = transition_params()
    cases = {
        "RISK_SIGN_REVERSAL": (2.0, -2.0, 0.6, 0.6),
        "GROWTH_SIGN_REVERSAL": (0.6, 0.6, 2.0, -2.0),
        "RISK_STATE_ACCELERATION": (0.6, 1.2, 0.6, 0.6),
        "GROWTH_STATE_ACCELERATION": (0.6, 0.6, 0.6, 1.2),
    }
    for mechanic, values in cases.items():
        frame = transition_frame(*values)
        frame["impulse_1_atr"] = 0.0
        frame["body_atr"] = [0.0, 0.1]
        frame["mid_close"] = [100.0, 101.0]
        frame["prior_high_6"] = 100.0
        frame["prior_low_6"] = 100.0
        frame["atr14"] = 1.0
        mask, direction = signal_mask_direction(frame, mechanic, params)
        assert mask.iloc[1]
        assert set(direction.loc[mask].unique()).issubset({-1, 1})


def test_policy_spaces_are_bounded_and_contain_execution_geometry() -> None:
    for mechanic in MECHANICS:
        space = parameter_space(mechanic)
        assert 1_000 < len(space) <= 200_000
        assert {"stop_atr", "target_r", "hold_hours"}.issubset(space[0])


def test_manifest_is_sequential_unique_and_constructed_from_source_only() -> None:
    rows = 2_400
    frame = pd.DataFrame(
        {
            "bar_end_utc": pd.date_range(
                "2022-07-01T01:00:00Z", periods=rows, freq="h"
            ),
            "session_slot": np.resize(["ASIA", "LONDON", "NY"], rows),
        }
    )
    risk = np.resize([0.5, 2.0, -2.0, -0.5, -2.0, 2.0, 0.5, 2.0], rows)
    growth = np.resize([-0.5, 2.0, 2.0, -0.5, -2.0, -2.0, 0.5, 2.0], rows)
    for horizon in (1, 3, 6):
        for lookback in (120, 240, 480):
            frame[f"risk_score_{horizon}h_{lookback}"] = risk
            frame[f"growth_score_{horizon}h_{lookback}"] = growth
    for prefix in ("spx", "copper", "usdcnh"):
        frame[f"{prefix}_active_m5"] = 12
        frame[f"{prefix}_staleness_minutes"] = 0.0

    manifest = generate_manifest(
        frame,
        pd.Timestamp("2022-07-01T00:00:00Z"),
        pd.Timestamp("2023-01-01T00:00:00Z"),
        attempt_first=127001,
        policies_per_mechanic=2,
        minimum_raw_signals=60,
    )

    assert len(manifest) == 8
    assert manifest["attempt_no"].tolist() == list(range(127001, 127009))
    assert manifest["policy_id"].is_unique
    assert manifest.groupby("mechanic").size().eq(2).all()


def test_windows_and_attempts_target_two_per_day_not_v60_milestone() -> None:
    config = json.loads(
        (ROOT / "config" / "dukascopy_growth_risk_state_transition_v96.json").read_text()
    )
    assert config["windows"]["discovery"] == [
        "2022-07-01T00:00:00Z",
        "2024-07-01T00:00:00Z",
    ]
    assert config["shared_account"]["minimum_combined_trades_per_weekday"] == 2.0
    assert config["research_controls"]["attempt_first"] == 127001
    assert config["research_controls"]["attempt_last"] == 128000
    assert config["research_controls"]["registered_policy_count"] == 1000
    assert config["research_controls"]["v59_v60_modification_authorized"] is False


def test_expected_months_requires_exact_consecutive_source_range() -> None:
    assert expected_months(
        "2022-01-01T00:00:00Z", "2022-04-01T00:00:00Z"
    ) == ["2022-01", "2022-02", "2022-03"]


def test_v96_requires_artifact_bound_terminal_v94_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_path = tmp_path / "V94_RESULT.json"
    shared_path = tmp_path / "V94_SHARED.json"
    manifest_path = tmp_path / "V94_ARTIFACT_MANIFEST.json"
    result = {
        "attempt_first": 125001,
        "attempt_last": 126000,
        "registered_policy_count": 1000,
        "contract_sha256": "locked-v94",
        "decision": "V94_DISCOVERY_FAIL_TERMINAL",
    }
    result_path.write_text(json.dumps(result), encoding="utf-8")
    manifest = {
        "contract_sha256": "locked-v94",
        "artifacts": {
            result_path.name: {"sha256": run_research._sha256(result_path)}
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(run_research, "V94_RESULT_PATH", result_path)
    monkeypatch.setattr(run_research, "V94_SHARED_RESULT_PATH", shared_path)
    monkeypatch.setattr(run_research, "V94_ARTIFACT_MANIFEST_PATH", manifest_path)
    evidence = run_research._verify_v94_terminal_failure()
    assert evidence["v94_terminal_reason"] == "V94_DISCOVERY_FAIL_TERMINAL"

    result["decision"] = "V94_DISCOVERY_PASS_ADVANCE"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    manifest["artifacts"][result_path.name]["sha256"] = run_research._sha256(
        result_path
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="remains sealed"):
        run_research._verify_v94_terminal_failure()


def test_v96_requires_source_bound_v95_preoutcome_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failure_path = tmp_path / "V95_FAILURE.json"
    failure = {
        "status": "TERMINAL_PREOUTCOME_LOCK_FAILURE",
        "failure_stage": "SOURCE_ONLY_POLICY_MANIFEST_ADMISSION",
        "failed_mechanic": "RISK_GROWTH_CONVERGENCE",
        "source_eligible_policy_count": 0,
        "required_policy_count": 200,
        "growth_risk_feature_sha256": "feature-hash",
        "growth_risk_manifest_sha256": "manifest-hash",
        "outcomes_opened": False,
        "strategy_scoring_performed": False,
        "thresholds_changed_after_failure": False,
    }
    failure_path.write_text(json.dumps(failure), encoding="utf-8")
    monkeypatch.setattr(run_research, "V95_FAILURE_PATH", failure_path)
    config = {
        "growth_risk_source": {
            "feature_sha256": "feature-hash",
            "manifest_sha256": "manifest-hash",
        }
    }
    evidence = run_research._verify_v95_preoutcome_failure(config)
    assert evidence["v95_status"] == "TERMINAL_PREOUTCOME_LOCK_FAILURE"

    failure["outcomes_opened"] = True
    failure_path.write_text(json.dumps(failure), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence is invalid"):
        run_research._verify_v95_preoutcome_failure(config)
