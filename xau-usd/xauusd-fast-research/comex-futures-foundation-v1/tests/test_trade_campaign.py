from __future__ import annotations

import pandas as pd
import pytest

from spot_labels import load_label_config
from tbbo_features import load_trade_feature_config
from trade_campaign import build_evidence_report, candidates_for_events, filter_session_with_warmup


def event_frame() -> pd.DataFrame:
    times = pd.date_range("2026-01-05T13:14:00Z", periods=430, freq="s")
    sizes = [1000 if timestamp >= pd.Timestamp("2026-01-05T13:20:00Z") else 10 for timestamp in times]
    return pd.DataFrame(
        {
            "ts_event": times,
            "publisher_id": 1,
            "instrument_id": 101,
            "sequence": range(len(times)),
            "side": "B",
            "price": 100.0 + pd.Series(range(len(times))) * 0.1,
            "size": sizes,
        }
    )


def test_session_filter_keeps_exact_locked_warmup() -> None:
    result = filter_session_with_warmup(event_frame(), load_trade_feature_config())
    assert result["ts_event"].min() == pd.Timestamp("2026-01-05T13:15:00Z")
    assert result["ts_event"].max() == pd.Timestamp("2026-01-05T13:21:09Z")


def test_candidate_ids_are_deterministic_and_unique() -> None:
    result = candidates_for_events(event_frame(), load_trade_feature_config())
    assert not result.empty
    assert result["candidate_id"].is_unique
    assert result["candidate_id"].str.endswith(":101").all()


def resolved_labels() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["a", "b", "c", "d"],
            "family": ["flow_continuation"] * 4,
            "split": ["train"] * 4,
            "status": ["RESOLVED"] * 4,
            "reason": [""] * 4,
            "exit_time_utc": pd.date_range("2023-01-01", periods=4, tz="UTC"),
            "baseline_net_pnl_usd": [2.0, -1.0, -1.0, 4.0],
            "stress_net_pnl_usd": [1.5, -1.5, -1.5, 3.5],
            "stress_net_r": [0.75, -0.75, -0.75, 1.75],
        }
    )


def test_report_calculates_profit_factor_drawdown_and_rejects_sparse_family() -> None:
    report = build_evidence_report(resolved_labels(), load_label_config())
    row = next(
        item
        for item in report["summaries"]
        if item["split"] == "train" and item["family"] == "flow_continuation"
    )
    assert row["profit_factor"] == pytest.approx(3.0)
    assert row["stress_profit_factor"] == pytest.approx(5.0 / 3.0)
    assert row["maximum_closed_trade_drawdown_usd"] == pytest.approx(3.0)
    assert row["maximum_consecutive_losses"] == 2
    assert row["gate_pass"] is False
    assert report["research_decision"] == "REJECT"


def test_report_rejects_duplicate_candidate_ids() -> None:
    labels = resolved_labels()
    labels.loc[1, "candidate_id"] = labels.loc[0, "candidate_id"]
    with pytest.raises(ValueError, match="duplicate candidate IDs"):
        build_evidence_report(labels, load_label_config())


def test_infinite_profit_factor_is_json_safe() -> None:
    labels = resolved_labels().iloc[[0]].copy()
    report = build_evidence_report(labels, load_label_config())
    row = next(
        item
        for item in report["summaries"]
        if item["split"] == "train" and item["family"] == "flow_continuation"
    )
    assert row["profit_factor"] is None
    assert row["profit_factor_is_infinite"] is True
