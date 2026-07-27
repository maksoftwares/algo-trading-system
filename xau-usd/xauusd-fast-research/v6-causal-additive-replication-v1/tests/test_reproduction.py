from pathlib import Path

import pandas as pd
import pytest

from src.reproduction import (
    add_capital_outcomes,
    choose_annual_members,
    deduplicate_by_prior_rank,
    internal_capital_lock,
    prepare_candidate_ledger,
    route_candidates,
    verify_sources,
)


UTC = "UTC"


def frame(exits, entries, returns, risks):
    return pd.DataFrame(
        {
            "cap_exit_t": pd.to_datetime(exits, utc=True),
            "entry_t": pd.to_datetime(entries, utc=True),
            "rc": returns,
            "stop_usd": risks,
        }
    )


def test_annual_selection_uses_only_capital_exits_before_year():
    pool = {
        "future_winner": frame(
            ["2023-01-02"] * 30, ["2022-12-20"] * 30, [10.0] * 30, [1.0] * 30
        ),
        "known_member": frame(
            ["2022-12-30"] * 30, ["2022-12-20"] * 30, [0.5] * 30, [1.0] * 30
        ),
    }
    chosen, _ = choose_annual_members(pool, 2023, 30, 1, 20.0, 3.0)
    assert chosen == ["known_member"]


def test_dedup_uses_prior_rank_not_realized_return():
    trades = pd.DataFrame(
        {
            "i": [10, 10],
            "long": [True, True],
            "pick_rank": [1, 2],
            "spec": ["prior_best", "future_winner"],
            "rc": [-1.0, 50.0],
        }
    )
    selected = deduplicate_by_prior_rank(trades)
    assert selected["spec"].tolist() == ["prior_best"]


def test_internal_lock_uses_capital_exit_clock():
    trades = pd.DataFrame(
        {
            "entry_t": pd.to_datetime(
                ["2025-01-01 00:00", "2025-01-01 01:00"], utc=True
            ),
            "cap_exit_t": pd.to_datetime(
                ["2025-01-01 04:00", "2025-01-01 02:00"], utc=True
            ),
            "exit_t": pd.to_datetime(
                ["2025-01-01 00:30", "2025-01-01 01:30"], utc=True
            ),
            "pick_rank": [1, 1],
            "spec": ["a", "b"],
        }
    )
    selected = internal_capital_lock(trades, 1)
    assert selected["spec"].tolist() == ["a"]


def test_prepare_candidate_reconciles_stressed_endpoint():
    executed = pd.DataFrame(
        {
            "i": [1],
            "spec": ["a"],
            "long": [True],
            "stop": [10.0],
            "dec_time": pd.to_datetime(["2025-01-01 00:00"], utc=True),
            "entry_t": pd.to_datetime(["2025-01-01 00:05"], utc=True),
            "exit_t": pd.to_datetime(["2025-01-01 01:00"], utc=True),
            "cap_exit_t": pd.to_datetime(["2025-01-02 00:05"], utc=True),
            "r": [1.0],
            "rc": [1.0],
            "stop_usd": [10.0],
            "pick_rank": [1],
            "selection_year": [2025],
            "cap_entry_price": [2000.0],
            "cap_exit_price": [2010.3],
        }
    )
    stress = {
        "base_fee_usd": 0.30,
        "additional_fixed_cost_usd": 0.30,
        "holding_cost_usd_per_24h": 0.35,
        "slippage_r": 0.05,
    }
    ledger = prepare_candidate_ledger(executed, stress)
    assert ledger.loc[0, "pnl_usd"] == pytest.approx(10.0)
    assert ledger.loc[0, "fee_stress_pnl_usd"] == pytest.approx(8.85)
    assert (
        ledger.loc[0, "exit_price"]
        - ledger.loc[0, "entry_price"]
        - ledger.loc[0, "fee_stress_open_cost_usd"]
    ) == pytest.approx(ledger.loc[0, "fee_stress_pnl_usd"])


