from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_paper_ledger_schema_report_passes_complete_schema(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    (root / "docs").mkdir(parents=True)
    _write_schema_doc(root / "docs" / "PHASE2_PAPER_LEDGER_SCHEMA.md", module)

    output = module.generate_phase2_paper_ledger_schema_report(root)

    report = output.report_path.read_text(encoding="utf-8")
    with output.columns_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert output.status == "PASS"
    assert "paper-ledger evidence contract is defined" in report
    assert len(rows) == len(module.REQUIRED_COLUMNS)
    assert rows[0]["column"] == "event_id"


def test_phase2_paper_ledger_schema_report_fails_missing_schema(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"

    output = module.generate_phase2_paper_ledger_schema_report(root)

    assert output.status == "FAIL"
    assert any(check.name == "schema_doc" and check.status == "FAIL" for check in output.checks)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_paper_ledger_schema_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_paper_ledger_schema_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_paper_ledger_schema_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_schema_doc(path: Path, module) -> None:
    columns = "\n".join(f"- {name}" for name, *_ in module.REQUIRED_COLUMNS)
    tokens = "\n".join(f"- {token}" for token in module.REQUIRED_TOKENS)
    path.write_text(f"# Schema\n\n{columns}\n\n## Controls\n\n{tokens}\n", encoding="utf-8")
