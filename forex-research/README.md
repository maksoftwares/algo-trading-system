# Forex Research Lane

Status: RESEARCH_ONLY - raw/tuned USDJPY, tuned EURUSD MT5 watchlist leads, sparse USDJPY bond-vol clue, rejected GBPUSD frequency extension, no demo spec

This lane is separate from the XAUUSD EA lanes. It uses local historical bar data for offline research only.

Boundaries:

- Do not touch MT5 terminals, profiles, charts, presets, demo EAs, or running XAU EAs from this lane.
- Do not mark a Forex candidate approved from a single screen.
- Treat all outputs as research evidence only until a candidate survives repeatable, net-of-cost, out-of-sample review.
- Use unique magic/comment specs only after a candidate survives; do not attach anything without owner approval.

Current source data is read from:

`../xau-usd/xauusd-phase0/data/processed/bars`

Primary commands:

```powershell
python forex-research\scripts\run_forex_research_lane.py cost-scan
python forex-research\scripts\run_forex_research_lane.py first-screen
python forex-research\scripts\run_forex_research_lane.py second-pass
python forex-research\scripts\run_forex_research_lane.py recent-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py recent-commodity-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py recent-proxy-stress
python forex-research\scripts\run_forex_research_lane.py macro-screen
python forex-research\scripts\run_forex_research_lane.py treasury-curve-screen
python forex-research\scripts\run_forex_research_lane.py cny-dollar-screen
python forex-research\scripts\run_forex_research_lane.py calendar-session-screen
python forex-research\scripts\run_forex_research_lane.py weekly-structure-screen
python forex-research\scripts\run_forex_research_lane.py financial-liquidity-screen
python forex-research\scripts\run_forex_research_lane.py cot-financial-acquire
python forex-research\scripts\run_forex_research_lane.py cot-positioning-screen
python forex-research\scripts\run_forex_research_lane.py global-risk-screen
python forex-research\scripts\run_forex_research_lane.py commodity-dollar-screen
python forex-research\scripts\run_forex_research_lane.py commodity-dollar-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-real-asset-rotation-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py real-asset-rotation-screen
python forex-research\scripts\run_forex_research_lane.py real-asset-rotation-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-haven-liquidity-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py haven-liquidity-screen
python forex-research\scripts\run_forex_research_lane.py haven-liquidity-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-rates-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py rates-dollar-screen
python forex-research\scripts\run_forex_research_lane.py rates-dollar-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-equity-leadership-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py equity-leadership-screen
python forex-research\scripts\run_forex_research_lane.py equity-leadership-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-sector-rotation-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py sector-rotation-screen
python forex-research\scripts\run_forex_research_lane.py sector-rotation-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-currency-basket-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py currency-basket-screen
python forex-research\scripts\run_forex_research_lane.py currency-basket-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-bond-vol-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py bond-vol-screen
python forex-research\scripts\run_forex_research_lane.py bond-vol-recent-stress
python forex-research\scripts\run_forex_research_lane.py recent-crypto-risk-proxy-acquire
python forex-research\scripts\run_forex_research_lane.py crypto-risk-screen
python forex-research\scripts\run_forex_research_lane.py crypto-risk-recent-stress
python forex-research\scripts\run_forex_research_lane.py broker-refresh-validate
python forex-research\scripts\run_forex_research_lane.py broker-refresh-retest
python forex-research\scripts\run_forex_research_lane.py external-flow-screen
python forex-research\scripts\run_forex_research_lane.py risk-regime-screen
python forex-research\scripts\run_forex_research_lane.py fx-cross-screen
python forex-research\scripts\run_forex_research_lane.py all
```

Current verdict:

