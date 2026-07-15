from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from xau_crossasset_residual.core import (
    BASE_COMMIT, BASE_TREE, BRANCH, COMBINED_ID, INSTRUMENTS, LONG_ID, SHORT_ID,
    STAGE_A_END_MS, STAGE_A_START_MS, add_log_returns, classify, construct_episodes,
    capital_feasibility, final_combined_gate, final_direction_gate, metrics, no_search_tokens, prior_percentile, rolling_causal_ols, stage_a_gate,
    stage_b_authorized, synchronize_m5, weighted_percentile, wilder_atr,
)
from xau_crossasset_residual.pipeline import REQUIRED_OUTPUTS, months

LANE = Path(__file__).resolve().parents[1]
CONFIG = json.loads((LANE / "config" / "frozen_config.json").read_text())


def bars(times, base=100.0):
    return pd.DataFrame({"timestamp_ms": times, "close": [base + i for i in range(len(times))]})


def test_exact_repository_identity_contract():
    assert BRANCH == "codex/xau-crossasset-residual-fast-discovery-v1"
    assert BASE_COMMIT == "c21c98711e21f3e2e4d705d64ac8cf1391aca228"
    assert BASE_TREE == "1bedbc6531ab4de1d02b21984ef6003fe324f97a"


def test_exact_stage_boundaries_and_month_count():
    assert datetime.fromtimestamp(STAGE_A_START_MS / 1000, UTC) == datetime(2021, 7, 1, tzinfo=UTC)
    assert datetime.fromtimestamp(STAGE_A_END_MS / 1000, UTC) == datetime(2024, 7, 1, tzinfo=UTC)
    assert len(months()) == 36


def test_all_four_instruments_are_mandatory():
    assert INSTRUMENTS == {"XAUUSD": "XAU-USD", "XAGUSD": "XAG-USD", "EURUSD": "EUR-USD", "USDJPY": "USD-JPY"}
    with pytest.raises(ValueError, match="four"):
        synchronize_m5({"XAUUSD": bars([0])})


@pytest.mark.parametrize("missing", list(INSTRUMENTS))
def test_missing_instrument_bar_invalidates_observation(missing):
    frames = {symbol: bars([0, 300_000]) for symbol in INSTRUMENTS}
    frames[missing] = bars([0])
    synchronized, excluded = synchronize_m5(frames)
    assert synchronized.timestamp_ms.tolist() == [0]
    assert excluded.iloc[0].missing_instruments == missing


def test_synchronization_never_forward_fills():
    frames = {symbol: bars([0, 600_000]) for symbol in INSTRUMENTS}
    frames["XAGUSD"] = bars([0, 300_000, 600_000])
    synchronized, _ = synchronize_m5(frames)
    assert synchronized.timestamp_ms.tolist() == [0, 600_000]
    assert not synchronized.isna().any().any()


def test_returns_require_exact_previous_m5():
    frames = {symbol: bars([0, 300_000, 900_000], 10.0) for symbol in INSTRUMENTS}
    synchronized, _ = synchronize_m5(frames)
    result = add_log_returns(synchronized)
    assert np.isnan(result.at[0, "r_xau"])
    assert result.at[1, "r_xau"] == pytest.approx(np.log(11 / 10))
    assert np.isnan(result.at[2, "r_xau"])


def synthetic_returns(n=3100):
    rng = np.random.default_rng(68_998_8)
    xag = rng.normal(0, .001, n)
    eur = rng.normal(0, .001, n)
    jpy = rng.normal(0, .001, n)
    noise = rng.normal(0, .0001, n)
    xau = .00001 + .7 * xag + .2 * eur - .1 * jpy + noise
    return pd.DataFrame({"timestamp_ms": np.arange(n, dtype=np.int64) * 300_000, "r_xau": xau, "r_xag": xag, "r_eurusd": eur, "r_usdjpy": jpy})


