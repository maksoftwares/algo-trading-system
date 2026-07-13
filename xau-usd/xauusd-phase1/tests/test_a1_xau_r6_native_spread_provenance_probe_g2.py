from __future__ import annotations

import importlib.util
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


PHASE = Path(__file__).resolve().parents[1]
SCRIPTS = PHASE / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "run_a1_xau_r6_native_spread_provenance_probe_g2.py"
SPEC = importlib.util.spec_from_file_location("a1_np1_g2", SCRIPT)
assert SPEC and SPEC.loader
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


def _record(command: list[str], exit_code: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> dict[str,object]:
    done=type("Done",(),{"returncode":exit_code,"stdout":stdout,"stderr":stderr})()
    return G.G1.record(command,done)


def _tsv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns,delimiter="\t",lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def _write_campaign_outputs(root: Path, run_id: str) -> None:
    report=root/"Reports"/f"np1_g2_{run_id}.htm"
    fields={"Expert":"A1XauR6NativeSpreadProvenanceProbe","Symbol":"XAUUSD","Period":"M5 (2015.06.01 - 2026.07.01)","History Quality":"1% real ticks","Currency":"USD","Initial Deposit":"10 000.00","Leverage":"1:50","Company":"Capital Com Mena Securities Trading L.L.C","Bars":"1","Ticks":"8","Total Trades":"0","Total Deals":"0"}
    report.write_text("<table><tr>"+"".join(f"<td>{key}:</td><td>{value}</td>" for key,value in fields.items())+"</tr></table>",encoding="utf-8")
    files=root/"Tester"/"Agent-1"/"MQL5"/"Files"; files.mkdir(parents=True,exist_ok=True)
    prefix=f"np1_g2_{run_id}_"
    ids=G.WARMUP_ASSERTIONS if run_id=="warmup" else G.OFFICIAL_ASSERTIONS
    values={value:("pass","pass") for value in ids}; values.update(positions_zero=("0","0"),orders_zero=("0","0"),run_id=(("warmup","warmup") if run_id=="warmup" else ("official","official")))
    if run_id=="warmup": values["warmup_only"]=("true","true")
    _tsv(files/f"{prefix}assertions.tsv",["assertion_id","passed","observed","expected"],[{"assertion_id":value,"passed":"true","observed":values[value][0],"expected":values[value][1]} for value in sorted(ids)])
    (files/f"{prefix}order.zero").write_bytes(b""); (files/f"{prefix}deal.zero").write_bytes(b"")
    if run_id=="warmup": return
    for tf in ("H1","H4","D1"):
        row={"schema_version":"a1_xau_np1_g1_bar_v1","timeframe":tf,"open_time_broker":"2015-06-01T00:00:00","open":"10","high":"11","low":"9","close":"10","tick_volume":"1","spread":"5","real_volume":"1","copyrates_return":"1","copyrates_error":"0"}
        _tsv(files/f"{prefix}{tf.lower()}_bars.tsv",G.BAR_COLUMNS,[row])
    interface_rows=[]
    for tf in ("H1","H4","D1"):
        for day in ("2025.06.18","2025.09.29","2025.11.17","2026.04.14"):
            interface_rows.append({"schema_version":"a1_xau_np1_g1_interface_v1","timeframe":tf,"open_time_broker":f"{day.replace('.','-')}T03:00:00","open":"10","high":"11","low":"9","close":"10","tick_volume":"1","real_volume":"1","copyrates_spread":"5","copyspread_spread":"5","ispread_spread":"5","copyspread_return":"1","copyspread_error":"0","ibarshift":"1","ispread_error":"0","point":"0.01","digits":"2"})
    _tsv(files/f"{prefix}bar_spread_interfaces.tsv",G.INTERFACE_COLUMNS,interface_rows)
    for name,day in G.TICK_DAYS.items():
        stamp=f"{day.replace('.','-')}T00:00:01"; msc=str(int(datetime.strptime(stamp,"%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())*1000)
        rows=[{"schema_version":"a1_xau_np1_g1_tick_v1","broker_day":day,"time_msc":msc,"time":stamp,"bid":bid,"ask":ask,"last":"0","volume":"1","volume_real":"1","flags":flag,"raw_ask_minus_bid":"1","raw_spread_points":"100","negative_spread_boolean":"false","quote_sides_positive":"true","copyticks_return":"2","copyticks_error":"0"} for bid,ask,flag in (("10","11","1"),("10.5","11.5","2"))]
        _tsv(files/f"{prefix}{name}",G.TICK_COLUMNS,rows)


def _auth_fields(commit: str, tree: str) -> dict[str,str]:
    base=G.CANONICAL_REPORTS_RELATIVE
    return {"NP1_G2B_AUTHORIZATION_STATUS":"AUTHORIZED","REVIEW_VERDICT":"PASS","REVIEWED_EXECUTOR_COMMIT":commit,"REVIEWED_EXECUTOR_TREE":tree,"NEW_ROOT_PATH":str(G.NEW_ROOT),"MARKER_BYTES":"NP1 SPREAD PROBE G2 ONLY\\n","CANONICAL_REPORTS_ROOT":base,"COMPLETE_OUTPUT_ROOT":f"{base}/{G.COMPLETE_NAME}","STOP_OUTPUT_ROOT":f"{base}/{G.STOP_NAME}","METADATA_RECEIPT_MODES":"COPIED_ALLOWLIST,ZERO_COPY","METADATA_ALLOWLIST":"Config/accounts.dat,Config/servers.dat","METAEDITOR_COMPILATIONS_MAX":"1","STRATEGY_TESTER_RUNS_MAX":"3","STRATEGY_TESTER_ORDER":"warmup,probe1,probe2","MT5_EXECUTION_AUTHORIZED":"true","CANONICAL_NP1C_RESULT_AUTHORIZED":"false","R6_CENSUS_AUTHORIZED":"false","PNL_AUTHORIZED":"false","TARGET_EXIT_MFE_MAE_AUTHORIZED":"false","DEMO_LIVE_ATTACH_AUTHORIZED":"false","PRESET_PROFILE_ARMING_AUTHORIZED":"false","BROKER_ACTION_AUTHORIZED":"false","DEPLOYMENT_AUTHORIZED":"false"}


def _authorization_name(commit: str) -> str:
    return f"A1_XAU_NP1G2A10_EXECUTION_AUTHORIZATION_{commit[:8].upper()}_2026_07_13.md"


def _assert_native_report_required_fields_aligned(contract_fields: list[str], runner_fields: tuple[str, ...]) -> None:
    assert len(contract_fields) == len(set(contract_fields))
    assert len(runner_fields) == len(set(runner_fields))
    assert set(contract_fields) == set(runner_fields)


def test_contract_native_report_required_fields_exactly_match_runner() -> None:
    contract_path = PHASE / "docs" / "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_CONTRACT_V1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract_fields = contract["effective_tester_evidence"]["native_report_required_fields"]
    expected = (
        "Expert", "Symbol", "Period", "History Quality", "Company", "Currency",
        "Initial Deposit", "Leverage", "Bars", "Ticks", "Total Trades", "Total Deals",
    )
    assert tuple(contract_fields) == G.NATIVE_REPORT_REQUIRED_FIELDS == expected
    _assert_native_report_required_fields_aligned(contract_fields, G.NATIVE_REPORT_REQUIRED_FIELDS)


@pytest.mark.parametrize("required_field", ["History Quality", "Company", "Currency"])
@pytest.mark.parametrize("removed_from", ["contract", "runner"])
def test_native_report_required_field_removal_breaks_cross_file_invariant(required_field: str, removed_from: str) -> None:
    contract_path = PHASE / "docs" / "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_CONTRACT_V1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract_fields = list(contract["effective_tester_evidence"]["native_report_required_fields"])
    runner_fields = list(G.NATIVE_REPORT_REQUIRED_FIELDS)
    (contract_fields if removed_from == "contract" else runner_fields).remove(required_field)
    with pytest.raises(AssertionError):
        _assert_native_report_required_fields_aligned(contract_fields, tuple(runner_fields))


def _retag_selected(packet: Path, run_id: str, kind: str, path: Path) -> None:
    selected=json.loads((packet/"searched_location_inventory.json").read_text())
    row=next(item for item in selected["selected_sources"] if item["kind"]==kind and f"np1_g2_{run_id}" in item["source"])
    row["size_bytes"]=path.stat().st_size; row["sha256"]=G.sha256_file(path); G.write_json(packet/"searched_location_inventory.json",selected)


def _root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "clean-g2"; root.mkdir()
    (root / G.MARKER).write_bytes(G.MARKER_BYTES)
    (root / "terminal64.exe").write_bytes(b"terminal")
    (root / "MetaEditor64.exe").write_bytes(b"editor")
    monkeypatch.setattr(G, "NEW_ROOT", root)
    return root


def test_exact_new_root_and_marker_acceptance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch)
    terminal, editor = G.validate_exact_root(root, initial=True)
    assert terminal.name == "terminal64.exe" and editor.name == "MetaEditor64.exe"


def test_old_and_wrong_roots_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch)
    for wrong in (tmp_path / "old1", tmp_path / "old2"):
        wrong.mkdir(); (wrong / G.MARKER).write_bytes(G.MARKER_BYTES)
        (wrong / "terminal64.exe").write_bytes(b"x"); (wrong / "MetaEditor64.exe").write_bytes(b"x")
    monkeypatch.setattr(G, "QUARANTINED_ROOTS", (tmp_path / "old1", tmp_path / "old2"))
    with pytest.raises(RuntimeError, match="exact new root|quarantined"):
        G.validate_exact_root(tmp_path / "old1", initial=True)
    (root / G.MARKER).write_text("wrong\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="marker"):
        G.validate_exact_root(root, initial=True)


@pytest.mark.parametrize("relative", ["Bases", "history", "Tester/bases", "Tester/cache", "Tester/Agent-1", "MQL5/Files", "Logs", "Reports", "Profiles"])
def test_forbidden_initial_surfaces_rejected(relative: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch); (root / relative).mkdir(parents=True)
    with pytest.raises(RuntimeError, match="forbidden initial"):
        G.validate_exact_root(root, initial=True)


def test_metadata_allowlist_and_hash_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch); old = tmp_path / "old"; (old / "Config").mkdir(parents=True)
    monkeypatch.setattr(G, "QUARANTINED_ROOTS", (old, tmp_path / "other"))
    copied = []
    for name in ("accounts.dat", "servers.dat"):
        source = old / "Config" / name; source.write_bytes(name.encode())
        destination = root / "Config" / name; destination.parent.mkdir(exist_ok=True); destination.write_bytes(source.read_bytes())
        copied.append({"source_path": str(source), "source_relative": f"Config/{name}", "destination_relative": f"Config/{name}", "size_bytes": destination.stat().st_size, "sha256": G.sha256_file(destination)})
    G.validate_metadata_receipt(root, {"mode":"COPIED_ALLOWLIST","copied": copied})
    copied.append({"source_path": str(old / "Config" / "common.ini"), "source_relative":"Config/common.ini", "destination_relative": "Config/common.ini", "size_bytes": 0, "sha256": "0" * 64})
    with pytest.raises(RuntimeError, match="unexpected"):
        G.validate_metadata_receipt(root, {"mode":"COPIED_ALLOWLIST","copied": copied})
    with pytest.raises(RuntimeError,match="closed schema"): G.validate_metadata_receipt(root,{"mode":"COPIED_ALLOWLIST","copied":[],"extra":True})


def test_reports_runner_create_write_read_delete_attestation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch)
    before, after, attestation = G.prepare_reports_directory(root)
    assert before["exists"] and after["exists"]
    assert (root / "Reports").is_dir()
    assert not (root / "Reports" / G.REPORT_SENTINEL).exists()
    assert all(attestation[key] for key in ("created_by_runner", "sentinel_read_back", "sentinel_deleted", "writable"))


def test_reports_must_be_initially_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch); (root / "Reports").mkdir()
    with pytest.raises(RuntimeError, match="absent"):
        G.prepare_reports_directory(root)


