from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurusd_regime_specialists.neutral_five_session_reversal import (
    build_candidates,
    execute,
)


def _m5() -> pd.DataFrame:
    index = pd.date_range(
        "2020-01-01T00:00:00Z",
        periods=3000,
        freq="5min",
    )
    close = pd.Series(
        [1.1000 + position * 0.00001 for position in range(len(index))],
        index=index,
    )
    return pd.DataFrame(
        {
            "bid_open": close,
            "bid_high": close + 0.0001,
            "bid_low": close - 0.0001,
            "bid_close": close,
            "ask_open": close + 0.0002,
            "ask_high": close + 0.0003,
            "ask_low": close + 0.0001,
            "ask_close": close + 0.0002,
        },
        index=index,
    )


def _config(source: Path) -> dict:
    return {
        "neutral_timestamp_source": {"path": str(source)},
        "strategy": {
            "entry_hour_utc": 0,
            "entry_minute_utc": 0,
            "completed_m5_lookback_bars": 12,
            "cooldown_hours_from_entry": 72,
        },
        "execution": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
            "risk_pips": 40.0,
            "target_r": 1.5,
            "maximum_hold_hours": 72,
            "risk_per_trade_portfolio_r": 0.25,
        },
        "windows": {
            "development_2019_2022": [
                "2019-01-01T00:00:00Z",
                "2022-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def test_completed_rising_move_maps_to_short(
    tmp_path: Path, monkeypatch
) -> None:
    m5 = _m5()
    entry = m5.index[1440]
    source = pd.DataFrame(
        {
            "entry_time_utc": [entry, entry],
            "side": ["LONG", "SHORT"],
        }
    )
    path = tmp_path / "source.parquet"
    source.to_parquet(path, index=False)
    from eurusd_regime_specialists import (
        neutral_five_session_reversal as module,
    )

    monkeypatch.setattr(module, "PACKAGE_ROOT", tmp_path)
    candidates, _ = build_candidates(
        m5, _config(path), enforce_frozen_census=False
    )
    assert len(candidates) == 1
    assert candidates.iloc[0]["side"] == "SHORT"
    assert candidates.iloc[0]["signal_end_time_utc"] == m5.index[1439]
    assert candidates.iloc[0]["completed_m5_bars"] == 12


def test_cooldown_is_entry_time_based(
    tmp_path: Path, monkeypatch
) -> None:
    m5 = _m5()
    entries = [m5.index[1440], m5.index[1728], m5.index[2304]]
    source = pd.DataFrame(
        {
            "entry_time_utc": [
                timestamp
                for timestamp in entries
                for _ in ("LONG", "SHORT")
            ],
            "side": ["LONG", "SHORT"] * len(entries),
        }
    )
    path = tmp_path / "source.parquet"
    source.to_parquet(path, index=False)
    from eurusd_regime_specialists import (
        neutral_five_session_reversal as module,
    )

    monkeypatch.setattr(module, "PACKAGE_ROOT", tmp_path)
    cfg = _config(path)
    cfg["strategy"]["entry_hour_utc"] = entries[0].hour
    cfg["strategy"]["entry_minute_utc"] = entries[0].minute
    cfg["strategy"]["cooldown_hours_from_entry"] = 48
    candidates, census = build_candidates(
        m5, cfg, enforce_frozen_census=False
    )
    assert len(candidates) == 2
    assert census["cooldown_cash_points"] == 1


def test_execution_uses_wide_one_point_five_r_contract() -> None:
    index = pd.date_range(
        "2020-01-06T00:00:00Z", periods=4, freq="5min"
    )
    m5 = pd.DataFrame(
        {
            "bid_open": [1.1000] * 4,
            "bid_high": [1.1001, 1.1063, 1.1001, 1.1001],
            "bid_low": [1.0999] * 4,
            "bid_close": [1.1000] * 4,
            "ask_open": [1.1002] * 4,
            "ask_high": [1.1003, 1.1064, 1.1003, 1.1003],
            "ask_low": [1.1001] * 4,
            "ask_close": [1.1002] * 4,
        },
        index=index,
    )
    candidates = pd.DataFrame(
        [
            {
                "family": "TEST",
                "regime": "NEUTRAL",
                "eligible_date": "2020-01-06",
                "trade_id": "one",
                "entry_time_utc": index[0],
                "entry_position": 0,
                "side": "LONG",
                "signal_start_time_utc": index[0],
                "signal_end_time_utc": index[0],
                "completed_m5_bars": 12,
                "five_session_move_pips": -10.0,
                "window": "development_2019_2022",
            }
        ]
    )
    cfg = _config(Path("unused"))
    trades = execute(candidates, m5, cfg)
    assert trades.iloc[0]["exit_reason"] == "TARGET"
    assert trades.iloc[0]["risk_pips"] == 40.0
    assert 1.49 < trades.iloc[0]["r"] < 1.50
    assert trades.iloc[0]["extra_half_pip_stress_r"] < trades.iloc[0]["r"]
