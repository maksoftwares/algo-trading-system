from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as mt5


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_M5_REGIME_SPECIALIST_CAMPAIGN_20260713"
HISTORICAL_RUN_AUTHORIZED = True

# Frozen before this campaign was executed.  The screen is intentionally small:
# four structurally different M5-native signal families per tradable Router V1
# state.  SHOCK is a capital-protection state and is never permitted to enter.
BASE_INPUTS = {
    "InpFixedLots": "0.01",
    "InpUseRiskNormalizedLots": "false",
    "InpMaxRiskLots": "0.05",
    "InpMaxTradesPerDay": "8",
    "InpCooldownMinutes": "10",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpRiskReward": "1.50",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.15",
    # Snapshot mode is a no-trade attribution mode in this EA.  Trading screens
    # must leave it disabled and rely on the fail-closed regime router.
    "InpRegimeSnapshotLogEnabled": "false",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
}


def candidate(
    name: str,
    label: str,
    regime_mode: int,
    direction_mode: int,
    signal_mode: int,
    **inputs: str,
) -> mt5.Variant:
    return mt5.Variant(
        name=name,
        label=label,
        run_id=f"BT_A1_XAU_M5_REGIME_{name.upper()}_V1",
        tester_inputs={
            **BASE_INPUTS,
            "InpRegimeRouterMode": str(regime_mode),
            "InpDirectionMode": str(direction_mode),
            "InpSignalMode": str(signal_mode),
            **inputs,
        },
    )


def profile_candidate(
    name: str,
    label: str,
    regime_mode: int,
    source_profile: str,
) -> mt5.Variant:
    """Route an unchanged, pre-existing M5 profile into one strict regime."""
    source = next((item for item in mt5.VARIANTS if item.name == source_profile), None)
    if source is None:
        raise ValueError(f"Missing pre-existing M5 profile: {source_profile}")
    return mt5.Variant(
        name=name,
        label=label,
        run_id=f"BT_A1_XAU_M5_REGIME_{name.upper()}_V1",
        tester_inputs={
            **BASE_INPUTS,
            **source.tester_inputs,
            "InpRegimeRouterMode": str(regime_mode),
            "InpRegimeSnapshotLogEnabled": "false",
        },
    )


def router_substituted_profile_candidate(
    name: str,
    label: str,
    regime_mode: int,
    source_profile: str,
) -> mt5.Variant:
    """Preserve the M5 profile while replacing its old HTF owner with Router V1."""
    routed = profile_candidate(name, label, regime_mode, source_profile)
    return mt5.Variant(
        name=routed.name,
        label=routed.label,
        run_id=routed.run_id,
        tester_inputs={
            **routed.tester_inputs,
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
        },
    )


def with_overrides(variant: mt5.Variant, **inputs: str) -> mt5.Variant:
    return mt5.Variant(
        name=variant.name,
        label=variant.label,
        run_id=variant.run_id,
        tester_inputs={**variant.tester_inputs, **inputs},
    )


PRIMARY_VARIANTS = [
    # R1 / UPTREND: long-only M5 continuation and pullback structures.
    candidate("r1_break_run_long", "R1 M5 break-and-run long", 1, 1, 0),
    candidate("r1_ema_pullback_long", "R1 M5 EMA pullback long", 1, 1, 1),
    candidate("r1_compression_break_long", "R1 M5 compression expansion long", 1, 1, 2),
    candidate("r1_m5_ema_trend_long", "R1 M5 EMA trend continuation long", 1, 1, 5),
    # R2 / DOWNTREND: short-only M5 continuation and retest structures.
    candidate("r2_break_run_short", "R2 M5 break-and-run short", 2, 2, 0),
    candidate("r2_ema_pullback_short", "R2 M5 EMA pullback short", 2, 2, 1),
    candidate("r2_m5_ema_trend_short", "R2 M5 EMA trend continuation short", 2, 2, 5),
    candidate("r2_impulse_retest_short", "R2 M5 downside impulse/retest short", 2, 2, 19),
    # R3 / COMPRESSION: M5 release or failed-release structures, both directions.
    candidate("r3_compression_break", "R3 M5 compression expansion", 6, 0, 2),
    candidate("r3_sweep_reclaim", "R3 M5 sweep/reclaim", 6, 0, 3),
    candidate("r3_opening_range_reversal", "R3 M5 opening-range reversal", 6, 0, 6),
    candidate("r3_prior_day_reclaim", "R3 M5 prior-day level reaction", 6, 0, 13),
    # R4 / CHOP: M5 mean-reversion structures, both directions.
    candidate("r4_sweep_reclaim", "R4 M5 sweep/reclaim", 4, 0, 3),
    candidate("r4_opening_range_reversal", "R4 M5 opening-range reversal", 4, 0, 6),
    candidate("r4_daily_extreme_reclaim", "R4 M5 daily-extreme reclaim", 4, 0, 11),
    candidate("r4_prior_day_reclaim", "R4 M5 prior-day level reaction", 4, 0, 13),
]

