from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c58_generates_three_review_templates_without_authorizing_broker_action(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_fill_collection_mode import generate_demo_fill_collection_mode

    root = _root_with_c58_inputs(tmp_path)

    output = generate_demo_fill_collection_mode(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "DEMO_FILL_COLLECTION_REVIEW_PACKET_READY"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["authorization"]["review_only_templates_contain_armed_demo_inputs"] is True
    assert payload["boundary"]["preset_deployed_to_mt5"] is False
    assert payload["boundary"]["committed_preset_modified"] is False
    assert len(payload["templates"]) == 3
    assert pointer["c58_demo_fill_collection_mode_status"] == "DEMO_FILL_COLLECTION_REVIEW_PACKET_READY"
    assert pointer["broker_action_authorized"] is False

    by_label = {item["account_label"]: item for item in payload["templates"]}
    assert set(by_label) == {"A1", "A2", "A3"}
    assert by_label["A1"]["values"]["InpAllowedAccountLoginsCsv"] == "1025742"
    assert by_label["A2"]["values"]["InpAllowedAccountLoginsCsv"] == "1033030"
    assert by_label["A3"]["values"]["InpAllowedAccountLoginsCsv"] == "1033669"
    for item in payload["templates"]:
        path = Path(item["path"])
        text = path.read_text(encoding="utf-8")
        assert path.is_relative_to(root / "outputs" / "reports" / "demo_fill_collection")
        assert "mt5" not in [part.lower() for part in path.parts]
        assert "InpDryRunOnly=false" in text
        assert "InpBrokerActionAllowed=true" in text
        assert "InpFixedLot=0.01" in text
        assert "InpMaxOrdersPerDay=3" in text
        assert "InpMaxAccountOrdersPerDay=3" in text
        assert "InpMaxOpenPositionsPerInstance=1" in text
        assert "InpMaxOpenPositionsPerMagic=1" in text
        assert "InpTradeSessionGateEnabled=false" in text


def test_c58_blocks_when_committed_base_template_is_unsafe(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_fill_collection_mode import generate_demo_fill_collection_mode

    root = _root_with_c58_inputs(tmp_path, unsafe_base_template=True)

    output = generate_demo_fill_collection_mode(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {item["check"]: item for item in payload["validations"]}

    assert payload["status"] == "DEMO_FILL_COLLECTION_PACKET_BLOCKED"
    assert checks["base_template_committed_safe"]["passed"] is False
    assert payload["templates"] == []
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c58_blocks_when_executor_source_is_truncated(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_fill_collection_mode import generate_demo_fill_collection_mode

    root = _root_with_c58_inputs(tmp_path, truncated_source=True)

    output = generate_demo_fill_collection_mode(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {item["check"]: item for item in payload["validations"]}

    assert payload["status"] == "DEMO_FILL_COLLECTION_PACKET_BLOCKED"
    assert checks["source_brace_balance"]["passed"] is False
    assert checks["source_ends_cleanly"]["passed"] is False
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c58_script_loads() -> None:
    module = load_script("c58_generate_demo_fill_collection_mode")

    assert hasattr(module, "main")


def test_c59_updates_existing_mt5_chart_without_duplicate_carriage_returns(tmp_path: Path) -> None:
    module = load_script("c59_attach_demo_fill_collection")
    profile_dir = tmp_path / "Default"
    profile_dir.mkdir(parents=True)
    chart = profile_dir / "chart01.chr"
    chart.write_bytes(
        b"<chart>\r\n"
        b"symbol=XAUUSD\r\n"
        b"<expert>\r\n"
        b"name=Phase2ExperimentalDemoExecutor\r\n"
        b"path=Experts\\Phase2ExperimentalDemoExecutor.ex5\r\n"
        b"<inputs>\r\n"
        b"InpRunId=OLD\r\n"
        b"</inputs>\r\n"
        b"</expert>\r\n"
        b"</chart>\r\n"
    )

    updated, action = module._write_or_update_chart(chart.parent, {"InpRunId": "A3_DEMO_FILL_COLLECTION_A3_V1"})

    assert updated == chart
    assert action == "updated_existing_phase2_chart"
    raw = chart.read_bytes()
    assert b"\r\r\n" not in raw
    assert b"symbol=XAUUSD\r\n" in raw
    assert b"InpRunId=A3_DEMO_FILL_COLLECTION_A3_V1\r\n" in raw


def test_c59_can_select_one_account_without_losing_three_account_registry() -> None:
    module = load_script("c59_attach_demo_fill_collection")
    accounts = [_account("A1", "1", "C:/A1/terminal64.exe", "C:/A1", False, "a1"), _account("A2", "2", "C:/A2/terminal64.exe", "C:/A2", True, "a2"), _account("A3", "3", "C:/A3/terminal64.exe", "C:/A3", True, "a3")]

    selected = module._select_accounts(accounts, {"A3"})

    assert [item["account_label"] for item in selected] == ["A3"]
    assert [item["account_label"] for item in accounts] == ["A1", "A2", "A3"]


def _root_with_c58_inputs(tmp_path: Path, *, unsafe_base_template: bool = False, truncated_source: bool = False) -> Path:
    root = tmp_path / "phase1"
    _write_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    _write_base_template(root / "mt5" / "Presets" / "Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set", unsafe=unsafe_base_template)
    _write_source(root / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5", truncated=truncated_source)
    _write_base_include(root / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh")
    _write_json(
        root / "outputs" / "reports" / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C58",
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    return root


def _write_registry(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "mt5_multi_account_registry_v1",
            "common": {
                "symbol": "XAUUSD",
                "expected_server_regex": "^Capital\\.ComMena-Demo$",
                "require_demo_trade_mode": True,
                "require_existing_terminal_process": True,
                "allow_mt5_login_call": False,
                "allow_symbol_select_call": False,
                "export_timezone": "UTC",
                "snapshot_safety_lag_minutes": 5,
            },
            "accounts": {
                "A1": _account("A1", "1025742", "C:/MT5A1/terminal64.exe", "C:/MT5A1", False, "standard_experimental_demo"),
                "A2": _account("A2", "1033030", "C:/MT5A2/terminal64.exe", "C:/MT5A2", True, "tier1_breakout_only"),
                "A3": _account("A3", "1033669", "C:/MT5A3/terminal64.exe", "C:/MT5A3", True, "paused_repair_lane"),
            },
        },
    )


def _account(label: str, login: str, terminal: str, data_path: str, portable: bool, role: str) -> dict[str, object]:
    return {
        "account_scope": login,
        "account_label": label,
        "expected_login": login,
        "terminal_exe": terminal,
        "expected_data_path": data_path,
        "portable": portable,
        "role": role,
        "symbol": "XAUUSD",
        "files_roots": [f"{data_path}/MQL5/Files"],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_base_template(path: Path, *, unsafe: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "InpRunId=TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10",
                "InpDryRunOnly=true",
                "InpBrokerActionAllowed=true" if unsafe else "InpBrokerActionAllowed=false",
                "InpCandidate=breakout_retest",
                "InpCandidateStatus=EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
                "InpFamilyLifecycleStatus=COST_SUSPENDED_CANONICAL",
                "InpTargetSymbol=XAUUSD",
                "InpQualifiedSymbolsCsv=XAUUSD",
                "InpExpectedServerMarker=Demo",
                "InpAllowedAccountLoginsCsv=<OWNER_TO_FILL>",
                "InpExperimentalAuthorizationToken=",
                "InpRequiredExperimentalAuthorizationToken=EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY",
                "InpCostSuspensionAcknowledgementToken=",
                "InpRequiredCostSuspensionAcknowledgementToken=I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT",
                "InpAuthorizedCandidatesCsv=breakout_retest",
                "InpAttachmentLogFileName=tier1_bestea_signal_log_xauusd.csv",
                "InpStartupLogFileName=tier1_bestea_startup_xauusd.csv",
                "InpOrderLogFileName=tier1_bestea_order_log_xauusd.csv",
                "InpKillSwitchFileName=tier1_bestea_kill_switch.txt",
                "InpFixedLot=0.01",
                "InpEURUSDFixedLot=0.01",
                "InpGBPUSDFixedLot=0.01",
                "InpMaxOrdersPerDay=0",
                "InpMaxAccountOrdersPerDay=0",
                "InpMinSecondsBetweenOrders=60",
                "InpMaxOpenPositionsPerInstance=1",
                "InpDeviationPoints=50",
                "InpMaxEstimatedCostR=0.30",
                "InpMaxMeasuredSpreadPoints=75.0",
                "InpTradeSessionGateEnabled=true",
                "InpTradeSessionStartHour=12",
                "InpTradeSessionEndHour=15",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_source(path: Path, *, truncated: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        'input bool InpBrokerActionAllowed = false;',
        'input string InpExperimentalAuthorizationToken = "";',
        'input string InpCostSuspensionAcknowledgementToken = "";',
        "input int InpMaxOrdersPerDay = 0;",
        "input int InpMaxAccountOrdersPerDay = 0;",
        "input int InpMaxOpenPositionsPerInstance = 0;",
        "input int InpMaxOpenPositionsPerMagic = 1;",
        "input double InpMaxEstimatedCostR = 0.00;",
        "input double InpMaxMeasuredSpreadPoints = 0.0;",
        "bool KillSwitchActive() { return true; // Presence is enough; operators should not need to type KILL during an emergency. }",
        "bool AccountTradeModeDemo() { return AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO; }",
        "bool SendDemoMarketOrder() {",
        "  MqlTradeResult result;",
        "  bool sent = OrderSend(request, result);",
        "  return sent;",
        "}",
        'bool Guard() { return !ContainsText(server, "live") && !ContainsText(server, "real") && AccountTradeModeDemo(); }',
    ]
    if truncated:
        lines.extend(["void OnTimer() {", "  bool broken = true;"])
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_base_include(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#ifndef A3_BREAKOUT_EXECUTOR_BASE_MQH",
                "#define A3_BREAKOUT_EXECUTOR_BASE_MQH",
                "void A3BreakoutBaseIntegrity() {",
                "}",
                "#endif",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
