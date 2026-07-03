# Project Status Summary

Generated UTC: `2026-07-03T08:37:24.505884Z`
Artifact generation base commit: `0a9823b0e69dd54eac8dbccb213b1dedf063c79d`
Branch: `main`

This small file is the audit-friendly companion to the large `status.html` dashboard.

## Accounts

| Account | Login | Role | Round quarantine active | Touched by round quarantine |
| --- | ---: | --- | ---: | ---: |
| A1 | `1025742` | standard/noisy demo account | `true` | `true` |
| A2 | `1033030` | Tier-1 clean breakout account | `false` | `false` |
| A3 | `1033669` | repair / Tier-1 compatibility demo account | `false` | `false` |

## A1 Round-Family Quarantine

Status: `ROUND_FAMILY_QUARANTINE_APPLIED`
Scope: `A1 XAUUSD round-family only`
Keep active through forward week: `true`
Rollback required now: `false`

| Chart | Candidate | Dry run | Broker action | Status |
| --- | --- | ---: | ---: | --- |
| `chart09.chr` | `symbol_normalized_round_retest_v0` | `true` | `false` | `OWNER_APPROVED_ROUND_FAMILY_QUARANTINED` |
| `chart11.chr` | `round_number_retest_v0` | `true` | `false` | `OWNER_APPROVED_ROUND_FAMILY_QUARANTINED` |

## Protected Breakout Core

Source: `runtime_inventory`

| Chart | Candidate | Account | Magic | Session | Smart trend | Dry run | Broker action | Status |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| `A1 chart03.chr` | `breakout_retest` | `1025742` | `920101` | `0->23` | `enabled=true shadow=false D1_required=false D1=0.25 H1_required=true H1=0.15` | `false` | `true` | `BROKER_ACTION_ENABLED` |
| `A2 chart02.chr` | `breakout_retest` | `1033030` | `920101` | `0->23` | `enabled=true shadow=false D1_required=false D1=0.25 H1_required=true H1=0.15` | `false` | `true` | `BROKER_ACTION_ENABLED` |

## XAU 920101 Breakout-Retest Failure Forensic

Status: `OFFLINE_FORENSIC_NO_RUNTIME_CHANGE`
Finding: Entry quality remains weak; fast-stop losses and top-winner dependence are the main repair targets.

| Slice | Trades | WR | Net AED | PF | Top 3 Removed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `current_24h_h1_smart` | `272` | `37.5%` | `98.35` | `1.02` | `-564.57` |
| `server_16_19_h1_smart` | `39` | `43.59%` | `228.02` | `1.56` | `30.63` |
| `repair_24h_h1_faststop_min800` | `67` | `43.28%` | `563.45` | `1.37` | `-68.39` |
| `repair_24h_h1_faststop_min800_lock100_050` | `68` | `54.41%` | `633.04` | `1.49` | `1.2` |

Fast-exit warning: `hold_<=15m` in the current lane is `-1238.75 AED` at `25.2%` WR.
Forensic report: `xau-usd/xauusd-phase1/outputs/reports/XAU_920101_BREAKOUT_RETEST_PROFIT_PROTECTION_FORENSIC_2026_07_01.md`

## A1 Momentum Continuation Lane

This is a separate A1-only demo lane for M5 break-and-run moves. It is not part of the protected `920101` breakout-retest core.

| Field | Value |
| --- | --- |
| Status | `PASS_ATTACHED` |
| Account | `1025742 / Capital.ComMena-Demo` |
| EA | `A1XauM5MomentumContinuationExecutor` |
| Symbol | `XAUUSD` |
| Magic | `932200` |
| Lot | `0.01` |
| Run ID | `A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702` |
| Order comment | `A1_XAU_M5_MOM` |
| Broker action enabled for new lane | `true` |
| Existing 920101 chart edited | `false` |
| A2 touched | `false` |
| A3 touched | `false` |
| Startup rows seen | `4` |
| Signal rows seen | `4` |
| Order proof | `ORDER_OR_GUARD_ROW_PRESENT` |
| Evidence status | `SELECTED_ON_ALL_AVAILABLE_HISTORY_FORWARD_IS_FIRST_CLEAN_TEST` |
| Spec SHA256 | `70f64b6c6a2608659597563aa039279793ed690f4762d8248254463b388c4026` |
| Forward start broker time | `2026-07-02 04:46:42` |
| Expected 100-trade duration | `18-25 weeks` |
| Dedicated kill switch | `a1_xau_m5_momentum_rr2_kill_switch.txt` |
| Attribution report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_RR2_ATTRIBUTION_EXPORT_2026_07_02.md` |
| Shadow counterfactual report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_RR2_SHADOW_COUNTERFACTUAL_2026_07_02.md` |
| Attachment report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_ATTACHMENT_2026_07_02.md` |

### A1 Momentum Split-Entry BE-on-TP1 Forward Lane

This is the owner-approved A1-only experimental split-entry lane. It can place demo orders on A1 only, using a shared signal-claim guard so only the highest-priority component acts on an overlapping signal.

| Field | Value |
| --- | --- |
| Status | `PASS_ATTACHED` |
| Account | `1025742 / Capital.ComMena-Demo` |
| Symbol / timeframe | `XAUUSD / M5` |
| Shared magic | `932280` |
| Components attached | `3` |
| First order status | `PENDING_FIRST_VALID_SIGNAL` |
| Exposure note | `Owner accepted 2 x 0.01 split-entry exposure; typical failed signal -20 to -30 USD, worst tested about -36 USD.` |
| Boundary | `A1 demo only; no live trading, no real capital, no canonical Phase 2 approval.` |
| Frozen spec | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md` |
| Owner authorization | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_OWNER_AUTHORIZATION_2026_07_03.md` |
| Hash verification | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SPLIT_BE_HASH_VERIFICATION_2026_07_03.md` |

