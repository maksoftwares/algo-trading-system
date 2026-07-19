from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gap_restart import (  # noqa: E402
    CANDIDATE_COLUMNS,
    assert_v24_execution_parity,
    evaluate_stage,
    generate_candidates,
    load_config,
    load_locked_v24,
)


def make_ticks(gap_ms: int = 2200, direction: int = 1) -> pd.DataFrame:
    start = int(pd.Timestamp("2026-07-20T12:00:00Z").timestamp() * 1000)
    before = [start, start + 100]
    restart = before[-1] + gap_ms
    after = [restart + offset for offset in range(0, 1100, 100)]
    times = np.asarray(before + after, dtype=np.int64)
    mid = np.asarray(
        [2000.0, 2000.0]
        + [2000.0 + direction * 0.10 * index for index in range(len(after))],
        dtype=float,
    )
    return pd.DataFrame(
        {
            "tick_time_msc": times,
            "bid": mid - 0.15,
            "ask": mid + 0.15,
            "spread_price": 0.30,
        }
    )


def test_restart_candidate_is_causal_and_directional() -> None:
    config = load_config(ROOT)
    ticks = make_ticks(direction=1)
    candidates, audit = generate_candidates(ticks, config)
    assert audit["restart_episode_count"] == 1
    assert audit["raw_candidate_count"] == 1
    assert len(candidates) == 1
    candidate = candidates.iloc[0]
    assert candidate["candidate_side"] == "LONG"
    assert candidate["nonzero_mid_updates"] >= 5
    assert candidate["elapsed_since_restart_ms"] <= 1000
    assert int(candidate["tick_time_msc"]) <= int(ticks["tick_time_msc"].max())


def test_gap_outside_locked_range_creates_no_restart() -> None:
    config = load_config(ROOT)
    for gap in (1999, 5001):
        candidates, audit = generate_candidates(make_ticks(gap_ms=gap), config)
        assert candidates.empty
        assert audit["restart_episode_count"] == 0


def test_future_quote_does_not_change_existing_candidate() -> None:
    config = load_config(ROOT)
    ticks = make_ticks(direction=-1)
    before, _ = generate_candidates(ticks, config)
    future = ticks.iloc[[-1]].copy()
    future["tick_time_msc"] += 60_000
    future["bid"] += 100.0
    future["ask"] += 100.0
    after, _ = generate_candidates(pd.concat([ticks, future], ignore_index=True), config)
    pd.testing.assert_frame_equal(before, after)


def test_only_first_restart_event_per_four_hour_block_is_kept() -> None:
    config = load_config(ROOT)
    first = make_ticks()
    second = make_ticks()
    second["tick_time_msc"] += 10 * 60 * 1000
    candidates, audit = generate_candidates(
        pd.concat([first, second], ignore_index=True), config
    )
    assert audit["raw_candidate_count"] == 2
    assert len(candidates) == 1


def test_empty_input_has_stable_candidate_schema() -> None:
    candidates, audit = generate_candidates(pd.DataFrame(), load_config(ROOT))
    assert tuple(candidates.columns) == CANDIDATE_COLUMNS
    assert audit == {"restart_episode_count": 0, "raw_candidate_count": 0}


def test_execution_cost_and_gate_contract_matches_v24_1() -> None:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    assert_v24_execution_parity(config, v24)
    changed = deepcopy(config)
    changed["simulation"]["hold_seconds"] += 1
    with pytest.raises(ValueError, match="differs from V24.1"):
        assert_v24_execution_parity(changed, v24)


def test_selection_adjusted_block_bootstrap_gate_is_applied() -> None:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    dates = pd.date_range("2026-07-20", periods=20, freq="B").strftime("%Y-%m-%d")
    rows = []
    sequence = 0
    for date in dates:
        for side in ("LONG", "SHORT"):
            rows.append(
                {
                    "evidence_partition": "FORWARD_VALIDATION",
                    "date_utc": date,
                    "entry_time_msc": sequence,
                    "side": side,
                    "base_pnl_dollars": 1.0,
                    "stress_pnl_dollars": 0.8,
                }
            )
            sequence += 1
    audit, _ = evaluate_stage(
        pd.DataFrame(rows),
        dates.tolist(),
        "FORWARD_VALIDATION",
        config,
        v24,
    )
    assert config["multiple_testing"]["maximum_one_sided_pvalue"] == pytest.approx(
        config["multiple_testing"]["family_alpha"]
        / config["multiple_testing"]["registered_capital_forward_hypotheses"]
    )
    key = "selection_adjusted_daily_block_bootstrap_pvalue"
    assert audit["gate_checks"][key]
    assert audit["metrics"][key] <= 0.025
    assert audit["block_length_weekdays"] == 5
    assert audit["v24_1_external_admission_recheck_required"] is True
    assert audit["gate_passed"]


def test_selection_adjusted_block_bootstrap_rejects_zero_mean() -> None:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    dates = pd.date_range("2026-07-20", periods=20, freq="B").strftime("%Y-%m-%d")
    rows = []
    for index, date in enumerate(dates):
        pnl = 1.0 if index % 2 == 0 else -1.0
        rows.append(
            {
                "evidence_partition": "FORWARD_VALIDATION",
                "date_utc": date,
                "entry_time_msc": index,
                "side": "LONG" if index % 2 == 0 else "SHORT",
                "base_pnl_dollars": pnl,
                "stress_pnl_dollars": pnl,
            }
        )
    audit, _ = evaluate_stage(
        pd.DataFrame(rows),
        dates.tolist(),
        "FORWARD_VALIDATION",
        config,
        v24,
    )
    key = "selection_adjusted_daily_block_bootstrap_pvalue"
    assert not audit["gate_checks"][key]
    assert audit["metrics"][key] > 0.025
    assert not audit["gate_passed"]


def test_research_controls_never_authorize_training_or_trading() -> None:
    controls = load_config(ROOT)["research_controls"]
    assert controls["hypothesis_count"] == 1
    assert controls["outcome_blind_calibration_before_lock"] is True
    for key in (
        "calibration_post_candidate_prices_used_for_label_or_outcome",
        "calibration_pnl_calculated",
        "parameter_grid_allowed",
        "same_version_tuning_authorized",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    ):
        assert controls[key] is False
