# COMEX Size-Segment Flow V32 Preregistration

## Status

This is a research-only historical development campaign. It grants no model,
Python prediction, EA, demo, live, account, terminal, paid-data, or broker
authority.

## Hypothesis

Prior COMEX campaigns aggregated all buyer- and seller-initiated volume. V32
tests one different mechanism: directional disagreement between large-lot and
small-lot aggressive flow. A completed five-minute window in which large-lot
flow is strongly directional while small-lot flow is materially opposed may
represent a latent institutional metaorder whose impact has not fully reached
XAUUSD spot. V32 follows the large-lot direction for at most 60 minutes.

The hypothesis is intentionally narrow. Public trade prints cannot identify a
true parent metaorder, so V32 claims only a reproducible size-segment flow
relationship. Work on persistent order flow and metaorder impact motivates the
test but does not establish profitability:

- Farmer, Gerig, Lillo, and Waelbroeck, "How efficiency shapes market impact",
  arXiv:1102.5457.
- Naviglio et al., "Why is the estimation of metaorder impact with public market
  data so challenging?", arXiv:2501.17096.

## Data

- Signal source: already-acquired Databento `GLBX.MDP3` `GC.v.0` trades schema,
  2022-07-01 through 2026-07-01.
- Execution source: verified Dukascopy XAUUSD bid/ask tick foundation.
- No network request, payment, new Databento job, or API key is authorized.
- Trade side is the venue-provided aggressor side. `N` rows contribute no signed
  flow.
- Multiple instrument IDs are processed independently; no whole-day dominant
  contract is selected with future information.

## Clock And Causality

- Session: 08:20 inclusive to 13:30 exclusive, `America/New_York`.
- Feature bars: fixed five-minute half-open intervals.
- Decision time: exact end of the completed five-minute interval.
- Small trades: size no greater than two contracts, fixed before calibration.
- Large trades: size threshold selected only from the locked grid.
- All feature rows satisfy event timestamp strictly before decision time.
- Candidate direction is the sign of large-lot signed volume.
- Small-lot imbalance must have the opposite sign.
- A 60-minute global cooldown starts at each retained decision. It is never used
  to fill a daily quota.

## Outcome-Blind Calibration

The 2022-07-01 through 2022-08-01 packet may expose only:

- source/session quality;
- raw and selected candidate counts;
- candidates per eligible full weekday;
- active-day share; and
- long/short balance.

It may not expose any future spot price, entry, exit, MFE, MAE, label, return,
P/L, win rate, or profit factor. The deterministic selector chooses among the
locked grid only when frequency is 2.3869731801-3.3869731801 per eligible full
weekday, active-day share is at least 80%, and minority direction share is at
least 30%. It minimizes distance from the midpoint of the frequency interval,
then prefers stricter size, volume, and imbalance thresholds.

If no grid row qualifies, V32 fails before economic outcomes are opened.

## Economic Rule

- Entry: first verified Dukascopy quote strictly after the decision, no later
  than two seconds.
- Long at ask and short at bid; exits use the opposite executable side.
- Stop distance: maximum of 0.50 completed-M5 ATR, four entry spreads, and USD
  1.00.
- Target: 1.50R.
- Timeout: 60 minutes.
- Size: one XAU ounce for research accounting.
- Baseline ticket cost: USD 0.30.
- Holding cost: USD 0.35 per 24 hours, prorated.
- Stress slippage: an additional 0.05R per trade.
- Maximum initial research risk: USD 50.

## Chronological Firewall

1. Calibration: 2022-07-01 to 2022-08-01, candidate facts only.
2. Development: 2022-08-01 to 2024-07-01.
3. Validation: 2024-07-01 to 2025-07-01, sealed unless development passes.
4. Exam: 2025-07-01 to 2026-07-01, sealed unless validation passes.

The runner stops at the first failed stage. Same-version threshold, direction,
holding-period, stop, target, or gate changes after any economic result are
forbidden. Because earlier research has broadly consulted these years, even a
historical exam pass is development evidence and requires an unchanged forward
shadow after 2026-07-20.

## Stage Gates

Every opened economic stage must satisfy all of the following:

- 2.3869731801-3.3869731801 resolved trades per eligible full weekday;
- base PF at least 1.20 and stress PF at least 1.10;
- positive base and stress net P/L and positive mean stress P/L;
- at least 50% profitable full weekdays and 50% positive calendar months;
- at least 20% of resolved trades in each direction;
- first-half and second-half stress PF at least 1.00;
- positive stress net after removing the five largest winners;
- maximum closed-trade stress drawdown no greater than USD 250; and
- one-sided centered-null circular five-weekday block-bootstrap p-value no
  greater than 0.01, using the frozen seed and 10,000 resamples.

Development additionally requires at least 500 resolved trades. Validation and
exam each require at least 200.

## Multiplicity And Authority

V32 is one registered family claim with one selected configuration. The 0.01
one-sided gate is intentionally conservative after the preceding Capital and
COMEX research attempts. No mirror is registered. A failure is terminal for
this exact size-segment continuation family on the exposed history.
