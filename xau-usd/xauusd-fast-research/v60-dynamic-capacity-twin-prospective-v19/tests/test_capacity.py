from collections import defaultdict, deque
from datetime import UTC, datetime
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.capacity import (
    CandidateFact,
    TickDay,
    advance_resolution,
    canonical_sha256,
    completed_tick_paths,
    five_second_cycles,
    initial_resolution,
    load_causal_scores,
    load_tick_day,
    warm_started_challenger_class,
)


HEADER = (
    "schema_version,account_login,symbol,tick_time_msc,bid,ask\n"
)


def write_ticks(path: Path, rows: list[tuple[int, float, float]]) -> None:
    body = "".join(
        f"xau_prospective_tick_v1,1033030,XAUUSD,{stamp},{bid},{ask}\n"
        for stamp, bid, ask in rows
    )
    path.write_text(HEADER + body, encoding="utf-8")


def fact(
    *,
    direction: str = "LONG",
    target_r: float | None = 2.0,
    hold_hours: float | None = None,
) -> CandidateFact:
    candidate = SimpleNamespace(
        candidate_id="candidate-1",
        source_id="V57_BREAK_SWING_H4ADX_HIGH",
        specialist_id="V57_BREAK_SWING_H4ADX_HIGH",
        sleeve_type="ADDON",
        direction=direction,
        event_id="event-1",
        scheduled_at=datetime(2026, 8, 26, tzinfo=UTC),
        maximum_entry_gap_minutes=10,
        maximum_spread_r=0.15,
        stop_distance=10.0,
        initial_risk_usd=10.0,
        target_r=target_r,
        hold_hours=hold_hours,
    )
    return CandidateFact(candidate=candidate, source={}, fact_sha256="fact-hash")


def day(rows: list[tuple[int, float, float]]) -> TickDay:
    return TickDay(
        path=Path("ticks_20260826.csv"),
        day=datetime(2026, 8, 26, tzinfo=UTC).date(),
        times=np.asarray([row[0] for row in rows], dtype=np.int64),
        bids=np.asarray([row[1] for row in rows], dtype=float),
        asks=np.asarray([row[2] for row in rows], dtype=float),
        sha256="tick-hash",
        duplicate_rows_collapsed=0,
    )


ECONOMICS = {
    "ticket_cost_usd": 0.30,
    "holding_cost_per_24h_usd": 0.35,
    "stress_slippage_r": 0.05,
}


def test_tick_loader_collapses_only_identical_timestamp_quotes(tmp_path: Path) -> None:
    path = tmp_path / "feed_ticks_20260826.csv"
    write_ticks(
        path,
        [
            (1787702400000, 100.0, 100.2),
            (1787702400000, 100.0, 100.2),
            (1787702401000, 100.1, 100.3),
        ],
    )
    loaded = load_tick_day(path, "xau_prospective_tick_v1")
    assert loaded.times.tolist() == [1787702400000, 1787702401000]
    assert loaded.duplicate_rows_collapsed == 1

    write_ticks(
        path,
        [
            (1787702400000, 100.0, 100.2),
            (1787702400000, 100.1, 100.3),
        ],
    )
    with pytest.raises(ValueError, match="Conflicting quotes"):
        load_tick_day(path, "xau_prospective_tick_v1")