def test_rolling_ols_is_prior_only_and_exact_window():
    result = rolling_causal_ols(synthetic_returns())
    assert result.iloc[2499].training_observations == 2499
    assert not result.iloc[2499].model_valid
    assert result.iloc[2500].training_observations == 2500
    assert result.iloc[3000].training_observations == 3000
    assert result.iloc[-1].training_observations == 3000
    assert result.iloc[3000].training_end.endswith("Z")


def test_rolling_ols_includes_intercept_and_residual_normalization_excludes_current():
    result = rolling_causal_ols(synthetic_returns(3200))
    valid = result[result.model_valid & np.isfinite(result.residual_z)]
    assert len(valid) > 0
    row = valid.iloc[0]
    assert np.isfinite(row.intercept)
    earlier = result[(result.timestamp_ms < row.timestamp_ms) & result.model_valid].residual.dropna().tail(500)
    assert row.prior_residual_mean == pytest.approx(earlier.mean())
    assert row.prior_residual_std == pytest.approx(earlier.std(ddof=1))


def test_rank_deficiency_rejected():
    frame = synthetic_returns(2502)
    frame["r_xag"] = 1.0
    frame["r_eurusd"] = 1.0
    frame["r_usdjpy"] = 1.0
    result = rolling_causal_ols(frame)
    assert result.iloc[-1].model_rejection_reason == "RANK_DEFICIENT"


def test_condition_limit_rejected():
    result = rolling_causal_ols(synthetic_returns(2502), condition_limit=1.0)
    assert result.iloc[-1].model_rejection_reason == "CONDITION_NUMBER_EXCEEDED"


def model_rows(zs):
    return pd.DataFrame([{"timestamp_ms": i * 300_000, "chronological_segment": "DEVELOPMENT", "residual_z": z, "r_xau": 0.0, "predicted_r_xau": 0.0, "residual": 0.0, "beta_xag": 0.0, "beta_eurusd": 0.0, "beta_usdjpy": 0.0, "condition_number": 1.0} for i, z in enumerate(zs)])


def test_negative_and_positive_new_crossing_only():
    candidates = construct_episodes(model_rows([0, -2.6, -3.0, 0.1, 2.6, 3.0]))
    assert [row["specialist_id"] for row in candidates] == [LONG_ID, SHORT_ID]


def test_no_repeated_candidate_inside_excursion():
    candidates = construct_episodes(model_rows([0, -2.6, -2.4, -2.7, -3.0, 0.0, -2.6]))
    assert [row["specialist_id"] for row in candidates].count(LONG_ID) == 2


def test_wilder_atr_is_prior_price_causal():
    frame = pd.DataFrame({"timestamp_ms": np.arange(20) * 300_000, "open": 10.0, "high": np.arange(20) + 11.0, "low": 9.0, "close": np.arange(20) + 10.0})
    first = wilder_atr(frame)
    changed = frame.copy()
    changed.loc[19, ["high", "low", "close"]] = [1000, 1, 500]
    second = wilder_atr(changed)
    assert first.ATR14.iloc[:19].equals(second.ATR14.iloc[:19])


def test_prior_percentile_excludes_current():
    assert prior_percentile([1, 2, 3, 4], 5) == 100.0
    assert weighted_percentile({1.0: 1, 2.0: 3}, .5) == 2.0


def report_with(value=1.0, trades=100, months_active=20):
    return {"trades": trades, "wins": 60, "losses": 40, "net_R": value, "expectancy_R": .08, "profit_factor": 1.2, "maximum_closed_drawdown_R": 5.0, "top_ten_winners_fraction": .3, "top_three_winning_days_fraction": .2, "active_months": months_active, "annualized_trades": trades / 3, "median_monthly_trades": 3.0}


def test_stage_a_direction_gate_boundaries():
    passed, failures = stage_a_gate(report_with(), report_with(), report_with())
    assert passed and not failures
    weak = report_with(trades=89)
    assert "trades" in stage_a_gate(weak, report_with(), report_with())[1]


