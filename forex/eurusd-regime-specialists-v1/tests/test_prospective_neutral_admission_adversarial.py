from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    evaluate_admission,
)

EVALUATED_AT = "2027-08-01T00:00:00Z"


def _ledger(
    values: Sequence[float],
    *,
    sides: Sequence[str] | None = None,
    stressed_values: Sequence[float] | None = None,
    oracle_labels: Sequence[object] | None = None,
) -> pd.DataFrame:
    count = len(values)
    resolved_sides = (
        list(sides)
        if sides is not None
        else ["LONG" if index < count / 2 else "SHORT" for index in range(count)]
    )
    resolved_stress = (
        list(stressed_values)
        if stressed_values is not None
        else [value - 0.125 for value in values]
    )
    resolved_oracle = (
        list(oracle_labels)
        if oracle_labels is not None
        else [index < count / 2 for index in range(count)]
    )
    if not (
        len(resolved_sides)
        == len(resolved_stress)
        == len(resolved_oracle)
        == count
    ):
        raise ValueError("Synthetic admission columns must have equal length")
    rows = []
    start = pd.Timestamp("2026-08-01T00:00:00Z")
    for index, value in enumerate(values):
        entry = start + pd.Timedelta(days=index)
        rows.append(
            {
                "signal_id": f"{index:064x}",
                "status": "CLOSED",
                "entry_time_utc": entry,
                "exit_time_utc": entry + pd.Timedelta(hours=1),
                "side": resolved_sides[index],
                "r": value,
                "extra_half_pip_stress_r": resolved_stress[index],
                "oracle_same_day_same_side": resolved_oracle[index],
                "path_evidence_sha256": "e" * 64,
            }
        )
    return pd.DataFrame(rows)


def _balanced_values() -> list[float]:
    return [1.5 if index % 2 == 0 else -1.0 for index in range(30)]


def test_perfect_but_subminimum_sample_cannot_enter_review() -> None:
    result = evaluate_admission(
        _ledger([1.5] * 29),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result["status"] == "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    assert result["gate_results"]["minimum_executed_trades"] is False
    assert result["research_review_allowed"] is False


def test_profitable_one_sided_sample_fails_side_balance() -> None:
    result = evaluate_admission(
        _ledger(
            _balanced_values(),
            sides=["LONG"] * 30,
        ),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result["overall"]["profit_factor"] == 1.5
    assert result["gate_results"]["both_sides"] is False
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"


def test_one_unknown_oracle_label_blocks_oracle_precision_gate() -> None:
    labels: list[object] = [index < 15 for index in range(30)]
    labels[-1] = pd.NA
    result = evaluate_admission(
        _ledger(
            _balanced_values(),
            oracle_labels=labels,
        ),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result["oracle_same_day_same_side_precision"] is None
    assert result["gate_results"]["oracle_precision"] is False
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"


def test_nominal_pf_reliant_on_top_five_percent_winners_is_rejected() -> None:
    wins = [9.875, *([0.5] * 7), 9.875, *([0.5] * 6)]
    values = [
        value
        for win in wins
        for value in (win, -1.0)
    ]
    result = evaluate_admission(
        _ledger(values),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result["overall"]["win_rate"] == 0.5
    assert result["overall"]["realized_payoff_ratio"] == 1.75
    assert result["overall"]["profit_factor"] == 1.75
    assert result["gate_results"]["profit_factor"] is True
    assert result["gate_results"]["both_sides"] is True
    assert result["gate_results"]["top_5pct_winner_removal"] is False
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"


def test_nominally_valid_sample_failing_cost_stress_is_rejected() -> None:
    values = _balanced_values()
    stressed = [0.9 if value > 0 else -1.1 for value in values]
    result = evaluate_admission(
        _ledger(
            values,
            stressed_values=stressed,
        ),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result["overall"]["profit_factor"] == 1.5
    assert result["extra_half_pip_round_trip"]["profit_factor"] < 1.0
    assert result["gate_results"]["extra_half_pip"] is False
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"
