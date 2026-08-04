import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mt5/Experts/EurUsdUnifiedPortfolioControlledDemoV20.mq5"
ARMED = ROOT / "mt5/Presets/EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030_ARMED.set"
RESET = ROOT / "mt5/Presets/EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030_RESET.set"
DEPLOYMENT = ROOT / "config/frozen_eurusd_v20r6_shared_account_deployment.json"


def test_v20r5_identifies_the_account_migration_candidate() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert '#property version   "20.67"' in text
    assert "EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030" in text
    assert "strategy-scoped USD risk" in text


def test_v20r3_replaces_friday_shorts_with_a_causal_reversal() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    m15 = text[text.index("void AddM15Candidates(") : text.index("void AddM30Candidates(")]
    m30 = text[text.index("void AddM30Candidates(") : text.index("int CountForeignSymbolPositions()")]
    assert "candidate[BASELINE_CHOP] = true;" in m15
    assert "bar.close > refLow" in m15
    assert "bar.close > bar.open" in m15
    assert "fridayOffset >= 1" in m15
    assert "if(parts.day_of_week == 5)" in m30
    assert "IsLongSleeve(sleeve)" in text
    assert "friday_false_break_reversal_confirmed" in text


def test_v20r3_remains_disarmed_by_default() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "input bool InpShadowMode = true;" in text
    assert "input bool InpEnableDemoOrders = false;" in text
    assert "input bool InpEmergencyStop = true;" in text
    assert 'input string InpDemoArmToken = "DISARMED";' in text


def test_v20r5_minimum_equity_waiver_is_scoped_to_demo_account_1033030() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "input double InpMinimumAccountEquityUsd = 0.0;" in text
    assert "const double FROZEN_MINIMUM_ACCOUNT_EQUITY_USD = 0.0;" in text
    assert "const long FROZEN_MINIMUM_EQUITY_WAIVER_ACCOUNT = 1033030;" in text
    assert "InpAllowedAccountLogin" in text
    assert "!= FROZEN_MINIMUM_EQUITY_WAIVER_ACCOUNT" in text


def test_v20r5_has_no_artificial_balance_or_free_margin_requirement() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    armed = ARMED.read_text(encoding="utf-8")
    reset = RESET.read_text(encoding="utf-8")
    assert "input double InpMinimumAccountEquityUsd = 0.0;" in text
    assert "const double FROZEN_MINIMUM_ACCOUNT_EQUITY_USD = 0.0;" in text
    assert "const double FROZEN_MINIMUM_FREE_MARGIN_USD = 0.0;" in text
    assert "InpMinimumAccountEquityUsd=0.0" in armed
    assert "InpMinimumFreeMarginAfterOrderUsd=0.0" in armed
    assert "InpMinimumAccountEquityUsd=0.0" in reset
    assert "InpMinimumFreeMarginAfterOrderUsd=0.0" in reset


def test_v20r3_uses_equal_specialist_sizing() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    block = text[text.index("double ResearchLots(") : text.index("bool IsProtectedCoreSleeve(")]
    assert "return InpLotsPerTrade;" in block
    assert "return 0.03;" not in block
    assert "return 0.02;" not in block


def test_v20r3_monthly_giveback_guard_is_causal() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    block = text[text.index("bool MonthlyGivebackAllows(") : text.index("bool VolumeGridAllows(")]
    assert "HistorySelect(monthStart, TimeCurrent())" in block
    assert "peakUsd - cumulativeUsd >= InpResearchMonthlyGivebackUsd" in block
    assert "portfolio_monthly_giveback" in block
    assert "MonthlyGivebackAllows(reason)" in text


def test_v20r4_armed_preset_cannot_silently_leave_rsi_observer_only() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    armed = ARMED.read_text(encoding="utf-8")
    reset = RESET.read_text(encoding="utf-8")
    assert "InpEnableRsiOrders=true" in armed
    assert "InpEnableRsiOrders=false" in reset
    assert 'Audit("INIT_FAILED", "ordering_requires_rsi_orders")' in source
    assert 'InpEnableRsiOrders ? "_rsi_orders_armed" : "_rsi_observer"' in source
    assert '"mode=%s;rsi_orders=%s;' in source


def test_v20r4_rsi_orders_still_use_the_common_pretrade_guards() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    block = text[text.index("void RsiTryPlaceOrder(") : text.index("void RsiEvaluateCompletedBar(")]
    assert "NewOrderAllowed(RSI_SLEEVE_ID" in block
    assert "AcquirePortfolioOrderLock()" in block
    assert "ConfirmRsiPosition(" in block
    assert '"ORDER_CONFIRMED"' in block
    assert 'LatchPersistentBreaker("rsi_order_execution_not_confirmed")' in block


