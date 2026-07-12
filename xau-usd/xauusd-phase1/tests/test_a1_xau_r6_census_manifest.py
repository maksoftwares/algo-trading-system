from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402
import validate_a1_xau_r6_outcome_blind_census as V  # noqa: E402


def test_lock_manifest_and_phase_boundary() -> None:
    V.validate_lock_manifest(ROOT, ROOT / "outputs" / "manifests" / "A1_XAU_R6_CENSUS_LOCK_MANIFEST_V1.json")


def test_detector_is_bound_to_locked_rule_hash() -> None:
    manifest = json.loads((ROOT / "outputs" / "manifests" / "A1_XAU_R6_CENSUS_LOCK_MANIFEST_V1.json").read_text())
    key = "docs/A1_XAU_R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1_RULE_LOCK.json"
    assert R.RULE_SHA256 == manifest["artifacts"][key]["sha256"]


def test_terminal_funnel_reconciles_raw_rows() -> None:
    funnel = {status: 0 for status in R.TERMINAL_STATUSES}
    funnel["IMPULSE_REJECTED"] = 9
    funnel["RAW_OPPORTUNITY_AVAILABLE"] = 2
    V.validate_funnel(funnel, [{}, {}])
    funnel["RAW_OPPORTUNITY_AVAILABLE"] = 1
    with pytest.raises(ValueError, match="raw"):
        V.validate_funnel(funnel, [{}, {}])


def test_calendar_half_bucket_and_zero_filled_windows() -> None:
    values = [datetime(2016, 7, 1), datetime(2021, 6, 30, 23, 59, 59), datetime(2021, 7, 1), datetime(2026, 6, 30)]
    assert [R.annual_bucket(value) for value in values] == [2016, 2020, 2021, 2025]
    report = R.concentration(values)
    assert len(report["july_june"]) == 10
    assert len(report["months"]) == 120
    assert report["best_24_month_share"] == pytest.approx(0.5)


def test_canonical_ids_are_stable_and_order_sensitive() -> None:
    base = datetime(2020, 1, 1)
    bars = [R.Bar(base.replace(hour=4 * i), 1, 2, 1, 1.5) for i in range(6)]
    tick = R.Tick(datetime(2020, 1, 2), 42, 1.1, 1.2)
    contract = R.Contract(0.01, 2, 0.01, 1, 0.01, 0.01, 100, 0, 0)
    first = R.canonical_ids(symbol="XAUUSD", distribution=bars, box_low=1, box_high=2, breakdown_time=datetime(2020, 1, 2), reclaim_time=datetime(2020, 1, 2, 1), entry_tick=tick, contract=contract)
    second = R.canonical_ids(symbol="XAUUSD", distribution=list(reversed(bars)), box_low=1, box_high=2, breakdown_time=datetime(2020, 1, 2), reclaim_time=datetime(2020, 1, 2, 1), entry_tick=tick, contract=contract)
    assert all(len(value) == 64 for value in first)
    assert first != second
