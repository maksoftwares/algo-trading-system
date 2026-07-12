# A1 XAU R6 H4 Distribution-Break Failed-Reclaim Short V1 — Census Preregistration

## Authority and boundary

- Independent authority: `A1_XAU_H4_RULE_CLEAN_RERUN_V2_INDEPENDENT_REVIEW_51D7191B_2026_07_12.md`.
- Reviewed H4 commit: `51d7191b050697eb9854c25b092ee5f3c11fad67`.
- Study: `R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1`.
- Phase: `R6-C1`, contract files and hashes only.
- Data through `2026-06-30` is development data.
- Runtime and broker action are not authorized.

This commit may contain only this preregistration, the exact JSON rule lock, the
outcome-blind JSON schema, the lock manifest, and the independent review that
authorized them. It contains no detector, census result, exit simulation, P/L,
MT5 source change, H4 join, portfolio join, or broker action.

## Economic thesis

After an objective completed-H4 upward impulse, a six-H4 distribution box, its
immediate first bearish breakdown, and the first failed H1 reclaim of the frozen
box floor can identify a supply-led uptrend-weakening transition. This hypothesis
is developed without H4 positions, P/L, drawdown dates, exposure episodes, or
known loss periods.

## Causal data convention

At the first tick after a completed H4 bar:

- H4 shift 1 is the completed candidate breakdown bar.
- H4 shifts 2 through 7 are the six distribution bars, oldest at shift 7.
- H4 shifts 8 through 13 are the six prior-impulse bars, oldest at shift 13.
- Shift 0 OHLC and indicators are forbidden.
- Missing, duplicate, non-monotonic, invalid, or incomplete bars produce
  `DATA_UNAVAILABLE`; no forward fill is allowed.

ATR14 is Wilder RMA of completed-bar true range. The seed is the arithmetic mean
of the first 14 valid true ranges, then `ATR_t=(13*ATR_(t-1)+TR_t)/14`.
`A_impulse` is H4 ATR14 at shift 8, `A_box` and `A_break` are H4 ATR14 at shift 2,
and `A_reclaim` is H1 ATR14 ending at the completed first reclaim-attempt bar.

## Frozen market structure

### Prior upward impulse — H4 shifts 13 through 8

Let the impulse low/high be the extrema of the six bars. Require all:

- close at shift 8 minus open at shift 13 is at least `1.50*A_impulse`;
- impulse range is at least `2.00*A_impulse`;
- at least four of six bars close above open;
- final close location within the impulse range is at least `0.75`.

### Distribution box — H4 shifts 7 through 2

Let box high/low be the extrema and box mid their midpoint. Require all:

- width between `1.00*A_box` and `3.00*A_box`, inclusive;
- at least four closes in the inner 60% of the box;
- at least four of five adjacent chronological pairs have overlap ratio at
  least `0.25`, with overlap divided by the smaller bar range;
- absolute close-at-shift-2 minus open-at-shift-7 drift no more than
  `0.75*A_box`.

### Router context

Use the existing market-only Router V1 from completed data. Only `UPTREND` and
`CHOP` are allowed. `SHOCK`, `COMPRESSION`, `DOWNTREND`, and `UNKNOWN` are blocked.
The router may not read any strategy state or ledger.

### Immediate first H4 breakdown — shift 1

Require all:

- shift-2 close is at or above box low;
- shift-1 close is at or below `box_low-0.10*A_break`;
- shift-1 close is below open;
- bearish body fraction is at least `0.50`;
- close location in the bar is no more than `0.25`.

The box is not held open for a later breakdown. A later bar is evaluated only
against its own immediately preceding six-bar box.

### First failed H1 reclaim

