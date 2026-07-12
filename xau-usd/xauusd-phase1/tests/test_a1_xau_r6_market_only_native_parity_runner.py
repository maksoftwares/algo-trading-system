from __future__ import annotations

import importlib.util
import sys
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
    )

    assert result.ex5.is_file()
    assert result.log.is_file()
    assert len(fake.commands) == 1
    assert fake.commands[0][1].startswith("/compile:")
    assert fake.commands[0][2].startswith("/log:")


def test_compile_only_fails_closed_on_warning_or_non_temp_workspace(tmp_path: Path) -> None:
    editor = _metaeditor(tmp_path / "editor" / "MetaEditor64.exe")
    with pytest.raises(RuntimeError, match="temporary/test/compile"):
        R.compile_only_safety_check(metaeditor=editor, workspace=tmp_path / "production", command_runner=FakeMetaEditor())
    with pytest.raises(RuntimeError, match="zero warnings"):
        R.compile_only_safety_check(
            metaeditor=editor, workspace=tmp_path / "compile-test", command_runner=FakeMetaEditor(warnings=1)
        )


def test_historical_campaign_is_review_gated_and_ini_is_isolated(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="prohibited"):
        R.run_historical_evidence_campaign(
            authorization="NOT_AUTHORIZED",
            tester_sandbox=tmp_path / "tester",
            compiled_ex5=tmp_path / "oracle.ex5",
            output_dir=tmp_path / "evidence",
        )

    ini = R.render_tester_ini(run_id="run1", report_relative="Reports/np1_run1")
    R.assert_tester_ini_contract(ini)
    assert "Login=" not in ini
    assert "Server=" not in ini
    assert "UseRemote=0" in ini and "UseCloud=0" in ini
    assert "FromDate=2015.06.01" in ini and "ToDate=2026.07.01" in ini
