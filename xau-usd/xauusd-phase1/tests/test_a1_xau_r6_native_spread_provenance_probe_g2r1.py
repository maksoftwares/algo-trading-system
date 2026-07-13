from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import pytest


PHASE = Path(__file__).resolve().parents[1]
SCRIPTS = PHASE / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "run_a1_xau_r6_native_spread_provenance_probe_g2r1.py"
SPEC = importlib.util.spec_from_file_location("a1_np1_g2r1", SCRIPT)
assert SPEC and SPEC.loader
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


def _selector() -> dict[str, str]:
    return {
        "schema_version": "a1_xau_np1_g2r1_account_selector_v1",
        "login": "8642097531",
        "platform_server": "Runtime-Platform-Selection",
        "expected_account_server": "Runtime-Account-Selection",
    }


def _write_selector(path: Path, payload: dict[str, str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload or _selector()), encoding="utf-8", newline="\n")


def _authorization_fields(commit: str, tree: str) -> dict[str, str]:
    base = G.CANONICAL_REPORTS_RELATIVE
    return {
        "NP1_G2R1_EXECUTION_AUTHORIZATION_STATUS":"AUTHORIZED", "REVIEW_VERDICT":"PASS",
        "REVIEWED_EXECUTOR_COMMIT":commit, "REVIEWED_EXECUTOR_TREE":tree,
        "NEW_ROOT_PATH":str(G.NEW_ROOT), "MARKER_BYTES":"NP1 SPREAD PROBE G2R1 ONLY\\n",
        "CANONICAL_REPORTS_ROOT":base, "COMPLETE_OUTPUT_ROOT":f"{base}/{G.COMPLETE_NAME}",
        "STOP_OUTPUT_ROOT":f"{base}/{G.STOP_NAME}", "METADATA_RECEIPT_MODE":"COPIED_ALLOWLIST",
        "METADATA_SOURCE_ROOT":str(G.METADATA_SOURCE_ROOT), "METADATA_ALLOWLIST":"Config/accounts.dat,Config/servers.dat",
        "ACCOUNTS_DAT_SIZE_BYTES":"15935", "ACCOUNTS_DAT_SHA256":G.METADATA_IDENTITIES["Config/accounts.dat"][1],
        "SERVERS_DAT_SIZE_BYTES":"326364", "SERVERS_DAT_SHA256":G.METADATA_IDENTITIES["Config/servers.dat"][1],
        "ACCOUNT_SELECTOR_MODE":"EXTERNAL_RUNTIME_FILE", "ACCOUNT_SELECTOR_PATH":str(G.ACCOUNT_SELECTOR),
        "ACCOUNT_SELECTOR_COMMITTED":"false", "COMMON_LOGIN_REQUIRED":"true", "COMMON_SERVER_REQUIRED":"true",
        "TESTER_LOGIN_REQUIRED":"true", "TESTER_SERVER_KEY_AUTHORIZED":"false", "PASSWORD_IN_INI_AUTHORIZED":"false",
        "RAW_EXECUTION_INI_COMMITTED":"false", "RAW_ACCOUNT_LOGS_COMMITTED":"false", "RAW_NATIVE_REPORT_COMMITTED":"false",
        "REDACTED_ACCOUNT_EVIDENCE_REQUIRED":"true",
        "ACCOUNT_ASSERTIONS_REQUIRED":"account_login_present,account_login_matches,account_server_present,account_server_matches",
        "METAEDITOR_COMPILATIONS_MAX":"1", "STRATEGY_TESTER_RUNS_MAX":"3", "STRATEGY_TESTER_ORDER":"warmup,probe1,probe2",
        "AUTOMATIC_RETRY_AUTHORIZED":"false", "REUSE_G2A10_AUTHORIZATION_AUTHORIZED":"false", "REUSE_G2_ROOT_AUTHORIZED":"false",
        "MT5_EXECUTION_AUTHORIZED":"true", "CANONICAL_NP1C_RESULT_AUTHORIZED":"false", "R6_CENSUS_AUTHORIZED":"false",
        "PNL_AUTHORIZED":"false", "PROFITABILITY_AUTHORIZED":"false", "TARGET_EXIT_AUTHORIZED":"false",
        "MFE_MAE_AUTHORIZED":"false", "H4_PORTFOLIO_AUTHORIZED":"false", "DEMO_LIVE_ATTACH_AUTHORIZED":"false",
        "PRESET_PROFILE_ARMING_AUTHORIZED":"false", "BROKER_ACTION_AUTHORIZED":"false", "BTC_WORK_AUTHORIZED":"false",
        "DEPLOYMENT_AUTHORIZED":"false",
    }


