from __future__ import annotations

import json

import pandas as pd
import pytest

from capture_prospective_tradingview_consensus import (
    build_pre_release_rows,
    evidence_chain,
    write_immutable,
)


def _payload() -> dict:
    return {
        "status": "ok",
        "result": [
            {
                "id": "future-valid",
                "date": "2026-08-07T12:30:00Z",
                "ticker": "ECONOMICS:USNFP",
                "title": "Non Farm Payrolls",
                "actualRaw": None,
                "forecastRaw": 150000,
                "previousRaw": 147000,
            },
            {
                "id": "already-released",
                "date": "2026-07-03T12:30:00Z",
                "ticker": "ECONOMICS:USNFP",
                "actualRaw": 147000,
                "forecastRaw": 120000,
            },
            {
                "id": "future-with-actual",
                "date": "2026-08-12T12:30:00Z",
                "ticker": "ECONOMICS:USIRMM",
                "actualRaw": 0.2,
                "forecastRaw": 0.3,
            },
            {
                "id": "future-no-forecast",
                "date": "2026-08-13T12:30:00Z",
                "ticker": "ECONOMICS:USPPIMM",
                "actualRaw": None,
                "forecastRaw": None,
            },
            {
                "id": "wrong-ticker",
                "date": "2026-08-13T12:30:00Z",
                "ticker": "ECONOMICS:USCPPMM",
                "actualRaw": None,
                "forecastRaw": 0.2,
            },
        ],
    }


def test_only_strict_pre_release_forecast_enters_ledger() -> None:
    frame, excluded = build_pre_release_rows(
        _payload(),
        pd.Timestamp("2026-07-28T12:00:00Z"),
        "raw/snapshot.json",
        "a" * 64,
    )
    assert frame["tradingview_event_id"].tolist() == ["future-valid"]
    assert frame["forecast_value"].tolist() == [150000.0]
    assert frame["capture_semantics"].eq(
        "STRICTLY_PRE_RELEASE_NO_ACTUAL_PRESENT"
    ).all()
    assert excluded == {
        "wrong_ticker": 1,
        "not_strictly_pre_release": 1,
        "actual_already_present": 1,
        "forecast_missing": 1,
    }


def test_event_inside_minimum_lead_is_excluded() -> None:
    payload = {
        "status": "ok",
        "result": [
            {
                "id": "too-close",
                "date": "2026-08-07T12:30:30Z",
                "ticker": "ECONOMICS:USNFP",
                "actualRaw": None,
                "forecastRaw": 100000,
            }
        ],
    }
    frame, excluded = build_pre_release_rows(
        payload,
        pd.Timestamp("2026-08-07T12:30:00Z"),
        "raw/snapshot.json",
        "b" * 64,
    )
    assert frame.empty
    assert excluded["not_strictly_pre_release"] == 1


def test_immutable_writer_refuses_changed_payload(tmp_path) -> None:
    path = tmp_path / "raw" / "snapshot.json"
    write_immutable(path, b"first")
    write_immutable(path, b"first")
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        write_immutable(path, b"changed")


def test_evidence_chain_is_deterministic(tmp_path) -> None:
    raw = tmp_path / "raw" / "a.json"
    metadata = tmp_path / "metadata" / "a.json"
    write_immutable(raw, json.dumps({"a": 1}).encode())
    write_immutable(metadata, json.dumps({"m": 2}).encode())
    first = evidence_chain(tmp_path)
    second = evidence_chain(tmp_path)
    assert first == second
