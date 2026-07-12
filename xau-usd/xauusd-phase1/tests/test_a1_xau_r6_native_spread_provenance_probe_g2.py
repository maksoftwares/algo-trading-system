from __future__ import annotations

import importlib.util
import hashlib
import json
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
        copied.append({"source_path": str(source), "destination_relative": f"Config/{name}", "size_bytes": destination.stat().st_size, "sha256": G.sha256_file(destination)})
    G.validate_metadata_receipt(root, {"copied": copied})
    copied.append({"source_path": str(old / "Config" / "common.ini"), "destination_relative": "Config/common.ini", "size_bytes": 0, "sha256": "0" * 64})
    with pytest.raises(RuntimeError, match="unexpected"):
        G.validate_metadata_receipt(root, {"copied": copied})


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
    stop = G.preserve_stop_packet(stop=tmp_path / "stop", root=root, ledger=ledger.path, preflight={"pre": True}, reports_attestation={"writable": True}, commands=[{"exit_code": 0}], run_ids=["warmup"], error=RuntimeError("missing report"))
    assert json.loads((stop / "result.json").read_text(encoding="utf-8"))["status"] == "NP1_G2_EVIDENCE_INVALID"
    assert (stop / "invocation_ledger.json").is_file() and (stop / "preflight_root_inventory.json").is_file() and (stop / "post_stop_root_inventory.json").is_file()
    assert (stop / "logs" / "log_inventory.json").is_file() and (stop / "runs" / "warmup" / "assertions.tsv").is_file()
    assert (stop / "manifest.json").is_file() and (stop / "manifest.sha256").is_file()


def test_ex5_drift_is_fail_closed(tmp_path: Path) -> None:
    ex5 = tmp_path / "probe.ex5"; ex5.write_bytes(b"one"); expected = G.sha256_file(ex5); ex5.write_bytes(b"two")
    assert G.sha256_file(ex5) != expected


def test_g2a_cli_and_executor_are_not_authorized(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="repo-only"):
        G.execute_future(authorization="", review_artifact=tmp_path / "none", root=tmp_path, reports_root=tmp_path)


def test_static_no_normalization_result_research_attach_or_broker_action() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    lowered = source.lower()
    assert all(token not in lowered for token in ("abs(spread", "max(spread", "net_profit", "profit_factor", "mfe", "mae", "order.send", "ordersend", "positionopen", "chartopen"))
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
