# H4 CME CVOL Skew Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: CME Gold options-skew / implied-variance stress reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 96-288
Expected median hold hours: 8-24
Expected decisions per week: 1-5
Timeframe diversification qualifies: yes
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.60R reversals after options-implied variance imbalance aligns with an H4 spot exhaustion candle. Reject if results require changing the variance imbalance thresholds, CVOL percentile, H4 return threshold, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path. Real matrix execution is blocked until licensed CME Gold CVOL history is supplied.

Expert id: `h4_cme_cvol_skew_reversal_v0`

Independence: High. This is not a level retest, round-number, intraday breakout, session, ETF-flow, COT, macro-rate, VIX/GVZ proxy, or OHLC-only pattern.

## Mechanical Definition

This candidate trades XAUUSD H4 reversals when licensed CME Gold CVOL data shows elevated options-implied risk and a strong directional variance imbalance.

Required external data:

```text
data/reference/options/cme_cvol_gold_daily.csv
```

Required columns:

```text
timestamp_utc
gold_cvol
gold_upvar
gold_downvar
gold_skew
gold_atm
gold_convexity
```

The data must cover the full matrix window before a real run is allowed.

Rules:

1. Build H4 ATR(14), H4 EMA(40), and 12-H4-bar log return from XAUUSD H4 bars.
2. Load daily CME Gold CVOL data and shift all CVOL-derived features by one observation before merging into H4 bars.
3. Compute `down_up_imbalance = gold_downvar - gold_upvar`.
4. Compute `down_up_ratio = gold_downvar / gold_upvar`.
5. Compute rolling CVOL percentile over 252 observations.
6. Compute rolling z-score of `down_up_imbalance` over 126 observations.
7. Long setup:
   - `cvol_percentile252 >= 0.55`
   - `down_up_imbalance_z126 >= 0.70` or `down_up_ratio >= 1.12`
   - 12-H4 return <= -0.0035
   - Current H4 candle closes above open
   - Close location is in the upper 45% of the H4 range
   - Close is not more than 0.45 H4 ATR above EMA(40)
8. Short setup:
   - `cvol_percentile252 >= 0.55`
   - `down_up_imbalance_z126 <= -0.70` or `down_up_ratio <= 0.90`
   - 12-H4 return >= 0.0035
   - Current H4 candle closes below open
   - Close location is in the lower 45% of the H4 range
   - Close is not more than 0.45 H4 ATR below EMA(40)
9. At most one setup per UTC day and direction.
10. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
11. Stop: 1.20 H4 ATR beyond the estimated entry.
12. Target: 1.60R.
13. Time stop: 288 M5 bars, equal to six H4 bars.
14. Invalidation: no setup if CME CVOL data, H4 ATR, H4 EMA, skew/variance features, or stop/target construction are unavailable.

## Expected Behavior

Expected trade count: Unknown until licensed CME CVOL history is available. Minimum expectation for a valid first pass remains at least 40 trades per cell unless a frequency-normalized reviewer-approved test is explicitly used.

Expected PF: >= 1.30 in at least 7 of 9 cells.

Expected losing-month percentage: <= 45%.

Expected worst month: no worse than -8R at Phase 0 fixed-risk normalization.

Expected max zero-trade months: <= 3.

Expected R distribution: modest average win/loss asymmetry near the 1.6R target, with enough losing trades to prove this is not a sparse one-event artifact.

## Why This Hypothesis Should Exist

Gold options markets may price asymmetric risk before or during spot dislocations. If downside option variance becomes unusually expensive while H4 spot has already sold off and begins rejecting lower prices, the setup may capture panic exhaustion rather than continuation. The mirrored short case tests whether upside variance stress after a sharp H4 rally can similarly precede exhaustion.

This is a higher-timeframe and options-derived mechanism. It is materially different from the approved breakout/retest family and may reduce cost pressure if it produces fewer, larger-R trades.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- Licensed CME CVOL data cannot cover the required matrix period.
- Fewer than 7 of 9 cells reach PF >= 1.30.
- Trade count, activity, concentration, cost-sensitivity, decile, multisymbol, or adversarial gates fail.
- Performance depends on one broker, one cost model, one time window, or one gold shock episode.
- The only positive result appears after changing thresholds based on first-pass output.

## Code Mapping

- CME CVOL data contract: `src/phase0/cme_cvol_gold_data.py`
- H4/CVOL feature construction: `src/phase0/strategies/h4_cme_cvol_skew_reversal_v0.py::H4CmeCvolSkewReversalV0Strategy.prepare_features`
- H4 setup classification: `src/phase0/strategies/h4_cme_cvol_skew_reversal_v0.py::H4CmeCvolSkewReversalV0Strategy._setup_at_row`
- Stop/target construction: `src/phase0/strategies/h4_cme_cvol_skew_reversal_v0.py::H4CmeCvolSkewReversalV0Strategy.build_trade_plan`
