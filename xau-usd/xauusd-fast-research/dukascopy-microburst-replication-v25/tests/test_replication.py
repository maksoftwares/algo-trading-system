from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from replication import (  # noqa: E402
    assert_frozen_rule_parity,
    decode_hour_payload,
    first_runnable_stage,
    label_path_within_stage,
    load_config,
    load_locked_v24,
    maximum_label_path_ms,
)


def synthetic_payload(hour: pd.Timestamp) -> dict[str, object]:
    return {
        "timestamp": int(hour.timestamp() * 1000),
        "multiplier": 0.001,
        "bid": 2000.0,
        "ask": 2000.3,
        "times": [100, 900, 1000],
        "bids": [0, 100, -50],
        "asks": [0, 100, -50],
        "bidVolumes": [1.0, 1.0, 1.0],
        "askVolumes": [1.0, 1.0, 1.0],
    }


def test_decoder_reconstructs_delta_encoded_bidask_ticks() -> None:
    hour = pd.Timestamp("2026-06-30T20:00:00Z")
    times, bids, asks = decode_hour_payload(synthetic_payload(hour), hour, 3)
    base = int(hour.timestamp() * 1000)
    assert times.tolist() == [base + 100, base + 1000, base + 2000]
    assert bids.tolist() == pytest.approx([2000.0, 2000.1, 2000.05])
    assert asks.tolist() == pytest.approx([2000.3, 2000.4, 2000.35])


def test_decoder_rejects_crossed_quote() -> None:
    hour = pd.Timestamp("2026-06-30T20:00:00Z")
    payload = synthetic_payload(hour)
    payload["ask"] = 1999.0
    with pytest.raises(ValueError, match="quote is invalid"):
        decode_hour_payload(payload, hour, 3)


def test_label_path_is_purged_at_chronological_boundary() -> None:
    config = load_config(ROOT)
    end = int(pd.Timestamp("2020-07-01T00:00:00Z").timestamp() * 1000)
    width = maximum_label_path_ms(config)
    assert width == 124_000
    assert label_path_within_stage(end - width - 1, end, config)
    assert not label_path_within_stage(end - width, end, config)


def test_all_signal_cost_and_gate_sections_equal_locked_v24_1() -> None:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    assert_frozen_rule_parity(config, v24)
    changed = deepcopy(config)
    changed["feature"]["lookback_ms"] += 1
    with pytest.raises(ValueError, match="differs from frozen V24.1"):
        assert_frozen_rule_parity(changed, v24)


def test_locked_candidate_generator_remains_causal_and_bidirectional() -> None:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    start = int(pd.Timestamp("2026-06-30T12:00:00Z").timestamp() * 1000)
    times = np.arange(start, start + 12_100, 100, dtype=np.int64)
    first = np.linspace(2000.0, 2004.0, 61)
    second = np.linspace(2004.0, 1999.0, len(times) - len(first))
    mid = np.concatenate((first, second))
    ticks = pd.DataFrame(
        {
            "tick_time_msc": times,
            "bid": mid - 0.15,
            "ask": mid + 0.15,
            "spread_price": 0.30,
        }
    )
    candidates, features = v24.generate_candidates(ticks, config)
    assert not candidates.empty
    assert candidates["tick_time_msc"].max() <= times.max()
    assert set(candidates["candidate_side"]).issubset({"LONG", "SHORT"})
    assert not any("future" in column.lower() for column in features.columns)


def test_stage_order_opens_only_first_unseen_stage_after_prior_pass() -> None:
    config = load_config(ROOT)
    assert first_runnable_stage(config, {})["id"] == "EARLY_REPLICATION"
    early_pass = {"EARLY_REPLICATION": {"gate_passed": True}}
    assert first_runnable_stage(config, early_pass)["id"] == "MIDDLE_VALIDATION"
    early_fail = {"EARLY_REPLICATION": {"gate_passed": False}}
    assert first_runnable_stage(config, early_fail) is None


def test_research_controls_never_authorize_training_or_execution() -> None:
    controls = load_config(ROOT)["research_controls"]
    assert controls["hypothesis_count"] == 1
    assert controls["dukascopy_archive_previously_used_for_other_research"] is True
    for key in (
        "replication_rule_selected_from_dukascopy_outcomes",
        "untouched_archive_claimed",
        "parameter_grid_allowed",
        "same_version_tuning_authorized",
        "paid_data_used",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    ):
        assert controls[key] is False


def test_config_has_three_contiguous_chronological_stages() -> None:
    config = load_config(ROOT)
    stages = config["stages"]
    assert len(stages) == 3
    assert stages[0]["start_inclusive_utc"] == config["source"]["start_inclusive_utc"]
    assert stages[-1]["end_exclusive_utc"] == config["source"]["end_exclusive_utc"]
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        assert left["end_exclusive_utc"] == right["start_inclusive_utc"]
    assert json.dumps(stages, sort_keys=True)
