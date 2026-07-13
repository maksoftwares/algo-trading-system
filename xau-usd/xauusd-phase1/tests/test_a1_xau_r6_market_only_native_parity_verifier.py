from __future__ import annotations

import csv
import copy
import importlib.util
import json
import hashlib
import platform
import subprocess
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
    errors = V.verify_assertions(path, schema, "run1")
    assert "required assertion did not pass: pending_orders_zero" in errors


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


def _synthetic_packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, available: bool = False) -> tuple[Path, dict, dict]:
    real_source, real_schema, manifest = V.load_contracts()
    source = copy.deepcopy(real_source)
    schema = copy.deepcopy(real_schema)
    schema["native_router_rows"]["evidence_interval_from_inclusive"] = "2016-07-01T00:00:00"
    schema["native_router_rows"]["evidence_interval_to_exclusive"] = "2016-07-01T08:00:00"
    synthetic_start = datetime(2016, 7, 1) - (timedelta(days=309) if available else timedelta(days=3))
    source["tester_environment"]["test_from_inclusive_broker_time"] = synthetic_start.isoformat()
    source["tester_environment"]["test_to_exclusive_broker_time"] = "2016-07-01T08:00:00"
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
    if available:
        h1_times = [synthetic_start + timedelta(hours=i) for i in range(int((base + timedelta(hours=8) - synthetic_start).total_seconds() // 3600))]
        h4_times = [synthetic_start + timedelta(hours=4 * i) for i in range(int((base + timedelta(hours=8) - synthetic_start).total_seconds() // (4 * 3600)))]
        d1_times = [synthetic_start + timedelta(days=i) for i in range(310)]
    else:
        h1_times = [synthetic_start + timedelta(hours=i) for i in range(80)]
        h4_times = [synthetic_start + timedelta(hours=4 * i) for i in range(20)]
        d1_times = [synthetic_start + timedelta(days=i) for i in range(4)]
    h1_rows = _bar_rows(schema, "H1", h1_times)
    h4_rows = _bar_rows(schema, "H4", h4_times)
    d1_rows = _bar_rows(schema, "D1", d1_times)
    decisions = [base, base + timedelta(hours=4)]
    last_times = [
        ((base - timedelta(hours=1)).isoformat(), (base - timedelta(hours=4)).isoformat(), (base - timedelta(days=1)).isoformat()),
        ((base + timedelta(hours=3)).isoformat(), base.isoformat(), (base - timedelta(days=1)).isoformat()),
    ]
    router_columns = schema["native_router_rows"]["columns"]
    for run_id in ("run1", "run2"):
        run = evidence / "runs" / run_id
        run.mkdir(parents=True)
        (run / "tester.ini").write_text(R.render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}"), encoding="utf-8")
        inputs = " ".join(f"{key}={value}" for key, value in R.parse_ini_exact(R.render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}"))["TesterInputs"].items())
        report_fields = {
            "Expert": "A1XauR6MarketOnlyNativeParityOracle", "Symbol": "XAUUSD",
            "Period": "M5 (2015.06.01 - 2026.07.01)",
            "Model": "Every tick based on real ticks", "Initial Deposit": "10000.00 USD", "Leverage": "1:50",
            "Bars": "1000", "Ticks": "10000", "Total Trades": "0", "Total Deals": "0",
        }
        report_html = "<table>" + "".join(f"<tr><td>{key}:</td><td>{value}</td></tr>" for key, value in report_fields.items()) + f"</table><p>{inputs}</p>"
        (run / "native_report.htm").write_text(report_html, encoding="utf-8")
        _write_tsv(run / "native_h1_bars.tsv", schema["bar_exports"]["columns"], h1_rows)
        _write_tsv(run / "native_h4_bars.tsv", schema["bar_exports"]["columns"], h4_rows)
        _write_tsv(run / "native_d1_bars.tsv", schema["bar_exports"]["columns"], d1_rows)
        native_rows = []
        router = V.load_python_router(source)
        h1_bars = [router.Bar(datetime.fromisoformat(row["open_time_broker"]), *(float(row[name]) for name in ("open", "high", "low", "close"))) for row in h1_rows]
        h4_bars = [router.Bar(datetime.fromisoformat(row["open_time_broker"]), *(float(row[name]) for name in ("open", "high", "low", "close"))) for row in h4_rows]
        d1_bars = [router.Bar(datetime.fromisoformat(row["open_time_broker"]), *(float(row[name]) for name in ("open", "high", "low", "close"))) for row in d1_rows]
        for decision, (h1_last, h4_last, d1_last) in zip(decisions, last_times):
            row = {column: "" for column in router_columns}
            row.update({
                "schema_version": "a1_xau_r6_native_router_row_v1", "run_id": run_id,
                "timestamp_broker": decision.isoformat(), "symbol": "XAUUSD",
                "router_source_commit": B.SOURCE_COMMIT, "router_source_blob": B.SOURCE_BLOB,
                "source_equivalence_sha256": eq_sha,
                "h1_bar_count": str(sum(datetime.fromisoformat(item["open_time_broker"]) <= decision for item in h1_rows)),
                "h4_bar_count": str(sum(datetime.fromisoformat(item["open_time_broker"]) <= decision for item in h4_rows)),
                "d1_bar_count": str(sum(datetime.fromisoformat(item["open_time_broker"]) <= decision for item in d1_rows)),
                "h1_shift1_time": h1_last, "h4_shift1_time": h4_last, "d1_shift1_time": d1_last,
                "data_available": "false", "state_code": "0", "state_name": "unknown", "native_error_code": "0",
            })
            if available:
                state, metrics = V.python_metrics(router, h1_bars, h4_bars, d1_bars, decision)
                assert state != "UNKNOWN"
                h1_i, h4_i, d1_i = (router._last_completed_index(bars, decision) for bars in (h1_bars, h4_bars, d1_bars))
                row.update({key: format(value, ".17g") for key, value in metrics.items()})
                row.update({
                    "h1_shift1_high": format(h1_bars[h1_i].high, ".17g"),
                    "h1_shift1_low": format(h1_bars[h1_i].low, ".17g"),
                    "h1_shift1_range": format(h1_bars[h1_i].high - h1_bars[h1_i].low, ".17g"),
                    "h4_close_shift1": format(h4_bars[h4_i].close, ".17g"),
                    "d1_close_shift1": format(d1_bars[d1_i].close, ".17g"),
                    "d1_close_shift2": format(d1_bars[d1_i - 1].close, ".17g"),
                    "data_available": "true", "state_code": str(V.STATE_CODES[state]), "state_name": state.lower(),
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
        expected_inputs = R.parse_ini_exact(R.render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}"))["TesterInputs"]
        assertions.extend(
            {"assertion_id": f"effective_input_{key}", "passed": "true", "observed": value, "expected": value, "detail": ""}
            for key, value in expected_inputs.items()
        )
        fixed_constants = {
            "InpTargetSymbol": "XAUUSD", "InpAtrPeriod": "14", "InpRegimeFastEmaPeriod": "20",
            "InpRegimeSlowEmaPeriod": "50", "InpRegimeSlopeLagBars": "5",
            "InpRegimePersistenceD1Bars": "2", "InpRegimeRequireH4Confirm": "true",
            "InpRegimeShockH1RangeAtrMultiple": "3", "InpRegimeShockD1AtrLookback": "60",
            "InpRegimeShockD1AtrPercentileMin": "95", "InpRegimeCompressionBoxDays": "5",
            "InpRegimeCompressionD1AtrPercentileMax": "30", "InpRegimeCompressionRangeMedianMax": "1",
        }
        assertions.extend(
            {"assertion_id": f"fixed_constant_{key}", "passed": "true", "observed": value, "expected": value, "detail": ""}
            for key, value in fixed_constants.items()
        )
        environment = {
            "environment_mql_tester": "true", "environment_symbol": "XAUUSD", "environment_period": "PERIOD_M5",
            "environment_account_login": "1025742", "environment_server": "Capital.ComMena-Demo",
            "environment_company": "Capital Com Mena Securities Trading L.L.C", "environment_currency": "USD",
            "environment_leverage": "50", "environment_terminal_build": "5833",
        }
        assertions.extend(
            {"assertion_id": key, "passed": "true", "observed": value, "expected": value, "detail": ""}
            for key, value in environment.items()
        )
        _write_tsv(run / "native_assertions.tsv", assertion_columns, assertions)
        (run / "order.zero").write_bytes(b"")
        (run / "deal.zero").write_bytes(b"")
    return evidence, source, schema


def _attestation(evidence: Path) -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()
    empty = hashlib.sha256(b"").hexdigest()
    artifact_hashes = V.attested_artifact_hashes(evidence)
    ex5 = evidence / "compiled" / Path(B.ORACLE_NAME).with_suffix(".ex5").name
    command = lambda values: {"command": values, "exit_code": 0, "stdout_base64": "", "stderr_base64": "", "stdout_sha256": empty, "stderr_sha256": empty}
    head, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    return {
        "schema_version": "a1_xau_np1_exact_commit_attestation_v1", "git_head": git("rev-parse", "HEAD"),
        "git_tree": tree, "git_status_porcelain": "", "os": platform.platform(),
        "architecture": platform.machine(), "python_version": platform.python_version(), "python_executable": sys.executable,
        "dependency_versions": {"python_implementation": platform.python_implementation(), "pytest": pytest.__version__, "third_party_runtime_dependencies": {}},
        "mt5_terminal_build": 5833, "metaeditor_version": "5.0.0.5833",
        "same_ex5_sha256_run1_run2": V.sha256_file(ex5),
        "history_stability": {
            "status": "NP1_RETRY_HISTORY_STABLE",
            "same_ex5_sha256_warmup_run1_run2": V.sha256_file(ex5),
            "warmup_artifact_sha256": {"native_report.htm": "d" * 64},
            "official_fingerprints": {"contract_sha256": V.sha256_file(V.RETRY_CONTRACT), "runs": {}},
        },
        "commands": [
            command(["MetaEditor64.exe", "/compile:oracle", "/log:compile.log"]),
            command(["terminal64.exe", "/portable", "/config:np1_warmup.ini"]),
            command(["terminal64.exe", "/portable", "/config:np1_run1.ini"]),
            command(["terminal64.exe", "/portable", "/config:np1_run2.ini"]),
            command([sys.executable, str(SCRIPTS / "verify_a1_xau_r6_market_only_native_parity.py"), str(evidence), "--finalize", "--attestation-json", "attestation.json", "--quiet"]),
            command([sys.executable, str(SCRIPTS / "verify_a1_xau_r6_market_only_native_parity.py"), str(evidence), "--quiet"]),
        ],
        "artifact_sha256": artifact_hashes,
        "review_authority": {"controlling_review_artifact": "A1_XAU_NP1B4_PASS_REVIEW_TEST.md", "controlling_review_sha256": "c" * 64,
                             "reviewed_generator_commit": head, "reviewed_generator_tree": tree,
                             "authorization_status": "AUTHORIZED", "review_verdict": "PASS"},
        "environment": {"cwd": str(ROOT), "timezone": "test", "account_login": 1025742,
                        "server": "Capital.ComMena-Demo", "currency": "USD", "leverage": "1:50", "symbol": "XAUUSD"},
    }


def _finalize(evidence: Path):
    attestation = _attestation(evidence)
    V.finalize_evidence_directory(evidence, attestation=attestation)
    attestation["artifact_sha256"] = V.attested_artifact_hashes(evidence)
    return V.finalize_evidence_directory(evidence, attestation=attestation)


def test_complete_synthetic_packet_generates_every_artifact_and_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    result = _finalize(evidence)

    assert result.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS", result.errors
    assert {path.relative_to(evidence).as_posix() for path in evidence.rglob("*") if path.is_file()} == set(schema["exact_tree"])
    assert V.verify_nonrecursive_manifest(evidence, schema) == []
    assert len(list(csv.DictReader((evidence / "parity" / "router_python_native_parity.csv").open(), delimiter=","))) == 4
    assert len(list(csv.DictReader((evidence / "parity" / "native_prefix_chain_hashes.csv").open(), delimiter=","))) == 4
    assert len(list(csv.DictReader((evidence / "parity" / "ordercalcprofit_python_native_parity.csv").open(), delimiter=","))) == 24
    summary = next(csv.DictReader((evidence / "parity" / "router_state_summary.csv").open(), delimiter=","))
    assert {"state_exact_match_rate", "data_availability_exact_match_rate", "first_mismatch_timestamp", "first_mismatch_field", "mismatch_count_by_native_state"} <= set(summary)


def _verbatim_build_5833_report_fragment() -> str:
    # Verbatim relevant rows from committed Capital.com Build-5833 report:
    # outputs/reports/A1_XAU_FEE_NATIVE_REPLAYS_EXACT_20260710/runs/
    # h4_d1_long_best_box2_atr80/A1_XAU_FEE_NATIVE_REPLAY_H4_D1_LONG_BEST_BOX2_ATR80.htm
    return """<table>
   <tr align="right">
      <td nowrap colspan="3">Expert:</td>
      <td nowrap colspan="10" align="left"><b>A1XauFeeEvidence_d15fc9a6</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3">Symbol:</td>
      <td nowrap colspan="10" align="left"><b>XAUUSD</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3">Period:</td>
      <td nowrap colspan="10" align="left"><b>M5 (2022.07.01 - 2026.06.30)</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3" >Initial Deposit:</td>
      <td nowrap colspan="10" align="left"><b>1 000.00</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3" >Leverage:</td>
      <td nowrap colspan="10" align="left"><b>1:50</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3">Bars:</td>
      <td nowrap><b>282644</b></td>
      <td nowrap colspan="3">Ticks:</td>
      <td nowrap><b>204204660</b></td>
      <td nowrap colspan="3">Symbols:</td>
      <td nowrap colspan="2"><b>1</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3">Total Trades:</td>
      <td nowrap><b>145</b></td>
   </tr>
   <tr align="right">
      <td nowrap colspan="3">Total Deals:</td>
      <td nowrap><b>290</b></td>
   </tr>
</table>"""


def test_real_mt5_report_shape_and_locked_iso_timestamp_contract(tmp_path: Path) -> None:
    report = tmp_path / "native_report.htm"
    report.write_text(_verbatim_build_5833_report_fragment(), encoding="utf-8")
    parsed = V.parse_native_report(report)
    assert parsed["expert"] == "A1XauFeeEvidence_d15fc9a6"
    assert parsed["period"] == "M5 (2022.07.01 - 2026.06.30)"
    assert parsed["bars"] == 282644 and parsed["ticks"] == 204204660
    assert parsed["total_trades"] == 145 and parsed["total_deals"] == 290
    assert parsed["model"] == ""
    assert V._dt("2016-07-01T00:00:00") == datetime(2016, 7, 1)
    with pytest.raises(ValueError, match="locked ISO"):
        V._dt("2016.07.01 00:00:00")


def test_native_report_accepts_configured_todate_and_rejects_other_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, _, _ = _synthetic_packet(tmp_path, monkeypatch)
    assert _finalize(evidence).status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS"
    for run_id in ("run1", "run2"):
        path = evidence / "runs" / run_id / "native_report.htm"
        path.write_text(path.read_text(encoding="utf-8").replace("2026.07.01", "2026.06.30"), encoding="utf-8")
    result = _finalize(evidence)
    assert result.status == "R6_NP1_EVIDENCE_INVALID"
    assert any("native report period mismatch" in error for error in result.errors)


@pytest.mark.parametrize("duplicate_value", ["282644", "999999"])
def test_native_report_rejects_duplicate_or_conflicting_labels(tmp_path: Path, duplicate_value: str) -> None:
    report = tmp_path / "native_report.htm"
    duplicate = f'<tr><td nowrap colspan="3">Bars:</td><td nowrap><b>{duplicate_value}</b></td></tr>'
    report.write_text(_verbatim_build_5833_report_fragment().replace("</table>", duplicate + "</table>"), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate/conflicting Bars"):
        V.parse_native_report(report)


def test_exact_session_whitelist_contains_weekend_maintenance_and_holiday_rows() -> None:
    contract, allowed = V.load_retry_contracts()
    assert contract["session_gap_policy"]["mode"] == "EXACT_INTERVAL_WHITELIST"
    assert ("2015-06-05T20:00:00", "2015-06-07T22:00:00") in allowed["H1"]
    assert ("2015-06-01T20:00:00", "2015-06-01T22:00:00") in allowed["H1"]
    assert any(first.startswith("2015-12-2") and (datetime.fromisoformat(second) - datetime.fromisoformat(first)) > timedelta(days=1) for first, second in allowed["H1"])


def test_exact_whitelist_accepts_listed_gap_and_rejects_unlisted_or_missing(tmp_path: Path) -> None:
    _, schema, _ = V.load_contracts()
    router = V.load_python_router(V.load_contracts()[0])
    start, end = datetime(2015, 6, 5, 20), datetime(2015, 6, 8, 0)
    listed = ("2015-06-05T20:00:00", "2015-06-07T22:00:00")
    rows = _bar_rows(schema, "H1", [start, datetime(2015, 6, 7, 22), datetime(2015, 6, 7, 23)])
    path = tmp_path / "native_h1_bars.tsv"
    _write_tsv(path, schema["bar_exports"]["columns"], rows)
    V.load_bar_rows(path, schema, router, timeframe="H1", test_start=start, test_end=end, allowed_session_gaps={listed}, require_exact_session_gaps=True)
    with pytest.raises(ValueError, match="unlisted"):
        V.load_bar_rows(path, schema, router, timeframe="H1", test_start=start, test_end=end, allowed_session_gaps=set())
    continuous = _bar_rows(schema, "H1", [start + timedelta(hours=i) for i in range(52)])
    _write_tsv(path, schema["bar_exports"]["columns"], continuous)
    with pytest.raises(ValueError, match="listed market-history gap missing"):
        V.load_bar_rows(path, schema, router, timeframe="H1", test_start=start, test_end=end, allowed_session_gaps={listed}, require_exact_session_gaps=True)


def test_retry_lock_ignores_occurrence_count_and_fails_closed_on_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(V, "ROOT", tmp_path)
    contract_path = tmp_path / "docs" / "contract.json"
    source_path = tmp_path / "analysis" / "gaps.csv"
    manifest_path = tmp_path / "outputs" / "manifest.json"
    contract_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    manifest_path.parent.mkdir(parents=True)
    source_path.write_text(
        "timeframe,prior_bar_time,next_bar_time,present_in_run1,present_in_run2,occurrence_count\n"
        "H1,2020-01-01T00:00:00,2020-01-01T02:00:00,true,true,999\n"
        "H4,2020-01-01T00:00:00,2020-01-01T08:00:00,true,true,2\n"
        "D1,2020-01-03T00:00:00,2020-01-06T00:00:00,true,true,2\n",
        encoding="utf-8",
    )
    contract = {
        "schema_version": "a1_xau_r6_capitalcom_session_and_history_stability_contract_v1",
        "session_gap_policy": {
            "mode": "EXACT_INTERVAL_WHITELIST", "allowed_interval_filter": {"ignore_columns": ["occurrence_count"]},
            "source": {"path": "analysis/gaps.csv", "sha256": V.sha256_file(source_path)},
        },
        "source_artifacts": {},
    }
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    manifest = {
        "schema_version": "a1_xau_r6_np1_retry_lock_manifest_v1",
        "artifacts": {"docs/contract.json": {"sha256": V.sha256_file(contract_path), "size_bytes": contract_path.stat().st_size}},
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _, allowed = V.load_retry_contracts(contract_path, manifest_path)
    assert ("2020-01-01T00:00:00", "2020-01-01T02:00:00") in allowed["H1"]
    source_path.write_text(source_path.read_text(encoding="utf-8").replace(",999", ",1"), encoding="utf-8")
    with pytest.raises(RuntimeError, match="source hash mismatch"):
        V.load_retry_contracts(contract_path, manifest_path)
    source_path.write_text(source_path.read_text(encoding="utf-8").replace(",1", ",999"), encoding="utf-8")
    manifest["artifacts"]["docs/contract.json"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="retry-manifest mismatch"):
        V.load_retry_contracts(contract_path, manifest_path)


@pytest.mark.parametrize("mutation", ["report_ticks", "bar_hash", "negative_spread"])
def test_official_history_instability_stops_before_finalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    evidence, source, _ = _synthetic_packet(tmp_path, monkeypatch)
    contract = {
        "configured_period": {
            "native_report_period": "M5 (2015.06.01 - 2026.07.01)",
            "test_from_inclusive_broker_time": source["tester_environment"]["test_from_inclusive_broker_time"],
            "test_to_exclusive_broker_time": source["tester_environment"]["test_to_exclusive_broker_time"],
        }
    }
    monkeypatch.setattr(V, "load_retry_contracts", lambda: (contract, {"H1": set(), "H4": set(), "D1": set()}))
    assert V.official_history_fingerprints(evidence)["status"] == "NP1_RETRY_HISTORY_STABLE"
    if mutation == "report_ticks":
        path = evidence / "runs" / "run2" / "native_report.htm"
        path.write_text(path.read_text(encoding="utf-8").replace("Ticks:</td><td>10000", "Ticks:</td><td>10001"), encoding="utf-8")
    else:
        path = evidence / "runs" / "run2" / "native_h1_bars.tsv"
        rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
        rows[0]["close" if mutation == "bar_hash" else "spread"] = "999" if mutation == "bar_hash" else "-1"
        _write_tsv(path, list(rows[0]), rows)
    with pytest.raises(RuntimeError, match="NP1_RETRY_HISTORY_NOT_STABLE"):
        V.official_history_fingerprints(evidence)


@pytest.mark.parametrize("surface", ["bar", "router"])
def test_bar_and_router_exclusive_boundary_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, surface: str,
) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    for run_id in ("run1", "run2"):
        if surface == "bar":
            path = evidence / "runs" / run_id / "native_h1_bars.tsv"
            rows = V.read_tsv(path, schema["bar_exports"]["columns"])
            rows.append({**rows[-1], "open_time_broker": "2016-07-01T08:00:00"})
            _write_tsv(path, schema["bar_exports"]["columns"], rows)
        else:
            path = evidence / "runs" / run_id / "native_router_rows.tsv"
            rows = V.read_tsv(path, schema["native_router_rows"]["columns"])
            rows[-1]["timestamp_broker"] = "2016-07-01T08:00:00"
            _write_tsv(path, schema["native_router_rows"]["columns"], rows)
    result = _finalize(evidence)
    assert result.status == "R6_NP1_EVIDENCE_INVALID"
    assert any("exclusive evidence boundary" in error for error in result.errors)


def test_available_state_fixture_exercises_numeric_router_parity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, _, _ = _synthetic_packet(tmp_path, monkeypatch, available=True)
    result = _finalize(evidence)
    assert result.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS", result.errors
    rows = list(csv.DictReader((evidence / "parity" / "router_python_native_parity.csv").open(), delimiter=","))
    assert rows and all(row["native_data_available"] == "true" for row in rows)
    assert all(row["state_exact_match"] == "true" for row in rows)


def test_postcommit_verifier_is_strictly_read_only_and_does_not_heal_tamper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, _, _ = _synthetic_packet(tmp_path, monkeypatch)
    finalized = _finalize(evidence)
    assert finalized.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS"
    before = {path.relative_to(evidence).as_posix(): path.read_bytes() for path in evidence.rglob("*") if path.is_file()}
    verified = V.verify_evidence_directory(evidence)
    after = {path.relative_to(evidence).as_posix(): path.read_bytes() for path in evidence.rglob("*") if path.is_file()}
    assert verified.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS", verified.errors
    assert after == before

    derived = evidence / "parity" / "router_state_summary.csv"
    derived.write_bytes(derived.read_bytes() + b"tamper\n")
    tampered = derived.read_bytes()
    rejected = V.verify_evidence_directory(evidence)
    assert rejected.status == "R6_NP1_EVIDENCE_INVALID"
    assert derived.read_bytes() == tampered


@pytest.mark.parametrize("mutation", ["truncated_history", "native_input", "exact_probe", "malformed_contract"])
def test_malformed_native_contracts_resolve_to_typed_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    if mutation == "truncated_history":
        path = evidence / "runs" / "run1" / "native_h1_bars.tsv"
        rows = V.read_tsv(path, schema["bar_exports"]["columns"])[1:]
        _write_tsv(path, schema["bar_exports"]["columns"], rows)
    elif mutation == "native_input":
        path = evidence / "runs" / "run1" / "native_assertions.tsv"
        rows = V.read_tsv(path, schema["native_assertions"]["columns"])
        next(row for row in rows if row["assertion_id"] == "effective_input_InpRunId")["observed"] = "wrong"
        _write_tsv(path, schema["native_assertions"]["columns"], rows)
    elif mutation == "exact_probe":
        path = evidence / "runs" / "run1" / "native_ordercalcprofit.tsv"
        rows = V.read_tsv(path, schema["native_ordercalcprofit"]["columns"])
        rows[0]["order_type"] = "BUY"
        _write_tsv(path, schema["native_ordercalcprofit"]["columns"], rows)
    else:
        path = evidence / "runs" / "run1" / "native_contract.tsv"
        rows = V.read_tsv(path, schema["contract_snapshot"]["columns"])
        rows[0]["tick_size"] = "not-a-number"
        _write_tsv(path, schema["contract_snapshot"]["columns"], rows)
    result = _finalize(evidence)
    assert result.status == "R6_NP1_EVIDENCE_INVALID", result.errors


def test_long_weekend_spanning_history_gap_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch, available=True)
    for run_id in ("run1", "run2"):
        path = evidence / "runs" / run_id / "native_h1_bars.tsv"
        rows = V.read_tsv(path, schema["bar_exports"]["columns"])
        del rows[100:220]
        _write_tsv(path, schema["bar_exports"]["columns"], rows)
    result = _finalize(evidence)
    assert result.status == "R6_NP1_EVIDENCE_INVALID"
    assert any("unlisted market-history gap" in error for error in result.errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong"), ("native_error_code", "7"), ("data_available", "yes"),
        ("state_name", "invalid"), ("state_code", "5"), ("h1_bar_count", "999999"),
        ("h4_shift1_time", "2016.07.01 00:00:00"),
    ],
)
def test_malformed_native_router_rows_are_evidence_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: str
) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    for run_id in ("run1", "run2"):
        path = evidence / "runs" / run_id / "native_router_rows.tsv"
        rows = V.read_tsv(path, schema["native_router_rows"]["columns"])
        rows[0][field] = value
        _write_tsv(path, schema["native_router_rows"]["columns"], rows)
    result = _finalize(evidence)
    assert result.status == "R6_NP1_EVIDENCE_INVALID", result.errors
    payload = json.loads((evidence / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json").read_text(encoding="utf-8"))
    assert payload["errors"]["parity"] == []


@pytest.mark.parametrize(
    ("data_available", "state_name", "state_code"),
    [("false", "uptrend", "2"), ("true", "unknown", "0")],
)
def test_native_availability_state_coherence_is_evidence_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    data_available: str, state_name: str, state_code: str,
) -> None:
    evidence, _, schema = _synthetic_packet(tmp_path, monkeypatch)
    for run_id in ("run1", "run2"):
        path = evidence / "runs" / run_id / "native_router_rows.tsv"
        rows = V.read_tsv(path, schema["native_router_rows"]["columns"])
        rows[0].update({"data_available": data_available, "state_name": state_name, "state_code": state_code})
        _write_tsv(path, schema["native_router_rows"]["columns"], rows)
    result = _finalize(evidence)
    assert result.status == "R6_NP1_EVIDENCE_INVALID"
    payload = json.loads((evidence / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json").read_text(encoding="utf-8"))
    assert payload["errors"]["parity"] == []
    assert any("availability/state coherence" in error for error in payload["errors"]["invalid"])


@pytest.mark.parametrize(
    "mutation", ["review_tree", "dependency_version", "command_stream", "command_order", "tester_exit", "extra_command"]
)
def test_attestation_binds_exact_review_dependencies_and_command_streams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    evidence, _, _ = _synthetic_packet(tmp_path, monkeypatch)
    attestation = _attestation(evidence)
    if mutation == "review_tree":
        attestation["review_authority"]["reviewed_generator_tree"] = "d" * 40
    elif mutation == "dependency_version":
        attestation["dependency_versions"]["pytest"] = ""
    else:
        if mutation == "command_stream":
            attestation["commands"][0]["stdout_base64"] = "eA=="
        elif mutation == "command_order":
            attestation["commands"][1], attestation["commands"][2] = attestation["commands"][2], attestation["commands"][1]
        elif mutation == "tester_exit":
            attestation["commands"][1]["exit_code"] = 1
        else:
            attestation["commands"].append(copy.deepcopy(attestation["commands"][-1]))
    result = V.finalize_evidence_directory(evidence, attestation=attestation)
    assert result.status == "R6_NP1_EVIDENCE_INVALID"


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ("invalid", "R6_NP1_EVIDENCE_INVALID"),
        ("source", "R6_NP1_SOURCE_EQUIVALENCE_FAIL"),
        ("zero", "R6_NP1_ZERO_ACTION_CONTRACT_FAIL"),
        ("parity", "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"),
        ("coverage", "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"),
        ("determinism", "R6_NP1_EVIDENCE_INVALID"),
        ("ordercalc", "R6_NP1_EVIDENCE_INVALID"),
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
        path = evidence / "runs" / "run1" / "native_report.htm"
        text = path.read_text(encoding="utf-8").replace("Total Trades:</td><td>0", "Total Trades:</td><td>1").replace("Total Deals:</td><td>0", "Total Deals:</td><td>1")
        path.write_text(text, encoding="utf-8")
    elif mutation in {"parity", "coverage"}:
        path = evidence / "runs" / "run1" / "native_router_rows.tsv"
        rows = V.read_tsv(path, schema["native_router_rows"]["columns"])
        if mutation == "parity":
            rows[0]["data_available"], rows[0]["state_name"], rows[0]["state_code"] = "true", "uptrend", "2"
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

    result = _finalize(evidence)
    assert result.status == expected_status
