from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_growth_risk_consensus import (
    build_candidates,
    simulate,
    stage_metrics,
)


def _config() -> dict:
    return {
        "experts": {
            "ASIA_HANDOFF_0300": {
                "decision_hour_utc": 3,
                "decision_minute_utc": 0,
            },
            "EUROPE_MORNING_0900": {
                "decision_hour_utc": 9,
                "decision_minute_utc": 0,
            },
            "US_RISK_1500": {
                "decision_hour_utc": 15,
                "decision_minute_utc": 0,
            },
        },
        "windows": {
            "development_2022": [
                "2022-01-01T00:00:00Z",
                "2022-12-31T23:59:59Z",
            ],
            "confirmation_2023": [
                "2023-01-01T00:00:00Z",
                "2023-12-31T23:59:59Z",
            ],
            "forward_2024": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ],
            "forward_2025": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ],
            "recent_2026_h1": [
                "2026-01-01T00:00:00Z",
                "2026-06-30T23:59:59Z",
            ],
        },
        "outcome_blind_census": {
            "minimum_candidates_total": 0,
            "minimum_candidates_development": 0,
            "minimum_candidates_confirmation": 0,
            "minimum_candidates_each_full_forward_year": 0,
            "minimum_candidates_recent_half_year": 0,
            "minimum_candidates_each_side": 0,
            "minimum_candidates_each_expert": 0,
        },
        "strategy": {
            "eurusd_stop_lookback_completed_m5_bars": 12,
            "stop_buffer_pips": 0.5,
            "stop_floor_pips": 4.0,
            "stop_ceiling_pips": 20.0,
            "target_r": 1.5,
            "maximum_hold_hours": 6,
        },
        "execution": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
            "extra_round_trip_stress_pips": 0.5,
        },
    }


