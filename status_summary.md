# Project Status Summary

Generated UTC: `2026-07-06T08:49:50Z`
Artifact generation base commit: `0a9823b0e69dd54eac8dbccb213b1dedf063c79d`
Branch: `main`

This small file is the audit-friendly companion to the large `status.html` dashboard.

## Primary Gold Goal - Exact-Ledger Core Frontier

Status: `EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW`

Scope: primary objective is now the GOLD/XAUUSD owner goal: signal-level win rate `>=50%`, realized average winning trade / average losing trade `>=2.0`, and daily activity, with `90%+` active market days worth showing if the first two goals hold. Headline evidence must come from exact MT5 Strategy Tester runs in the isolated root `C:\MT5A1M5MomentumBacktest`.

Runtime boundary: restart restore reopened the recorded terminals, but the current headline evidence uses exact MT5 Strategy Tester only in `C:\MT5A1M5MomentumBacktest`. No live/demo runtime terminal, chart, preset, order, position, or broker-action state was changed by the replay work.

| Item | Result |
| --- | --- |
| Restart restore | `RESTORED_WITH_CAVEAT`: all 9 recorded MT5 executable paths are running again, plus Codex, ChatGPT, Claude, Chrome, TextInputHost, and Realtek Audio Console. `C:\MT5PortableGoldMission\terminal64.exe` reopened as account `121409 - Capital.ComMena-Live`; saved config has `[Experts] AllowLiveTrading=0`, so it is not treated as broker-action-enabled and must be manually verified before any runtime work. |
| Step 1 pre-registration | Frozen 27-cell split-entry shape grid: TP1 fraction `{1/3, 1/2, 2/3}` x runner target `{2.0R, 2.5R, 3.0R}` x BE timing `{on TP1 fill, at +1.0R, never}` across the three priority components `v6`, `weak`, and `v13`. |
| Exact MT5 completion | `27/27` cells complete, `81/81` component runs complete over `2022-07-01 -> 2026-06-30`. Step 1 is closed. |
| Step 1 verdict | `NO_SURVIVOR`: no split-shape cell reaches WR `>=50%`, W/L `>=2.0`, and daily activity. No demo/runtime promotion, no forward spec, no reviewer spend yet. |
| Best above-50% WR payoff | `f33_r30_be_1r`: WR `50.42%`, W/L `1.5626`, active days `61.07%`, PF `1.6039`, net `9608.53`, DD `519.79`. This is the best compromise but still far below W/L `2.0` and daily activity. |
| Best W/L overall | `f33_r30_be_never`: WR `38.77%`, W/L `2.4908`, active days `60.50%`, PF `1.5770`, net `11000.59`, DD `571.20`. Payoff clears target, but WR fails badly. |
| Best WR overall | `f67_r20_be_tp1`: WR `59.17%`, W/L `0.9606`, active days `62.42%`, PF `1.4152`, net `6759.79`, DD `369.32`. WR clears, but payoff is near 1:1. |
| Best two-thirds no-BE payoff | `f67_r30_be_never`: WR `47.16%`, W/L `1.6753`, active days `60.50%`, PF `1.4954`, net `7584.75`, DD `391.72`. It does not clear either the WR or W/L target. |
| Two-thirds r25 completed read | The `2/3` split at runner `2.5R` also fails the owner target: TP1-BE is WR `57.70%` / W/L `1.0288`, +1R BE is WR `53.85%` / W/L `1.2466`, and no-BE is WR `48.85%` / W/L `1.5443`. It does not improve the best above-`50%` payoff frontier. |
| Two-thirds r20 completed read | The `2/3` split at runner `2.0R` does not solve the owner target. TP1-BE keeps WR high but W/L is only `0.9606`; +1R BE is WR `55.25%` / W/L `1.1650`; no-BE is WR `51.23%` / W/L `1.3894`. The best above-`50%` payoff point remains `f33_r30_be_1r` at W/L `1.5626`. |
| Half-split completed-row read | The `1/2` row is dominated by the `1/3` row for the owner frontier. Above-`50%` WR cells top out at W/L `1.4764`; no-BE cells clear `2.0x` at 2.5R/3.0R but WR is only `42.07%`/`38.81%`. |
| Half-split r25 read | At runner `2.5R`, the `1/2` TP1 fraction still does not improve the frontier: TP1-BE and +1R BE trail the `1/3` equivalents on W/L/PF/net, while no-BE clears `2.0x` W/L but WR remains only `42.07%`. |
| Half-split r20 read | At runner `2.0R`, the `1/2` TP1 fraction does not improve the frontier: TP1-BE keeps WR but lowers W/L, +1R BE lowers W/L versus `1/3`, and no-BE remains below `2.0x` W/L while still below `50%` WR. |
| Completed-row read | The `1/3` row proves the expected frontier: BE-on-TP1 keeps WR high but W/L near `1.0-1.17`; +1R BE keeps WR just above `50%` up to 3.0R but W/L only reaches `1.5626`; no-BE clears `2.0x` W/L at 2.5R and 3.0R but WR drops to `41.99%` and `38.77%`. Daily activity stays around `60.5-62.4%`, so Step 3 portfolio work would still be required even if a later cell solves WR/WL. |
| Step 2 pre-registration | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_STEP2_INTERNAL_REGIME_GATE_PREREG_2026_07_05.md`: constrained causal gate over MT5 `WOULD_SIGNAL` fields only, fixed candidate cells, fixed feature list, fixed quantile thresholds, single gates plus limited two-gate combinations. |
| Step 2 internal regime gate | `NO_IN_SAMPLE_WR_WL_HIT`. Best near row: `f33_r30_be_1r` with `block_ANY_break_distance_atr_<=_0.8994`, `716` signals, WR `52.23%`, W/L `1.9792`, active days `36.53%`, PF `2.1965`, net `4789.17`. It still misses W/L `2.0`, cuts activity sharply, and is in-sample only. |
| Step 2 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_STEP2_INTERNAL_REGIME_GATE_2026_07_05.md` |
| Breakout-retest prereg | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_STEP4_BREAKOUT_RETEST_PROBE_PREREG_2026_07_05.md`: six fixed existing XAU 920101 breakout-retest variants over `2022-07-01 -> 2026-06-30`, exact MT5 Strategy Tester only. |
| Breakout-retest probe | `REJECT`: best PnL row was `repair_24h_h1_faststop_min800_lock100_050`, only `246` trades, WR `47.97%`, PF `1.03`, net `44.86`, and top-3-winner removal `-147.30`. Raw 24h and current H1 variants were negative. No row is near the owner WR/W-L/activity target. |
| Breakout-retest report | `xau-usd/xauusd-phase1/outputs/reports/XAU_920101_BREAKOUT_RETEST_VARIANT_BACKTEST_OWNER_GOAL_BR_202207_202606.md` |
| A3 round-retest RR2 prereg | `xau-usd/xauusd-phase1/docs/A3_ROUND_RETEST_RR2_MT5_PROBE_PREREG_2026_07_05.md`: six fixed Account 3 guarded/structured round-retest variants, exact MT5 Strategy Tester only, `2022-07-01 -> 2026-06-30`. The only EA change was default-safe `InpTargetR=1.50`, allowing tester inputs at `2.0R/2.5R` while preserving committed default behavior. |
| A3 round-retest RR2 probe | `REJECT / NO_OWNER_GOAL_HIT`: guarded rows are profitable but wrong-shaped: best WR row `rdguard_default_r20_cost015` has WR `31.52%`, W/L `2.4473`, active days `14.86%`, PF `1.1262`, manual PnL `6973.98 AED`; best net row `rdguard_default_r25_cost030` has WR `27.29%`, W/L `3.2155`, PF `1.2070`, manual PnL `10371.75 AED`. Structured rows are unusable: `rdstruct_default_r20_cost030` closed 1 loss with `5777` order-send failures, and `rdstruct_default_r25_cost030` timed out with no report. |
| A3 round-retest report | `xau-usd/xauusd-phase1/outputs/reports/A3_ROUND_RETEST_RR2_MT5_PROBE_OWNER_GOAL_A3_RD_202207_202606.md` |
| RR2 long-only causal filter diagnostic | `NO_CORE_HIT_DIAGNOSTIC_ONLY`: baseline exact-MT5 RR2 long-only is `798` trades, WR `41.35%`, W/L `2.1292`, active days `32.89%`, PF `1.5014`, net `1744.60 AED`. Best offline causal-filter near miss is `234` trades, WR `48.72%`, W/L `2.0418`, active days `15.24%`, PF `1.9397`, net `1022.91`, last-12-months WR/W-L `54.24%/2.03`. No row with `>=200` trades reached both WR `>=50%` and W/L `>=2.0`, so no MT5 rerun/reviewer spend. |
| RR2 long-only diagnostic report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_RR2_LONG_ONLY_CAUSAL_FILTER_DIAGNOSTIC_2026_07_05.md` |
| V9/V10 RR2 stretch prereg | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_V9_V10_RR2_STRETCH_PROBE_PREREG_2026_07_05.md`: four fixed high-WR family variants stretched to `2.0R`, exact MT5 Strategy Tester only, `2022-07-01 -> 2026-06-30`. |
| V9/V10 RR2 stretch probe | `REJECT_NO_OWNER_GOAL_HIT`: the payoff target is reachable, but hit rate collapses at `2R`. Best row `v9_sweep_h1_long_rr2p0` has `640` trades, WR `37.03%`, W/L `2.2003`, active days `39.02%`, PF `1.2939`, manual P&L `697.48 USD`, last-12-months WR/W-L `45.00%/2.05`. Other rows show WR only `33.71%` to `37.41%`. |
| V9/V10 RR2 stretch report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_V9_V10_RR2_STRETCH_PROBE_OWNER_GOAL_V9V10_RR2_202207_202606.md` |
| Opening-range reversal Step 4 prereg | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_OPENING_RANGE_REVERSAL_STEP4_PREREG_2026_07_05.md`: 12 fixed exact-MT5 design cells over `2016-01-01 -> 2021-12-31`, then top three design rows frozen into exam over `2022-07-01 -> 2026-06-30`. |
| Opening-range reversal Step 4 exam | `REJECT_NO_OWNER_GOAL_HIT`: design selected `orrev_london_firm_stop15`, `orrev_london_firm_stop10`, and `orrev_london_loose_stop15`. Best exam row `orrev_london_firm_stop15` has `1422` trades, WR `32.70%`, W/L `2.0542`, active days `74.30%`, PF `0.9981`, manual P&L `-7.38 USD`, max closed DD `272.06`, last-12-months WR/W-L `32.93%/2.07`. This improves activity and preserves `~2R`, but misses the WR target by about `17.3` percentage points. |
| Opening-range reversal report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_OPENING_RANGE_REVERSAL_STEP4_COMBINED_VERDICT_2026_07_05.md` |
| RR2 profit-lock management prereg | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_PREREG_2026_07_05.md`: six fixed management cells on the known RR2 long-only A1 baseline, design window `2016-01-01 -> 2021-12-31`, top three frozen into exam `2022-07-01 -> 2026-06-30`. |
| RR2 profit-lock management exam | `REJECT_NO_OWNER_GOAL_HIT`: design selected `rr2_lock080_020`, `rr2_lock080_010`, and `rr2_lock100_010`. Best WR exam row `rr2_lock080_010` has `877` trades, WR `58.04%`, W/L `0.9666`, active days `33.56%`, PF `1.3369`, manual P&L `920.51 USD`, last-12-months WR/W-L `59.14%/0.93`. Best P&L row `rr2_lock100_010` has `843` trades, WR `52.79%`, W/L `1.2019`, active days `33.27%`, PF `1.3438`, manual P&L `1016.70 USD`, last-12 `54.38%/1.19`. Profit-lock recovers WR but collapses realized W/L far below `2.0`. |
| RR2 profit-lock report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_COMBINED_VERDICT_2026_07_05.md` |
| External macro traffic-light gate | `REJECT_NO_EXTERNAL_MACRO_GATE_OWNER_SHAPE`: predeclared daily external gates over exact MT5 trade ledgers did not produce an exam-window core hit. Best high-WR rows stayed in the profit-lock corner (`rr2_lock080_010` real-asset gate: `507` trades, WR `60.55%`, W/L `0.9399`), while the `~2R` rows stayed low-WR (`rr2_baseline_no_lock`: `798` trades, WR `41.35%`, W/L `2.1292`; opening-range reversal: `1422` trades, WR `32.70%`, W/L `2.0542`). No reviewer spend. |
| External macro traffic-light report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_EXTERNAL_MACRO_TRAFFIC_LIGHT_GATE_DIAGNOSTIC_2026_07_05.md` |
| Split break-distance exact probe | `REJECT_NO_OWNER_CORE_SHAPE`: added default-disabled MT5 guard inputs `InpMinBreakDistanceAtr` / `InpMaxBreakDistanceAtr`, then exact-tested the strongest internal near miss as three guarded split-entry components with `InpMinBreakDistanceAtr=0.8994`. After Step-1-style component dedupe: `1176` signals, WR `52.38%`, W/L `1.4857`, active days `48.90%`, PF `1.6490`, manual P&L `4683.08 USD`, last-12 WR/W-L `54.22%/1.44`. The exact implementation did not preserve the offline near miss (`52.23%/1.9792`) and is rejected. |
| Split break-distance exact report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_SPLIT_BREAK_DISTANCE_GUARD_EXACT_PROBE_202207_202606.md` |
| Early adverse exit exact probe | `REJECT_NO_OWNER_CORE_SHAPE`: added default-disabled MT5-side managed close inputs `InpEarlyAdverseExitEnabled`, `InpEarlyAdverseExitAfterMinutes`, and `InpEarlyAdverseExitR`, then exact-tested four frozen loss-truncation cells on the `f33_r30_be_1r` split components. Best payoff cell `eae30_r035` reached W/L `2.1917` but WR fell to `39.13%`; best WR cell `eae60_r050` reached WR `46.09%` but W/L was only `1.8040`. Activity stayed near `62%`. This proves early loss truncation can lift payoff but does not solve the WR/W-L owner core. |
| Early adverse exit exact report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_202207_202606.md`; SHA256 `038697311095A70A264D615069913E37B0BAFB178640AF04357BE9E4A3EFFE47`; EA SHA256 `6FAD2D06D43387E55FBF6BC196384EDE6FD531DF82B3FFCB5B958B373F2B61A0`; no isolated-root `terminal64.exe` remained after completion. |
| Early adverse internal gate diagnostic | `NO_IN_SAMPLE_WR_WL_HIT`: reused the causal Step 2 feature-gate analyzer on the exact early-adverse kept-signal ledger. No row reached the hard WR `>=50%` and W/L `>=2.0` shape with the sample/activity floor. The most tempting row was `eae60_r050` with `block_ANY_against_wick_points_<=_0.95`: `258` signals, WR `50.78%`, W/L `2.1375`, active `15.53%`, but it fails sample and activity and is diagnostic only. |
| Early adverse internal gate report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_EARLY_ADVERSE_EXIT_INTERNAL_GATE_DIAGNOSTIC_2026_07_05.md`; SHA256 `5726955F8369CDD3806D6E66DE793D1E6881BD93202237EB1D1A5095589E7CCB`. |
| V7/V8/V11/V13 RR2 stretch probe | `REJECT_NO_OWNER_GOAL_HIT`: four fixed existing entry families were stretched to `2.0R` with exact MT5 over `2022-07-01 -> 2026-06-30`. Best row was `v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning`: `1008` trades, WR `39.68%`, W/L `2.1943`, active `58.68%`, PF `1.4436`, manual P&L `1794.42 USD`, max DD `119.10`, last-12 WR/W-L `45.04%/2.11`. V7 and V11 also preserved ~2R but WR stayed near `36%`; V8 was only `17` trades. No reviewer spend. |
| V7/V8/V11/V13 RR2 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_V7_V8_V11_V13_RR2_STRETCH_PROBE_OWNER_GOAL_202207_202606.md`; SHA256 `D1DAC3574811A5D073B2CECF50F81B84AB4894EAF5A99C8CF64B1D5579631977`; no isolated-root `terminal64.exe` remained after completion. |
| Step 3 portfolio composition | `REJECT_NO_STEP3_OWNER_PORTFOLIO`: checked `3599` legal cross-family portfolios using exact MT5 trade CSVs and exact MT5 signal ledgers only. No MT5 launch, no runtime attach, no inferred exits. There were `0` portfolios with WR `>=50%` and W/L `>=2.0`, and `0` near-owner rows by the preregistered near-shape rule. |
| Step 3 best frontier | Best WR-preserving row: `step1_f67_r20_be_tp1 + v8_compress_h1_long_rr2p0 + orrev_london_firm_stop15`, `4128` signals, WR `50.02%`, W/L `1.3227`, active weekdays `86.58%`, PF `1.3356`, net `6777.71 USD`, top-25 removed net `5315.01`, last-12 WR/W-L `52.09%/1.3074`. It fails W/L badly. |
| Step 3 payoff/activity tradeoff | Best payoff row reached W/L `2.6153` but only WR `36.39%` and active `84.56%`. Best activity row reached active `93.19%` and W/L `2.1506`, but only WR `36.74%`. Composition improves frequency but does not bridge the owner WR/W-L tradeoff. |
| Step 3 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_2026_07_05.md`; result CSV `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_2026_07_05_RESULTS.csv`; kept/dropped overlap lists were written for the best frontier row. |
| H4 independent observer exact probe | `CORE_SHAPE_HIT_FREQUENCY_GAP`: new tester-only H4/D1 observer premises were converted into default-off exact-MT5 signal modes. Best row `d1_compression_h4_expansion_rr2p0` reached `19` trades, WR `52.63%`, W/L `2.9284`, PF `3.2538`, manual P&L `+862.54 USD`, but only `1.82%` active weekdays. |
| D1 compression frequency mechanics | `CORE_SHAPE_SURVIVES_FREQUENCY_GAP`: the baseline had `107` raw signals but only `19` trades because `86` were blocked by `own_position_exists`. Relaxing max-open caps to 2/4/8/16 preserved core shape only at higher caps. Best row `d1_compression_h4_expansion_rr2p0_max16` reached `103` trades, WR `53.40%`, W/L `2.7193`, PF `3.1159`, manual P&L `+4398.58 USD`, active weekdays `7.48%`. |
| H4/D1 reports | Initial probe `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_INDEPENDENT_OBSERVER_FAMILIES_EXACT_PROBE_202207_202606.md`; frequency probe `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_COMPRESSION_FREQUENCY_MECHANICS_202207_202606.md`. |
| Raw-frequency ladder | `NEAR_MISS_RAW_FREQUENCY_LADDER`: broadening D1/H4 frequency reached `335` trades, WR `49.55%`, W/L `2.2456`, PF `2.2057`, manual P&L `+11018.80 USD`, active weekdays `20.33%`. It missed the hard WR target by `0.45` percentage points. Exact-ledger direction split showed longs at `203` trades, WR `61.58%`, W/L `2.2942`, PF `3.6766`, while shorts were losing. |
| Long-only frequency stress | `LONG_ONLY_CORE_SHAPE_FREQUENCY_GAP`: post-diagnostic long-only exact MT5 stress produced the current best row, `long_box2_atr80_range150_body035`, with `344` trades, WR `57.56%`, W/L `2.2812`, PF `3.0937`, manual P&L `+16084.99 USD`, max closed DD `1521.71 USD`, active weekdays `19.56%`. Still not demo-ready because activity is far below target. |
| Long-only reports | Raw ladder `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_COMPRESSION_RAW_FREQUENCY_LADDER_202207_202606.md`; long-only stress `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_LONG_ONLY_FREQUENCY_STRESS_202207_202606.md`. |
| H1 D1-long expansion stress | `REJECT_H1_LONG_FREQUENCY_STRESS_BREAKS_CORE_SHAPE`: lowering the same D1 breakout premise from completed H4 decisions to completed H1 decisions broke the edge. Best H1 row had only `41` trades, WR `4.88%`, W/L `2.0367`, PF `0.1044`, manual P&L `-980.11 USD`, active weekdays `1.25%`. |
| H1 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H1_D1_LONG_EXPANSION_FREQUENCY_STRESS_202207_202606.md` |
| H4 long-only robustness audit | `COMPONENT_CLUE_ROBUSTNESS_GAP_NO_REVIEW`: full-window metrics are strong, but review/demo is blocked by active weekdays only `19.56%`, 2022/2023 below 50% WR, last-12-month W/L only `1.6650`, only `20/41` active months positive, and top-100-winner removal flipping net P&L to `-1211.70 USD`. |
| Robustness report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_LONG_ONLY_ROBUSTNESS_AUDIT_2026_07_05.md` |
| H4 long-only pre-2022 extension | `REJECT_PRE2022_CORE_SHAPE_FAIL`: frozen older-window exact MT5 run over `2016-01-01 -> 2021-12-31` produced `591` trades, WR `43.99%`, W/L `1.9095`, PF `1.4999`, manual P&L `+3844.54 USD`, active weekdays `23.05%`. It fails both hard core thresholds, so the D1-compression/H4-expansion branch is rejected for promotion. |
| Pre-2022 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_LONG_ONLY_PRE2022_ROBUSTNESS_201601_202112.md` |
| Daily extreme reclaim prereg probe | `REJECT_DESIGN_NO_CORE_OR_NEAR_FRONTIER`: new default-off exact-MT5 M5 signal mode `SIGNAL_DAILY_EXTREME_RECLAIM` was preregistered as a separate intraday exhaustion/reclaim family. Six design rows over `2016-01-01 -> 2021-12-31` all failed. Best row `der_exhaustion_125` had `555` trades, WR `27.93%`, W/L `2.0529`, PF `0.7955`, manual P&L `-353.54 USD`, active weekdays `14.75%`. Because no row reached core or near-frontier, the `2022-2026` exam was not spent. |
| Daily extreme report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_DAILY_EXTREME_RECLAIM_PREREG_EXACT_PROBE_2026_07_05.md` |
| High-payout feature-gate diagnostic | `DIAGNOSTIC_REJECT_NO_REPLAY_CANDIDATE`: tested three fixed high-payout exact-MT5 portfolios against single signal-feature blocks joined back to MT5 signal logs. Best usable row `hp_core_v13_orrev` with `LONG estimated_cost_r <= 0.0114` kept `3551` signals, WR `36.69%`, W/L `2.6773`, PF `1.5518`, net `11195.26 USD`, active weekdays `84.18%`, retention `91.71%`. Aggressive rows approached `48%` WR only by retaining about `10%` of trades and collapsing active coverage near `20%`. No exact-MT5 replay or reviewer spend. |
| High-payout feature-gate report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_HIGH_PAYOUT_FEATURE_GATE_DIAGNOSTIC_2026_07_05.md` |
| News hygiene diagnostic | `NEWS_HYGIENE_REJECT_NO_REPLAY_CANDIDATE`: fixed deterministic NFP/CPI/FOMC-style windows did not improve the high-payout frontier. Best row remained the baseline `step3_high_payout_v13_orrev`: `3872` signals, WR `36.39%`, W/L `2.6153`, active weekdays `84.56%`, PF `1.4961`, net `11422.59 USD`. |
| News hygiene report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_NEWS_HYGIENE_DIAGNOSTIC_2026_07_05.md` |
| Best-of-each hybrid frontier | `HYBRID_CORE_SHAPE_FREQUENCY_GAP`: checked `381` exact-ledger component combinations. Best core-shape row is `h4_d1_long_best_box2_atr80 + h4_d1_long_broad_box3_atr60`: `346` signals, WR `57.80%`, W/L `2.3077`, active weekdays `19.65%`, PF `3.1613`, net `16603.86 USD`, stress `-0.30/ticket` W/L `2.2890`. |
| Closest broad hybrid | `NEAR_OWNER_FRONTIER`: `freq_step3_frontier + hp_v13_orrev + split_high_payout_f33_r30_be_never + h4_d1_long_best_box2_atr80 + h4_d1_long_broad_box3_atr60` reached `4829` signals, WR `49.47%`, W/L `1.8287`, active weekdays `88.78%`, PF `1.8038`, net `23864.21 USD`. It is the closest all-around shape but still misses hard WR and W/L. |
| Hybrid report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEST_OF_EACH_HYBRID_FRONTIER_2026_07_05.md` |
| M5 EMA HTF exact frequency source | `REJECT_M5_EMA_HTF_NO_OWNER_SHAPE`: exact MT5 tested three preregistered `SIGNAL_M5_EMA_TREND_CONTINUATION` long-only variants over `2022.07.01 -> 2026.06.30`. Best row `m5ema_long_h1h4_rr2p0` produced `2784` trades, WR `35.42%`, W/L `2.0756`, active weekdays `44.97%`, PF `1.1382`, net `1610.73 USD`. This supplied trades but not win rate. |
| M5 EMA HTF report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_EMA_HTF_FREQUENCY_SOURCE_202207_202606.md` |
| Remaining built-in M5 2R design | `DESIGN_CANDIDATE_EXAM_REQUIRED`: four fixed remaining built-in M5 families were exact-tested over `2016.01.01 -> 2021.12.31`. Only `compression_long_h1h4_rr2p0` earned a frozen exam with `28` trades, WR `57.14%`, W/L `2.2990`, active weekdays `1.72%`, PF `3.0653`, net `90.09 USD`. |
| Compression H1/H4 2R exam | `REJECT_COMPRESSION_H1H4_RR2_EXAM_FAILED`: the frozen candidate failed the recent exact-MT5 exam over `2022.07.01 -> 2026.06.30`: `9` trades, WR `22.22%`, W/L `2.9646`, active weekdays `0.86%`, PF `0.8470`, net `-8.58 USD`. |
| Compression exam report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_COMPRESSION_H1H4_RR2_EXAM_202207_202606.md` |
| Hybrid categorical gate diagnostic | `DIAGNOSTIC_NEAR_FRONTIER_NO_REVIEW`: fixed causal categorical gates on the broad hybrid produced the closest high-cadence frontier so far. Best row `wr_rank16` with `block_direction_hour=LONG|13 + block_direction_hour=LONG|3` reached `4006` signals, WR `50.00%`, W/L `1.9528`, active weekdays `86.96%`, PF `1.9695`, net `23277.20 USD`. It still misses W/L `2.0` and the `90%` active-day target. |
| Hybrid gate report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_CATEGORICAL_GATE_DIAGNOSTIC_2026_07_05.md` |
| Hybrid long-hour payout diagnostic | `DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED`: seeded long-hour repair on `freq_step3_frontier + split_high_payout_f33_r30_be_never + h4_d1_long_best_box2_atr80 + h4_d1_long_broad_box3_atr60` found blocked LONG hours `3,10,13,14`: `3690` diagnostic signals, WR `50.03%`, W/L `2.0510`, active weekdays `86.10%`, PF `2.0712`, net `23036.88 USD`. Stress `-0.30/ticket` W/L fell to `1.9575`, so exact replay was required before review. |
| Hybrid long-hour payout report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_LONG_HOUR_PAYOUT_REPAIR_2026_07_05.md` |
| Exact hybrid LH3/10/13/14 replay | `EXACT_NEAR_PAYOUT_NO_REVIEW`: exact MT5 replay of the 10 affected components plus manual signal-level composition produced `3847` signals, WR `50.09%`, W/L `1.9859`, active weekdays `86.39%`, PF `2.0077`, net `22587.43 USD`, max closed DD `1547.07 USD`, last-12 WR/W-L/active `52.88%/2.1553/80.84%`, and stress `-0.30/ticket` W/L `1.8887`. It misses W/L `2.0` by `0.0141` and active days by `3.61` percentage points; no reviewer spend. |
| Exact hybrid replay report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_LH3_10_13_14_EXACT_REPLAY_202207_202606.md` |
| F67 hour-16 exact repair | `EXACT_FAIL_OWNER_SHAPE`: reran the three affected f67 components in exact MT5 with server hour `16` blocked for both directions while retaining LONG blocks `3,10,13,14`. Composition with the unchanged exact component ledgers produced `3861` signals, WR `49.96%`, W/L `1.9999`, active weekdays `86.39%`, PF `2.0114`, net `22797.26 USD`, last-12 WR/W-L/active `52.48%/2.1850/80.84%`, stress `-0.30/ticket` W/L `1.9020`. It improved payoff but missed both hard core metrics by rounding-level margins. |
| F67 hour-16 exact repair report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606.md` |
| F67-H16 no-f33 composition | `EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW`: exact-ledger composition after removing `step1_f33_r30_be_never` from the final hybrid and rerunning dedupe produced the best frontier so far: `3751` signals, WR `50.23%`, W/L `2.0002`, active weekdays `86.39%`, PF `2.0336`, net `22294.46 USD`, max closed DD `1583.72 USD`, last-12 WR/W-L/active `52.86%/2.2118/80.84%`, stress `-0.30/ticket` W/L `1.9029`. It clears WR/W-L only by a razor-thin margin, still misses 90% active days, and fails stress W/L; no demo spec. |
| F67-H16 no-f33 composition report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606.md` |
| Companion activity search | `NO_ACTIVITY_BRIDGE_NO_REVIEW`: simple exact-ledger companion filters did not bridge the activity gap. Best core-preserving row was `rr2_baseline_no_lock[month=08]`: `3794` signals, WR `50.03%`, W/L `2.0093`, active weekdays `87.06%`, only `+7` new active weekdays, stress `-0.30/ticket` W/L `1.9110`. |
| Companion combo search | `ACTIVITY_OR_CORE_NOT_BOTH_NO_REVIEW`: small exact-ledger combos can buy the activity target but break WR. Best activity row reached `5164` signals, WR `46.40%`, W/L `2.1050`, active weekdays `90.99%`, `+48` new active weekdays, stress W/L `1.9954`. There is still no WR `>=50%` + W/L `>=2.0` + active `>=90%` bridge in the current exact source pool. |
| Companion reports | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_COMPANION_ACTIVITY_SEARCH_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_COMPANION_COMBO_SEARCH_2026_07_05.md` |
| V7/V11 antipoison diagnostic | `NO_V7_V11_ANTIPOISON_BRIDGE_NO_REVIEW`: causal MT5 signal-feature gates on the v7/v11 activity sources did not bridge the gap. Best core-preserving row added only `+2` active weekdays (`3730` signals, WR `50.00%`, W/L `2.0172`, active `86.58%`). Best 90%+ activity row reached `4656` signals, WR `47.32%`, W/L `2.0879`, active `90.03%`, validation WR/W-L `49.48%/2.1501`. |
| Prune-fill diagnostic | `PRUNE_FILL_FAILS_WR_NO_REVIEW`: categorical pruning of the baseline frequency branch plus v7/v11 activity fill still failed WR. Best row blocked `f67_v13_lh` hour `15` and filled with all v7: `4970` signals, WR `46.14%`, W/L `2.1509`, active `90.41%`, validation WR/W-L `48.39%/2.2276`. |
| Antipoison/prune-fill reports | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_V7_V11_ANTIPOISON_GATE_DIAGNOSTIC_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_PRUNE_FILL_DIAGNOSTIC_2026_07_05.md` |
| Liquidity sweep-reclaim 2R diagnostic | `NO_EXACT_MT5_REPLAY_CANDIDATE`: preregistered `576` offline M5 variants on 2016-2021 design, froze five rows, and examined 2022-07-01 through 2025-06-30. Best exam row solved activity/payoff but failed WR badly: `3975` signals, WR `30.19%`, W/L `2.0650`, active weekdays `98.08%`, PF `0.8930`, net `-615.37` at approx 0.01 lot, last-12 WR/W-L/active `29.02%/2.0676/98.85%`. No MT5 replay, no reviewer spend. |
| Liquidity sweep-reclaim reports | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_PREREG_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_2026_07_05.md` |
| HTF pullback-reclaim 2R diagnostic | `NO_EXACT_MT5_REPLAY_CANDIDATE`: preregistered `256` offline M5 variants on 2016-2021 design, froze five rows, and examined 2022-07-01 through 2025-06-30. Best exam row improved structure versus raw false-break but still failed WR: `2615` signals, WR `31.09%`, W/L `2.1445`, active weekdays `81.84%`, PF `0.9675`, net `-166.47` at approx 0.01 lot, last-12 WR/W-L/active `33.65%/2.0441/84.67%`. No MT5 replay, no reviewer spend. |
| HTF pullback-reclaim reports | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_HTF_PULLBACK_RECLAIM_2R_DIAGNOSTIC_PREREG_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_HTF_PULLBACK_RECLAIM_2R_DIAGNOSTIC_2026_07_05.md` |
| Quiet-day 2R companion diagnostic | `NO_QUIET_DAY_2R_COMPANION_BRIDGE`: tested only base-missing weekdays in the common `2022-07-01 -> 2025-06-30` window using the frozen liquidity sweep-reclaim and HTF pullback-reclaim diagnostic ledgers. Best row `base_plus_lsr_all_on_missing_day` restored active weekdays to `98.98%`, but broke core shape: `3365` signals, WR `46.63%`, W/L `1.8878`, PF `1.6593`, net `8749.70`, last-12 WR/W-L/active `47.89%/2.0930/98.85%`. No MT5 replay, no reviewer spend. |
| Quiet-day companion reports | `xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_FRONTIER_QUIET_DAY_2R_COMPANION_DIAGNOSTIC_PREREG_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CURRENT_FRONTIER_QUIET_DAY_2R_COMPANION_DIAGNOSTIC_2026_07_05.md` |
| D1/H4 sparse-quality scout | `NO_EXACT_MT5_REPLAY_CANDIDATE`: preregistered `256` offline D1-context/H4-confirmation variants on 2016-2021 design, froze five rows, and examined 2022-07-01 through 2025-06-30. Best exam row was only `108` signals, WR `44.44%`, W/L `1.8636`, active weekdays `11.64%`, PF `1.4909`, net `386.71` at approx 0.01 lot, last-12 WR/W-L/active `39.22%/1.5691/16.09%`. No MT5 replay, no reviewer spend. |
| D1/H4 sparse-quality reports | `xau-usd/xauusd-phase1/docs/A1_XAU_D1H4_SPARSE_QUALITY_2R_SCOUT_PREREG_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_D1H4_SPARSE_QUALITY_2R_SCOUT_2026_07_05.md` |
| Weekly loss-shape repair diagnostic | `NO_CAUSAL_WEEKLY_REPAIR`: baseline current frontier has only `58.10%` positive weeks and worst week `-$609.41`; June 2026 was `-$222.84`, with worst week `-$522.85`. Best causal count-cap row `h4_max_1_per_week` improves June to `+$128.43` and worst week to `-$285.81`, but breaks owner core to WR `49.66%` and W/L `1.6008`. Sensitivity-only loss caps near `$50-$75` preserve the core and improve June, but are not executable claims. |
| Weekly loss-shape reports | `xau-usd/xauusd-phase1/docs/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_PREREG_2026_07_05.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05.md` |
| H4/D1 stop-ceiling one iteration | `REJECT_STOPCEIL3000_BREAKS_OR_FAILS_FRONTIER`: exact-MT5 standalone H4/D1 cell with `InpStopCeilingPoints=3000` reached `70` trades, WR `54.29%`, W/L `2.0684`, PF `2.4562`, net `1039.02 USD`, max DD `198.54`. Replacing the current H4/D1 source inside the hybrid improved max DD (`1583.72 -> 727.02`), worst week (`-609.41 -> -429.39`), positive months (`60.42% -> 70.83%`), and June 2026 (`-222.84 -> +368.84`), but broke W/L to `1.9408` and reduced net to `17760.44 USD`. No demo spec and no reviewer spend. |
| H4/D1 stop-ceiling report | `xau-usd/xauusd-phase1/docs/A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_PREREG_2026_07_06.md`; `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606.md` |
| Next action | Do not draft a demo spec and do not spend reviewer yet. The best full-window frontier remains F67-H16 no-f33 at WR `50.23%` / W/L `2.0002` / active `86.39%`, but weekly loss shape is weak and simple stop-ceiling filtering breaks the core W/L. The next useful direction is a true exact-MT5 stop/risk geometry implementation, not more ceiling filters. |
| Step 1 frontier report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_FRONTIER_2026_07_05.md` |
| Pre-registration document | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_PREREG_2026_07_05.md` |