# Phase two was frozen only after phase one showed that R1, R3, and R4 had no
# survivor.  These are new event families; none changes a threshold or exit of a
# phase-one candidate.  R2 is deliberately absent because it already has screen
# survivors awaiting confirmation.
SECONDARY_VARIANTS = [
    candidate(
        "r1_h1_pullback_m5_confirm",
        "R1 H1 trend pullback with M5 confirmation",
        1,
        1,
        20,
        InpR1PullbackConfirmTimeframe="5",
    ),
    candidate("r1_opening_range_cont_long", "R1 M5 opening-range continuation long", 1, 1, 4),
    candidate(
        "r1_prior_day_break_long",
        "R1 M5 prior-day breakout continuation long",
        1,
        1,
        13,
        InpPriorDayLevelMode="0",
    ),
    candidate("r1_sweep_reclaim_long", "R1 M5 downside sweep/reclaim long", 1, 1, 3),
    candidate("r3_break_run", "R3 M5 break-and-run release", 6, 0, 0),
    candidate("r3_ema_pullback", "R3 M5 EMA reaction", 6, 0, 1),
    candidate("r3_opening_range_cont", "R3 M5 opening-range release", 6, 0, 4),
    candidate("r3_m5_ema_trend", "R3 M5 EMA trend release", 6, 0, 5),
    candidate("r4_bear_sweep_reclaim", "R4 M5 bearish resistance sweep/reclaim", 4, 2, 16),
    candidate("r4_bear_lower_high", "R4 M5 bearish lower-high rejection", 4, 2, 17),
    candidate("r4_bear_breakdown_retest", "R4 M5 bearish failed-support retest", 4, 2, 15),
    candidate("r4_local_compression_release", "R4 M5 local compression release", 4, 0, 2),
]

# Phase three was frozen before execution.  It does not tune any threshold from
# the first two regime campaigns.  Instead it applies exact profiles that were
# already selected and reported by the independent V4/V12/V13 M5 studies, then
# adds only the strict fail-closed regime owner.
TERTIARY_VARIANTS = [
    profile_candidate(
        "r1_v4_break_run_long",
        "R1 pre-existing V4 break-and-run long",
        1,
        "freq_h1_h4_long_rr0p7_v4_combo_rank1",
    ),
    profile_candidate(
        "r1_v13_ema_long",
        "R1 pre-existing V13 EMA-trend long",
        1,
        "v13_ema_trend_h1h4_long_rr0p6_no_morning",
    ),
    profile_candidate(
        "r2_v13_ema_short",
        "R2 pre-existing V13 EMA-trend short core",
        2,
        "v13_ema_trend_h1h4_short_rr0p6_core",
    ),
    profile_candidate(
        "r2_v13_feature_loss_short",
        "R2 pre-existing V13 feature-loss short profile",
        2,
        "v13_feature_loss_short_extreme_rr0p6",
    ),
    profile_candidate(
        "r3_v13_ema_both",
        "R3 pre-existing V13 EMA-trend profile",
        6,
        "v13_ema_trend_h1h4_both_rr0p7_no_weak_short",
    ),
    profile_candidate(
        "r3_v12_ema_both",
        "R3 pre-existing V12 EMA-trend profile",
        6,
        "v12_ema_trend_h1h4_both_rr0p6_block_bad_hours",
    ),
    profile_candidate(
        "r4_v13_ema_both",
        "R4 pre-existing V13 EMA-trend profile",
        4,
        "v13_ema_trend_h1h4_both_rr0p7_no_weak_short",
    ),
    profile_candidate(
        "r4_v12_ema_both",
        "R4 pre-existing V12 EMA-trend profile",
        4,
        "v12_ema_trend_h1h4_both_rr0p6_block_bad_hours",
    ),
]

