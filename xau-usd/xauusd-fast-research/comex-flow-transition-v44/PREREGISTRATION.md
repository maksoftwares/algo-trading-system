# COMEX Flow-Transition V44 Preregistration

## Status And Purpose

V44 is a research-only historical diagnostic. It cannot change the frozen Core,
train a production model, emit an EA prediction, or authorize demo/live/broker
action. The broad 2022-2026 history has informed earlier research, so even an
all-stage pass is only a near-survivor and must be followed unchanged in a new
forward period.

The acquired Databento packet contains individual `GLBX.MDP3` `GC.v.0` trade
prints but no TBBO, MBP, or MBO data. Earlier COMEX campaigns tested static
signed-flow imbalance, five-minute lead/lag, large-versus-small flow, and
auction summaries. V44 registers a narrower unused mechanism: a transition
from one-sided aggressive flow with weak price response into confirmed
opposite aggressive flow.

## Fixed Hypothesis

A one-sided COMEX flow episode that no longer moves price efficiently may be
temporarily exhausted or absorbed. If a completed five-second window then has
opposite signed flow, elevated activity, and at least one tick of price response
in the new direction, XAUUSD spot may continue in the new direction for a short
horizon. V44 follows the new flow direction. It never mirrors a failed signal.

For each instrument ID and decision second `t`:

- prior window: `(t-35s, t-5s]`;
- current window: `(t-5s, t]`;
- prior imbalance: prior signed volume divided by prior total volume;
- current imbalance: current signed volume divided by current total volume;
- prior directional impact efficiency: prior-flow-sign times prior price move,
  in ticks, divided by absolute prior signed volume;
- current acceleration: current five-second volume divided by one sixth of
  prior thirty-second volume; and
- current directional impulse: current-flow-sign times current five-second
  price move, in ticks.

All decisions use completed source events only. Every source event in a feature
row must be strictly earlier than its decision time. The prior and current flow
signs must oppose. Current acceleration is at least 0.75 and current directional
impulse is at least one tick. A global 45-minute cooldown retains the first
qualifying transition; it is a dependence control, not a quota.

## Outcome-Blind Calibration

The calibration packet is 2022-07-01 through 2022-08-01. It may expose only
source quality, candidate count, candidates per eligible full weekday,
active-day share, and direction balance. It may not open any future XAUUSD
price, fill, MFE, MAE, label, return, win rate, profit factor, or P/L.

Exactly 1,000 deterministic policies are registered before calibration:

- minimum prior volume: 60, 100, 140, 180, or 220 contracts;
- minimum absolute prior imbalance: 0.15, 0.25, 0.35, 0.45, or 0.55;
- maximum prior directional impact efficiency: 0.00, 0.02, 0.05, or 0.10
  ticks per net contract;
- minimum current five-second volume: 10, 20, 30, 40, or 50 contracts; and
- minimum absolute current imbalance: 0.20 or 0.40.

A policy is selectable only at 2.3869731801-3.3869731801 candidates per eligible
full weekday, at least 80% active days, and at least 30% minority direction. The
selector minimizes distance from 2.8869731801/day, then prefers stricter prior
volume, imbalance, weaker impact, current volume, and current imbalance. No
economic outcome participates in selection. If no policy qualifies, V44 ends
before economic testing.

## Frozen Economic Test

- Signal session: 08:20 inclusive to 13:30 exclusive, America/New_York.
- Entry: first verified Dukascopy XAUUSD quote strictly after the decision and
  within two seconds.
- Long enters at ask and exits at bid; short enters at bid and exits at ask.
- Stop: max(0.50 completed-M5 ATR, four entry spreads, USD 1.00).
- Target: 1.50R.
- Timeout: 30 minutes.
- Research size: one XAU ounce.
- Ticket cost: USD 0.30; holding cost: USD 0.35 per 24 hours prorated.
- Stress: an additional 0.05R adverse slippage per trade.

Chronological partitions open sequentially:

1. development: 2022-08-01 through 2024-07-01;
2. validation: 2024-07-01 through 2025-07-01; and
3. exam: 2025-07-01 through 2026-07-01.

Every opened stage must satisfy the frozen frequency interval, positive base
and stress net and mean, base PF >= 1.20, stress PF >= 1.10, at least 50%
profitable full weekdays and positive months, at least 20% each direction, both
half-stage stress PFs >= 1.00, positive stress net after removing the five
largest winners, closed-trade stress drawdown <= USD 250, and a centered-null
five-weekday circular-block bootstrap one-sided p-value <= 0.01. Development
requires 500 resolved trades; validation and exam require 200 each.

The runner stops at the first failure. Same-version threshold, direction,
session, hold, stop, target, cost, or gate changes after outcomes are forbidden.

## Risk And Authority Firewall

V44 does not modify the frozen R1 cap of one new box entry per UTC day and two
concurrent box positions. It cannot bypass the V43 account-capital finding,
combine with Core before a sealed shared-account test, or consume paid data.
Network access, Databento payment, model training, Python execution signals, EA
consumption, demo/live deployment, account changes, terminal changes, and
broker actions are all unauthorized.
