from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from eurusd_regime_specialists.neutral_rates_dollar_sign_consensus_h4 import (
    build_lagged_context,
    create_signal_candidates,
    load_config,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_neutral_rates_dollar_sign_consensus_h4.json"
)
LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_PREREG_"
    "2026_07_29.sha256.json"
)
CENSUS_PATH = (
    PACKAGE_ROOT / "outputs" / "neutral_rates_dollar_sign_consensus_h4" / "CENSUS.json"
)
CENSUS_LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_CENSUS_RESULT_"
    "2026_07_29.sha256.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sign_consensus_contract_is_frozen_before_outcomes() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    assert lock["frozen_before_census_and_forward_outcomes"] is True
    assert lock["pnl_or_forward_path_loaded"] is False
    assert lock["oracle_decision_use_allowed"] is False
    assert lock["parameter_search_allowed"] is False
    for relative, expected in lock["files"].items():
        assert _sha256(PACKAGE_ROOT / relative) == expected


def test_sign_consensus_has_no_tunable_macro_threshold() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    strategy = config["strategy"]
    assert strategy["macro_rule"]["zero_threshold_only"] is True
    assert strategy["directions"] == ["LONG", "SHORT"]
    assert strategy["target_r"] == 1.5
    assert strategy["owned_regime_only"] is True
    assert config["decision_policy"]["no_parameter_search"] is True


def test_daily_context_is_lagged_to_next_calendar_day() -> None:
    context = build_lagged_context(load_config())
    observation = pd.to_datetime(context["observation_date"], utc=True)
    assert (context["available_time_utc"] == observation + pd.Timedelta(days=1)).all()


def test_signal_rule_is_symmetric_and_uses_completed_h4() -> None:
    index = pd.DatetimeIndex(
        ["2026-01-05T00:00:00Z", "2026-01-05T04:00:00Z"],
        name="signal_time_utc",
    )
    h4 = pd.DataFrame(
        {
            "bid_open": [1.10, 1.20],
            "bid_high": [1.12, 1.21],
            "bid_low": [1.09, 1.18],
            "bid_close": [1.11, 1.19],
            "atr": [0.01, 0.01],
            "ema20": [1.105, 1.195],
            "ema50": [1.10, 1.20],
            "ema100": [1.09, 1.21],
            "recent_low": [1.08, 1.17],
            "recent_high": [1.13, 1.22],
        },
        index=index,
    )
    context = pd.DataFrame(
        {
            "available_time_utc": [
                pd.Timestamp("2026-01-04T00:00:00Z"),
                pd.Timestamp("2026-01-05T02:00:00Z"),
            ],
            "observation_date": ["2026-01-03", "2026-01-04"],
            "tlt_uup_5d_pct": [1.0, -1.0],
            "tlt_uup_20d_pct": [1.0, -1.0],
            "tlt_shy_20d_pct": [1.0, -1.0],
        }
    )
    candidates = create_signal_candidates(h4, context, load_config())
    assert candidates["side"].tolist() == ["LONG", "SHORT"]
    assert candidates["entry_time"].tolist() == [
        pd.Timestamp("2026-01-05T04:00:00Z"),
        pd.Timestamp("2026-01-05T08:00:00Z"),
    ]


def test_capacity_failure_keeps_forward_paths_closed() -> None:
    result = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    lock = json.loads(CENSUS_LOCK_PATH.read_text(encoding="utf-8"))
    assert result["status"] == "REJECTED_OUTCOME_BLIND_CAPACITY_CENSUS"
    assert result["summary"]["eligible_neutral_signals"] == 62
    assert result["summary"]["by_side"] == {"LONG": 32, "SHORT": 30}
    assert (
        result["summary"]["gate_results"]["minimum_neutral_signals_recent_half_year"]
        is False
    )
    assert result["boundary"]["pnl_loaded_or_computed"] is False
    assert lock["execution_allowed"] is False
    assert lock["pnl_or_forward_path_loaded"] is False
