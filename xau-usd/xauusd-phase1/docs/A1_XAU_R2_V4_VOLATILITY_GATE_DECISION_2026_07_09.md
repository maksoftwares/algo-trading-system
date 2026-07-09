# A1 XAU R2 V4 Volatility Gate Decision

Date: 2026-07-09

## Decision

R2 backtest tuning is frozen.

Carry forward both V1 and V4 as shadow-only controls:

| Candidate | Role | Status |
| --- | --- | --- |
| `r2_impulse_retest_body45` | raw profit leader / control baseline | shadow only |
| `r2_impulse_body45_atr45` | primary V4 quality candidate | shadow only |
| `r2_impulse_body45_atr50` | stricter V4 quality sensitivity | shadow only |
| `r2_impulse_body45_atr45_daily_loss10` | containment diagnostic only | shadow only |

No R2 variant is demo-ready. No R2 variant is approved for forward execution.

## Reason

V1 remains the raw profit leader:

| Book | Trades | WR | W/L | PF | Net | Recent 3M Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V1 raw combined | 1,060 | 44.72% | 3.0454 | 2.4634 | +$9,750.48 | +$818.35 |

V4 is the quality leader:

| Book | Trades | WR | W/L | PF | Net | Recent 3M Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V4 ATR45 + daily loss10 combined | 678 | 51.03% | 2.6082 | 2.7182 | +$9,640.05 | +$764.92 |

V4 improved WR, PF, and May 2026 behavior, but it sacrificed full-window net, recent-three-month net, and trade count. It is also concentrated in recent high-volatility 2026 downside conditions, so it is not durable standalone proof.

## Accepted Review Findings

- V4 is structurally plausible, but recent-regime biased.
- V4 neutralizes May-style damage mostly by removing lower-volatility continuation attempts.
- The absolute ATR floor `4.50` is acceptable as a frozen diagnostic, not as a final production threshold.
- `atr45_daily_loss10` is not the primary V4 identity because the daily loss stop only fired twice and added about +$21 versus ATR45.
- Further R2 parameter tuning now carries more overfit risk than value.

## Frozen R2 Boundary

Allowed R2 work:

- documentation;
- audit;
- V1/V4 shadow comparison;
- forward observation;
- reviewer review.

Forbidden R2 work:

- no V5 R2 parameter pass;
- no new ATR values;
- no session, hour, day, or month masks;
- no R2 router relaxation;
- no extra H1/H4/D1 filters stacked onto R2;
- no breakeven, partial, trailing, or RR change;
- no demo or forward execution spec.

## Next Direction

After completing the ATR-floor audit and V1/V4 shadow-control spec, move new strategy research to a separate chop / failed-breakdown specialist. R2 should remain a clean downtrend continuation specialist, not a chop handler.
