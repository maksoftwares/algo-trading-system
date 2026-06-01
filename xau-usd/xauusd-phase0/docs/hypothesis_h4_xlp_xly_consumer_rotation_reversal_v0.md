# H4 XLP/XLY Consumer Rotation Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 consumer-defensive-versus-discretionary rotation / XAU overreaction reversal
Entry / decision timeframe: H4 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 96-336
Expected median hold hours: 16-56
Expected decisions per week: 0-4 during active consumer rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 25-450
Expected cost-adjusted PF: 1.05-1.70
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -30R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H4 reversal attempts with losses near -1R and occasional 1.55R wins when XAU rejects a multi-session move after consumer defensive/discretionary rotation is stretched.
Hypothesis SHA256: pending registration
Expert: `h4_xlp_xly_consumer_rotation_reversal_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, demo attachment, or live execution.

## Mechanical Definition

This candidate uses shifted public daily XLP/XLY ETF OHLCV proxy data from `data/reference/etf/xlp_xly_daily_yahoo_2015_2025.csv`. The proxy is not primary consumer-sector futures, equity index futures, or order-flow data.

Consumer rotation:

```text
xlp_return_5d = log(XLP close / XLP close 5d ago)
xly_return_5d = log(XLY close / XLY close 5d ago)
consumer_rotation_5d = xlp_return_5d - xly_return_5d
abs(consumer_rotation_5d) >= 0.0090
abs(consumer_rotation_z126) >= 0.35
consumer_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
consumer_rotation_5d >= +0.0090
XAU H4 12-bar return <= -0.0045
XAU H4 24-bar return >= -0.0450
XAU H4 6-bar return <= +0.0010
current H4 candle closes bullish
current H4 close location >= 0.60
current close is not more than 2.50 ATR below EMA40
```

Short setup:

```text
consumer_rotation_5d <= -0.0090
XAU H4 12-bar return >= +0.0045
XAU H4 24-bar return <= +0.0450
XAU H4 6-bar return >= -0.0010
current H4 candle closes bearish
current H4 close location <= 0.40
current close is not more than 2.50 ATR above EMA40
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.15 x H4 ATR(14)
Target: 1.55R
Time stop: 7 H4 bars
Duplicate control: maximum one signal per ISO week per direction
```

## Expected Behavior

The strategy should capture XAU reversal after consumer defensive-versus-discretionary rotation becomes stretched and XAU rejects a multi-session move. It is the opposite timing expression of the rejected H1 XLP/XLY follow-through candidate, moved to H4 to reduce execution-cost pressure and avoid H1 noise.

## Why This Hypothesis Should Exist

XLP/XLY is a traded proxy for consumer defensive demand versus discretionary risk appetite. Strong XLP leadership can conflict with a local gold selloff, while strong XLY leadership can conflict with a local gold rally. The candidate waits for completed H4 rejection rather than following the consumer rotation immediately.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if XLP/XLY observations are not shifted before XAU H4 decisions. Do not tune v0 after results are known.

## Code Mapping

- Strategy: `src/phase0/strategies/h4_xlp_xly_consumer_rotation_reversal_v0.py`
- XLP/XLY context loader: `src/phase0/xlp_xly_consumer_rotation_data.py`
- Matrix data-context injection: `src/phase0/matrix.py`
- Synthetic smoke context: `src/phase0/synthetic.py`
- Focused smoke test: `tests/test_h4_xlp_xly_consumer_rotation_reversal_v0.py`

## Safety Boundary

This is Phase 0 research code only. It must not place orders, modify positions, call MT5 trading APIs, or be attached to demo/live accounts. Any passing result only authorizes review and later dry-run planning, never live execution.