## Forex Research Lane

Status: `RESEARCH_ONLY_MT5_RAW_AND_TUNED_WATCHLISTS_NO_DEMO`

Separate lane: `forex-research`

Runtime boundary: actual MT5 Strategy Tester was used only in the isolated tester root for research. No live/demo terminal, chart, preset, running XAU EA, order, position, or broker runtime state was touched.

| Item | Result |
| --- | --- |
| MT5 recent-12 frozen frequency gate | `FOREX_RECENT12_FROZEN_GATE_COMPLETE_NO_DEMO`: exact MT5 runs from 2025-07-01 through 2026-07-03 plus manual trade-CSV P&L. EURUSD M30 tuned: 242 trades, 57.02% WR, manual PF 1.1254, +$16.87, top-10 removed -$3.67. EURUSD M15 tuned: 366 trades, 52.46% WR, PF 0.9078, -$16.92. USDJPY London60 M30 tuned: 193 trades, 50.26% WR, PF 1.0997, +$20.81, top-10 removed -$27.47. No candidate moved closer to demo. |
| MT5 last-3M best-candidate manual P&L | `FOREX_LAST3M_MANUAL_PNL_COMPLETE_NO_DEMO`: exact `2026-04-01 -> 2026-07-03` entry-date audit from actual MT5 trade CSVs. Best fixed-0.01 result is USDJPY Asia-London M30 raw: 31 trades, 48.39% WR, PF 1.2924, +$8.69. USDJPY London120 M15 D1 ATR20 guard: 17 trades, 58.82% WR, PF 1.5180, +$6.33. EURUSD M30 tuned: 69 trades, 55.07% WR, PF 1.0875, +$2.92. USDJPY London60 M30 tuned and EURUSD M15 tuned are negative. This is not a leverage issue; no demo spec. |
| MT5 D1 slow-book trend scout | `REJECT_MT5_D1_TREND_SLOW_BOOK_NO_EDGE`: new tester-only `ForexDailyTrendScout.mq5` compiled and ran in actual MT5 Strategy Tester across EURUSD/GBPUSD/USDJPY/AUDUSD/NZDUSD/USDCAD/USDCHF from `2024-07-01 -> 2026-07-03`. Rule was D1 40-day close breakout, 2 ATR initial stop, 3 ATR daily trail, max 120 holding days, no TP. All rows were low-frequency and non-viable; best manual PF was EURUSD 15 trades, PF 0.9936, -$0.65 while MT5 PF was 0.85. No extension, tuning, or demo spec. |
| Available clean spread cells | `EURUSD/USDJPY M5/M15/H1/H4 Capital.com` |
| Missing required symbol data | `GBPUSD processed bars missing` |
| Best cost cell | `USDJPY H4 p95_cost_R_recent=0.0206` |
| Next cost cells | `EURUSD H4=0.0282, USDJPY H1=0.0565, EURUSD H1=0.0573` |
| MT5 raw frequency-first lead | `EURUSD rsi_extreme_fade_m15_long_rr0p80`: 1524 MT5 trades, CSV PF 1.1336, MT5 PF about 1.12, +$97.94 from 2022-07-01 through 2026-07-02 |
| MT5 tuned watchlist lead | Block entry hours `1,7,21`: 1309 MT5 trades, CSV PF 1.1705, MT5 PF about 1.15, +$108.84; splits are 2022-2024 PF 1.0875 / +$30.87 and 2024-2026 PF 1.2733 / +$77.97 |
| MT5 tuned robustness read | `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`; top-10-winner removal still PF 1.1232 / +$78.66, but only 27/49 positive months and worst 250-trade rolling window PF 0.8131 / -$25.78 |
| MT5 M30 tuned watchlist lead | `EURUSD rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80`: 831 MT5 trades, CSV PF 1.2325, MT5 PF about 1.20, +$114.80; splits are 2022-2024 PF 1.1585 / +$40.57 and 2024-2026 PF 1.3123 / +$74.23 |
| MT5 M30 tuned robustness read | Strongest Forex MT5 packet so far, but `WATCHLIST_ONLY`: 36/49 positive months, worst 250-trade rolling window PF 0.9765 / -$3.62, top-10-winner removal PF 1.1641 / +$80.99; blocked by negative 100/150-trade windows, top-50-winner removal PF 0.9735 / -$13.10, and failed GBPUSD/USDJPY portability |
| MT5 USDJPY raw diversification lead | `USDJPY london120_break_m15`: 521 MT5 trades from 2022-2026, CSV PF 1.3917, MT5 PF about 1.38, +$232.03; no-parameter-change 2020-2026 extension improves sample to 859 MT5 trades, CSV PF 1.3028, MT5 PF about 1.28, +$289.44; full 2018-2026 remains positive at 1144 trades, CSV PF 1.2230, MT5 PF about 1.21, +$273.09 |
| MT5 USDJPY raw robustness read | `WATCHLIST_ONLY_MT5_RAW_DIVERSIFICATION_LEAD`; every 2020-2026 entry-date calendar year is positive, both long and short are positive over 2020-2026, 32/48 months positive in the original 2022-2026 packet, worst 250-trade window stays positive in both windows; blocked by negative standalone 2018-2019 PF 0.9435 / -$15.09, weak 2019, weak 2021-H2 and 2024-H1 half-years, pre-2022 short-side PF 0.9856 / -$2.91, negative short rolling windows, top-winner dependency, and failed EURUSD/GBPUSD portability |
| MT5 USDJPY D1 ATR20 range-quality guard | `USDJPY london120_break_m15_d1atr20_guard`: one predeclared structural guard, no sweep. Full 2018-2026 actual MT5 result is 865 trades, manual PF 1.2551, MT5 PF about 1.23, +$253.17 manual / +$235.21 MT5; recent 2025-2026 is 169 trades, PF 1.2114, +$44.76; trailing 12M after +0.5 pip stress is PF 1.1527 / +$20.84. Status: `ACCEPT_GUARD_AS_WATCHLIST_V1_NO_DEMO_APPROVAL` |
| Dukascopy USDJPY D1 ATR20 alternate-history replay | Public Dukascopy M5 bid-OHLC replay of frozen v1, UTC-aligned from MT5 price probes, 892800 M5 rows from 2018-01-01 through 2026-06-27. Full available replay is 1038 trades, PF 1.2164, +$241.33; from 2020 is PF 1.2514, +$225.82; but recent 2025-2026 fails at 180 trades, PF 0.9275, -$17.22 and PF 0.9040 after +0.5 pip stress. Status: `DUKASCOPY_BID_M5_ALT_HISTORY_REPLAY_RESEARCH_ONLY`; no demo spec |
| Dukascopy USDJPY ask/tick acquisition | `dukascopy-node` bid M5 works, but ask-side M5 and tick probes failed with `Unknown error`. This blocks a stricter bid/ask Dukascopy replay through that tool. The failure does not improve the candidate because the bid-only 2025-2026 replay is already negative before stricter ask-side costs. |
| Dukascopy USDJPY direct bid/ask tick replay | `DUKASCOPY_DIRECT_TICK_BIDASK_REPLAY_RESEARCH_ONLY`: direct `.bi5` downloader/replay closed the wrapper gap without touching MT5 runtime. Frozen `london120_break_m15_d1atr20_guard` over `2025-01-01 -> 2026-06-27` produced 177 trades, WR 50.28%, PF 0.9578, -$9.64; +0.5 pip extra stress PF 0.9333, -$15.43. 2025 alone failed at 117 trades, PF 0.8366, -$28.26; 2026 partial was positive at 60 trades, PF 1.3368, +$18.62. This strengthens NO DEMO SPEC. |
| MT5 USDJPY tuned M30 frequency lead | `USDJPY london60_break_m30_blockh7_11_rr1`: raw M30 stretch was 1560 MT5 trades, CSV PF 1.1271, MT5 PF about 1.12, +$214.98 from 2020-2026; tuned block-hours version is 1227 trades, CSV PF 1.2062, MT5 PF about 1.19, +$278.20 from 2020-2026 and 384 trades, CSV PF 1.2057, MT5 PF about 1.20, +$94.87 from 2024-2026; full 2018-2026 is 1607 trades, CSV PF 1.1524, MT5 PF about 1.14, +$257.53 |
| MT5 USDJPY tuned M30 robustness read | `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_DIVERSIFICATION_LEAD`; best tuned high-frequency USDJPY clue, but blocked by post-hoc hour filter, negative standalone 2018-2019 PF 0.9410 / -$20.05, negative 2019 and 2023, materially negative 2023-H1, negative full-history rolling windows, top-winner dependency, barely positive recent long side, and failed frozen EURUSD/GBPUSD portability |
| MT5 USDJPY raw M30 Asia-London lead | `USDJPY asia_london_break_m30`: fixed raw extension, no tuning; 207 trades, CSV PF 1.1996, MT5 PF about 1.17, +$54.04 parsed / +$46.56 MT5 in 2018-2019; 721 trades, CSV PF 1.1564, MT5 PF about 1.14, +$179.97 parsed / +$161.13 MT5 in 2020-2026; full 2018-2026 is 928 trades, CSV PF 1.1646, MT5 PF about 1.14, +$234.01 parsed / +$207.69 MT5 |
| MT5 USDJPY raw M30 Asia-London robustness read | `WATCHLIST_ONLY_MT5_RAW_FREQUENCY_DIVERSIFICATION_LEAD_NEEDS_REVIEW`; cleaner all-window raw M30 USDJPY lead than `london120_break_m30`, with both long and short positive, but blocked from demo by PF only 1.1646, 2021/2023 negative, 58/102 positive months, worst 250-trade rolling PF 0.9142 / -$30.37, and top-50-winner removal PF 0.9527 / -$67.27 |
| MT5 USDJPY Asia-London M30 blockh7 tune | `TUNE_REJECT_KEEP_RAW_WATCHLIST_PREFERRED`; pre-declared design picked only hour `7` from 2018-2023 raw trades. It improved design PF slightly but hurt validation and full-window net: validation raw 252 trades / PF 1.2100 / +$90.16 parsed versus blockh7 232 trades / PF 1.1750 / +$70.37 parsed; full raw 928 trades / PF 1.1646 / +$234.01 parsed versus blockh7 859 trades / PF 1.1700 / +$226.71 parsed |
| MT5 GBPUSD rejected frequency extension | `GBPUSD bb_wick_reclaim_m30_rr0p80`: 2024-2026 current screen was 156 trades, CSV PF 1.1731, MT5 PF about 1.15, +$23.70, but the fixed extension diluted to 498 trades, CSV PF 1.0717, MT5 PF about 1.06, +$35.05 parsed / +$27.67 MT5 from 2020-2026 and failed 2018-2019 at 157 trades, CSV PF 0.9697, MT5 PF about 0.96, -$5.22 parsed / -$7.54 MT5. Verdict: `REJECT_MT5_THIN_EDGE_NO_TUNING` |
| MT5 M15 session-breakout frequency sweep | Broad raw M15 sweep across EURUSD/GBPUSD/USDJPY and four session variants found no new survivor. Known `USDJPY london120_break_m15` remained top in the current split at 278 trades / CSV PF 1.2973 / MT5 PF about 1.29 / +$98.05. The only new pocket, `EURUSD ny60_break_m15`, had 490 current trades / CSV PF 1.0706 / MT5 PF about 1.04 / +$45.83, then failed fixed 2020-2026 extension at 1532 trades / CSV PF 0.9654 / MT5 PF about 0.94 / -$79.73. Verdict: `REJECT_MT5_M15_SESSION_BREAKOUT_EXTENSION_FAIL_NO_TUNING` |
| MT5 extra-major M15 session-breakout sweep | Extra-major raw M15 sweep across AUDUSD/NZDUSD/USDCAD/USDCHF found one current pocket, `USDCHF asia_london_break_m15`: 365 trades / CSV PF 1.1332 / MT5 PF about 1.12 / +$71.43. Fixed 2020-2026 extension failed at 1432 trades / CSV PF 0.9595 / MT5 PF about 0.95 / -$87.14. Verdict: `REJECT_MT5_EXTRA_MAJOR_M15_EXTENSION_FAIL_NO_TUNING` |
| MT5 extra-major mean-reversion follow-up | Extra-major M30 short mean-reversion found one current pocket, `USDCAD rsi_extreme_fade_m30_short_rr0p80`: 394 trades / CSV PF 1.2147 / MT5 PF about 1.17 / +$33.53 from 2024-2026. Frozen unchanged 2020-2026 extension collapsed to 1357 trades / CSV PF 1.0004 / MT5 PF about 0.97 / +$0.30, with top-10-winner removal -$34.89 and worst 250-trade window -$51.55. Verdict: `REJECT_MT5_EXTRA_MAJOR_MEANREV_EXTENSION_FAIL_NO_TUNING` |
| MT5 USDJPY bond-vol actual cross-check | `usdjpy_h4_bond_vol_asia_session_carry_relief_v1`: frozen tester-only H4 EA run on actual MT5 Strategy Tester from 2018-01-01 through 2026-06-27 produced 79 trades, parsed CSV PF 1.7010, MT5 PF 1.68, +$79.04 parsed / +$77.37 MT5 at fixed 0.01 lots |
| MT5 USDJPY bond-vol robustness read | `WATCHLIST_ONLY_MT5_GATE_PASS_NO_DEMO_APPROVAL`; useful sparse clue, not a frequency/tuning candidate: 2020-2022 negative, 2025-2026 negative at 13 trades / PF 0.5618 / -$13.00, and top-10-winner removal leaves PF 1.0003 / +$0.03 |
| First-screen candidates | `4` |
| Second-pass candidates | `2` |
| Recent proxy stress candidates | `6` |
| Macro/rate candidates | `3` |
| CNY/dollar candidates | `2` |
| Calendar/session candidates | `2` |
| Weekly-structure candidates | `3 historical; 3 recent-stress; 0 survivors` |
| Financial/liquidity candidates | `2 historical; 2 recent-proxy; 0 survivors` |
| CFTC/COT positioning candidates | `2 historical; 2 recent-proxy; 0 survivors` |
| Global risk/credit candidates | `2` |
| Commodity/dollar candidates | `2` |
| Commodity/dollar recent stress | `2 candidates; 0 survivors` |
| Real-asset rotation candidates | `2 historical; 2 recent-stress; 0 survivors` |
| Haven/liquidity candidates | `2 historical; 2 recent-stress; 0 survivors` |
| Rates/dollar candidates | `3 historical; 3 recent-stress; 0 survivors` |
| Treasury curve candidates | `2 historical; 2 recent-proxy; 0 survivors` |
| Equity-leadership candidates | `2 historical; 2 recent-stress; 0 survivors` |
| Sector-rotation candidates | `2 historical; 2 recent-stress; 0 survivors` |
| Currency-basket candidates | `2 historical; 1 recent-stress due CYB unavailable; 0 survivors` |
| Bond-volatility candidates | `3 historical; 3 recent-stress; 0 survivors` |
| Crypto-risk candidates | `2 historical; 2 recent-stress; 0 survivors` |
| External flow candidates | `2` |
| Risk-regime candidates | `2` |
| FX-cross candidates | `2` |
| FX relative-strength candidates | `4 historical; 4 recent-proxy; 0 survivors` |
| Policy-uncertainty candidates | `4 historical; 4 recent-proxy; 0 survivors` |
| Short-rate differential candidates | `4 historical; 4 recent-proxy; 0 survivors` |
| Survivors | `0 demo-approved; 2 raw USDJPY MT5 diversification leads; 1 tuned USDJPY MT5 frequency lead; 1 sparse USDJPY MT5 bond-vol watchlist clue; 2 EURUSD MT5 watchlist-only leads; 1 rejected GBPUSD MT5 frequency extension; 1 rejected EURUSD M15 session-breakout extension; 1 rejected USDCHF extra-major M15 extension; 1 rejected USDCAD extra-major mean-reversion extension; 1 rejected D1 slow-book trend scout; 0 broad Forex survivors` |
| Demo-forward-test spec | `NOT_PREPARED_NO_SURVIVOR` |
| MT5 frequency status | `forex-research/docs/FOREX_MT5_FREQUENCY_STATUS_2026_07_04.md` |
| MT5 robustness report | `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.md` |
| MT5 tuned robustness report | `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md` |
| MT5 lead review response | `forex-research/docs/FOREX_MT5_FREQUENCY_LEAD_REVIEW_RESPONSE_2026_07_04.md` |
| MT5 portability review | `forex-research/docs/FOREX_MT5_FREQUENCY_PORTABILITY_REVIEW_2026_07_04.md`; frozen tuned rule failed on GBPUSD and USDJPY, no new candidate |
| MT5 M30 review prompt | `forex-research/docs/FOREX_MT5_M30_FREQUENCY_LEAD_REVIEW_PROMPT_2026_07_04.md` |
| MT5 M30 robustness report | `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M30_RSI_BB_LONG_BLOCKH6_7_10_13_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md` |
| MT5 USDJPY breakout review prompt | `forex-research/docs/FOREX_MT5_USDJPY_SESSION_BREAKOUT_REVIEW_PROMPT_2026_07_04.md` |
| MT5 USDJPY breakout review response | `forex-research/docs/FOREX_MT5_USDJPY_SESSION_BREAKOUT_REVIEW_RESPONSE_2026_07_04.md` |
| MT5 USDJPY breakout robustness report | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md` |
| MT5 USDJPY tuned M30 review prompt | `forex-research/docs/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_REVIEW_PROMPT_2026_07_04.md` |
| MT5 USDJPY tuned M30 robustness report | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.md` |
| MT5 USDJPY Asia-London M30 raw review prompt | `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_PROMPT_2026_07_04.md` |
| MT5 USDJPY Asia-London M30 raw review response | `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_RESPONSE_2026_07_04.md` |
| MT5 USDJPY Asia-London M30 robustness report | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md` |
| MT5 USDJPY Asia-London M30 blockh7 tuning report | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_BLOCKH7_TUNING_ROBUSTNESS_2026_07_04.md` |
| MT5 GBPUSD rejected M30 full extension | `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_GBPUSD_BB_WICK_RECLAIM_M30_RAW_EDGE.md` |
| MT5 GBPUSD rejected M30 pre-2020 extension | `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_GBPUSD_BB_WICK_RECLAIM_M30_RAW_EDGE.md` |
| MT5 M15 session-breakout current sweep | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.md` |
| MT5 EURUSD NY60 M15 rejected extension | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_EURUSD_NY60_M15_RAW_FREQ_EXTENSION.md` |
| MT5 extra-major M15 current sweep | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_EXTRA_MAJORS_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.md` |
| MT5 USDCHF Asia-London M15 rejected extension | `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_USDCHF_ASIA_LONDON_M15_RAW_FREQ_EXTENSION.md` |
| MT5 extra-major mean-reversion rejected extension | `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_EXTRA_MAJOR_MEANREV_EXTENSION_REJECT_2026_07_04.md` |
| MT5 USDJPY bond-vol review prompt | `forex-research/docs/FOREX_MT5_BOND_VOL_REVIEW_PROMPT_2026_07_04.md` |
| MT5 USDJPY bond-vol actual report | `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.md` |
| MT5 recent-12 frozen frequency gate report | `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_RECENT12_FROZEN_FREQUENCY_GATE_2026_07_04.md` |
| MT5 recent-12 frozen frequency gate daily CSV | `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_RECENT12_FROZEN_FREQUENCY_GATE_DAILY_2026_07_04.csv` |
| MT5 last-3M best-candidate manual P&L report | `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_LAST3M_BEST_CANDIDATES_MANUAL_PNL_2026_07_04.md` |
| MT5 last-3M best-candidate daily CSV | `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_LAST3M_BEST_CANDIDATES_DAILY_2026_07_04.csv` |
| Broker refresh spec | `forex-research/docs/FOREX_BROKER_DATA_REFRESH_SPEC_2026_07_03.md` |
| Independent review response | `forex-research/docs/FOREX_RESEARCH_LANE_REVIEW_RESPONSE_2026_07_03.md` |
| Broker refresh validator | `NO_REFRESH_FILES_FOUND` |
| Broker refresh frozen retest | `NO_VALIDATED_REFRESH_FILES` |
| Staleness caveat | `local Forex bars end around 2025-06/2025-07` |

MT5 frequency-first update: actual MT5 Strategy Tester found one raw-frequency EURUSD lead, `rsi_extreme_fade_m15_long_rr0p80`. A constrained bad-hour tune blocking only hours `1,7,21` improves the full run to PF `1.1705`, +`$108.84`, and a lower max trade-curve DD of `$32.72`, but it remains too thin for deployment: the 2022-2024 split is only PF `1.0875`, only `27/49` active months are positive, and a 250-trade rolling stretch from `2025-07-07` to `2026-03-18` is still PF `0.8131` / `-$25.78`. Status is `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`, no Forex demo-forward spec.

MT5 recent-12 frozen frequency gate: after the review, three existing watchlist rules were rerun unchanged in actual MT5 Strategy Tester for `2025-07-01 -> 2026-07-03`, then manually recalculated from trade CSVs. EURUSD M30 RSI+BB tuned stayed positive but too thin: 242 trades, WR `57.02%`, PF `1.1254`, +`$16.87`, and top-10-winner removal flips to `-$3.67`. EURUSD M15 RSI extreme tuned failed recent recency outright: 366 trades, WR `52.46%`, PF `0.9078`, `-$16.92`. USDJPY London60 M30 blockh7/11 tuned was positive but also thin: 193 trades, WR `50.26%`, PF `1.0997`, +`$20.81`, and top-10-winner removal flips to `-$27.47`. This confirms no current Forex candidate is demo-ready; next work should be a genuinely new MT5-tested mechanism or an alternate-broker/custom-symbol replay, not more tuning from these same diagnostics. Report: `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_RECENT12_FROZEN_FREQUENCY_GATE_2026_07_04.md`.

MT5 last-3M manual P&L audit: the owner asked for Forex-only last-three-month results with manual P&L rather than MT5 summary totals. Using actual MT5 trade CSVs and entry dates `2026-04-01 -> 2026-07-03`, the best result is only `USDJPY asia_london_break_m30` at 31 trades, WR `48.39%`, PF `1.2924`, +`$8.69`. `USDJPY london120_break_m15_d1atr20_guard` is positive but low-sample at 17 trades, WR `58.82%`, PF `1.5180`, +`$6.33`; `EURUSD rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80` is barely positive at 69 trades, PF `1.0875`, +`$2.92`; `USDJPY london60_break_m30_blockh7_11_rr1` and `EURUSD rsi_extreme_fade_m15_long_blockh1_7_21_rr0p80` are negative. The small dollar P&L is not caused by leverage being absent: these runs are fixed `0.01` lot, and leverage only changes margin, not fixed-lot P&L. Report: `forex-research/outputs/reports/mt5_backtests/FOREX_MT5_LAST3M_BEST_CANDIDATES_MANUAL_PNL_2026_07_04.md`.

MT5 D1 slow-book trend scout: a deliberately different daily trend-following branch was added with tester-only `ForexDailyTrendScout.mq5` and runner `forex-research/scripts/run_forex_mt5_daily_trend_scout.py`. Smoke compile passed after replacing `TimeHour` with `TimeToStruct`-based hour extraction. The single raw actual-MT5 screen across EURUSD/GBPUSD/USDJPY/AUDUSD/NZDUSD/USDCAD/USDCHF from `2024-07-01` through `2026-07-03` rejected the branch: all rows were low-frequency, and the best manual result was EURUSD at 15 trades, PF `0.9936`, -`$0.65` with MT5 PF `0.85`; GBPUSD was worst at 19 trades, PF `0.2034`, -`$159.22`. Verdict: `REJECT_MT5_D1_TREND_SLOW_BOOK_NO_EDGE`; no tuning, no full-window extension, and no Forex demo-forward spec. Report: `forex-research/outputs/reports/mt5_backtests/daily_trend_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_D1_TREND_SLOW_BOOK_RAW.md`.

MT5 lead review response: `forex-research/docs/FOREX_MT5_FREQUENCY_LEAD_REVIEW_RESPONSE_2026_07_04.md` confirms no blocker to watchlist status, but blocks demo-forward because the hour filter is post-hoc against the full raw sample, the edge remains thin, and rolling-window weakness persists.

MT5 portability review: `forex-research/docs/FOREX_MT5_FREQUENCY_PORTABILITY_REVIEW_2026_07_04.md` replayed the frozen tuned rule on GBPUSD and USDJPY with no symbol-specific tuning. Portability failed: GBPUSD full PF `0.9597` / `-$38.75`, GBPUSD current PF `0.8959` / `-$48.15`, USDJPY full PF `0.8838` / `-$122.40`, USDJPY current PF `0.8128` / `-$102.23`. The lead is EURUSD-only and not yet a portfolio-diversifying Forex strategy.

MT5 M30 frequency-first update: actual MT5 Strategy Tester found a stronger EURUSD-only packet, `rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80`. Raw M30 full result was 1145 trades, CSV PF `1.1301`, MT5 PF about `1.11`, +`$90.57`. The only tune blocked hours `6,7,10,13`, selected from the older 2022-2024 split and checked on 2024-2026 validation. Tuned full result is 831 trades, CSV PF `1.2325`, MT5 PF about `1.20`, +`$114.80`; tuned splits are 2022-2024 PF `1.1585` / +`$40.57` and 2024-2026 PF `1.3123` / +`$74.23`. Robustness is improved but not demo-grade: `36/49` positive months, worst 250-trade rolling window PF `0.9765` / `-$3.62`, top-10-winner removal PF `1.1641` / +`$80.99`; however worst 100/150-trade windows are negative, top-50-winner removal is negative, and frozen GBPUSD/USDJPY portability failed. Status remains watchlist-only, no Forex demo-forward spec.

MT5 USDJPY session-breakout update: a fresh actual-MT5 family added `ForexSessionBreakoutScout.mq5`, guarded to Strategy Tester only. The raw lead is `USDJPY london120_break_m15`: 06:00-08:00 broker-server range, trade M15 breaks from 08:00 for four hours, both directions, RR `1.00`, no post-discovery tuning. Full 2022-2026 result is 521 trades, CSV PF `1.3917`, MT5 PF about `1.38`, +`$232.03`; same-rule 2020-2026 extension is 859 trades, CSV PF `1.3028`, MT5 PF about `1.28`, +`$289.44`. Every 2020-2026 entry-date year is positive and both directions are positive over the full extension, but pre-2022 shorts are slightly negative, 2021-H2 and 2024-H1 are weak, short rolling windows remain negative, and top-75/top-100-winner removal flips negative. This is the best diversification evidence so far, but still watchlist-only and not demo-forward. No Forex demo-forward spec.

MT5 USDJPY M30 frequency-tuning update: following the user's instruction to chase frequency first and tune only after raw evidence, a fresh M30 session-breakout screen found `USDJPY london60_break_m30`. The raw candidate held over 2020-2026 at 1560 trades, CSV PF `1.1271`, MT5 PF about `1.12`, +`$214.98`; GBPUSD and EURUSD M30 raw standouts failed their 2020-2026 extensions. A constrained hour-block tune on USDJPY blocked entry hours `7` and `11` and kept RR `1.00`, improving full 2020-2026 to 1227 trades, CSV PF `1.2062`, MT5 PF about `1.19`, +`$278.20`, while also confirming on 2024-2026 at 384 trades, CSV PF `1.2057`, MT5 PF about `1.20`, +`$94.87`. RR `1.50` was rejected despite a better full-window number because it weakened to PF `1.0680` in the recent window. Frozen same-rule portability failed on EURUSD and GBPUSD: full 2020-2026 EURUSD PF `0.9992` / -`$1.47`, full GBPUSD PF `0.9474` / -`$121.36`, recent EURUSD PF `0.9509` / -`$26.81`, and recent GBPUSD PF `0.9967` / -`$2.04`. Status is `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_DIVERSIFICATION_LEAD`, not demo-forward, because the hour filter is post-hoc, portability failed, 2023 is negative, 2023-H1 is materially negative, full-history rolling windows remain negative, and top-winner removal exposes fragility. Review prompt: `forex-research/docs/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_REVIEW_PROMPT_2026_07_04.md`. Robustness packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.md`.