| Component | Run ID | Magic | Lot | Comment | Broker action | Report |
| --- | --- | ---: | ---: | --- | ---: | --- |
| `split_be_tp1_v6_max2` | `A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V6_MAX2_20260703` | `932280` | `0.01` | `A1_XAU_M5_MOM_SPLIT_BE_V6` | `true` | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V6_MAX2_ATTACHMENT_2026_07_03.md` |
| `split_be_tp1_weak_hours` | `A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_WEAK_HOURS_20260703` | `932280` | `0.01` | `A1_XAU_M5_MOM_SPLIT_BE_WH` | `true` | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_WEAK_HOURS_ATTACHMENT_2026_07_03.md` |
| `split_be_tp1_v13` | `A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V13_20260703` | `932280` | `0.01` | `A1_XAU_M5_MOM_SPLIT_BE_V13` | `true` | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V13_ATTACHMENT_2026_07_03.md` |

### A1 Momentum Frequency-First Replacement Candidate

This is the current candidate that better matches the project goal. It is not attached yet and should replace the sparse RR2 lane by default, not stack with it.

| Field | Value |
| --- | --- |
| Status | `READY_FOR_REVIEW_NOT_ATTACHED` |
| Candidate | `freq_h1_h4_long_rr0p7_v4_combo_rank1` |
| Replacement policy | `replace_sparse_rr2_by_default` |
| Currently attached business fit | `TOO_SPARSE_FOR_PRIMARY_GOAL` |
| Runtime touched by readiness work | `False` |
| Review required | `True` |
| Owner approval required | `True` |
| Run ID if approved | `A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702` |
| Direction | `LONG_ONLY` |
| Risk reward | `0.70` |
| Max cost R | `0.05` |
| Blocked hours | `2,9,10,11,12,13,17,19,21,23` |
| Max trades/day | `12` |
| Cooldown minutes | `5` |
| Readiness doc | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_DEMO_REPLACEMENT_READINESS_2026_07_02.md` |
| V6 diagnostic doc | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V6_DIAGNOSTIC_VERDICT_2026_07_02.md` |
| Frequency requirement verdict | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQUENCY_REQUIREMENT_VERDICT_2026_07_02.md` |
| Attach command after approval | `python xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py --variant freq_v4` |

### A1 Momentum Portfolio Combination Candidate

This diagnostic checks whether V4 can be paired with a V13 companion lane to satisfy the multiple-trades/day objective without collapsing edge quality.

| Field | Value |
| --- | --- |
| Status | `PORTFOLIO_DIAGNOSTIC_COMPLETE` |
| Candidate | `v4_plus_v13_leading_raw` |
| Decision | `REVIEW_CANDIDATE` |
| Trades | `2918` |
| Win rate | `63.23%` |
| Net PnL USD | `1905.0` |
| Profit factor | `1.29` |
| Active days | `692` |
| Trades / active day | `4.22` |
| Multi-trade days | `518` |
| Positive / negative months | `33 / 15` |
| Max closed DD USD | `132.63` |
| Recommendation | `review_before_demo; possible V4 primary plus V13 companion forward-test` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_V4_V13_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.md` |

### A1 Momentum Broad Portfolio Search

This broader offline search ranks exact-MT5 portfolio combinations and flags duplicate-like same-minute stacking.

| Field | Headline candidate | Best clean candidate |
| --- | --- | --- |
| Name | `rr_2p0_long_only_h1_h4_atr15_no0910 + v6_freq_v4_rr0p7_max2` | `v5_v4_move12 + freq_h1_h4_short_rr0p7_v1_core_1_5_15_19` |
| Decision | `REVIEW_CANDIDATE` | `REVIEW_CANDIDATE` |
| Trades | `2009` | `1317` |
| Win rate | `56.65%` | `64.54%` |
| Net USD | `2884.32` | `1139.94` |
| Profit factor | `1.49` | `1.43` |
| Active days | `435` | `535` |
| Trades / active day | `4.62` | `2.46` |
| Duplicate-like trade pct | `26.28%` | `0.0%` |
| Max closed DD USD | `131.65` | `59.38` |
| Recommendation | `review best clean no-duplicate candidate before any demo attachment` | `review best clean no-duplicate candidate before any demo attachment` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md` | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md` |
| Verdict | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md` | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md` |
| Clean forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` |

### A1 Momentum Deep Portfolio Search

