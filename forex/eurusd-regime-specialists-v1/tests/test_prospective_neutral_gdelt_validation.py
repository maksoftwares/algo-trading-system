from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from capture_prospective_neutral_gdelt_relative_tone import (
    load_and_verify_preregistration,
)
from validate_prospective_neutral_gdelt_relative_tone import (
    evaluate_validation,
    load_decisions,
)


def _evidence(
    *,
    winning_r: float = 1.5,
    losing_r: float = -1.0,
) -> tuple[
    list[dict[str, object]],
    dict[str, dict[str, object]],
    pd.DataFrame,
    set[str],
]:
    decisions: list[dict[str, object]] = []
    paths: dict[str, dict[str, object]] = {}
    oracle_rows: list[dict[str, object]] = []
    completed: set[str] = set()
    dates: list[pd.Timestamp] = []
    for month in range(12):
        base = pd.Timestamp("2026-08-01", tz="UTC") + pd.DateOffset(
            months=month
        )
        dates.extend([base, base + pd.Timedelta(days=1)])
    dates.extend(
        [
            pd.Timestamp("2027-02-03", tz="UTC"),
            pd.Timestamp("2027-02-04", tz="UTC"),
            pd.Timestamp("2027-04-03", tz="UTC"),
            pd.Timestamp("2027-04-04", tz="UTC"),
            pd.Timestamp("2027-06-03", tz="UTC"),
            pd.Timestamp("2027-06-04", tz="UTC"),
        ]
    )
    for index, day in enumerate(dates):
        side = ("LONG", "LONG", "SHORT", "SHORT")[index % 4]
        result_r = (
            winning_r if index % 2 == 0 else losing_r
        )
        signal_id = f"signal-{index:02d}"
        entry = day + pd.Timedelta(minutes=20)
        exit_time = entry + pd.Timedelta(hours=1)
        date_text = day.strftime("%Y-%m-%d")
        decisions.append(
            {
                "entry_date_utc": date_text,
                "status": "SIGNAL",
                "side": side,
                "decision_id": signal_id,
            }
        )
        paths[signal_id] = {
            "manifest_sha256": f"path-{index:02d}",
            "tick_replay_verified": True,
            "execution": {
                "status": "CLOSED",
                "side": side,
                "entry_time_utc": entry.isoformat(),
                "exit_time_utc": exit_time.isoformat(),
                "exit_reason": "TARGET" if result_r > 0 else "STOP",
                "r": result_r,
                "extra_half_pip_stress_r": result_r - 0.125,
            },
        }
        oracle_rows.append(
            {
                "oracle_date": date_text,
                "side": side,
                "regime": "NEUTRAL",
                "entry_time_utc": entry.isoformat(),
                "oracle_trade_number": 1,
            }
        )
        completed.add(date_text)
    return decisions, paths, pd.DataFrame(oracle_rows), completed


def test_frequency_is_not_an_admission_gate() -> None:
    strategy, _ = load_and_verify_preregistration()
    result = evaluate_validation(
        [],
        {},
        pd.DataFrame(),
        set(),
        strategy,
        evaluated_at_utc="2026-07-30T00:00:00Z",
    )
    assert result["status"] == "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    assert result["frequency"]["admission_gate"] is False
    assert result["frequency"]["closed_trades"] == 0
    assert not result["profitability_review_allowed"]


def test_balanced_profitable_evidence_reaches_full_review() -> None:
    strategy, _ = load_and_verify_preregistration()
    decisions, paths, oracle, completed = _evidence()
    result = evaluate_validation(
        decisions,
        paths,
        oracle,
        completed,
        strategy,
        evaluated_at_utc="2027-07-29T00:00:00Z",
    )
    assert result["overall"]["trades"] == 30
    assert result["overall"]["win_rate"] == 0.5
    assert result["overall"]["realized_payoff_ratio"] == 1.5
    assert result["economic_and_robustness_gates_passed"]
    assert result["same_day_regime_resemblance_gates_passed"]
    assert result["full_temporal_oracle_imitation_gates_passed"]
    assert result["profitability_review_allowed"]
    assert not result["controlled_demo_ready"]


def test_mature_losing_evidence_is_rejected_without_retuning() -> None:
    strategy, _ = load_and_verify_preregistration()
    decisions, paths, oracle, completed = _evidence(
        winning_r=0.25,
        losing_r=-1.0,
    )
    result = evaluate_validation(
        decisions,
        paths,
        oracle,
        completed,
        strategy,
        evaluated_at_utc="2027-07-29T00:00:00Z",
    )
    assert result["status"] == "REJECTED_WITHOUT_RETUNING"
    assert not result["economic_and_robustness_gates_passed"]
    assert not result["profitability_review_allowed"]


def test_decision_filename_must_bind_content_hash(tmp_path: Path) -> None:
    decision_root = tmp_path / "ledger" / "decisions"
    decision_root.mkdir(parents=True)
    record = {
        "entry_date_utc": "2026-07-29",
        "evaluated_at_utc": "2026-07-29T00:15:01Z",
        "decision_time_utc": "2026-07-29T00:15:00Z",
        "status": "CASH_NO_SIGNAL",
        "side": None,
    }
    payload = (
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    ).encode()
    digest = hashlib.sha256(payload).hexdigest()
    wrong = decision_root / f"DECISION_2026-07-29_{digest[:15]}0.json"
    wrong.write_bytes(payload)
    with pytest.raises(RuntimeError, match="filename/hash drift"):
        load_decisions(
            tmp_path / "ledger",
            evaluated_at_utc="2026-07-29T01:00:00Z",
        )