def _write_authorization(path: Path, fields: dict[str, str]) -> None:
    body = "\n".join(f"{key}: {value}" for key, value in fields.items())
    path.write_text(f"NP1_G2R1_EXECUTION_AUTHORIZATION_BLOCK_BEGIN\n{body}\nNP1_G2R1_EXECUTION_AUTHORIZATION_BLOCK_END\n", encoding="utf-8", newline="\n")


def _write_assertions(path: Path, run_id: str) -> None:
    expected = G.WARMUP_ASSERTIONS if run_id == "warmup" else G.OFFICIAL_ASSERTIONS
    values = {value:("pass","pass") for value in expected}
    values.update(positions_zero=("0","0"),orders_zero=("0","0"),run_id=(("warmup","warmup") if run_id=="warmup" else ("official","official")))
    if run_id == "warmup": values["warmup_only"] = ("true","true")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=["assertion_id","passed","observed","expected"],delimiter="\t",lineterminator="\n")
        writer.writeheader()
        for assertion in sorted(expected):
            writer.writerow({"assertion_id":assertion,"passed":"true","observed":values[assertion][0],"expected":values[assertion][1]})


def test_builder_matches_committed_source_and_has_no_hardcoded_selector() -> None:
    payload = G.B.verify_source()
    source = G.B.SOURCE.read_text(encoding="utf-8")
    assert payload["zero_action"]
    assert "InpExpectedLogin=0" in source and 'InpExpectedAccountServer=""' in source
    assert not re.search(r"InpExpectedLogin\s*=\s*[1-9][0-9]*", source)
    assert not re.search(r'InpExpectedAccountServer\s*=\s*"[^\"]+"', source)
    assert not re.search(r"AccountInfoInteger\(ACCOUNT_LOGIN\)\s*==\s*[1-9][0-9]*", source)
    assert not re.search(r'AccountInfoString\(ACCOUNT_SERVER\)\s*==\s*"[^\"]+"', source)
    assert all(f'AssertRow("{name}"' in source for name in G.ACCOUNT_ASSERTIONS)


def test_exact_external_selector_accepts_closed_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path=tmp_path/"secrets"/"selector.json"; root=tmp_path/"root"; root.mkdir(); _write_selector(path)
    monkeypatch.setattr(G,"ACCOUNT_SELECTOR",path.absolute()); monkeypatch.setattr(G,"ROOT",tmp_path/"repo")
    assert G.load_account_selector(path,root)==_selector()


@pytest.mark.parametrize("mutation", [
    lambda p: p.pop("login"),
    lambda p: p.__setitem__("extra","x"),
    lambda p: p.__setitem__("login","0"),
    lambda p: p.__setitem__("login","12x"),
    lambda p: p.__setitem__("platform_server",""),
    lambda p: p.__setitem__("expected_account_server"," bad "),
    lambda p: p.__setitem__("password","secret"),
])
def test_selector_missing_malformed_or_extra_fields_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation) -> None:
    payload=_selector(); mutation(payload); path=tmp_path/"selector.json"; _write_selector(path,payload)
    monkeypatch.setattr(G,"ACCOUNT_SELECTOR",path.absolute()); monkeypatch.setattr(G,"ROOT",tmp_path/"repo")
    with pytest.raises(PermissionError): G.load_account_selector(path,tmp_path/"root")


@pytest.mark.parametrize("location", ["repo", "root"])
def test_selector_inside_repo_or_execution_root_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, location: str) -> None:
    repo=tmp_path/"repo"; root=tmp_path/"root"; repo.mkdir(); root.mkdir()
    path=(repo if location=="repo" else root)/"selector.json"; _write_selector(path)
    monkeypatch.setattr(G,"ACCOUNT_SELECTOR",path.absolute()); monkeypatch.setattr(G,"ROOT",repo)
    with pytest.raises(PermissionError,match="outside"): G.load_account_selector(path,root)


def test_selector_hard_link_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source=tmp_path/"source.json"; link=tmp_path/"selector.json"; _write_selector(source); os.link(source,link)
    monkeypatch.setattr(G,"ACCOUNT_SELECTOR",link.absolute()); monkeypatch.setattr(G,"ROOT",tmp_path/"repo")
    with pytest.raises(PermissionError,match="link"): G.load_account_selector(link,tmp_path/"root")