This deeper offline search tests one-, two-, and three-lane portfolios after deterministic same-minute same-direction de-duplication. It is the closest current work to the owner requirement: enough intraday frequency without counting clone stacks as edge.

| Field | Headline deep candidate | Low-overlap frequency candidate |
| --- | --- | --- |
| Name | `freq_h1_h4_long_rr0p7_cost005_block_bad_hours + v6_freq_v4_rr0p7_max2 + freq_h1_h4_short_rr0p7_v1_night_early` | `v6_freq_v4_rr0p7_max2 + v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning + freq_h1_h4_short_rr0p7_v1_core_1_5_15_19` |
| Decision | `REVIEW_CANDIDATE` | `REVIEW_CANDIDATE` |
| Raw trades | `3027` | `3107` |
| Deduped trades | `2364` | `3058` |
| Win rate | `65.91%` | `65.73%` |
| Net USD | `2282.51` | `2156.21` |
| Profit factor | `1.47` | `1.34` |
| Active days | `565` | `718` |
| Trades / active day | `4.18` | `4.26` |
| Raw duplicate-like pct | `43.81%` | `3.15%` |
| Top25 removed USD | `1846.77` | `1835.2` |
| Max closed DD USD | `79.1` | `89.04` |
| Stress verdict | `REVIEW_FOR_FORWARD_TEST` | `REVIEW_FOR_FORWARD_TEST` |
| Recommendation | `review low-overlap frequency portfolio as the next primary candidate; sparse RR2 remains too sparse` | `review low-overlap frequency portfolio as the next primary candidate; sparse RR2 remains too sparse` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.md` | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.md` |
| Stress report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.md` | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.md` |
| Verdict | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md` | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` |

### A1 Momentum Robust Portfolio Search

This is the current strongest match for the owner requirement: active XAU M5 trading, de-duplicated evidence, win rate above 50%, and positive older/newer split windows.

| Field | Robust candidate |
| --- | --- |
| Name | `v6_freq_v4_rr0p7_max2 + v13_ema_trend_h1h4_long_rr0p6_no_morning + freq_h1_h4_short_rr0p7_v1_night_early` |
| Decision | `ROBUST_REVIEW_CANDIDATE` |
| Trades | `2503` |
| Win rate | `66.4%` |
| Net USD | `1933.57` |
| Profit factor | `1.37` |
| Active days | `603` |
| Trades / active day | `4.15` |
| Older net / PF | `441.29 / 1.24` |
| Newer net / PF | `1492.28 / 1.44` |
| Raw duplicate-like pct | `2.84%` |
| Top25 removed USD | `1611.51` |
| Max closed DD USD | `93.43` |
| Stress verdict | `REVIEW_FOR_FORWARD_TEST` |
| Walk-forward verdict | `REVIEW_FOR_FORWARD_TEST` |
| Weakest half-year | `2022-H2 / PF 1.07 / net 32.38` |
| Best repair | `v13_ema_trend_h1h4_long_rr0p6_no_morning@18` |
| Repair metrics | `2443 trades / WR 66.56% / PF 1.38 / net 1944.34` |
| Repair 2022-H2 | `PF 1.1 / net 46.68` |
| Repair walk-forward verdict | `REVIEW_FOR_FORWARD_TEST` |
| Repair weakest half-year | `2022-H2 / PF 1.1 / net 46.68` |
| Recommendation | `strongest current fit for active intraday frequency plus split-period robustness; review before any demo attachment` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.md` |
| Stress report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_STRESS_2026_07_02.md` |
| Walk-forward report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.md` |
| Repair report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.md` |
| Repair walk-forward report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_2026_07_02.md` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` |
| Repair forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_FORWARD_DRAFT_2026_07_02.md` |

### A1 Momentum Daily-Fit Portfolio Search

This is the newest diagnostic layer for the owner's actual operating target: multiple trades per active day, enough 3+ trade days, positive active-day rate, PF/net, and low duplicate-like overlap.

| Field | Daily-fit candidate |
| --- | --- |
| Status | `DAILY_FIT_PORTFOLIO_SEARCH_COMPLETE` |
| Decision | `DAILY_FIT_REVIEW_CANDIDATE` |
| Members | `freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1, v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning` |
| Trades | `2785` |
| Win rate | `65.35%` |
| Net USD | `1757.13` |
| Profit factor | `1.29` |
| Active days | `689` |
| Trades / active day | `4.04` |
| 3+ trade day pct | `55.59%` |
| Positive day pct | `53.85%` |
| Median day USD | `0.95` |
| Worst day USD | `-40.12` |
| Positive / negative months | `34 / 14` |
| Worst month USD | `-35.87` |
| Top100 removed USD | `672.6` |
| Older net / PF | `318.7 / 1.15` |
| Newer net / PF | `1438.43 / 1.37` |
| Raw duplicate-like pct | `4.08%` |
| Stress report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.md` |
| Repair status | `DAILY_FIT_REPAIR_DIAGNOSTIC_COMPLETE` |
| Best repair blocks | `v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@18, v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@22` |
| Repaired metrics | `2589 trades / WR 65.66% / PF 1.31 / net 1764.38` |
| Repaired active-day shape | `645 active days / 4.01 trades per active day / 55.04% 3+ trade days` |
| Repaired day/month stability | `53.02% positive days / 37 positive months / 11 negative months` |
| Repaired top100 removed USD | `681.97` |
| Repaired older net / PF | `376.5 / 1.19` |
| Recommendation | `best current candidate for the owner's daily-activity target; repair candidate improves PF/DD/month stability but needs review before demo attachment` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.md` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md` |
| Repair report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.md` |
| Repair forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_FORWARD_DRAFT_2026_07_02.md` |