def test_candidate_ids_preserve_simultaneous_distinct_signals():
    executed = pd.DataFrame(
        {
            "i": [1, 2],
            "spec": ["a", "b"],
            "long": [True, True],
            "stop": [10.0, 10.0],
            "dec_time": pd.to_datetime(["2025-01-01 00:00"] * 2, utc=True),
            "entry_t": pd.to_datetime(["2025-01-01 00:05"] * 2, utc=True),
            "exit_t": pd.to_datetime(["2025-01-01 01:00"] * 2, utc=True),
            "cap_exit_t": pd.to_datetime(["2025-01-02 00:05"] * 2, utc=True),
            "r": [1.0, 1.0],
            "rc": [1.0, 1.0],
            "stop_usd": [10.0, 10.0],
            "pick_rank": [1, 2],
            "selection_year": [2025, 2025],
            "cap_entry_price": [2000.0, 2000.0],
            "cap_exit_price": [2010.3, 2010.3],
        }
    )
    stress = {
        "base_fee_usd": 0.30,
        "additional_fixed_cost_usd": 0.30,
        "holding_cost_usd_per_24h": 0.35,
        "slippage_r": 0.05,
    }
    ledger = prepare_candidate_ledger(executed, stress)
    assert ledger["trade_id"].nunique() == 2


def test_capital_outcome_enters_on_candidate_next_bar():
    times = pd.date_range("2025-01-01", periods=5, freq="5min", tz=UTC)
    capital = pd.DataFrame(
        {
            "bid_open": [99.9, 100.9, 101.9, 102.9, 103.9],
            "bid_low": [99.5, 100.5, 101.5, 102.5, 103.5],
            "bid_close": [100.0, 101.0, 102.0, 103.0, 104.0],
            "ask_open": [100.1, 101.1, 102.1, 103.1, 104.1],
            "ask_high": [100.5, 101.5, 102.5, 103.5, 104.5],
            "ask_close": [100.2, 101.2, 102.2, 103.2, 104.2],
        }
    )
    candidates = pd.DataFrame(
        {"i1": [5], "j": [2], "stop": [10.0], "long": [True]}
    )
    result = add_capital_outcomes(
        candidates,
        {"t": pd.Series(times), "cap": capital, "cap_t": times.values},
        0.30,
    )
    assert result.loc[0, "cap_entry_price"] == pytest.approx(102.1)
    assert result.loc[0, "cap_exit_t"] == times[4]


def test_router_counts_existing_addon_risk():
    entry = pd.Timestamp("2025-01-01 01:00", tz=UTC)
    baseline = pd.DataFrame(
        {
            "trade_id": ["base"],
            "sleeve_id": ["EXISTING_ADDON"],
            "entry_time": [entry - pd.Timedelta(hours=1)],
            "exit_time": [entry + pd.Timedelta(hours=1)],
            "risk_usd": [30.0],
            "fee_stress_pnl_usd": [1.0],
        }
    )
    candidate = pd.DataFrame(
        {
            "trade_id": ["candidate"],
            "policy_id": ["p"],
            "entry_time": [entry],
            "exit_time": [entry + pd.Timedelta(hours=1)],
            "risk_usd": [20.0],
            "pick_rank": [1],
            "fee_stress_pnl_usd": [1.0],
        }
    )
    limits = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_candidate_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 225.0,
        "drawdown_resume_usd": 180.0,
    }
    accepted, decisions = route_candidates(baseline, candidate, limits)
    assert accepted.empty
    assert decisions.loc[0, "reason"] == "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK_USD"


def test_verify_sources_fails_closed_on_hash_drift(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("changed", encoding="utf-8")
    config = {
        "external_package": {
            "root": str(tmp_path),
            "sources": {"one": {"path": "source.txt", "sha256": "0" * 64}},
        },
        "external_data": {},
        "canonical_v60": {},
    }
    with pytest.raises(ValueError, match="Locked source drift"):
        verify_sources(config)
