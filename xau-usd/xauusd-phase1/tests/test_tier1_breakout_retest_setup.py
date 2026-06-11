from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import load_script, write_csv


def _write_tier1_source(root: Path) -> None:
    source = root / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                'input string InpRunId = "phase2-experimental-demo-executor-v0.2";',
                "input bool InpDryRunOnly = false;",
                "input bool InpBrokerActionAllowed = false;",
                'input string InpCandidate = "breakout_retest";',
                'input string InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY";',
                'input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";',
                'input string InpTargetSymbol = "XAUUSD";',
                'input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,GBPUSD";',
                'input string InpExpectedServerMarker = "Demo";',
                'input string InpAllowedAccountLoginsCsv = "";',
                'input string InpExperimentalAuthorizationToken = "";',
                'input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";',
                'input string InpCostSuspensionAcknowledgementToken = "";',
                'input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";',
                'input string InpAuthorizedCandidatesCsv = "breakout_retest";',
                'input string InpAttachmentLogFileName = "experimental_demo_executor_signal_log_v02.csv";',
                'input string InpStartupLogFileName = "experimental_demo_executor_startup_v02.csv";',
                'input string InpOrderLogFileName = "experimental_demo_executor_order_log_v02.csv";',
                'input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";',
                "input double InpFixedLot = 0.01;",
                "input double InpEURUSDFixedLot = 0.05;",
                "input double InpGBPUSDFixedLot = 0.05;",
                "input int InpMaxOrdersPerDay = 0;",
                "input int InpMaxAccountOrdersPerDay = 0;",
                "input int InpMinSecondsBetweenOrders = 0;",
                "input int InpMaxOpenPositionsPerInstance = 0;",
                "input int InpDeviationPoints = 50;",
                "input double InpMaxEstimatedCostR = 0.00;",
                "input double InpMaxMeasuredSpreadPoints = 0.0;",
                "input bool InpTradeSessionGateEnabled = false;",
                "input int InpTradeSessionStartHour = 0;",
                "input int InpTradeSessionEndHour = 23;",
                "long InstanceMagic(){ return 920101; }",
            ]
        ),
        encoding="utf-8",
    )
    includes = root / "mt5" / "Include" / "Phase1"
    includes.mkdir(parents=True)
    (includes / "Phase1Types.mqh").write_text("// types\n", encoding="utf-8")
    (includes / "Phase1BreakoutRetest.mqh").write_text("// breakout\n", encoding="utf-8")