def _growth_row(
    decision: pd.Timestamp,
    spx: float,
    copper: float,
    usdcnh: float,
) -> dict:
    bar_open = decision - pd.Timedelta(minutes=5)
    bar_ms = int(bar_open.value // 1_000_000)
    decision_ms = int(decision.value // 1_000_000)
    row = {
        "source_bar_open_time_utc": bar_open,
        "decision_time_utc": decision,
        "bar_open_timestamp_ms": bar_ms,
    }
    for prefix, value in (
        ("spx", spx),
        ("copper", copper),
        ("usdcnh", usdcnh),
    ):
        row[f"{prefix}_available_timestamp_ms"] = decision_ms
        row[f"{prefix}_source_last_timestamp_ms"] = decision_ms - 1
        row[f"{prefix}_return_60m"] = value
    return row


def test_consensus_direction_uses_exact_completed_external_bar(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "eurusd_regime_specialists.neutral_growth_risk_consensus."
        "load_ensemble_config",
        lambda: {"quarantine": []},
    )
    neutral = pd.DataFrame({"eligible_date": ["2022-01-03"]})
    rows = [
        _growth_row(
            pd.Timestamp("2022-01-03T03:00:00Z"),
            0.01,
            0.02,
            -0.01,
        ),
        _growth_row(
            pd.Timestamp("2022-01-03T09:00:00Z"),
            -0.01,
            -0.02,
            0.01,
        ),
        _growth_row(
            pd.Timestamp("2022-01-03T15:00:00Z"),
            0.01,
            -0.02,
            -0.01,
        ),
    ]
    candidates, census = build_candidates(
        neutral, pd.DataFrame(rows), _config()
    )
    assert list(candidates["side"]) == ["LONG", "SHORT"]
    assert list(candidates["expert"]) == [
        "ASIA_HANDOFF_0300",
        "EUROPE_MORNING_0900",
    ]
    assert census["mixed_or_zero_cash_points"] == 1


def test_noncausal_external_row_is_cash(monkeypatch) -> None:
    monkeypatch.setattr(
        "eurusd_regime_specialists.neutral_growth_risk_consensus."
        "load_ensemble_config",
        lambda: {"quarantine": []},
    )
    decision = pd.Timestamp("2022-01-03T03:00:00Z")
    row = _growth_row(decision, 0.01, 0.02, -0.01)
    row["copper_available_timestamp_ms"] += 300_000
    candidates, census = build_candidates(
        pd.DataFrame({"eligible_date": ["2022-01-03"]}),
        pd.DataFrame([row]),
        _config(),
    )
    assert candidates.empty
    assert census["noncausal_or_incomplete_points"] == 1


def _m5_for_simulation(entry: pd.Timestamp) -> pd.DataFrame:
    index = pd.date_range(
        entry - pd.Timedelta(minutes=60),
        entry + pd.Timedelta(minutes=30),
        freq="5min",
    )
    return pd.DataFrame(
        {
            "bid_open": 1.1000,
            "bid_high": 1.1002,
            "bid_low": 1.0998,
            "bid_close": 1.1000,
            "ask_open": 1.1001,
            "ask_high": 1.1003,
            "ask_low": 1.0999,
            "ask_close": 1.1001,
        },
        index=index,
    )


def test_entry_bar_cannot_change_structural_stop() -> None:
    entry = pd.Timestamp("2022-01-03T03:00:00Z")
    candidate = pd.DataFrame(
        {
            "entry_time_utc": [entry],
            "expert": ["ASIA_HANDOFF_0300"],
            "side": ["LONG"],
            "eligible_date": ["2022-01-03"],
            "spx_return_60m": [0.01],
            "copper_return_60m": [0.01],
            "usdcnh_return_60m": [-0.01],
        }
    )
    first = _m5_for_simulation(entry)
    first.loc[entry, ["bid_high", "bid_low"]] = [1.1020, 1.0990]
    second = first.copy()
    second.loc[entry, ["bid_high", "bid_low"]] = [1.1040, 1.0970]
    trades_a, _ = simulate(candidate, first, _config())
    trades_b, _ = simulate(candidate, second, _config())
    assert trades_a["stop_price"].iloc[0] == (
        trades_b["stop_price"].iloc[0]
    )


def test_same_bar_ambiguity_is_stop_first() -> None:
    entry = pd.Timestamp("2022-01-03T03:00:00Z")
    candidate = pd.DataFrame(
        {
            "entry_time_utc": [entry],
            "expert": ["ASIA_HANDOFF_0300"],
            "side": ["LONG"],
            "eligible_date": ["2022-01-03"],
            "spx_return_60m": [0.01],
            "copper_return_60m": [0.01],
            "usdcnh_return_60m": [-0.01],
        }
    )
    m5 = _m5_for_simulation(entry)
    m5.loc[entry, ["bid_high", "bid_low"]] = [1.1020, 1.0980]
    trades, _ = simulate(candidate, m5, _config())
    assert trades["exit_reason"].iloc[0] == "STOP"


def test_stage_gate_requires_profitability_and_both_sides() -> None:
    trades = pd.DataFrame(
        {
            "r": [1.5, -1.0, 1.5, -1.0],
            "side": ["LONG", "LONG", "SHORT", "SHORT"],
            "expert": [
                "ASIA_HANDOFF_0300",
                "ASIA_HANDOFF_0300",
                "EUROPE_MORNING_0900",
                "US_RISK_1500",
            ],
        }
    )
    gate = {
        "minimum_trades": 4,
        "minimum_win_rate": 0.4,
        "maximum_win_rate": 0.6,
        "minimum_realized_payoff_ratio": 1.25,
        "maximum_realized_payoff_ratio": 1.85,
        "minimum_profit_factor": 1.1,
        "minimum_expectancy_r": 0.0,
        "minimum_each_side_trades": 2,
        "minimum_each_side_profit_factor": 0.9,
        "maximum_drawdown_r": 12.0,
    }
    result = stage_metrics(
        trades, gate, list(_config()["experts"])
    )
    assert result["passed"] is True
