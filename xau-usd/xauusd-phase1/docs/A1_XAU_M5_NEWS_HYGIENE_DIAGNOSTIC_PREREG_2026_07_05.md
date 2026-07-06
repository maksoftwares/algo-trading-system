# A1 XAU M5 News-Hygiene Diagnostic Preregistration

Generated: 2026-07-05

## Purpose

This is the cheap Phase 3b "News Clock" test from the new-family plan: before building a new news strategy, check whether simply blocking known US macro-event windows improves existing exact-MT5 Gold portfolios.

This diagnostic is not a final news deployment spec. It uses the repository's deterministic proxy calendar, not actual historical release/surprise data.

## Boundary

- Offline diagnostic only.
- Inputs are already-realized exact MT5 Strategy Tester trade/signal CSVs.
- No MT5 launch, no runtime attach, no charts, no presets, no orders, and no broker state mutation.
- MT5 tester timestamps are treated as UTC-like broker-server timestamps, consistent with the existing session-hour definitions; this is sufficient for rejection/hygiene triage only.
- Any replay-worthy result would still need exact MT5 implementation with a real event calendar/time-provenance spec before review.

## Event Calendar

Use the existing deterministic standardized US macro-event slots:

- `NFP_FIRST_FRIDAY`: first Friday of each month at 08:30 New York time.
- `CPI_SECOND_WEDNESDAY`: second Wednesday of each month at 08:30 New York time.
- `FOMC_THIRD_WEDNESDAY`: third Wednesday in Jan/Mar/May/Jun/Jul/Sep/Nov/Dec at 14:00 New York time.

The New York wall-clock slots are converted to UTC with the same fixed US DST rule used in Phase 0.

## Fixed Portfolios

1. `step3_best_frequency_frontier`: the Step 3 best frequent frontier kept-signal CSV.
2. `step3_high_payout_v13_orrev`: `step1_f33_r30_be_never` + `v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning` + `orrev_london_firm_stop10`.
3. `step1_compromise_f33_r30_be_1r`: single Step 1 compromise stream.
4. `step1_high_wr_f67_r20_be_tp1`: single Step 1 high-WR stream.

## Fixed Hygiene Windows

- `event_m30_p60`: block trades from 30 minutes before through 60 minutes after each event slot.
- `event_m60_p180`: block trades from 60 minutes before through 180 minutes after each event slot.
- `event_day`: block trades on the UTC date of each event slot.

No event-type selection is allowed in this diagnostic.

## Decision Rules

- `NEWS_HYGIENE_OWNER_HIT`: WR >= 50%, realized avg win/loss >= 2.0, active weekday coverage >= 90%, positive net, retention >= 50%.
- `NEWS_HYGIENE_CORE_REPLAY_CANDIDATE`: WR >= 50%, realized avg win/loss >= 2.0, active weekday coverage >= 50%, positive net, retention >= 50%.
- `NEWS_HYGIENE_NEAR_REPLAY_CANDIDATE`: WR >= 48%, realized avg win/loss >= 1.9, active weekday coverage >= 50%, PF >= 1.30, positive net, retention >= 70%.
- Otherwise reject.

Reviewer spend is preserved unless a later exact-MT5 replay validates a candidate. This offline diagnostic alone is not review-worthy.
