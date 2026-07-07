# A1 XAU Asia-Range M5 V16 Preregistration

Date: 2026-07-07

## Goal

Test one distinct, naturally frequent source without adding more EA code: continuation/reversal around the fixed 00:00-06:00 broker-time Asian range, using the existing exact-MT5 opening-range signal modes.

## Fixed Grid

| Variant | Mode | Range | Trade window | Target |
|---|---|---|---|---:|
| `v16_asia_range_cont_rr2` | continuation | 00:00-06:00 | next 16h | 2.0R |
| `v16_asia_range_cont_rr15` | continuation | 00:00-06:00 | next 16h | 1.5R |
| `v16_asia_range_reversal_rr2` | reversal | 00:00-06:00 | next 16h | 2.0R |
| `v16_asia_range_reversal_rr15` | reversal | 00:00-06:00 | next 16h | 1.5R |

Shared settings: risk-normalized `$10`, max lots `0.05`, cost cap `0.08R`, max trades/day `8`, cooldown `15m`.

## Decision Rule

No optimizer, hour expansion, direction split, or threshold tuning in this pass. Freeze if it does not materially improve hybrid positive weeks while preserving plausible standalone edge.