def test_selector_symlink_fails_when_supported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source=tmp_path/"source.json"; link=tmp_path/"selector.json"; _write_selector(source)
    try: link.symlink_to(source)
    except OSError: pytest.skip("symlink creation unavailable")
    monkeypatch.setattr(G,"ACCOUNT_SELECTOR",link.absolute()); monkeypatch.setattr(G,"ROOT",tmp_path/"repo")
    with pytest.raises(PermissionError,match="link"): G.load_account_selector(link,tmp_path/"root")


def test_render_ini_requires_exact_common_and_tester_selection() -> None:
    selector=_selector(); raw=G.render_ini("warmup",selector); sections=G.validate_raw_ini(raw,selector)
    assert sections["Common"]=={"Login":selector["login"],"Server":selector["platform_server"]}
    assert sections["Tester"]["Login"]==selector["login"] and "Server" not in sections["Tester"]
    assert sections["TesterInputs"]["InpExpectedAccountServer"]==selector["expected_account_server"]
    assert "Password" not in raw and "/login:" not in raw.lower()


@pytest.mark.parametrize(("old","new","match"),[
    ("Login=8642097531\nServer=Runtime-Platform-Selection", "Server=Runtime-Platform-Selection", "Common Login"),
    ("Server=Runtime-Platform-Selection", "", "Common Server"),
    ("[Tester]\nLogin=8642097531", "[Tester]", "Tester Login"),
    ("[Tester]\nLogin=8642097531", "[Tester]\nLogin=999", "Tester Login"),
])
def test_missing_or_mismatched_account_ini_keys_fail(old: str, new: str, match: str) -> None:
    with pytest.raises(RuntimeError,match=match): G.validate_raw_ini(G.render_ini("warmup",_selector()).replace(old,new,1),_selector())


@pytest.mark.parametrize("injection", ["Server=ForbiddenTesterServer\n", "Password=forbidden\n"])
def test_tester_server_or_password_key_fails(injection: str) -> None:
    raw=G.render_ini("warmup",_selector()).replace("[Tester]\n",f"[Tester]\n{injection}",1)
    with pytest.raises(RuntimeError): G.validate_raw_ini(raw,_selector())


def test_redacted_ini_proves_structure_without_values() -> None:
    selector=_selector(); redacted=G.render_redacted_ini(G.render_ini("probe1",selector),selector)
    assert G.REDACTED_LOGIN in redacted and G.REDACTED_PLATFORM_SERVER in redacted and G.REDACTED_ACCOUNT_SERVER in redacted
    assert all(value not in redacted for value in G.sensitive_values(selector))
    assert "Password" not in redacted and "[Tester]\nServer=" not in redacted


def test_runtime_text_sanitization_removes_exact_values_case_insensitively() -> None:
    selector=_selector(); raw=" ".join((selector["login"],selector["platform_server"].lower(),selector["expected_account_server"]))
    sanitized=G.sanitize_runtime_text(raw,selector)
    assert all(re.search(re.escape(value),sanitized,re.I) is None for value in G.sensitive_values(selector))


@pytest.mark.parametrize("relative", ["runs/warmup/tester.ini","runs/warmup/native_report.htm","accounts.dat","servers.dat","A1_XAU_NP1_G2R1_ACCOUNT_SELECTOR_V1.json"])
def test_raw_account_artifact_in_packet_fails(tmp_path: Path, relative: str) -> None:
    path=tmp_path/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b"redacted")
    with pytest.raises(RuntimeError,match="raw account-bearing"): G.assert_packet_redacted(tmp_path,_selector())


@pytest.mark.parametrize("container", ["complete","stop"])
def test_unredacted_selector_value_anywhere_in_candidate_packet_fails(tmp_path: Path, container: str) -> None:
    packet=tmp_path/container; packet.mkdir(); (packet/"evidence.txt").write_text(f"value={_selector()['login']}",encoding="utf-8")
    with pytest.raises(RuntimeError,match="sensitive"): G.assert_packet_redacted(packet,_selector())


def test_redacted_candidate_packet_passes(tmp_path: Path) -> None:
    (tmp_path/"runs").mkdir(); (tmp_path/"runs"/"tester.redacted.ini").write_text("Login=<REDACTED_LOGIN_MATCHED>\n",encoding="utf-8")
    G.assert_packet_redacted(tmp_path,_selector())


