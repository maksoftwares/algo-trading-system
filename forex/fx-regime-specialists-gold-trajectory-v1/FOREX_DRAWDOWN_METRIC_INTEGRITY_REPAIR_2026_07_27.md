# Forex Drawdown Metric Integrity Repair — 2026-07-27

Status: `REPORTING_CORRECTION_NO_DECISION_CHANGE`

During the S1 cycle-exit work, the common offline metric helper was found to initialize peak equity at the first trade's cumulative result instead of zero.

That understates drawdown when a ledger or reporting slice begins with a loss. The helper now prepends zero equity before calculating the running peak and drawdown.

## Scope

- Signal generation: unchanged.
- Regime ownership: unchanged.
- Entries and exits: unchanged.
- Trade count, R, PF, expectancy, win rate, and stress P/L: unchanged.
- Only affected maximum-drawdown fields changed.
- No admission or portfolio decision changed.

Material corrected examples:

- Cross-asset R1 overall max drawdown: 31.7021R → 32.7077R.
- Cross-asset R2 overall max drawdown: 41.6356R → 41.6514R.
- Seed-decomposition S2 validation max drawdown: 0.0000R → 1.0024R.

The S1 established-aligned overall max drawdown remains 3.0041R because its ledger began with a winning trade and later peak-to-trough drawdown was already the maximum.
