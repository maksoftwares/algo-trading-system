# XAUUSD COMEX Session-VWAP Specialists V1

Date: `2026-07-17`

## Question

Can completed COMEX gold-futures session VWAP state define two cost-surviving,
mechanically distinct XAUUSD specialists when raw trade-flow continuation,
absorption, fading, and ML rankers have failed?

## Frozen Families

1. `COMEX_VWAP_PULLBACK_CONTINUATION_V1` follows the direction of the completed
   futures price relative to session VWAP. It requires a moderate `0.25-1.00`
   spot-ATR deviation, a same-direction six-bar VWAP slope of at least `0.05`
   ATR, aligned XAUUSD EMA20/EMA50 trend, a directional completed XAUUSD M5
   candle of at least `0.15 ATR`, directional close location at least `0.60`,
   and current futures volume at least `0.75` of its prior 20-bar median.
2. `COMEX_VWAP_EXHAUSTION_REVERSION_V1` trades opposite a futures deviation of
   at least `1.50` spot ATR. It requires absolute six-bar VWAP slope no greater
   than `0.25 ATR`, a completed XAUUSD reversal candle of at least `0.10 ATR`,
   directional close location at least `0.60`, and current futures volume at
   least its prior 20-bar median.

Both families trade only from `08:30` through `13:30 America/New_York`. The
continuation family uses a `1.25 ATR` stop, `2R` target, and six-hour maximum
hold. The reversion family uses a `1.25 ATR` stop, `1.5R` target, and four-hour
maximum hold.

## Causality And Execution

- Every COMEX row is available only at the end of its completed five-minute
  bucket. Joins are exact; future and stale VWAP rows are prohibited.
- Spot features use only the completed Dukascopy M5 bar at the same timestamp.
- Entry is the next contiguous spot M5 open, long at Ask and short at Bid.
- Long exits use Bid, short exits use Ask, and collisions are stop-first.
- Stress includes native spread, `$0.30` extra execution cost, `$0.35` per 24
  hours, and `0.05R` slippage.
- One position per family, one-hour cooldown, and at most two trades per family
  per UTC day.

## Firewall And Gates

- Fit: `2022-07-01` through `2023-07-01`.
- Development: `2023-07-01` through `2024-07-01`.
- No later COMEX period is prepared or evaluated in V1.

Fit requires at least 52 trades, `0.20` trades per source day, PF `1.15`, average
`0.03R`, drawdown no greater than `25R`, and positive P&L after removing the five
largest winners. Development tightens PF to `1.25`, average to `0.05R`, and
drawdown to `20R`. A failed fit makes development decision-ineligible.

Only a family passing both stages may authorize building the 2024-26 VWAP cache.
No result authorizes Python predictions, EA consumption, demo, live, or broker
actions. Same-version post-outcome tuning is forbidden.
