from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_session_campaign import (  # noqa: E402
    HOUR_MS,
    _active_days_by_split,
    _select_train_profile,
    _validate_contract,
    generate_session_candidates,
)


def _contract() -> dict:
    return json.loads(
        (ROOT / "config" / "ml" / "a3_ml_dukascopy_session_campaign.json").read_text(
            encoding="utf-8"
        )
    )


def _timestamp(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _bars(hours: int = 80) -> list[dict]:
    start = datetime(2020, 1, 6, tzinfo=UTC)
    output = []
    for index in range(hours):
        middle = 1500.0 + 0.01 * index
        output.append(
            {
                "timestamp_ms": _timestamp(start + timedelta(hours=index)),
                "bid_open": middle - 0.2,
                "bid_high": middle + 0.5,
                "bid_low": middle - 0.5,
                "bid_close": middle + 0.2,
                "tick_count": 100,
            }
        )
    return output


def _set_breakout(rows: list[dict], index: int) -> None:
    prior_high = max(row["bid_high"] for row in rows[index - 8 : index])
    rows[index].update(
        {
            "bid_open": prior_high - 0.3,
            "bid_high": prior_high + 0.4,
            "bid_low": prior_high - 0.4,
            "bid_close": prior_high + 0.3,
        }
    )


def _set_downside_sweep(rows: list[dict], index: int) -> None:
    prior_low = min(row["bid_low"] for row in rows[index - 8 : index])
    rows[index].update(
        {
            "bid_open": prior_low - 0.2,
            "bid_high": prior_low + 0.5,
            "bid_low": prior_low - 0.5,
            "bid_close": prior_low + 0.3,
        }
    )


def test_contract_locks_exact_bounded_profile_set() -> None:
    contract = _contract()
    _validate_contract(contract)
    assert len(contract["profiles"]) == 8
    assert {row["mechanism"] for row in contract["profiles"]} == {
        "BREAKOUT",
        "SWEEP_REVERSAL",
    }
    assert {row["lookback_h1_bars"] for row in contract["profiles"]} == {4, 8}
    assert {row["reward_r"] for row in contract["profiles"]} == {1.5, 2.0}


def test_contract_rejects_broker_authorization() -> None:
    contract = _contract()
    contract["authorization"]["broker_action_authorized"] = True
    with pytest.raises(ValueError, match="forbidden authorization"):
        _validate_contract(contract)


def test_generator_detects_causal_trend_aligned_session_breakout() -> None:
    rows = _bars()
    _set_breakout(rows, 30)  # Tuesday 06:00 UTC.
    candidates = generate_session_candidates(rows, _contract())
    decision = rows[30]["timestamp_ms"] + HOUR_MS
    selected = [row for row in candidates if row.decision_timestamp_ms == decision]
    assert selected
    assert {row.direction for row in selected} == {"LONG"}
    assert {row.family_id for row in selected} == {
        "session_breakout_lb4_r15",
        "session_breakout_lb8_r15",
        "session_breakout_lb4_r20",
        "session_breakout_lb8_r20",
    }
    assert all(row.stop_distance_atr == pytest.approx(1.0) for row in selected)


def test_generator_detects_session_liquidity_sweep_reversal() -> None:
    rows = _bars()
    _set_downside_sweep(rows, 30)
    candidates = generate_session_candidates(rows, _contract())
    decision = rows[30]["timestamp_ms"] + HOUR_MS
    selected = [row for row in candidates if row.decision_timestamp_ms == decision]
    assert selected
    assert {row.direction for row in selected} == {"LONG"}
    assert {row.family_id for row in selected} == {
        "session_sweep_lb4_r15",
        "session_sweep_lb8_r15",
        "session_sweep_lb4_r20",
        "session_sweep_lb8_r20",
    }
    assert all(0.6 <= row.stop_distance_atr <= 1.5 for row in selected)


def test_each_profile_is_capped_at_one_candidate_per_session_day() -> None:
    rows = _bars()
    for index in (30, 31, 36, 37):
        _set_breakout(rows, index)
    candidates = generate_session_candidates(rows, _contract())
    counts: dict[tuple[str, str, str], int] = {}
    for row in candidates:
        start = datetime.fromisoformat(row.signal_bar_start_utc.replace("Z", "+00:00"))
        session = "LONDON" if start.hour in {6, 7} else "NEW_YORK"
        key = (row.family_id, start.date().isoformat(), session)
        counts[key] = counts.get(key, 0) + 1
    assert counts
    assert max(counts.values()) == 1


def test_future_bars_cannot_change_prior_candidate_identity() -> None:
    rows = _bars()
    _set_breakout(rows, 30)
    baseline = generate_session_candidates(rows, _contract())
    assert baseline
    changed = copy.deepcopy(rows)
    future_start = changed[-1]["timestamp_ms"] + HOUR_MS
    changed.append(
        {
            "timestamp_ms": future_start,
            "bid_open": 9998.0,
            "bid_high": 10001.0,
            "bid_low": 9997.0,
            "bid_close": 10000.0,
            "tick_count": 100,
        }
    )
    rerun = generate_session_candidates(changed, _contract())
    assert [row.candidate_id for row in baseline] == [
        row.candidate_id
        for row in rerun
        if row.decision_timestamp_ms <= rows[-1]["timestamp_ms"] + HOUR_MS
    ]


def test_active_day_denominator_counts_dates_not_session_bars() -> None:
    rows = _bars(48)
    counts = _active_days_by_split(rows, _contract())
    assert counts["train"] == 2
    assert counts["validation"] == 0
    assert counts["test"] == 0


def _selection_contract() -> dict:
    return {
        "sessions": {"LONDON": [6, 7], "NEW_YORK": [12, 13]},
        "profiles": [
            {"family_id": "family_a", "mechanism": "A", "lookback_h1_bars": 4, "reward_r": 1.5},
            {"family_id": "family_b", "mechanism": "B", "lookback_h1_bars": 4, "reward_r": 1.5},
        ],
        "bootstrap": {"calendar_month_samples": 100, "seed": 7},
        "train_selection_gates": {
            "minimum_resolved_rows": 12,
            "minimum_rows_each_direction": 2,
            "minimum_rows_each_session": 2,
            "minimum_trades_per_active_day": 0.5,
            "minimum_stress_profit_factor": 1.0,
            "minimum_average_stress_r": 0.0,
            "maximum_closed_drawdown_r": 10.0,
            "minimum_positive_exit_month_share": 0.5,
            "minimum_bootstrap_average_r_p025": -1.0,
        },
    }


def _selection_rows() -> tuple[list[SimpleNamespace], dict[str, SimpleNamespace]]:
    labels = []
    candidates = {}
    for family_id, loss in (("family_a", -0.5), ("family_b", -0.2)):
        for index in range(24):
            month = index // 2 + 1
            day = 1 + index % 2
            session_hour = 6 if index % 2 == 0 else 12
            entry = datetime(2020, month, day, session_hour + 1, tzinfo=UTC)
            candidate_id = f"{family_id}_{index}"
            value = 1.0 if index % 2 == 0 else loss
            labels.append(
                SimpleNamespace(
                    candidate_id=candidate_id,
                    family_id=family_id,
                    split="train",
                    status="RESOLVED",
                    direction="LONG" if index % 2 == 0 else "SHORT",
                    entry_time_utc=entry.isoformat().replace("+00:00", "Z"),
                    exit_time_utc=(entry + timedelta(hours=1)).isoformat().replace(
                        "+00:00", "Z"
                    ),
                    stress_net_pnl_usd=value,
                    stress_net_r=value,
                )
            )
            candidates[candidate_id] = SimpleNamespace(
                candidate_id=candidate_id,
                signal_bar_start_utc=datetime(
                    2020, month, day, session_hour, tzinfo=UTC
                ).isoformat().replace("+00:00", "Z"),
            )
    return labels, candidates


def test_validation_rows_cannot_change_train_only_profile_selection() -> None:
    labels, candidates = _selection_rows()
    contract = _selection_contract()
    selected, evidence = _select_train_profile(
        labels=labels,
        candidates=candidates,
        active_days={"train": 24},
        contract=contract,
    )
    assert selected == "family_b"
    mutated = list(labels)
    mutated.extend(
        SimpleNamespace(
            candidate_id=f"validation_{index}",
            family_id="family_a",
            split="validation",
            status="RESOLVED",
            direction="LONG",
            entry_time_utc="2022-01-01T07:00:00Z",
            exit_time_utc="2022-01-01T08:00:00Z",
            stress_net_pnl_usd=1000.0,
            stress_net_r=1000.0,
        )
        for index in range(20)
    )
    selected_after, evidence_after = _select_train_profile(
        labels=mutated,
        candidates=candidates,
        active_days={"train": 24},
        contract=contract,
    )
    assert selected_after == selected
    assert evidence_after == evidence
