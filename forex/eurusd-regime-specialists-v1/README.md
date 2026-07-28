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
```
