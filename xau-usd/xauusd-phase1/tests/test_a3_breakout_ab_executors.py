from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERTS = ROOT / "mt5" / "Experts"
INCLUDE = ROOT / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh"
PRESETS = ROOT / "mt5" / "Presets"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _text(path).splitlines():
        if "=" in line and not line.strip().startswith(";"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def test_a3_breakout_wrappers_use_shared_breakout_kernel_and_separate_magics():
    plain = _text(EXPERTS / "Account3BreakoutPlainExecutor.mq5")
    improved = _text(EXPERTS / "Account3BreakoutImprovedExecutor.mq5")
    compat = _text(EXPERTS / "Account3BreakoutTier1CompatExecutor.mq5")
    base = _text(INCLUDE)

    assert "#include <A3BreakoutExecutorBase.mqh>" in plain
    assert "#include <A3BreakoutExecutorBase.mqh>" in improved
    assert "#include <A3BreakoutExecutorBase.mqh>" in compat
    assert "#include <Phase1/Phase1BreakoutRetest.mqh>" in base
    assert "g_breakout_observer.Evaluate(_Symbol, point, observation);" in base
    assert '#define A3_BREAKOUT_DEFAULT_MAGIC 933200' in plain
    assert '#define A3_BREAKOUT_DEFAULT_MAGIC 933300' in improved
    assert '#define A3_BREAKOUT_DEFAULT_MAGIC 933400' in compat
    assert "InpMagicNumber != A3_BREAKOUT_EXPECTED_MAGIC" in base


def test_a3_breakout_committed_defaults_are_non_executing_and_a3_scoped():
    base = _text(INCLUDE)
    assert "input bool InpDryRunOnly = true;" in base
    assert "input bool InpBrokerActionAllowed = false;" in base
    assert 'input string InpAllowedAccountLoginsCsv = "1033669";' in base
    assert 'input string InpTargetSymbol = "XAUUSD";' in base
    assert 'input string InpExpectedServerMarker = "Demo";' in base
    assert 'input string InpExecutionKillSwitchFileName = "A3_EXECUTION_KILL.txt";' in base
    assert 'input string InpFullStopFileName = "A3_FULL_STOP.txt";' in base
    assert "FullStopActive()" in base
    assert "ExecutionKillSwitchActive()" in base
    assert "EXECUTION_KILL_SWITCH_BLOCK" in base
    assert 'ContainsText(server, "live") || ContainsText(server, "real")' in base
    assert "SCOPE_LOCK_LOGIN_BLOCK" in base
    assert "SCOPE_LOCK_SYMBOL_BLOCK" in base
    assert "SCOPE_LOCK_DEMO_SERVER_BLOCK" in base
    assert "InpFixedLot = 0.01" in base
    assert "InpMaxOpenPositionsPerMagic = 1" in base
    assert "input bool InpTradeSessionGateEnabled = A3_BREAKOUT_SESSION_GATE_DEFAULT;" in base
    assert "input bool InpXauStopDistanceFloorEnabled = A3_BREAKOUT_STOP_FLOOR_DEFAULT;" in base


def test_a3_breakout_new_base_macro_defaults_protect_existing_lanes():
    plain = _text(EXPERTS / "Account3BreakoutPlainExecutor.mq5")
    improved = _text(EXPERTS / "Account3BreakoutImprovedExecutor.mq5")
    base = _text(INCLUDE)

    assert "#ifndef A3_BREAKOUT_SESSION_GATE_DEFAULT" in base
    assert "#define A3_BREAKOUT_SESSION_GATE_DEFAULT false" in base
    assert "#ifndef A3_BREAKOUT_STOP_FLOOR_DEFAULT" in base
    assert "#define A3_BREAKOUT_STOP_FLOOR_DEFAULT false" in base
    assert "#ifndef A3_BREAKOUT_TREND_SHADOW_DEFAULT" in base
    assert "#define A3_BREAKOUT_TREND_SHADOW_DEFAULT false" in base

    for wrapper in (plain, improved):
        assert "A3_BREAKOUT_SESSION_GATE_DEFAULT" not in wrapper
        assert "A3_BREAKOUT_STOP_FLOOR_DEFAULT" not in wrapper
        assert "A3_BREAKOUT_TREND_SHADOW_DEFAULT" not in wrapper


def test_a3_breakout_lane_b_only_enables_guard_and_exit_defaults():
    plain = _text(EXPERTS / "Account3BreakoutPlainExecutor.mq5")
    improved = _text(EXPERTS / "Account3BreakoutImprovedExecutor.mq5")
    compat = _text(EXPERTS / "Account3BreakoutTier1CompatExecutor.mq5")
    base = _text(INCLUDE)

    assert "#define A3_BREAKOUT_TREND_GUARD_DEFAULT false" in plain
    assert "#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT false" in plain
    assert "#define A3_BREAKOUT_TREND_GUARD_DEFAULT true" in improved
    assert "#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT true" in improved
    assert "#define A3_BREAKOUT_TREND_GUARD_DEFAULT false" in compat
    assert "#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT false" in compat
    assert "TrendGuardPass" in base
    assert "MoveStopToBreakeven" in base
    assert "TakePartialProfit" in base
    assert "PARTIAL_SKIP_MIN_VOLUME" in base
    assert "FIXED_001_LOT_CANNOT_LEAVE_RUNNER" in base


def test_a3_breakout_safe_presets_match_magic_and_do_not_arm():
    cases = [
        ("Account3BreakoutPlainExecutor.safe_xauusd.set", "933200", "A3_BREAKOUT_PLAIN", "false", "false"),
        ("Account3BreakoutImprovedExecutor.safe_xauusd.set", "933300", "A3_BREAKOUT_IMPROVED", "true", "true"),
        ("Account3BreakoutTier1CompatExecutor.safe_xauusd.set", "933400", "A3_BREAKOUT_TIER1_COMPAT", "false", "false"),
    ]
    for preset_name, magic, comment, trend_guard, exit_protection in cases:
        values = _values(PRESETS / preset_name)
        assert values["InpDryRunOnly"] == "true"
        assert values["InpBrokerActionAllowed"] == "false"
        assert values["InpAllowedAccountLoginsCsv"] == "1033669"
        assert values["InpTargetSymbol"] == "XAUUSD"
        assert values["InpExecutionKillSwitchFileName"] == "A3_EXECUTION_KILL.txt"
        assert values["InpFullStopFileName"] == "A3_FULL_STOP.txt"
        assert values["InpMagicNumber"] == magic
        assert values["InpOrderComment"] == comment
        assert values["InpFixedLot"] == "0.01"
        assert values["InpMaxOpenPositionsPerMagic"] == "1"
        assert values["InpTrendGuardEnabled"] == trend_guard
        assert values["InpBreakevenEnabled"] == exit_protection
        assert values["InpPartialTakeProfitEnabled"] == exit_protection


def test_a3_tier1_compat_copies_a2_gate_and_floor_but_keeps_trend_shadow_only():
    compat = _text(EXPERTS / "Account3BreakoutTier1CompatExecutor.mq5")
    base = _text(INCLUDE)
    values = _values(PRESETS / "Account3BreakoutTier1CompatExecutor.safe_xauusd.set")
    attach_script = _text(ROOT / "scripts" / "attach_a3_tier1_compat_broker_action.py")

    assert "#define A3_BREAKOUT_SESSION_GATE_DEFAULT true" in compat
    assert "#define A3_BREAKOUT_STOP_FLOOR_DEFAULT true" in compat
    assert "#define A3_BREAKOUT_TREND_SHADOW_DEFAULT true" in compat
    assert "ServerHourInTradeSession" in base
    assert 'guard_reason = "SERVER_HOUR_SESSION_GATE";' in base
    assert "InpXauStopDistanceFloorEnabled" in base
    assert 'if(_Symbol == "XAUUSD" && min_distance < 300.0 * point)' in base
    assert "TrendGuardDecision" in base
    assert "trend_shadow_reason" in base

    assert values["InpTradeSessionGateEnabled"] == "true"
    assert values["InpTradeSessionStartHour"] == "12"
    assert values["InpTradeSessionEndHour"] == "15"
    assert values["InpXauStopDistanceFloorEnabled"] == "true"
    assert values["InpTrendGuardEnabled"] == "false"
    assert values["InpTrendGuardShadowOnly"] == "true"
    assert '"InpExecutionKillSwitchFileName": "A3_EXECUTION_KILL.txt"' in attach_script
    assert '"InpFullStopFileName": "A3_FULL_STOP.txt"' in attach_script
