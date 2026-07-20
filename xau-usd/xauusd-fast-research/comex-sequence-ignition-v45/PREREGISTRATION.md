# COMEX Sequence-Ignition V45 Preregistration

## Status

V45 is a research-only historical diagnostic and grants no model, Python, EA,
demo/live, account, terminal, data-purchase, or broker authority. Earlier work,
including V44 development, has exposed broad historical XAUUSD behavior. An
all-stage pass would therefore be a near-survivor only and would require an
unchanged new forward shadow before any admission decision.

V44's exhausted-flow flip reached the frequency target but failed terminally.
V45 does not change or mirror that rule. It tests the separately registered
mechanism described before V44 opened: ignition after quieter flow, identified
from the ordering and arrival rate of individual aggressor trades.

## Fixed Mechanism

The venue-supplied `A` and `B` aggressor sequence is processed independently by
instrument ID. `N` trades do not enter signed sequence features. Each decision
occurs at the second strictly after all events in that source second.

For completed `(t-5s,t]` and preceding `(t-35s,t-5s]` windows, V45 calculates:

- current known-trade count and signed-volume imbalance;
- same-side transition share among the current known aggressor transitions;
- terminal same-side run length at `t`;
- current five-second price impulse in the terminal-run direction; and
- arrival acceleration: current trade count divided by
  `max(preceding_trade_count / 6, 1)`.

A signal requires the terminal run direction and current signed-flow direction
to agree, at least one tick of current directional price response, and the
locked policy thresholds. V45 follows the terminal-run direction. The first
qualifying event sequence is retained under a global 45-minute cooldown. The
cooldown controls dependence and never fills a daily quota.

The mechanism overlaps static continuation only in using current flow direction
and price response. Its registered claim is specifically event-sequence
persistence plus relative arrival acceleration; V45 must not be described as a
new result if those event-order fields do not add evidence.

## Outcome-Blind Calibration

Calibration covers 2022-07-01 through 2022-08-01 and may reveal only source
quality, candidate count, frequency, active-day share, and direction balance.
Future spot prices, labels, MFE/MAE, returns, win rate, P/L, and profit factor are
prohibited.

Exactly 1,000 deterministic policies are registered:

- minimum current five-second known trades: 10, 20, 30, 40, or 50;
- minimum terminal same-side run: 3, 5, 8, 13, or 21 trades;
- minimum current same-side transition share: 0.50, 0.60, 0.70, or 0.80;
- minimum absolute current signed-volume imbalance: 0.20, 0.35, 0.50, 0.65,
  or 0.80; and
- minimum arrival acceleration: 1.25 or 2.00.

Selection requires 2.3869731801-3.3869731801 candidates per eligible full
weekday, at least 80% active days, and at least 30% minority direction. It
minimizes distance from 2.8869731801/day, then prefers stricter trade count, run
length, transition share, imbalance, and acceleration. Economic outcomes cannot
participate. No qualifying policy ends V45 before economics.

## Frozen Economic Test

- Signal session: 08:20-13:30 America/New_York.
- Entry: first verified Dukascopy XAUUSD quote strictly after the decision and
  no more than two seconds later.
- Long uses ask/bid and short uses bid/ask for executable entry/exit.
- Stop: max(0.50 completed-M5 ATR, four entry spreads, USD 1.00).
- Target: 1.50R; timeout: 20 minutes; research size: one XAU ounce.
- Ticket cost: USD 0.30; prorated holding cost: USD 0.35/day.
- Stress slippage: an additional 0.05R per trade.

Development is 2022-08-01 to 2024-07-01, validation is 2024-07-01 to
2025-07-01, and exam is 2025-07-01 to 2026-07-01. A later stage is sealed until
all prior gates pass.

Every stage requires the frozen frequency interval; positive base/stress net
and mean; base PF >= 1.20; stress PF >= 1.10; at least 50% profitable full days
and positive months; at least 20% each direction; first- and second-half stress
PF >= 1.00; positive stress net after removing the five largest winners;
closed-trade stress drawdown <= USD 250; and centered-null five-weekday circular
block-bootstrap one-sided p <= 0.01. Development requires 500 resolved trades;
validation and exam require 200 each.

Same-version threshold, direction, session, stop, target, hold, cost, or gate
changes after an economic outcome are prohibited. V45 cannot modify the frozen
Core, bypass the V43 capital failure, enter V42 without a separate sealed
shared-account test, or interrupt V24.1/V26 forward collection.