Freeze `L=box_low`. Inspect exactly the first six subsequently completed H1 bars.
The first bar whose high reaches `L-0.10*A_reclaim` consumes the episode as the
only reclaim attempt. It is a failed reclaim only when its close is no more than
`L-0.05*A_reclaim`, close is below open, body fraction is at least `0.35`, and
close location is no more than `0.35`. If that first attempt does not reject,
status is `FIRST_RECLAIM_NOT_REJECTED`; a later attempt is unavailable. If no
attempt occurs, status is `NO_RECLAIM_WITHIN_SIX_H1`.

### Entry availability and structural risk

The entry tick is the first recorded tick belonging to the next H1 bar, strictly
after the failed-reclaim bar in recorded sequence, while the broker trade session
is open. It must occur within 15 minutes of the scheduled H1 close or status is
`ENTRY_TICK_UNAVAILABLE`. Record bid as the short entry reference and ask only for
spread evidence. No later tick or bar may be read.

The structural stop for contract-risk census is the greater of reclaim-bar high
and box low, plus `0.25*A_reclaim`, normalized upward to the next symbol tick.
There is no target or exit simulation in the census.

## Episode identity and suppression

`box_id` is SHA-256 of rule version, symbol, the six distribution H4 open times,
and tick-normalized box low/high. One breakdown candidate is allowed per box.
After a valid breakdown, suppress later candidates for the same symbol/direction
until either a completed H4 close reaches the original box mid or 12 further H4
bars complete. One failed-reclaim signal is allowed per episode. Suppression may
not depend on a position or result.

## Outcome-blindness

Allowed inputs are native H4/H1 bars, ordered XAUUSD ticks only through the entry
tick, completed-data Router V1 state, an exact symbol/account contract snapshot,
this rule lock, schema lock, and market-data manifests.

Forbidden inputs and discoverable dependencies include all H4 strategy ledgers,
magics, position/exposure intervals, entries/exits, P/L, drawdown, balance/equity,
portfolio data, MFE/MAE, future prices, win/loss or SL/TP labels, known adverse
dates, December 2025 identifiers, and loss-cluster identifiers. Prefix invariance
must prove future appended market data cannot alter an emitted row.

## Locked incidence and contract gates

For `2016-07-01` through `2026-06-30`:

1. Raw causal incidence: at least 120; at least 40 in each five-year half; at
   least 8 of 10 July-June buckets with at least 5; no bucket above 25%; best
   contiguous 24 months no more than 40%.
2. USD 10,000 reference at fixed USD 25 risk: at least 100 risk-qualified; at
   least 35 in each half; coverage in at least 8 July-June buckets.
3. USD 1,000 deployment at fixed USD 2.50 risk: at least 100 feasible, at least
   80% of raw, at least 35 in each half, and coverage in at least 8 buckets.

Minimum-contract risk must use `OrderCalcProfit` for a sell at actual
`SYMBOL_VOLUME_MIN`, entry bid, and normalized structural stop plus one symbol
tick, or a separately validated equivalent from the exact contract snapshot.
Invalid/nonfinite contract fields fail closed. No tighter stop or higher risk is
permitted to rescue feasibility.

## Locked statuses and precedence

Exactly one census status, in this precedence:

1. `R6_CENSUS_EVIDENCE_INVALID`
2. `R6_CENSUS_INSUFFICIENT_INCIDENCE`
3. `R6_CENSUS_REFERENCE_RISK_UNDERPOWERED`
4. `R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE`
5. `R6_CENSUS_PASS`

Any failed locked gate stops the current R6 definition; no neighboring threshold
may be run. `R6_CENSUS_PASS` authorizes only a new standalone preregistration and
review, never P/L by itself.

## Frozen commit sequence

- `R6-C1`: these three contract files and their SHA-256 manifest only.
- `R6-C2`: detector, validator, and tests only; no census output or P/L.
- `R6-C3`: census evidence only from a clean exact R6-C2 commit; no code change.

R6-C2 must attest the exact commit and tree hashes, clean status, full command and
environment, full test output and its SHA-256 (or immutable CI), script/test/data
hashes, causality, prefix invariance, schema outcome blindness, contract-risk
parity, and absence of runtime-capable CLI surfaces.