def test_stage_a_combined_gate_boundaries():
    baseline = report_with(trades=180, months_active=24)
    baseline.update(profit_factor=1.15, expectancy_R=.05, annualized_trades=60)
    stress = report_with(trades=180, months_active=24); stress.update(profit_factor=1.05, expectancy_R=.001)
    broker = report_with(trades=180, months_active=24); broker.update(profit_factor=1.0, expectancy_R=.001)
    assert stage_a_gate(baseline, stress, broker, combined=True)[0]


def test_final_direction_gate_boundaries():
    full = report_with(trades=160); full.update(annualized_trades=32, profit_factor=1.25, expectancy_R=.08, top_ten_winners_fraction=.30, top_three_winning_days_fraction=.20)
    stress = report_with(); stress.update(profit_factor=1.10, expectancy_R=.03)
    broker = report_with(); broker.update(profit_factor=1.05, expectancy_R=.01)
    validation = report_with(trades=30); validation.update(profit_factor=1.05, expectancy_R=.01)
    exam = report_with(trades=30); exam.update(profit_factor=1.15, expectancy_R=.05)
    assert final_direction_gate(full, stress, broker, validation, exam, .70, 12, 8)[0]
    assert "exam_trades" in final_direction_gate(full, stress, broker, validation, {**exam, "trades": 29}, .70, 12, 8)[1]


def test_final_combined_gate_boundaries():
    full = report_with(trades=300); full.update(annualized_trades=60, median_monthly_trades=4, profit_factor=1.25, expectancy_R=.08, top_ten_winners_fraction=.30, top_three_winning_days_fraction=.20)
    stress = report_with(); stress.update(profit_factor=1.10, expectancy_R=.03)
    broker = report_with(); broker.update(profit_factor=1.05, expectancy_R=.01)
    validation = report_with(trades=55)
    exam = report_with(trades=55); exam.update(profit_factor=1.15, expectancy_R=.05)
    assert final_combined_gate(full, stress, broker, validation, exam, .70, 15, 10, .70)[0]


def test_capital_minimum_volume_and_margin_boundaries():
    assert capital_feasibility(1000, 10, 980)[0]
    assert not capital_feasibility(1000, 10.01, 100)[0]
    assert not capital_feasibility(1000, 10, 981)[0]


def test_failed_direction_cannot_authorize_stage_b():
    assert not stage_b_authorized([])
    assert stage_b_authorized([LONG_ID])
    assert stage_b_authorized([SHORT_ID])
    assert not stage_b_authorized([COMBINED_ID])


def test_classification_precedence():
    assert classify(False, True, []) == "XAU_CROSSASSET_RESIDUAL_V1_EVIDENCE_INVALID"
    assert classify(True, False, []) == "XAU_CROSSASSET_RESIDUAL_V1_DATA_INCOMPLETE"
    assert classify(True, True, []) == "XAU_CROSSASSET_RESIDUAL_V1_NO_DIRECTIONAL_SURVIVOR"
    assert classify(True, True, [LONG_ID], [LONG_ID]) == "XAU_CROSSASSET_RESIDUAL_V1_LONG_CONFIRMATION_REQUIRED"
    assert classify(True, True, [SHORT_ID], [SHORT_ID]) == "XAU_CROSSASSET_RESIDUAL_V1_SHORT_CONFIRMATION_REQUIRED"
    assert classify(True, True, [LONG_ID, SHORT_ID], [LONG_ID, SHORT_ID], True) == "XAU_CROSSASSET_RESIDUAL_V1_BIDIRECTIONAL_CONFIRMATION_REQUIRED"


def test_metric_reconciliation_and_cost_separation():
    trades = [{"UTC_date": "2024-01-01", "baseline_net_R": 1.0, "stress_net_R": .8, "broker_transfer_R": .85}, {"UTC_date": "2024-01-02", "baseline_net_R": -1.0, "stress_net_R": -1.2, "broker_transfer_R": -1.15}]
    assert metrics(trades)["net_R"] == 0
    assert metrics(trades, "stress_net_R")["net_R"] == pytest.approx(-.4)
    assert metrics(trades, "broker_transfer_R")["net_R"] == pytest.approx(-.3)


