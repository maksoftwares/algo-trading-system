import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
ATTACH = ROOT / "scripts" / "attach_a1_xau_m5_momentum_continuation.py"
RUNNER = ROOT / "scripts" / "run_a1_xau_m5_momentum_backtest_variants.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _runner_variant_block(text: str, name: str) -> str:
    start = text.index(f'name="{name}"')
    next_variant = text.find("    Variant(", start + 1)
    return text[start:] if next_variant == -1 else text[start:next_variant]


def _attach_module():
    spec = importlib.util.spec_from_file_location("attach_a1_momentum", ATTACH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_momentum_executor_defaults_are_observer_safe_and_a1_scoped() -> None:
    text = _text(EA)
    assert "input bool   InpAllowDemoTrading              = false;" in text
    assert "input bool   InpAllowNonDemoAccounts          = false;" in text
    assert 'input string InpTargetSymbol                  = "XAUUSD";' in text
    assert "input long   InpMagicNumber                   = 932200;" in text
    assert "input double InpFixedLots                     = 0.01;" in text
    assert "input bool   InpUseRiskNormalizedLots         = false;" in text
    assert "input double InpRiskAmountUsd                 = 0.00;" in text
    assert "input double InpMaxRiskLots                   = 0.05;" in text
    assert "InpAllowedAccountLogin" in text
    assert "ACCOUNT_TRADE_MODE_DEMO" in text
    assert "experimental_demo_kill_switch.txt" in text
    assert "input MomentumDirectionMode InpDirectionMode  = MOMENTUM_BOTH_DIRECTIONS;" in text
    assert "input bool   InpUseH1TrendFilter              = false;" in text
    assert "input bool   InpUseH4TrendFilter              = false;" in text
    assert "input bool   InpUseDirectionalSessionFilter   = false;" in text
    assert "input bool   InpFeatureLossFilterEnabled      = false;" in text
    assert "input bool   InpFeatureLossFilterShadowOnly   = true;" in text
    assert "input double InpShortCloseToRecentExtremeBlockMin = -0.75;" in text
    assert "input bool   InpShortCloseToRecentExtremeBlockMaxEnabled = false;" in text
    assert "input double InpShortCloseToRecentExtremeBlockMax = -2.51;" in text
    assert 'input string InpBlockedEntryHoursCsv          = "";' in text
    assert "input bool   InpLegacySelectionMasksEnabled   = true;" in text
    assert "input double InpMinAtrAbsoluteForEntry        = 0.00;" in text
    assert "input double InpMaxThreeBarMoveAtr            = 0.00;" in text
    assert "input bool   InpPortfolioDailyGuardEnabled    = false;" in text
    assert 'input string InpPortfolioGuardMagicCsv        = "";' in text
    assert "input int    InpPortfolioMaxTradesPerDay      = 0;" in text
    assert "input double InpPortfolioDailyProfitTargetUsd = 0.00;" in text
    assert "input double InpPortfolioDailyLossStopUsd     = 0.00;" in text
    assert "input int    InpPortfolioCooldownAfterLossMinutes = 0;" in text
    assert "input int    InpMaxOpenPositionsPerMagic      = 1;" in text


def test_momentum_executor_is_separate_from_920101_breakout_lane() -> None:
    text = _text(EA)
    assert "input long   InpMagicNumber                   = 920101;" not in text
    assert "InpCandidate" not in text
    assert "do not retest a broken level" in text
    assert "M5_BREAK_AND_RUN_LONG" in text
    assert "M5_BREAK_AND_RUN_SHORT" in text


def test_momentum_executor_variant_switches_are_auditable() -> None:
    text = _text(EA)
    assert "MOMENTUM_SHORT_ONLY" in text
    assert "direction_mode_block" in text
    assert "h1_trend_filter_block" in text
    assert "h4_trend_filter_block" in text
    assert "directional_session_filter_block" in text
    assert "blocked_entry_hour" in text
    assert "atr_below_entry_floor" in text
    assert "three_bar_move_atr_exceeds_cap" in text
    assert "max_open_positions_reached" in text
    assert "LotsForStopDistance(stop_distance)" in text
    assert "NormalizeLotsForSymbol" in text
    assert "requested_lots + 0.0000001 < min_lots" in text
    assert 'InpUseRiskNormalizedLots ? "minimum_lot_risk_excess" : "invalid_order_lots"' in text
    assert '"swap", "fee", "order_ticket"' in text
    assert "HistoryDealGetDouble(deal_ticket, DEAL_FEE)" in text
    assert text.count("if(!InpLegacySelectionMasksEnabled)") == 3
    assert "ACCOUNT_CURRENCY" in text
    assert "ACCOUNT_LEVERAGE" in text
    assert "ACCOUNT_MARGIN_MODE" in text
    assert "SYMBOL_TRADE_CONTRACT_SIZE" in text
    assert "SYMBOL_TRADE_TICK_VALUE_LOSS" in text
    assert "H1TrendAllows" in text
    assert "H4TrendAllows" in text
    assert "TrendAllows" in text
    assert "DirectionalSessionAllows" in text
    assert "FeatureLossFilterBlocks" in text
    assert "CloseToRecentExtreme" in text
    assert "feature_loss_filter_short_close_to_recent_extreme_min" in text
    assert "feature_loss_filter_short_close_to_recent_extreme_max" in text
    assert "HourInWindow" in text
    assert "PERIOD_H1" in text
    assert "PERIOD_H4" in text


def test_attach_script_targets_only_a1_and_new_magic() -> None:
    text = _text(ATTACH)
    assert 'ACCOUNT_LOGIN = "1025742"' in text
    assert 'SERVER = "Capital.ComMena-Demo"' in text
    assert 'SYMBOL = "XAUUSD"' in text
    assert '"magic": 932200' in text
    assert '"magic": 932210' in text
    assert '"magic": 932211' in text
    assert '"magic": 932220' in text
    assert '"magic": 932221' in text
    assert '"magic": 932222' in text
    assert '"magic": 932230' in text
    assert '"magic": 932231' in text
    assert '"magic": 932232' in text
    assert '"magic": 932240' in text
    assert '"magic": 932241' in text
    assert '"magic": 932242' in text
    assert '"magic": 932250' in text
    assert '"magic": 932251' in text
    assert '"magic": 932260' in text
    assert '"magic": 932261' in text
    assert '"magic": 932270' in text
    assert '"magic": 932271' in text
    assert '"magic": 932280' in text
    assert '"magic": 932281' in text
    assert '"magic": 932292' in text
    assert '"magic": 932293' in text
    assert '"magic": 932294' in text
    assert '"magic": 932295' in text
    assert '"magic": 932296' in text
    assert '"magic": 932297' in text
    assert '"magic": 932298' in text
    assert '"magic": 932299' in text
    assert '"magic": 932300' in text
    assert '"magic": 932301' in text
    assert 'A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_LONG_V5_MOVE12_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_SHORT_CORE_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V6_MAX2_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V13_BOTH_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SHORT_CORE_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V6_MAX2_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V13_LONG_NO_MORNING_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SHORT_NIGHT_EARLY_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V6_MAX2_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V13_LONG_NO_MORNING_NO18_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_SHORT_NIGHT_EARLY_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DAILY_FIT_LONG_WEAK_HOURS_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DAILY_FIT_V13_BOTH_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_LONG_WEAK_HOURS_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_V13_BOTH_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DAILY_GUARD_LONG_WEAK_HOURS_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_DAILY_GUARD_V13_BOTH_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_GUARD_LONG_WEAK_HOURS_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_GUARD_V13_BOTH_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_LONG_WEAK_HOURS_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_V13_BOTH_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_V13_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_V13_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_V13_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_V13_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_LONG_20260702' in text
    assert 'A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_V13_20260702' in text
    assert '"spec_sha256": "70f64b6c6a2608659597563aa039279793ed690f4762d8248254463b388c4026"' in text
    assert '"spec_sha256": "2b5fe5ba37f5649353534a06f682c328f4c410ebd2ef95a45986e3172b19db3b"' in text
    assert '"spec_sha256": "e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a"' in text
    assert '"spec_sha256": "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d"' in text
    assert '"spec_sha256": "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615"' in text
    assert '"spec_sha256": "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269"' in text
    assert '"spec_sha256": "511af42042a5d6cfa3bac71a98c572a5a2292f47554a1f7fdfe1cd11094eac3f"' in text
    assert '"spec_sha256": "fe911d1c8fb91ed0712eb272b9e517f0b6ca61582a555a9281507d1f2afe9386"' in text
    assert '"spec_sha256": "b5d25b1f2cb109e4aa758b9a4203ec7961d9875000f3589803080a0dd5d26c3c"' in text
    assert '"spec_sha256": "c36778bef2ced45d19fa25b99480722bfc6741cdcadab0755b22aab9737cefb4"' in text
    assert '"spec_sha256": "2841f87404e085954da5614b43331f5d85884f3170986ccc5cad01bc35271279"' in text
    assert '"spec_sha256": "188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b"' in text
    assert '"spec_sha256": "693d070050666ccd066a834f71b666b3f865829e6a05c8942190be7da9c1729b"' in text
    assert '"spec_sha256": "1b84b0f7195a79a7cd031118ef54c203a55442027288064bc817da07c2510edd"' in text
    assert '"spec_sha256": "1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71"' in text
    assert '"spec_sha256": "de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a"' in text
    assert '"a2_touched": False' in text
    assert '"a3_touched": False' in text
    assert '"existing_920101_chart_edited": False' in text
    assert "A1XauM5MomentumContinuationExecutor" in text


def test_attach_script_renders_legacy_rr2_inputs() -> None:
    module = _attach_module()
    chart = module.render_chart(29, module.VARIANT_CONFIGS["rr2_long_only"])
    assert "InpRunId=A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702" in chart
    assert "InpRiskReward=2.00" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_rr2_kill_switch.txt" in chart
    assert "InpBlockedEntryHoursCsv=9,10" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpMinAtrAbsoluteForEntry=1.5" in chart
    assert "InpUseDirectionalSessionFilter=false" in chart
    assert "InpLongSessionStartHour=0" in chart
    assert "InpLongSessionEndHour=24" in chart
    assert "InpShortSessionStartHour=0" in chart
    assert "InpShortSessionEndHour=24" in chart
    assert "InpFeatureLossFilterEnabled=false" in chart
    assert "InpFeatureLossFilterShadowOnly=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.75" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=false" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpUseH1TrendFilter=true" in chart
    assert "InpH1TrendApplyToLong=true" in chart
    assert "InpH1TrendApplyToShort=true" in chart
    assert "InpUseH4TrendFilter=true" in chart
    assert "InpH4TrendApplyToLong=true" in chart
    assert "InpH4TrendApplyToShort=true" in chart


def test_attach_script_renders_frequency_first_v4_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["freq_v4"]
    chart = module.render_chart(29, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_V4" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpMaxTradesPerDay=12" in chart
    assert "InpCooldownMinutes=5" in chart
    assert "InpMinAtrAbsoluteForEntry=0.00" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,21,23" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_v4_kill_switch.txt" in chart
    assert config["spec_sha256"] == "2b5fe5ba37f5649353534a06f682c328f4c410ebd2ef95a45986e3172b19db3b"


def test_attach_script_renders_clean_portfolio_long_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["clean_long_v5_move12"]
    chart = module.render_chart(30, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_LONG_V5_MOVE12_20260702" in chart
    assert "InpMagicNumber=932210" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_CLN_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,21,23" in chart
    assert "InpMinThreeBarMoveAtr=1.20" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_clean_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a"


def test_attach_script_renders_clean_portfolio_short_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["clean_short_core"]
    chart = module.render_chart(31, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_SHORT_CORE_20260702" in chart
    assert "InpMagicNumber=932211" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_CLN_S" in chart
    assert "InpDirectionMode=2" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23" in chart
    assert "InpMinThreeBarMoveAtr=0.70" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_clean_short_kill_switch.txt" in chart
    assert config["spec_sha256"] == "e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a"


def test_attach_script_renders_deep_v6_max2_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["deep_v6_max2_long"]
    chart = module.render_chart(32, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V6_MAX2_LONG_20260702" in chart
    assert "InpMagicNumber=932220" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DP_L1" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxTradesPerDay=20" in chart
    assert "InpCooldownMinutes=3" in chart
    assert "InpOnePositionPerMagic=false" in chart
    assert "InpMaxOpenPositionsPerMagic=2" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,21,23" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_deep_v6_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d"


def test_backtest_runner_includes_frequency_preserving_feature_loss_variant() -> None:
    text = _text(RUNNER)
    assert 'name="v13_feature_loss_short_extreme_rr0p6"' in text
    assert "SHORT close_to_recent_extreme >= -0.75 block" in text
    base_block = _runner_variant_block(text, "v13_feature_loss_short_extreme_rr0p6")
    assert '"InpFeatureLossFilterEnabled": "true"' in base_block
    assert '"InpFeatureLossFilterShadowOnly": "false"' in base_block
    assert '"InpShortCloseToRecentExtremeBlockMin": "-0.75"' in base_block
    assert '"InpShortCloseToRecentExtremeBlockMaxEnabled": "false"' in base_block
    assert '"InpShortCloseToRecentExtremeBlockMax": "-2.51"' in base_block
    assert '"InpFeatureLossFilterEnabled": "false"' in text


def test_backtest_runner_includes_feature_pair_band_variant_without_mutating_base_v13() -> None:
    text = _text(RUNNER)
    band_block = _runner_variant_block(text, "v13_feature_loss_short_extreme_band_m2p51_rr0p6")
    assert "SHORT close_to_recent_extreme >= -0.75 or <= -2.51 block" in band_block
    assert '"InpFeatureLossFilterEnabled": "true"' in band_block
    assert '"InpFeatureLossFilterShadowOnly": "false"' in band_block
    assert '"InpShortCloseToRecentExtremeBlockMin": "-0.75"' in band_block
    assert '"InpShortCloseToRecentExtremeBlockMaxEnabled": "true"' in band_block
    assert '"InpShortCloseToRecentExtremeBlockMax": "-2.51"' in band_block


def test_attach_script_renders_deep_v13_both_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["deep_v13_both"]
    chart = module.render_chart(33, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V13_BOTH_20260702" in chart
    assert "InpMagicNumber=932221" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DP_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpM5TrendEmaFastPeriod=8" in chart
    assert "InpM5TrendEmaSlowPeriod=21" in chart
    assert "InpM5TrendSlopeBars=3" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpM5TrendMaxDistanceAtr=1.20" in chart
    assert "InpMinBodyFraction=0.30" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert "InpShortCloseLocation=0.42" in chart
    assert "InpMinThreeBarMoveAtr=0.10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_deep_v13_both_kill_switch.txt" in chart
    assert config["spec_sha256"] == "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d"


def test_attach_script_renders_deep_short_core_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["deep_short_core"]
    chart = module.render_chart(34, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SHORT_CORE_20260702" in chart
    assert "InpMagicNumber=932222" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DP_S" in chart
    assert "InpDirectionMode=2" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpBlockedEntryHoursCsv=0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23" in chart
    assert "InpOnePositionPerMagic=true" in chart
    assert "InpMaxOpenPositionsPerMagic=1" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_deep_short_kill_switch.txt" in chart
    assert config["spec_sha256"] == "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d"


def test_attach_script_renders_robust_v6_max2_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["robust_v6_max2_long"]
    chart = module.render_chart(35, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V6_MAX2_LONG_20260702" in chart
    assert "InpMagicNumber=932230" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RB_L1" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxTradesPerDay=20" in chart
    assert "InpCooldownMinutes=3" in chart
    assert "InpOnePositionPerMagic=false" in chart
    assert "InpMaxOpenPositionsPerMagic=2" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,21,23" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_robust_v6_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615"


def test_attach_script_renders_robust_v13_long_no_morning_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["robust_v13_long_no_morning"]
    chart = module.render_chart(36, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V13_LONG_NO_MORNING_20260702" in chart
    assert "InpMagicNumber=932231" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RB_L2" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpM5TrendEmaFastPeriod=8" in chart
    assert "InpM5TrendEmaSlowPeriod=21" in chart
    assert "InpM5TrendSlopeBars=3" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpM5TrendMaxDistanceAtr=1.20" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert "InpMinThreeBarMoveAtr=0.10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_robust_v13_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615"


def test_attach_script_renders_robust_short_night_early_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["robust_short_night_early"]
    chart = module.render_chart(37, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SHORT_NIGHT_EARLY_20260702" in chart
    assert "InpMagicNumber=932232" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RB_S" in chart
    assert "InpDirectionMode=2" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpBlockedEntryHoursCsv=0,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23" in chart
    assert "InpOnePositionPerMagic=true" in chart
    assert "InpMaxOpenPositionsPerMagic=1" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_robust_short_kill_switch.txt" in chart
    assert config["spec_sha256"] == "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615"


def test_attach_script_renders_robust_repair_v6_max2_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["robust_repair_v6_max2_long"]
    chart = module.render_chart(38, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V6_MAX2_LONG_20260702" in chart
    assert "InpMagicNumber=932240" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RP_L1" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpOnePositionPerMagic=false" in chart
    assert "InpMaxOpenPositionsPerMagic=2" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,21,23" in chart
    assert config["spec_sha256"] == "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269"


def test_attach_script_renders_robust_repair_v13_no18_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["robust_repair_v13_long_no_morning_no18"]
    chart = module.render_chart(39, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V13_LONG_NO_MORNING_NO18_20260702" in chart
    assert "InpMagicNumber=932241" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RP_L2" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,18,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert config["spec_sha256"] == "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269"


def test_attach_script_renders_robust_repair_short_night_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["robust_repair_short_night_early"]
    chart = module.render_chart(40, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_SHORT_NIGHT_EARLY_20260702" in chart
    assert "InpMagicNumber=932242" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RP_S" in chart
    assert "InpDirectionMode=2" in chart
    assert "InpBlockedEntryHoursCsv=0,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23" in chart
    assert config["spec_sha256"] == "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269"


def test_attach_script_renders_daily_fit_long_weak_hours_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["daily_fit_long_weak_hours"]
    chart = module.render_chart(41, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DAILY_FIT_LONG_WEAK_HOURS_20260702" in chart
    assert "InpMagicNumber=932250" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DF_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpMaxTradesPerDay=12" in chart
    assert "InpCooldownMinutes=5" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_daily_fit_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "511af42042a5d6cfa3bac71a98c572a5a2292f47554a1f7fdfe1cd11094eac3f"


def test_attach_script_renders_daily_fit_v13_both_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["daily_fit_v13_both"]
    chart = module.render_chart(42, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DAILY_FIT_V13_BOTH_20260702" in chart
    assert "InpMagicNumber=932251" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DF_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpM5TrendEmaFastPeriod=8" in chart
    assert "InpM5TrendEmaSlowPeriod=21" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert "InpShortCloseLocation=0.42" in chart
    assert "InpMinThreeBarMoveAtr=0.10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_daily_fit_v13_both_kill_switch.txt" in chart
    assert config["spec_sha256"] == "511af42042a5d6cfa3bac71a98c572a5a2292f47554a1f7fdfe1cd11094eac3f"


def test_attach_script_renders_daily_fit_repair_long_weak_hours_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["daily_fit_repair_long_weak_hours"]
    chart = module.render_chart(43, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_LONG_WEAK_HOURS_20260702" in chart
    assert "InpMagicNumber=932260" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DFR_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpMaxTradesPerDay=12" in chart
    assert "InpCooldownMinutes=5" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_daily_fit_repair_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "fe911d1c8fb91ed0712eb272b9e517f0b6ca61582a555a9281507d1f2afe9386"


def test_attach_script_renders_daily_fit_repair_v13_both_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["daily_fit_repair_v13_both"]
    chart = module.render_chart(44, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_V13_BOTH_20260702" in chart
    assert "InpMagicNumber=932261" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DFR_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,18,19,20,22" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpM5TrendEmaFastPeriod=8" in chart
    assert "InpM5TrendEmaSlowPeriod=21" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert "InpShortCloseLocation=0.42" in chart
    assert "InpMinThreeBarMoveAtr=0.10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_daily_fit_repair_v13_both_kill_switch.txt" in chart
    assert config["spec_sha256"] == "fe911d1c8fb91ed0712eb272b9e517f0b6ca61582a555a9281507d1f2afe9386"


def test_attach_script_renders_daily_guard_long_weak_hours_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["daily_guard_long_weak_hours"]
    chart = module.render_chart(45, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DAILY_GUARD_LONG_WEAK_HOURS_20260702" in chart
    assert "InpMagicNumber=932270" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DG_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpMaxTradesPerDay=12" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932270,932271" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=25.00" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_daily_guard_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "b5d25b1f2cb109e4aa758b9a4203ec7961d9875000f3589803080a0dd5d26c3c"


def test_attach_script_renders_daily_guard_v13_both_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["daily_guard_v13_both"]
    chart = module.render_chart(46, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_DAILY_GUARD_V13_BOTH_20260702" in chart
    assert "InpMagicNumber=932271" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DG_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,18,19,20,22" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932270,932271" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=25.00" in chart
    assert "InpMaxTradesPerDay=24" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_daily_guard_v13_both_kill_switch.txt" in chart
    assert config["spec_sha256"] == "b5d25b1f2cb109e4aa758b9a4203ec7961d9875000f3589803080a0dd5d26c3c"


def test_attach_script_renders_feature_guard_long_weak_hours_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_guard_long_weak_hours"]
    chart = module.render_chart(47, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_GUARD_LONG_WEAK_HOURS_20260702" in chart
    assert "InpMagicNumber=932280" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_FG_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpMaxTradesPerDay=12" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932280,932281" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=20.00" in chart
    assert "InpFeatureLossFilterEnabled=false" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_guard_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "c36778bef2ced45d19fa25b99480722bfc6741cdcadab0755b22aab9737cefb4"


def test_attach_script_renders_feature_guard_v13_both_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_guard_v13_both"]
    chart = module.render_chart(48, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_GUARD_V13_BOTH_20260702" in chart
    assert "InpMagicNumber=932281" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_FG_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpM5TrendEmaFastPeriod=8" in chart
    assert "InpM5TrendEmaSlowPeriod=21" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert "InpShortCloseLocation=0.42" in chart
    assert "InpMinThreeBarMoveAtr=0.10" in chart
    assert "InpFeatureLossFilterEnabled=true" in chart
    assert "InpFeatureLossFilterShadowOnly=false" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.75" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=false" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932280,932281" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=20.00" in chart
    assert "InpMaxTradesPerDay=24" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_guard_v13_both_kill_switch.txt" in chart
    assert config["spec_sha256"] == "c36778bef2ced45d19fa25b99480722bfc6741cdcadab0755b22aab9737cefb4"


def test_attach_script_renders_feature_band_long_weak_hours_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_long_weak_hours"]
    chart = module.render_chart(49, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_LONG_WEAK_HOURS_20260702" in chart
    assert "InpMagicNumber=932290" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_FB_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpMaxTradesPerDay=12" in chart
    assert "InpPortfolioDailyGuardEnabled=false" in chart
    assert "InpFeatureLossFilterEnabled=false" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "2841f87404e085954da5614b43331f5d85884f3170986ccc5cad01bc35271279"


def test_attach_script_renders_feature_band_v13_both_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_v13_both"]
    chart = module.render_chart(50, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_V13_BOTH_20260702" in chart
    assert "InpMagicNumber=932291" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_FB_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpM5TrendEmaFastPeriod=8" in chart
    assert "InpM5TrendEmaSlowPeriod=21" in chart
    assert "InpM5TrendMinSlopeAtr=0.03" in chart
    assert "InpLongCloseLocation=0.58" in chart
    assert "InpShortCloseLocation=0.42" in chart
    assert "InpMinThreeBarMoveAtr=0.10" in chart
    assert "InpFeatureLossFilterEnabled=true" in chart
    assert "InpFeatureLossFilterShadowOnly=false" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.75" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=false" in chart
    assert "InpMaxTradesPerDay=24" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_v13_both_kill_switch.txt" in chart
    assert config["spec_sha256"] == "2841f87404e085954da5614b43331f5d85884f3170986ccc5cad01bc35271279"


def test_attach_script_renders_feature_band_daily_income_long_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_daily_income_long"]
    chart = module.render_chart(51, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_LONG_20260702" in chart
    assert "InpMagicNumber=932292" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DI_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpMaxEstimatedCostR=0.05" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932292,932293" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=0" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_daily_income_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b"


def test_attach_script_renders_feature_band_daily_income_v13_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_daily_income_v13_both"]
    chart = module.render_chart(52, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_V13_20260702" in chart
    assert "InpMagicNumber=932293" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DI_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpFeatureLossFilterEnabled=true" in chart
    assert "InpFeatureLossFilterShadowOnly=false" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.75" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932292,932293" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=0" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_daily_income_v13_kill_switch.txt" in chart
    assert config["spec_sha256"] == "188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b"


def test_attach_script_renders_feature_band_daily_reliability_long_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_daily_reliability_long"]
    chart = module.render_chart(53, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_LONG_20260702" in chart
    assert "InpMagicNumber=932294" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DR_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932294,932295" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=15" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_daily_reliability_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "693d070050666ccd066a834f71b666b3f865829e6a05c8942190be7da9c1729b"


def test_attach_script_renders_feature_band_daily_reliability_v13_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_daily_reliability_v13_both"]
    chart = module.render_chart(54, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_V13_20260702" in chart
    assert "InpMagicNumber=932295" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_DR_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.75" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932294,932295" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=15" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_daily_reliability_v13_kill_switch.txt" in chart
    assert config["spec_sha256"] == "693d070050666ccd066a834f71b666b3f865829e6a05c8942190be7da9c1729b"


def test_attach_script_renders_feature_band_residual_reliability_long_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_residual_reliability_long"]
    chart = module.render_chart(55, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_LONG_20260702" in chart
    assert "InpMagicNumber=932296" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RR_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,18,22,23" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932296,932297" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=15" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_residual_reliability_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "1b84b0f7195a79a7cd031118ef54c203a55442027288064bc817da07c2510edd"


def test_attach_script_renders_feature_band_residual_reliability_v13_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_residual_reliability_v13_both"]
    chart = module.render_chart(56, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_V13_20260702" in chart
    assert "InpMagicNumber=932297" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RR_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8,18" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.92" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932296,932297" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=15" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_residual_reliability_v13_kill_switch.txt" in chart
    assert config["spec_sha256"] == "1b84b0f7195a79a7cd031118ef54c203a55442027288064bc817da07c2510edd"


def test_attach_script_renders_feature_band_residual_plus50_cooldown10_long_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_residual_plus50_cooldown10_long"]
    chart = module.render_chart(57, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_LONG_20260702" in chart
    assert "InpMagicNumber=932298" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RR10_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,18,22,23" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932298,932299" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71"


def test_attach_script_renders_feature_band_residual_plus50_cooldown10_v13_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_residual_plus50_cooldown10_v13_both"]
    chart = module.render_chart(58, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_V13_20260702" in chart
    assert "InpMagicNumber=932299" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RR10_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8,18" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.92" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932298,932299" in chart
    assert "InpPortfolioDailyProfitTargetUsd=50.00" in chart
    assert "InpPortfolioMaxTradesPerDay=6" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_v13_kill_switch.txt" in chart
    assert config["spec_sha256"] == "1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71"


def test_attach_script_renders_feature_band_residual_plus75_high_net_long_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_residual_plus75_high_net_long"]
    chart = module.render_chart(59, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_LONG_20260702" in chart
    assert "InpMagicNumber=932300" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RR75_L" in chart
    assert "InpDirectionMode=1" in chart
    assert "InpRiskReward=0.70" in chart
    assert "InpBlockedEntryHoursCsv=2,9,10,11,12,17,18,22,23" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932300,932301" in chart
    assert "InpPortfolioDailyProfitTargetUsd=75.00" in chart
    assert "InpPortfolioMaxTradesPerDay=0" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_residual_plus75_high_net_long_kill_switch.txt" in chart
    assert config["spec_sha256"] == "de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a"


def test_attach_script_renders_feature_band_residual_plus75_high_net_v13_inputs() -> None:
    module = _attach_module()
    config = module.VARIANT_CONFIGS["feature_band_residual_plus75_high_net_v13_both"]
    chart = module.render_chart(60, config)
    assert "InpRunId=A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_V13_20260702" in chart
    assert "InpMagicNumber=932301" in chart
    assert "InpOrderComment=A1_XAU_M5_MOM_RR75_B" in chart
    assert "InpSignalMode=5" in chart
    assert "InpDirectionMode=0" in chart
    assert "InpRiskReward=0.60" in chart
    assert "InpBlockedEntryHoursCsv=0,2,4,9,10,11,12,16,19,20" in chart
    assert "InpBlockedLongEntryHoursCsv=6,7,8,18" in chart
    assert "InpBlockedShortEntryHoursCsv=13,14,15,17,18" in chart
    assert "InpShortCloseToRecentExtremeBlockMin=-0.92" in chart
    assert "InpShortCloseToRecentExtremeBlockMaxEnabled=true" in chart
    assert "InpShortCloseToRecentExtremeBlockMax=-2.51" in chart
    assert "InpPortfolioDailyGuardEnabled=true" in chart
    assert "InpPortfolioGuardMagicCsv=932300,932301" in chart
    assert "InpPortfolioDailyProfitTargetUsd=75.00" in chart
    assert "InpPortfolioMaxTradesPerDay=0" in chart
    assert "InpPortfolioDailyLossStopUsd=0.00" in chart
    assert "InpPortfolioCooldownAfterLossMinutes=10" in chart
    assert "InpKillSwitchFileName=a1_xau_m5_momentum_feature_band_residual_plus75_high_net_v13_kill_switch.txt" in chart
    assert config["spec_sha256"] == "de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a"


def test_attach_script_finds_existing_lane_by_identity_not_generic_ea_name(tmp_path: Path) -> None:
    module = _attach_module()
    profile = tmp_path
    (profile / "chart01.chr").write_text(
        "\n".join(
            [
                "name=A1XauM5MomentumContinuationExecutor",
                "InpRunId=OTHER_LANE",
                "InpMagicNumber=932200",
                "InpOrderComment=A1_XAU_M5_MOM_V4",
            ]
        ),
        encoding="utf-8",
    )
    (profile / "chart02.chr").write_text(
        "\n".join(
            [
                "name=A1XauM5MomentumContinuationExecutor",
                "InpRunId=A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_SHORT_CORE_20260702",
                "InpMagicNumber=932211",
                "InpOrderComment=A1_XAU_M5_MOM_CLN_S",
            ]
        ),
        encoding="utf-8",
    )
    assert module.find_existing_lane(profile, module.VARIANT_CONFIGS["clean_long_v5_move12"]) is None
    assert module.find_existing_lane(profile, module.VARIANT_CONFIGS["clean_short_core"]) == profile / "chart02.chr"
