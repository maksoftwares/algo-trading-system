from __future__ import annotations

import pytest

from xau_crossasset_residual.core import capital_feasibility, sizing_rejection_rate_passes


def test_exact_half_percent_risk_boundary():
    passed, details = capital_feasibility(1000, 5.00, 100)
    assert passed and details["risk_limit"] == 5.0
    assert not capital_feasibility(1000, 5.01, 100)[0]


def test_exact_twenty_percent_margin_boundary():
    assert capital_feasibility(1000, 5, 200.00)[0]
    passed, details = capital_feasibility(1000, 5, 200.01)
    assert not passed and "REQUIRED_MARGIN_EXCEEDS_20_PERCENT" in details["rejection_reason"]


def test_exact_eighty_percent_free_margin_boundary():
    assert capital_feasibility(1000, 5, 200.00)[1]["post_entry_free_margin"] == 800.0
    passed, details = capital_feasibility(1000, 5, 200.01)
    assert not passed and details["post_entry_free_margin"] == pytest.approx(799.99)
    assert "POST_ENTRY_FREE_MARGIN_BELOW_80_PERCENT" in details["rejection_reason"]


def test_sizing_rejection_rate_boundary():
    assert sizing_rejection_rate_passes(10, 100)
    assert not sizing_rejection_rate_passes(11, 100)


def test_invalid_sizing_rejection_counts_fail_closed():
    with pytest.raises(ValueError):
        sizing_rejection_rate_passes(1, 0)
    with pytest.raises(ValueError):
        sizing_rejection_rate_passes(101, 100)


def test_leverage_cannot_enlarge_risk_limit():
    # Margin may be tiny under leverage, but loss above USD 5 still fails.
    passed, details = capital_feasibility(1000, 5.01, 10)
    assert not passed and details["risk_limit"] == 5.0
