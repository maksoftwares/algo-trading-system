# Worthy EA Candidate Inventory

Generated: 2026-06-07

## Verdict

There are worthy Phase 0 research candidates, but none are execution-ready and none solve the independent lower-cost replacement problem yet.

The only candidates with enough evidence to call worthy are in the breakout/retest family. That family is currently `COST_SUSPENDED_CANONICAL` for formal Phase 2 execution after measured-cost revalidation failed with 0/9 passing cells, overall PF 0.4125, and net expectancy -0.6150R. These candidates may be worth preserving for future research, dry-run observation, or owner review, but they do not authorize live execution, paper execution, `OrderSend`, `CTrade`, or position management.

## Approved Future Expert Candidates

| Candidate | Status | Why it is worthy | Boundary |
| --- | --- | --- | --- |
| `swing_breakout_retest_v0` | `APPROVED_FUTURE_EXPERT_CANDIDATE` | Passed 9-cell matrix, deciles, multisymbol, intrabar ambiguity, and Gate 9 manual adversarial review. Gate 9 reviewed 120/120 sampled losses with 0 logic gaps. | Same-family with `breakout_retest`; not independent diversification and not execution-ready under current measured-cost evidence. |
| `symbol_normalized_round_retest_v0` | `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY` | Passed matrix, deciles, multisymbol transfer, intrabar ambiguity, and Gate 9. Gate 9 reviewed 120/120 sampled losses with 0 logic gaps. Multisymbol transfer: EURUSD PF 1.2976 on 12,260 trades; USDJPY PF 1.5594 on 14,380 trades. | Same-family level/retest candidate. The older research-result memo still says provisional, but the current backlog and adversarial score show Gate 9 PASS. |
| `quarter_round_retest_v0` | `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY` | Passed matrix, deciles, multisymbol transfer, intrabar ambiguity, and Gate 9. Gate 9 reviewed 119/119 sampled losses with 0 logic gaps. EURUSD PF 1.3548 on 23,949 trades; USDJPY PF 1.4607 on 27,145 trades. | Same-family level/retest candidate. Gate 9 was a Codex packet-level mechanical review, not owner chart-by-chart attestation. Not independent diversification and not execution-ready under current measured-cost evidence. |
| `session_extreme_retest_v0` | `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY` | Passed matrix, deciles, multisymbol check, intrabar ambiguity, and Gate 9. Gate 9 reviewed 120/120 sampled losses with 0 logic gaps. XAU matrix PF range 1.328 to 1.596 over 23,727 total matrix trades. | Same-family level/retest candidate. Gate 9 was a Codex packet-level mechanical review, not owner chart-by-chart attestation. Not independent diversification and not execution-ready under current measured-cost evidence. |
| `round_number_retest_v0` | `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY_XAU_SPECIFIC` | Passed XAU matrix, deciles, intrabar ambiguity, XAU-specific multisymbol defense, and Gate 9. Gate 9 reviewed 120/120 sampled losses with 0 logic gaps. Matrix PF passed 9/9 with 3,837 to 6,462 trades per cell. | Same-family level/retest candidate and XAU-specific because EURUSD produced 0 trades. Gate 9 was a Codex packet-level mechanical review, not owner chart-by-chart attestation. Not independent diversification and not execution-ready under current measured-cost evidence. |

## Strong Provisional Candidates

These are worthy enough to keep on the shortlist, but they are not approved until Gate 9 manual adversarial review is completed and scored PASS.

None.

## BTC Branch

BTC has not produced a worthy EA yet.

The strongest BTC clue so far was `h4_btc_risk_pressure_gold_reversal_v0`: it reached 9/9 PF cells above 1.30 including p95 costs, but only produced 9 to 14 trades per cell and reached 8 max zero-trade months. That is useful signal evidence, not an approval-worthy EA.

Subsequent fresh BTC attempts failed the same Phase 0 path:

| Candidate | Result |
| --- | --- |
| `h4_btc_risk_pressure_gold_reversal_v1` | Rejected. Broadened v0 to 37-48 trades per cell, but 0/9 PF cells reached 1.30 and Dukascopy was negative across costs. |
| `h4_btc_risk_pressure_gold_reversal_v2` | Rejected. Produced 13-21 trades per cell, 3/9 PF cells, 0/9 trade-count cells, and materially negative Dukascopy cells. |
| `h1_btc_risk_pressure_gold_reversal_v0` | Rejected. Produced 10-26 trades per cell, 0/9 PF cells, 0/9 trade-count cells, and negative Capital.com/Pepperstone results. |
| `h4_btc_failed_trend_gold_reversal_v0` | Rejected. BTC 20-day trend failure plus H4 XAU rejection produced a Dukascopy-only PF pocket, but only 4-10 trades per cell, 0/9 trade-count cells, and negative Capital.com/Pepperstone results. |
| `h4_btc_gvz_dual_vol_reversal_v0` | Rejected sparse PF lead. Combined BTC volatility stress plus GVZ/VIX gold-volatility premium produced 6/9 PF cells above 1.30 and 8/9 positive cells, but only 10-21 trades per cell, 0/9 trade-count cells, max zero-trade months 11, and Dukascopy failed threshold. |
| `h1_btc_gvz_dual_vol_reversal_v0` | Rejected sparse lead lost. H1 execution retest of BTC volatility stress plus GVZ/VIX gold-volatility premium produced only 11-25 trades per cell, 3/9 PF cells, 0/9 trade-count cells, and negative Pepperstone/Dukascopy results. |
| `h4_btc_crash_gold_safe_haven_continuation_v0` | Rejected. Produced 5-7 trades per cell, 3/9 PF cells, 0/9 trade-count cells, and negative Capital.com/Dukascopy results. |
| `h4_btc_rally_gold_risk_on_continuation_v0` | Rejected. Produced 8-17 trades per cell, 0/9 PF cells, 0/9 trade-count cells, and all broker/cost cells were negative. |
| `h4_btc_risk_pressure_gold_reversal_v3` | Rejected. Produced 6-15 trades per cell, 3/9 PF cells, 0/9 trade-count cells, and negative Capital.com/Dukascopy results. |
| `h1_btc_risk_pressure_gold_followthrough_v1` | Rejected. Produced 32-51 trades per cell, 0/9 PF cells, only 3/9 trade-count cells, and Pepperstone/Dukascopy were negative. |
| `h1_btc_risk_pressure_gold_followthrough_v2` | Rejected. Produced 105-128 trades per cell and passed activity, but 0/9 PF cells reached 1.30; Capital.com was positive below threshold while Pepperstone/Dukascopy were negative. |
| `h4_btc_volatility_regime_gold_breakout_v0` | Rejected. BTC volatility-regime, not return-pressure, produced 40-56 trades per cell and a strong Pepperstone PF pocket, but only 3/9 PF cells passed; Capital.com was flat-negative and Dukascopy negative. |
| `h4_btc_volatility_regime_gold_pullback_v0` | Rejected. BTC volatility-regime H4 XAU pullback-continuation produced small Capital.com/Pepperstone positive pockets, but only 9-17 trades per cell, 0/9 PF cells above 1.30, 0/9 trade-count cells, and negative Dukascopy results. |
| `h4_btc_volatility_regime_gold_reversal_v0` | Rejected. High BTC volatility with H4 XAU exhaustion reversal produced 35-43 trades per cell and mild Capital.com positives, but 0/9 PF cells reached 1.30 and Pepperstone/Dukascopy were negative. |
| `h4_btc_volatility_compression_gold_expansion_v0` | Rejected. Opposite BTC low-volatility compression context with H4 XAU expansion produced 27-49 trades per cell, but 0/9 PF cells, 0/9 positive-PnL cells, and all broker/cost windows were negative. |
| `h4_btc_volume_climax_gold_reversal_v0` | Rejected. BTC participation-intensity/volume-climax lane produced only 10-13 trades per cell, 0/9 PF cells above 1.30, and all broker/cost cells were negative. |
| `h4_btc_whipsaw_gold_reversal_v0` | Rejected. BTC path-inefficient volatility regime with H4 XAU rejection produced 29-56 trades per cell, but every broker/cost cell was negative, 0/9 PF cells reached 1.0, and max zero-trade months reached 8. |
| `h4_weekly_level_rejection_v0` | Rejected. Produced 55-76 trades per cell, but only 3/9 PF cells; all PF-threshold cells were Pepperstone-only and Capital.com/Dukascopy were negative. |

## Latest Independent Macro Attempt