def _write_template(root: Path) -> Path:
    template = root / "mt5" / "Presets" / "Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set"
    template.parent.mkdir(parents=True)
    template.write_text(
        "\n".join(
            [
                "InpRunId=TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10",
                "InpDryRunOnly=true",
                "InpBrokerActionAllowed=false",
                "InpCandidate=breakout_retest",
                "InpCandidateStatus=EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
                "InpFamilyLifecycleStatus=COST_SUSPENDED_CANONICAL",
                "InpTargetSymbol=XAUUSD",
                "InpQualifiedSymbolsCsv=XAUUSD",
                "InpExpectedServerMarker=Demo",
                "InpAllowedAccountLoginsCsv=<OWNER_TO_FILL>",
                "InpExperimentalAuthorizationToken=<OWNER_TO_FILL>",
                "InpRequiredExperimentalAuthorizationToken=EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY",
                "InpCostSuspensionAcknowledgementToken=<OWNER_TO_FILL>",
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
        ),
        encoding="utf-8",
    )
    return template


def test_tier1_owner_preset_uses_current_executor_inputs_and_derived_magic(tmp_path):
    root = tmp_path / "phase1"
    _write_tier1_source(root)
    _write_template(root)
    module = load_script("make_tier1_breakout_retest_owner_preset")

    payload = module.make_tier1_owner_preset(root, authorized_account_login="1033030", authorized_server_marker="Capital.ComMena-Demo")
    preset = (root / "local" / "Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set").read_text(encoding="utf-8")

    assert payload["status"] == "PASS"
    assert payload["derived_magic"] == 920101
    assert "InpAllowedAccountLoginsCsv=1033030" in preset
    assert "InpExpectedServerMarker=Demo" in preset
    assert "InpBrokerActionAllowed=true" in preset
    assert "InpDryRunOnly=false" in preset
    assert "InpMaxEstimatedCostR=0.30" in preset
    assert "InpMaxMeasuredSpreadPoints=75.0" in preset
    assert "InpMinSecondsBetweenOrders=60" in preset
    assert "InpMaxOpenPositionsPerInstance=1" in preset
    assert "InpTradeSessionGateEnabled=true" in preset
    assert "InpTradeSessionStartHour=12" in preset
    assert "InpTradeSessionEndHour=15" in preset
    assert "InpMagicNumber" not in preset


def test_tier1_setup_prepares_and_deploys_without_chart_attachment(tmp_path):
    root = tmp_path / "phase1"
    install = tmp_path / "install"
    source_config = tmp_path / "source_config"
    portable = tmp_path / "portable"
    _write_tier1_source(root)
    _write_template(root)
    for name in ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico"):
        (install / name).parent.mkdir(parents=True, exist_ok=True)
        (install / name).write_text(name, encoding="utf-8")
    for name in ("accounts.dat", "servers.dat"):
        source_config.mkdir(parents=True, exist_ok=True)
        (source_config / name).write_text(name, encoding="utf-8")
    preset_module = load_script("make_tier1_breakout_retest_owner_preset")
    preset_module.make_tier1_owner_preset(root, authorized_account_login="1033030", authorized_server_marker="Capital.ComMena-Demo")
    setup_module = load_script("setup_tier1_breakout_retest_portable_demo_terminal")

    payload = setup_module.setup_tier1_portable_terminal(
        root,
        install_root=install,
        source_config_root=source_config,
        portable_root=portable,
        authorized_account_login="1033030",
        prepare=True,
        deploy=True,
    )

    assert payload["status"] == "PENDING"
    assert payload["charts_attached_by_codex"] is False
    assert (portable / "MQL5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5").exists()
    assert (portable / "MQL5" / "Presets" / "Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set").exists()
    assert "Expert=" not in (portable / "Config" / "tier1_bestea_startup.ini").read_text(encoding="utf-8")


def test_tier1_preflight_flags_active_source_spread_logger(tmp_path):
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    _write_tier1_source(root)
    _write_template(root)
    (repo / ".gitignore").write_text("xau-usd/xauusd-phase1/local/\n*owner_authorized*.local.*\n", encoding="utf-8")
    preset_module = load_script("make_tier1_breakout_retest_owner_preset")
    preset_module.make_tier1_owner_preset(root, authorized_account_login="1033030", authorized_server_marker="Capital.ComMena-Demo")
    portable = tmp_path / "portable"
    (portable / "MQL5" / "Experts").mkdir(parents=True)
    (portable / "MQL5" / "Experts" / "Phase2ExperimentalDemoExecutor.ex5").write_text("compiled", encoding="utf-8")
    (portable / "MQL5" / "Logs").mkdir(parents=True)
    (portable / "MQL5" / "Logs" / "compile_Phase2ExperimentalDemoExecutor.log").write_text("Result: 0 errors, 0 warnings", encoding="utf-8")
    source_terminal = tmp_path / "spread_logger"
    files = source_terminal / "MQL5" / "Files"
    files.mkdir(parents=True)
    (files / "spread_log_1033030_Capital.ComMena-Demo_XAUUSD_20260610.csv").write_text("active", encoding="utf-8")
    module = load_script("tier1_breakout_retest_preflight")

    payload = module.generate_tier1_preflight(root, portable_root=portable, source_terminal_root=source_terminal)

    assert payload["status"] == "FAIL"
    assert any(check["name"] == "source_terminal_not_using_tier1_account" and check["status"] == "FAIL" for check in payload["checks"])


def test_tier1_daily_report_server_buckets_and_dst_labels(tmp_path):
    root = tmp_path / "phase1"
    order_log = tmp_path / "tier1_bestea_order_log_xauusd.csv"
    write_csv(
        order_log,
        [
            {
                "timestamp_broker": "2026.06.10 12:05:00",
                "action": "ORDER_SEND_OK",
                "direction": "LONG",
                "estimated_cost_R": "0.08",
                "stop_distance_points": "900",
            },
            {
                "timestamp_broker": "2026.06.10 23:05:00",
                "action": "GUARD_BLOCK",
                "direction": "SHORT",
                "estimated_cost_R": "0.12",
                "guard_reason": "measured_spread_points_exceeds_threshold",
            },
        ],
    )
    module = load_script("tier1_breakout_retest_daily_report")

    payload = module.generate_tier1_daily_report(root, "2026_06_10", order_log=order_log)

    assert payload["status"] == "PENDING"
    assert payload["session_buckets"]["NY_MORNING"]["orders_sent"] == 1
    assert payload["session_buckets"]["NY_MORNING"]["dubai_equivalent"] == "16:00-19:59 Dubai"
    assert payload["session_buckets"]["ASIA"]["guard_blocks"] == 1
    assert "2026-11-01" in payload["standing_annotations"]["november_dst_prediction"]


def test_tier1_first_order_verification_checks_magic_lot_and_cost(tmp_path):
    root = tmp_path / "phase1"
    _write_tier1_source(root)
    _write_template(root)
    preset_module = load_script("make_tier1_breakout_retest_owner_preset")
    preset_module.make_tier1_owner_preset(root, authorized_account_login="1033030", authorized_server_marker="Capital.ComMena-Demo")
    order_log = tmp_path / "tier1_bestea_order_log_xauusd.csv"
    write_csv(
        order_log,
        [
            {
                "action": "ORDER_SEND_OK",
                "account_login": "1033030",
                "symbol": "XAUUSD",
                "candidate": "breakout_retest",
                "magic": "920101",
                "broker_action_allowed": "true",
                "dry_run": "false",
                "volume": "0.01",
                "sl": "4180.00",
                "tp": "4200.00",
                "estimated_cost_R": "0.08",
                "stop_distance_points": "900",
            }
        ],
    )
    module = load_script("tier1_first_order_verification")

    payload = module.generate_tier1_first_order_verification(root, order_log=order_log)

    assert payload["status"] == "PENDING"
    assert any(check["name"] == "magic_920101" and check["status"] == "PASS" for check in payload["checks"])
    assert any(check["name"] == "lot_0_01" and check["status"] == "PASS" for check in payload["checks"])
    assert any(check["name"] == "comment_history_verification" and check["status"] == "PENDING_MANUAL_CONFIRMATION" for check in payload["checks"])