MT5 USDJPY Asia-London M30 raw update: continuing frequency-first before tuning, actual MT5 Strategy Tester extended `USDJPY asia_london_break_m30` unchanged. It uses the broker-server 00:00-06:00 Asia range and trades M30 breakouts from 07:00 for four hours, both directions, RR `1.00`. Results are positive in both major windows: 2018-2019 has 207 trades, CSV PF `1.1996`, MT5 PF about `1.17`, +`$54.04` parsed / +`$46.56` MT5; 2020-2026 has 721 trades, CSV PF `1.1564`, MT5 PF about `1.14`, +`$179.97` parsed / +`$161.13` MT5; full 2018-2026 has 928 trades, CSV PF `1.1646`, MT5 PF about `1.14`, +`$234.01` parsed / +`$207.69` MT5. It is cleaner than `london120_break_m30`, which failed 2018-2019, but still watchlist-only: 2021 and 2023 are negative, only `58/102` active months are positive, worst 250-trade rolling window is PF `0.9142` / -`$30.37`, and top-50-winner removal flips to PF `0.9527` / -`$67.27`. Review prompt: `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_PROMPT_2026_07_04.md`. Robustness packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`.

MT5 USDJPY Asia-London M30 tuning update: local review response `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_RESPONSE_2026_07_04.md` allowed one constrained tuning pass, designed only from 2018-2023 raw trades. The pre-declared rule selected only broker-server entry hour `7`. The tune is rejected: design improved from raw 676 trades / PF `1.1450` / +`$143.85` parsed to 627 trades / PF `1.1678` / +`$156.34` parsed, but validation worsened from raw 252 trades / PF `1.2100` / +`$90.16` parsed to 232 trades / PF `1.1750` / +`$70.37` parsed. Full 2018-2026 also worsened by net/trade count: raw 928 trades / PF `1.1646` / +`$234.01` parsed versus blockh7 859 trades / PF `1.1700` / +`$226.71` parsed. Status is `TUNE_REJECT_KEEP_RAW_WATCHLIST_PREFERRED`; keep raw preferred, no more tuning and no Forex demo-forward spec. Tuning report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_BLOCKH7_TUNING_ROBUSTNESS_2026_07_04.md`.

