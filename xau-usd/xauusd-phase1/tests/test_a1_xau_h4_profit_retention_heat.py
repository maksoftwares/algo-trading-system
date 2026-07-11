from __future__ import annotations

import importlib.util
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


B = load("build_a1_xau_h4_profit_retention_heat_source")
R = load("run_a1_xau_h4_profit_retention_heat_exact")


def frozen_config() -> str:
    return (
        ROOT / "outputs" / "reports" / "A1_XAU_ROUTER_ENTRY_HOLD_PATH_INPUTS_20260710"
        / "immutable_evidence" / R.H4_SPEC.source_id / "tester.ini"
    ).read_text(encoding="utf-8-sig")


def test_heat_config_preserves_profit_stream_and_locks_six_pct() -> None:
    text, _ = R.derive_config(frozen_config(), R.extended.HORIZONS[1])
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Deposit"] == "1000"
    assert parsed["TesterInputs"]["InpFixedLots"] == "0.01"
    assert parsed["TesterInputs"]["InpOnePositionPerMagic"] == "false"
    assert parsed["TesterInputs"]["InpMaxOpenPositionsPerMagic"] == "32"
    assert parsed["TesterInputs"]["InpMaxAggregateStopRiskPct"] == "6.00"


def test_profit_protection_variant_uses_existing_frozen_defaults() -> None:
    text, _ = R.derive_config(frozen_config(), R.extended.HORIZONS[1], True)
    parsed = R.exact.parse_ini(text)
    assert parsed["TesterInputs"]["InpProfitProtectionEnabled"] == "true"
    assert parsed["TesterInputs"]["InpProfitProtectionShadowOnly"] == "false"
    assert parsed["TesterInputs"]["InpProfitProtectionTriggerR"] == "0.80"
    assert parsed["TesterInputs"]["InpProfitProtectionLockR"] == "0.20"


def test_source_guard_is_causal_and_retains_original_state_signal() -> None:
    base = (ROOT / "outputs" / "reports" / "A1_XAU_H4_EPISODE_IDENTITY_REPAIR_EXACT_20260711_FINAL2" / "compiled" / "A1XauH4EpisodeIdentityRepairV1.mq5").read_text(encoding="utf-8")
    assert "h4_previous_close <= box_high" in base
    assert "AggregateStopRiskAllows" not in base
    assert "AggregateStopRiskAllows" in B.HEAT_HELPER
    assert "POSITION_PRICE_CURRENT" in B.HEAT_HELPER
    assert "final_pnl" not in B.HEAT_HELPER.lower()


def test_locked_gate_requires_profit_retention_and_drawdown() -> None:
    row = {
        "horizon": "ten_year",
        "maximum_relative_equity_drawdown_pct": 9.0,
        "net_profit_retention_pct": 61.0,
        "order_failure_count": 0,
        "trade_metrics": {"profit_factor": 1.4, "net_usd": 5000.0, "trades": 101},
        "exposure": {"maximum_accepted_projected_heat_pct": 6.0},
    }
    assert R.evaluate([row])["pass"] is True
    row["net_profit_retention_pct"] = 59.9
    assert R.evaluate([row])["pass"] is False


def test_cli_has_no_live_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.isdisjoint({"live", "demo", "account", "server", "attach", "profile"})
