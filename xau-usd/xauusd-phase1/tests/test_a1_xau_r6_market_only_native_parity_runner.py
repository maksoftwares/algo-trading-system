from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load():
    path = SCRIPTS / "run_a1_xau_r6_market_only_native_parity_exact.py"
    spec = importlib.util.spec_from_file_location("np1_runner", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = _load()


class FakeMetaEditor:
    def __init__(self, *, returncode: int = 1, errors: int = 0, warnings: int = 0):
        self.returncode = returncode
        self.errors = errors
        self.warnings = warnings
        self.commands: list[list[str]] = []

    def __call__(self, command, cwd: Path, timeout_seconds: int):
        command = [str(value) for value in command]
        self.commands.append(command)
        source = Path(next(value for value in command if value.startswith("/compile:")).split(":", 1)[1])
        log = Path(next(value for value in command if value.startswith("/log:")).split(":", 1)[1])
        source.with_suffix(".ex5").write_bytes(b"NP1_COMPILE_ONLY_EX5")
        log.write_text(
            f"MetaEditor 5 x64 build 5833\nResult: {self.errors} errors, {self.warnings} warnings\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=self.returncode, stdout=b"", stderr=b"")


def _metaeditor(path: Path) -> Path:
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    return path


def test_compile_only_accepts_build_5833_exit_one_in_temp_workspace(tmp_path: Path) -> None:
    fake = FakeMetaEditor(returncode=1)
    result = R.compile_only_safety_check(
        metaeditor=_metaeditor(tmp_path / "editor" / "MetaEditor64.exe"),
        workspace=tmp_path / "compile-test",
        command_runner=fake,
        version_reader=lambda _: "5.0.0.5833",
    )

    assert result.ex5.is_file()
    assert result.log.is_file()
    assert len(fake.commands) == 1
    assert fake.commands[0][1].startswith("/compile:")
    assert fake.commands[0][2].startswith("/log:")


def test_compile_only_fails_closed_on_warning_or_non_temp_workspace(tmp_path: Path) -> None:
    editor = _metaeditor(tmp_path / "editor" / "MetaEditor64.exe")
    with pytest.raises(RuntimeError, match="temporary/test/compile"):
        R.compile_only_safety_check(metaeditor=editor, workspace=tmp_path / "production", command_runner=FakeMetaEditor(), version_reader=lambda _: "5.0.0.5833")
    with pytest.raises(RuntimeError, match="zero warnings"):
        R.compile_only_safety_check(
            metaeditor=editor, workspace=tmp_path / "compile-test", command_runner=FakeMetaEditor(warnings=1), version_reader=lambda _: "5.0.0.5833"
        )
    with pytest.raises(RuntimeError, match="must be 5.0.0.5833"):
        R.compile_only_safety_check(
            metaeditor=editor, workspace=tmp_path / "compile-test-build", command_runner=FakeMetaEditor(),
            version_reader=lambda _: "5.0.0.9999",
        )


def test_historical_campaign_is_review_gated_and_ini_is_isolated(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="prohibited"):
        R.run_historical_evidence_campaign(
            authorization="NOT_AUTHORIZED",
            tester_sandbox=tmp_path / "tester",
            metaeditor=tmp_path / "MetaEditor64.exe",
            compile_workspace=tmp_path / "compile-test",
            output_dir=tmp_path / "evidence",
        )

    ini = R.render_tester_ini(run_id="run1", report_relative="Reports/np1_run1")
    R.assert_tester_ini_contract(ini)
    assert "Login=" not in ini
    assert "Server=" not in ini
    assert "UseRemote=0" in ini and "UseCloud=0" in ini
    assert "FromDate=2015.06.01" in ini and "ToDate=2026.07.01" in ini
    assert "InpRouterRowsFileName=np1_run1_native_router_rows.tsv" in ini
    assert "InpOrderZeroFileName=np1_run1_order.zero" in ini


def test_run_outputs_are_collected_by_unique_run_name_without_overwrite(tmp_path: Path) -> None:
    sandbox = tmp_path / "tester"
    files = sandbox / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    reports = sandbox / "Reports"
    files.mkdir(parents=True)
    reports.mkdir()
    destination = tmp_path / "evidence" / "runs"
    for run_id in ("run1", "run2"):
        ini = tmp_path / f"{run_id}.ini"
        ini.write_text(R.render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}"), encoding="utf-8")
        (reports / f"np1_{run_id}.htm").write_text(f"report-{run_id}", encoding="utf-8")
        for destination_name, emitted_name in R.emitted_names(run_id).items():
            (files / emitted_name).write_bytes(b"" if destination_name.endswith(".zero") else f"{run_id}:{destination_name}".encode())
        R.collect_run_outputs(sandbox, run_id, ini, destination / run_id)

    assert (destination / "run1" / "native_router_rows.tsv").read_text() == "run1:native_router_rows.tsv"
    assert (destination / "run2" / "native_router_rows.tsv").read_text() == "run2:native_router_rows.tsv"
    assert (destination / "run1" / "order.zero").stat().st_size == 0
    assert (destination / "run2" / "deal.zero").stat().st_size == 0


def test_collection_rejects_ambiguous_agent_outputs(tmp_path: Path) -> None:
    sandbox = tmp_path / "tester"
    ini = tmp_path / "run1.ini"
    ini.write_text("locked", encoding="utf-8")
    reports = sandbox / "Reports"
    reports.mkdir(parents=True)
    (reports / "np1_run1.htm").write_text("report", encoding="utf-8")
    for agent in ("Agent-a", "Agent-b"):
        files = sandbox / "Tester" / agent / "MQL5" / "Files"
        files.mkdir(parents=True)
        for emitted_name in R.emitted_names("run1").values():
            (files / emitted_name).write_bytes(b"")
    with pytest.raises(RuntimeError, match="expected exactly one isolated"):
        R.collect_run_outputs(sandbox, "run1", ini, tmp_path / "run")


def test_exact_ini_parser_rejects_duplicate_keys_and_stale_report(tmp_path: Path) -> None:
    ini_text = R.render_tester_ini(run_id="run1", report_relative="Reports/np1_run1")
    with pytest.raises(RuntimeError, match="duplicate"):
        R.assert_tester_ini_contract(ini_text.replace("Symbol=XAUUSD", "Symbol=XAUUSD\nSymbol=XAUUSD"))

    sandbox = tmp_path / "tester"
    files = sandbox / "Tester" / "Agent-a" / "MQL5" / "Files"
    files.mkdir(parents=True)
    report = sandbox / "Reports" / "np1_run1.htm"
    report.parent.mkdir()
    report.write_text("stale", encoding="utf-8")
    old = time.time_ns() - 10_000_000_000
    os.utime(report, ns=(old, old))
    ini = tmp_path / "run1.ini"
    ini.write_text(ini_text, encoding="utf-8")
    for destination_name, emitted_name in R.emitted_names("run1").items():
        (files / emitted_name).write_bytes(b"" if destination_name.endswith(".zero") else b"fresh")
    with pytest.raises(RuntimeError, match="stale"):
        R.collect_run_outputs(sandbox, "run1", ini, tmp_path / "run", not_before_ns=time.time_ns())


def test_end_to_end_fake_campaign_isolated_collects_and_attests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sandbox = tmp_path / "tester"
    sandbox.mkdir()
    (sandbox / ".a1_xau_np1_tester_only").write_text("NP1 TESTER ONLY\n", encoding="utf-8")
    (sandbox / "terminal64.exe").write_bytes(b"")
    editor = _metaeditor(tmp_path / "editor" / "MetaEditor64.exe")
    agent_files = sandbox / "Tester" / "Agent-fake" / "MQL5" / "Files"
    agent_files.mkdir(parents=True)

    class FakeTerminal:
        def __init__(self):
            self.commands = []

        def __call__(self, command, cwd: Path, timeout_seconds: int):
            self.commands.append(list(command))
            run_id = Path(next(value for value in command if str(value).startswith("/config:")).split(":", 1)[1]).stem.removeprefix("np1_")
            reports = sandbox / "Reports"
            reports.mkdir(exist_ok=True)
            (reports / f"np1_{run_id}.htm").write_text(f"fresh-{run_id}", encoding="utf-8")
            for destination_name, emitted_name in R.emitted_names(run_id).items():
                (agent_files / emitted_name).write_bytes(b"" if destination_name.endswith(".zero") else f"{run_id}:{destination_name}".encode())
            return SimpleNamespace(returncode=0, stdout=b"terminal-out", stderr=b"")

    captured = {}
    import verify_a1_xau_r6_market_only_native_parity as verifier

    def fake_finalize(path: Path, *, attestation):
        captured["path"], captured["attestation"] = path, attestation
        (path / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json").write_text(
            '{"status":"R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS","errors":[]}\n', encoding="utf-8"
        )
        return SimpleNamespace(status="R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS", errors=())

    monkeypatch.setattr(verifier, "finalize_evidence_directory", fake_finalize)
    monkeypatch.setattr(R, "capture_clean_git_identity", lambda: {"git_head": "a" * 40, "git_tree": "b" * 40, "git_status_porcelain": ""})
    monkeypatch.setattr(
        R, "build_campaign_attestation",
        lambda output_dir, compiled, commands, git_identity, review_authority, finalizer_commands: {
            "commands": commands, "artifact_sha256": {}
        },
    )
    terminal = FakeTerminal()
    output = tmp_path / "evidence"
    review_artifact = tmp_path / "A1_XAU_NP1B3_PASS_REVIEW_TEST.md"
    review_artifact.write_text("reviewed\n", encoding="utf-8")
    produced = R.run_historical_evidence_campaign(
        authorization=R.NP1_C_AUTHORIZATION, tester_sandbox=sandbox, metaeditor=editor,
        compile_workspace=tmp_path / "compile-test", output_dir=output, command_runner=terminal,
        compile_command_runner=FakeMetaEditor(), metaeditor_version_reader=lambda _: "5.0.0.5833",
        verification_command_runner=lambda command, cwd, timeout: SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
        review_artifact=review_artifact, review_sha256=R.sha256_file(review_artifact),
        reviewed_generator_commit="a" * 40, reviewed_generator_tree="b" * 40,
    )
    assert produced == [output / "runs" / "run1", output / "runs" / "run2"]
    assert len(terminal.commands) == 2 and len(captured["attestation"]["commands"]) == 2
    assert (output / "runs" / "run1" / "native_router_rows.tsv").read_text() == "run1:native_router_rows.tsv"
    assert (output / "runs" / "run2" / "native_router_rows.tsv").read_text() == "run2:native_router_rows.tsv"