### A1 Momentum Daily Guard Search

This is the lifecycle layer for the active daily-cadence candidate. It tests portfolio-wide trade caps and loss stops on exact MT5 trade CSVs without touching runtime.

| Field | Daily guard candidate |
| --- | --- |
| Status | `DAILY_GUARD_SEARCH_COMPLETE` |
| Decision | `DAILY_GUARD_REVIEW_CANDIDATE` |
| Base | `daily_fit_repair_no_v13_18_22` |
| Profit target USD | `None` |
| Daily loss stop USD | `-25.0` |
| Portfolio max trades/day | `6` |
| Max losses/day | `None` |
| Trades | `2130` |
| Retention | `82.27%` |
| Win rate | `65.59%` |
| Net USD | `1450.35` |
| Profit factor | `1.33` |
| Active days | `645` |
| Trades / active day | `3.3` |
| 3+ trade day pct | `55.04%` |
| Positive day pct | `55.35%` |
| Median day USD | `1.89` |
| Worst day USD | `-38.13` |
| Max closed DD USD | `90.82` |
| Top25 / Top100 removed USD | `1148.04 / 403.96` |
| Older net / PF | `295.57 / 1.18` |
| Newer net / PF | `1154.78 / 1.41` |
| Trade-cap days | `164` |
| Loss-stop days | `10` |
| Recommendation | `review the repaired daily-fit package with a shared portfolio guard: max 6 trades/day, -25 USD daily loss stop, no profit target; preserves 3+ trades/active-day cadence while improving positive-day rate and drawdown` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.md` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md` |

### A1 Momentum Pocket Portfolio Search

This diagnostic tested whether cleaner `variant + direction + hour` pockets could replace the active daily-cadence portfolio. Result: the cleanest pockets were too sparse for the owner requirement.

| Field | Pocket search |
| --- | --- |
| Status | `POCKET_PORTFOLIO_SEARCH_COMPLETE` |
| Best decision | `FAIL_SAMPLE` |
| Best pocket count | `10` |
| Best trades | `677` |
| Best win rate | `72.38%` |
| Best net USD | `1049.79` |
| Best profit factor | `1.92` |
| Best active days | `317` |
| Best trades / active day | `2.14` |
| Best 3+ trade day pct | `31.55%` |
| Non-sample-fail rows in top set | `0` |
| Recommendation | `do not pivot to sparse pocket pruning; the cleanest pockets failed the sample/frequency gate, so the daily-guard portfolio remains the current best frequent-trade candidate` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.csv` |

### A1 Momentum Daily-State Guard Search

This diagnostic tests whether causal day-state rules can improve the frequent daily-guard package without collapsing trade cadence. Result: no state rule crossed the daily-income bar; the best shape remains the simple daily guard.

| Field | Daily-state search |
| --- | --- |
| Status | `DAILY_STATE_GUARD_SEARCH_COMPLETE` |
| Searched rules | `3519` |
| Base trades / WR / PF | `2589 / 65.66% / 1.31` |
| Base active shape | `645 active days / 4.01 trades per active day / 53.02% positive days` |
| Best decision | `REVIEW_DAY_RATE` |
| Best rule | `none` |
| Best guard | `target=None; stop=-25.0; max_trades=6; max_losses=None; cooldown=0` |
| Best trades / retention | `2130 / 82.27%` |
| Best WR / PF / net | `65.59% / 1.33 / 1450.35` |
| Best active shape | `645 active days / 3.3 trades per active day / 55.04% 3+ trade days / 55.35% positive days` |
| Top100 removed USD | `403.96` |
| Review-count in top set | `63` |
| Recommendation | `daily-state lifecycle rules did not cross the daily-income bar; the best result remains the existing daily guard shape, so the next improvement probably needs a better entry or feature filter rather than more day-stop pruning` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.csv` |

### A1 Momentum Feature Loss-Cluster Analysis

This diagnostic joins the frequent daily-guard trades back to MT5 signal features. Unlike sparse pocket pruning, it looks for measurable setup conditions that can block bad trades while preserving active-day cadence.

