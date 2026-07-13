from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r2_mode27_prehistory_overlap_controls_exact as runner


def test_locked_complete_package_has_exact_five_controls() -> None:
    assert runner.RUNNER_COMPLETE is True
    assert runner.HISTORICAL_RUN_AUTHORIZED is False
    assert tuple(spec.control_id for spec in runner.CONTROL_SPECS) == runner.EXPECTED_CONTROL_IDS
    assert len(runner.CONTROL_SPECS) == 5
    assert runner.FROM_DATE == "2016.01.01"
    assert runner.TO_DATE == "2021.12.31"
    assert runner.TESTER_DEPOSIT == "1000"
    assert runner.TESTER_CURRENCY == "USD"


def test_authoritative_variant_inputs_equal_frozen_hashes_without_overlay() -> None:
    selected = runner.resolve_variants()
    assert set(selected) == set(runner.EXPECTED_CONTROL_IDS)
    for spec in runner.CONTROL_SPECS:
        authoritative = [
            variant
            for variant in spec.source_module.build_variants()
            if variant.name == spec.variant_name
        ]
        assert len(authoritative) == 1
        assert selected[spec.control_id].tester_inputs == authoritative[0].tester_inputs
        assert runner.stable_hash(selected[spec.control_id].tester_inputs) == spec.input_sha256


def test_static_checks_and_expected_mode27_filenames_are_exact() -> None:
    assert all(runner.static_checks().values())
    expected = {
        f"A1_XAU_R2_CONTROL_PREHISTORY_201601_202112_{control}_NORMALIZED_TRADES.csv"
        for control in runner.EXPECTED_CONTROL_IDS
    }
    assert {spec.normalized_path.name for spec in runner.CONTROL_SPECS} == expected
    assert runner.MANIFEST_PATH.name == (
        "A1_XAU_R2_CONTROL_PREHISTORY_201601_202112_PROVENANCE.json"
    )


def test_authorized_history_path_reaches_mt5_after_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def authorized_run(**_kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        raise RuntimeError("authorized MT5 sentinel")

    monkeypatch.setattr(runner, "HISTORICAL_RUN_AUTHORIZED", True)
    monkeypatch.setattr(runner.mt5, "run_variants", authorized_run)
    with pytest.raises(RuntimeError, match="authorized MT5 sentinel"):
        runner.run_historical_package(1)
    assert called is True


def test_normalized_writer_marks_every_row_with_provenance(tmp_path: Path) -> None:
    spec = runner.CONTROL_SPECS[0]
    variant = runner.resolve_variants()[spec.control_id]
    raw = [
        {
            "component": "component",
            "source_id": "source",
            "entry_time": datetime(2018, 1, 2, 3, 4, 5),
            "entry_date": date(2018, 1, 2),
            "exit_time": datetime(2018, 1, 2, 4, 4, 5),
            "exit_date": date(2018, 1, 2),
            "direction": "SHORT",
            "pnl_usd": 2.5,
            "tickets": 1,
            "lots": 0.01,
        }
    ]
    rows = runner.provenance_for_rows(
        spec,
        variant,
        raw,
        source_runner_sha256="a" * 64,
        ea_sha256="b" * 64,
        generated_at_utc="2026-07-10T00:00:00Z",
    )
    path = tmp_path / "normalized.csv"
    runner.write_normalized_ledger(path, rows)
    with path.open(encoding="utf-8", newline="") as handle:
        written = list(csv.DictReader(handle))
    assert len(written) == 1
    assert written[0]["control_id"] == spec.control_id
    assert written[0]["control_variant"] == variant.name
    assert written[0]["control_input_sha256"] == spec.input_sha256
    assert written[0]["control_ea_sha256"] == "b" * 64
    assert written[0]["control_manifest"].endswith(runner.MANIFEST_PATH.name)


def test_execution_reconciliation_is_exact_and_fail_closed(
    tmp_path: Path,
) -> None:
    trade_csv = tmp_path / "trades.csv"
    trade_csv.write_text("entry_time\n2018-01-02 03:04:05\n", encoding="utf-8")
    order_csv = tmp_path / "orders.csv"
    order_csv.write_text("action\tretcode\tretcode_description\nORDER_SEND_OK\t\t\n", encoding="utf-8")
    spec = runner.CONTROL_SPECS[0]
    variant = runner.resolve_variants()[spec.control_id]
    result = {
        "name": variant.name,
        "trade_csv": str(trade_csv),
        "order_csv": str(order_csv),
        "order_activity": {"actions": {"ORDER_SEND_OK": 1}},
        "mt5_report_metrics": {"Total Trades": "1"},
        "summary": {"overall": {"trades": 1}},
    }
    rows = [
        {
            "entry_date": date(2018, 1, 2),
            "exit_time": datetime(2018, 1, 2, 4, 0),
            "direction": "SHORT",
        }
    ]
    reconciled = runner.execution_reconciliation(spec, variant, result, rows)
    assert reconciled["ready"] is True
    assert all(reconciled["checks"].values())

    result["order_activity"]["actions"]["ORDER_SEND_OK"] = 2
    failed = runner.execution_reconciliation(spec, variant, result, rows)
    assert failed["ready"] is False
    assert failed["checks"]["successful_sends_match_mt5"] is False


def test_runner_source_keeps_lock_before_mt5_and_no_variant_input_overlay() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    lock = source.index("if not HISTORICAL_RUN_AUTHORIZED:")
    mt5_call = source.index("mt5_payload = mt5.run_variants(")
    assert lock < mt5_call
    assert "variant.tester_inputs.update" not in source
    assert "tester_inputs={**" not in source
