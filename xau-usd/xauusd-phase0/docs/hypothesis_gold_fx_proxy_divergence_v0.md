# Hypothesis: gold_fx_proxy_divergence_v0

Expert name: gold_fx_proxy_divergence_v0
Hypothesis date: 2026-05-25
Hypothesis version: v0.1
Author / owner: Project owner and Codex research assistant
Mechanic family: intermarket / macro-regime / relative-strength continuation
Entry / decision timeframe: H1 decision, next available execution simulation
Expected median hold bars M5-equivalent: 96
Expected median hold hours: 8
Expected decisions per week: 2 to 5
Timeframe diversification qualifies: no

## Mechanical Definition

This candidate is a bidirectional XAUUSD intermarket relative-strength expert. It uses completed H1 bars for XAUUSD and a USD proxy built from EURUSD and USDJPY. The USD proxy is:

```text
usd_proxy_return_24h = mean(-EURUSD_log_return_24h, USDJPY_log_return_24h)
```

The strategy also calculates:

```text
xau_return_24h = XAUUSD_log_return_24h
rolling_beta = rolling_250h_beta(xau_return_24h, usd_proxy_return_24h)
xau_expected_return = rolling_beta * usd_proxy_return_24h
xau_residual_return = xau_return_24h - xau_expected_return
usd_proxy_z = rolling_250h_zscore(usd_proxy_return_24h)
xau_residual_z = rolling_250h_zscore(xau_residual_return)
xau_ema20 = EMA20 of XAUUSD H1 close
xau_atr14 = ATR14 of XAUUSD H1
```

All signals require at least 300 completed H1 bars of synchronized data and no open position for this expert.

Long setup:

1. `usd_proxy_z >= +1.00`, meaning broad USD strength is present.
2. `xau_residual_z >= +0.75`, meaning XAUUSD is stronger than its USD-proxy-implied return.
3. The latest completed XAUUSD H1 close is above `xau_ema20`.
4. The current H1 candle body is positive.
5. No trade has already been emitted in the same ISO week and direction.

Short setup:

1. `usd_proxy_z <= -1.00`, meaning broad USD weakness is present.
2. `xau_residual_z <= -0.75`, meaning XAUUSD is weaker than its USD-proxy-implied return.
3. The latest completed XAUUSD H1 close is below `xau_ema20`.
4. The current H1 candle body is negative.
5. No trade has already been emitted in the same ISO week and direction.

Trade plan:

- Entry type: market at the next available execution quote after the completed H1 signal.
- Long stop: signal close minus `1.10 * xau_atr14`.
- Short stop: signal close plus `1.10 * xau_atr14`.
- Take profit: fixed `1.80R`.
- Time stop: exit after 12 completed H1 bars if neither stop nor target has fired.
- Pyramiding: disabled.
- One open position per expert: enforced by the Phase 0 engine.

This hypothesis requires a cross-symbol data contract. A Phase 0 result run is not meaningful until XAUUSD, EURUSD, and USDJPY H1 bars are synchronized for the evaluated broker/window or a documented DXY proxy replaces the two-FX proxy.

## Expected Behavior

Expected trade count per year: 150 +/- 30

Expected cost-adjusted PF: 1.35 +/- 0.25

Expected losing-month percentage: 42% +/- 10%

Expected worst single month: $-900

Expected max consecutive zero months: 1

Expected R-multiple distribution: Most losses should cluster near -1R; most wins should cluster near +1.8R; the median trade may be slightly negative after modeled costs, so the edge must come from enough follow-through after relative-strength divergence rather than from frequent small wins.

## Why This Hypothesis Should Exist

The current approved family depends on XAUUSD level behavior: breaks, retests, and continuation after a level holds. This candidate tests a different information source. It asks whether gold-specific flow can be detected when XAUUSD refuses to follow a broad USD move.

If gold rises during USD strength, the move may reflect safe-haven demand, metals-specific flow, central-bank/institutional buying, or other non-FX pressure. If gold falls during USD weakness, the opposite pressure may be present. The candidate tries to follow that relative strength for several hours using only completed H1 data and fixed risk rules.

This candidate is intentionally not a retest, reclaim, round-number, session-extreme, sweep, pivot, inside-bar, or XAU-only volatility pattern. It should only remain in the research lane if the intermarket input adds information that survives costs and cross-window testing.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 research run:

- Fewer than 7 of 9 matrix cells reach PF >= 1.30.
- Any matrix cell has fewer than 40 trades.
- Any matrix cell breaches the configured drawdown or total-return failure limits.
- The candidate fails the forward concentration gates, including frequency-normalized concentration.
- Pepperstone plus Dukascopy average PF is below 1.20.
- Performance is dominated by one venue, one year, or one small cluster of macro shock periods.
- The edge only appears when EURUSD/USDJPY proxy data is unavailable, stale, or misaligned.
- Manual adversarial review finds logic-gap losing trades above the allowed threshold.
- The strategy behaves like a disguised level/retest candidate rather than an intermarket relative-strength candidate.
