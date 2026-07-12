from __future__ import annotations

import csv
import copy
import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load("build_a1_xau_r6_market_only_native_parity_oracle")
R = _load("run_a1_xau_r6_market_only_native_parity_exact")
V = _load("verify_a1_xau_r6_market_only_native_parity")


def _write_tsv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_contracts_pin_actual_python_router_and_load_directly() -> None:
    source, schema, manifest = V.load_contracts()
    router = V.load_python_router(source)

    assert router.classify_router is not None
    assert source["python_router_authority"]["module_reimplementation_in_np1_b_forbidden"] is True
    assert source["parity_acceptance"] == schema["parity"]["acceptance"]
    assert manifest["dependencies"]["python_router_authority"]["sha256"] == source["python_router_authority"]["sha256"]


def test_source_equivalence_and_safety_fail_closed_on_tamper(tmp_path: Path) -> None:
    generated = tmp_path / B.ORACLE_NAME
    sidecar = tmp_path / "source_equivalence.json"
    B.build_oracle(generated, sidecar)
    assert V.verify_source_equivalence(sidecar, generated) == []

    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["blocks"][0]["exact_equal"] = False
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    assert any("flag false" in error for error in V.verify_source_equivalence(sidecar, generated))


def test_assertion_contract_requires_open_positions_and_pending_orders(tmp_path: Path) -> None:
    _, schema, _ = V.load_contracts()
    contract = schema["native_assertions"]
    required = contract["required_assertion_ids"]
    assert "open_positions_zero" in required
    assert "pending_orders_zero" in required

    path = tmp_path / "native_assertions.tsv"
    rows = [
        {"assertion_id": item, "passed": "true", "observed": "0", "expected": "0", "detail": "ok"}
        for item in required
        if item != "pending_orders_zero"
    ]
    _write_tsv(path, contract["columns"], rows)
    errors = V.verify_assertions(path, schema)
    assert errors == ["required assertion did not pass: pending_orders_zero"]


