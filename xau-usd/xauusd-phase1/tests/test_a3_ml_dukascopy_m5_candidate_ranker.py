from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_m5_candidate_ranker import (  # noqa: E402
    _economic_stats,
    _feature_value,
    _fraction_cutoff,
    _portfolio_select,
    _split_rows,
    _validate_contract,
)


def _contract() -> dict:
    return json.loads(
        (ROOT / "config" / "ml" / "a3_ml_dukascopy_m5_candidate_ranker.json").read_text(
            encoding="utf-8"
        )
    )


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _row(candidate_id: str, decision: datetime, **overrides: str) -> dict[str, str]:
    row = {
        "candidate_id": candidate_id,
        "family_id": "breakout_h1_rr1p5",
        "direction": "LONG",
        "decision_time_utc": _iso(decision),
        "entry_time_utc": _iso(decision + timedelta(seconds=1)),
        "exit_time_utc": _iso(decision + timedelta(minutes=30)),
        "ema_fast_slope_atr": "0.2",
        "ema_fast": "100.0",
        "ema_slow": "99.0",
        "atr": "2.0",
        "signal_close": "101.0",
        "body_fraction": "0.6",
        "close_location": "0.8",
        "touch_distance_atr": "0.2",
        "stop_distance": "4.0",
        "stop_distance_atr": "2.0",
        "signal_tick_count": "100",
        "entry_spread": "0.2",
        "label_profitable_after_stress": "1",
        "stress_net_pnl_usd": "2.0",
        "stress_net_r": "0.5",
    }
    row.update(overrides)
    return row


def test_contract_rejects_reserved_outcome_authorization() -> None:
    contract = _contract()
    _validate_contract(contract)
    changed = copy.deepcopy(contract)
    changed["authorization"]["reserved_validation_outcomes_authorized"] = True
    with pytest.raises(ValueError, match="requires reserved_validation_outcomes_authorized=false"):
        _validate_contract(changed)


def test_feature_values_do_not_depend_on_pnl_or_exit() -> None:
    contract = _contract()
    row = _row("a", datetime(2019, 1, 2, tzinfo=UTC))
    changed = dict(row)
    changed["stress_net_pnl_usd"] = "-99999"
    changed["stress_net_r"] = "-999"
    changed["exit_time_utc"] = "2030-01-01T00:00:00Z"
    for feature in contract["features"]:
        assert _feature_value(row, feature, contract) == pytest.approx(
            _feature_value(changed, feature, contract)
        )


def test_time_splits_are_half_open_and_chronological() -> None:
    rows = [
        _row("a", datetime(2019, 12, 31, 23, 55, tzinfo=UTC)),
        _row("b", datetime(2020, 1, 1, tzinfo=UTC)),
        _row("c", datetime(2021, 1, 1, tzinfo=UTC)),
    ]
    split = _split_rows(rows, _contract()["windows"])
    assert [row["candidate_id"] for row in split["train"]] == ["a"]
    assert [row["candidate_id"] for row in split["validation"]] == ["b"]
    assert [row["candidate_id"] for row in split["test"]] == ["c"]


def test_fraction_cutoff_is_deterministic() -> None:
    assert _fraction_cutoff([0.1, 0.4, 0.3, 0.2], 0.5) == pytest.approx(0.3)


def test_portfolio_groups_same_event_and_enforces_overlap() -> None:
    contract = _contract()
    start = datetime(2020, 1, 2, 8, 0, tzinfo=UTC)
    rows = [
        _row("a", start, exit_time_utc=_iso(start + timedelta(hours=2))),
        _row(
            "b",
            start,
            family_id="band_fade_any_rr1p5",
            exit_time_utc=_iso(start + timedelta(hours=1)),
        ),
        _row("c", start + timedelta(minutes=10), exit_time_utc=_iso(start + timedelta(hours=3))),
        _row("d", start + timedelta(minutes=20), exit_time_utc=_iso(start + timedelta(hours=4))),
    ]
    selected = _portfolio_select(rows, [0.6, 0.9, 0.8, 0.7], 0.5, contract["portfolio"])
    assert [row["candidate_id"] for row in selected] == ["b", "c"]


def test_economic_stats_count_missing_direction_as_zero_share() -> None:
    start = datetime(2020, 1, 2, tzinfo=UTC)
    rows = [_row(str(index), start + timedelta(days=index)) for index in range(12)]
    stats = _economic_stats(rows, source_days=12)
    assert stats["minimum_direction_share"] == 0.0
    assert stats["top10_winners_removed_net_usd"] == pytest.approx(4.0)


def test_family_one_hot_is_exact() -> None:
    contract = _contract()
    row = _row("a", datetime(2019, 1, 2, tzinfo=UTC))
    assert _feature_value(row, "family_breakout", contract) == 1.0
    assert _feature_value(row, "family_band_fade", contract) == 0.0
