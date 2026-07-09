# A1 XAU R2 V1/V4 Shadow-Control Spec

Date: 2026-07-09

## Purpose

Freeze the current R2 short-specialist candidates and compare them side-by-side without further R2 tuning.

This is not a demo spec. This is a shadow-control protocol for future exact-MT5 / forward-shadow evidence.

## Frozen Candidates

| ID | Variant | Role |
| --- | --- | --- |
| `R2_V1_RAW` | `r2_impulse_retest_body45` | raw profit/control baseline |
| `R2_V4_ATR45` | `r2_impulse_body45_atr45` | primary quality candidate |
| `R2_V4_ATR50` | `r2_impulse_body45_atr50` | strict quality sensitivity |
| `R2_V4_ATR45_DL10` | `r2_impulse_body45_atr45_daily_loss10` | containment diagnostic only |

## Fixed Identity

All candidates remain:

- strict R2 downtrend router only;
- short-only;
- signal mode 19 downside impulse/retest;
- fixed 2R;
- no breakeven;
- no partial close;
- no trailing;
- no day/month/hour/session masks;
- no extra trend-stack filter;
- no router relaxation.

## Comparison Rules

Each future R2 evidence packet must report:

- full-window and latest-month trades;
- WR, W/L, PF, net, stress net after -$0.30/trade;
- monthly PnL;
- positive and negative months;
- max closed drawdown;
- V1 trades kept by V4;
- V1 trades removed by V4;
- PnL of kept versus removed trades;
- May/June-style analog months if present;
- ATR distribution at entry;
- whether V4 still preserves clean downside continuation.

## Promotion Boundary

No R2 candidate can be promoted from shadow until it has:

- forward-shadow evidence outside Apr-Jun 2026;
- enough non-2026 exposure to reduce recent-regime concentration risk;
- a completed ATR-floor audit;
- reviewer approval;
- no unresolved exact-MT5 reporting gaps.

## Stop Rule

If V1 keeps beating V4 on profit while V4 only improves cosmetic WR, do not tune R2. Keep both as controls and move research effort to the separate chop / failed-breakdown specialist.

If V4 keeps preserving most V1 profit while avoiding failed-breakdown months, keep V4 as the quality candidate, but still require out-of-sample shadow proof before any demo conversation.

## Forbidden Work

Do not create:

- `R2_V5`;
- new ATR threshold variants;
- ATR percentile implementation;
- new R2 filters;
- new R2 session/hour/day masks;
- altered RR variants.

Those ideas require a separate review and are not authorized by this spec.
