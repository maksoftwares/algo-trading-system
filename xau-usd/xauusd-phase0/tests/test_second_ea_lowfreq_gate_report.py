from __future__ import annotations

from pathlib import Path

from phase0.second_ea_lowfreq_gate_report import (
    VerificationResult,
    write_low_frequency_gate_test_report,
)


def test_low_frequency_gate_test_report_records_verification_results(tmp_path: Path):
    report_path = write_low_frequency_gate_test_report(
        tmp_path,
        [
            VerificationResult(
                name="Low-frequency gate and safety subset",
                command="python -m pytest tests/test_second_ea_research_gates.py tests/test_second_ea_research_safety.py",
                status="PASS",
                summary="6 passed in 0.44s",
            ),
            VerificationResult(
                name="Second-EA focused suite",
                command="python -m pytest tests/test_second_ea_missing_inputs.py",
                status="PASS",
                summary="50 passed in 4.00s",
            ),
        ],
        generated_at="2026-06-10T00:00:00+00:00",
    )

    text = report_path.read_text(encoding="utf-8")

    assert "Status: PASS" in text
    assert "Generated at UTC: 2026-06-10T00:00:00+00:00" in text
    assert "scripts/generate_second_ea_lowfreq_gate_tests.py" in text
    assert "Result: 6 passed in 0.44s" in text
    assert "Result: 50 passed in 4.00s" in text
    assert "do not authorize MT5 runtime access" in text


def test_low_frequency_gate_test_report_fails_if_any_verification_fails(tmp_path: Path):
    report_path = write_low_frequency_gate_test_report(
        tmp_path,
        [
            VerificationResult(
                name="Low-frequency gate and safety subset",
                command="python -m pytest tests/test_second_ea_research_gates.py",
                status="FAIL",
                summary="1 failed in 0.44s",
            )
        ],
        generated_at="2026-06-10T00:00:00+00:00",
    )

    assert "Status: FAIL" in report_path.read_text(encoding="utf-8")
