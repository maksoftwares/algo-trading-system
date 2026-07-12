from __future__ import annotations

import importlib.util
import csv
import hashlib
import json
import shutil
import sys
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


def _tsv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns,delimiter="\t",lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def _write_campaign_outputs(root: Path, run_id: str) -> None:
    report=root/"Reports"/f"np1_g2_{run_id}.htm"
    report.write_text("<table><tr><td>Period:</td><td>H1</td><td>Bars:</td><td>1</td><td>Ticks:</td><td>1</td><td>Total Trades:</td><td>0</td><td>Total Deals:</td><td>0</td></tr></table>",encoding="utf-8")
    files=root/"Tester"/"Agent-1"/"MQL5"/"Files"; files.mkdir(parents=True,exist_ok=True)
    prefix=f"np1_g2_{run_id}_"
    ids=G.WARMUP_ASSERTIONS if run_id=="warmup" else G.OFFICIAL_ASSERTIONS
    _tsv(files/f"{prefix}assertions.tsv",["assertion_id","passed","observed","expected"],[{"assertion_id":value,"passed":"true","observed":"pass","expected":"pass"} for value in sorted(ids)])
    (files/f"{prefix}order.zero").write_bytes(b""); (files/f"{prefix}deal.zero").write_bytes(b"")
    if run_id=="warmup": return
    for tf in ("h1","h4","d1"): _tsv(files/f"{prefix}{tf}_bars.tsv",["open_time_broker","spread"],[{"open_time_broker":"2025-06-18T03:00:00","spread":"5"}])
    _tsv(files/f"{prefix}bar_spread_interfaces.tsv",["timeframe","open_time_broker","copyrates_spread","copyspread_spread","ispread_spread"],[{"timeframe":"H1","open_time_broker":"2025-06-18T03:00:00","copyrates_spread":"5","copyspread_spread":"5","ispread_spread":"5"}])
    columns=["schema_version","broker_day","time_msc","time","bid","ask","last","volume","volume_real","flags","raw_ask_minus_bid","raw_spread_points","negative_spread_boolean","quote_sides_positive","copyticks_return","copyticks_error"]
    row={"schema_version":"v1","broker_day":"d","time_msc":"1","time":"t","bid":"10","ask":"11","last":"0","volume":"1","volume_real":"1","flags":"1","raw_ask_minus_bid":"1","raw_spread_points":"1","negative_spread_boolean":"false","quote_sides_positive":"true","copyticks_return":"1","copyticks_error":"0"}
    for name in G.G1.OFFICIAL_NAMES:
        if name.startswith("ticks_"): _tsv(files/f"{prefix}{name}",columns,[row])


