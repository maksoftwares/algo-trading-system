# EURUSD regime specialists v1

This package tests the Gold-style trajectory on EURUSD: causal market regimes, exclusive specialist ownership, and a portfolio composed only from specialists that survive frozen chronological and cost gates.

Outcome-locked causal experiments and one intentionally contaminated control were run:

1. M30-only seed: stopped before P&L because its opportunity census failed.
2. M15/M30 two-clock ensemble: passed capacity, but every specialist failed admission after exact-cost backtesting.
3. A 1.50R/12-hour asymmetric exit: realized payoff reached 1.428 overall and 1.454 in the latest six months, but full-history win rate was only 38.75% and PF was 0.904.
4. M15 exhaustion plus M5 structure confirmation: capacity passed at 2.10 signals/day, but full-history win rate fell to 37.15% and PF to 0.841. The price-confirmation family is closed.
5. DXY-confirmed London and New York session handoffs: capacity passed at 0.254 signals/weekday, but full-history win rate was 33.87% and PF was 0.744. The cross-asset continuation family is closed.
6. Gold-style retrospective selection: the dense perfect-foresight oracle reached exactly 4.00 trades on every one of 1,954 archived weekdays (7,816 trades) with 100% wins by scanning future long/short paths from M5 entries. Its average winner was 1.475R and PF is infinite because every loss was deleted. This is direct path leakage, not a strategy.
7. Regime 1 Neutral causal reconstruction: four rule families, regularized bar models, synchronized GBPUSD/USDJPY features, constrained nonlinear models, raw EURUSD tick microstructure, and volatility-scaled risk were preregistered and tested chronologically. None qualified development or passed the forward gates. The best isolated year was tick microstructure in 2023 at PF 1.079; it collapsed afterward. Regime 1 remains cash.
8. Frozen July prospective diagnostic: the rejected volatility-scaled tick model was locked before bulk July acquisition and run without retuning. It produced 19 trades, 31.58% wins, 1.459 payoff, PF 0.673, and -4.317R. Both the 100-trade/60-day sample gate and the metric gate failed, so the result cannot admit or rescue the model.
9. Direct causal oracle imitation: a purged five-minute classifier learned meaningful entry resemblance (23.03% exact precision and 27.52% recall), but this was mostly the oracle's midnight scan artifact. Its 1,246 chronological trades won 31.54%, returned PF 0.654, and lost 306.20R. Every forward year failed.
10. Synchronous DXY/Treasury oracle imitation: 18 completed M5 cross-asset features raised exact-match precision only to 24.76% while recall fell to 15.15%. Its 638 chronological trades won 30.56%, returned PF 0.633, and lost 166.43R. Every forward year failed, so this quoted-cross-asset extension is closed.
11. Deterministic UTC-open cross-market vote: one Neutral trade per date used completed EURUSD, EURGBP, EURJPY, and bounded prior-session DXY returns. It achieved 31.11% exact precision and 51.11% same-side precision within 15 minutes, but its 135 forward trades returned PF 0.650 and lost 33.40R. All 42 exact members won and all 93 nonmembers lost, proving that this midnight task reduces directly to selecting the future-winning side. The route is closed without retuning.
12. Official CFTC Euro FX participant flow: conservatively released weekly leveraged-fund, asset-manager, and inverse-dealer changes produced 241 balanced candidates. Forward exact precision improved to 34.31%, but 102 trades returned PF 0.752 and lost 17.05R. Only 2025 passed; 2026 H1 collapsed to 13.33% wins and PF 0.221. Weekly aggregate positioning is closed without retuning.
13. Official CFTC options-equivalent flow: paired futures-only and futures-and-options-combined participant positions changed 46.47% of the futures-flow directions. The 102 forward trades nevertheless finished with the same 35 winners, 34.31% precision, PF 0.752, and -17.05R. No year passed. Free aggregate options delta is closed without post-outcome unanimous-vote selection.
14. Official CME EUR/USD strike surface: the exact `EOD_XCME_EUU_OPT_0` dataset and its 71-column schema were validated. A non-tuned 25-delta risk-reversal parser and signal were frozen, including put-call-parity and Black-76 fallbacks. The required 2019-2026 EOD history is not locally entitled; CME lists complete history at USD 2,249, while the free Daily Bulletin retains only the latest day.
15. Free official CME SPAN route: DataMine's `SPAN_ALL_GRP_EXCG` archive was verified at USD 0.00 with coverage from 2021-11-19. Its public PA2/XML sample contains the exact `EUU` long-dated EUR/USD options product, 20 expiries, and 2,562 contracts. The sample was downloaded and a settlement-only parser now feeds the frozen risk-reversal builder. The user's signup was stopped by missing OTP delivery; the legacy archive exposes indexes but blocks anonymous binary retrieval, so no historical options backtest was run.
16. Price-only Neutral session OCO: four fixed UTC anchors let the first executable side of a two-sided breakout select direction without option data. The frozen rule produced 1,790 trades, 24.25% wins, 1.293 payoff, PF 0.414, and -895.98R. The latest six months produced 122 trades, 23.77% wins, PF 0.414, and -60.65R. This exact fallback is closed without repair.
17. Exchange-traded participation: prior-session Euro FX futures direction was required to agree with inverse UUP direction, with both volume ratios above their preceding 20-session medians. The frozen rule produced 227 trades, 31.72% wins, 1.439 payoff, PF 0.668, and -52.70R. The latest six months produced 18 trades, 16.67% wins, PF 0.288, and -10.95R. This exact fallback is closed.
18. Official OCC FXE customer flow: a login-free OCC batch query supplied prior-day customer call and put volumes. The frozen normalized imbalance rule produced 78 trades, 38.46% wins, 1.439 payoff, PF 0.899, and -4.95R. The latest six months produced 21 trades, 38.10% wins, PF 0.886, and -1.53R. An isolated profitable eight-trade quarter was not selected; the full rule is closed.
19. Public DTCC OTC options flow: 674 credential-free CFTC public-dissemination queries supplied executed EUR/USD vanilla calls and puts. The frozen standalone 7-90 day notional-plus-premium imbalance produced 66 trades, 24.24% wins, 1.439 payoff, PF 0.460, and -27.65R. The latest six months produced 39 trades, 25.64% wins, PF 0.496, and -14.98R. The direction is not reversed after outcome inspection.
20. Matched DTCC premium skew: standalone OTM calls and puts were paired on tenor and absolute moneyness using only M5 spot completed before execution. The frozen normalized premium-skew rule produced 48 trades, 35.42% wins, 1.439 payoff, PF 0.789, and -6.70R. Development reached PF 1.119 but both forward quarters failed; the latest six months returned PF 0.654 and -7.80R. The exact surface is closed.
21. Four-session opening drive: the fully completed first 30-minute bar at each six-hour UTC anchor selected direction before entry. The frozen rule produced 593 trades, 32.04% wins, 1.432 payoff, PF 0.675, and -134.20R. PF improved monotonically across windows and reached 0.957 in the latest six months, but never crossed break-even. Its planned post-lock watchlist was cancelled with zero observations.
22. Midnight dual-side pairs: independent long and short tickets were retained at both 00:00 and 00:05 UTC on every Neutral-owned weekday, guaranteeing exactly four causal tickets per eligible day without direction prediction. The frozen rule produced 2,620 trades, 31.56% wins, 1.433 payoff, PF 0.661, and -625.38R. One-winner pairs earned only about +0.45R while no-winner pairs lost about -2.05R. The latest six months produced 156 tickets, 27.56% wins, PF 0.547, and -52.43R. This hedge-mode route is closed.
23. Four-clock paired side ranker: a purged L2 model learned LONG-minus-SHORT feature contrasts directly and forced one side at 00:00, 00:15, 00:30, and 00:45 UTC. It produced exactly four trades on all 433 evaluation Neutral dates, but conditional direction accuracy was only 52.60%. Its 1,732 trades won 33.26%, returned 1.432 payoff, PF 0.714, and -341.10R. The latest six months produced 156 trades, 29.49% wins, PF 0.601, and -44.98R. Direct paired learning is closed.
24. Login-free EURUSDT executed flow: 78 official Binance archives supplied 682,290 checksum-validated M5 bars with actual volume, trade count, and taker-buy volume from 2020 through June 2026. A frozen, unfitted rule used the sign of the prior 15-minute taker imbalance at four first-hour clocks. It produced exactly four trades on all 519 eligible Neutral dates, but conditional side accuracy was only 50.72%. Its 2,076 trades won 32.18%, returned 1.433 payoff, PF 0.680, and -463.75R. The latest six months fell to 26.28% wins, PF 0.513, and -57.48R. The source pipeline is retained; the sign rule is closed.
25. Flow-augmented paired ranker: the same checksum-pinned EURUSDT archive added only prior-15-minute taker imbalance and return to the frozen 16-feature paired side model. The 2020-2021 period was training-only; 1,336 later trades executed exactly four times on all 334 eligible Neutral dates. Conditional side accuracy was only 51.30%, win rate 32.41%, payoff 1.430, PF 0.686, and net -292.70R. The latest six months improved to PF 0.698 but still lost 32.48R. All four windows and every clock failed, so this final predeclared fitted use of the source is closed.
26. Kraken/Binance multivenue executed flow: 699 login-free Kraken API pages supplied 398,079 trades from the actual EUR/USD pair inside the required decision-time windows. Kraken and Binance imbalance correlated only 0.06, establishing source novelty. A locked equal-weight sign rule produced exactly four trades on all 453 eligible Neutral dates, but conditional accuracy was 50.57%. Its 1,812 trades won 31.95%, returned 1.439 payoff, PF 0.676, and -410.05R. The latest six months returned PF 0.602 and -44.93R. Every window and clock failed; both venue histories are now closed.
27. Coinbase stablecoin/EUR volume pressure: 668 login-free public responses supplied 7,260 M5 candles from the USDC-EUR and USDT-EUR order books. A frozen prior-three-candle signed-volume agreement rule selected 614 trades, or 1.838 per source-eligible Neutral date. It won 33.22%, returned 1.439 payoff, PF 0.716, and -119.33R. The latest six months produced 85 trades, 29.41% wins, PF 0.600, and -24.60R. Development and every validation window failed; the exact rule is closed.
28. Macro-event drift: 30 login-free Dukascopy calendar responses supplied 84,305 events from 2019 through June 2026. A source audit prohibited historical actual/forecast/previous/impact values after finding that they were not trustworthy point-in-time records. A frozen title taxonomy and completed event-to-midnight EURUSD impulse produced 439 candidates. Development selected momentum over reversal, but both lost. The selected branch's 185 forward trades won 29.19%, returned 1.439 payoff, PF 0.593, and -54.63R. The latest six months produced 31 trades, 19.35% wins, PF 0.345, and -16.78R. Every forward window failed; the exact event-timing family is closed.
29. Direct post-event drive: the latest qualifying event on each Neutral date opened a 15-minute completed-bar observation, followed by a structure-risk 1.5R trade. The outcome-blind rule produced 495 candidates. Development selected momentum, but both frozen branches lost. The selected branch's 210 forward trades won 35.71%, returned 1.388 payoff, PF 0.771, and -31.11R. The latest six months were a genuine profitable exception—37 trades, 43.24% wins, 1.459 payoff, PF 1.112, and +2.39R—but 2019-2025 all lost and the rule had zero oracle matches. The exact rule is closed rather than cherry-picking 2026.
30. Selective post-event probability: one fixed side-stacked L2 model learned from the 2019-2022 post-event candidates and required a cost-aware 0.42 predicted win probability. The forward-outcome-blind screen retained only 28 of 210 candidates: 11/5/9/3 across 2023, 2024, 2025, and 2026 H1. The latter two deficient blocks failed the frozen eight-trade capacity gate, so forward P&L was intentionally not loaded. A three-trade six-month sample is not sufficient evidence of profitability; the threshold is not lowered after screening.
31. Capacity-calibrated selective post-event probability: a fixed outcome-blind 0.42/0.41/0.40 threshold ladder chose 0.40, the highest level retaining at least eight candidates in every window. The exact 75-candidate manifest was locked before P&L. It improved forward PF to 0.853 and reduced the loss to -6.77R, but still won only 38.67%. Both 2024 (PF 1.391) and 2026 H1 (9 trades, 44.44% wins, 1.468 payoff, PF 1.175, +0.88R) were profitable; 2023 and 2025 lost. The two favorable windows are not converted into a post-outcome activation filter.
32. XAUUSD/XAGUSD first-hour consensus: 438 missing login-free XAGUSD hours were downloaded from Dukascopy's public Jetta endpoint and combined with existing XAUUSD raw history into a checksum-pinned 40,481-row M5 source. A frozen, unfitted 60-minute sign-agreement rule selected 690 forward trades at the Neutral oracle's four actual clocks. Conditional side accuracy reached 52.06%, but the rule won only 32.90%, returned 1.439 payoff, PF 0.705, and -139.83R. The latest six months produced 111 trades, 27.93% wins, PF 0.558, and -36.25R. Development and every forward window failed; the economic direction is not reversed.
33. Five-session mean reversal: a development-only audit rejected two-stage opportunity scoring, 240 fixed-stop price rules, 480 wider session-entry rules, and 72 Asian-range OCO rules before forward data. The simplest surviving rule reversed the sign of 1,440 completed M5 bars with a 40-pip stop, 60-pip target, 72-hour hold, and deterministic cooldown. It earned PF 1.228 in 234 development trades and PF 1.309 in untouched 2023, but 2024-2026 all lost. Its 171 forward trades won 41.52%, realized only 1.268 payoff, returned PF 0.900, and lost 9.43R. The latest six months returned PF 0.816 and -2.62R. The exact rule is closed rather than activating the favorable 2023 window.