| Field | Feature-loss result |
| --- | --- |
| Status | `FEATURE_LOSS_CLUSTER_ANALYSIS_COMPLETE` |
| Implementation | `CODED_DEFAULT_OFF_MT5_BACKTEST_VARIANT_READY` |
| Enriched trades | `2589 / 2589 (100.0%)` |
| Daily-guard baseline | `2130 trades / WR 65.59% / PF 1.33 / net 1450.35 / positive days 55.5%` |
| Review-candidate filters | `3` |
| Best decision | `FEATURE_FILTER_REVIEW_CANDIDATE` |
| Best block rule | `SHORT close_to_recent_extreme >= -0.75` |
| Raw blocked trades | `248` |
| Guarded result | `1882 trades / WR 66.15% / PF 1.36 / net 1427.47` |
| Active-day shape | `560 active days / 3.36 trades per active day / 55.54% 3+ trade days / 57.5% positive days` |
| Positive-day delta | `2.0 percentage points` |
| Top100 removed USD | `385.98` |
| Recommendation | `the top single-feature filter is now coded default-off in A1XauM5MomentumContinuationExecutor and exposed as an MT5 tester variant: block SHORT entries where close_to_recent_extreme >= -0.75, then replay the daily guard; offline analysis preserved 3+ trades/active-day cadence and lifted positive active days to about 57.5%. Next required proof is an exact MT5 real-tick backtest before any demo attachment.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_CLUSTERS_2026_07_02.md` |
| Filter CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_FILTERS_2026_07_02.csv` |
| Bin CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_BINS_2026_07_02.csv` |

### A1 Momentum Feature-Loss Portfolio Verdict

This uses exact MT5 trade CSVs from the new default-off feature-loss EA variant and checks the portfolio-shaped goal: enough trades per active day, better win rate/PF, and better active-day positivity.

| Field | Portfolio result |
| --- | --- |
| Status | `FEATURE_LOSS_PORTFOLIO_VERDICT_COMPLETE` |
| Best portfolio | `feature_daily_guard_long_plus_feature_v13_band_m2p51_m0p75` |
| Decision | `REVIEW_READY_NOT_PROMOTED` |
| Members | `freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1, v13_feature_loss_short_extreme_band_m2p51_rr0p6` |
| Result | `1948 trades / WR 66.27% / PF 1.35 / net 1428.77` |
| Active-day shape | `594 active days / 3.28 trades per active day / 53.54% 3+ trade days / 58.59% positive days` |
| Month stability | `39 positive / 9 negative months` |
| Robustness | `top100 removed 389.77 / DD 92.68` |
| Recommendation | `feature-filtered V13 plus the existing weak-hour long lane is the best current frequency-preserving repair shape from exact MT5 CSV evidence: it improves WR/PF and positive-day rate versus the old V13 daily-guard portfolio while keeping more than 3 trades per active day. It remains review-ready, not promoted.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_PORTFOLIO_VERDICT_2026_07_02.md` |

### A1 Momentum Feature-Loss Daily Guard Optimizer

This keeps the entry family fixed and searches daily lifecycle controls around the feature-loss portfolio. The goal is not sparse PF; it is a frequent intraday engine with better day-to-day reliability.

| Field | Optimizer result |
| --- | --- |
| Status | `FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_COMPLETE` |
| Searched rows | `13230` |
| Decision | `FREQUENCY_FIRST_REVIEW_CANDIDATE` |
| Threshold | `band_m2p51_m0p75` |
| Guard | `target=75.0, loss=None, max_trades=None, max_losses=None` |
| Result | `2476 trades / WR 66.32% / PF 1.34 / net 1813.89` |
| Active-day shape | `594 active days / 4.17 trades per active day / 53.54% 3+ trade days / 56.23% positive days` |
| Month stability | `40 positive / 8 negative months` |
| Robustness | `top100 removed 735.1 / DD 112.39` |
| Guard hits | `skipped 4 / loss-stop days 0 / trade-cap days 0` |
| Recommendation | `daily-control optimization around the feature-loss portfolio now selects the exact MT5-backed feature-band package as the best frequency-first candidate. The selected row must be read from the guard fields because the current best uses no shared daily portfolio guard. It remains review-ready, not promoted.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.csv` |

### A1 Momentum Feature-Pair Filter Search

This keeps the frequent feature-loss portfolio intact, then checks whether one more signal-feature block can improve daily reliability without shrinking the engine below the multiple-trades/day requirement.

| Field | Feature-pair result |
| --- | --- |
| Status | `FEATURE_PAIR_FILTER_SEARCH_COMPLETE` |
| Review candidates | `5` |
| Baseline | `1995 trades / WR 66.17% / PF 1.34 / 3.27 trades per active day / 57.28% positive days` |
| Best rule | `SHORT close_to_recent_extreme <= -2.51` |
| Decision | `FEATURE_PAIR_REVIEW_CANDIDATE` |
| Result | `1922 trades / WR 66.18% / PF 1.35 / net 1384.36` |
| Active-day shape | `588 active days / 3.27 trades per active day / 53.06% 3+ trade days / 58.5% positive days` |
| Month stability | `39 positive / 9 negative months` |
| Robustness | `top100 removed 354.56 / DD 91.4` |
| Recommendation | `feature-pair search found one more frequency-preserving repair candidate: block SHORT entries where close_to_recent_extreme <= -2.51 in addition to the existing >= -0.75 feature-loss block. It still keeps about 3.27 trades per active day and slightly improves positive-day rate. Next proof is exact MT5 real-tick testing of the new default-off band variant before any demo attachment.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.csv` |

### A1 Momentum Feature-Band Daily-Income Tradeoff

