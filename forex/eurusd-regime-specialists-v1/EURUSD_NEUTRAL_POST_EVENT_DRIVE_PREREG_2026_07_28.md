# EURUSD Neutral post-event drive preregistration

This contract will be hash-locked before loading an EURUSD trade outcome or
oracle field for this exact post-release rule.

## Hypothesis

A qualifying EUR or USD macro event can initiate a short, observable price
drive. After the first three complete M5 bars, either continuation or reversal
of that drive may carry enough causal information to trade Regime 1 Neutral
dates profitably.

The Dukascopy source audit found that historical numeric surprise fields are
not point-in-time safe. This campaign therefore inherits the already locked
event-time/title taxonomy and uses only event ID, time, currency, title, tag,
and prices complete at the decision.

## Frozen opportunity and event rule

- Consider only dates in the locked Regime 1 Neutral 00:00 UTC parent census.
- On each Neutral UTC date, use the latest qualifying event timestamp.
- Treat multiple qualifying rows at that timestamp as one event cluster.
- Start observation at the first full M5 bar at or after the event timestamp.
- Require three consecutive completed M5 observation bars.
- Enter at the executable open of the next M5 bar, 15 minutes after observation
  starts.
- The entry must remain on the same UTC date as the event.
- Missing bars, quarantine intervals, or a zero midpoint impulse produce cash.
- The midpoint impulse is the last observation close minus the first
  observation open. There is no magnitude threshold.
- Freeze two mechanism branches:
  - `MOMENTUM`: trade in the impulse direction;
  - `REVERSAL`: trade opposite the impulse direction.
- Select one branch once on 2019-2022 development trades by higher PF, then
  higher net R, then `MOMENTUM` on an exact tie.
- Never refit or reselect the branch in 2023-2026.

## Outcome-blind census

| Window | Neutral dates | Candidates | Cash dates | Momentum long |
|---|---:|---:|---:|---:|
| 2019-2022 development | 383 | 285 | 98 | 48.77% |
| 2023 validation | 74 | 54 | 20 | 57.41% |
| 2024 validation | 66 | 55 | 11 | 56.36% |
| 2025 pseudo-OOS | 80 | 64 | 16 | 65.63% |
| 2026 H1 pseudo-OOS | 39 | 37 | 2 | 48.65% |
| Total | 642 | 495 | 147 | 52.73% |

There are 549 Neutral dates with a qualifying event. Ninety-three dates have
no event, one has a zero impulse, and 53 exceed the risk ceiling. Every
accepted date has exactly one candidate. Candidate frequency is 0.771 per
Neutral date; frequency is descriptive and is not an admission gate.

The accepted long-side risks range from 4.0 to 24.8 pips with a 5.4-pip
median. Short-side risks range from 4.0 to 24.6 pips with a 5.1-pip median.
The event-cluster census contains 350 EUR clusters, 142 USD clusters, and
three simultaneous EUR/USD clusters. These are frozen diagnostics, not
post-outcome subgroups.

## Structure risk and execution

- Long entry uses the effective ask plus 0.1 pip adverse slippage.
- Short entry uses the bid minus 0.1 pip adverse slippage.
- A 0.7-pip minimum executable spread is imposed.
- Long stop is the lowest observation bid low minus 0.5 pip.
- Short stop is the highest observation effective ask high plus 0.5 pip.
- Expand either stop away from entry when necessary to enforce a 4-pip
  minimum risk.
- If either branch requires more than 25 pips of risk, the date is cash.
- Target is fixed at 1.5R.
- Maximum hold is 12 hours.
- Stop wins when stop and target occur in the same M5 bar.
- Only one position may be open; skipped overlaps are cash.
- Each admitted ticket would risk 0.25 portfolio R.

## Admission

The selected development branch must contain at least 50 trades, positive net
R, and PF strictly above 1.00.

Each of 2023, 2024, 2025, and 2026 H1 must contain at least eight trades, have
40-60% wins, preserve a 1.35-1.75 realized payoff ratio, positive net R, and
ticket and daily PF strictly above 1.00.

Across all forward windows, PF must be at least 1.15 and win rate must be
45-55%. The forward ledger must retain PF above 1.00 with an extra half-pip
stress and remain positive after removing its best 5% of winners. Daily
portfolio drawdown cannot exceed 20R.

The last six months require at least eight trades, positive net R, and ticket
and daily PF above 1.00. Exact oracle precision must reach 5% and same-side
15-minute precision 20%. Frequency is not an admission gate.

No event-time, currency, event-age, impulse, range, volatility, or weekday
subgroup may be created after outcomes.

## Evidence status

Existing EURUSD history is adaptive research even though the entry mechanism
is new. A complete historical pass remains research-only and requires at least
100 new observations and six post-lock calendar months beginning 2026-07-29.
No broker action is authorized.
