from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARSER = load("parse_mt5_effective_inputs")
VERIFY = load("verify_a1_xau_effective_inputs")


def report_text(day_mask: str = "5:20", long_mask: str = "3,10,13,14") -> str:
    return f"""<html><body><table>
<tr><td colspan='13'><div><b>Capital.ComMena-Demo (Build 5833)</b></div></td></tr>
<tr><td>Expert:</td><td><b>ExampleEA</b></td></tr>
<tr><td>Symbol:</td><td><b>XAUUSD</b></td></tr>
<tr><td>Period:</td><td><b>M5 (2016.07.01 - 2026.06.30)</b></td></tr>
<tr><td>Inputs:</td><td><b>InpLegacySelectionMasksEnabled=false</b></td></tr>
<tr><td></td><td><b>InpBlockedEntryDayHoursCsv={day_mask}</b></td></tr>
<tr><td></td><td><b>InpBlockedLongEntryHoursCsv={long_mask}</b></td></tr>
<tr><td>Company:</td><td><b>Capital Com Mena Securities Trading L.L.C</b></td></tr>
<tr><td>Currency:</td><td><b>USD</b></td></tr>
<tr><td>Initial Deposit:</td><td><b>10 000.00</b></td></tr>
<tr><td>Leverage:</td><td><b>1:50</b></td></tr>
</table></body></html>"""


def test_parser_reads_effective_inputs_and_native_environment(tmp_path: Path) -> None:
    report = tmp_path / "report.htm"
    report.write_text(report_text(), encoding="utf-16")
    inputs = PARSER.parse_effective_inputs(report)
    environment = PARSER.parse_native_environment(report)
    assert inputs == {
        "InpLegacySelectionMasksEnabled": "false",
        "InpBlockedEntryDayHoursCsv": "5:20",
        "InpBlockedLongEntryHoursCsv": "3,10,13,14",
    }
    assert environment["server"] == "Capital.ComMena-Demo"
    assert environment["build"] == "5833"
    assert environment["currency"] == "USD"
    assert environment["leverage"] == "1:50"


def test_ini_empty_native_nonempty_is_hard_mismatch(tmp_path: Path) -> None:
    report = tmp_path / "report.htm"
    report.write_text(report_text(), encoding="utf-16")
    config = tmp_path / "tester.ini"
    config.write_text(
        "[TesterInputs]\n"
        "InpLegacySelectionMasksEnabled=false\n"
        "InpBlockedEntryDayHoursCsv=\n"
        "InpBlockedLongEntryHoursCsv=\n",
        encoding="utf-8",
    )
    lock = tmp_path / "lock.json"
    expected = PARSER.parse_tester_ini_inputs(config)
    lock.write_text(
        json.dumps({"horizons": {"ten_year": {"tester_inputs": expected}}}),
        encoding="utf-8",
    )
    payload = VERIFY.verify(report=report, lock=lock, horizon="ten_year", tester_config=config)
    assert payload["status"] == "EFFECTIVE_INPUTS_MISMATCH"
    assert payload["intended_comparison"]["pass"] is True
    assert payload["native_comparison"]["pass"] is False
    assert payload["native_comparison"]["unequal"] == {
        "InpBlockedEntryDayHoursCsv": {"expected": "", "actual": "5:20"},
        "InpBlockedLongEntryHoursCsv": {"expected": "", "actual": "3,10,13,14"},
    }


def test_parser_proves_committed_rule_clean_report_is_contaminated() -> None:
    report = (
        ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_H4_EPISODE_IDENTITY_REPAIR_EXACT_20260711_FINAL2"
        / "runs"
        / "rule_clean_common_risk"
        / "ten_year"
        / "A1_XAU_H4_EPISODE_REPAIR_RULE_CLEAN_COMMON_RISK_TEN_YEAR.htm"
    )
    inputs = PARSER.parse_effective_inputs(report)
    assert inputs["InpBlockedEntryDayHoursCsv"] == "5:20"
    assert inputs["InpBlockedLongEntryHoursCsv"] == "3,10,13,14"


def test_duplicate_effective_input_fails_closed(tmp_path: Path) -> None:
    report = tmp_path / "duplicate.htm"
    report.write_text(
        report_text().replace(
            "<tr><td>Company:</td>",
            "<tr><td></td><td><b>InpBlockedEntryDayHoursCsv=</b></td></tr><tr><td>Company:</td>",
        ),
        encoding="utf-16",
    )
    try:
        PARSER.parse_effective_inputs(report)
    except PARSER.EffectiveInputError as exc:
        assert "Duplicate effective input" in str(exc)
    else:
        raise AssertionError("duplicate native input was accepted")


def test_shared_m5_runner_fails_on_generated_versus_native_input_mismatch() -> None:
    text = (SCRIPTS / "run_a1_xau_m5_momentum_backtest_variants.py").read_text(encoding="utf-8")
    assert "native_effective_inputs = effective_inputs.parse_effective_inputs(html_report)" in text
    assert "effective_inputs.require_equal_inputs(" in text
    assert '"effective_input_comparison": input_comparison' in text
