# H4 SLV/GLD Precious-Beta Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 precious-metals beta rotation / XAU multi-session exhaustion reversal
Entry / decision timeframe: H4 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 96-576
Expected median hold hours: 8-48
Expected decisions per week: 0-8 during SLV/GLD rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 25-450
Expected cost-adjusted PF: 1.05-1.70
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -30R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H4 reversal attempts with stop losses near -1R and occasional 1.55R wins when XAU rejects a multi-session move after silver/gold beta rotation is stretched.
Hypothesis SHA256: pending registration
Expert: `h4_slv_gld_precious_beta_reversal_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public daily SLV/GLD ETF OHLCV proxy data from `data/reference/etf/slv_gld_daily_yahoo_2015_2025.csv`. The proxy is not primary COMEX order flow.

Precious-beta rotation:

```text
slv_return_5d = log(SLV close / SLV close 5d ago)
gld_return_5d = log(GLD close / GLD close 5d ago)
precious_rotation_5d = slv_return_5d - gld_return_5d
abs(precious_rotation_5d) >= 0.0120
abs(precious_rotation_z126) >= 0.35
precious_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
precious_rotation_5d <= -0.0120, meaning SLV is materially underperforming GLD
XAU H4 6-bar return <= -0.0030
XAU H4 3-bar return >= -0.0010
XAU H4 12-bar return >= -0.0500
current H4 candle closes bullish
current H4 close location >= 0.58
current close is not more than 2.50 ATR below EMA40
```

Short setup:

```text
precious_rotation_5d >= +0.0120, meaning SLV is materially outperforming GLD
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

The strategy should capture XAU reversal after silver/gold beta rotation becomes stretched and XAU rejects a multi-session move. It is the opposite timing expression of the rejected H1 SLV/GLD follow-through candidate, moved to H4 to reduce execution-cost pressure and avoid H1 noise.

## Why This Hypothesis Should Exist

Silver often behaves as the higher-beta precious metal while GLD proxies institutional gold demand. A large SLV/GLD rotation can mark risk-on/risk-off precious-metals pressure that may overshoot in XAU before reversing on a completed H4 rejection candle. This remains distinct from retest, round-number, session, macro-yield, CNY-dollar, options-volatility, credit-risk, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if SLV/GLD observations are not shifted before XAU H4 decisions. Do not tune v0 after results are known.

## Code Mapping

- Strategy: `src/phase0/strategies/h4_slv_gld_precious_beta_reversal_v0.py`
- SLV/GLD context loader: `src/phase0/slv_gld_precious_rotation_data.py`
- Matrix data-context injection: `src/phase0/matrix.py`
- Synthetic smoke context: `src/phase0/synthetic.py`
- Focused smoke test: `tests/test_h4_slv_gld_precious_beta_reversal_v0.py`

## Safety Boundary

This is Phase 0 research code only. It must not place orders, modify positions, call MT5 trading APIs, or be attached to demo/live accounts. Any passing result only authorizes review and later dry-run planning, never live execution.
