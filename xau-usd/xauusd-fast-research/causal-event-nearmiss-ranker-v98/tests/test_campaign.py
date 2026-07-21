from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import run_research
from src import ml_campaign as campaign


ROOT = Path(__file__).resolve().parents[1]


def _synthetic_m5(rows: int = 1500) -> pd.DataFrame:
    start = pd.Timestamp("2022-01-03T00:00:00Z")
    bar_start = pd.date_range(start, periods=rows, freq="5min")
    wave = np.sin(np.arange(rows) / 11.0) + np.arange(rows) * 0.002
    open_ = 1800.0 + wave
    close = open_ + 0.08 * np.sin(np.arange(rows) / 3.0)
    return pd.DataFrame(
        {
            "bar_start_utc": bar_start,
            "bar_end_utc": bar_start + pd.Timedelta(minutes=5),
            "mid_open": open_,
            "mid_high": np.maximum(open_, close) + 0.10,
            "mid_low": np.minimum(open_, close) - 0.10,
            "mid_close": close,
            "atr": 0.8,
            "atr_ratio": 1.0,
            "quote_intensity_ratio": 1.0,
            "tick_book_imbalance_mean": np.sin(np.arange(rows) / 7.0) * 0.1,
            "tick_microprice_edge_mean": np.cos(np.arange(rows) / 7.0) * 0.01,
            "tick_imbalance_5m": np.sin(np.arange(rows) / 5.0) * 0.05,
            "tick_imbalance_15m": np.sin(np.arange(rows) / 9.0) * 0.03,
            "price_efficiency_5m": 0.1,
            "tick_spread_mean": 0.25,
            "tick_realized_variance": 0.2,
            "close_location": 0.5,
        }
    )


def _candidate_config() -> dict[str, object]:
    return {
        "candidate_protocol": {
            "range_lookback_bars": 16,
            "trend_lookback_bars": 16,
            "impulse_lookback_bars": 4,
            "compression_lookback_bars": 32,
            "compression_quantile_lookback_bars": 64,
            "compression_quantile": 0.25,
            "minimum_body_atr": 0.05,
            "minimum_impulse_atr": 0.20,
            "minimum_trend_atr": 0.20,
        }
    }


def test_policy_registry_is_exactly_one_thousand() -> None:
    all_rows = []
    for mechanic in campaign.MECHANICS:
        rows = campaign.parameter_space(mechanic)
        assert len(rows) == 200
        assert len({json.dumps(row, sort_keys=True) for row in rows}) == 200
        all_rows.extend((mechanic, json.dumps(row, sort_keys=True)) for row in rows)
    assert len(all_rows) == 1000
    assert len(set(all_rows)) == 1000


def test_feature_sets_are_distinct_and_contain_no_outcomes() -> None:
    sets = {name: campaign.feature_columns(name) for name in campaign.MECHANICS}
    assert len({tuple(value) for value in sets.values()}) == 5
    assert "body_atr" in sets["PRICE_EVENT_STATE"]
    assert "book_imbalance" in sets["MICRO_EVENT_STATE"]
    assert set(sets["ALL_EVENT_STATE"]).issuperset(
        sets["PRICE_MICRO_EVENT_STATE"]
    )
    assert not any(
        "future" in column or "label" in column or "pnl" in column
        for value in sets.values()
        for column in value
    )


def test_candidate_features_do_not_change_when_future_bars_change() -> None:
    source = _synthetic_m5()
    changed = source.copy()
    cutoff = source.loc[1199, "bar_end_utc"]
    future = changed["bar_end_utc"].gt(cutoff)
    for column in ("mid_open", "mid_high", "mid_low", "mid_close"):
        changed.loc[future, column] += 500.0
    first = campaign.prepare_features(pd.DataFrame(), source, None, _candidate_config())
    second = campaign.prepare_features(pd.DataFrame(), changed, None, _candidate_config())
    first = first.loc[first["bar_end_utc"].le(cutoff)].reset_index(drop=True)
    second = second.loc[second["bar_end_utc"].le(cutoff)].reset_index(drop=True)
    pd.testing.assert_frame_equal(first, second)
    assert first["bar_end_utc"].dt.minute.isin((0, 15, 30, 45)).all()


