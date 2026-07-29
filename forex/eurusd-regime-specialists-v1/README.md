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
34. Adaptive-frequency fallback audit: the two raw Capital.com MT5 reports reproduce the published 697 trades, 57.82% win rate, PF 1.3075, and +$119.42. The stronger Regime 1 claim fails. Realized payoff is only 0.954, the best 5% of trades contribute 93.78% of net, and a further 0.5-pip round-trip haircut reduces PF to 1.194. Exact UTC normalization and the causal cross-asset classifier isolate 116 Neutral trades at PF 1.448, but fixed 0.01-lot sizing plus 0.5 pip reduces PF to 1.261, while 2026 H1 falls to PF 0.898 and -$1.79. The slice is 97.41% long and has zero same-side oracle matches within 15 minutes. The H4 overlay is conditional leverage on the same M15 entries, not an independent specialist; combined portfolio floating drawdown remains unavailable from the two separate reports. Status is `REJECTED_AS_REGIME_1_IMITATION / NO_DEMO_PROMOTION`.
35. Neutral symmetric RSI 1.5R: the rule, source, costs, and gates were hash-locked before an outcome-blind census. Capacity passed with 3,920 balanced Neutral signals, and the one frozen run executed 1,433 trades. The target delivered a 1.424 realized payoff, but win rate was only 37.89%, PF 0.869, and net -114.11R. Both sides lost, every block through 2025 lost, and the marginal 2026 H1 PF 1.027 / +1.52R fell to PF 0.928 / -4.30R under 0.5-pip stress and was -$2.75 at fixed 0.01 lot. Best-5%-removed PF was 0.745, maximum drawdown 129.87R, and only 29 trades matched the oracle within 15 minutes. The exact rule is rejected without deleting shorts or activating 2026.
36. Event-conditioned DXY/Treasury rates agreement: the event clock, exact USD title taxonomy, completed M5 cross-asset reaction, Neutral ownership, execution, and census gates were hash-locked and pushed before candidate counts. Of 890 qualifying USD event clusters, 402 produced opposite-sign DXY/Treasury agreement before regime filtering, but only 53 survived the full frozen Neutral and risk contract: 28/4/10/6/5 across development, 2023, 2024, 2025, and 2026 H1. LONG/SHORT capacity was balanced at 26/27, but the total, development, later-window, and recent sample gates failed. Per the lock, P&L was not opened and the gates were not relaxed. The exact family is closed as `CENSUS_FAIL_NO_PNL_ALLOWED`.
37. Point-in-time BLS source: 267 official archived CPI, PPI, and Employment Situation PDFs were downloaded without login and normalized to the values initially published at each release. Coverage is 98.89%/96.74%/96.74%, every parsed PDF has an evidence sentence and checksum, no later database revision is used, and the 2020 NFP unit audit preserves -20.5 million and +2.5 million correctly. This revision-safe source is accepted for causal research, not trading authorization.
38. BLS release-time acceleration: the source, same-family initial-value comparison, 15-minute wait, fixed 15-pip/1.5R execution, entry-time Neutral ownership, and gates were hash-locked and pushed before census. The 267 releases produced 244 directional macro signals but only 30 full-contract Neutral candidates: 19/2/1/6/2 across development, 2023, 2024, 2025, and 2026 H1. Both sides and all three families were represented, but total, development, 2023, and 2024 capacity failed. P&L was not opened and the exact event-entry family is closed.
39. BLS first-hour macro carry: the revision-safe acceleration state was carried for at most 72 hours to Regime 1's four outcome-blind first-hour clocks. The frozen census passed with 448 candidates on 112 Neutral dates, balanced across directions and all three families. The single permitted run achieved the intended 1.439 payoff but only 32.37% wins, PF 0.689, and -96.70R. Only 2024 was positive. The latest six months produced 20 trades, 20.00% wins, PF 0.360, -10.50R, and -$4.20 at fixed 0.01 lot. Stress PF was 0.562 and 15-minute oracle precision only 34.82%; the exact carry rule is rejected without reversal or year selection.
40. BLS six-release rolling surprise: the current first-published CPI, PPI, or NFP value was compared with the median of its six previous consecutive initial values, then carried for at most 72 hours to the same four Neutral clocks. The locked census passed with 404 candidates on 101 dates. The frozen run achieved 1.439 payoff but only 32.18% wins, PF 0.683, and -89.10R. The latest six months appear strong at four trades, 75% wins, PF 4.317, +3.40R, and +$1.36 at 0.01 lot, but all four were overlapping CPI shorts on one date, 12 June 2026. That effective sample of one cannot authorize demo trading; development, 2023, and 2025 lost, stress PF was 0.557, and the exact rule is rejected.
41. TradingView consensus source: 90 login-free monthly JSON responses supplied historical consensus forecasts for the exact CPI MoM, PPI MoM, and NFP tickers. Every provider row had to match the UTC timestamp and initial actual parsed from the official BLS PDF. This accepted 262 of 267 releases at 98.13% total coverage and 100% forecast coverage among matches; five revised, missing, or value-less rows were quarantined. The known 2024-01-05 payroll corruption check reproduces the contemporaneous 216K/170K/173K actual/forecast/previous triplet. The source is deterministic and accepted for one adaptive historical test, but its post-hoc API retrieval is not pristine point-in-time proof; prospective pre-release capture remains mandatory.
42. Consensus-surprise finite family: actual-minus-consensus direction was carried for at most 72 hours to the four Neutral clocks, both raw and with agreement from the completed prior 15-minute EURUSD return. Both locked censuses passed at 404 and 212 trades. Full-history PFs were only 0.755 and 0.772, with 34.41% and 34.91% wins; development, 2023, and 2025 lost for both. The latest six months were profitable—carry returned 16 tickets, 68.75% wins, PF 3.166, +11.10 ticket R, and +$4.44 at 0.01 lot; agreement returned 12 tickets, 58.33% wins, PF 2.015, +5.20 ticket R, and +$2.08—but all activity clustered on only four dates. The 2026 exception is not selected after inspection, and both exact variants are rejected.
43. Neutral consensus event confirmation: on a date classified Neutral at 00:00, a CPI/PPI/NFP surprise was traded only when the first three completed post-release M5 bars agreed with its EURUSD side. The locked census passed with 49 trades on 49 dates. The 15-pip/1.5R execution returned 36.73% wins, 1.522 payoff, PF 0.884, -3.38R, and -$5.07 at 0.01 lot. Combined 2023-2026 was marginally positive at PF 1.027, but profitable 2023-2024 gave way to PF 0.297 in 2025 and PF 0.742 in 2026 H1. The latest six months contained only three trades and lost -0.52R / -$0.78. Same-day oracle-side precision reached 63.27%, but cost and winner stress failed; the exact rule is rejected.
44. Two-stage opportunity audit: a fixed L2 model first estimated whether either side had a 1.5R opportunity, then a separate paired model chose LONG or SHORT. Only 2019-2020 training labels and 2021-2022 development outcomes were admitted; the source filter stopped at 2022-12-30 00:45 UTC and no 2023-2026 return was loaded. At success-score thresholds 0.45/0.43/0.41, the development selections returned PF 0.739/0.726/0.764 and lost 19.80R/29.45R/35.05R. The strictest threshold retained 112 trades but won only 33.93%, with PF 0.632 in 2021 and 0.872 in 2022. Opportunity probability was not the missing variable; future side remained unlearnable from the available causal feature set. The family is rejected in development and forward evaluation is forbidden.
45. Prospective consensus capture: a no-login append-only pipeline now records raw TradingView responses, local request times, provider HTTP date, immutable normalized pre-release rows, and a deterministic SHA-256 evidence chain. The first 28 July snapshot saw the scheduled 7 August NFP, 12 August CPI, and 13 August PPI events but correctly admitted zero rows because all three forecasts were still null. The null snapshot is retained as point-in-time proof; repeated captures closer to release can append a forecast but can never rewrite earlier evidence. This fixes the historical source's timestamp boundary, not strategy profitability, and authorizes no broker action.
46. Prospective Neutral macro/cross-asset agreement: the post-release collector now links an actual only to an immutable forecast captured at least 60 seconds before the same TradingView event id, ticker, and UTC timestamp. The new specialist is frozen without any historical backtest or historical P&L. On a Neutral-owned date it waits for three completed M5 bars, then requires a macro surprise, EURUSD reaction, and DXY/Treasury reaction to agree. Frequency is not a gate; the rule remains shadow-only until at least 12 months and 30 trades pass win-rate, 1.5R payoff, PF, side-balance, drawdown, cost, winner-removal, and oracle-precision checks. The initial state has zero forecasts, actuals, signals, and trades, so no profitability claim or broker action is authorized.
47. Prospective event-market capture: a no-login Dukascopy collector now preserves the exact EURUSD, DXY, and Treasury hourly tick responses needed around each eligible release, reconstructs only completed M5 bars, and appends one linked reaction row with an evidence-chain hash. It refuses all requests until the three observation bars plus a 60-second lag are complete, excludes the entry bar, and stays in cash if any required bar is absent. The 7 August NFP dry run correctly reports that 12:46 UTC is the earliest capture time and makes no network request now.
48. Neutral London-fix reversal: a new two-expert structural-flow family separated ordinary from calendar month-end fixes, converted 16:00 Europe/London with DST, required a large prior-only 60-minute displacement and opposite completed fix-bar confirmation, and was locked before census. Capacity passed with 165 candidates on 165 dates, balanced 98/67 across LONG/SHORT. Development then rejected both experts without opening any 2023-2026 outcome. Ordinary fixes returned 93 trades, 29.03% wins, 1.454 payoff, PF 0.595, -27.25R, and 30.56R drawdown; both 2019-2020 and 2021-2022 lost. Month-end had only three development trades and PF 0.731. The empty selection forbids a forward or latest-six-month P&L run, and the exact family is closed without direction reversal or threshold repair.
49. Neutral growth/risk consensus: a no-login Dukascopy panel of SPX, copper, and USD/CNH was audited for exact completed-M5 availability, then a single three-session consensus family was locked before EURUSD outcomes. Its census passed with 410 candidates. The bounded 2022 development slice produced 68 trades, 45.59% wins, 1.434 payoff, PF 1.202, and +7.55R, but the exact family is contractually rejected because it missed its frozen 80-trade evidence floor. No 2023-2026 EURUSD outcome was loaded. Asia and Europe were individually profitable while the US expert lost; that decomposition may only be used as disclosed development evidence for a separately locked successor.
50. Neutral selected growth/risk experts: an explicitly adaptive N47 successor permanently selected the profitable 2022 Asia and Europe experts and was committed before opening 2023. The 54-trade development portfolio had 48.15% wins, 1.471 payoff, PF 1.366, and +10.36R. Untouched 2023 confirmation rejected it with 60 trades, 31.67% wins, 1.526 payoff, PF 0.707, -11.69R, and 17.16R drawdown. Asia was near flat at PF 0.980, while Europe collapsed to PF 0.346. No 2024-2026 outcome was loaded and the exact portfolio cannot be repaired or forwarded.
51. Neutral Asia growth/risk transmission: a final one-rule successor kept only the comparatively stable 03:00 Asia expert and required the completed pre-entry EURUSD 15-minute move to agree with the external SPX/copper/USD-CNH consensus. Its outcome-blind census passed with 87 low-frequency candidates. Development rejected it with 41 trades across 2022-2023, 39.02% wins, 1.470 payoff, PF 0.941, and -1.49R. The LONG side was only marginally positive at PF 1.052 and the SHORT side lost at PF 0.800. No 2024-2026 trade outcome was loaded; the growth/risk branch is closed rather than tuned against sealed future data.
52. Neutral oracle target-timing audit: the source-hashed perfect-foresight ledger contains 2,615 Neutral oracle rows on 662 dates. Because the oracle scans M5 candidates chronologically and stops after its first four target-before-stop winners, 2,482 entries (94.91%) occur before 01:00 UTC. Zero lie within four hours of the prospective macro specialist's 12:45 UTC entry clock. The macro rule can still be evaluated as a profitable Neutral-owned specialist, but it cannot claim temporal imitation without passing the separately frozen one-to-one timing test; this distinction changes no signal or threshold.
53. GDELT GKG source audit: a no-login official 15-minute GKG batch was preserved on `D:` with an exact provider-MD5 match and independent SHA-256. All 1,800 rows have the expected 27 fields and one batch timestamp. The feed contains central-bank and currency themes, but a strict monetary-policy-plus-organization filter found 12 Fed documents and zero ECB documents, while several Fed matches concerned unrelated oil, equity, or political context. The free timestamped source is accepted only for a separately frozen multi-date coverage census; no EURUSD signal, threshold, outcome, or broker action was created.
54. GDELT multi-date coverage census: before downloading another source file, 24 entry dates were fixed as the first and third Tuesday of each month from August 2025 through July 2026. Only four prior-date 23:00-23:45 GKG batches per date may be requested, for 96 files. File, schema, paired ECB/Fed-date, unique-source, concentration, and duplication gates are frozen. EURUSD prices, oracle rows, direction mapping, and P&L are prohibited; failure closes the source lane and passing permits only a separately preregistered prospective design.
55. GDELT coverage result: 95 of 96 frozen archives passed strict validation, 23 of 24 dates were complete, and 17 dates contained both ECB and Fed documents. The filter retained 57 ECB documents from 53 sources and 733 Fed documents from 375 sources; largest-source shares were 3.51% and 3.00%, with zero duplicate-document share. All ten capacity gates passed without loading EURUSD prices, returns, oracle rows, or P&L.
56. GDELT source-only relative tone: one median-of-source-medians ECB-minus-Fed transform and its MAD-normalized threshold were locked before tone inspection. All 790 strict documents had finite tone, 12 dates met two-source quorum on both sides, and six source-only candidates split 3 LONG / 3 SHORT. This passed the frozen transform-capacity gates but did not test return prediction.
57. Prospective GDELT Neutral expert: the exact source filter, relative-tone transform, Neutral ownership, 00:15 decision, 00:20 bid/ask shadow entry, 0.7-pip spread floor, 1.5-pip spread ceiling, adverse slippage, four-pip stop, six-pip target, four-hour path, and conservative cross-expert conflict rule are implementation-hash locked before the 29 July start. Frequency is not a gate. The first boundary is scheduled, but signals, trades, P&L, profitability approval, and broker authorization remain zero.
58. Prospective GDELT independent validation: the validator contract and implementation were hash-locked with zero source captures, decisions, signals, paths, or oracle rows. It verifies every decision/path/raw-tick hash, replays each closed path from immutable ticks, reports frequency without gating it, and separates profitability, same-day Regime 1 resemblance, and full temporal oracle-imitation claims. The empty-evidence status is `WAITING_FOR_PROSPECTIVE_START`; the full suite is 335 passed with two existing dependency warnings.
59. First-boundary publication safety: a direct diagnostic received HTTP 400 when requesting Dukascopy's still-open current-hour archive. The waiting helper was therefore replaced before the boundary; if a signal occurs, it preserves the exact 04:20 UTC time exit but delays evidence capture until 05:16 UTC, after the 04:00-05:00 archive is complete, and then runs the locked validator.
60. Dukascopy SWFX sentiment feasibility: the official no-login public endpoint returned 1,360 consumer-sentiment rows with exactly one EUR/USD record, an HTTP timestamp, and a reproducible response hash. The source is genuinely new but not yet strategy-ready: its JSONP payload lacks an explicit settlement timestamp, its signed field semantics are not formally bound to the documented percentage-long versus tendency definitions, and the raw diagnostic body was not preserved. Only a separately preregistered, source-only prospective capture census is allowed next; no direction, threshold, outcome, or P&L was selected.
61. Prospective SWFX sentiment source census: before its `2026-07-29T06:30:00Z` start, a source-only half-hourly UTC-weekday capture was locked. It preserves immutable raw JSONP, headers, local observation clocks, hashes, and the exact EUR/USD row while loading no EURUSD price, return, oracle, outcome, or P&L. The source cannot qualify before 27 calendar days, 20 weekdays, 800 valid captures, the frozen coverage/variation gates, and three official-widget or JForex semantic comparisons. Passing would permit only a separately preregistered prospective strategy; this census cannot generate a signal or trade.
62. GDELT daily operations restart: the missed `2026-07-29` boundary was recorded honestly as `CASH_MISSING_ON_TIME_SOURCE`, with no late backfill or trade. A hash-locked operations-only helper now schedules the unchanged source, ownership, decision, delayed path, and validator functions beginning with the `2026-07-30` entry date. It cannot change strategy logic or authorize broker action, and it skips source or ownership acquisition after the frozen decision deadline.
63. SWFX semantics audit: the official Dukascopy page verifies that consumer sentiment is based on long/short open-position shares, that the index is the long-share-minus-short-share percentage-point difference, and that it updates every 30 minutes. The exact public JSONP `*_long`/`*_short` field binding remains unproven because the embedded instrument rows failed to load in both browser surfaces. This observation therefore counts as zero of the three frozen visible-value comparisons and does not authorize a strategy mapping.
64. Independent SWFX source validation: before the first prospective capture, a separately hash-locked, network-free validator was frozen. It replays each EUR/USD row from immutable raw JSONP, independently verifies clocks, hashes, antipodal fields, normalized values, source-only boundaries, missing slots, failures, and every census gate. The collector can no longer certify its own output, and source admission still permits only a later separately preregistered strategy design.

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
- `EURUSD_NEUTRAL_GDELT_COVERAGE_CENSUS_RESULT_2026_07_28.md`
- `EURUSD_NEUTRAL_GDELT_RELATIVE_TONE_DESIGN_AUDIT_RESULT_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_GDELT_RELATIVE_TONE_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_GDELT_VALIDATION_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_DUKASCOPY_SWFX_SENTIMENT_SOURCE_FEASIBILITY_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_SOURCE_CENSUS_PREREG_2026_07_29.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_SOURCE_CENSUS_STATE_2026_07_29.json`
- `EURUSD_NEUTRAL_DUKASCOPY_SWFX_SENTIMENT_SEMANTICS_AUDIT_2026_07_29.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_VALIDATION_PREREG_2026_07_29.md`
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
- `EURUSD_NEUTRAL_EVENT_CROSSASSET_RATES_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_EVENT_CROSSASSET_RATES_CENSUS_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_INITIAL_RELEASE_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_RELEASE_ACCELERATION_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_RELEASE_ACCELERATION_CENSUS_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_FIRST_HOUR_CARRY_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_FIRST_HOUR_CARRY_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_ROLLING_SURPRISE_CARRY_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_BLS_ROLLING_SURPRISE_CARRY_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_TRADINGVIEW_CONSENSUS_SOURCE_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_CONSENSUS_SURPRISE_FAMILY_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_CONSENSUS_SURPRISE_FAMILY_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_CONSENSUS_EVENT_CONFIRMATION_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_CONSENSUS_EVENT_CONFIRMATION_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_TWO_STAGE_OPPORTUNITY_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_CONSENSUS_CAPTURE_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_CONSENSUS_CAPTURE_STATE_2026_07_28.json`
- `EURUSD_NEUTRAL_PROSPECTIVE_ACTUAL_CAPTURE_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_MACRO_CROSSASSET_AGREEMENT_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_MACRO_CROSSASSET_AGREEMENT_STATE_2026_07_28.json`
- `EURUSD_NEUTRAL_PROSPECTIVE_MARKET_CAPTURE_2026_07_28.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_MARKET_CAPTURE_2026_07_28.sha256.json`
- `EURUSD_NEUTRAL_LONDON_FIX_REVERSAL_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_LONDON_FIX_REVERSAL_DEVELOPMENT_VERDICT_2026_07_28.md`
- `EURUSD_NEUTRAL_LONDON_FIX_REVERSAL_DEVELOPMENT_CLOSURE_2026_07_28.sha256.json`
- `EURUSD_ADAPTIVE_FREQUENCY_FALLBACK_AUDIT_2026_07_28.md`
- `EURUSD_NEUTRAL_SYMMETRIC_RSI_1P5R_PREREG_2026_07_28.md`
- `EURUSD_NEUTRAL_SYMMETRIC_RSI_1P5R_VERDICT_2026_07_28.md`
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
- `outputs/neutral_event_crossasset_rates/CENSUS.json`
- `outputs/neutral_bls_release_acceleration/CENSUS.json`
- `outputs/neutral_bls_first_hour_carry/RESULT.json`
- `outputs/neutral_bls_rolling_surprise_carry/RESULT.json`
- `outputs/neutral_growth_risk_consensus/DEVELOPMENT_RESULT.json`
- `outputs/neutral_growth_risk_selected/CONFIRMATION_RESULT.json`
- `outputs/neutral_asia_growth_risk_transmission/DEVELOPMENT_RESULT.json`

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
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_event_crossasset_rates.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_bls_release_acceleration.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_bls_first_hour_carry.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_bls_first_hour_carry.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_bls_rolling_surprise_carry.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_bls_rolling_surprise_carry.py backtest
uv run --with pandas --with pyarrow python download_neutral_tradingview_consensus.py resume
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_consensus_surprise_family.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_consensus_surprise_family.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_consensus_event_confirmation.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_consensus_event_confirmation.py backtest
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_two_stage_opportunity_audit.py
uv run --with pandas --with pyarrow python capture_prospective_tradingview_consensus.py capture --days-ahead 60
uv run --with pandas --with pyarrow python capture_prospective_tradingview_actuals.py capture
uv run --with pandas --with pyarrow python capture_prospective_dukascopy_event_m5.py capture --event-time 2026-08-07T12:30:00Z
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_london_fix_reversal.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_london_fix_reversal.py development
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_growth_risk_consensus.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_growth_risk_consensus.py development
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_growth_risk_selected.py confirmation
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_asia_growth_risk_transmission.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_asia_growth_risk_transmission.py development
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python validate_prospective_neutral_gdelt_relative_tone.py status
uv run python capture_prospective_neutral_swfx_sentiment_source.py status
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_prospective_neutral_gdelt_daily_operations.py
uv run python validate_prospective_neutral_swfx_sentiment_source.py status
```
