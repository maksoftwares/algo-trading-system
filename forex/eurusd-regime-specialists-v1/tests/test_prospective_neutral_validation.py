from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.prospective_neutral_validation import (
    evaluate_validation,
    load_config,
    poisson_binomial_tail_probability,
    trade_path_marks,
)

PATH_HASH = "f" * 64


def _path(
    entry: pd.Timestamp,
    *,
    bid_high: float = 1.0017,
    bid_low: float = 1.0000,
    ask_high: float | None = None,
    ask_low: float | None = None,
) -> dict:
    index = pd.date_range(entry, periods=144, freq="5min")
    ask_high = bid_high + 0.00007 if ask_high is None else ask_high
    ask_low = bid_low + 0.00007 if ask_low is None else ask_low
    frame = pd.DataFrame(
        {
            "timestamp_utc": index,
            "bid_open": 1.00000,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": 1.00000,
            "ask_open": 1.00007,
            "ask_high": ask_high,
            "ask_low": ask_low,
            "ask_close": 1.00007,
        }
    )
    return {
        "frame": frame,
        "entry_time_utc": entry,
        "deadline_utc": entry + pd.Timedelta(hours=12),
        "path_evidence_sha256": PATH_HASH,
    }


def _trade(
    number: int,
    entry: pd.Timestamp,
    *,
    side: str,
    outcome_r: float,
    reason: str,
) -> dict:
    risk_pips = 10.0
    exit_time = (
        entry + pd.Timedelta(hours=12)
        if reason == "TIME_12H"
        else entry
    )
    return {
        "signal_id": f"{number:064x}",
        "status": "CLOSED",
        "entry_time_utc": entry,
        "exit_time_utc": exit_time,
        "side": side,
        "entry_price": 1.00008 if side == "LONG" else 1.00000,
        "risk_pips": risk_pips,
        "risk_distance": risk_pips * 0.0001,
        "exit_reason": reason,
        "r": outcome_r,
        "extra_half_pip_stress_r": outcome_r - 0.05,
        "fixed_0p01_lot_usd": outcome_r,
        "path_evidence_sha256": PATH_HASH,
    }


def _empty_routed() -> pd.DataFrame:
    return pd.DataFrame(columns=["status"])


def _qualifying_sample() -> tuple[pd.DataFrame, dict, pd.DataFrame, set[str]]:
    # Eight profitable active months and four losing months. The sample has
    # exactly 15 wins and 15 losses, balanced sides, PF 1.50, and payoff 1.50.
    monthly_outcomes = [
        [1.5, 1.5, -1.0],
        [1.5, 1.5, -1.0],
        [1.5, 1.5, -1.0],
        [1.5, 1.5, -1.0],
        [1.5, 1.5, -1.0],
        [1.5, 1.5, -1.0],
        [1.5, 1.5, -1.0],
        [1.5],
        [-1.0, -1.0],
        [-1.0, -1.0],
        [-1.0, -1.0],
        [-1.0, -1.0],
    ]
    trades: list[dict] = []
    paths: dict[str, dict] = {}
    labels: list[dict] = []
    completed: set[str] = set()
    number = 1
    for month_offset, outcomes in enumerate(monthly_outcomes):
        month = pd.Timestamp("2026-08-01T00:00:00Z") + pd.DateOffset(
            months=month_offset
        )
        for day_offset, outcome in enumerate(outcomes, start=1):
            entry = month + pd.Timedelta(days=day_offset, hours=12)
            side = "LONG" if number % 2 else "SHORT"
            reason = "TARGET" if outcome > 0 else "STOP"
            trade = _trade(
                number,
                entry,
                side=side,
                outcome_r=outcome,
                reason=reason,
            )
            trades.append(trade)
            paths[trade["signal_id"]] = _path(entry)
            day = entry.strftime("%Y-%m-%d")
            completed.add(day)
            labels.append(
                {
                    "oracle_date": day,
                    "side": side,
                    "regime": "NEUTRAL",
                    "entry_time_utc": entry,
                }
            )
            number += 1
    return pd.DataFrame(trades), paths, pd.DataFrame(labels), completed


def test_validation_waits_before_prospective_start_without_loading_history() -> None:
    result = evaluate_validation(
        _empty_routed(),
        {},
        pd.DataFrame(),
        set(),
        evaluated_at_utc="2026-07-28T23:59:59Z",
    )
    assert result["status"] == "WAITING_FOR_PROSPECTIVE_START"
    assert result["historical_pnl_loaded"] is False
    assert result["network_request_made"] is False
    assert result["broker_action_allowed"] is False


