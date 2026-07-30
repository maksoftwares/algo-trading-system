from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (
    ROOT
    / "mt5"
    / "Experts"
    / "EurUsdH4FrequencyCompletionControlledDemo.mq5"
)
ORDERING = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_ORDERING_DEMO.template.set"
)
V2_CONFIG = (
    ROOT
    / "config"
    / "frozen_h4_frequency_completion_v2_no_deployment.json"
)
V2_RESULT = (
    ROOT
    / "outputs"
    / "h4_frequency_completion_v2_mt5"
    / "RESULT.json"
)


def test_v2_defaults_and_ordering_template_are_fail_closed() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for expected in (
        '#property version   "2.00"',
        "input bool InpShadowMode = true;",
        "input bool InpEnableDemoOrders = false;",
        "input bool InpEmergencyStop = true;",
        "input bool InpTesterOrdersEnabled = false;",
        "input bool InpEnableCompressionSleeves = false;",
        'input string InpDemoArmToken = "DISARMED";',
        "input double InpLotsPerTrade = 0.01;",
        "input int InpMaximumTradesPerUtcDay = 6;",
        "input int InpMaximumOwnPositions = 6;",
    ):
        assert expected in source
    text = ORDERING.read_text(encoding="utf-8")
    assert "InpShadowMode=false" in text
    assert "InpEnableDemoOrders=false" in text
    assert "InpEmergencyStop=true" in text
    assert "InpTesterOrdersEnabled=false" in text
    assert "InpEnableCompressionSleeves=false" in text
    assert "InpDemoArmToken=DISARMED" in text
    assert "InpLotsPerTrade=0.01" in text


def test_ea_preserves_sleeve_identity_but_disables_failed_compression() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    sleeves = {
        "BASELINE_CHOP",
        "BASELINE_COMPRESSION",
        "NEXT_CLOSE_CHOP",
        "NEXT_CLOSE_COMPRESSION",
        "RETEST_CHOP",
        "RETEST_COMPRESSION",
        "M15_FOLLOW_3_CHOP",
        "M15_FOLLOW_5_CHOP",
        "M15_FOLLOW_5_COMPRESSION",
        "M15_FOLLOW_7_COMPRESSION",
        "M30_FIRST_BREAK_CHOP",
        "M30_FIRST_BREAK_COMPRESSION",
    }
    assert all(name in source for name in sleeves)
    assert (
        "regime == REGIME_COMPRESSION && "
        "!InpEnableCompressionSleeves"
    ) in source
    assert "STAGE_ONE_MAXIMUM_RISK = 2.0" in source
    assert "STAGE_TWO_MAXIMUM_RISK = 2.5" in source
    assert "STAGE1_CAP_REJECTED" in source
    assert "STAGE2_CAP_REJECTED" in source


def test_ea_revalidates_volume_reconciles_positions_and_recovers_state() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for expected in (
        "SYMBOL_VOLUME_MIN",
        "SYMBOL_VOLUME_STEP",
        "frozen_0p01_lot_required",
        "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING",
        "foreign_eurusd_position_mutex",
        "ReconcilePositions",
        "RebuildDailyState",
        "RESTART_RECOVERY_OK",
        "persisted_schema_mismatch",
        "duplicate_instance_mutex",
        "minimum_account_equity",
        "minimum_free_margin_after_order",
        "maximum_aggregate_initial_risk",
        "stale_tick",
        "terminal_disconnected",
    ):
        assert expected in source


def test_v2_confirms_transactions_and_fails_closed_on_audit_faults() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for expected in (
        "bool Audit(",
        "auditHealthy = false;",
        'reason = "audit_unavailable";',
        "ConfirmSleevePosition",
        "trade.ResultRetcode() != TRADE_RETCODE_DONE",
        "trade.ResultDeal() == 0",
        "ORDER_CONFIRMED",
        "ORDER_EXECUTION_UNCERTAIN",
        "TIME_EXIT_CONFIRMED",
        "OnTradeTransaction(",
    ):
        assert expected in source


def test_v2_persists_peak_equity_breaker_and_mutex_ownership() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for expected in (
        "sessionPeakEquity",
        "peakEquityName",
        "breakerLatchName",
        "persistentBreakerLatched",
        "RISK_BREAKER_LATCHED",
        "ManagePersistentBreakerExits",
        "mutexOwnerToken",
        "mutexHeartbeatName",
        "MUTEX_OWNERSHIP_LOST",
    ):
        assert expected in source


def test_v2_frozen_contract_prohibits_deployment_and_compression() -> None:
    config = json.loads(V2_CONFIG.read_text(encoding="utf-8"))
    assert config["demo_deployment_authorized"] is False
    assert config["demo_orders_authorized"] is False
    assert config["decision_policy"][
        "compression_sleeves_must_be_disabled"
    ]
    assert config["transfer_gates"]["required_lot"] == 0.01
    assert config["transfer_gates"]["maximum_trades_per_active_day"] == 6


def test_v2_generated_predeployment_result_passes_without_authority() -> None:
    result = json.loads(V2_RESULT.read_text(encoding="utf-8"))
    assert (
        result["status"]
        == "V2_PREDEPLOYMENT_VALIDATION_PASSED_NO_DEPLOYMENT"
    )
    assert result["demo_deployment_performed"] is False
    assert result["demo_order_authorized"] is False
    assert all(result["gate_results"].values())
    assert result["windows"]["FULL_TRANSFER"]["profit_factor"] > 1.35
    assert (
        result["robustness"]["one_pip_plus_commission"][
            "profit_factor"
        ]
        > 1.20
    )