This compares the max-net feature-band package with the owner-target daily-income guard shape. The headline daily-income version uses a +50 USD package target and max 6 package trades/day without falling below the multiple-trades/day requirement.

| Field | Daily-income result |
| --- | --- |
| Status | `FEATURE_BAND_DAILY_INCOME_TRADEOFF_COMPLETE` |
| Eligible rows | `412` |
| Max-net reference | `2413.0 trades / WR 66.31% / PF 1.35 / net 1837.59 / 56.06% positive days` |
| Owner-target guard | `target=50.0, loss=None, max_trades=6.0, max_losses=None` |
| Result | `1959.0 trades / WR 66.31% / PF 1.35 / net 1431.19` |
| Active-day shape | `594.0 active days / 3.3 trades per active day / 53.54% 3+ trade days / 58.59% positive days` |
| Month stability | `39.0 positive / 9.0 negative months` |
| Robustness | `top100 removed 395.04 / DD 105.72` |
| Smoother +25 fallback | `1922.0 trades / 58.75% positive days / net 1361.02` |
| Recommendation | `daily-income tradeoff report separates the max-net feature-band package from the owner-target +50 USD / max 6 trades package, while also preserving the smoother +25 USD fallback for reviewer comparison. Review both before runtime selection because the daily-income versions improve positive active-day rate while giving up some total historical net.` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.csv` |

### A1 Momentum Feature-Band Daily-Income Readiness

| Field | Readiness |
| --- | --- |
| Status | `PASS_READY_FOR_REVIEW_NOT_ATTACHED` |
| Decision | `review_ready_not_attached` |
| Draft SHA256 | `188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b` |
| Planned magics | `feature_band_daily_income_long:932292, feature_band_daily_income_v13_both:932293` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02.md` |
| JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02.json` |

### A1 Momentum Feature-Band Daily-Reliability Candidate

This is the frequency-aligned candidate: it keeps the +50 USD / max 6 package shape, then adds a 15-minute package cooldown after a closed package loss. It is review-ready and not attached.

| Field | Daily-reliability result |
| --- | --- |
| Day-state status | `FEATURE_BAND_DAY_STATE_SEARCH_COMPLETE` |
| Best row | `owner_target_50_max6_cooldown_after_loss_15` |
| Decision | `DAILY_RELIABILITY_REVIEW_CANDIDATE_WITH_CADENCE_NOTE` |
| Result | `1894 trades / WR 68.74% / PF 1.49 / net 1817.95` |
| Active-day shape | `594 active days / 3.19 trades per active day / 51.01% 3+ trade days / 60.44% positive days` |
| Robustness | `top100 removed 784.2 / DD 79.45` |
| Readiness | `PASS_READY_FOR_REVIEW_NOT_ATTACHED` |
| Draft SHA256 | `693d070050666ccd066a834f71b666b3f865829e6a05c8942190be7da9c1729b` |
| Planned magics | `feature_band_daily_reliability_long:932294, feature_band_daily_reliability_v13_both:932295` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_FORWARD_DRAFT_2026_07_02.md` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_READINESS_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.csv` |

### A1 Momentum Feature-Band Residual-Reliability Candidate

This keeps the frequent daily-reliability package and adds two residual blocks: LONG server hour 18 and SHORT close-to-recent-extreme >= -0.92. It is review-ready and not attached.

| Field | Residual-reliability result |
| --- | --- |
| Search status | `FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_COMPLETE` |
| Best row | `combo__block_ANY_entry_hour_18__block_SHORT_close_to_recent_extreme_>=_-0.92` |
| Decision | `RELIABILITY_UPGRADE_REVIEW_CANDIDATE` |
| Baseline | `1894 trades / WR 68.74% / PF 1.49 / net 1817.95 / 60.44% positive days` |
| Candidate | `1822 trades / WR 69.1% / PF 1.52 / net 1837.34 / 62.59% positive days` |
| Active-day shape | `572 active days / 3.19 trades per active day / 50.87% 3+ trade days` |
| Robustness | `top100 removed 806.2 / DD 84.11` |
| Stress status | `RESIDUAL_RELIABILITY_STRESS_PASS_REVIEW_READY` |
| Stress cadence | `1822 trades / 3.19 trades per active day / 66.08% 2+ days / 50.87% 3+ days` |
| Stress robustness | `top100 removed 806.2 / top200 removed 36.55 / older-newer 520.77 and 1316.57` |
| Package optimizer | `RESIDUAL_PACKAGE_OPTIMIZER_COMPLETE` / searched `4540` rows |
| Best +50 target row | `1823 trades / WR 69.17% / PF 1.53 / net 1863.81 / 62.94% positive days / cooldown 10m` |
| Best net row | `2231 trades / WR 69.48% / PF 1.54 / net 2400.9 / 60.66% positive days` |
| Best positive-day row | `1824 trades / WR 69.19% / PF 1.53 / net 1875.96 / 62.94% positive days` |
| Preferred +50/10m readiness | `PASS_READY_FOR_REVIEW_NOT_ATTACHED` |
| Preferred +50/10m candidate | `1823 trades / WR 69.17% / PF 1.53 / net 1863.81 / 62.94% positive days / cooldown 10m` |
| Preferred +50/10m magics | `feature_band_residual_plus50_cooldown10_long:932298, feature_band_residual_plus50_cooldown10_v13_both:932299` |
| Preferred +50/10m draft SHA256 | `1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71` |
| High-net +75 readiness | `PASS_READY_FOR_REVIEW_NOT_ATTACHED` |
| High-net +75 candidate | `2231 trades / WR 69.48% / PF 1.54 / net 2400.9 / 3.9 trades per active day / 60.66% positive days` |
| High-net +75 magics | `feature_band_residual_plus75_high_net_long:932300, feature_band_residual_plus75_high_net_v13_both:932301` |
| High-net +75 draft SHA256 | `de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a` |
| Readiness | `PASS_READY_FOR_REVIEW_NOT_ATTACHED` |
| Draft SHA256 | `1b84b0f7195a79a7cd031118ef54c203a55442027288064bc817da07c2510edd` |
| Planned magics | `feature_band_residual_reliability_long:932296, feature_band_residual_reliability_v13_both:932297` |
| Forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_FORWARD_DRAFT_2026_07_02.md` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_READINESS_2026_07_02.md` |
| Stress report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.md` |
| Package optimizer report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.md` |
| Preferred +50/10m report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.md` |
| Preferred +50/10m forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md` |
| High-net +75 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.md` |
| High-net +75 forward draft | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.csv` |

### A1 Momentum Business-Goal Scoreboard

This table ranks candidates by the owner's stated objective: multiple trades per active day, win rate above 50%, positive PF/net, and enough robustness that the result is not just a sparse PF artifact.

| Field | Value |
| --- | --- |
| Status | `PASS_SCOREBOARD_READY` |
| Top candidate | `residual_plus75_high_net` |
| Top status | `OWNER_GOAL_PASS_REVIEW_READY` |
| Top metrics | `2231.0 trades / WR 69.48% / PF 1.54 / net 2400.9 USD / 3.9 trades per active day / 60.66% positive days` |
| Passing candidates | `7` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.csv` |