def test_source_only_manifest_has_exact_attempt_registry() -> None:
    timestamps = pd.date_range("2022-07-01", periods=1800, freq="h", tz="UTC")
    events = pd.DataFrame(
        {
            "bar_end_utc": timestamps,
            "direction_value": np.where(np.arange(len(timestamps)) % 2, 1, -1),
        }
    )
    manifest = campaign.generate_manifest(
        events,
        pd.Timestamp("2022-07-01T00:00:00Z"),
        pd.Timestamp("2024-07-01T00:00:00Z"),
        129001,
        200,
        1500,
    )
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(129001, 130001))
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()


def test_best_action_is_selected_before_frequency_routing() -> None:
    time = pd.Timestamp("2024-01-02T08:00:00Z")
    actions = pd.DataFrame(
        {
            "signal_time": [time, time],
            "entry_time": [time, time],
            "exit_time": [time + pd.Timedelta(hours=1)] * 2,
            "direction_value": [1, -1],
            "event_type": ["IMPULSE_RETEST", "FAILED_RANGE_BREAK"],
            "session_slot": ["LONDON", "LONDON"],
            "score": [0.51, 0.61],
        }
    )
    selected = campaign._best_action_per_signal(actions)
    assert len(selected) == 1
    assert int(selected.iloc[0]["direction_value"]) == -1


def test_router_enforces_daily_and_session_caps() -> None:
    times = pd.to_datetime(
        [
            "2024-01-02T02:00:00Z",
            "2024-01-02T03:00:00Z",
            "2024-01-02T08:00:00Z",
            "2024-01-02T14:00:00Z",
        ],
        utc=True,
    )
    actions = pd.DataFrame(
        {
            "signal_time": times,
            "entry_time": times,
            "exit_time": times + pd.Timedelta(minutes=30),
            "direction_value": [1, 1, -1, 1],
            "event_type": ["IMPULSE_RETEST"] * 4,
            "session_slot": ["ASIA", "ASIA", "LONDON", "NY"],
            "score": [0.9, 0.8, 0.7, 0.6],
        }
    )
    config = {
        "execution": {
            "maximum_model_open_positions": 2,
            "maximum_trades_per_policy_utc_day": 2,
            "maximum_trades_per_session_slot": 1,
        }
    }
    selected = campaign._route_candidates(actions, 0.5, config)
    assert len(selected) == 2
    assert selected["session_slot"].tolist() == ["ASIA", "LONDON"]


def test_config_fixes_ceiling_attempts_and_research_only_training() -> None:
    config = json.loads(
        (ROOT / "config" / "causal_event_nearmiss_ranker_v98.json").read_text()
    )
    controls = config["research_controls"]
    assert controls["attempt_first"] == 129001
    assert controls["attempt_last"] == 130000
    assert controls["registered_policy_count"] == 1000
    assert controls["model_training_authorized"] is True
    assert controls["model_training_for_research_only"] is True
    assert controls["python_predictions_authorized"] is False
    assert controls["broker_action_authorized"] is False
    assert config["shared_account"]["minimum_combined_trades_per_weekday"] == 2.0


def test_v98_requires_artifact_bound_terminal_v97_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_path = tmp_path / "V97_RESULT.json"
    manifest_path = tmp_path / "V97_ARTIFACT_MANIFEST.json"
    result = {
        "attempt_first": 128001,
        "attempt_last": 129000,
        "registered_policy_count": 1000,
        "contract_sha256": "locked-v97",
        "decision": "V97_DISCOVERY_FAIL_TERMINAL",
    }
    result_path.write_text(json.dumps(result))
    result_hash = hashlib.sha256(result_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(
            {
                "contract_sha256": "locked-v97",
                "artifacts": {result_path.name: {"sha256": result_hash}},
            }
        )
    )
    monkeypatch.setattr(run_research, "V97_RESULT_PATH", result_path)
    monkeypatch.setattr(run_research, "V97_ARTIFACT_MANIFEST_PATH", manifest_path)
    evidence = run_research._verify_v97_terminal_failure()
    assert evidence["v97_terminal_reason"] == "V97_DISCOVERY_FAIL_TERMINAL"

    result["decision"] = "V97_DISCOVERY_PASS_ADVANCE"
    result_path.write_text(json.dumps(result))
    with pytest.raises(RuntimeError):
        run_research._verify_v97_terminal_failure()
