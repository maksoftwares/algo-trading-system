# COMEX Round-Barrier Rejection V71 Preregistration

## Purpose

V71 asks whether fixed round COMEX gold prices act as short-horizon liquidity
barriers. This causal variable has not been tested by the prior flow, auction,
VWAP, lead/lag, basis, sequence, or receipt-innovation campaigns. V71 does not
change V59/V60 and cannot reuse or rescue a failed V44-V70 threshold.

The historical periods are broadly exposed by earlier research. Even an
all-stage pass is only a near-survivor requiring unchanged prospective shadow
evidence. No network request, paid data, clock shift, future quote, model, EA,
demo/live action, or broker action is permitted.

## Fixed Mechanism

COMEX trades are aggregated into completed one-second buckets. For each fixed
level spacing and lookback window, the price at or before the window start
defines the next round level above and below. The starting price must lie no
farther than half one spacing from that level.

An upward rejection requires the completed-window high to probe through the
upper level, the last completed price to close back below it by the policy's
rejection distance, and completed five-second aggressor flow to be negative.
V71 signals short. A downward rejection is the exact causal symmetry and
signals long. All source events are strictly earlier than the decision second.
The earliest qualifying event per UTC date is retained, without quota filling
or replacement.

## Outcome-Blind Calibration

Calibration covers 2022-07-01 through 2022-08-01 and may reveal only source
quality, feature rows, candidate counts, frequency, active-day share, and
direction balance. Future spot prices, labels, entries, exits, MFE, MAE,
returns, P/L, win rate, and profit factor are prohibited.

Exactly 1,000 policies are registered:

- level spacing: USD 1, 2, 5, 10, or 20;
- lookback: 10, 20, 30, 60, or 120 seconds;
- minimum probe beyond the level: USD 0.00, 0.10, 0.20, 0.30, or 0.40;
- minimum rejection back across the level: USD 0.20, 0.40, 0.60, or 0.80; and
- minimum opposite five-second flow imbalance: 0.10 or 0.25.

A policy is selectable only at 0.65-1.00 candidates per eligible full weekday,
at least 65% active days, and at least 20% each direction. The selector
minimizes distance from 0.80/day, then prefers wider spacing, longer lookback,
larger probe, larger rejection, and stronger opposite flow. No economic outcome
participates. No selectable policy ends V71 before contract lock.

## Frozen Economic Test

- Session: 08:20 inclusive to 13:30 exclusive, America/New_York.
- Entry: first verified Dukascopy quote strictly after the decision and within
  two seconds.
- Long enters at ask and exits at bid; short enters at bid and exits at ask.
- Stop: max(0.50 completed-M5 ATR, four entry spreads, USD 1.00).
- Target: 1.50R; timeout: 30 minutes; one XAU ounce research size.
- Ticket cost: USD 0.30; prorated holding cost: USD 0.35 per 24 hours.
- Stress: an additional adverse 0.05R per resolved trade.

Development is 2022-08-01 to 2024-07-01, validation is 2024-07-01 to
2025-07-01, and exam is 2025-07-01 to 2026-07-01. Stages open separately.

Every stage requires 0.65-1.00/day; positive base/stress net and mean; base PF
>= 1.20; stress PF >= 1.10; at least 40% profitable full days; at least 60%
positive months; at least 20% each direction; both half-stage stress PF values
>= 1.00; positive stress net after removing five winners; stress closed DD <=
USD 150; and a centered-null five-weekday circular-block bootstrap one-sided
p-value <= 0.01. Development requires 300 resolved trades; validation and exam
require 150 each.

No same-version spacing, window, threshold, direction, session, stop, target,
hold, cost, quota, or gate rescue is authorized after outcomes open.