### A1 Momentum Calendar Cadence Audit

This audit prevents a subtle overclaim: active-day cadence is not the same as market-day cadence. The current candidates are frequent on days they fire, but quiet market days still exist.

| Field | Value |
| --- | --- |
| Status | `PASS_CADENCE_AUDIT_READY` |
| Window | `2022-07-01 -> 2026-06-25` |
| Weekday market days | `1040` |
| `residual_plus75_high_net` decision | `PASS_WITH_3PLUS_MARKET_DAY_CAVEAT` |
| `residual_plus75_high_net` cadence | `2231 trades / 2.15 trades per market day / 3.9 trades per active day / 28.08% 3+ market days` |
| `residual_plus50_10m` decision | `PASS_ACTIVE_DAY_BUT_MARKET_DAY_CADENCE_CAVEAT` |
| `residual_plus50_10m` cadence | `1823 trades / 1.75 trades per market day / 3.19 trades per active day / 28.08% 3+ market days` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.md` |
| JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.json` |

### A1 Momentum Market-Day Coverage Search

This search answers the owner's stricter objection: a candidate should not only look good on active days, it should produce multiple trades across the actual weekday market calendar. The result is still a review candidate, not a runtime approval.

| Field | Value |
| --- | --- |
| Status | `PASS_COVERAGE_SEARCH_READY` |
| Best candidate | `residual_plus75_high_net + freq_h1_h4_rr0p7_cost005_block_bad_hours + v6_freq_v4_rr0p7_max2` |
| Guard | `target75_cooldown10` |
| Decision | `REVIEW_CANDIDATE_OWNER_CADENCE` |
| Metrics | `3714 trades / WR 64.27% / PF 1.29 / net 2391.4 / 3.57 trades per market day / 5.02 trades per active day / 46.35% 3+ market days` |
| Robustness | `top100 removed 1142.41 / top200 removed 191.2` |
| Duplicate control | `2218 same-direction 5m duplicate drops before scoring` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.md` |
| CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.csv` |

### A1 Momentum Market-Day Coverage Stress

This stress report checks whether the higher-cadence market-day candidate survives beyond the headline search score. It is still review evidence, not runtime approval.

| Field | Value |
| --- | --- |
| Status | `PASS_CAUSAL_STRESS_REPORT_READY` |
| Decision | `REVISE_ROBUSTNESS` |
| Metrics | `3714 trades / WR 64.27% / PF 1.29 / net 2391.4 / 3.57 trades per market day / top300 removed -629.28` |
| Rolling windows | `250tr negative=339 pf_lt_1=317; 500tr negative=0 pf_lt_1=0` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.md` |
| Selected trades CSV | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03_TRADES.csv` |

### A1 Momentum Business-Goal Promotion Packet

This packet converts the scoreboard into an owner/reviewer decision: replace the sparse RR2 lane with the highest-ranked frequent package only after approval.

