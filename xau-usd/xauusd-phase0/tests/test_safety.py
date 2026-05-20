from __future__ import annotations

from pathlib import Path

from phase0.cli import main
from phase0.config import ProjectConfig, load_project_config
from phase0.safety import audit_no_live_trading_calls


def test_safety_audit_passes_project_sources(project_root):
    config = load_project_config(project_root)

    assert audit_no_live_trading_calls(config) == []


def test_safety_audit_detects_forbidden_call(tmp_path):
    path = tmp_path / "project" / "src" / "phase0" / "bad.py"
    path.parent.mkdir(parents=True)
    path.write_text("def bad():\n    " + "Order" + "Send" + "()\n", encoding="utf-8")
    config = ProjectConfig(
        root=tmp_path / "project",
        phase0={},
        symbols={},
        cost_models={},
        broker_sources={},
        true_holdout={},
    )

    findings = audit_no_live_trading_calls(config)

    assert len(findings) == 1
    assert findings[0].line_number == 2


def test_audit_safety_cli(project_root, capsys):
    exit_code = main(["--root", str(project_root), "audit-safety"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Safety audit OK" in captured.out
