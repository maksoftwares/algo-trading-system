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


def contract() -> R.Contract:
    return R.Contract(
        account_currency="USD", account_leverage=50, margin_mode=2,
        server="Capital.ComMena-Demo", symbol="XAUUSD", point=0.01, digits=2,
        tick_size=0.01, tick_value=1.0, tick_value_loss=1.0,
        volume_min=0.01, volume_step=0.01, volume_max=1000.0,
        contract_size=100.0, stops_level=0, freeze_level=0,
    )


def test_lock_manifest_and_phase_boundary() -> None:
    V.validate_lock_manifest(ROOT, ROOT / "outputs" / "manifests" / "A1_XAU_R6_CENSUS_LOCK_MANIFEST_V1.json")


def test_native_fixture_manifest_and_provenance_roots() -> None:
    payload = V.validate_native_fixture_manifest(
        ROOT, ROOT / "tests" / "fixtures" / "A1_XAU_R6_NATIVE_FIXTURE_MANIFEST_V1.json",
    )
    assert payload["phase_boundary"] == {
        "market_only": True,
        "real_census_authorized": False,
        "pnl_authorized": False,
        "mt5_execution_authorized": False,
        "h4_or_portfolio_join_authorized": False,
        "runtime_or_broker_action_authorized": False,
    }


def test_detector_is_bound_to_locked_rule_hash() -> None:
    manifest = json.loads((ROOT / "outputs" / "manifests" / "A1_XAU_R6_CENSUS_LOCK_MANIFEST_V1.json").read_text())
    key = "docs/A1_XAU_R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1_RULE_LOCK.json"
    assert R.RULE_SHA256 == manifest["artifacts"][key]["sha256"]


def test_terminal_funnel_reconciles_raw_rows() -> None:
    funnel = {status: 0 for status in R.TERMINAL_STATUSES}
    funnel["IMPULSE_REJECTED"] = 9
    anchors = [R.TerminalAnchor(datetime(2020, 1, index + 1), datetime(2020, 1, index + 2), "IMPULSE_REJECTED") for index in range(9)]
    V.validate_funnel(funnel, [], anchors, R.incidence_report([]))
    funnel["IMPULSE_REJECTED"] = 8
    with pytest.raises(ValueError, match="anchor"):
        V.validate_funnel(funnel, [], anchors, R.incidence_report([]))


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
    snapshot = contract()
    first = R.canonical_ids(symbol="XAUUSD", distribution=bars, box_low=1, box_high=2, breakdown_time=datetime(2020, 1, 2), reclaim_time=datetime(2020, 1, 2, 1), entry_tick=tick, contract=snapshot)
    second = R.canonical_ids(symbol="XAUUSD", distribution=list(reversed(bars)), box_low=1, box_high=2, breakdown_time=datetime(2020, 1, 2), reclaim_time=datetime(2020, 1, 2, 1), entry_tick=tick, contract=snapshot)
    assert all(len(value) == 64 for value in first)
    assert first != second


def incidence_rows(*, reference: bool, deployment: bool) -> list[dict[str, object]]:
    rows = []
    for year in range(2016, 2026):
        for month_offset in range(12):
            month = ((7 - 1 + month_offset) % 12) + 1
            calendar_year = year if month >= 7 else year + 1
            rows.append({
                "entry_tick_time": datetime(calendar_year, month, 15).isoformat(timespec="seconds"),
                "reference_risk_feasible": reference,
                "deployment_risk_feasible": deployment,
            })
    return rows


def test_all_locked_incidence_gates_and_status_precedence() -> None:
    empty = R.incidence_report([])
    assert R.locked_final_status(empty, evidence_valid=False) == "R6_CENSUS_EVIDENCE_INVALID"
    assert R.locked_final_status(empty) == "R6_CENSUS_INSUFFICIENT_INCIDENCE"
    reference_fail = R.incidence_report(incidence_rows(reference=False, deployment=False))
    assert reference_fail["raw"]["passes"]
    assert R.locked_final_status(reference_fail) == "R6_CENSUS_REFERENCE_RISK_UNDERPOWERED"
    deployment_fail = R.incidence_report(incidence_rows(reference=True, deployment=False))
    assert R.locked_final_status(deployment_fail) == "R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE"
    passed = R.incidence_report(incidence_rows(reference=True, deployment=True))
    assert passed["raw"]["qualifying_july_june_buckets"] == 10
    assert passed["raw"]["largest_july_june_bucket_share"] == pytest.approx(0.1)
    assert passed["raw"]["best_contiguous_24_month_share"] == pytest.approx(0.2)
    assert R.locked_final_status(passed) == "R6_CENSUS_PASS"


def test_validate_detection_rejects_unreviewed_final_status() -> None:
    incidence = R.incidence_report([])
    detection = R.Detection(
        (), {status: 0 for status in R.TERMINAL_STATUSES}, (), incidence, "R6_CENSUS_PASS", {},
    )
    schema = json.loads((ROOT / "docs" / "A1_XAU_R6_OUTCOME_BLIND_CENSUS_SCHEMA_V1.json").read_text())
    with pytest.raises(ValueError, match="final status"):
        V.validate_detection(detection, schema)