Final status: `RESEARCH_FAILURE_NOT_DEMO_READY`.

Key reports:

- `EURUSD_TWO_CLOCK_ENSEMBLE_VERDICT_2026_07_27.md`
- `EURUSD_LAST_6_MONTHS_BACKTEST_2026_01_TO_2026_06.md`
- `EURUSD_ASYMMETRIC_PAYOFF_VERDICT_2026_07_27.md`
- `EURUSD_CONFIRMED_REVERSAL_VERDICT_2026_07_27.md`
- `EURUSD_CROSSASSET_HANDOFF_VERDICT_2026_07_27.md`
- `EURUSD_RETROSPECTIVE_OVERFIT_DEMONSTRATION_2026_07_27.md`
- `EURUSD_REGIME_1_NEUTRAL_CAUSAL_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_JULY_RESULT_2026_07_27.md`
- `EURUSD_NEUTRAL_ORACLE_IMITATION_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_SYNCHRONOUS_CROSSASSET_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_UTC_OPEN_VOTE_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_COT_FLOW_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_COT_OPTIONS_FLOW_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_CME_OPTIONS_SURFACE_PREREG_2026_07_27.md`
- `EURUSD_NEUTRAL_CME_OPTIONS_SURFACE_DATA_AUDIT_2026_07_27.md`
- `EURUSD_NEUTRAL_CME_SPAN_FREE_SOURCE_AUDIT_2026_07_27.md`
- `EURUSD_NEUTRAL_SESSION_OCO_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_SESSION_OCO_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_FUTURES_PARTICIPATION_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_FUTURES_PARTICIPATION_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_OCC_FXE_FLOW_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_OCC_FXE_FLOW_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_DTCC_FX_OPTIONS_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_DTCC_FX_OPTIONS_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_DTCC_SKEW_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_DTCC_SKEW_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_OPENING_DRIVE_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_OPENING_DRIVE_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_OPENING_DRIVE_PROSPECTIVE_STATE_2026_07_28.json`
- `EURUSD_NEUTRAL_MIDNIGHT_PAIRS_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_MIDNIGHT_PAIRS_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_FOUR_CLOCK_RANKER_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_FOUR_CLOCK_RANKER_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_BINANCE_EURUSDT_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_BINANCE_EURUSDT_FLOW_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_BINANCE_EURUSDT_FLOW_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_FLOW_AUGMENTED_RANKER_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_FLOW_AUGMENTED_RANKER_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_KRAKEN_EURUSD_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_KRAKEN_MULTIVENUE_FLOW_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_KRAKEN_MULTIVENUE_FLOW_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_SELECTIVE_MULTIVENUE_AGREEMENT_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_SELECTIVE_MULTIVENUE_AGREEMENT_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_SELECTIVE_TARGET_PROBABILITY_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_SELECTIVE_TARGET_PROBABILITY_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_COINBASE_STABLECOIN_EUR_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_COINBASE_STABLECOIN_FLOW_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_COINBASE_STABLECOIN_FLOW_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_DUKASCOPY_EVENT_TIMING_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_MACRO_EVENT_DRIFT_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_MACRO_EVENT_DRIFT_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_POST_EVENT_DRIVE_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_POST_EVENT_DRIVE_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_SELECTIVE_POST_EVENT_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_SELECTIVE_POST_EVENT_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_CAPACITY_SELECTIVE_POST_EVENT_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_CAPACITY_SELECTIVE_POST_EVENT_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_PRECIOUS_METALS_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_PRECIOUS_METALS_CONSENSUS_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_PRECIOUS_METALS_CONSENSUS_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_FIVE_SESSION_REVERSAL_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_FIVE_SESSION_REVERSAL_VERDICT_2026_07_28.md`
- `outputs/two_clock/backtest_results.json`
- `outputs/asymmetric_payoff/RESULT.json`
- `outputs/confirmed_reversal/RESULT.json`
- `outputs/crossasset_handoff/RESULT.json`
- `outputs/retrospective_overfit/RESULT.json`
- `outputs/neutral_causal/RESULT.json`
- `outputs/neutral_walkforward/RESULT.json`
- `outputs/neutral_crosspair/RESULT.json`
- `outputs/neutral_crosspair_nonlinear/RESULT.json`
- `outputs/neutral_tick_microstructure/RESULT.json`
- `outputs/neutral_tick_volatility/RESULT.json`
- `outputs/neutral_prospective_july/RESULT.json`
- `outputs/neutral_oracle_imitation/RESULT.json`
- `outputs/neutral_synchronous_crossasset/RESULT.json`
- `outputs/neutral_utc_open_vote/RESULT.json`
- `outputs/neutral_cot_flow/RESULT.json`
- `outputs/neutral_cot_options_flow/RESULT.json`
- `outputs/neutral_cme_options_surface/AUDIT.json`
- `outputs/neutral_cme_span_surface/AUDIT.json`
- `outputs/neutral_session_oco/RESULT.json`
- `outputs/neutral_futures_participation/RESULT.json`
- `outputs/neutral_occ_fxe_flow/RESULT.json`
- `outputs/neutral_dtcc_fx_options/RESULT.json`
- `outputs/neutral_dtcc_skew/RESULT.json`
- `outputs/neutral_opening_drive/RESULT.json`
- `outputs/neutral_midnight_pairs/RESULT.json`
- `outputs/neutral_four_clock_ranker/RESULT.json`
- `outputs/neutral_binance_eurusdt_flow/RESULT.json`
- `outputs/neutral_flow_augmented_ranker/RESULT.json`
- `outputs/neutral_kraken_multivenue_flow/RESULT.json`
- `outputs/neutral_selective_multivenue_agreement/RESULT.json`
- `outputs/neutral_selective_target_probability/RESULT.json`
- `outputs/neutral_coinbase_stablecoin_flow/RESULT.json`
- `outputs/neutral_macro_event_drift/RESULT.json`
- `outputs/neutral_post_event_drive/RESULT.json`
- `outputs/neutral_selective_post_event/SCREEN.json`
- `outputs/neutral_capacity_selective_post_event/RESULT.json`
- `outputs/neutral_precious_metals_consensus/RESULT.json`
- `outputs/neutral_five_session_reversal/RESULT.json`

