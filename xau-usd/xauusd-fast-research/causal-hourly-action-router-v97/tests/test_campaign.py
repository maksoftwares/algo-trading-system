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


def test_policy_registry_is_exactly_one_thousand() -> None:
    all_rows = []
    for mechanic in campaign.MECHANICS:
        rows = campaign.parameter_space(mechanic)
        assert len(rows) == 200
        assert len({json.dumps(row, sort_keys=True) for row in rows}) == 200
        all_rows.extend((mechanic, json.dumps(row, sort_keys=True)) for row in rows)
    assert len(all_rows) == 1000
    assert len(set(all_rows)) == 1000


def test_feature_sets_are_causal_and_distinct() -> None:
    sets = {name: campaign.feature_columns(name) for name in campaign.MECHANICS}
    assert len({tuple(value) for value in sets.values()}) == 5
    assert "body_atr" in sets["PRICE_STATE"]
    assert "m5_book_imbalance" in sets["MICROSTRUCTURE_STATE"]
    assert "risk_score_3h_240" in sets["CROSSASSET_STATE"]
    assert set(sets["ALL_CAUSAL_STATE"]).issuperset(
        sets["PRICE_CROSSASSET_STATE"]
    )
    assert not any("future" in column or "label" in column for value in sets.values() for column in value)


def test_source_only_manifest_has_exact_attempt_registry() -> None:
    timestamps = pd.date_range("2022-07-01", periods=2200, freq="h", tz="UTC")
    source = pd.DataFrame({"bar_end_utc": timestamps})
    source["session_slot"] = np.select(
        [
            source["bar_end_utc"].dt.hour.between(1, 6),
            source["bar_end_utc"].dt.hour.between(7, 12),
            source["bar_end_utc"].dt.hour.between(13, 18),
        ],
        ["ASIA", "LONDON", "NY"],
        default="OUTSIDE",
    )
    for prefix in campaign.PREFIXES:
        source[f"{prefix}_active_m5"] = 12
        source[f"{prefix}_staleness_minutes"] = 1.0
    manifest = campaign.generate_manifest(
        source,
        pd.Timestamp("2022-07-01T00:00:00Z"),
        pd.Timestamp("2024-07-01T00:00:00Z"),
        128001,
        200,
        1000,
    )
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(128001, 129001))
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()
    assert manifest["raw_discovery_signal_count"].min() >= 1000


def test_best_action_is_selected_before_frequency_routing() -> None:
    time = pd.Timestamp("2024-01-02T08:00:00Z")
    actions = pd.DataFrame(
        {
            "signal_time": [time, time],
            "entry_time": [time, time],
            "exit_time": [time + pd.Timedelta(hours=1)] * 2,
            "direction_value": [1, -1],
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


def test_config_fixes_attempts_and_research_only_training() -> None:
    config = json.loads(
        (ROOT / "config" / "causal_hourly_action_router_v97.json").read_text()
    )
    controls = config["research_controls"]
    assert controls["attempt_first"] == 128001
    assert controls["attempt_last"] == 129000
    assert controls["registered_policy_count"] == 1000
    assert controls["model_training_authorized"] is True
    assert controls["model_training_for_research_only"] is True
    assert controls["python_predictions_authorized"] is False
    assert controls["broker_action_authorized"] is False
    assert config["shared_account"]["minimum_combined_trades_per_weekday"] == 2.0


def test_v97_requires_artifact_bound_terminal_v96_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_path = tmp_path / "V96_RESULT.json"
    manifest_path = tmp_path / "V96_ARTIFACT_MANIFEST.json"
    result = {
        "attempt_first": 127001,
        "attempt_last": 128000,
        "registered_policy_count": 1000,
        "contract_sha256": "locked-v96",
        "decision": "V96_DISCOVERY_FAIL_TERMINAL",
    }
    result_path.write_text(json.dumps(result))
    result_hash = hashlib.sha256(result_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(
            {
                "contract_sha256": "locked-v96",
                "artifacts": {result_path.name: {"sha256": result_hash}},
            }
        )
    )
    monkeypatch.setattr(run_research, "V96_RESULT_PATH", result_path)
    monkeypatch.setattr(run_research, "V96_ARTIFACT_MANIFEST_PATH", manifest_path)
    evidence = run_research._verify_v96_terminal_failure()
    assert evidence["v96_terminal_reason"] == "V96_DISCOVERY_FAIL_TERMINAL"

    result["decision"] = "V96_DISCOVERY_PASS_ADVANCE"
    result_path.write_text(json.dumps(result))
    with pytest.raises(RuntimeError):
        run_research._verify_v96_terminal_failure()