def test_tick_loader_rejects_nonmonotonic_and_wrong_day_rows(tmp_path: Path) -> None:
    path = tmp_path / "feed_ticks_20260826.csv"
    write_ticks(
        path,
        [(1787702401000, 100.0, 100.2), (1787702400000, 100.1, 100.3)],
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        load_tick_day(path, "xau_prospective_tick_v1")

    write_ticks(path, [(1787616000000, 100.0, 100.2)])
    with pytest.raises(ValueError, match="wrong UTC file day"):
        load_tick_day(path, "xau_prospective_tick_v1")


def test_empty_market_closed_day_and_completed_day_selection(tmp_path: Path) -> None:
    empty = tmp_path / "feed_ticks_20260822.csv"
    empty.write_text(HEADER, encoding="utf-8")
    loaded = load_tick_day(empty, "xau_prospective_tick_v1")
    assert len(loaded.times) == 0
    assert all(len(values) == 0 for values in five_second_cycles(loaded, 5).values())

    current = tmp_path / "feed_ticks_20260826.csv"
    current.write_text(HEADER, encoding="utf-8")
    assert completed_tick_paths(
        tmp_path,
        "feed_ticks_*.csv",
        now=datetime(2026, 8, 26, 12, tzinfo=UTC),
    ) == [empty]


def test_resolution_uses_executable_side_and_first_target_hit() -> None:
    item = fact()
    state = initial_resolution(item)
    ticks = day(
        [
            (1787702400000, 100.0, 100.2),
            (1787702401000, 120.2, 120.4),
        ]
    )
    resolved = advance_resolution(
        state,
        item,
        ticks,
        economics=ECONOMICS,
        maximum_horizon_gap_minutes=60,
    )
    assert resolved["status"] == "EXECUTED"
    assert resolved["entry_price"] == pytest.approx(100.2)
    assert resolved["exit_price"] == pytest.approx(120.2)
    assert resolved["exit_reason"] == "TARGET"
    assert resolved["pnl_usd"] == pytest.approx(19.7)


def test_resolution_requires_target_or_horizon() -> None:
    item = fact(target_r=None, hold_hours=None)
    with pytest.raises(ValueError, match="neither target nor horizon"):
        advance_resolution(
            initial_resolution(item),
            item,
            day([(1787702400000, 100.0, 100.2)]),
            economics=ECONOMICS,
            maximum_horizon_gap_minutes=60,
        )


def score_record(
    *, observed: str = "2026-08-26T00:00:10Z", feature_bar: str = "2026-08-25T23:55:00Z"
) -> dict:
    return {
        "event_type": "SCORE_DECISION",
        "observed_at_utc": observed,
        "payload": {
            "prospective_contract_sha256": "contract",
            "candidate_id": "candidate-1",
            "entry_time_utc": "2026-08-26T00:00:00Z",
            "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
            "candidate_direction": "LONG",
            "causal_rank": 0.05,
            "feature_bar_time_utc": feature_bar,
            "causal_policy_features_complete": True,
            "atr_ratio": 1.3,
            "dist_hi_24h": 0.5,
            "ret_4h": 0.2,
            "ret_24h": 0.5,
        },
    }


def test_score_evidence_enforces_latency_and_feature_causality() -> None:
    ranks, features, timing, audit = load_causal_scores(
        [score_record()],
        expected_contract_sha256="contract",
        maximum_delay_seconds=120,
        maximum_feature_age_minutes=10,
    )
    assert ranks == {"candidate-1": 0.05}
    assert features["candidate-1"]["atr_ratio"] == 1.3
    assert timing["candidate-1"]["causal_policy_features_complete"] is True
    assert audit["late_score_rows"] == 0

    ranks, _, _, audit = load_causal_scores(
        [score_record(observed="2026-08-26T00:02:01Z")],
        expected_contract_sha256="contract",
        maximum_delay_seconds=120,
        maximum_feature_age_minutes=10,
    )
    assert ranks == {}
    assert audit["late_score_rows"] == 1

    with pytest.raises(ValueError, match="Post-entry feature bar"):
        load_causal_scores(
            [score_record(feature_bar="2026-08-26T00:00:01Z")],
            expected_contract_sha256="contract",
            maximum_delay_seconds=120,
            maximum_feature_age_minutes=10,
        )


def test_warm_start_seeds_source_history_without_cross_source_leakage() -> None:
    class Base:
        def __init__(self) -> None:
            self.veto_policy = {"lookback_closed_trades": 2}
            self.source_closed = defaultdict(lambda: deque(maxlen=2))
            self.source_closed_count = defaultdict(int)
            self.source_consecutive_losses = defaultdict(int)

    warm = {
        "retained_history_counts_by_source": {"A": 52},
        "rows": [
            {
                "source_id": "A",
                "candidate_id": "1",
                "closed_at_utc": "2026-08-01T00:00:00Z",
                "pnl_usd": 2.0,
            },
            {
                "source_id": "A",
                "candidate_id": "2",
                "closed_at_utc": "2026-08-02T00:00:00Z",
                "pnl_usd": -1.0,
            },
            {
                "source_id": "A",
                "candidate_id": "3",
                "closed_at_utc": "2026-08-03T00:00:00Z",
                "pnl_usd": -2.0,
            },
        ],
    }
    seeded = warm_started_challenger_class(Base, warm)()
    assert list(seeded.source_closed["A"]) == [-1.0, -2.0]
    assert seeded.source_closed_count["A"] == 52
    assert seeded.source_consecutive_losses["A"] == 2
