# H1 Walk Forward Linear State v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Auditable walk-forward learned H1 state
Entry / decision timeframe: H1 completed-candle decision, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 1-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-260
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many model misses near -1R, fewer +1.5R winners, and rejection if the learned state only works in one broker window.

## Mechanical Definition

This candidate is a research-only walk-forward learned-state hypothesis for XAUUSD. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, gold/silver relative-value, fixed autocorrelation-state, M5 path-skew, or tick-volume climax rule.

The intended mechanical setup is:

1. Market and decision timeframe: XAUUSD H1 bars only.
2. Execution timeframe: M5 bars are used only by the existing simulator for market-entry and exit sequencing.
3. Features: compute completed-bar H1 momentum, close-versus-EMA state, range in ATR, realized-volatility ratio, directional efficiency, and tick-count z-score when available.
4. Label: for historical training rows only, label the next 12 H1 bars of normalized forward return.
5. Walk-forward rule: at each scoring point, train a small ridge-regularized linear model only on rows whose 12-bar future label is already fully known before the current signal timestamp.
6. Update cadence: model weights are refreshed on a fixed bar cadence and then applied to the current completed H1 feature vector.
7. Long setup: model score exceeds the locked positive threshold.
8. Short setup: model score is below the locked negative threshold.
9. Frequency control: take at most one signal per UTC day and direction.
10. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
11. Stop: ATR-based XAUUSD stop using only completed H1 data.
12. Target: fixed R multiple between 1.4R and 1.7R, selected in the locked implementation before any result-producing run.
13. Invalidation: no setup if the model has fewer than the minimum completed historical labels, features are incomplete, or stop/target construction creates non-positive risk.

## Expected Behavior

Expected behavior is adaptive short-horizon continuation or reversal depending on the learned local H1 state. This is the first proper AI-style research lane because the signal is learned walk-forward rather than a fixed hand-authored threshold. It must remain fully auditable: fixed features, fixed label horizon, fixed training window, fixed regularization, fixed update cadence, and no external model calls.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must be reproducible from local data and the locked model recipe.

## Why This Hypothesis Should Exist

The fixed-rule search has produced many adequate-frequency failures. A walk-forward learned state may discover a simple local relationship among existing H1 features without introducing discretionary logic or leaking future data. This is a controlled way to integrate AI thinking into Phase 0 while preserving falsifiability.

The hypothesis should only pass if the learned state survives across Capital.com, Pepperstone, and Dukascopy windows. If it overfits one window or collapses under costs, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the feature set, label horizon, training window, thresholds, or regularization after results are known without creating a new versioned hypothesis.