MT5 GBPUSD M30 wick-reclaim extension: actual MT5 Strategy Tester extended `GBPUSD bb_wick_reclaim_m30_rr0p80` before any tuning. The current 2024-2026 pocket had looked interesting at 156 trades, CSV PF `1.1731`, MT5 PF about `1.15`, +`$23.70`, but the fixed 2020-2026 extension diluted to 498 trades, CSV PF `1.0717`, MT5 PF about `1.06`, +`$35.05` parsed / +`$27.67` MT5, and the standalone 2018-2019 extension failed at 157 trades, CSV PF `0.9697`, MT5 PF about `0.96`, -`$5.22` parsed / -`$7.54` MT5. Verdict is `REJECT_MT5_THIN_EDGE_NO_TUNING`; no demo-forward spec.

MT5 M15 session-breakout frequency sweep: actual MT5 Strategy Tester ran a broad raw M15 sweep across EURUSD/GBPUSD/USDJPY and four session variants with no blocked hours, no RR edits, and no direction mining. The known `USDJPY london120_break_m15` stayed top in the current split at 278 trades, CSV PF `1.2973`, MT5 PF about `1.29`, +`$98.05`. The only new current-window pocket worth extending was `EURUSD ny60_break_m15` at 490 trades, CSV PF `1.0706`, MT5 PF about `1.04`, +`$45.83`; its fixed 2020-2026 extension failed at 1532 trades, CSV PF `0.9654`, MT5 PF about `0.94`, -`$79.73`. Verdict is `REJECT_MT5_M15_SESSION_BREAKOUT_EXTENSION_FAIL_NO_TUNING`; no new candidate and no demo-forward spec.

