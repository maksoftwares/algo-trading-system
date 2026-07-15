from __future__ import annotations

from conftest import BASE_TS, model_rows
from xau_crossasset_residual.core import LONG_ID, SHORT_ID, construct_episodes


def test_negative_and_positive_residual_crossings_create_correct_directions():
    candidates = construct_episodes(model_rows([0, -2.6, -3.0, 0.1, 2.6, 3.0]))
    assert [row["specialist_id"] for row in candidates] == [LONG_ID, SHORT_ID]


def test_no_repeated_long_candidate_inside_one_excursion():
    candidates = construct_episodes(model_rows([0, -2.6, -2.4, -2.7, -3.0, 0.0, -2.6]))
    assert [row["specialist_id"] for row in candidates].count(LONG_ID) == 2


def test_zero_crossing_ends_excursion_and_allows_new_episode():
    candidates = construct_episodes(model_rows([0, 2.6, 2.4, 0.0, 2.6]))
    assert [row["specialist_id"] for row in candidates].count(SHORT_ID) == 2


def test_six_hour_gap_ends_existing_excursion():
    frame = model_rows([0, -2.6, -2.4])
    frame.loc[2, "timestamp_ms"] = BASE_TS + 6 * 3_600_000 + 300_000
    frame.loc[2, "residual_z"] = -2.6
    candidates = construct_episodes(frame)
    assert len(candidates) == 1  # a discontinuous bar cannot fabricate a new crossing