# The exact-profile stack produced zero trades in every regime because two
# independent owners (the legacy H1/H4 filter and Router V1) had to agree.
# This recovery set was frozen before execution and changes only ownership:
# Router V1 replaces the legacy HTF filters; every M5 signal/exit/hour setting
# remains copied from the pre-existing source profile.
ROUTER_SUBSTITUTED_VARIANTS = [
    router_substituted_profile_candidate(
        "r1_router_v4_break_run_long",
        "R1 V4 M5 profile with Router V1 as sole regime owner",
        1,
        "freq_h1_h4_long_rr0p7_v4_combo_rank1",
    ),
    router_substituted_profile_candidate(
        "r1_router_v13_ema_long",
        "R1 V13 M5 profile with Router V1 as sole regime owner",
        1,
        "v13_ema_trend_h1h4_long_rr0p6_no_morning",
    ),
    router_substituted_profile_candidate(
        "r2_router_v13_ema_short",
        "R2 V13 short M5 profile with Router V1 as sole regime owner",
        2,
        "v13_ema_trend_h1h4_short_rr0p6_core",
    ),
    router_substituted_profile_candidate(
        "r2_router_v13_feature_loss_short",
        "R2 V13 feature-loss M5 profile with Router V1 as sole regime owner",
        2,
        "v13_feature_loss_short_extreme_rr0p6",
    ),
    router_substituted_profile_candidate(
        "r3_router_v13_ema_both",
        "R3 V13 M5 profile with Router V1 as sole regime owner",
        6,
        "v13_ema_trend_h1h4_both_rr0p7_no_weak_short",
    ),
    router_substituted_profile_candidate(
        "r3_router_v12_ema_both",
        "R3 V12 M5 profile with Router V1 as sole regime owner",
        6,
        "v12_ema_trend_h1h4_both_rr0p6_block_bad_hours",
    ),
    router_substituted_profile_candidate(
        "r4_router_v13_ema_both",
        "R4 V13 M5 profile with Router V1 as sole regime owner",
        4,
        "v13_ema_trend_h1h4_both_rr0p7_no_weak_short",
    ),
    router_substituted_profile_candidate(
        "r4_router_v12_ema_both",
        "R4 V12 M5 profile with Router V1 as sole regime owner",
        4,
        "v12_ema_trend_h1h4_both_rr0p6_block_bad_hours",
    ),
]

# Frozen after the router-substitution batch: R1 remained just below the PF
# gate while R3/R4 rejected EMA-trend continuation.  These candidates are
# pre-existing profiles with different mechanisms, again changing only the
# regime owner.  R2 is absent because it already has ten-year survivors.
MECHANISM_FOLLOWUP_VARIANTS = [
    router_substituted_profile_candidate(
        "r1_router_v3_break_run_long",
        "R1 higher-PF V3 break-and-run with Router V1 as sole owner",
        1,
        "freq_h1_h4_long_rr0p7_v3_block3_8",
    ),
    router_substituted_profile_candidate(
        "r1_router_v13_rr0p7_long",
        "R1 V13 0.7R M5 trend with Router V1 as sole owner",
        1,
        "v13_ema_trend_h1h4_both_rr0p7_no_weak_short",
    ),
    router_substituted_profile_candidate(
        "r3_router_v8_compression_long",
        "R3 true M5 compression expansion with Router V1 as sole owner",
        6,
        "v8_compress_h1_long_rr0p6",
    ),
    router_substituted_profile_candidate(
        "r3_router_v4_break_run_long",
        "R3 V4 M5 release with Router V1 as sole owner",
        6,
        "freq_h1_h4_long_rr0p7_v4_combo_rank1",
    ),
    router_substituted_profile_candidate(
        "r4_router_v9_sweep_long",
        "R4 M5 sweep/reclaim with Router V1 as sole owner",
        4,
        "v9_sweep_h1_long_rr0p6",
    ),
    router_substituted_profile_candidate(
        "r4_router_v9_sweep_v4mask_long",
        "R4 masked M5 sweep/reclaim with Router V1 as sole owner",
        4,
        "v9_sweep_h1h4_long_rr0p6_v4mask",
    ),
]