def test_manifest_policy_is_nonrecursive_and_sidecar_hashes_manifest(tmp_path: Path) -> None:
    _, schema, _ = V.load_contracts()
    schema = {**schema, "exact_tree": ["artifact.txt", "manifest.json", "manifest.sha256"]}
    (tmp_path / "artifact.txt").write_text("locked\n", encoding="utf-8")
    manifest = {
        "artifacts": [
            {
                "relative_path": "artifact.txt",
                "size_bytes": (tmp_path / "artifact.txt").stat().st_size,
                "sha256": V.sha256_file(tmp_path / "artifact.txt"),
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (tmp_path / "manifest.sha256").write_text(V.sha256_file(manifest_path) + "\n", encoding="ascii")

    assert V.verify_nonrecursive_manifest(tmp_path, schema) == []
    manifest["artifacts"].append({"relative_path": "manifest.json", "size_bytes": 0, "sha256": "0" * 64})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any("excluded" in error for error in V.verify_nonrecursive_manifest(tmp_path, schema))


def _bar_rows(schema: dict, timeframe: str, times: list[datetime]) -> list[dict[str, str]]:
    rows = []
    for index, time in enumerate(times):
        price = 1900.0 + index
        rows.append({
            "schema_version": "a1_xau_r6_native_bar_v1", "timeframe": timeframe,
            "open_time_broker": time.isoformat(), "open": str(price), "high": str(price + 1.0),
            "low": str(price - 1.0), "close": str(price + 0.25), "tick_volume": "100",
            "spread": "10", "real_volume": "0",
        })
    assert set(rows[0]) == set(schema["bar_exports"]["columns"])
    return rows


def _synthetic_packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict, dict]:
    source, real_schema, manifest = V.load_contracts()
    schema = copy.deepcopy(real_schema)
    schema["native_router_rows"]["evidence_interval_from_inclusive"] = "2016-07-01T00:00:00"
    schema["native_router_rows"]["evidence_interval_to_exclusive"] = "2016-07-01T08:00:00"
    monkeypatch.setattr(V, "load_contracts", lambda: (source, schema, manifest))
    evidence = tmp_path / "evidence"
    compiled = evidence / "compiled"
    compiled.mkdir(parents=True)
    B.build_oracle(compiled / B.ORACLE_NAME, compiled / "source_equivalence.json")
    (compiled / Path(B.ORACLE_NAME).with_suffix(".ex5").name).write_bytes(b"SYNTHETIC_COMPILE_ONLY_EX5")
    (compiled / "compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log").write_text(
        "MetaEditor executable version: 5.0.0.5833\nResult: 0 errors, 0 warnings\n", encoding="utf-8"
    )
    eq_sha = V.sha256_file(compiled / "source_equivalence.json")
    base = datetime(2016, 7, 1)
    h1_rows = _bar_rows(schema, "H1", [base - timedelta(hours=4) + timedelta(hours=i) for i in range(10)])
    h4_rows = _bar_rows(schema, "H4", [base - timedelta(hours=4), base, base + timedelta(hours=4), base + timedelta(hours=8)])
    d1_rows = _bar_rows(schema, "D1", [base - timedelta(days=3) + timedelta(days=i) for i in range(5)])
    decisions = [base, base + timedelta(hours=4)]
    last_times = [
        (h1_rows[3]["open_time_broker"], h4_rows[0]["open_time_broker"], d1_rows[2]["open_time_broker"]),
        (h1_rows[7]["open_time_broker"], h4_rows[1]["open_time_broker"], d1_rows[2]["open_time_broker"]),
    ]
    router_columns = schema["native_router_rows"]["columns"]
    for run_id in ("run1", "run2"):
        run = evidence / "runs" / run_id
        run.mkdir(parents=True)
        (run / "tester.ini").write_text(R.render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}"), encoding="utf-8")
        (run / "native_report.htm").write_text(
            "<table><tr><td>Total Trades:</td><td>0</td></tr><tr><td>Total Deals:</td><td>0</td></tr></table>", encoding="utf-8"
        )
        _write_tsv(run / "native_h1_bars.tsv", schema["bar_exports"]["columns"], h1_rows)
        _write_tsv(run / "native_h4_bars.tsv", schema["bar_exports"]["columns"], h4_rows)
        _write_tsv(run / "native_d1_bars.tsv", schema["bar_exports"]["columns"], d1_rows)
        native_rows = []
        for decision, (h1_last, h4_last, d1_last) in zip(decisions, last_times):
            row = {column: "" for column in router_columns}
            row.update({
                "schema_version": "a1_xau_r6_native_router_row_v1", "run_id": run_id,
                "timestamp_broker": decision.isoformat(), "symbol": "XAUUSD",
                "router_source_commit": B.SOURCE_COMMIT, "router_source_blob": B.SOURCE_BLOB,
                "source_equivalence_sha256": eq_sha, "h1_bar_count": str(len(h1_rows)),
                "h4_bar_count": str(len(h4_rows)), "d1_bar_count": str(len(d1_rows)),
                "h1_shift1_time": h1_last, "h4_shift1_time": h4_last, "d1_shift1_time": d1_last,
                "data_available": "false", "state_code": "0", "state_name": "unknown", "native_error_code": "0",
            })
            native_rows.append(row)
        _write_tsv(run / "native_router_rows.tsv", router_columns, native_rows)
        contract_columns = schema["contract_snapshot"]["columns"]
        contract = {column: "1" for column in contract_columns}
        contract.update({
            "timestamp_broker": base.isoformat(), "server": "Capital.ComMena-Demo",
            "company": "Capital Com Mena Securities Trading L.L.C", "account_login": "1025742",
            "account_currency": "USD", "account_leverage": "50", "symbol": "XAUUSD",
            "digits": "2", "point": "0.01", "volume_min": "0.01", "volume_step": "0.01",
            "volume_max": "100", "contract_size": "100", "tick_size": "0.01",
            "tick_value": "1", "tick_value_profit": "1", "tick_value_loss": "1",
            "stops_level": "0", "freeze_level": "0", "trade_calc_mode": "0", "trade_mode": "4",
        })
        _write_tsv(run / "native_contract.tsv", contract_columns, [contract])
        probe_columns = schema["native_ordercalcprofit"]["columns"]
        exits = [2002.49, 2002.50, 2002.51, 2024.99, 2025.00, 2025.01, 1997.51, 1997.50, 1997.49, 1975.01, 1975.00, 1974.99]
        probes = []
        for probe_id, exit_price in zip(schema["native_ordercalcprofit"]["required_probe_ids"], exits):
            loss = abs(exit_price - 2000.0)
            probes.append({
                "probe_id": probe_id, "order_type": "SELL" if probe_id.startswith("SELL") else "BUY",
                "symbol": "XAUUSD", "volume": "0.01", "entry_price": "2000", "exit_price": str(exit_price),
                "success": "true", "profit_account_currency": str(-loss), "absolute_loss": str(loss),
                "last_error": "0", "evidence_class": "NATIVE_ORDERCALCPROFIT_PROBE",
            })
        _write_tsv(run / "native_ordercalcprofit.tsv", probe_columns, probes)
        assertion_columns = schema["native_assertions"]["columns"]
        assertions = [
            {"assertion_id": name, "passed": "true", "observed": "0", "expected": "0", "detail": "ok"}
            for name in schema["native_assertions"]["required_assertion_ids"]
        ]
        _write_tsv(run / "native_assertions.tsv", assertion_columns, assertions)
        (run / "order.zero").write_bytes(b"")
        (run / "deal.zero").write_bytes(b"")
    return evidence, source, schema


def test_complete_synthetic_packet_generates_every_artifact_and_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    result = V.finalize_evidence_directory(evidence)

    assert result.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS", result.errors
    assert {path.relative_to(evidence).as_posix() for path in evidence.rglob("*") if path.is_file()} == set(schema["exact_tree"])
    assert V.verify_nonrecursive_manifest(evidence, schema) == []
    assert len(list(csv.DictReader((evidence / "parity" / "router_python_native_parity.csv").open(), delimiter=","))) == 4
    assert len(list(csv.DictReader((evidence / "parity" / "native_prefix_chain_hashes.csv").open(), delimiter=","))) == 4
    assert len(list(csv.DictReader((evidence / "parity" / "ordercalcprofit_python_native_parity.csv").open(), delimiter=","))) == 24


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ("invalid", "R6_NP1_EVIDENCE_INVALID"),
        ("source", "R6_NP1_SOURCE_EQUIVALENCE_FAIL"),
        ("zero", "R6_NP1_ZERO_ACTION_CONTRACT_FAIL"),
        ("parity", "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"),
        ("coverage", "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"),
        ("determinism", "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"),
        ("ordercalc", "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"),
    ],
)
def test_explicit_status_precedence_and_missing_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str, expected_status: str
) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    if mutation == "invalid":
        (evidence / "runs" / "run1" / "native_contract.tsv").unlink()
    elif mutation == "source":
        path = evidence / "compiled" / "source_equivalence.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["blocks"][0]["exact_equal"] = False
        path.write_text(json.dumps(payload), encoding="utf-8")
    elif mutation == "zero":
        (evidence / "runs" / "run1" / "native_report.htm").write_text(
            "<table><tr><td>Total Trades:</td><td>1</td></tr><tr><td>Total Deals:</td><td>1</td></tr></table>", encoding="utf-8"
        )
    elif mutation in {"parity", "coverage"}:
        path = evidence / "runs" / "run1" / "native_router_rows.tsv"
        rows = V.read_tsv(path, schema["native_router_rows"]["columns"])
        if mutation == "parity":
            rows[0]["state_name"], rows[0]["state_code"] = "shock", "1"
        else:
            rows.pop()
        _write_tsv(path, schema["native_router_rows"]["columns"], rows)
    elif mutation == "determinism":
        path = evidence / "runs" / "run2" / "native_h4_bars.tsv"
        rows = V.read_tsv(path, schema["bar_exports"]["columns"])
        rows[0]["close"] = str(float(rows[0]["close"]) + 0.1)
        _write_tsv(path, schema["bar_exports"]["columns"], rows)
    else:
        path = evidence / "runs" / "run1" / "native_ordercalcprofit.tsv"
        rows = V.read_tsv(path, schema["native_ordercalcprofit"]["columns"])
        rows[0]["absolute_loss"] = str(float(rows[0]["absolute_loss"]) + 0.01)
        _write_tsv(path, schema["native_ordercalcprofit"]["columns"], rows)

    result = V.finalize_evidence_directory(evidence)
    assert result.status == expected_status
