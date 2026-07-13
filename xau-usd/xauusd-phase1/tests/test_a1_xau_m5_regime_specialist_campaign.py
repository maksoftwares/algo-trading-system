from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_a1_xau_m5_regime_specialist_campaign.py"
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
VERDICT = ROOT / "docs" / "A1_XAU_M5_REGIME_SPECIALIST_CAMPAIGN_VERDICT_2026_07_13.json"


def load_campaign():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("m5_regime_campaign", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_campaign_has_four_frozen_candidates_per_tradable_regime() -> None:
    campaign = load_campaign()
    names = [variant.name for variant in campaign.PRIMARY_VARIANTS]
    assert len(names) == len(set(names)) == 16
    for prefix in ("r1_", "r2_", "r3_", "r4_"):
        assert sum(name.startswith(prefix) for name in names) == 4


def test_secondary_campaign_adds_new_families_only_for_missing_regimes() -> None:
    campaign = load_campaign()
    primary = {variant.name for variant in campaign.PRIMARY_VARIANTS}
    secondary = {variant.name for variant in campaign.SECONDARY_VARIANTS}
    assert len(secondary) == 12
    assert primary.isdisjoint(secondary)
    assert not any(name.startswith("r2_") for name in secondary)
    for prefix in ("r1_", "r3_", "r4_"):
        assert sum(name.startswith(prefix) for name in secondary) == 4


def test_tertiary_campaign_routes_preexisting_profiles_without_duplication() -> None:
    campaign = load_campaign()
    previous = {
        variant.name
        for variant in campaign.PRIMARY_VARIANTS + campaign.SECONDARY_VARIANTS
    }
    tertiary = {variant.name for variant in campaign.TERTIARY_VARIANTS}
    assert len(tertiary) == 8
    assert previous.isdisjoint(tertiary)
    for prefix in ("r1_", "r2_", "r3_", "r4_"):
        assert sum(name.startswith(prefix) for name in tertiary) == 2


def test_router_substitution_removes_legacy_htf_owner_only() -> None:
    campaign = load_campaign()
    previous = {
        variant.name
        for variant in (
            campaign.PRIMARY_VARIANTS
            + campaign.SECONDARY_VARIANTS
            + campaign.TERTIARY_VARIANTS
        )
    }
    recovery = {variant.name for variant in campaign.ROUTER_SUBSTITUTED_VARIANTS}
    assert len(recovery) == 8
    assert previous.isdisjoint(recovery)
    for variant in campaign.ROUTER_SUBSTITUTED_VARIANTS:
        assert variant.tester_inputs["InpUseH1TrendFilter"] == "false"
        assert variant.tester_inputs["InpUseH4TrendFilter"] == "false"
    for prefix in ("r1_", "r2_", "r3_", "r4_"):
        assert sum(name.startswith(prefix) for name in recovery) == 2


def test_mechanism_followup_is_bounded_to_missing_regimes() -> None:
    campaign = load_campaign()
    followup = {variant.name for variant in campaign.MECHANISM_FOLLOWUP_VARIANTS}
    assert len(followup) == 6
    assert not any(name.startswith("r2_") for name in followup)
    for prefix in ("r1_", "r3_", "r4_"):
        assert sum(name.startswith(prefix) for name in followup) == 2
    for variant in campaign.MECHANISM_FOLLOWUP_VARIANTS:
        assert variant.tester_inputs["InpUseH1TrendFilter"] == "false"
        assert variant.tester_inputs["InpUseH4TrendFilter"] == "false"


def test_bounded_discovery_has_fixed_regime_counts_and_actual_reclaims() -> None:
    campaign = load_campaign()
    discovery = campaign.BOUNDED_DISCOVERY_VARIANTS
    names = {variant.name for variant in discovery}
    assert len(names) == len(discovery) == 8
    assert sum(name.startswith("r1_") for name in names) == 2
    assert sum(name.startswith("r3_") for name in names) == 3
    assert sum(name.startswith("r4_") for name in names) == 3
    assert not any(name.startswith("r2_") for name in names)
    prior_day = next(item for item in discovery if item.name == "r4_discovery_prior_day_reclaim")
    assert prior_day.tester_inputs["InpPriorDayLevelMode"] == "1"


def test_every_candidate_is_m5_routed_and_shock_is_never_enabled() -> None:
    campaign = load_campaign()
    expected_router = {"r1_": "1", "r2_": "2", "r3_": "6", "r4_": "4"}
    for variant in campaign.VARIANTS:
        prefix = variant.name[:3]
        assert variant.tester_inputs["InpRegimeRouterMode"] == expected_router[prefix]
        assert variant.tester_inputs["InpRegimeSnapshotLogEnabled"] == "false"
        assert variant.tester_inputs["InpFixedLots"] == "0.01"
    assert "SHOCK" not in {campaign.regime_for(variant.name) for variant in campaign.VARIANTS}


def test_ea_has_compression_only_router_and_global_data_fail_closed() -> None:
    source = EA.read_text(encoding="utf-8")
    assert "REGIME_ROUTER_R3_COMPRESSION_ONLY = 6" in source
    assert 'return "r3_compression_only";' in source
    assert "if(!RegimeRouterDataAvailable())" in source
    assert "if(regime == XAU_REGIME_SHOCK)" in source
    assert "if(regime == XAU_REGIME_COMPRESSION)" in source


def test_tracked_verdict_keeps_rejected_regimes_disabled() -> None:
    import json

    verdict = json.loads(VERDICT.read_text(encoding="utf-8"))
    regimes = verdict["regimes"]
    assert regimes["DOWNTREND"]["status"] == "TEN_YEAR_EDGE_CONFIRMED_NOT_DEMO_READY"
    assert regimes["UPTREND"]["status"] == "NO_TEN_YEAR_CONFIRMED_SPECIALIST"
    assert regimes["COMPRESSION"]["status"] == "NO_SPECIALIST"
    assert regimes["CHOP"]["status"] == "NO_SPECIALIST"
    assert regimes["SHOCK"]["trading_enabled"] is False
    assert verdict["authorization"] == "RESEARCH_ONLY_NO_DEMO_OR_LIVE_DEPLOYMENT"