def _auth_fields(commit: str, tree: str) -> dict[str,str]:
    base=G.CANONICAL_REPORTS_RELATIVE
    return {"NP1_G2B_AUTHORIZATION_STATUS":"AUTHORIZED","REVIEW_VERDICT":"PASS","REVIEWED_EXECUTOR_COMMIT":commit,"REVIEWED_EXECUTOR_TREE":tree,"NEW_ROOT_PATH":str(G.NEW_ROOT),"MARKER_BYTES":"NP1 SPREAD PROBE G2 ONLY\\n","CANONICAL_REPORTS_ROOT":base,"COMPLETE_OUTPUT_ROOT":f"{base}/{G.COMPLETE_NAME}","STOP_OUTPUT_ROOT":f"{base}/{G.STOP_NAME}","METADATA_RECEIPT_MODES":"COPIED_ALLOWLIST,ZERO_COPY","METADATA_ALLOWLIST":"Config/accounts.dat,Config/servers.dat","METAEDITOR_COMPILATIONS_MAX":"1","STRATEGY_TESTER_RUNS_MAX":"3","STRATEGY_TESTER_ORDER":"warmup,probe1,probe2","MT5_EXECUTION_AUTHORIZED":"true","CANONICAL_NP1C_RESULT_AUTHORIZED":"false","R6_CENSUS_AUTHORIZED":"false","PNL_AUTHORIZED":"false","TARGET_EXIT_MFE_MAE_AUTHORIZED":"false","DEMO_LIVE_ATTACH_AUTHORIZED":"false","PRESET_PROFILE_ARMING_AUTHORIZED":"false","BROKER_ACTION_AUTHORIZED":"false","DEPLOYMENT_AUTHORIZED":"false"}


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
    path = tmp_path / "A1_XAU_NP1G2A5_EXECUTION_AUTHORIZATION_D8699D6E_2026_07_13.md"
    commit, tree = "a" * 40, "b" * 40
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
    review=tmp_path/"A1_XAU_NP1G2A5_EXECUTION_AUTHORIZATION_D8699D6E_2026_07_13.md"
    fields=_auth_fields(commit,tree)
    review.write_text("NP1_G2B_AUTHORIZATION_BLOCK_BEGIN\n"+"\n".join(f"{k}: {v}" for k,v in fields.items())+"\nNP1_G2B_AUTHORIZATION_BLOCK_END\n",encoding="utf-8")
    class C: pass
    def compile_fake(root,editor,runner,version_reader):
        experts=root/"MQL5"/"Experts"; experts.mkdir(parents=True); source=experts/G.B.PROBE_NAME; source.write_text(G.B.render_probe(),encoding="utf-8"); ex5=source.with_suffix('.ex5'); ex5.write_bytes(b'ex5'); log=root/'compile.log'; log.write_text('0 errors 0 warnings'); return G.G1.CompileResult(source,ex5,log,G.sha256_file(source),G.sha256_file(ex5),G.G1.EXPECTED_VERSION,{"command":[str(editor),f"/compile:{source}"],"exit_code":0})
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
    review=tmp_path/"A1_XAU_NP1G2A5_EXECUTION_AUTHORIZATION_D8699D6E_2026_07_13.md"; fields=_auth_fields(commit,tree); review.write_text("NP1_G2B_AUTHORIZATION_BLOCK_BEGIN\n"+"\n".join(f"{k}: {v}" for k,v in fields.items())+"\nNP1_G2B_AUTHORIZATION_BLOCK_END\n",encoding="utf-8")
    def comp(root,editor,runner,version_reader):
        e=root/"MQL5"/"Experts"; e.mkdir(parents=True); s=e/G.B.PROBE_NAME; s.write_text(G.B.render_probe(),encoding="utf-8"); x=s.with_suffix('.ex5'); x.write_bytes(b'x'); log=root/'compile.log'; log.write_text('0 errors 0 warnings'); return G.G1.CompileResult(s,x,log,G.sha256_file(s),G.sha256_file(x),G.G1.EXPECTED_VERSION,{"command":[str(editor),f"/compile:{s}"],"exit_code":0})
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
    tampered=tmp_path/"tampered-result"; shutil.copytree(complete,tampered); payload=json.loads((tampered/"result.json").read_text()); payload["flags"].append("STALE"); (tampered/"result.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    with pytest.raises(RuntimeError,match="semantic recomputation"): G.semantic_verify_packet(tampered,tmp_path/"scratch-result",context)
    tampered_auth=tmp_path/"tampered-auth"; shutil.copytree(complete,tampered_auth); auth=json.loads((tampered_auth/"authorization_attestation.json").read_text()); auth["sha256"]="0"*64; G.write_json(tampered_auth/"authorization_attestation.json",auth)
    with pytest.raises(RuntimeError,match="authorization attestation"): G.semantic_verify_packet(tampered_auth,tmp_path/"scratch-auth",context)
    tampered_assert=tmp_path/"tampered-assert"; shutil.copytree(complete,tampered_assert); assertion=tampered_assert/"runs"/"warmup"/"assertions.tsv"; lines=assertion.read_text().splitlines(); assertion.write_text("\n".join(lines[:-1])+"\n",encoding="utf-8"); selected=json.loads((tampered_assert/"searched_location_inventory.json").read_text()); row=next(item for item in selected["selected_sources"] if item["kind"]=="assertions.tsv" and "warmup" in item["source"]); row["size_bytes"]=assertion.stat().st_size; row["sha256"]=G.sha256_file(assertion); G.write_json(tampered_assert/"searched_location_inventory.json",selected)
    with pytest.raises(RuntimeError,match="assertion set"): G.semantic_verify_packet(tampered_assert,tmp_path/"scratch-assert",context)


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