def test_all_four_value_free_account_assertions_are_required(tmp_path: Path) -> None:
    for run_id in G.RUN_IDS: _write_assertions(tmp_path/"runs"/run_id/"assertions.tsv",run_id)
    G.assert_exact_assertions(tmp_path)
    path=tmp_path/"runs"/"warmup"/"assertions.tsv"; rows=path.read_text(encoding="utf-8").splitlines(); path.write_text("\n".join(row for row in rows if not row.startswith("account_server_matches\t"))+"\n",encoding="utf-8")
    with pytest.raises(RuntimeError,match="assertion set"): G.assert_exact_assertions(tmp_path)


def test_account_assertion_observations_cannot_emit_values(tmp_path: Path) -> None:
    for run_id in G.RUN_IDS: _write_assertions(tmp_path/"runs"/run_id/"assertions.tsv",run_id)
    path=tmp_path/"runs"/"probe1"/"assertions.tsv"; text=path.read_text(encoding="utf-8").replace("account_login_matches\ttrue\tpass\tpass",f"account_login_matches\ttrue\t{_selector()['login']}\tpass")
    path.write_text(text,encoding="utf-8")
    with pytest.raises(RuntimeError,match="observed/expected"): G.assert_exact_assertions(tmp_path)


def test_exact_future_authorization_accepts_only_g2a11_commit_derived_artifact(tmp_path: Path) -> None:
    commit,tree="a"*40,"b"*40; path=tmp_path/f"A1_XAU_NP1G2A11_EXECUTION_AUTHORIZATION_{commit[:8].upper()}_2026_07_13.md"; fields=_authorization_fields(commit,tree); _write_authorization(path,fields)
    assert G.parse_future_authorization(path,G.sha256_file(path),commit,tree)==fields
    old=tmp_path/f"A1_XAU_NP1G2A10_EXECUTION_AUTHORIZATION_{commit[:8].upper()}_2026_07_13.md"; old.write_bytes(path.read_bytes())
    with pytest.raises(PermissionError): G.parse_future_authorization(old,G.sha256_file(old),commit,tree)


@pytest.mark.parametrize(("key","value"),[("AUTOMATIC_RETRY_AUTHORIZED","true"),("REUSE_G2A10_AUTHORIZATION_AUTHORIZED","true"),("REUSE_G2_ROOT_AUTHORIZED","true"),("PNL_AUTHORIZED","true"),("BTC_WORK_AUTHORIZED","true")])
def test_future_authorization_fails_if_any_boundary_is_enabled(tmp_path: Path, key: str, value: str) -> None:
    commit,tree="c"*40,"d"*40; path=tmp_path/f"A1_XAU_NP1G2A11_EXECUTION_AUTHORIZATION_{commit[:8].upper()}_2026_07_13.md"; fields=_authorization_fields(commit,tree); fields[key]=value; _write_authorization(path,fields)
    with pytest.raises(PermissionError): G.parse_future_authorization(path,G.sha256_file(path),commit,tree)


def test_consumed_root_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fresh=tmp_path/"fresh"; consumed=tmp_path/"consumed"; fresh.mkdir(); consumed.mkdir()
    monkeypatch.setattr(G,"NEW_ROOT",fresh); monkeypatch.setattr(G,"QUARANTINED_ROOTS",(consumed,))
    (consumed/G.MARKER).write_bytes(G.MARKER_BYTES); (consumed/"terminal64.exe").write_bytes(b"x"); (consumed/"MetaEditor64.exe").write_bytes(b"x")
    with pytest.raises(RuntimeError,match="exact new root|quarantined"): G.validate_exact_root(consumed,initial=True)


def test_ledger_forbids_second_compile_out_of_order_adaptive_and_fourth_run(tmp_path: Path) -> None:
    ledger=G.Ledger(tmp_path/"ledger.json"); ledger.compilation()
    with pytest.raises(RuntimeError,match="second"): ledger.compilation()
    with pytest.raises(RuntimeError,match="adaptive"): ledger.run("probe1")
    for run_id in G.RUN_IDS: ledger.run(run_id)
    with pytest.raises(RuntimeError,match="fourth"): ledger.run("warmup")