def test_stale_empty_rejected_and_fresh_nonempty_accepted(tmp_path: Path) -> None:
    report = tmp_path / "report.htm"; parser = lambda path: path.read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing"):
        G.validate_fresh_report(report, 1, parser)
    report.write_bytes(b"")
    with pytest.raises(RuntimeError, match="missing"):
        G.validate_fresh_report(report, 1, parser)
    report.write_text("report", encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale"):
        G.validate_fresh_report(report, report.stat().st_mtime_ns + 3_000_000_000, parser)
    assert G.validate_fresh_report(report, report.stat().st_mtime_ns, parser) == "report"


@pytest.mark.parametrize(("old","new"),[("M5 (2015.06.01 - 2026.07.01)","H1 (2015.06.01 - 2026.07.01)"),("M5 (2015.06.01 - 2026.07.01)","M5 (2026.07.01 - 2015.06.01)"),("2015.06.01","2016.06.01"),("<td>Currency:</td><td>USD</td>","<td>Currency:</td><td>EUR</td>"),("10 000.00","9 999.00"),("1:50","1:100")])
def test_native_report_effective_settings_fail_closed(tmp_path: Path, old: str, new: str) -> None:
    root=tmp_path/"root"; (root/"Reports").mkdir(parents=True); _write_campaign_outputs(root,"warmup"); report=root/"Reports"/"np1_g2_warmup.htm"; report.write_text(report.read_text().replace(old,new),encoding="utf-8")
    with pytest.raises(RuntimeError,match="native report"): G.validate_effective_report(report)


def test_native_report_duplicate_label_fails_closed(tmp_path: Path) -> None:
    root=tmp_path/"root"; (root/"Reports").mkdir(parents=True); _write_campaign_outputs(root,"warmup"); report=root/"Reports"/"np1_g2_warmup.htm"
    report.write_text(report.read_text().replace("<td>Period:</td>","<td>Period:</td><td>M5 (2015.06.01 - 2026.07.01)</td><td>Period:</td>"),encoding="utf-8")
    with pytest.raises(RuntimeError,match="duplicate native report label"): G.validate_effective_report(report)


@pytest.mark.parametrize("case",["missing_currency","embedded_currency_only","duplicate_currency","duplicate_deposit"])
def test_native_report_currency_deposit_shape_fail_closed(tmp_path: Path, case: str) -> None:
    root=tmp_path/"root"; (root/"Reports").mkdir(parents=True); _write_campaign_outputs(root,"warmup"); report=root/"Reports"/"np1_g2_warmup.htm"; text=report.read_text()
    currency="<td>Currency:</td><td>USD</td>"; deposit="<td>Initial Deposit:</td><td>10 000.00</td>"
    if case=="missing_currency": text=text.replace(currency,"")
    elif case=="embedded_currency_only": text=text.replace(currency,"").replace(deposit,"<td>Initial Deposit:</td><td>10 000.00 USD</td>")
    elif case=="duplicate_currency": text=text.replace(currency,currency+currency)
    else: text=text.replace(deposit,deposit+deposit)
    report.write_text(text,encoding="utf-8")
    with pytest.raises(RuntimeError,match="native report"): G.validate_effective_report(report)


def test_native_report_positive_real_tick_percentage_is_evidence_not_threshold(tmp_path: Path) -> None:
    root=tmp_path/"root"; (root/"Reports").mkdir(parents=True); _write_campaign_outputs(root,"warmup"); report=root/"Reports"/"np1_g2_warmup.htm"
    report.write_text(report.read_text().replace("1% real ticks","12.5% real ticks"),encoding="utf-8")
    assert G.validate_effective_report(report)["History Quality"]=="12.5% real ticks"


@pytest.mark.parametrize("case",["missing_history","non_real_history","zero_history","duplicate_history","missing_company","wrong_company","duplicate_company","wrong_optional_model"])
def test_native_report_real_tick_history_and_company_fail_closed(tmp_path: Path, case: str) -> None:
    root=tmp_path/"root"; (root/"Reports").mkdir(parents=True); _write_campaign_outputs(root,"warmup"); report=root/"Reports"/"np1_g2_warmup.htm"; text=report.read_text()
    history="<td>History Quality:</td><td>1% real ticks</td>"; company="<td>Company:</td><td>Capital Com Mena Securities Trading L.L.C</td>"
    if case=="missing_history": text=text.replace(history,"")
    elif case=="non_real_history": text=text.replace("1% real ticks","100% modeled ticks")
    elif case=="zero_history": text=text.replace("1% real ticks","0% real ticks")
    elif case=="duplicate_history": text=text.replace(history,history+history)
    elif case=="missing_company": text=text.replace(company,"")
    elif case=="wrong_company": text=text.replace("Capital Com Mena Securities Trading L.L.C","Other Broker")
    elif case=="duplicate_company": text=text.replace(company,company+company)
    else: text=text.replace(history,history+"<td>Model:</td><td>Open prices only</td>")
    report.write_text(text,encoding="utf-8")
    with pytest.raises(RuntimeError,match="native report"): G.validate_effective_report(report)


def test_exact_command_arrays_streams_and_compile_exit_semantics(tmp_path: Path) -> None:
    root=tmp_path.resolve(); source=root/"MQL5"/"Experts"/G.B.PROBE_NAME; log=root/"compile.log"
    commands=[_record([str(root/"MetaEditor64.exe"),f"/compile:{source}",f"/log:{log}"],exit_code=1,stdout=b"ok")]
    commands += [_record([str(root/"terminal64.exe"),"/portable",f"/config:{root/'Config'/f'np1_g2_{rid}.ini'}"]) for rid in G.RUN_IDS]
    G.validate_command_records(commands,root)
    bad=json.loads(json.dumps(commands)); bad[0]["exit_code"]=2
    with pytest.raises(RuntimeError,match="compile command"): G.validate_command_records(bad,root)
    bad=json.loads(json.dumps(commands)); bad[1]["command"].append("/extra")
    with pytest.raises(RuntimeError,match="tester command"): G.validate_command_records(bad,root)
    bad=json.loads(json.dumps(commands)); bad[0]["stdout_sha256"]="0"*64
    with pytest.raises(RuntimeError,match="stream hash"): G.validate_command_records(bad,root)


def test_synthetic_writer_requires_parent_directory(tmp_path: Path) -> None:
    report = tmp_path / "Reports" / "np1_g2_warmup.htm"
    with pytest.raises(FileNotFoundError):
        report.write_text("report", encoding="utf-8")
    report.parent.mkdir(); report.write_text("report", encoding="utf-8")
    assert report.is_file()


def test_versioned_ini_and_output_names_only() -> None:
    for run_id in G.RUN_IDS:
        text = G.render_ini(run_id)
        assert f"Report=Reports/np1_g2_{run_id}" in text
        assert f"np1_g2_{run_id}_" in text
        assert "np1_g1_" not in text


def test_ledger_one_compile_and_exact_three_order(tmp_path: Path) -> None:
    ledger = G.Ledger(tmp_path / "ledger.json")
    ledger.compilation()
    with pytest.raises(RuntimeError, match="second compilation"):
        ledger.compilation()
    for run_id in G.RUN_IDS: ledger.run(run_id)
    with pytest.raises(RuntimeError, match="fourth"):
        ledger.run("probe2")
    assert json.loads(ledger.path.read_text(encoding="utf-8"))["tester_runs"] == list(G.RUN_IDS)


def test_warmup_or_probe1_failure_prevents_later_runs(tmp_path: Path) -> None:
    ledger = G.Ledger(tmp_path / "one.json"); ledger.compilation(); ledger.run("warmup")
    assert ledger.data["tester_runs"] == ["warmup"] and "probe1" not in ledger.data["tester_runs"]
    second = G.Ledger(tmp_path / "two.json"); second.compilation(); second.run("warmup"); second.run("probe1")
    assert second.data["tester_runs"] == ["warmup", "probe1"] and "probe2" not in second.data["tester_runs"]


def test_mutually_exclusive_complete_and_stop_paths(tmp_path: Path) -> None:
    complete, stop = G.assert_mutually_exclusive(tmp_path)
    assert complete.name == G.COMPLETE_NAME and stop.name == G.STOP_NAME
    complete.mkdir()
    with pytest.raises(RuntimeError, match="already exists"):
        G.assert_mutually_exclusive(tmp_path)


def test_automatic_stop_packet_preserves_ledger_inventories_logs_and_outputs(tmp_path: Path) -> None:
    root = tmp_path / "root"; (root / "Config").mkdir(parents=True); (root / "Reports").mkdir()
    (root / "Config" / "np1_g2_warmup.ini").write_text("ini", encoding="utf-8")
    files = root / "Tester" / "Agent-1" / "MQL5" / "Files"; files.mkdir(parents=True)
    (files / "np1_g2_warmup_assertions.tsv").write_text("assert", encoding="utf-8")
    terminal_logs = root / "Tester" / "logs"; terminal_logs.mkdir(parents=True); (terminal_logs / "x.log").write_text("log", encoding="utf-8")
    agent_logs = root / "Tester" / "Agent-1" / "logs"; agent_logs.mkdir(); (agent_logs / "y.log").write_text("agent", encoding="utf-8")
    ledger = G.Ledger(tmp_path / "ledger.json"); ledger.compilation(); ledger.run("warmup")
    preflight=G.inventory(root)
    partial=tmp_path/"staging"; partial.mkdir(); (partial/"late_verifier_marker.txt").write_text("preserve",encoding="utf-8")
    stop = G.preserve_stop_packet(stop=tmp_path / "stop", root=root, ledger=ledger.path, preflight=preflight, reports_attestation={"writable": True}, commands=[{"exit_code": 0}], run_ids=["warmup"], error=RuntimeError("late packet verifier failure"), authorization_attestation={"artifact":"review.md"}, post_reports_inventory={"exists":True},partial_staging=partial)
    assert json.loads((stop / "result.json").read_text(encoding="utf-8"))["status"] == "NP1_G2_EVIDENCE_INVALID"
    assert (stop / "invocation_ledger.json").is_file() and (stop / "preflight_root_inventory.json").is_file() and (stop / "post_stop_root_inventory.json").is_file()
    assert (stop / "logs" / "log_inventory.json").is_file() and (stop / "searched_location_inventory.json").is_file()
    assert json.loads((stop / "authorization_attestation.json").read_text())["artifact"] == "review.md"
    assert json.loads((stop / "post_reports_creation_inventory.json").read_text())["exists"] is True
    assert (stop/"partial_staging"/"late_verifier_marker.txt").read_text()=="preserve" and not partial.exists()
    assert (stop / "manifest.json").is_file() and (stop / "manifest.sha256").is_file()


def test_ex5_drift_is_fail_closed(tmp_path: Path) -> None:
    ex5 = tmp_path / "probe.ex5"; ex5.write_bytes(b"one"); expected = G.sha256_file(ex5); ex5.write_bytes(b"two")
    assert G.sha256_file(ex5) != expected


def test_g2a_cli_and_executor_are_not_authorized(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="repo-only"):
        G.execute_future(authorization="", review_artifact=tmp_path / "none", review_sha256="", reviewed_commit="", reviewed_tree="", root=tmp_path, reports_root=tmp_path, metadata_receipt=tmp_path / "receipt")


def test_wrong_root_rejection_is_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wrong=tmp_path/"wrong"; reports=tmp_path/"reports"; reports.mkdir(); monkeypatch.setattr(G,"CANONICAL_REPORTS_ROOT",reports); monkeypatch.setattr(G.G1,"git",lambda *a:"" if a[0]=="status" else ("a"*40 if "rev-parse" in a else "b"*40)); monkeypatch.setattr(G,"parse_future_authorization",lambda *a:{})
    with pytest.raises(RuntimeError): G.execute_future(authorization=G.ACTIVATION,review_artifact=tmp_path/"x",review_sha256="x",reviewed_commit="a"*40,reviewed_tree="b"*40,root=wrong,reports_root=reports,metadata_receipt=tmp_path/"m")
    assert not wrong.exists() and not any(reports.iterdir())


def test_closed_review_parser_exact_hash_fields_and_no_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    commit, tree = "a" * 40, "b" * 40
    path = tmp_path / _authorization_name(commit)
    fields = _auth_fields(commit,tree)
    block = "NP1_G2B_AUTHORIZATION_BLOCK_BEGIN\n" + "\n".join(f"{k}: {v}" for k,v in fields.items()) + "\nNP1_G2B_AUTHORIZATION_BLOCK_END\n"
    path.write_text(block, encoding="utf-8")
    assert G.parse_future_authorization(path, G.sha256_file(path), commit, tree) == fields
    path.write_text("NO-GO\n" + block, encoding="utf-8")
    with pytest.raises(PermissionError): G.parse_future_authorization(path, G.sha256_file(path), commit, tree)
    path.write_text(block.replace("REVIEW_VERDICT: PASS","REVIEW_VERDICT: FAIL\nREVIEW_VERDICT: PASS"),encoding="utf-8")
    with pytest.raises(PermissionError,match="duplicate"): G.parse_future_authorization(path,G.sha256_file(path),commit,tree)


def test_end_to_end_warmup_failure_automatically_creates_stop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path, monkeypatch); reports_root = tmp_path / "reports"; reports_root.mkdir()
    monkeypatch.setattr(G,"CANONICAL_REPORTS_ROOT",reports_root)
    old = tmp_path / "old"; (old / "Config").mkdir(parents=True); monkeypatch.setattr(G,"QUARANTINED_ROOTS",(old,tmp_path/"other"))
    config = root / "Config"; config.mkdir()
    copied=[]
    for name in ("accounts.dat","servers.dat"):
        src=old/"Config"/name; src.write_bytes(name.encode()); dst=config/name; dst.write_bytes(src.read_bytes()); copied.append({"source_path":str(src),"source_relative":f"Config/{name}","destination_relative":f"Config/{name}","size_bytes":dst.stat().st_size,"sha256":G.sha256_file(dst)})
    receipt=tmp_path/"receipt.json"; receipt.write_text(json.dumps({"mode":"COPIED_ALLOWLIST","copied":copied}),encoding="utf-8")
    commit,tree="a"*40,"b"*40; monkeypatch.setattr(G.G1,"git",lambda *args: "" if args[0]=="status" else (commit if "rev-parse" in args else tree))
    review=tmp_path/_authorization_name(commit)
    fields=_auth_fields(commit,tree)
    review.write_text("NP1_G2B_AUTHORIZATION_BLOCK_BEGIN\n"+"\n".join(f"{k}: {v}" for k,v in fields.items())+"\nNP1_G2B_AUTHORIZATION_BLOCK_END\n",encoding="utf-8")
    class C: pass
    def compile_fake(root,editor,runner,version_reader):
        experts=root/"MQL5"/"Experts"; experts.mkdir(parents=True); source=experts/G.B.PROBE_NAME; source.write_text(G.B.render_probe(),encoding="utf-8",newline="\n"); ex5=source.with_suffix('.ex5'); ex5.write_bytes(b'ex5'); log=root/'compile.log'; log.write_text('0 errors 0 warnings'); command=[str(editor),f"/compile:{source}",f"/log:{log}"]; return G.G1.CompileResult(source,ex5,log,G.sha256_file(source),G.sha256_file(ex5),G.G1.EXPECTED_VERSION,_record(command))
    monkeypatch.setattr(G.G1,"compile_once",compile_fake)
    done=type("Done",(),{"returncode":0,"stdout":b"","stderr":b""})()
    with pytest.raises(RuntimeError,match="report"):
        G.execute_future(authorization=G.ACTIVATION,review_artifact=review,review_sha256=G.sha256_file(review),reviewed_commit=commit,reviewed_tree=tree,root=root,reports_root=reports_root,metadata_receipt=receipt,command_runner=lambda *a:done,compile_runner=lambda *a:done,version_reader=lambda p:G.G1.EXPECTED_VERSION)
    stop=reports_root/G.STOP_NAME
    assert stop.is_dir() and (stop/"invocation_ledger.json").is_file() and not (reports_root/G.COMPLETE_NAME).exists()