- Actual MT5 frequency-first pass: one watchlist-only lead found, `EURUSD rsi_extreme_fade_m15_long_rr0p80`, tested in MT5 Strategy Tester from 2022-07-01 through 2026-07-02 with 1524 trades, CSV PF 1.1336, MT5 report PF about 1.12, and +$97.94 at fixed 0.01 lots. A constrained bad-hour tune blocking only entry hours `1`, `7`, and `21` improved the full run to 1309 trades, CSV PF 1.1705, MT5 report PF about 1.15, and +$108.84. The tuned splits are both positive but uneven: 2022-2024 PF 1.0875 / +$30.87, 2024-2026 PF 1.2733 / +$77.97. Status is `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`; no Forex demo-forward spec is prepared.
- Fresh M30 MT5 frequency follow-up: `EURUSD rsi_bb_close_fade_m30_long_rr0p80` was first validated raw across 2022-2024, 2024-2026, and full 2022-2026. Raw full result was 1145 MT5 trades, CSV PF 1.1301, MT5 PF about 1.11, and +$90.57. One older-split-designed hour tune blocking `6,7,10,13` improved the full run to 831 trades, CSV PF 1.2325, MT5 PF about 1.20, and +$114.80. The tuned validation split is stronger than the design split: 2022-2024 PF 1.1585 / +$40.57, 2024-2026 PF 1.3123 / +$74.23. Robustness is the best Forex MT5 packet so far, but still watchlist-only: 36/49 active months positive and worst 250-trade window PF 0.9765 / -$3.62, while worst 100/150-trade windows remain negative and top-50-winner removal flips the run negative. Frozen portability failed on GBPUSD and USDJPY, so this is EURUSD-only and not demo-forward.
- M30 review prompt: `docs/FOREX_MT5_M30_FREQUENCY_LEAD_REVIEW_PROMPT_2026_07_04.md`. Robustness packet: `outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M30_RSI_BB_LONG_BLOCKH6_7_10_13_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`.
- New USDJPY session-breakout MT5 diversification lead: `USDJPY london120_break_m15`, from `ForexSessionBreakoutScout.mq5`, uses a 06:00-08:00 broker-server range and trades M15 breakouts from 08:00 for four hours. This is raw, both-direction, RR 1.00, and no post-discovery tuning was applied. Full 2022-2026 actual MT5 result: 521 trades, CSV PF 1.3917, MT5 PF about 1.38, +$232.03. Splits are both positive: 2022-2024 PF 1.5157 / +$134.95 and 2024-2026 PF 1.2973 / +$98.05. A no-parameter-change actual-MT5 extension to 2020-2026 improves sample size to 859 trades, CSV PF 1.3028, MT5 PF about 1.28, and +$289.44, with every entry-date calendar year from 2020 through 2026 positive. A further no-parameter-change 2018-2019 extension is negative at 284 trades, CSV PF 0.9435, MT5 PF about 0.94, -$15.09; full 2018-2026 remains positive at 1144 trades, CSV PF 1.2230, MT5 PF about 1.21, +$273.09. Both directions are positive over 2020-2026, but pre-2022 shorts are slightly negative and weak half-years remain in 2021-H2 and 2024-H1. Robustness is watchlist-grade: 2022-2026 has 32/48 months positive, 119/201 weeks positive, and worst 250-trade window PF 1.1529 / +$47.40; 2020-2026 keeps worst 250/400/500-trade windows positive, but worst 50/100/150-trade windows are negative and top-75/top-100-winner removal flips negative. EURUSD/GBPUSD same-rule portability failed. Status is `WATCHLIST_ONLY_MT5_RAW_DIVERSIFICATION_LEAD`, no demo-forward spec; the correct claim is post-2020 strength, not all-regime robustness.
- USDJPY session-breakout review prompt: `docs/FOREX_MT5_USDJPY_SESSION_BREAKOUT_REVIEW_PROMPT_2026_07_04.md`. Review response: `docs/FOREX_MT5_USDJPY_SESSION_BREAKOUT_REVIEW_RESPONSE_2026_07_04.md`. Robustness packet: `outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`.
- USDJPY M30 frequency-first tuned lead: `USDJPY london60_break_m30_blockh7_11_rr1`, also from `ForexSessionBreakoutScout.mq5`, uses a 06:00-07:00 broker-server range and trades M30 breaks from 07:00 for four hours while blocking entry hours `7` and `11`. The raw M30 candidate first survived a no-parameter-change 2020-2026 stretch at 1560 trades, CSV PF 1.1271, MT5 PF about 1.12, +$214.98. The tuned `blockh7_11_rr1` version improves full 2020-2026 to 1227 trades, CSV PF 1.2062, MT5 PF about 1.19, +$278.20, and confirms on 2024-2026 at 384 trades, CSV PF 1.2057, MT5 PF about 1.20, +$94.87. The same tuned rule fails standalone 2018-2019 at 378 trades, CSV PF 0.9410, MT5 PF about 0.92, -$20.05, while full 2018-2026 remains positive at 1607 trades, CSV PF 1.1524, MT5 PF about 1.14, +$257.53. Frozen same-rule portability failed on EURUSD and GBPUSD in both full and recent windows, so this is USDJPY-specific and post-2020-dependent. It remains watchlist-only because the hour filter is post-hoc, 2019 and 2023 are negative, 2023-H1 is materially negative, full-history rolling windows remain negative, and top-winner removal still exposes fragility.
- USDJPY M30 tuned review prompt: `docs/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_REVIEW_PROMPT_2026_07_04.md`. Robustness packet: `outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.md`.
- USDJPY Asia-London M30 raw frequency lead: `USDJPY asia_london_break_m30` was extended unchanged before any tuning. It uses a 00:00-06:00 broker-server Asia range and trades M30 breakouts from 07:00 for four hours, both directions, RR 1.00. Actual MT5 results are positive in both major windows: 207 trades, CSV PF 1.1996, MT5 PF about 1.17, +$54.04 parsed / +$46.56 MT5 in 2018-2019; 721 trades, CSV PF 1.1564, MT5 PF about 1.14, +$179.97 parsed / +$161.13 MT5 in 2020-2026; and 928 trades, CSV PF 1.1646, MT5 PF about 1.14, +$234.01 parsed / +$207.69 MT5 in full 2018-2026. This is the cleanest raw M30 USDJPY all-window frequency lead so far, but remains `WATCHLIST_ONLY_MT5_RAW_FREQUENCY_DIVERSIFICATION_LEAD_NEEDS_REVIEW` because 2021/2023 are negative, worst 250-trade rolling window is PF 0.9142 / -$30.37, and top-50-winner removal flips negative. Review prompt: `docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_PROMPT_2026_07_04.md`. Robustness packet: `outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`.
- USDJPY Asia-London M30 block-hour tune rejected: the raw-lead review allowed one constrained tune, selected only from 2018-2023 raw trades. Hour `7` was the only qualifying blocked hour. The tune slightly improved design PF but reduced validation net and full net: 2024-2026 validation fell from raw 252 trades / PF 1.2100 / +$90.16 parsed to 232 trades / PF 1.1750 / +$70.37 parsed; full 2018-2026 fell from raw +$234.01 parsed to +$226.71 parsed. Verdict is `TUNE_REJECT_KEEP_RAW_WATCHLIST_PREFERRED`; no more tuning and no demo-forward spec.
- GBPUSD M30 wick-reclaim extension rejected before tuning: `GBPUSD bb_wick_reclaim_m30_rr0p80` looked interesting in the 2024-2026 current screen with 156 trades, CSV PF 1.1731, MT5 PF about 1.15, +$23.70. The fixed no-parameter-change extension diluted to 498 trades, CSV PF 1.0717, MT5 PF about 1.06, +$35.05 parsed / +$27.67 MT5 from 2020-2026, then failed standalone 2018-2019 at 157 trades, CSV PF 0.9697, MT5 PF about 0.96, -$5.22 parsed / -$7.54 MT5. Verdict is `REJECT_MT5_THIN_EDGE_NO_TUNING`; no demo-forward spec.
- USDJPY bond-vol actual-MT5 cross-check: the frozen sparse H4 clue `usdjpy_h4_bond_vol_asia_session_carry_relief_v1` was run in actual MT5 Strategy Tester with tester-only EA `ForexBondVolAsiaCarryReliefV1.mq5` and lagged MOVE context through 2026-06-27. Full 2018-2026 result is 79 trades, parsed CSV PF 1.7010, MT5 PF 1.68, +$79.04 parsed / +$77.37 MT5, equity DD max $37.68. It remains `WATCHLIST_ONLY_MT5_GATE_PASS_NO_DEMO_APPROVAL`, but is not a frequency/tuning candidate: 2020-2022 is negative, 2025-2026 is negative at 13 trades / PF 0.5618 / -$13.00, and top-10-winner removal leaves PF 1.0003 / +$0.03. Review prompt: `docs/FOREX_MT5_BOND_VOL_REVIEW_PROMPT_2026_07_04.md`. Actual report: `outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.md`.
- Review of the MT5 frequency lead is complete: `docs/FOREX_MT5_FREQUENCY_LEAD_REVIEW_RESPONSE_2026_07_04.md`. It confirms watchlist-only status and blocks demo-forward because the hour filter is post-hoc, the edge is thin, and the tuned 250-trade rolling window remains negative.
- Portability review is complete: `docs/FOREX_MT5_FREQUENCY_PORTABILITY_REVIEW_2026_07_04.md`. The frozen tuned rule failed on GBPUSD and USDJPY, including the current 2024-2026 split, so it is an EURUSD-only watchlist clue and produced no additional Forex candidate.
- First-screen candidates: 4 rejected.
- Second-pass candidates: 2 rejected.
- Recent Yahoo proxy stress: 6 candidates/probes tested on 2025-07-01 through 2026-07-03 H1 proxy data; no survivor.
- Macro/rate candidates: 3 tested with lagged FRED real-yield and broad-dollar context; one EURUSD H4 historical lead rejected by recent low-sample gate.
- CNY/dollar candidates: 2 tested with lagged FRED USD/CNY and broad-dollar context; both rejected.
- Calendar/session candidates: 2 tested with EURUSD NY-fix H1 reversion and USDJPY H4 month-turn pullbacks; both rejected.
- Weekly-structure candidates: 3 price-only H4 candidates tested against prior-week range/open state; all rejected historically and recent proxy stress did not rescue them.
- Financial/liquidity candidates: 2 tested with lagged FRED NFCI, ANFCI, and WALCL context; both rejected for low historical sample and no recent proxy trades.
- CFTC/COT positioning candidates: 2 tested with official CFTC Traders in Financial Futures Euro FX and Japanese Yen leveraged-money positioning, shifted by a conservative seven-day lag; both rejected for low historical sample, and recent proxy stress produced zero trades.
- Global risk/credit candidates: 2 tested with lagged EEM/SPY and HYG/IEF ETF ratios; both rejected for low sample.
- Commodity/dollar candidates: 2 tested with lagged DBC/UUP and DBB/UUP ETF ratios; EURUSD rejected outright, USDJPY is a low-sample clue only. Recent public ETF/FX proxy stress did not confirm it.
- Real-asset rotation candidates: 2 tested with lagged USO/UUP, HG/GC, and SLV/GLD ETF/futures ratios; both rejected historically, and recent public proxy stress produced zero EURUSD trades and only 6 weak USDJPY trades.
- Haven/liquidity candidates: 2 tested with lagged GLD, GDX/GLD, SPY/TLT, and XLU/XLK ETF context; both rejected historically, and recent public proxy stress was low-sample only.
- Rates/dollar candidates: 3 tested with lagged TLT/UUP and TLT/SHY ETF ratios; two rejected outright and EURUSD short-session v1 is historical watchlist-only, but recent public proxy stress is only a 9-trade clue, not a survivor.
- Treasury curve candidates: 2 tested with lagged FRED DGS2, DGS10, and T10Y2Y context; USDJPY failed historical edge, EURUSD was low-sample, and recent public FX proxy stress was one losing trade per candidate.
- Equity-leadership candidates: 2 tested with lagged ACWX/SPY, IWM/SPY, and XLF/XLU ETF ratios; both rejected historically, and recent public proxy stress is only 9 trades per candidate, not a survivor.
- Sector-rotation candidates: 2 tested with lagged XLY/XLP, QQQ/SPY, XLE/XLU, XLI/XLU, XME/SPY, and TIP/IEF ETF ratios; both rejected historically, and recent public proxy stress is only 12 and 4 trades, not a survivor.
- Currency-basket candidates: 2 tested with lagged FXA/UUP, FXF/UUP, and CYB/UUP ETF ratios; EURUSD failed historically, USDJPY was only a 32-trade historical clue, and recent stress had only 1 losing USDJPY trade after Yahoo returned no usable recent CYB rows.
- Bond-volatility candidates: 3 tested with lagged MOVE context; USDJPY Asia-session v1 is historically strong, but recent public MOVE/FX proxy stress is only 7 trades and negative, not a survivor.
- Crypto-risk candidates: 2 tested with lagged BTC-USD context; both rejected historically, and recent public BTC/FX proxy stress is only 3 and 1 trades, not a survivor.
- External flow candidates: 2 tested with lagged FXE/UUP and inverted FXY/UUP daily ETF relative-flow context; both rejected.
- Risk-regime candidates: 2 tested with lagged FRED VIX/VXV context against EURUSD/USDJPY H4; both rejected.
- FX-cross candidates: 2 tested with lagged AUDJPY/USDJPY and EURJPY/USDJPY daily FX proxy ratios against USDJPY/EURUSD H4; both rejected.
- FX relative-strength candidates: 4 tested with same-time EURUSD/USDJPY USD-pressure agreement, H1 lagging-pair catch-up, and H4 dispersion reversal. All rejected historically; the small recent USDJPY H4 pocket had only 13 proxy trades and is not a survivor.
- Policy-uncertainty candidates: 4 tested with lagged FRED USEPUINDXD context against EURUSD/USDJPY H4/H1. EURUSD H4 was the only positive historical clue at 367 trades, PF 1.0998, +17.57R, but it failed the PF/drawdown gate and recent proxy stress had only 4 trades. The other three candidates were weak historically. No survivor. Standing rule: the current +1 day EPU lag is acceptable for rejection evidence only; any EPU watchlist/promotion attempt must be rerun with a 5-day availability lag and revision-robustness check.
- Short-rate differential candidates: 4 tested with FRED Fed funds, ECB deposit facility, and Japan call-rate context. All rejected historically: EURUSD H4 PF 0.9416 / -21.12R, EURUSD H1 PF 0.8242 / -130.49R, USDJPY H4 PF 0.6932 / -38.14R, USDJPY H1 PF 0.8801 / -25.28R. Recent public FX proxy stress also failed or stayed low-sample. No survivor.
- Independent review response: `docs/FOREX_RESEARCH_LANE_REVIEW_RESPONSE_2026_07_03.md` accepted the review verdict: methodology sound, no survivor, no demo spec, and broker refresh is the next evidence requirement.
- Broker refresh spec: `docs/FOREX_BROKER_DATA_REFRESH_SPEC_2026_07_03.md` requests broker-authoritative EURUSD and USDJPY H1/H4 data from 2022-01-01 through current with measured/exported spread plus terminal/account provenance; any pass is watchlist-only, not demo approval.
- Broker refresh validator: `broker-refresh-validate` audits CSVs under `data/broker_refresh/raw/<broker>/<symbol>/<timeframe>/`, records raw/normalized SHA256s plus export provenance, and writes normalized replay-ready copies only when the file passes timestamp/OHLC/spread checks.
- Broker refresh frozen retest: `broker-refresh-retest` reruns the review-approved frozen EURUSD macro, EURUSD rates/dollar, and USDJPY bond-volatility v0/v1 families on validated broker-refresh CSVs only. It reports `WATCHLIST_ONLY` at best and never prepares a demo-forward spec.
- CNY/dollar pressure screen: `cny-dollar-screen` tests lagged FRED USD/CNY (`DEXCHUS`) plus broad-dollar (`DTWEXBGS`) context against EURUSD/USDJPY H4.
- Calendar/session screen: `calendar-session-screen` tests price-only EURUSD NY-fix reversion and USDJPY month-turn carry-pullback hypotheses with recent proxy stress.
- Weekly-structure screen: `weekly-structure-screen` tests price-only prior-week liquidity fades, USDJPY weekly carry continuation, and EURUSD weekly-open reversion with recent proxy stress.
- Financial/liquidity screen: `financial-liquidity-screen` tests lagged FRED NFCI, ANFCI, and WALCL financial-conditions/liquidity context against EURUSD/USDJPY H4 with recent proxy stress.
- COT positioning screen: `cot-financial-acquire` downloads official CFTC financial-futures COT archives and `cot-positioning-screen` tests lagged leveraged-money positioning reversals on EURUSD/USDJPY H4.
- Global risk/credit screen: `global-risk-screen` tests lagged EEM/SPY and HYG/IEF risk-appetite ratios against EURUSD/USDJPY H4.
- Commodity/dollar screen: `commodity-dollar-screen` tests lagged DBC/UUP and DBB/UUP commodity-vs-dollar ratios against EURUSD/USDJPY H4.
- Commodity/dollar recent stress: `recent-commodity-proxy-acquire` fetches recent DBC/DBB/UUP proxy files and `commodity-dollar-recent-stress` tests the commodity candidates on recent public proxy data.
- Real-asset rotation screen: `real-asset-rotation-screen` tests lagged USO/UUP oil-dollar, HG/GC copper-gold, and SLV/GLD silver-gold ratios against EURUSD/USDJPY H4; `recent-real-asset-rotation-proxy-acquire` and `real-asset-rotation-recent-stress` test the candidates on recent public proxy data.
- Haven/liquidity screen: `haven-liquidity-screen` tests lagged GLD momentum, GDX/GLD miner participation, SPY/TLT risk preference, and XLU/XLK defensive leadership against EURUSD/USDJPY H4; `recent-haven-liquidity-proxy-acquire` and `haven-liquidity-recent-stress` test the candidates on recent public proxy data.
- Rates/dollar screen: `rates-dollar-screen` tests lagged TLT/UUP and TLT/SHY duration-vs-dollar ratios against EURUSD/USDJPY H4; `recent-rates-proxy-acquire` and `rates-dollar-recent-stress` test the rates candidates on recent public proxy data.
- Treasury curve screen: `treasury-curve-screen` tests lagged FRED DGS2, DGS10, and T10Y2Y front-end pressure / bull-steepening context against EURUSD/USDJPY H4 with recent public FX proxy stress.
- Equity-leadership screen: `equity-leadership-screen` tests lagged ACWX/SPY ex-US leadership and IWM/SPY plus XLF/XLU US cyclical leadership against EURUSD/USDJPY H4; `recent-equity-leadership-proxy-acquire` and `equity-leadership-recent-stress` test the candidates on recent public proxy data.
- Sector-rotation screen: `sector-rotation-screen` tests lagged XLY/XLP growth, QQQ/SPY tech, XLE/XLU and XLI/XLU cyclicals, XME/SPY materials, and TIP/IEF inflation-linked rotation against EURUSD/USDJPY H4; `recent-sector-rotation-proxy-acquire` and `sector-rotation-recent-stress` test the candidates on recent public proxy data.
- Currency-basket screen: `currency-basket-screen` tests lagged FXA/UUP, FXF/UUP, and CYB/UUP currency ETF rotation against EURUSD/USDJPY H4; `recent-currency-basket-proxy-acquire` and `currency-basket-recent-stress` test available candidates on recent public proxy data and explicitly record that Yahoo returned no usable recent CYB rows.
- Bond-volatility screen: `bond-vol-screen` tests lagged MOVE Treasury-rate volatility context against EURUSD/USDJPY H4; `recent-bond-vol-proxy-acquire` and `bond-vol-recent-stress` test the candidates on recent public proxy data.
- Crypto-risk screen: `crypto-risk-screen` tests lagged BTC-USD risk-on/risk-off context against EURUSD/USDJPY H4; `recent-crypto-risk-proxy-acquire` and `crypto-risk-recent-stress` test the candidates on recent public proxy data.
- External flow screen: `external-flow-screen` tests lagged daily currency ETF relative-flow proxies (`FXE/UUP`, `FXY/UUP`) against EURUSD/USDJPY H4.
- Demo-forward-test spec: not prepared because there is no survivor.
- Data caveat: local broker Forex bars end around 2025-06/2025-07. Public proxy data is useful for recency triage but cannot approve a broker EA.
