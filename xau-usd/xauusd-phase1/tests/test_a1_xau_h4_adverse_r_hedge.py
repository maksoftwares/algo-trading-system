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
V2 = load("build_a1_xau_h4_cluster_highwater_rearm_source")
V3 = load("build_a1_xau_h4_cluster_highwater_total_mtm_source")


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


def test_scaled_highwater_config_is_fixed_at_two_and_zero_point_eight_pct() -> None:
    text, _ = R.derive_config(
        frozen_config(), R.extended.HORIZONS[1], scaled_highwater=True,
    )
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Expert"].endswith("A1XauH4ClusterHighwaterHedgeV1.ex5")
    assert "SCALED_2P0_0P8" in parsed["Tester"]["Report"]
    assert parsed["TesterInputs"]["InpClusterEquityHedgeTriggerPct"] == "2.00"
    assert parsed["TesterInputs"]["InpClusterEquityHedgeReleasePct"] == "0.80"


def test_rearm_repair_keeps_five_and_two_and_uses_v2_expert() -> None:
    text, _ = R.derive_config(
        frozen_config(), R.extended.HORIZONS[1], rearm_highwater=True,
    )
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Expert"].endswith("A1XauH4ClusterHighwaterRearmV2.ex5")
    assert "REARM_V2" in parsed["Tester"]["Report"]
    assert parsed["TesterInputs"]["InpClusterEquityHedgeTriggerPct"] == "5.00"
    assert parsed["TesterInputs"]["InpClusterEquityHedgeReleasePct"] == "2.00"


def test_rearm_repair_uses_realization_invariant_total_mtm() -> None:
    assert "CloseClusterHedgeVolume" in V2.RELEASE_REPAIR
    assert "g_cluster_hedge_rearm_ready = true;" in V2.RELEASE_REPAIR
    assert "g_primary_cluster_peak_profit" not in V2.RELEASE_REPAIR
    assert "g_primary_cluster_realized_profit + primary_profit" in V2.CALCULATION_REPAIR
    assert "DEAL_PROFIT" in V2.TRANSACTION_REPAIR
    assert "DEAL_COMMISSION" in V2.TRANSACTION_REPAIR
    assert "DEAL_SWAP" in V2.TRANSACTION_REPAIR
    assert "DEAL_FEE" in V2.TRANSACTION_REPAIR
    assert "final_pnl" not in V2.TRANSACTION_REPAIR.lower()


def test_total_mtm_v3_synchronizes_settlement_before_hedge_action() -> None:
    text, _ = R.derive_config(
        frozen_config(), R.extended.HORIZONS[1], total_mtm_highwater=True,
    )
    parsed = R.exact.parse_ini(text)
    assert parsed["Tester"]["Expert"].endswith("A1XauH4ClusterHighwaterTotalMtmV3.ex5")
    assert "TOTAL_MTM_V3" in parsed["Tester"]["Report"]
    assert parsed["TesterInputs"]["InpClusterEquityHedgeTriggerPct"] == "5.00"
    assert parsed["TesterInputs"]["InpClusterEquityHedgeReleasePct"] == "2.00"
    assert "PrimaryLifetimeRealizedProfit" in V3.HISTORY_HELPER
    assert "primary_settlement_tick" in V3.CALCULATION_REPAIR
    assert "if(primary_settlement_tick)" in V3.FLAT_REPAIR
    assert "g_primary_cluster_peak_profit" not in V3.RELEASE_REPAIR
    assert "g_cluster_hedge_rearm_ready = true;" in V3.RELEASE_REPAIR


def test_primary_identity_is_stronger_than_entry_count(tmp_path: Path) -> None:
    header = "timestamp_broker\tdirection\tvolume\tprice\tentry_code\tmagic\n"
    control = tmp_path / "control.tsv"
    candidate = tmp_path / "candidate.tsv"
    control.write_text(
        header + "2025.01.01 12:00:00\tLONG\t0.01\t2600.00\t0\t932200\n",
        encoding="utf-8",
    )
    candidate.write_text(
        header
        + "2025.01.01 12:05:00\tLONG\t0.01\t2601.00\t0\t932200\n"
        + "2025.01.01 12:05:00\tSHORT\t0.01\t2601.00\t0\t932202\n",
        encoding="utf-8",
    )
    identity = R.primary_entry_identity(control, candidate)
    assert identity["expected_primary_entries"] == 1
    assert identity["actual_primary_entries"] == 1
    assert identity["mismatch_count"] == 1
    assert identity["exact_match"] is False


def test_scaled_manifest_records_executed_runtime_thresholds(tmp_path: Path) -> None:
    manifest = tmp_path / "source_manifest.json"
    manifest.write_text(
        '{"fixed_rule":{"primary_highwater_trigger_pct":5.0,"primary_highwater_release_pct":2.0}}',
        encoding="utf-8",
    )
    payload = R.normalize_source_manifest(manifest, scaled_highwater=True)
    assert payload["fixed_rule"]["primary_highwater_trigger_pct"] == 2.0
    assert payload["fixed_rule"]["primary_highwater_release_pct"] == 0.8
    assert payload["runtime_tester_rule"] == {
        "InpClusterEquityHedgeTriggerPct": "2.00",
        "InpClusterEquityHedgeReleasePct": "0.80",
    }


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


def test_scaled_highwater_gate_uses_ten_year_net_and_near_ten_drawdown() -> None:
    rows = []
    for horizon in ("five_year", "ten_year"):
        rows.append({
            "horizon": horizon,
            "maximum_relative_equity_drawdown_pct": 12.0,
            "order_failure_count": 0,
            "trade_metrics": {"net_usd": 7000.0, "profit_factor": 1.3},
            "reconciliation": {
                "primary_entry_count": R.EXPECTED_PRIMARY_ENTRIES[horizon],
                "primary_entry_identity_exact": True,
                "management_failure_count": 0,
                "unmatched_position_ids": [],
                "hedge_entry_volume": 0.2,
                "hedge_exit_volume": 0.2,
            },
        })
    assert R.evaluate_scaled_highwater(rows)["pass"] is True
    rows[1]["maximum_relative_equity_drawdown_pct"] = 12.01
    assert R.evaluate_scaled_highwater(rows)["pass"] is False


def test_cli_has_no_live_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.isdisjoint({"live", "demo", "account", "server", "attach", "profile"})
    assert "cluster_highwater_rearm_repair" in destinations
    assert "cluster_highwater_total_mtm_repair" in destinations