def test_end_to_end_synthetic_complete_campaign(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root=_root(tmp_path,monkeypatch); reports=tmp_path/"reports"; reports.mkdir(); old=tmp_path/"old"; (old/"Config").mkdir(parents=True); monkeypatch.setattr(G,"QUARANTINED_ROOTS",(old,tmp_path/"other")); (root/"Config").mkdir()
    monkeypatch.setattr(G,"CANONICAL_REPORTS_ROOT",reports)
    copied=[]
    for name in ("accounts.dat","servers.dat"):
        src=old/"Config"/name; src.write_bytes(name.encode()); dst=root/"Config"/name; dst.write_bytes(src.read_bytes()); copied.append({"source_path":str(src),"source_relative":f"Config/{name}","destination_relative":f"Config/{name}","size_bytes":dst.stat().st_size,"sha256":G.sha256_file(dst)})
    receipt=tmp_path/"receipt.json"; receipt.write_text(json.dumps({"mode":"COPIED_ALLOWLIST","copied":copied}),encoding="utf-8"); commit,tree="c"*40,"d"*40; monkeypatch.setattr(G.G1,"git",lambda *a:"" if a[0]=="status" else (commit if "rev-parse" in a else tree))
    review=tmp_path/_authorization_name(commit); fields=_auth_fields(commit,tree); review.write_text("NP1_G2B_AUTHORIZATION_BLOCK_BEGIN\n"+"\n".join(f"{k}: {v}" for k,v in fields.items())+"\nNP1_G2B_AUTHORIZATION_BLOCK_END\n",encoding="utf-8")
    def comp(root,editor,runner,version_reader):
        e=root/"MQL5"/"Experts"; e.mkdir(parents=True); s=e/G.B.PROBE_NAME; s.write_text(G.B.render_probe(),encoding="utf-8",newline="\n"); x=s.with_suffix('.ex5'); x.write_bytes(b'x'); log=root/'compile.log'; log.write_text('0 errors 0 warnings'); command=[str(editor),f"/compile:{s}",f"/log:{log}"]; return G.G1.CompileResult(s,x,log,G.sha256_file(s),G.sha256_file(x),G.G1.EXPECTED_VERSION,_record(command,exit_code=1))
    monkeypatch.setattr(G.G1,"compile_once",comp)
    import analyze_a1_xau_r6_native_spread_provenance_probe as AN
    prior=tmp_path/"prior.csv"; prior.write_text("run,timeframe,timestamp,raw_signed_spread\nrun1,H1,2025-06-18T03:00:00,-7\n",encoding="utf-8")
    fingerprints=tmp_path/"fingerprints.json"; fingerprints.write_text(json.dumps({tf:{"sha256":"0"*64,"row_count":1} for tf in AN.TIMEFRAMES}),encoding="utf-8")
    monkeypatch.setattr(AN,"PRIOR_NEGATIVE",prior); monkeypatch.setattr(AN,"PRIOR_FINGERPRINTS",fingerprints)
    done=type("D",(),{"returncode":0,"stdout":b"","stderr":b""})()
    def campaign(command, cwd, timeout):
        run_id=Path(next(part.split(":",1)[1] for part in command if part.startswith("/config:"))).stem.removeprefix("np1_g2_")
        _write_campaign_outputs(root,run_id); return done
    complete=G.execute_future(authorization=G.ACTIVATION,review_artifact=review,review_sha256=G.sha256_file(review),reviewed_commit=commit,reviewed_tree=tree,root=root,reports_root=reports,metadata_receipt=receipt,command_runner=campaign,compile_runner=lambda *a:done,version_reader=lambda p:G.G1.EXPECTED_VERSION)
    assert complete.name==G.COMPLETE_NAME and json.loads((complete/"result.json").read_text())["status"]=="NP1_G2_DIAGNOSTIC_COMPLETE" and not (reports/G.STOP_NAME).exists(); G.verify_manifest(complete)
    assert json.loads((complete/"manifest.json").read_text())["schema_version"]=="a1_xau_r6_np1_g2_complete_manifest_v1"
    verification=json.loads((complete/"packet_verification.json").read_text())
    assert verification["verifier"]=="full_packet_temporary_copy_recompute_v2" and not verification["original_packet_mutated"]
    assert len(json.loads((complete/"searched_location_inventory.json").read_text())["selected_sources"])==31
    context={"authorization_attestation":json.loads((complete/"authorization_attestation.json").read_text()),"metadata_receipt":json.loads((complete/"metadata_receipt.json").read_text()),"root":root}
    def packet_copy(name: str) -> Path:
        target=tmp_path/name; shutil.copytree(complete,target); return target
    def mutate_tsv(packet: Path, run_id: str, name: str, column: str, value: str) -> None:
        path=packet/"runs"/run_id/name
        with path.open(newline="",encoding="utf-8") as handle: rows=list(csv.DictReader(handle,delimiter="\t"))
        rows[0][column]=value; _tsv(path,list(rows[0]),rows); _retag_selected(packet,run_id,name,path)
    def mutate_all_tsv(packet: Path, run_id: str, name: str, column: str, value: str) -> None:
        path=packet/"runs"/run_id/name
        with path.open(newline="",encoding="utf-8") as handle: rows=list(csv.DictReader(handle,delimiter="\t"))
        for row in rows: row[column]=value
        _tsv(path,list(rows[0]),rows); _retag_selected(packet,run_id,name,path)
    def mutate_tsv_row(packet: Path, run_id: str, name: str, index: int, column: str, value: str) -> None:
        path=packet/"runs"/run_id/name
        with path.open(newline="",encoding="utf-8") as handle: rows=list(csv.DictReader(handle,delimiter="\t"))
        rows[index][column]=value; _tsv(path,list(rows[0]),rows); _retag_selected(packet,run_id,name,path)
    tampered=tmp_path/"tampered-result"; shutil.copytree(complete,tampered); payload=json.loads((tampered/"result.json").read_text()); payload["flags"].append("STALE"); (tampered/"result.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    with pytest.raises(RuntimeError,match="semantic recomputation"): G.semantic_verify_packet(tampered,tmp_path/"scratch-result",context)
    tampered_auth=tmp_path/"tampered-auth"; shutil.copytree(complete,tampered_auth); auth=json.loads((tampered_auth/"authorization_attestation.json").read_text()); auth["sha256"]="0"*64; G.write_json(tampered_auth/"authorization_attestation.json",auth)
    with pytest.raises(RuntimeError,match="authorization attestation"): G.semantic_verify_packet(tampered_auth,tmp_path/"scratch-auth",context)
    tampered_assert=tmp_path/"tampered-assert"; shutil.copytree(complete,tampered_assert); assertion=tampered_assert/"runs"/"warmup"/"assertions.tsv"; lines=assertion.read_text().splitlines(); assertion.write_text("\n".join(lines[:-1])+"\n",encoding="utf-8"); selected=json.loads((tampered_assert/"searched_location_inventory.json").read_text()); row=next(item for item in selected["selected_sources"] if item["kind"]=="assertions.tsv" and "warmup" in item["source"]); row["size_bytes"]=assertion.stat().st_size; row["sha256"]=G.sha256_file(assertion); G.write_json(tampered_assert/"searched_location_inventory.json",selected)
    with pytest.raises(RuntimeError,match="assertion set"): G.semantic_verify_packet(tampered_assert,tmp_path/"scratch-assert",context)
    contradictory=packet_copy("contradictory-assertion"); mutate_tsv(contradictory,"warmup","assertions.tsv","observed","false")
    with pytest.raises(RuntimeError,match="observed/expected"): G.semantic_verify_packet(contradictory,tmp_path/"scratch-contradictory",context)
    bad_rates=packet_copy("bad-copyrates"); [mutate_tsv(bad_rates,run_id,"h1_bars.tsv","copyrates_return","999") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="bar native return/error/range"): G.validate_native_exports(bad_rates)
    bad_interface=packet_copy("bad-interface"); [mutate_tsv(bad_interface,run_id,"bar_spread_interfaces.tsv","copyspread_error","4301") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="interface native return/error"): G.validate_native_exports(bad_interface)
    bad_ticks=packet_copy("bad-copyticks"); [mutate_tsv(bad_ticks,run_id,"ticks_20250618.tsv","copyticks_error","4301") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="tick native return/error/day"): G.validate_native_exports(bad_ticks)
    bad_source=packet_copy("bad-selected-source"); inventory=json.loads((bad_source/"searched_location_inventory.json").read_text()); next(row for row in inventory["selected_sources"] if "np1_g2_warmup" in row["source"] and row["kind"]=="assertions.tsv")["source"]="C:/invented/np1_g2_warmup_assertions.tsv"; G.write_json(bad_source/"searched_location_inventory.json",inventory)
    with pytest.raises(RuntimeError,match="selected output source path"): G.semantic_verify_packet(bad_source,tmp_path/"scratch-source",context)
    bad_root=packet_copy("bad-root-inventory"); post=json.loads((bad_root/"post_run_root_inventory.json").read_text()); post["entries"]=[row for row in post["entries"] if row["relative_path"]!="Config/np1_g2_probe2.ini"]; G.write_json(bad_root/"post_run_root_inventory.json",post)
    with pytest.raises(RuntimeError,match="post-run inventory incomplete"): G.semantic_verify_packet(bad_root,tmp_path/"scratch-root",context)
    bad_log=packet_copy("bad-log"); log_path=bad_log/"logs"/"unapproved"/"invented.log"; log_path.parent.mkdir(); log_path.write_text("invented",encoding="utf-8"); G.write_json(bad_log/"logs"/"log_inventory.json",{"logs":[{"source_relative":"unapproved/invented.log","size_bytes":log_path.stat().st_size,"sha256":G.sha256_file(log_path)}]})
    with pytest.raises(RuntimeError,match="unauthorized log path/schema"): G.semantic_verify_packet(bad_log,tmp_path/"scratch-log",context)
    dotted_bar=packet_copy("dotted-bar"); [mutate_tsv(dotted_bar,run_id,"h1_bars.tsv","open_time_broker","2015.06.01 00:00:00") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="ISO timestamp"): G.validate_native_exports(dotted_bar)
    dotted_tick=packet_copy("dotted-tick"); [mutate_tsv(dotted_tick,run_id,"ticks_20250618.tsv","time","2025.06.18 00:00:01") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="ISO timestamp"): G.validate_native_exports(dotted_tick)
    outside_tick=packet_copy("outside-tick"); outside_msc=str(int(datetime(2025,6,19,tzinfo=timezone.utc).timestamp())*1000)
    for run_id in ("probe1","probe2"): mutate_all_tsv(outside_tick,run_id,"ticks_20250618.tsv","time","2025-06-19T00:00:00"); mutate_all_tsv(outside_tick,run_id,"ticks_20250618.tsv","time_msc",outside_msc)
    with pytest.raises(RuntimeError,match="return/error/day"): G.validate_native_exports(outside_tick)
    disagreeing_msc=packet_copy("disagreeing-msc"); [mutate_tsv(disagreeing_msc,run_id,"ticks_20250618.tsv","time_msc","1") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="return/error/day"): G.validate_native_exports(disagreeing_msc)
    decreasing_msc=packet_copy("decreasing-msc"); base_msc=int(datetime(2025,6,18,0,0,1,tzinfo=timezone.utc).timestamp())*1000
    for run_id in ("probe1","probe2"): mutate_tsv_row(decreasing_msc,run_id,"ticks_20250618.tsv",0,"time_msc",str(base_msc+900)); mutate_tsv_row(decreasing_msc,run_id,"ticks_20250618.tsv",1,"time_msc",str(base_msc+100))
    with pytest.raises(RuntimeError,match="timestamps decreasing"): G.validate_native_exports(decreasing_msc)
    reordered_same_msc=packet_copy("reordered-same-msc"); reorder_path=reordered_same_msc/"runs"/"probe2"/"ticks_20250618.tsv"
    with reorder_path.open(newline="",encoding="utf-8") as handle: reorder_rows=list(csv.DictReader(handle,delimiter="\t"))
    _tsv(reorder_path,list(reorder_rows[0]),list(reversed(reorder_rows))); _retag_selected(reordered_same_msc,"probe2","ticks_20250618.tsv",reorder_path)
    with pytest.raises(RuntimeError,match="official export drift"): G.validate_native_exports(reordered_same_msc)
    deleted_same_msc=packet_copy("deleted-same-msc"); delete_path=deleted_same_msc/"runs"/"probe2"/"ticks_20250618.tsv"
    with delete_path.open(newline="",encoding="utf-8") as handle: delete_rows=list(csv.DictReader(handle,delimiter="\t"))
    _tsv(delete_path,list(delete_rows[0]),delete_rows[:1]); _retag_selected(deleted_same_msc,"probe2","ticks_20250618.tsv",delete_path)
    with pytest.raises(RuntimeError,match="official export drift"): G.validate_native_exports(deleted_same_msc)
    changed_same_msc=packet_copy("changed-same-msc"); mutate_tsv_row(changed_same_msc,"probe2","ticks_20250618.tsv",1,"flags","999")
    with pytest.raises(RuntimeError,match="official export drift"): G.validate_native_exports(changed_same_msc)
    mixed_point=packet_copy("mixed-point"); [mutate_tsv(mixed_point,run_id,"bar_spread_interfaces.tsv","point","0.1") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="mixed native point/digits"): G.validate_native_exports(mixed_point)
    wrong_point=packet_copy("wrong-point")
    for run_id in ("probe1","probe2"): mutate_all_tsv(wrong_point,run_id,"bar_spread_interfaces.tsv","point","0.1"); mutate_all_tsv(wrong_point,run_id,"bar_spread_interfaces.tsv","digits","1")
    with pytest.raises(RuntimeError,match="native-point"): G.validate_native_exports(wrong_point)
    false_positive_flag=packet_copy("false-positive-flag"); [mutate_tsv(false_positive_flag,run_id,"ticks_20250618.tsv","quote_sides_positive","false") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="quote-side flag"): G.validate_native_exports(false_positive_flag)
    unavailable_raw=packet_copy("unavailable-raw")
    for run_id in ("probe1","probe2"): mutate_tsv(unavailable_raw,run_id,"ticks_20250618.tsv","bid","0"); mutate_tsv(unavailable_raw,run_id,"ticks_20250618.tsv","quote_sides_positive","false")
    with pytest.raises(RuntimeError,match="unavailable tick raw fields"): G.validate_native_exports(unavailable_raw)
    nonfinite_quote=packet_copy("nonfinite-quote"); [mutate_tsv(nonfinite_quote,run_id,"ticks_20250618.tsv","bid","nan") for run_id in ("probe1","probe2")]
    with pytest.raises(RuntimeError,match="non-finite tick quote"): G.validate_native_exports(nonfinite_quote)
    bad_compiled_source=packet_copy("bad-compiled-source"); compiled=json.loads((bad_compiled_source/"compile_attestation.json").read_text()); compiled["compiled_source_sha256"]="0"*64; G.write_json(bad_compiled_source/"compile_attestation.json",compiled)
    with pytest.raises(RuntimeError,match="compiled identity"): G.semantic_verify_packet(bad_compiled_source,tmp_path/"scratch-compiled-source",context)


def test_noncanonical_reports_root_rejected_before_root_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root=tmp_path/"root"; wrong=tmp_path/"wrong"; wrong.mkdir(); canonical=tmp_path/"canonical"; canonical.mkdir()
    monkeypatch.setattr(G,"CANONICAL_REPORTS_ROOT",canonical); monkeypatch.setattr(G.G1,"git",lambda *a:"" if a[0]=="status" else ("a"*40 if "rev-parse" in a else "b"*40))
    with pytest.raises(PermissionError,match="canonical"):
        G.execute_future(authorization=G.ACTIVATION,review_artifact=tmp_path/"x",review_sha256="x",reviewed_commit="a"*40,reviewed_tree="b"*40,root=root,reports_root=wrong,metadata_receipt=tmp_path/"m")
    assert not root.exists() and not any(wrong.iterdir())


def test_changed_logs_excludes_unchanged_preflight_logs(tmp_path: Path) -> None:
    root=tmp_path/"root"; logs=root/"Logs"; logs.mkdir(parents=True); old=logs/"old.log"; old.write_text("old",encoding="utf-8")
    preflight=G.inventory(root); fresh=logs/"fresh.log"; fresh.write_text("fresh",encoding="utf-8")
    assert G.changed_logs(root,preflight)==[fresh]


def test_metadata_relabelled_source_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root=_root(tmp_path,monkeypatch); old=tmp_path/"old"; (old/"Config").mkdir(parents=True); monkeypatch.setattr(G,"QUARANTINED_ROOTS",(old,tmp_path/"x")); (root/"Config").mkdir()
    source=old/"Config"/"servers.dat"; source.write_bytes(b'x'); destination=root/"Config"/"accounts.dat"; destination.write_bytes(b'x')
    receipt={"mode":"COPIED_ALLOWLIST","copied":[{"source_path":str(source),"source_relative":"Config/servers.dat","destination_relative":"Config/accounts.dat","size_bytes":1,"sha256":G.sha256_file(source)}]}
    with pytest.raises(RuntimeError,match="identity"): G.validate_metadata_receipt(root,receipt)


def test_static_no_normalization_result_research_attach_or_broker_action() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    lowered = source.lower()
    assert all(token not in lowered for token in ("abs(spread", "max(spread", "net_profit", "profit_factor", "order.send", "ordersend", "positionopen", "chartopen"))
    assert '"TARGET_EXIT_MFE_MAE_AUTHORIZED":"false"' in source
    assert "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY" not in source
    assert '"NP1_G2_EVIDENCE_INVALID"' in source


def test_g2_lock_hash_size_and_canonical_self_binding() -> None:
    lock_path = PHASE / "outputs" / "manifests" / "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2_LOCK_V1.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    for relative, expected in payload["pinned_files"].items():
        path = PHASE / relative
        assert path.stat().st_size == expected["size_bytes"]
        assert G.sha256_file(path) == expected["sha256"]
    assert lock_path.stat().st_size == payload["self_size_bytes"]
    claimed = payload["self_canonical_sha256"]
    payload["self_canonical_sha256"] = "0" * 64
    canonical = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    assert hashlib.sha256(canonical).hexdigest() == claimed