| Candidate | Result |
| --- | --- |
| `d1_macro_liquidity_regime_v0` | Rejected. Official-FRED WALCL plus broad-dollar liquidity regime produced 25-44 trades per cell, 0/9 PF cells, only 3/9 trade-count cells, max zero-trade months 26, and no broker/cost cell reached PF 1.0. |
| `h4_gld_etf_flow_reversal_v3` | Rejected. GLD ETF flow-stress timing expansion produced 42-57 trades per cell and passed activity, but only 3/9 PF cells reached 1.30, all Dukascopy-only; Capital.com was negative and max zero-trade months reached 5. |
| `h4_gld_gvz_vol_flow_reversal_v0` | Rejected sparse one-broker lead. Combined GLD ETF flow stress plus GVZ/VIX gold-volatility premium produced 3/9 PF cells above 1.30, all Pepperstone, but only 12-26 trades per cell, 0/9 trade-count cells, and Capital.com/Dukascopy were not positive. |
| `h4_gld_btc_vol_flow_reversal_v0` | Rejected sparse PF lead. Combined GLD flow-stress plus BTC volatility regime produced 6/9 PF cells above 1.30 across Pepperstone/Dukascopy, but only 6-13 trades per cell, 0/9 trade-count cells, max zero-trade months 11, and Capital.com was materially negative. |
| `h1_gld_btc_vol_flow_reversal_v0` | Rejected. H1 execution retest of the same GLD-flow plus BTC-volatility clue produced only 6-9 trades per cell, 0/9 PF cells above 1.30, 0/9 trade-count cells, max zero-trade months 15, and negative Capital.com/Dukascopy results. |
| `h4_macro_momentum_confluence_v0` | Rejected sparse PF lead. Macro-composite plus D1/H4 momentum confluence reached 9/9 PF cells above 1.30 and all cells profitable, but only 5-30 trades per cell, 0/9 trade-count cells, max zero-trade months 17, and concentration failure. |
| `h4_macro_momentum_confluence_v1` | Rejected. Activity broadening solved trade count with 48-89 trades per cell, but diluted PF to 0/9 cells above 1.30; Capital.com and Pepperstone were negative across costs. |
| `h4_macro_momentum_confluence_v2` | Rejected. Strict macro with broader H4 execution improved activity to 20-55 trades per cell but reached only 1/9 PF cells above 1.30 and still failed trade-count/activity gates. |
| `h4_macro_pullback_reclaim_v0` | Rejected. Strict macro H4 pullback/reclaim without D1 confirmation produced 24-85 trades per cell and 4/9 PF cells above 1.30, with strong Capital.com but insufficient Pepperstone/Dukascopy persistence. |
| `h4_macro_pause_continuation_v0` | Rejected. Strict macro H4 pause/continuation without D1 confirmation produced 28-69 trades per cell, but 0/9 PF cells reached 1.30, only 3/9 cells met trade count, and Capital.com/Pepperstone were negative. |

## Practical Next Steps

1. If the goal is to preserve the best worthy candidates, the same-family shortlist is now fully Gate 9 scored; continue searching for independent lower-cost candidates.
2. If the goal is a BTC EA specifically, start a new versioned BTC hypothesis rather than tuning the rejected ones. The current clue is strict BTC stress plus H4 XAU rejection, but the problem to solve is activity without destroying cross-broker PF.
3. If the goal is an execution-eligible replacement, continue Phase 0R lower-cost independent research. The current worthy candidates are same-family and cost-suspended, so they do not solve the replacement requirement.

## Evidence Pointers

- Backlog: `docs/CANDIDATE_RESEARCH_BACKLOG.md`
- Swing Gate 9: `docs/SWING_BREAKOUT_RETEST_V0_GATE9_REVIEW.md`
- Symbol-normalized Gate 9 score: `outputs/adversarial_review/symbol_normalized_round_retest_v0_adversarial_score.md`
- Quarter-round Gate 9: `docs/QUARTER_ROUND_RETEST_V0_GATE9_REVIEW.md`
- Quarter-round status: `docs/QUARTER_ROUND_RETEST_V0_RESEARCH_STATUS.md`
- Session-extreme Gate 9: `docs/SESSION_EXTREME_RETEST_V0_GATE9_REVIEW.md`
- Session-extreme status: `docs/SESSION_EXTREME_RETEST_V0_RESEARCH_RESULT.md`
- Round-number Gate 9: `docs/ROUND_NUMBER_RETEST_V0_GATE9_REVIEW.md`
- Measured-cost decision: `outputs/reports/MEASURED_COST_REVALIDATION_DECISION.md`
