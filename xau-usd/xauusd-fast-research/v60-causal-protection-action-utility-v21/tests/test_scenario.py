from __future__ import annotations

import math
from dataclasses import dataclass

from src.scenario import (
    FORBIDDEN_MODEL_FIELDS,
    MODEL_FEATURES,
    build_action_rows,
)


@dataclass
class Candidate:
    source_id: str
    direction: str
    entry_ms: int
    exit_ms: int
    risk_usd: float
    pnl_usd: float


@dataclass
class Position:
    candidate: Candidate


class Replay:
    @staticmethod
    def utc_text(value: int) -> str:
        return str(value)


def test_action_rows_are_cluster_weighted_and_label_only() -> None:
    positions = {
        "a": Position(Candidate("S1", "LONG", 0, 3000, 10.0, 8.0)),
        "b": Position(Candidate("S2", "SHORT", 500, 3500, 20.0, -1.0)),
    }
    rows = build_action_rows(
        replay=Replay,
        positions=positions,
        marked_pnl={"a": 2.0, "b": 1.0},
        now_ms=2000,
        arm_ms=1000,
        active_risk=30.0,
        open_pnl=3.0,
        peak_open_pnl=18.0,
    )
    assert len(rows) == 2
    assert math.isclose(sum(row["action_sample_weight"] for row in rows), 1.0)
    assert rows[0]["keep_open_utility_r"] == 0.6
    assert rows[1]["keep_open_utility_r"] == -0.1
    assert rows[0]["basket_giveback_from_peak_r"] == 0.5


def test_forbidden_fields_are_not_model_features() -> None:
    assert not set(MODEL_FEATURES).intersection(FORBIDDEN_MODEL_FIELDS)
    assert "candidate_endpoint_pnl_usd" not in MODEL_FEATURES
    assert "action_year" not in MODEL_FEATURES