# Final bounded discovery set frozen before execution.  It addresses the exact
# observed failure mechanism in each missing regime without an hour/direction
# sweep: a two-point payoff bracket for R1, two loosened true-compression
# releases plus one masked break release for R3, and three explicit
# mean-reversion event families for R4.
BOUNDED_DISCOVERY_VARIANTS = [
    with_overrides(
        router_substituted_profile_candidate(
            "r1_discovery_v3_rr0p6_long",
            "R1 V3 break-and-run fixed 0.6R bracket",
            1,
            "freq_h1_h4_long_rr0p7_v3_block3_8",
        ),
        InpRiskReward="0.60",
    ),
    with_overrides(
        router_substituted_profile_candidate(
            "r1_discovery_v3_rr0p8_long",
            "R1 V3 break-and-run fixed 0.8R bracket",
            1,
            "freq_h1_h4_long_rr0p7_v3_block3_8",
        ),
        InpRiskReward="0.80",
    ),
    candidate(
        "r3_discovery_compress_release_a",
        "R3 M5 six-bar compression release",
        6,
        0,
        2,
        InpRiskReward="0.60",
        InpCompressionLookbackBars="6",
        InpCompressionMaxRangeAtr="1.60",
        InpCompressionBreakAtrMultiple="0.05",
        InpMaxEstimatedCostR="0.05",
        InpMaxTradesPerDay="24",
        InpCooldownMinutes="0",
    ),
    candidate(
        "r3_discovery_compress_release_b",
        "R3 M5 four-bar compression release",
        6,
        0,
        2,
        InpRiskReward="0.70",
        InpCompressionLookbackBars="4",
        InpCompressionMaxRangeAtr="2.00",
        InpCompressionBreakAtrMultiple="0.00",
        InpMaxEstimatedCostR="0.05",
        InpMaxTradesPerDay="24",
        InpCooldownMinutes="0",
    ),
    candidate(
        "r3_discovery_break_release_masked",
        "R3 masked M5 break release",
        6,
        0,
        0,
        InpRiskReward="0.70",
        InpMaxEstimatedCostR="0.05",
        InpBlockedEntryHoursCsv="2,9,10,11,12,13,17,19,21,23",
        InpMaxTradesPerDay="24",
        InpCooldownMinutes="0",
    ),
    candidate(
        "r4_discovery_opening_reversal",
        "R4 M5 opening-range mean reversion",
        4,
        0,
        6,
        InpRiskReward="0.70",
        InpMaxEstimatedCostR="0.05",
        InpBlockedEntryHoursCsv="0,2,4,9,10,11,12,16,19,20",
        InpMaxTradesPerDay="24",
        InpCooldownMinutes="0",
    ),
    candidate(
        "r4_discovery_prior_day_reclaim",
        "R4 M5 prior-day level reclaim",
        4,
        0,
        13,
        InpPriorDayLevelMode="1",
        InpRiskReward="0.70",
        InpMaxEstimatedCostR="0.05",
        InpBlockedEntryHoursCsv="0,2,4,9,10,11,12,16,19,20",
        InpMaxTradesPerDay="24",
        InpCooldownMinutes="0",
    ),
    candidate(
        "r4_discovery_daily_extreme_reclaim",
        "R4 M5 daily-extreme reclaim",
        4,
        0,
        11,
        InpRiskReward="0.70",
        InpMaxEstimatedCostR="0.05",
        InpBlockedEntryHoursCsv="0,2,4,9,10,11,12,16,19,20",
        InpMaxTradesPerDay="24",
        InpCooldownMinutes="0",
    ),
]

VARIANTS = (
    PRIMARY_VARIANTS
    + SECONDARY_VARIANTS
    + TERTIARY_VARIANTS
    + ROUTER_SUBSTITUTED_VARIANTS
    + MECHANISM_FOLLOWUP_VARIANTS
    + BOUNDED_DISCOVERY_VARIANTS
)

REGIME_BY_PREFIX = {
    "r1_": "UPTREND",
    "r2_": "DOWNTREND",
    "r3_": "COMPRESSION",
    "r4_": "CHOP",
}

SCREEN_GATES = {
    "minimum_trades": 100,
    "minimum_profit_factor": 1.20,
    "minimum_win_rate_pct": 35.0,
    "maximum_equity_drawdown_pct": 20.0,
    "require_positive_net": True,
}


def float_prefix(value: Any) -> float:
    text = str(value or "0").replace(" ", "")
    token = text.split("%", 1)[0].split("(", 1)[0].strip()
    try:
        return float(token)
    except ValueError:
        return 0.0


def percent_value(value: Any) -> float:
    return float_prefix(str(value).replace("%", ""))


def regime_for(name: str) -> str:
    for prefix, regime in REGIME_BY_PREFIX.items():
        if name.startswith(prefix):
            return regime
    raise ValueError(f"Unknown candidate prefix: {name}")


