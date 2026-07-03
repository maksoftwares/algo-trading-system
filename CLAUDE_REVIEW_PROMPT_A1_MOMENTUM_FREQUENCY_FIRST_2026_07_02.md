# Claude Review Request - A1 XAU M5 Momentum Frequency-First Candidate

Please independently review Codex's latest high-frequency XAUUSD M5 candidate. Be skeptical about overfitting, but keep the project objective in view: we need multiple trades per active day, win rate above 50%, and positive expectancy. Sparse two-trade-per-month strategies do not satisfy the business goal even if they look robust.

Primary review packet:
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_REVIEW_PACKET_2026_07_02.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_REVIEW_PACKET_2026_07_02.json`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_HOUR_MASK_ROBUSTNESS_2026_07_02.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_EXIT_PROTECTION_DIAGNOSTIC_2026_07_02.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_LONG_RR0P7_V4_COMBO_RANK1_FORWARD_2026_07_02.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_LONG_RR0P7_V4_COMBO_RANK1_FORWARD_2026_07_02.sha256.json`

Primary source files:
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_freq_first_v4_four_year_2022_07_2026_06_20260701\A1XauM5Momentum_FREQ_FIRST_V4_FOUR_YEAR_2022_07_2026_06_XAUUSD_M5_freq_h1_h4_long_rr0p7_v4_combo_rank1_trades.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_freq_first_v4_four_year_2022_07_2026_06_20260701\A1XauM5Momentum_FREQ_FIRST_V4_FOUR_YEAR_2022_07_2026_06_XAUUSD_M5_freq_h1_h4_long_rr0p7_v4_combo_rank1_orders.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_freq_first_v4_four_year_2022_07_2026_06_20260701\A1XauM5Momentum_FREQ_FIRST_V4_FOUR_YEAR_2022_07_2026_06_XAUUSD_M5_freq_h1_h4_long_rr0p7_v4_combo_rank1_signals.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.json`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_v4_lock06_four_year_usd_2022_07_2026_06_20260701\A1XauM5Momentum_V4_LOCK06_FOUR_YEAR_USD_2022_07_2026_06_XAUUSD_M5_v4_lock06_trades.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_LOCK06_FOUR_YEAR_USD_2022_07_2026_06.md`

Candidate under review:
- `freq_h1_h4_long_rr0p7_v4_combo_rank1`
- LONG-only XAUUSD M5 momentum continuation
- H1+H4 EMA alignment required
- target `0.7R`
- `cost_R <= 0.05`
- blocked server hours `2,9,10,11,12,13,17,19,21,23`
- max `12` trades/day
- cooldown `5` minutes

Please do the following:
1. Recompute the headline numbers from the source CSVs: 1132 trades, 65.90% WR, +1042.07 USD, PF 1.45, 383 active entry days, 2.96 trades/active entry day, 36 positive months / 11 negative active months.
2. Verify the OOS split: older window `2022.07-2024.06` has 520 trades, 65.00% WR, +309.24, PF 1.40; recent window `2024.07-2026.06` has 612 trades, 66.67% WR, +732.83, PF 1.47.
3. Challenge whether blocking server hours `2,9,10,11,12,13,17,19,21,23` is justified, whether this is overfit from the hour-combination search, and whether V3's higher PF should be preferred over V4's higher frequency.
4. Review the loss anatomy: hours, months, duration, ATR, stop size, cost_R, break strength, and outlier dependence.
5. Tell us exactly what would make this candidate fail despite the attractive WR/frequency profile.
6. Review the V4 hour-mask robustness note. Nearby exact MT5 masks rank 2-4 all stayed profitable with 65%+ WR and PF 1.46-1.50. Tell us whether this sufficiently reduces hour-mask overfit risk, or whether the mask is still too selected for forward demo.
7. Review the V4 exit-protection diagnostic. `v4_lock06` raises win rate from 65.90% to 68.60% but lowers net from +1042.07 to +966.84 with similar PF. Tell us whether forward demo should test plain V4 only, `v4_lock06` only, or both as separate isolated demo lanes with separate magic numbers.
8. If you endorse it, provide the exact frozen forward-demo spec and kill rules. If you revise/reject, provide the next most promising repair path that preserves trade frequency.

Additional provenance/companion diagnostics:
- Hour-combination search: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.md`
- Hour-mask robustness: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_HOUR_MASK_ROBUSTNESS_2026_07_02.md`
- Short-side companion diagnostic: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_SHORT_COMPANION_DIAGNOSTIC_2026_07_02.md`
- Exit-protection diagnostic: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_EXIT_PROTECTION_DIAGNOSTIC_2026_07_02.md`
- Codex conclusion: Plain V4 is still the primary review candidate because it has higher net and simpler execution. `v4_lock06` is a legitimate alternate if the owner prioritizes smoother win rate over maximum net. Short-side companions should remain diagnostic-only because practical short variants failed the older OOS split.

Important boundary:
- Do not recommend live trading or real capital.
- Do not treat this as canonical Phase 2 approval.
- Demo forward test only, minimum lot, no mid-test tuning.