def test_warmup_stop_packet_prevents_probe_claims_and_is_redacted(tmp_path: Path) -> None:
    selector=_selector(); root=tmp_path/"root"; root.mkdir(); ledger=G.Ledger(root/"ledger.json"); ledger.compilation(); ledger.run("warmup")
    ini=root/"Config"/"np1_g2r1_warmup.ini"; ini.parent.mkdir(); ini.write_text(G.render_ini("warmup",selector),encoding="utf-8")
    stop=tmp_path/"stop"; G.preserve_stop_packet(stop=stop,root=root,ledger=ledger.path,preflight=G.inventory(root),reports_attestation={},commands=[],run_ids=["warmup"],error=RuntimeError("warmup failed"),selector=selector)
    result=json.loads((stop/"result.json").read_text()); assert result["status"]=="NP1_G2R1_EVIDENCE_INVALID" and not result["probe1_invoked"] and not result["probe2_invoked"]
    assert (stop/"runs"/"warmup"/"tester.redacted.ini").is_file() and not (stop/"runs"/"warmup"/"tester.ini").exists()
    G.assert_packet_redacted(stop,selector); G.verify_manifest(stop)


def test_command_records_never_include_login_or_server_values(tmp_path: Path) -> None:
    root=tmp_path/"root"; (root/"MQL5"/"Experts").mkdir(parents=True); (root/"Config").mkdir()
    class Done:
        returncode=0; stdout=b""; stderr=b""
    commands=[G.G1.record([str(root/"MetaEditor64.exe"),f"/compile:{root/'MQL5'/'Experts'/G.B.PROBE_NAME}",f"/log:{root/'compile.log'}"],Done())]
    commands.extend(G.G1.record([str(root/"terminal64.exe"),"/portable",f"/config:{root/'Config'/f'np1_g2r1_{run_id}.ini'}"],Done()) for run_id in G.RUN_IDS)
    G.validate_command_records(commands,root)
    joined=json.dumps(commands); assert all(value not in joined for value in G.sensitive_values(_selector())) and "/login:" not in joined.lower()


def test_static_preserves_prior_scientific_and_no_action_controls() -> None:
    source=SCRIPT.read_text(encoding="utf-8"); combined=source+G.B.SOURCE.read_text(encoding="utf-8"); lowered=combined.lower()
    assert all(token in combined for token in ("validate_native_exports", "semantic_verify_packet", "CopyTicksRange", "tick timestamps decreasing", "assert_packet_redacted"))
    assert all(token not in lowered for token in ("order.send", "ordersend", "positionopen", "chartopen", "net_profit", "profit_factor"))
    assert '"PNL_AUTHORIZED":"false"' in source and '"DEPLOYMENT_AUTHORIZED":"false"' in source


def test_contract_exactly_matches_runner_privacy_and_future_boundaries() -> None:
    contract=json.loads((PHASE/"docs"/"A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2R1_CONTRACT_V1.json").read_text(encoding="utf-8"))
    assert contract["authorization"]["phase"]=="NP1-G2A11_EXPLICIT_ACCOUNT_SELECTION_PRIVACY_CLOSURE"
    assert contract["authorization"]["boundary"]=="REPO_ONLY" and not contract["authorization"]["mt5_execution_authorized"] and not contract["authorization"]["root_preparation_authorized"]
    assert set(contract["account_selector"]["closed_schema_fields"])==G.SELECTOR_FIELDS
    assert contract["account_selector"]["exact_path"]==str(G.ACCOUNT_SELECTOR)
    assert set(contract["account_selection"]["value_free_assertions"])==G.ACCOUNT_ASSERTIONS
    future=contract["future_campaign_reserved_not_activated"]
    assert future["new_root"]==str(G.NEW_ROOT) and future["strategy_tester_order"]==list(G.RUN_IDS) and not future["automatic_retry_authorized"]
    assert all(value is False for value in contract["prohibitions"].values())


def test_g2r1_lock_hash_size_and_canonical_self_binding() -> None:
    lock_path=PHASE/"outputs"/"manifests"/"A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_G2R1_LOCK_V1.json"
    payload=json.loads(lock_path.read_text(encoding="utf-8"))
    for relative,expected in payload["pinned_files"].items():
        path=PHASE/relative; assert path.stat().st_size==expected["size_bytes"] and G.sha256_file(path)==expected["sha256"]
    assert lock_path.stat().st_size==payload["self_size_bytes"]
    claimed=payload["self_canonical_sha256"]; payload["self_canonical_sha256"]="0"*64
    canonical=(json.dumps(payload,indent=2,sort_keys=True)+"\n").encode(); assert hashlib.sha256(canonical).hexdigest()==claimed