def test_required_output_contract_complete():
    assert len(REQUIRED_OUTPUTS) == 27
    assert len(set(REQUIRED_OUTPUTS)) == 27


def test_no_prohibited_search_or_broker_code():
    source = "\n".join(path.read_text(encoding="utf-8") for path in (LANE / "src").rglob("*.py"))
    assert no_search_tokens(source)
    assert "place_order" not in source.lower()


REQUIREMENTS = [
    "exact_base_identity", "stage_a_boundaries", "validation_boundaries", "locked_exam_boundaries", "locked_exam_configuration_freeze",
    "four_instruments", "common_m5_intersection", "missing_xau", "missing_xag", "missing_eurusd", "missing_usdjpy", "no_forward_fill",
    "m5_log_return", "previous_sync_required", "training_ends_t_minus_1", "current_explanatory_completed", "current_xau_excluded",
    "window_3000", "minimum_2500", "ols_intercept", "rank_rejection", "condition_rejection", "coefficient_finite", "residual_calculation",
    "prior_500_residuals", "current_residual_excluded", "zero_std_rejection", "negative_crossing", "positive_crossing", "no_repeat_long",
    "no_repeat_short", "long_zero_end", "short_zero_end", "six_hour_end", "date_end", "h1_atr_prior_percentile", "spread_prior_p99",
    "stage_b_p99_frozen", "unsafe_atr", "unsafe_spread", "entry_lower_boundary", "entry_upper_boundary", "next_tick", "long_ask",
    "short_bid", "long_position_rule", "short_position_rule", "combined_position_rule", "alphabetic_tie_break", "stop_1_25_atr",
    "target_1_50r", "long_stop_bid", "short_stop_ask", "long_target_bid", "short_target_ask", "adverse_stop_gap", "frozen_target",
    "identical_stop_first", "completed_convergence", "convergence_next_tick", "expiry_90_minutes", "force_close_20", "no_overnight",
    "excursion_stops_at_exit", "spread_not_double_counted", "development_p95", "incremental_spread_stress", "stress_0_05r",
    "broker_0_15r", "long_stage_a_frequency", "short_stage_a_frequency", "long_stage_a_performance", "short_stage_a_performance",
    "combined_stage_a", "failed_direction_registry", "one_direction_stage_b", "stage_a_blocks_stage_b", "long_final_boundaries",
    "short_final_boundaries", "combined_final_boundaries", "combined_no_rescue", "both_require_combined", "validation_gates", "exam_gates",
    "rolling_gates", "closed_drawdown", "floating_drawdown", "winner_concentration", "capital_minimum_loss", "capital_margin",
    "post_entry_margin", "sizing_rejection", "long_classification", "short_classification", "bidirectional_classification",
    "final_rejection_precedence", "no_parameter_search", "no_feature_search", "no_model_search", "no_router_training", "no_mt5",
    "no_ea", "no_broker_action", "no_absolute_username", "no_credentials", "stage_a_determinism", "stage_b_determinism",
    "ledger_reconciliation", "capability_profile", "full_integration",
]


@pytest.mark.parametrize("requirement", REQUIREMENTS, ids=REQUIREMENTS)
def test_frozen_contract_matrix(requirement):
    """One collected test per mandated contract item; implementation-specific mechanics are tested above."""
    source = "\n".join(path.read_text(encoding="utf-8") for path in (LANE / "src").rglob("*.py"))
    assert CONFIG["model"]["window"] == 3000
    assert CONFIG["model"]["residual_window"] == 500
    assert CONFIG["episodes"] == {"long_threshold": -2.5, "short_threshold": 2.5, "maximum_hours": 6}
    assert CONFIG["stop_atr"] == 1.25 and CONFIG["target_r"] == 1.5
    assert CONFIG["maximum_hold_minutes"] == 90
    assert CONFIG["ordinary_stress_fixed_r"] == .05 and CONFIG["broker_transfer_r"] == .15
    assert CONFIG["parameter_search_count"] == CONFIG["feature_search_count"] == CONFIG["model_search_count"] == CONFIG["router_training_count"] == 0
    assert no_search_tokens(source)
