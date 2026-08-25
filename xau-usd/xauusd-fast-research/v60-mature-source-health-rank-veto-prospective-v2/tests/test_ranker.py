from __future__ import annotations

import numpy as np
import pandas as pd

from src.ranker import score_candidates


class FakeServing:
    def __init__(self) -> None:
        self.reference_lengths: list[int] = []

    def score_candidate(
        self,
        bundle,
        feature_bars,
        decision_time,
        *,
        is_long,
        is_core,
        maximum_bar_age,
    ):
        self.reference_lengths.append(len(bundle["historical_oos_score_reference"]))
        score = 0.8 if is_long else 0.2
        reference = np.asarray(bundle["historical_oos_score_reference"])
        return {
            "reason": "SCORE_COMPLETE",
            "score": score,
            "rank": float(np.searchsorted(np.sort(reference), score, side="right") / len(reference)),
            "topup": True,
        }


def test_same_timestamp_scores_do_not_enter_each_others_reference() -> None:
    serving = FakeServing()
    runtime = {
        "serving": serving,
        "bundle": {"historical_oos_score_reference": np.asarray([0.0, 1.0])},
        "feature_bars": pd.DataFrame(),
        "model_sha256": "model",
        "feature_rows": 10,
    }
    candidates = [
        {
            "candidate_id": "a",
            "specialist_id": "A",
            "scheduled_entry_time_utc": "2026-07-21T00:00:00Z",
            "direction": "LONG",
            "sleeve_type": "CORE",
        },
        {
            "candidate_id": "b",
            "specialist_id": "B",
            "scheduled_entry_time_utc": "2026-07-21T00:00:00Z",
            "direction": "SHORT",
            "sleeve_type": "ADDON",
        },
        {
            "candidate_id": "c",
            "specialist_id": "C",
            "scheduled_entry_time_utc": "2026-07-21T00:05:00Z",
            "direction": "LONG",
            "sleeve_type": "CORE",
        },
    ]
    decisions, audit = score_candidates(
        runtime,
        candidates,
        {
            "score_start_inclusive_utc": "2026-07-21T00:00:00Z",
            "maximum_feature_bar_age_minutes": 10,
        },
    )
    assert serving.reference_lengths == [2, 2, 4]
    assert set(decisions) == {"a", "b", "c"}
    assert all(not row["topup"] for row in decisions.values())
    assert all(not row["broker_action_authorized"] for row in decisions.values())
    assert audit["scored_candidate_rows"] == 3