def test_frequency_is_reported_but_never_an_admission_gate() -> None:
    cfg = load_config()
    assert cfg["frequency_policy"]["minimum_trades_per_day"] is None
    assert cfg["frequency_policy"][
        "frequency_is_reported_but_not_an_admission_gate"
    ]
    result = evaluate_validation(
        _empty_routed(),
        {},
        pd.DataFrame(),
        set(),
        evaluated_at_utc="2026-08-01T00:00:00Z",
    )
    assert result["frequency"]["admission_gate"] is False
    assert all("frequency" not in key for key in result["gate_results"])


def test_stop_exit_bar_does_not_count_post_fill_extreme() -> None:
    entry = pd.Timestamp("2026-08-07T12:50:00Z")
    trade = _trade(
        1,
        entry,
        side="LONG",
        outcome_r=-1.0,
        reason="STOP",
    )
    path = _path(entry, bid_low=0.9900)
    marks = trade_path_marks(
        trade,
        path,
        minimum_spread_pips=0.7,
        adverse_slippage_pips_per_side=0.1,
    )
    assert marks["ordered_marks_r"] == pytest.approx([0.0, -1.0])
    assert marks["maximum_adverse_excursion_r"] == pytest.approx(-1.0)


def test_path_level_floating_drawdown_detects_closed_equity_blind_spot() -> None:
    entry = pd.Timestamp("2026-08-07T12:50:00Z")
    trade = _trade(
        1,
        entry,
        side="LONG",
        outcome_r=0.0,
        reason="TIME_12H",
    )
    routed = pd.DataFrame([trade])
    paths = {
        trade["signal_id"]: _path(
            entry,
            bid_high=1.0030,
            bid_low=0.9950,
        )
    }
    result = evaluate_validation(
        routed,
        paths,
        pd.DataFrame(),
        set(),
        evaluated_at_utc="2026-08-08T01:00:00Z",
    )
    assert result["overall"]["max_drawdown_r"] == 0.0
    assert (
        result["floating_equity"]["base_maximum_floating_drawdown_usd"]
        > 7.0
    )
    assert result["floating_equity"]["trade_excursions"][0][
        "maximum_adverse_excursion_r"
    ] < -5.0


def test_poisson_binomial_oracle_null_is_exact_and_one_sided() -> None:
    assert poisson_binomial_tail_probability([0.5, 0.5], 2) == pytest.approx(
        0.25
    )
    assert poisson_binomial_tail_probability([1.0, 0.5, 0.0], 2) == (
        pytest.approx(0.5)
    )
    assert poisson_binomial_tail_probability([0.5, 0.5], 0) == 1.0


def test_profitable_sparse_sample_passes_independent_validation_only() -> None:
    routed, paths, oracle, completed = _qualifying_sample()
    result = evaluate_validation(
        routed,
        paths,
        oracle,
        completed,
        evaluated_at_utc="2027-07-29T12:00:00Z",
    )
    assert result["overall"]["trades"] == 30
    assert result["overall"]["win_rate"] == pytest.approx(0.5)
    assert result["overall"]["realized_payoff_ratio"] == pytest.approx(1.5)
    assert result["overall"]["profit_factor"] == pytest.approx(1.5)
    assert result["extra_half_pip_round_trip"]["profit_factor"] > 1.15
    assert result["frequency"]["trades_per_elapsed_weekday"] < 1.0
    assert result["oracle_approximation"][
        "precision_lift_over_random_side"
    ] == pytest.approx(0.5)
    assert result["oracle_approximation"][
        "random_side_poisson_binomial_tail_p_value"
    ] < 0.1
    assert all(result["gate_results"].values())
    assert result["status"] == "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
    assert result["research_review_allowed"] is True
    assert result["controlled_demo_ready"] is False
    assert result["broker_action_allowed"] is False


def test_missing_path_or_oracle_date_fails_closed_after_sample_matures() -> None:
    routed, paths, oracle, completed = _qualifying_sample()
    missing_signal = str(routed.iloc[0]["signal_id"])
    paths.pop(missing_signal)
    completed.remove(
        pd.Timestamp(routed.iloc[1]["entry_time_utc"]).strftime("%Y-%m-%d")
    )
    result = evaluate_validation(
        routed,
        paths,
        oracle,
        completed,
        evaluated_at_utc="2027-07-29T12:00:00Z",
    )
    assert result["gate_results"]["all_closed_trade_paths"] is False
    assert result["gate_results"]["all_closed_trade_oracle_dates"] is False
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"
    assert result["research_review_allowed"] is False
