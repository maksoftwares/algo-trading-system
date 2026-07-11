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


B = load("build_a1_xau_h4_adverse_r_hedge_source")
R = load("run_a1_xau_h4_adverse_r_hedge_exact")
C = load("build_a1_xau_h4_cluster_equity_hedge_source")
W = load("build_a1_xau_h4_cluster_highwater_hedge_source")


def frozen_config() -> str:
    return (
        ROOT / "outputs" / "reports" / "A1_XAU_ROUTER_ENTRY_HOLD_PATH_INPUTS_20260710"
        / "immutable_evidence" / R.H4_SPEC.source_id / "tester.ini"
    ).read_text(encoding="utf-8-sig")


def test_config_preserves_original_h4_entries_and_locks_hedge() -> None:
    text, _ = R.derive_config(frozen_config(), R.extended.HORIZONS[1])
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Deposit"] == "1000"
    assert parsed["TesterInputs"]["InpFixedLots"] == "0.01"
    assert parsed["TesterInputs"]["InpOnePositionPerMagic"] == "false"
    assert parsed["TesterInputs"]["InpMaxOpenPositionsPerMagic"] == "32"
    assert parsed["TesterInputs"]["InpAdverseRHedgeTriggerR"] == "0.25"
    assert parsed["TesterInputs"]["InpAdverseRHedgeRecoveryR"] == "0.00"


def test_source_rule_is_one_cycle_and_separate_magic() -> None:
    assert "HedgeCycleDone(primary_ticket)" in B.HEDGE_HELPERS
    assert "MarkHedgeCycleDone(primary_ticket)" in B.HEDGE_HELPERS
    assert "InpAdverseRHedgeMagicNumber" in B.HEDGE_HELPERS
    assert "g_hedge_trade.Sell(volume" in B.HEDGE_HELPERS
    assert "final_pnl" not in B.HEDGE_HELPERS.lower()


def test_cluster_config_is_fixed_at_five_and_two_pct() -> None:
    text, _ = R.derive_config(frozen_config(), R.extended.HORIZONS[1], True)
    parsed = R.exact.parse_ini(text)
    assert parsed["TesterInputs"]["InpClusterEquityHedgeTriggerPct"] == "5.00"
    assert parsed["TesterInputs"]["InpClusterEquityHedgeReleasePct"] == "2.00"
    assert parsed["TesterInputs"]["InpClusterEquityHedgeMagicNumber"] == R.CLUSTER_HEDGE_MAGIC


def test_highwater_config_keeps_same_five_and_two_pct() -> None:
    text, _ = R.derive_config(frozen_config(), R.extended.HORIZONS[1], highwater=True)
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Expert"].endswith("A1XauH4ClusterHighwaterHedgeV1.ex5")
    assert parsed["TesterInputs"]["InpClusterEquityHedgeTriggerPct"] == "5.00"
    assert parsed["TesterInputs"]["InpClusterEquityHedgeReleasePct"] == "2.00"


def test_cluster_actions_defer_during_closed_market() -> None:
    assert C.HELPERS.count("if(!CurrentTradeSessionOpen())") == 2
    assert W.EXPERT_NAME == "A1XauH4ClusterHighwaterHedgeV1"


def test_gate_requires_full_profit_and_drawdown() -> None:
    rows = []
    for horizon, net in (("five_year", 6500.0), ("ten_year", 8000.0)):
        rows.append({
            "horizon": horizon,
            "maximum_relative_equity_drawdown_pct": 10.0,
            "order_failure_count": 0,
            "trade_metrics": {"net_usd": net, "profit_factor": 1.3},
            "reconciliation": {
                "management_failure_count": 0,
                "maximum_hedge_cycles_per_primary": 1,
                "cluster_mode": False,
                "unmatched_position_ids": [],
                "hedge_entry_count": 10,
                "hedge_exit_count": 10,
                "hedge_entry_volume": 0.1,
                "hedge_exit_volume": 0.1,
            },
        })
    assert R.evaluate(rows)["pass"] is True
    rows[1]["trade_metrics"]["net_usd"] = 7999.99
    assert R.evaluate(rows)["pass"] is False


def test_cli_has_no_live_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.isdisjoint({"live", "demo", "account", "server", "attach", "profile"})