MT5 extra-major M15 session-breakout sweep: actual MT5 Strategy Tester probed AUDUSD/NZDUSD/USDCAD/USDCHF because the isolated tester had tick/history traces for those pairs. The only current-window pocket was `USDCHF asia_london_break_m15`: 365 trades, CSV PF `1.1332`, MT5 PF about `1.12`, +`$71.43`. The fixed 2020-2026 extension failed at 1432 trades, CSV PF `0.9595`, MT5 PF about `0.95`, -`$87.14`. Verdict is `REJECT_MT5_EXTRA_MAJOR_M15_EXTENSION_FAIL_NO_TUNING`; no new candidate and no demo-forward spec.

MT5 extra-major mean-reversion follow-up: a bounded broad pass across AUDUSD/NZDUSD/USDCAD/USDCHF mean-reversion was narrowed to M30 short-side fades after the broad run proved slow and the completed AUDUSD rows were weak. The only current-window pocket was `USDCAD rsi_extreme_fade_m30_short_rr0p80`: 394 trades, CSV PF `1.2147`, MT5 PF about `1.17`, +`$33.53`. The frozen no-parameter-change 2020-2026 extension failed: 1357 trades, CSV PF `1.0004`, MT5 PF about `0.97`, +`$0.30`; top-10-winner removal flips to `-$34.89`, and the worst 250-trade window is PF `0.7381` / `-$51.55`. Verdict is `REJECT_MT5_EXTRA_MAJOR_MEANREV_EXTENSION_FAIL_NO_TUNING`; do not tune this USDCAD pocket and no Forex demo-forward spec.

