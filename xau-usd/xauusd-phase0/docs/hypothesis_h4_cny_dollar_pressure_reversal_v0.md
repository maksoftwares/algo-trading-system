# H4 CNY-Dollar Pressure Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 official CNY-dollar macro/FX pressure / XAU multi-session exhaustion reversal
Entry / decision timeframe: H4 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 96-576
Expected median hold hours: 8-48
Expected decisions per week: 0-6 during CNY-dollar pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 20-350
Expected cost-adjusted PF: 1.05-1.70
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -28R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H4 reversal attempts with stop losses near -1R and occasional 1.55R wins when XAU rejects a multi-session move after official CNY-dollar pressure is stretched.
Hypothesis SHA256: pending registration
Expert: `h4_cny_dollar_pressure_reversal_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses official public FRED daily macro/FX series:

- `DEXCHUS`: China / U.S. foreign exchange rate, Chinese yuan per U.S. dollar.
- `DTWEXBGS`: nominal broad U.S. dollar index.

The FRED observations are shifted by one completed daily observation before merging into XAU H4 decisions.

CNY-dollar pressure:

```text
cny_per_usd_return_5d = log(DEXCHUS / DEXCHUS 5d ago)
dollar_index_return_5d = log(DTWEXBGS / DTWEXBGS 5d ago)
cny_dollar_pressure_5d = cny_per_usd_return_5d + 0.50 * dollar_index_return_5d
abs(cny_dollar_pressure_5d) >= 0.0060
abs(cny_dollar_pressure_z126) >= 0.35
cny_dollar_pressure_abs_percentile252 >= 0.55
```

Long setup:

```text
CNY-dollar pressure >= +0.0060, meaning yuan weakness and broad dollar strength
XAU H4 6-bar return <= -0.0030
XAU H4 3-bar return >= -0.0010
XAU H4 12-bar return >= -0.0500
current H4 candle closes bullish
current H4 close location >= 0.58
current close is not more than 2.50 ATR below EMA40
```

Short setup:

```text
CNY-dollar pressure <= -0.0060, meaning yuan strength and broad dollar weakness
XAU H4 6-bar return >= +0.0030
XAU H4 3-bar return <= +0.0010
XAU H4 12-bar return <= +0.0500
current H4 candle closes bearish
current H4 close location <= 0.42
current close is not more than 2.50 ATR above EMA40
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.10 x H4 ATR(14)
Target: 1.55R
Time stop: 12 H4 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

The strategy should capture multi-session XAU reversal when official CNY-dollar pressure is stretched and the H4 path rejects continuation in the pressure-consistent direction. It is a slower-timing retest of the rejected H1 CNY-dollar reversion lane, not an in-place tune of the H1 rules.

## Why This Hypothesis Should Exist

The H1 CNY-dollar reversion candidate showed sparse Capital.com-only pockets that did not generalize. A possible reason is that official daily CNY and broad-dollar pressure acts too slowly for H1 timing. H4 timing gives the macro/FX signal more room to express while still using completed candles and shifted public data. This mechanism remains distinct from retest, round-number, session, GLD-flow, futures-volume, options-volatility, credit-risk, sector-rotation, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if FRED observations are not shifted before XAU H4 decisions. Do not tune v0 after results are known.

## Code Mapping

- Strategy: `src/phase0/strategies/h4_cny_dollar_pressure_reversal_v0.py`
- Official CNY-dollar context loader: `src/phase0/cny_dollar_pressure_data.py`
- Matrix data-context injection: `src/phase0/matrix.py`
- Synthetic smoke context: `src/phase0/synthetic.py`
- Focused smoke test: `tests/test_h4_cny_dollar_pressure_reversal_v0.py`

## Safety Boundary

This is Phase 0 research code only. It must not place orders, modify positions, call MT5 trading APIs, or be attached to demo/live accounts. Any passing result only authorizes review and later dry-run planning, never live execution.