def evaluate(result: dict[str, Any]) -> dict[str, Any]:
    overall = result["summary"]["overall"]
    metrics = result.get("mt5_report_metrics", {})
    equity_dd_pct = float_prefix(metrics.get("Equity Drawdown Relative", "0"))
    checks = {
        "trades": overall["trades"] >= SCREEN_GATES["minimum_trades"],
        "profit_factor": (overall["profit_factor"] or 0.0) >= SCREEN_GATES["minimum_profit_factor"],
        "win_rate": overall["win_rate_pct"] >= SCREEN_GATES["minimum_win_rate_pct"],
        "equity_drawdown": equity_dd_pct <= SCREEN_GATES["maximum_equity_drawdown_pct"],
        "positive_net": overall["pnl_aed"] > 0.0,
        "history_quality": percent_value(metrics.get("History Quality", "0")) >= 98.0,
    }
    return {
        "name": result["name"],
        "regime": regime_for(result["name"]),
        "trades": overall["trades"],
        "win_rate_pct": overall["win_rate_pct"],
        "net_usd": overall["pnl_aed"],
        "profit_factor": overall["profit_factor"],
        "equity_drawdown_pct": equity_dd_pct,
        "checks": checks,
        "screen_pass": all(checks.values()),
    }


def select_by_regime(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selections: dict[str, Any] = {}
    for regime in REGIME_BY_PREFIX.values():
        candidates = [row for row in rows if row["regime"] == regime]
        survivors = [row for row in candidates if row["screen_pass"]]
        ranked = sorted(
            survivors or candidates,
            key=lambda row: (
                row["screen_pass"],
                row["profit_factor"] or 0.0,
                row["net_usd"],
                -row["equity_drawdown_pct"],
            ),
            reverse=True,
        )
        selections[regime] = {
            "status": "SCREEN_SURVIVOR" if survivors else "NO_SCREEN_SURVIVOR",
            "selected": ranked[0] if ranked else None,
            "survivor_count": len(survivors),
        }
    selections["SHOCK"] = {
        "status": "CAPITAL_PROTECTION_NO_TRADE",
        "selected": None,
        "survivor_count": 0,
    }
    return selections


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen XAU M5 per-regime specialist screen.")
    parser.add_argument("--from-date", default="2021.07.01")
    parser.add_argument("--to-date", default="2026.07.01")
    parser.add_argument("--tag", default="REGIME_SCREEN_5Y_20260713")
    parser.add_argument("--backtest-root", type=Path, default=mt5.DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=mt5.DEFAULT_METAEDITOR)
    parser.add_argument("--variant-timeout-seconds", type=int, default=600)
    parser.add_argument("--variants", default="")
    args = parser.parse_args()

    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Historical execution is not authorized.")

    selected = {item.strip() for item in args.variants.split(",") if item.strip()} or None
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    report_json = OUTPUT_ROOT / f"{args.tag}.json"
    report_md = OUTPUT_ROOT / f"{args.tag}.md"

    original_variants = mt5.VARIANTS
    try:
        mt5.VARIANTS = VARIANTS
        payload = mt5.run_variants(
            backtest_root=args.backtest_root,
            metaeditor=args.metaeditor,
            output_dir=OUTPUT_ROOT / "mt5_runs",
            from_date=args.from_date,
            to_date=args.to_date,
            tag=args.tag,
            report_md=OUTPUT_ROOT / f"{args.tag}_MT5.md",
            report_json=OUTPUT_ROOT / f"{args.tag}_MT5.json",
            variant_names=selected,
            variant_timeout_seconds=args.variant_timeout_seconds,
            deposit="1000",
            currency="USD",
        )
    finally:
        mt5.VARIANTS = original_variants

    rows = [evaluate(result) for result in payload["variants"]]
    verdict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "M5_REGIME_SCREEN_COMPLETE",
        "scope": payload["scope"],
        "frozen_gates": SCREEN_GATES,
        "rows": rows,
        "selection_by_regime": select_by_regime(rows),
        "important_boundary": (
            "A five-year screen survivor is a candidate for untouched ten-year confirmation, "
            "not a demo or live authorization."
        ),
    }
    report_json.write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    lines = [
        "# A1 XAU M5 Per-Regime Specialist Screen",
        "",
        f"Generated: `{verdict['generated_at_utc']}`",
        "",
        "| Regime | Candidate | Trades | Win rate | Net USD | PF | Equity DD | Pass |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['regime']} | `{row['name']}` | {row['trades']} | "
            f"{row['win_rate_pct']:.2f}% | {row['net_usd']:.2f} | "
            f"{row['profit_factor']} | {row['equity_drawdown_pct']:.2f}% | "
            f"{'PASS' if row['screen_pass'] else 'FAIL'} |"
        )
    lines.extend(["", "## Mechanical selections", ""])
    for regime, selection in verdict["selection_by_regime"].items():
        name = selection["selected"]["name"] if selection["selected"] else "none"
        lines.append(f"- {regime}: `{selection['status']}`; `{name}`")
    lines.extend(["", verdict["important_boundary"], ""])
    report_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(verdict["selection_by_regime"], indent=2))
    print(report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