def test_v20r5_invalidates_the_old_account_state_contract() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "const int RSI_STATE_SCHEMA = 22;" in text
    assert "const long RSI_CONTRACT_FINGERPRINT = 2020260809;" in text


def test_v20r5_position_management_is_symbol_and_magic_isolated() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    portfolio = text[text.index("int CountPortfolioPositions()") : text.index("double OpenStageRisk(")]
    foreign = text[text.index("int CountForeignSymbolPositions()") : text.index("int CountSleevePositions(")]
    assert "PositionGetString(POSITION_SYMBOL) == InpTargetSymbol" in portfolio
    assert "IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))" in portfolio
    assert "PositionGetString(POSITION_SYMBOL) == InpTargetSymbol" in foreign
    assert "!IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))" in foreign


def test_v20r6_drawdown_uses_only_owned_eurusd_pnl() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    open_pnl = text[text.index("double OpenPortfolioPnlUsd()") : text.index("bool MonthlyGivebackAllows(")]
    refresh = text[text.index("void RefreshPersistentEquityState()") : text.index("bool TickIsFresh(")]

    assert "PositionGetString(POSITION_SYMBOL) != InpTargetSymbol" in open_pnl
    assert "!IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))" in open_pnl
    assert "ClosedPortfolioPnlSince(prospectiveStart) + OpenPortfolioPnlUsd()" in open_pnl
    assert "PortfolioStrategyEquityUsd()" in refresh
    assert "ACCOUNT_EQUITY" not in refresh
    assert "CODEX_EUV20R6_STRATEGY_PEAK" in text


def test_v20r6_converts_aed_account_values_before_usd_risk_checks() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    funding = text[text.index("bool FundingAndCashRiskAllow(") : text.index("bool IdentityAllowsManagement(")]

    assert "const double AED_PER_USD = 3.6725;" in text
    assert 'if(currency == "AED")' in text
    assert "return AccountValueUsd(pnl);" in text
    assert "AccountValueUsd(AccountInfoDouble(ACCOUNT_EQUITY))" in funding
    assert "AccountValueUsd(AccountInfoDouble(ACCOUNT_MARGIN_FREE) - margin)" in funding
    assert "AccountValueUsd(proposedAtStop)" in funding


def test_v20r6_deployment_artifacts_are_hash_bound() -> None:
    deployment = json.loads(DEPLOYMENT.read_text(encoding="utf-8"))

    assert deployment["drawdown_scope"] == "STRATEGY_ONLY"
    assert deployment["core_broker_stops_validation"] is True
    assert deployment["minimum_account_equity_usd"] == 0.0
    assert deployment["minimum_free_margin_after_order_usd"] == 0.0
    for relative, expected in deployment["artifacts"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected


def test_v20r4_makes_rsi_stops_broker_valid_before_order_submission() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    block = text[text.index("bool RsiEnsureBrokerStopDistances(") : text.index("void RsiEvaluateCompletedBar(")]
    assert "SYMBOL_TRADE_STOPS_LEVEL" in block
    assert "tick.bid - minimumDistance" in block
    assert "RSI_TARGET_R * riskDistance" in block
    assert '"RSI_STOPS_ADJUSTED"' in block
    assert "TRADE_RETCODE_INVALID_STOPS" in block
    assert '"ORDER_REJECTED"' in block


def test_v20r6_1_makes_core_stops_broker_valid_before_order_submission() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    validator = text[
        text.index("bool CoreEnsureBrokerStopDistances(") : text.index("void ProcessCandidates(")
    ]
    process = text[text.index("void ProcessCandidates(") : text.index("void EvaluateCompletedAt(")]

    assert "SYMBOL_TRADE_STOPS_LEVEL" in validator
    assert "tick.bid - minimumDistance" in validator
    assert "tick.ask + minimumDistance" in validator
    assert "entry + targetR * riskDistance" in validator
    assert "entry - targetR * riskDistance" in validator
    assert "CoreEnsureBrokerStopDistances(" in process
    assert process.index("CoreEnsureBrokerStopDistances(") < process.index("NewOrderAllowed(")
    assert process.index("CoreEnsureBrokerStopDistances(") < process.index("trade.Buy(")
    assert '"CORE_STOPS_ADJUSTED"' in process
