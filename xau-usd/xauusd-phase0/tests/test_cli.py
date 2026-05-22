from __future__ import annotations

from phase0.cli import build_parser, main


def test_cli_registers_required_commands():
    help_text = build_parser().format_help()

    assert "validate-config" in help_text
    assert "run-matrix" in help_text
    assert "normalize-bars" in help_text
    assert "import-required-bars" in help_text
    assert "generate-data-requirements" in help_text
    assert "generate-data-readiness" in help_text
    assert "generate-data-manifest" in help_text
    assert "generate-mt5-bar-presets" in help_text
    assert "generate-verdict" in help_text
    assert "generate-result-manifest" in help_text
    assert "generate-snapshot" in help_text
    assert "analyze-spread-logs" in help_text
    assert "generate-measured-cost-model" in help_text
    assert "generate-measured-cost-revalidation" in help_text
    assert "check-passive-spread-logger" in help_text
    assert "generate-independent-reproduction" in help_text
    assert "audit-true-holdout" in help_text
    assert "run-cpcv-validation" in help_text
    assert "run-reality-check" in help_text
    assert "register-research-hypothesis" in help_text
    assert "run-research-candidate-smoke" in help_text
    assert "run-research-matrix" in help_text
    assert "generate-fixed-notional-report" in help_text


def test_validate_config_command(project_root, capsys):
    exit_code = main(["--root", str(project_root), "validate-config"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Config OK" in captured.out


def test_cli_writes_run_log(project_root, tmp_path, capsys):
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    for path in (project_root / "config").glob("*.yaml"):
        (root / "config" / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = main(["--root", str(root), "validate-config"])

    assert exit_code == 0
    assert list((root / "outputs" / "logs").glob("phase0_run_*.log"))