| Field | Value |
| --- | --- |
| Status | `PASS_PROMOTION_PACKET_REVIEW_READY` |
| Recommended primary | `residual_plus75_high_net` |
| Recommended fallback | `residual_plus50_10m` |
| Decision boundary | `review_owner_approval_required_before_demo_replacement` |
| Magics | `[932300, 932301]` |
| Package guard | `+75 USD target, no shared max-trade cap, 10-minute cooldown after any package loss.` |
| Forward pass rule | `Forward PF >= 1.25, WR >= 55%, net positive, trades/active day >= 3, trades/market day >= 2 where market is open, positive active days >= 55%, and no single day contributes more than 30% of net.` |
| Forward kill rule | `Stop or revert if rolling 80-trade PF < 0.95, drawdown exceeds 1.5x historical package DD scaled to lot/account, net negative after 150 trades, or any broker/runtime safety violation appears.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02.md` |
| Owner authorization | `xau-usd/xauusd-phase1/docs/A1_MOMENTUM_BUSINESS_GOAL_OWNER_AUTHORIZATION_2026_07_02.md` |
| Claude review prompt | `CLAUDE_REVIEW_PROMPT_A1_MOMENTUM_BUSINESS_GOAL_PROMOTION_2026_07_02.md` |

### A1 Momentum MT5 Backtest

| Field | Value |
| --- | --- |
| Status | `FAIL_STANDALONE_BACKTEST` |
| Period | `2026.06.01 -> 2026.06.30` |
| Net PnL AED | `-128.93` |
| Profit factor | `0.96` |
| Win rate | `41.38%` |
| Trades | `116` |
| Short net AED | `614.09` |
| Long net AED | `-743.02` |
| Decision | `baseline_failed; research short-only/stricter-long variants offline` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MT5_BACKTEST_JUNE2026.md` |

### A1 Momentum Variant MT5 Backtests

| Field | Value |
| --- | --- |
| Status | `DIAGNOSTIC_WINNER_NOT_PROMOTED` |
| Best diagnostic variant | `directional_session_htf_both` |
| Variant count | `7` |
| Note | `This is a backtest-window diagnostic. Do not promote without fresh forward evidence.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_Q2_2026.md` |
| Diagnosis | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_LONG_FAILURE_DIAGNOSIS_Q2_2026.md` |

### A1 Momentum Frequency-First Repair

This is a diagnostic repair screen for the original high-frequency goal; it is not the currently attached sparse RR2 lane.

| Field | Value |
| --- | --- |
| Status | `REVIEW_READY_FREQUENCY_FIRST_V4_CANDIDATE_NOT_PROMOTED` |
| Trades | `1132` |
| Win rate | `65.9%` |
| Net PnL USD | `1042.07` |
| Profit factor | `1.45` |
| Avg USD/trade | `0.9206` |
| Meets frequency goal | `True` |
| Meets win-rate goal | `True` |
| Ready for live | `False` |
| Next action | `Send to reviewer. If accepted, lock and owner-approve replacing the sparse RR2 lane with the V4 combo_rank1 lane at 0.01 lot.` |
| Report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md` |

## A3 Runtime Decision

Effective runtime authorization: `A3_ENTRY_LANES_PAUSED`
Runtime snapshot UTC: `2026-06-18T07:44:27.604179Z`
Open positions: `0`
Pending orders: `0`
Artifact integrity: `PASS`
Runtime performance: `FAIL`
Shadow candidate performance: `NOT_EVALUATED`
Pause artifact/runtime consistency: `PASS`
Emergency pause report: `PASS`
Test suite: `PASS` (425 passed, 0 failed)
Family mutex: `NOT_IMPLEMENTED`
Containment: `NOT_IMPLEMENTED`
Shadow hypothesis: `REGISTERED_LOCKED`
Reactivation gate: `BLOCKED`

| Runtime lane | Current state |
| --- | --- |
| `933200` plain | `PAUSED` |
| `933300` improved | `PAUSED` |
| `933400` Tier1 compat | `PAUSED` |
| Profit-lock manager | `DRY_RUN_DISARMED` |

## A3 Historical Authorization

Tier1 `933400` owner authorization: `OWNER_AUTHORIZED_DEMO_BROKER_ACTION`
Current permission of that authorization: `SUPERSEDED_BY_EMERGENCY_PAUSE`

| Metric | Value |
| --- | ---: |
| Closed trades | `23` |
| Wins | `1` |
| Losses | `22` |
| Net PnL AED | `-758.79` |
| Duplicate events | `5` |
| Profit-lock actions | `0` |

## Authorization Boundary

| Item | Value |
| --- | --- |
| Canonical Phase 2 PASS | `false` |
| Live trading authorized | `false` |
| Real capital authorized | `false` |
| A3 Tier-1 demo broker action | `OWNER_AUTHORIZED_DEMO_BROKER_ACTION` |
| A3 current runtime authorization | `A3_ENTRY_LANES_PAUSED` |

## Next Evidence Required

- SQ-01 hash-locked A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md
- SQ-02 hash-locked A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md
- SQ-03 offline Python discovery sweep with frequency-quality and loss-attribution table
- Green CI run tied to the exact source commit before any shadow-terminal attachment
- A3 remains paused; no broker action, profile arming, or runtime attach before evidence gates pass
- A1 XAU M5 momentum-continuation lane: capture first magic 932200 order-log row or guard-block row after a valid break-and-run signal
