# EURUSD Neutral five-session reversal preregistration

This exact rule is frozen before any 2023-2026 trade outcome or oracle match
is evaluated.

## Why the lifecycle changes

Repeated causal campaigns could not make a four-pip stop profitable. The
failure persisted across fitted direction models, cross-asset signals,
executed-flow sources, event timing, selective filters, and an XAUUSD/XAGUSD
consensus. A development-only structural audit then rejected:

- a two-stage opportunity-plus-direction model;
- 240 fixed-stop momentum and reversal rules;
- 480 wider intraday session market-entry rules; and
- 72 Asian-range OCO breakout rules.

The remaining hypothesis is slower mean reversion with risk wide enough to
sit outside ordinary intraday noise.

## Adaptive development disclosure

The rule came from a 2019-2022 development screen of 216 simple daily-horizon
combinations: one-, three-, and five-session direction; 20-, 30-, and
40-pip risk; 24-, 48-, and 72-hour hold; momentum or reversal; and four
fixed signal-strength hurdles.

The exact fixed-cooldown variants were then checked on the same development
period. The final rule deliberately uses no strength threshold even though a
thresholded sibling had a slightly higher development PF. This reduces the
final rule to one sign comparison and avoids fitting a magnitude boundary.

This is adaptive research, not pristine discovery. The protection against
further overfit is a complete forward lock: 2023, 2024, 2025, and 2026 H1
outcomes remain unopened for the exact rule until this contract is hashed.

## Frozen causal rule

- Trade only at 00:00 UTC when the already pinned causal regime source has
  exactly one LONG and one SHORT Neutral row at that timestamp.
- Use the midpoint close of the M5 bar completed at 00:00.
- Compare it with the midpoint close exactly 1,440 completed M5 bars earlier.
  This is a five-session bar count, not five calendar days; weekend closure
  therefore cannot create a missing-endpoint shortcut.
- If the move is positive, enter SHORT.
- If the move is negative, enter LONG.
- If the move is exactly zero or either endpoint is unavailable, stay in
  cash.
- After an entry, accept no new entry for 72 elapsed hours, irrespective of
  whether the prior position exited early.
- There is no magnitude threshold, fitted parameter, probability, weekday,
  volatility, clock, year, event, side, or daily-frequency filter.

Only completed closes and the decision-time Neutral ownership field enter the
signal. Forward outcomes and oracle fields are evaluation-only.

## Frozen execution

- executable bid/ask market entry at 00:00 UTC;
- 40-pip stop and 60-pip target;
- 72-hour maximum hold;
- 0.7-pip minimum retail spread;
- 0.1-pip adverse slippage per execution side;
- stop first when stop and target share an M5 bar;
- one position at a time through the deterministic 72-hour cooldown;
- 0.25 portfolio R per ticket.

## Development evidence

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019 | 62 | 43.55% | 1.461 | 1.127 | +3.40R |
| 2020 | 64 | 46.88% | 1.457 | 1.286 | +9.03R |
| 2021 | 58 | 46.55% | 1.344 | 1.170 | +4.56R |
| 2022 | 50 | 50.00% | 1.327 | 1.327 | +8.19R |
| 2019-2022 | 234 | 46.58% | 1.409 | 1.228 | +25.18R |

Development maximum drawdown was 8.06R. Another half pip per round trip left
PF 1.199 and +22.26R. Removing the best 5% of all trades left PF 1.065 and
+7.21R. The final development trade exited on 2022-12-29, so no 2023 bar was
used in development P&L.

## Outcome-blind forward census

The candidate census reads only the parent timestamp and side columns plus
completed EURUSD closes. It does not read a trade outcome, exit, oracle
membership, or oracle match.

| Window | Candidates | LONG | SHORT |
|---|---:|---:|---:|
| 2019-2022 development | 234 | 120 | 114 |
| 2023 validation | 51 | 25 | 26 |
| 2024 validation | 41 | 20 | 21 |
| 2025 pseudo-OOS | 53 | 23 | 30 |
| 2026 H1 pseudo-OOS | 26 | 17 | 9 |
| Total | 405 | 205 | 200 |

The pinned Neutral source contains 642 midnight decision points. All have
complete signal history; none has a zero move. The fixed cooldown maps 237
points to cash. Forward candidate counts and directions are therefore fixed
before P&L.

## Admission

Development must retain at least 200 trades, 40-55% wins, 1.35-1.75 realized
payoff, PF at least 1.15, positive stress and winner-removal results, and
positive PF in every development year.

Each forward window must meet its frozen count floor, win 40-60%, realize a
1.35-1.75 payoff, and have positive ticket and daily PF. Count floors are 20
in each full year and ten in 2026 H1.

Forward overall requires PF at least 1.15, 40-55% wins, positive extra-cost
stress, positive net after removing the best 5% of all trades, and no more
than 20R ticket drawdown. The latest six months require at least ten trades
and positive ticket and daily PF.

Oracle resemblance is diagnostic only because the 40/60-pip, 72-hour
lifecycle intentionally differs from the hindsight oracle's 4/6-pip,
12-hour lifecycle.

## Prohibitions and evidence status

No side reversal, magnitude threshold, lifecycle repair, clock, weekday,
year, volatility, event, source, or subgroup filter may be added after
outcomes. A favorable isolated window cannot activate the rule.

Even a complete historical pass remains adaptive research and cannot
authorize broker action. Promotion requires at least 100 post-lock
observations and 12 calendar months beginning 2026-07-29.
