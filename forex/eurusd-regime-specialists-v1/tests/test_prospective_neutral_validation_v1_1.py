from __future__ import annotations

from pathlib import Path

import pandas as pd

from eurusd_regime_specialists import prospective_neutral_validation_v1_1 as module


def _closed(entries: list[tuple[str, str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "status": ["CLOSED"] * len(entries),
            "signal_id": [item[0] for item in entries],
            "entry_time_utc": pd.to_datetime(
                [item[1] for item in entries], utc=True
            ),
            "side": [item[2] for item in entries],
        }
    )


def _oracle(entries: list[tuple[str, str]]) -> pd.DataFrame:
    times = pd.to_datetime([item[0] for item in entries], utc=True)
    return pd.DataFrame(
        {
            "oracle_date": times.strftime("%Y-%m-%d"),
            "entry_time_utc": times,
            "side": [item[1] for item in entries],
            "regime": ["NEUTRAL"] * len(entries),
            "oracle_trade_number": list(range(1, len(entries) + 1)),
        }
    )


def test_temporal_matching_is_optimal_and_one_to_one() -> None:
    closed = _closed(
        [
            ("a", "2026-08-03T00:04:00Z", "LONG"),
            ("b", "2026-08-03T00:00:00Z", "LONG"),
        ]
    )
    oracle = _oracle(
        [
            ("2026-08-03T00:05:00Z", "LONG"),
            ("2026-08-03T00:10:00Z", "LONG"),
        ]
    )
    result = module.temporal_oracle_metrics(
        closed,
        oracle,
        {"2026-08-03"},
        windows_minutes=[6],
        grid_minutes=5,
    )
    metric = result["windows"]["within_6_minutes"]
    assert metric["one_to_one_matches"] == 2
    assert metric["precision"] == 1.0
    assert len({row["oracle_row_id"] for row in metric["matches"]}) == 2


def test_uniform_time_and_side_null_uses_exact_m5_grid_coverage() -> None:
    closed = _closed(
        [("a", "2026-08-03T12:00:00Z", "LONG")]
    )
    oracle = _oracle(
        [("2026-08-03T12:00:00Z", "LONG")]
    )
    result = module.temporal_oracle_metrics(
        closed,
        oracle,
        {"2026-08-03"},
        windows_minutes=[5],
        grid_minutes=5,
    )
    metric = result["windows"]["within_5_minutes"]
    assert metric["one_to_one_matches"] == 1
    assert metric["uniform_time_and_side_expected_precision"] == 3 / 576
    assert (
        metric["uniform_time_and_side_poisson_binomial_tail_p_value"]
        == 3 / 576
    )


def test_missing_date_or_two_trades_on_date_invalidates_exact_null() -> None:
    closed = _closed(
        [
            ("a", "2026-08-03T12:00:00Z", "LONG"),
            ("b", "2026-08-03T13:00:00Z", "SHORT"),
        ]
    )
    result = module.temporal_oracle_metrics(
        closed,
        _oracle([("2026-08-03T12:00:00Z", "LONG")]),
        set(),
        windows_minutes=[60],
        grid_minutes=5,
    )
    assert result["all_closed_trade_oracle_dates_available"] is False
    assert result["one_strategy_trade_per_utc_date"] is False
    metric = result["windows"]["within_60_minutes"]
    assert metric["exact_null_valid"] is False
    assert metric["uniform_time_and_side_poisson_binomial_tail_p_value"] is None


def test_wrapper_blocks_same_day_only_pass_without_temporal_imitation(
    monkeypatch,
) -> None:
    prior_result = {
        "schema_version": "old",
        "status": "INDEPENDENT_RESEARCH_REVIEW_REQUIRED",
        "gate_results": {"prior_gate": True},
        "all_gates_passed": True,
        "research_review_allowed": True,
        "controlled_demo_ready": False,
    }
    monkeypatch.setattr(
        module.prior,
        "evaluate_validation",
        lambda *args, **kwargs: prior_result.copy(),
    )
    closed = _closed(
        [("a", "2026-08-03T12:00:00Z", "LONG")]
    )
    oracle = _oracle(
        [("2026-08-03T00:00:00Z", "LONG")]
    )
    result = module.evaluate_validation(
        closed,
        {},
        oracle,
        {"2026-08-03"},
        evaluated_at_utc="2027-08-03T12:00:00Z",
    )
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"
    assert result["oracle_imitation_claim_allowed"] is False
    assert result["research_review_allowed"] is False


def test_lock_verifies_after_preregistration() -> None:
    checked = module.verify_lock()
    assert Path(module.CONFIG_PATH).relative_to(module.PACKAGE_ROOT).as_posix() in checked
