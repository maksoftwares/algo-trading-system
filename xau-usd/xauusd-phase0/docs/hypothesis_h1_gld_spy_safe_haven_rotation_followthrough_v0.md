# H1 GLD/SPY Safe-Haven Rotation Followthrough v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: GLD/SPY relative safe-haven rotation followthrough
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 60-120
Expected median hold hours: 5-10
Expected decisions per week: 0-10
Timeframe diversification qualifies: yes
Expected trade count per year: 80-450
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small 1R losses, occasional 1.5R trend-followthrough winners after GLD materially outperforms or underperforms SPY. Reject if results require changing thresholds, confirmation rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h1_gld_spy_safe_haven_rotation_followthrough_v0` tests whether shifted GLD/SPY 5-day relative strength identifies gold safe-haven preference that spills into XAU H1 trend followthrough.

Data source:

- GLD ETF daily OHLCV proxy from Yahoo Finance chart API symbol `GLD`.
- SPY daily OHLCV proxy from the existing Yahoo QQQ/SPY reference file.
- Both sources are public non-primary ETF proxies, not COMEX order-flow, not broker fill data, and not live execution evidence.
- Every GLD/SPY feature is shifted by one daily observation before merging into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, or 21:00 UTC.
2. Compute shifted 5-day GLD return, shifted 5-day SPY return, `gld_spy_rotation_5d = GLD 5d return - SPY 5d return`, 126-day z-score, and 252-day absolute percentile.
3. Rotation is active when:
   - absolute `gld_spy_rotation_5d` >= 0.0120
   - absolute 126-day z-score >= 0.35
   - absolute 252-day percentile >= 0.55
4. Long setup:
   - GLD/SPY rotation >= +0.0120
   - XAU H1 close > EMA50
   - XAU H1 EMA21 >= EMA50
   - XAU H1 12-bar return >= +0.0015
   - XAU H1 6-bar return >= -0.0005
   - XAU H1 24-bar return <= +0.0250
   - current H1 candle closes above open
   - current H1 close location >= 0.60
5. Short setup:
   - GLD/SPY rotation <= -0.0120
   - XAU H1 close < EMA50
   - XAU H1 EMA21 <= EMA50
   - XAU H1 12-bar return <= -0.0015
   - XAU H1 6-bar return <= +0.0005
   - XAU H1 24-bar return >= -0.0250
   - current H1 candle closes below open
   - current H1 close location <= 0.40
6. Entry is simulated at market from the signal bar close.
7. Stop is 1.05 x H1 ATR14 from entry.
8. Target is 1.50R.
9. Time stop is 10 H1 bars.
10. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-450 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if GLD/SPY relative strength contains tradable XAU followthrough information.
Expected losing-month percentage: below 55%.
Expected worst month: no worse than -10R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

Many rejected intermarket candidates used risk rotation proxies that were not gold-specific. GLD/SPY relative strength is closer to the question we care about: whether capital is preferring gold exposure over broad equity exposure. If that safe-haven preference is persistent, XAU should show H1 followthrough when the local H1 trend agrees with the shifted daily GLD/SPY state.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
