from __future__ import annotations

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_second_ea_research_safety import scan_phase0_code, scan_runtime_file_changes


def test_second_ea_safety_audit_detects_forbidden_python_pattern(tmp_path: Path):
    bad = tmp_path / "src" / "phase0" / "bad.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("def run():\n    " + "mt5." + "initialize" + "()\n", encoding="utf-8")

    findings = scan_phase0_code(tmp_path)

    assert len(findings) == 1
    assert findings[0].line_number == 2


def test_second_ea_safety_audit_detects_runtime_file_changes():
    changes = scan_runtime_file_changes(
        status_lines=[
            " M xau-usd/xauusd-phase0/src/phase0/ok.py",
            "?? xau-usd/xauusd-phase0/MQL5/Experts/SecondEA.mq5",
            " M xau-usd/xauusd-phase0/config/live.set",
            "R  old/path/foo.mqh -> xau-usd/xauusd-phase0/include/foo.mqh",
        ]
    )

    assert [change.path.as_posix() for change in changes] == [
        "xau-usd/xauusd-phase0/MQL5/Experts/SecondEA.mq5",
        "xau-usd/xauusd-phase0/config/live.set",
        "xau-usd/xauusd-phase0/include/foo.mqh",
    ]
