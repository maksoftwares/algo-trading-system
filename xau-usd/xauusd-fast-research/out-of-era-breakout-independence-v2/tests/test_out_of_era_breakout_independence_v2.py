from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODULE_PATH = ROOT / "src" / "replication.py"
SPEC = importlib.util.spec_from_file_location(
    "out_of_era_breakout_independence_v2_tests", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
REPLICATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPLICATION
SPEC.loader.exec_module(REPLICATION)

FINAL_SPEC = importlib.util.spec_from_file_location(
    "out_of_era_breakout_final_contract_tests", ROOT / "lock_final_contract.py"
)
if FINAL_SPEC is None or FINAL_SPEC.loader is None:
    raise ImportError(ROOT / "lock_final_contract.py")
FINAL = importlib.util.module_from_spec(FINAL_SPEC)
sys.modules[FINAL_SPEC.name] = FINAL
FINAL_SPEC.loader.exec_module(FINAL)


def _trades(times: list[str], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time": pd.to_datetime(times, utc=True),
            "direction": ["LONG"] * len(times),
            "stress_net_r": values,
        }
    )


def test_closed_drawdown_includes_initial_equity_peak() -> None:
    assert REPLICATION.closed_drawdown(pd.Series([-2.0, 3.0])) == 2.0


def test_daily_significance_includes_zero_trade_days() -> None:
    days = pd.date_range("2020-01-01T00:00:00Z", periods=10, freq="1D")
    trades = _trades(["2020-01-01T10:00:00Z"], [1.0])
    pvalue = REPLICATION.one_sided_daily_pvalue(trades, days)
    assert 0.0 < pvalue < 0.5
    values = REPLICATION.daily_values(trades, days)
    assert len(values) == 10
    assert np.isclose(values.sum(), 1.0)


def test_holm_adjustment_uses_all_registered_candidates() -> None:
    adjusted = REPLICATION.holm_adjust({"a": 0.01, "b": 0.03, "c": 0.50})
    assert adjusted == {"a": 0.03, "b": 0.06, "c": 0.5}


def test_entry_overlap_and_daily_correlation_are_explicit() -> None:
    days = pd.date_range("2020-01-01T00:00:00Z", periods=4, freq="1D")
    first = _trades(
        ["2020-01-01T10:00:00Z", "2020-01-02T10:00:00Z"], [1.0, -1.0]
    )
    second = _trades(
        ["2020-01-01T10:30:00Z", "2020-01-03T10:00:00Z"], [0.5, -0.5]
    )
    assert REPLICATION.entry_overlap_fraction(first, second, 60.0) == 0.5
    expected = REPLICATION.daily_values(first, days).corr(
        REPLICATION.daily_values(second, days)
    )
    assert np.isclose(
        REPLICATION.daily_pnl_correlation(first, second, days), expected
    )


def test_distinct_selection_respects_fixed_order_and_pairwise_failure() -> None:
    economic = ["R1", "R1B", "COMPRESSION"]
    pairwise = [
        {
            "first_candidate_id": "R1",
            "second_candidate_id": "R1B",
            "independence_pass": False,
        },
        {
            "first_candidate_id": "R1",
            "second_candidate_id": "COMPRESSION",
            "independence_pass": True,
        },
        {
            "first_candidate_id": "R1B",
            "second_candidate_id": "COMPRESSION",
            "independence_pass": True,
        },
    ]
    selected = REPLICATION.select_distinct_survivors(
        economic, pairwise, ["R1", "R1B", "COMPRESSION"]
    )
    assert selected == ["R1", "COMPRESSION"]


def test_month_contract_is_exactly_2010_01_through_2016_06() -> None:
    config = FINAL.load_config()
    months = FINAL.expected_months(config)
    assert len(months) == 78
    assert months[0] == "2010-01"
    assert months[-1] == "2016-06"