Run with:

```powershell
uv run --with pandas --with numpy --with pyarrow python run_ensemble.py census
uv run --with pandas --with numpy --with pyarrow python run_ensemble.py backtest
uv run --with pandas --with numpy --with pyarrow python run_asymmetric.py
uv run --with pandas --with numpy --with pyarrow python run_confirmed_reversal.py census
uv run --with pandas --with numpy --with pyarrow python run_confirmed_reversal.py backtest
uv run --with pandas --with numpy --with pyarrow python run_crossasset_handoff.py census
uv run --with pandas --with numpy --with pyarrow python run_crossasset_handoff.py backtest
uv run --with pandas --with numpy --with pyarrow python run_retrospective_overfit.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_causal.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_walkforward.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair_nonlinear.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_microstructure.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_volatility.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_prospective.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_oracle_imitation.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_synchronous_crossasset.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_utc_open_vote.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_cot_flow.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_cot_options_flow.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_session_oco.py
uv run --with pandas --with numpy --with pyarrow python download_neutral_futures_participation.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_futures_participation.py
powershell -ExecutionPolicy Bypass -File download_occ_fxe_flow_raw.ps1
uv run --with pandas --with numpy --with pyarrow python download_neutral_occ_fxe_flow.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_occ_fxe_flow.py
uv run --with pandas --with numpy --with pyarrow python download_neutral_dtcc_fx_options.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_dtcc_fx_options.py
uv run --with pandas --with numpy --with pyarrow python build_neutral_dtcc_skew_source.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_dtcc_skew.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_opening_drive.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_midnight_pairs.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_four_clock_ranker.py
uv run --with pandas --with numpy --with pyarrow python download_neutral_binance_eurusdt.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_binance_eurusdt_flow.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_flow_augmented_ranker.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python download_neutral_kraken_eurusd.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_kraken_multivenue_flow.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_multivenue_agreement.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_multivenue_agreement.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_target_probability.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_target_probability.py backtest
uv run --with pandas --with numpy --with pyarrow python download_neutral_coinbase_stablecoin_eur.py rebuild
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_coinbase_stablecoin_flow.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_coinbase_stablecoin_flow.py backtest
uv run --with pandas --with pyarrow python download_neutral_dukascopy_event_timing.py rebuild
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_macro_event_drift.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_macro_event_drift.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_post_event_drive.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_post_event_drive.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_post_event.py screen
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_capacity_selective_post_event.py screen
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_capacity_selective_post_event.py backtest
uv run --with pandas --with numpy --with pyarrow python download_neutral_precious_metals.py rebuild
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_precious_metals_consensus.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_precious_metals_consensus.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_five_session_reversal.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_five_session_reversal.py backtest
```
