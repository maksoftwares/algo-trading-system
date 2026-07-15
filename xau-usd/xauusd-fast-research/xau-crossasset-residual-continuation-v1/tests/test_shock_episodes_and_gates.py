from __future__ import annotations

import pandas as pd

from xau_continuation import research


def _model(zs: list[float], start: int = 1_530_403_200_000) -> pd.DataFrame:
    rows = []
    for index, z in enumerate(zs):
        rows.append({"timestamp_ms": start + index * 300_000, "residual_z": z, "r_xau": .001, "predicted_r_xau": .0001, "residual": .0009, "beta_xag": .2, "beta_eurusd": -.1, "beta_usdjpy": .1, "condition_number": 10.0})
    return pd.DataFrame(rows)


def test_positive_crossing_creates_long() -> None:
    candidates = research.construct_shock_episodes(_model([2.4, 2.5]))
    assert len(candidates) == 1
    assert (candidates[0]["direction"], candidates[0]["specialist_id"]) == ("LONG", research.LONG_ID)


def test_negative_crossing_creates_short() -> None:
    candidates = research.construct_shock_episodes(_model([-2.4, -2.5]))
    assert len(candidates) == 1
    assert (candidates[0]["direction"], candidates[0]["specialist_id"]) == ("SHORT", research.SHORT_ID)


def test_no_direction_inversion() -> None:
    candidates = research.construct_shock_episodes(_model([0.0, 2.6, 0.0, -2.6]))
    mapping = {row["specialist_id"]: row["direction"] for row in candidates}
    assert mapping == {research.LONG_ID: "LONG", research.SHORT_ID: "SHORT"}


def test_positive_episode_does_not_repeat_above_threshold() -> None:
    candidates = research.construct_shock_episodes(_model([2.4, 2.6, 2.4, 2.7]))
    assert len([row for row in candidates if row["direction"] == "LONG"]) == 1


def test_negative_episode_does_not_repeat_below_threshold() -> None:
    candidates = research.construct_shock_episodes(_model([-2.4, -2.6, -2.4, -2.7]))
    assert len([row for row in candidates if row["direction"] == "SHORT"]) == 1


def test_positive_episode_ends_at_zero_cross() -> None:
    candidates = research.construct_shock_episodes(_model([2.4, 2.6, -.1, 2.6]))
    assert len([row for row in candidates if row["direction"] == "LONG"]) == 2


def test_negative_episode_ends_at_zero_cross() -> None:
    candidates = research.construct_shock_episodes(_model([-2.4, -2.6, .1, -2.6]))
    assert len([row for row in candidates if row["direction"] == "SHORT"]) == 2


def test_episode_expires_after_six_hours() -> None:
    frame = _model([2.4, 2.6])
    later = frame.iloc[-1].copy()
    later.timestamp_ms = int(frame.iloc[-1].timestamp_ms) + 6 * 3_600_000
    later.residual_z = 2.6
    candidates = research.construct_shock_episodes(pd.concat([frame, later.to_frame().T], ignore_index=True))
    assert len(candidates) == 1  # a fresh crossing, not merely an above-threshold observation, is required


def test_episode_id_is_directional_and_deterministic() -> None:
    first = research.construct_shock_episodes(_model([0.0, 2.6]))
    second = research.construct_shock_episodes(_model([0.0, 2.6]))
    assert first[0]["shock_episode_id"] == second[0]["shock_episode_id"]
    assert first[0]["shock_episode_id"].startswith("LONG-")


def test_candidate_completion_is_next_bar_boundary() -> None:
    candidate = research.construct_shock_episodes(_model([0.0, 2.6]))[0]
    assert candidate["candidate_completed_ms"] - candidate["candidate_bar_ms"] == 300_000


def _metrics(trades: int, pf: float, expectancy: float, net: float, dd: float, active: int, annualized: float) -> dict:
    return {"trades": trades, "profit_factor": pf, "expectancy_R": expectancy, "net_R": net, "maximum_closed_drawdown_R": dd, "top_ten_winners_fraction": .2, "top_three_winning_days_fraction": .1, "active_months": active, "annualized_trades": annualized}


def test_directional_stage_a_passes_only_all_gates() -> None:
    baseline = _metrics(120, 1.2, .07, 10, 12, 24, 40)
    stress = _metrics(120, 1.08, .02, 2, 13, 24, 40)
    broker = _metrics(120, 1.03, .001, 1, 13, 24, 40)
    passed, failures = research.stage_a_gate(baseline, stress, broker)
    assert passed and failures == []


def test_directional_frequency_failure_is_reported() -> None:
    baseline = _metrics(119, 1.3, .1, 10, 5, 24, 39.67)
    passed, failures = research.stage_a_gate(baseline, _metrics(119, 1.2, .1, 8, 5, 24, 39.67), _metrics(119, 1.1, .01, 2, 5, 24, 39.67))
    assert not passed
    assert {"trades", "annualized_trades"}.issubset(failures)


def test_directional_profitability_failures_are_reported() -> None:
    baseline = _metrics(150, 1.19, .069, -1, 5, 30, 50)
    stress = _metrics(150, 1.07, .019, -1, 5, 30, 50)
    broker = _metrics(150, 1.02, 0, 0, 5, 30, 50)
    _, failures = research.stage_a_gate(baseline, stress, broker)
    assert "baseline_profit_factor" in failures
    assert "stress_expectancy_R" in failures
    assert "broker_expectancy_R" in failures


def test_drawdown_gate_is_direction_specific() -> None:
    baseline = _metrics(150, 1.3, .1, 10, 12.01, 30, 50)
    passed, failures = research.stage_a_gate(baseline, _metrics(150, 1.2, .05, 5, 0, 30, 50), _metrics(150, 1.1, .01, 1, 0, 30, 50))
    assert not passed and "maximum_closed_drawdown_R" in failures


def test_winner_concentration_gates_are_enforced() -> None:
    baseline = _metrics(150, 1.3, .1, 10, 5, 30, 50)
    baseline["top_ten_winners_fraction"] = .351
    baseline["top_three_winning_days_fraction"] = .251
    _, failures = research.stage_a_gate(baseline, _metrics(150, 1.2, .05, 5, 0, 30, 50), _metrics(150, 1.1, .01, 1, 0, 30, 50))
    assert {"top_ten_winners_fraction", "top_three_winning_days_fraction"}.issubset(failures)


def test_combined_gate_uses_higher_frequency_thresholds() -> None:
    baseline = _metrics(239, 1.3, .1, 10, 5, 29, 79.67)
    _, failures = research.stage_a_gate(baseline, _metrics(239, 1.2, .05, 5, 0, 29, 79.67), _metrics(239, 1.1, .01, 1, 0, 29, 79.67), combined=True)
    assert {"trades", "annualized_trades", "active_months"}.issubset(failures)


def test_combined_success_cannot_change_direction_ids() -> None:
    assert research.LONG_ID not in research.COMBINED_ID
    assert research.SHORT_ID not in research.COMBINED_ID