MT5 USDJPY bond-vol actual-MT5 cross-check: the frozen sparse H4 clue `usdjpy_h4_bond_vol_asia_session_carry_relief_v1` was run in actual MT5 Strategy Tester with the tester-only `ForexBondVolAsiaCarryReliefV1.mq5` EA and lagged MOVE context through `2026-06-27`. Full 2018-2026 result is 79 trades, parsed CSV PF `1.7010`, MT5 PF `1.68`, +`$79.04` parsed / +`$77.37` MT5, equity DD max `$37.68`. This keeps the clue alive as `WATCHLIST_ONLY_MT5_GATE_PASS_NO_DEMO_APPROVAL`, but it is not a frequency/tuning candidate: 2020-2022 is negative, 2025-2026 is negative at 13 trades / PF `0.5618` / -`$13.00`, and top-10-winner removal leaves PF `1.0003` / +`$0.03`. Review prompt: `forex-research/docs/FOREX_MT5_BOND_VOL_REVIEW_PROMPT_2026_07_04.md`. Actual report: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.md`.

First-screen verdicts: `eurusd_h4_compression_breakout_v0` PF `0.9887` / `-0.57R`; `eurusd_h1_london_asia_range_breakout_v0` PF `0.9535` / `-88.78R`; `usdjpy_h4_trend_continuation_pullback_v0` PF `1.0159` / `+7.77R` with `48.56R` DD and Pepperstone failure; `usdjpy_h1_tokyo_range_failed_break_v0` PF `0.8148` / `-249.96R`.

Useful clue only: USDJPY H4 long-only Asia/NY-morning diagnostic was PF `1.2844` / `+48.81R` overall but failed Pepperstone 2019-2021, so it requires a new pre-registered carry-regime hypothesis and fresher data before any forward-test package.

Second-pass verdicts: `usdjpy_h4_carry_session_pullback_v1` improved to PF `1.0878` / `+20.58R`, but failed the stricter gate with `27.41R` DD, negative Pepperstone (`-11.67R`, PF `0.7124`), and negative pre-2022 performance (`-1.94R`, PF `0.9817`). `eurusd_h4_range_rejection_reversion_v0` failed at PF `0.9653` / `-5.78R`. No Forex demo-forward spec is prepared.

Recent proxy stress: public Yahoo H1 proxy bars were acquired for `EURUSD`, `GBPUSD`, and `USDJPY` from `2025-07-01` through `2026-07-03`; this is not broker-authoritative and uses historical Capital.com spread proxies. USDJPY carry/session failed the recent proxy window (`41` trades, PF `0.6647`, `-8.11R`). EURUSD H4 range rejection had only a low-sample pocket (`17` trades, PF `1.1655`, `+1.19R`) and is not a survivor.

Macro/rate screen: lagged FRED real-yield plus broad-dollar context produced one historical lead, `eurusd_h4_real_yield_dollar_pressure_reversal_v0` (`147` historical trades, PF `1.3882`, `+23.47R`), but recent proxy confirmation was only `2` trades with PF `0.7486`, so the final gate is `REJECT_MACRO_RECENT_LOW_SAMPLE`. The EURUSD and USDJPY macro follow-through variants were weak historically. No Forex demo-forward spec is prepared.

CNY/dollar screen: lagged FRED USD/CNY plus broad-dollar context was tested on EURUSD/USDJPY H4. `eurusd_h4_cny_dollar_pressure_pullback_v0` failed at PF `0.9339` / `-18.75R` with only `13` recent proxy trades at PF `0.5126`; `usdjpy_h4_cny_shock_yen_reversion_v0` was low-sample and negative at `73` trades, PF `0.6335`, `-17.07R`. No CNY/dollar survivor.

Calendar/session screen: price-only EURUSD NY-fix H1 reversion and USDJPY H4 month-turn carry-pullback hypotheses were tested. `eurusd_h1_ny_fix_overextension_reversion_v0` failed at PF `0.8861` / `-115.38R` and recent proxy PF `0.6064`; `usdjpy_h4_month_turn_carry_pullback_v0` failed at PF `0.8611` / `-23.01R` and recent proxy PF `0.7400`. No calendar/session survivor.

Weekly-structure screen: price-only prior-week range/open-state hypotheses were tested on EURUSD/USDJPY H4. All three were rejected historically: EURUSD prior-week liquidity reversion PF `0.6611` / `-12.56R`, USDJPY weekly carry continuation PF `0.9569` / `-6.73R` with `31.79R` DD and broker instability, and EURUSD weekly-open reversion PF `0.8191` / `-65.04R`. Recent public FX proxy stress was also weak/low-sample: `3`, `19`, and `35` trades respectively, all final-gated below survivor status. No weekly-structure survivor and no demo-forward spec.

Financial/liquidity screen: lagged FRED NFCI, ANFCI, and WALCL context was tested on EURUSD/USDJPY H4 with a conservative seven-day availability lag. Both candidates were rejected for low historical sample and no recent proxy trades: EURUSD `33` trades, PF `0.8054`, `-3.68R`; USDJPY `16` trades, PF `1.0367`, `+0.29R`, top-winner-removed negative. No financial/liquidity survivor and no demo-forward spec.

CFTC/COT positioning screen: official CFTC Traders in Financial Futures futures-only archives were acquired for `2016-2026`, with Euro FX and Japanese Yen leveraged-money positioning shifted by a conservative seven-day availability lag. Both H4 reversal candidates were rejected for low historical sample and zero recent proxy trades: EURUSD `54` trades, PF `0.7354`, `-8.51R`; USDJPY `11` trades, PF `1.3561`, `+1.88R`. No COT survivor and no demo-forward spec.

Global risk/credit screen: lagged EEM/SPY and HYG/IEF ETF ratios were tested on EURUSD/USDJPY H4. `eurusd_h4_global_risk_dollar_beta_pullback_v0` failed at only `76` trades, PF `0.4461`, `-28.02R`; `usdjpy_h4_global_risk_credit_pullback_v0` was a tiny positive clue at `43` trades, PF `1.1682`, `+3.50R`, but is rejected for low sample, low frequency, and stale reference data. No global-risk/credit survivor.

Commodity/dollar screen: lagged DBC/UUP and DBB/UUP ETF ratios were tested on EURUSD/USDJPY H4. `eurusd_h4_commodity_dollar_reflation_pullback_v0` failed historically at PF `0.8911` / `-13.44R`; `usdjpy_h4_commodity_dollar_reflation_pullback_v0` was the cleanest positive historical external-reference clue at `64` trades, PF `1.5453`, `+14.45R`, but recent public DBC/DBB/UUP proxy stress through `2026-07-02` did not confirm it. Recent USDJPY stress had only `6` trades, PF `0.8725`, `-0.39R`; EURUSD stress had `8` trades, PF `0.0000`, `-8.18R`. No commodity/dollar survivor.

Real-asset rotation screen: lagged USO/UUP, HG/GC, and SLV/GLD ETF/futures ratios were tested on EURUSD/USDJPY H4. `eurusd_h4_real_asset_reflation_pullback_v0` failed at `107` trades, PF `0.8384`, `-10.15R`; `usdjpy_h4_real_asset_carry_pullback_v0` was mildly positive at `112` trades, PF `1.1465`, `+8.00R`, but failed the PF gate and Pepperstone was negative. Recent public proxy stress through `2026-07-02/03` produced zero EURUSD trades and only `6` USDJPY trades, PF `0.8737`, `-0.39R`. No real-asset rotation survivor.

Haven/liquidity screen: lagged GLD, GDX/GLD, SPY/TLT, and XLU/XLK ETF context was tested on EURUSD/USDJPY H4. `usdjpy_h4_haven_liquidity_yen_pullback_v0` failed historically at `129` trades, PF `0.8966`, `-7.09R`; `eurusd_h4_haven_liquidity_dollar_pullback_v0` failed at `193` trades, PF `0.9041`, `-9.50R`. Recent public proxy stress through `2026-07-02` was only `8` USDJPY trades, PF `1.4047`, `+1.25R`, and `3` EURUSD trades, PF `0.8986`, `-0.15R`; both final-gated `RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR`. No haven/liquidity survivor.

Rates/dollar screen: lagged TLT/UUP and TLT/SHY ETF ratios were tested on EURUSD/USDJPY H4. The v0 candidates failed: EURUSD duration pullback PF `1.0664` / `+18.16R`, USDJPY yield pullback PF `0.8938` / `-24.98R`. A separate EURUSD short-session v1 is historical watchlist-only at `295` trades, PF `1.2258`, `+29.97R`, but recent public proxy stress through `2026-07-02` is only `9` trades, PF `2.5920`, `+4.89R`, so the final gate is `RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR`. No rates/dollar survivor and no demo-forward spec.

Treasury curve screen: lagged FRED DGS2, DGS10, and T10Y2Y context was tested on EURUSD/USDJPY H4. USDJPY front-end pullback had `83` historical trades, PF `0.8635`, `-6.24R`, and failed historical edge; EURUSD dollar-pressure pullback had `68` trades, PF `0.9078`, `-3.36R`, and failed low sample. Recent public FX proxy stress produced one losing trade per candidate. No Treasury curve survivor and no demo-forward spec.

Equity-leadership screen: lagged ACWX/SPY, IWM/SPY, and XLF/XLU ETF ratios were tested on EURUSD/USDJPY H4. Both historical candidates failed: EURUSD ex-US leadership pullback PF `0.8534` / `-54.47R`, USDJPY US cyclical leadership pullback PF `0.8661` / `-14.47R`. Recent public proxy stress through `2026-07-02` was slightly positive but only `9` trades per candidate, with final gates `RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR`. No equity-leadership survivor and no demo-forward spec.

Bond-volatility screen: lagged MOVE Treasury-rate volatility context was tested on EURUSD/USDJPY H4. The broad v0 candidates failed: EURUSD PF `0.9627` / `-6.94R`, USDJPY PF `1.0819` / `+7.24R`. A separate USDJPY Asia-session v1 is historically strong at `125` trades, PF `2.0645`, `+48.23R`, with all broker splits positive, but recent public MOVE/FX proxy stress through MOVE `2026-06-26` is only `7` trades, PF `0.3170`, `-2.98R`, so the final gate is `RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR`. No bond-vol survivor and no demo-forward spec.

Crypto-risk screen: lagged BTC-USD context was tested on EURUSD/USDJPY H4. Both historical candidates failed: EURUSD BTC risk-beta pullback had `253` trades, PF `0.8955`, `-13.03R`; USDJPY BTC risk carry pullback had `122` trades, PF `0.9345`, `-4.10R`. Recent public BTC/FX proxy stress through BTC `2026-07-03` was only `3` and `1` trades, final-gated `RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR`. No crypto-risk survivor and no demo-forward spec.

Sector-rotation screen: lagged XLY/XLP, QQQ/SPY, XLE/XLU, XLI/XLU, XME/SPY, and TIP/IEF ETF ratios were tested on EURUSD/USDJPY H4. `eurusd_h4_sector_growth_rotation_pullback_v0` was mildly positive at `293` trades, PF `1.1123`, `+15.53R`, but failed the PF gate and broker stability; `usdjpy_h4_sector_cyclical_carry_pullback_v0` failed at `183` trades, PF `0.8338`, `-17.51R`. Recent public sector ETF/FX proxy stress through `2026-07-02` was only `12` and `4` trades, final-gated `RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR`. No sector-rotation survivor and no demo-forward spec.

Currency-basket screen: lagged FXA/UUP, FXF/UUP, and CYB/UUP ETF ratios were tested on EURUSD/USDJPY H4. `eurusd_h4_currency_basket_dollar_pressure_pullback_v0` failed at `752` trades, PF `0.7531`, `-103.29R`; `usdjpy_h4_safe_haven_currency_rotation_pullback_v0` was only a low-sample historical clue at `32` trades, PF `2.5935`, `+14.89R`. Recent Yahoo acquisition returned no usable `CYB` rows, so only the USDJPY candidate was stressed; it produced `1` losing trade, PF `0.0000`, `-1.03R`. No currency-basket survivor and no demo-forward spec.

External flow screen: lagged FXE/UUP and inverted FXY/UUP daily ETF relative-flow proxies were tested on EURUSD/USDJPY H4. `eurusd_h4_currency_etf_flow_pullback_v0` failed at PF `0.8008` / `-87.77R`; `usdjpy_h4_currency_etf_flow_pullback_v0` failed at PF `0.9474` / `-12.53R`. No external-flow survivor.

Risk-regime screen: lagged FRED VIX/VXV context was tested on EURUSD/USDJPY H4. `eurusd_h4_vix_vxv_risk_regime_pullback_v0` failed at PF `0.8816` / `-18.96R`; `usdjpy_h4_vix_vxv_risk_regime_pullback_v0` failed at PF `0.9814` / `-2.39R`, with only tiny negative recent proxy samples. No risk-regime survivor.

FX-cross screen: lagged AUDJPY/USDJPY and EURJPY/USDJPY daily FX proxy ratios were tested. `usdjpy_h4_audjpy_cross_risk_rotation_pullback_v0` was a weak positive clue at PF `1.0822` / `+5.66R`, but below the PF/frequency/watchlist bar; `eurusd_h4_eurjpy_cross_confirmation_pullback_v0` failed at PF `0.7325` / `-99.43R`. No FX-cross survivor.

FX relative-strength screen: same-time EURUSD/USDJPY USD-pressure agreement was tested with H1 lagging-pair catch-up and H4 dispersion-reversal hypotheses. All four candidates were rejected historically: EURUSD H1 catch-up PF `0.9763` / `-12.23R`; USDJPY H1 catch-up PF `0.9172` / `-37.94R`; EURUSD H4 dispersion reversal PF `0.8424` / `-20.14R`; USDJPY H4 dispersion reversal PF `0.8358` / `-24.07R`. Recent public FX proxy stress had weak H1 results and only tiny H4 pockets, including USDJPY H4 `13` trades at PF `1.6342`, which is low-sample and not a survivor.

Policy-uncertainty screen: lagged FRED USEPUINDXD was tested as a US policy-stress/relief regime on EURUSD/USDJPY H4/H1. EURUSD H4 dollar-haven reversal was the best new clue at `367` historical trades, PF `1.0998`, `+17.57R`, and `23.85R` max DD, but it failed the edge/drawdown gate and recent proxy stress had only `4` trades at PF `1.1933`. USDJPY H4 was negative at PF `0.8786` / `-17.94R`; EURUSD H1 was PF `0.9260` / `-26.00R`; USDJPY H1 was PF `0.9730` / `-5.85R`. No policy-uncertainty survivor and no demo-forward spec. Review caveat: `policy_available_utc = observation + 1 day` is acceptable for rejection evidence only; any EPU watchlist/promotion attempt must be rerun with a `5`-day availability lag and revision-robustness check.

Short-rate differential screen: FRED Fed funds (`DFF`), ECB deposit facility (`ECBDFR`), and Japan call-rate (`IRSTCI01JPM156N`) context was tested with explicit availability lags. All four candidates were rejected historically: EURUSD H4 failed-break reversal PF `0.9416` / `-21.12R`; EURUSD H1 session reversion PF `0.8242` / `-130.49R`; USDJPY H4 carry pullback PF `0.6932` / `-38.14R`; USDJPY H1 session carry PF `0.8801` / `-25.28R`. Recent public FX proxy stress also failed or stayed low-sample, including the only positive recent pocket, USDJPY H4, at only `19` trades with top-winner-removed net negative. No short-rate differential survivor and no demo-forward spec.

Independent review response: `FOREX_RESEARCH_LANE_INDEPENDENT_REVIEW_2026_07_03.md` confirmed the methodology, no-survivor verdict, no-demo-spec decision, and runtime isolation. Action accepted: broaden broker-refresh scope, keep watchlist definitions frozen, demote USDJPY bond-vol v1 expectations because it came after within-family iteration, and require export provenance plus file hashes for refreshed broker data.

Broker refresh requirement: priority 1 is Capital.com EURUSD and USDJPY H1/H4 from `2022-01-01` through current with measured/exported spread and terminal/account provenance, stored under `forex-research/data/broker_refresh/raw/<broker>/<symbol>/<timeframe>/`. Passing the refresh gates would only move the frozen EURUSD macro, frozen EURUSD rates/dollar, or frozen USDJPY bond-vol v0/v1 clues to `WATCHLIST_ONLY`, not demo approval.

Broker refresh validation: `python forex-research\scripts\run_forex_research_lane.py broker-refresh-validate` is implemented and currently reports `NO_REFRESH_FILES_FOUND`; when files exist it records raw/normalized SHA256s and export provenance status in the validation report.

Broker refresh frozen retest: `python forex-research\scripts\run_forex_research_lane.py broker-refresh-retest` is implemented and currently reports `NO_VALIDATED_REFRESH_FILES`. It will retest only the frozen EURUSD macro, EURUSD rates/dollar, and USDJPY bond-vol v0/v1 families from validated broker-refresh CSVs; a pass is still `WATCHLIST_ONLY`, not demo approval.

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
