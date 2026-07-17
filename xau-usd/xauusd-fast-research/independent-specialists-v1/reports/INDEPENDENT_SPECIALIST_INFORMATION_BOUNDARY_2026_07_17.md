# XAUUSD Independent Specialist Information Boundary

Date: `2026-07-17`

## Decision

The current historical information set does not contain a verified portfolio of
multiple independent XAUUSD specialists under the locked cost, chronology,
drawdown, concentration, and frequency requirements.

Do not train or authorize an execution model from these results. A model may not
convert rejected candidate families into approved labels merely by scoring them.

## Strongest Remaining Candidate

`R1` is a credible long uptrend near-survivor on the independent Dukascopy feed:

| Stage | Trades | Stress PF | Average R | Drawdown R | Top five removed R | Result |
|---|---:|---:|---:|---:|---:|---|
| Replication fit | 48 | 1.965 | 0.490 | 6.699 | 14.037 | PASS |
| Development | 28 | 1.805 | 0.436 | 4.555 | 2.694 | FAIL sample only, 28 required 30 |
| Exam | 41 | 2.911 | 0.778 | 3.696 | 22.263 | PASS |

R1 passes every economic, drawdown, stability, and winner-concentration check.
It misses only two development trades. It remains research-only and needs
prospective shadow evidence rather than retrospective threshold changes.

## New Independent-Mechanism Results

### Archived macro composite portability

The fixed H4 macro risk-state vote was reproduced on the continuous Dukascopy
feed with conservative FRED release lags and native bid/ask execution.

| Stage | Trades | Trades/day | Stress PF | Average R | Result |
|---|---:|---:|---:|---:|---|
| Replication fit | 61 | 0.039 | 0.828 | -0.091 | FAIL |
| Development | 67 | 0.072 | 0.650 | -0.221 | Ineligible |
| Exam | 31 | 0.053 | 1.230 | 0.089 | Ineligible and concentrated |

Decision: `REJECT_MACRO_COMPOSITE_PORTABILITY`.

### COMEX session-VWAP specialists

Two new fixed families used the already downloaded Databento COMEX trades. No
new purchase or payment was made.

| Family | Stage | Trades/day | Stress PF | Average R | Result |
|---|---|---:|---:|---:|---|
| VWAP pullback continuation | Fit | 0.190 | 0.601 | -0.320 | FAIL |
| VWAP pullback continuation | Development | 0.226 | 0.759 | -0.181 | Ineligible |
| VWAP exhaustion reversion | Fit | 0.458 | 0.538 | -0.351 | FAIL |
| VWAP exhaustion reversion | Development | 0.506 | 0.662 | -0.233 | Ineligible |

Decision: `REJECT_COMEX_SESSION_VWAP_V1`. Do not extend the VWAP cache for these
rules.

## Closed Routes

The following routes are already falsified or fail portability and must not be
repeated without a materially new information source:

- price-only compression outside R1, including the broader baseline and R1B;
- archived R2 short pullback/continuation rules;
- H4 and D1 Donchian trend grids, H1 pullback resumption, daily RSI exhaustion,
  session carry, opening-range, sweep/reclaim, and simple mean reversion;
- XAU/XAG relative value, lead-lag, FX composite, cross-asset residual, and
  futures/spot basis rules;
- slow FRED/CFTC macro families and direct intraday DXY/Treasury pressure;
- COMEX flow continuation, absorption reversal, flow fading, context ranking,
  M15 ranking, regular-hour ranking, and session VWAP;
- broad M15 cost-aware momentum/reversion ML rankers;
- the high-frequency breakout/retest family, which remains
  `COST_SUSPENDED_CANONICAL` after confirmed measured-cost failure.

## Information Required To Continue

At least one of these must become available before another independent specialist
campaign has a defensible prior:

1. Prospective R1 shadow labels, with no rule changes, until a meaningful new
   sample is accumulated.
2. Primary order-book depth such as MBP-10/MBO, acquired only under an explicit
   zero-payment source or later owner authorization. The deleted Databento
   account and no-payment rule prohibit accidental paid acquisition.
3. A causal gold-options surface or skew history with auditable timestamps and
   zero-payment licensing.
4. Synchronized historical quotes from multiple executable brokers to test
   venue dislocation and execution quality.
5. A materially revised objective that accepts lower frequency. The surviving
   evidence does not support forcing two XAUUSD trades per day.

## Authorization

- Python prediction: not authorized.
- EA consumption: not authorized.
- Demo execution from these new candidates: not authorized.
- Live or real-capital execution: not authorized.
- Databento payment: not authorized.

The honest result of this campaign is one high-quality near-survivor, R1, and a
well-defined information boundary. Inventing additional trades from rejected
families would weaken evidence rather than advance the objective.
