# EURUSD Neutral Midnight Dual-Side Pairs preregistration

Frozen before the first historical outcome pass on 2026-07-28.

## Research question

Can a causal hedge-mode construction approximate the Regime 1 Neutral
hindsight-oracle behavior without predicting direction or deleting losing
trades?

The fixed hypothesis is that retaining both a long and a short specialist at
two adjacent midnight timestamps can convert a sufficiently large directional
move into one 1.5R target and one 1R stop. The construction is not an oracle:
both tickets remain in the ledger and pay independent spread and slippage.

## Frozen signal and frequency

- EURUSD only.
- Monday through Friday UTC dates only.
- A date belongs to this specialist only when the latest regime state no
  later than the prior day at 23:00 UTC is Neutral, is not shock, and is not
  joint DXY/EURUSD compression.
- Both required M5 bars must exist and the two timestamps must not be in the
  frozen EURUSD quarantine.
- At 00:00 UTC, enter one long and one short.
- At 00:05 UTC, enter one long and one short.
- Every eligible date therefore has exactly four independent tickets and two
  paired timestamps. No one-position restriction, OCO cancellation,
  direction ranking, or post-outcome subgroup selection is allowed.

The outcome-blind census is 655 eligible dates, 1,310 paired timestamps, and
2,620 tickets. Every eligible date has exactly four candidates. Frozen window
counts are:

| Window | Eligible dates | Pairs | Tickets |
|---|---:|---:|---:|
| 2019-2020 development | 222 | 444 | 888 |
| 2021-2022 development | 174 | 348 | 696 |
| 2023-2024 validation | 140 | 280 | 560 |
| 2025-H1 2026 pseudo-OOS | 119 | 238 | 476 |

## Frozen execution

- Hedge-mode account with independent tickets is required. A netting account
  is incompatible.
- Entry is the applicable bid/ask M5 open, with a minimum 0.7-pip spread and
  an additional 0.1 pip of slippage per execution side.
- Stop distance is 4 pips.
- Target distance is 1.5R, or 6 pips.
- Maximum hold is 12 hours.
- Stop is assumed first when a stop and target are both inside one M5 bar.
- Each ticket carries 0.25 portfolio R, so the four scheduled entries open at
  most 1 portfolio R per eligible date.
- Robustness adds another 0.5 pip of round-trip cost to every ticket.

## Frozen evaluation

Ticket, paired-timestamp, and daily portfolio ledgers will be evaluated
separately in every chronological window. Admission requires:

- 45%-55% ticket win rate, 1.35-1.75 realized payoff, positive expectancy,
  and ticket PF at least 1.10 in every window;
- at least 200 tickets, 100 pairs, and 50 eligible dates in every window;
- pair and daily portfolio PF at least 1.10 with positive expectancy in every
  window;
- overall ticket PF at least 1.30;
- daily portfolio maximum drawdown no more than 20R;
- positive ticket and daily results after removing the top 5% of winners;
- positive stressed ticket and daily results, each with PF at least 1.15;
- exactly four executed tickets on every eligible date.

Exact and 15-minute same-side resemblance to the Neutral hindsight oracle is
diagnostic only and cannot affect entries or admission.

## Information status

The source history and earlier failed campaigns were already inspected. This
is adaptive historical research, not pristine out-of-sample evidence. Even a
historical pass would require at least six months and 400 post-lock tickets
starting 2026-07-29 before any promotion review. No broker action is
authorized by this campaign.
