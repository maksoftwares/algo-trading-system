from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load():
    path = SCRIPTS / "run_a1_xau_h4_episode_repair_exact.py"
    spec = importlib.util.spec_from_file_location("run_a1_xau_h4_episode_repair_exact", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = load()


def frozen_config() -> str:
    path = (
        ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_ROUTER_ENTRY_HOLD_PATH_INPUTS_20260710"
        / "immutable_evidence"
        / R.H4_SPEC.source_id
        / "tester.ini"
    )
    return path.read_text(encoding="utf-8-sig")


def test_structural_parity_changes_only_locked_exposure_inputs() -> None:
    text, _ = R.derive_config(frozen_config(), R.VARIANTS[0], R.extended.HORIZONS[0])
    parsed = R.exact.parse_ini(text)
    assert set(parsed) == {"Tester", "TesterInputs"}
    assert parsed["Tester"]["Deposit"] == "1000"
    assert parsed["TesterInputs"]["InpFixedLots"] == "0.01"
    assert parsed["TesterInputs"]["InpUseRiskNormalizedLots"] == "false"
    assert parsed["TesterInputs"]["InpOnePositionPerMagic"] == "true"
    assert parsed["TesterInputs"]["InpH4D1PrevMonthHealthGateEnabled"] == "true"
    assert parsed["TesterInputs"]["InpLegacySelectionMasksEnabled"] == "true"


def test_rule_clean_common_risk_is_fixed() -> None:
    text, _ = R.derive_config(frozen_config(), R.VARIANTS[1], R.extended.HORIZONS[1])
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Deposit"] == "10000"
    assert parsed["Tester"]["Currency"] == "USD"
    assert parsed["TesterInputs"]["InpRiskAmountUsd"] == "25.00"
    assert parsed["TesterInputs"]["InpH4D1PrevMonthHealthGateEnabled"] == "false"
    assert parsed["TesterInputs"]["InpLegacySelectionMasksEnabled"] == "false"
    assert parsed["TesterInputs"]["InpBlockedLongEntryHoursCsv"] == "__DISABLED__"
    assert parsed["TesterInputs"]["InpBlockedEntryDayHoursCsv"] == "__DISABLED__"


def test_rule_clean_derived_inputs_exactly_match_preregistered_lock() -> None:
    contract = json.loads(R.EFFECTIVE_INPUT_LOCK.read_text(encoding="utf-8"))
    for horizon in R.extended.HORIZONS:
        text, _ = R.derive_config(frozen_config(), R.VARIANTS[1], horizon)
        parsed = R.exact.parse_ini(text)
        assert parsed["TesterInputs"] == contract["horizons"][horizon.name]["tester_inputs"]


def test_small_account_variant_uses_owner_aed_basis() -> None:
    variant = R.VARIANTS[2]
    assert (variant.deposit, variant.currency, variant.risk_amount) == ("3672.50", "AED", "9.18")


def test_cli_has_no_live_or_attachment_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.isdisjoint({"live", "demo", "account", "server", "attach", "profile"})


def test_locate_run_files_dir_accepts_dynamic_local_agent_port(tmp_path: Path) -> None:
    expected = tmp_path / "Tester" / "Agent-127.0.0.1-3001" / "MQL5" / "Files"
    expected.mkdir(parents=True)
    (expected / "startup.csv").write_text("ok\n", encoding="utf-8")
    assert R.locate_run_files_dir(tmp_path, "startup.csv") == expected


def test_locate_run_files_dir_rejects_ambiguous_agent_output(tmp_path: Path) -> None:
    for port in ("3000", "3001"):
        files = tmp_path / "Tester" / f"Agent-127.0.0.1-{port}" / "MQL5" / "Files"
        files.mkdir(parents=True)
        (files / "startup.csv").write_text("ok\n", encoding="utf-8")
    try:
        R.locate_run_files_dir(tmp_path, "startup.csv")
    except RuntimeError as exc:
        assert "exactly one local tester agent" in str(exc)
    else:
        raise AssertionError("ambiguous tester-agent output was accepted")


def test_committed_rule_clean_native_report_fails_effective_input_lock(tmp_path: Path) -> None:
    run_dir = (
        ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_H4_EPISODE_IDENTITY_REPAIR_EXACT_20260711_FINAL2"
        / "runs"
        / "rule_clean_common_risk"
        / "ten_year"
    )
    report = run_dir / "A1_XAU_H4_EPISODE_REPAIR_RULE_CLEAN_COMMON_RISK_TEN_YEAR.htm"
    config = run_dir / "tester.ini"
    try:
        R.verify_effective_contract(
            variant=R.VARIANTS[1],
            horizon=R.extended.HORIZONS[1],
            config=config,
            report=report,
            run_dir=tmp_path,
        )
    except R.effective_inputs.EffectiveInputError as exc:
        assert "effective-input verification failed" in str(exc)
    else:
        raise AssertionError("mask-contaminated native report passed the effective-input lock")
    payload = (tmp_path / "effective_inputs.json").read_text(encoding="utf-8")
    assert '"status": "EFFECTIVE_INPUTS_MISMATCH"' in payload
    assert '"actual": "5:20"' in payload
