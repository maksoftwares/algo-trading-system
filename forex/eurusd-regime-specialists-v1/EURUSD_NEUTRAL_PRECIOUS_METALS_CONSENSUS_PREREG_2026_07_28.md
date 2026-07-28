# EURUSD Neutral precious-metals consensus preregistration

This contract will be hash-locked before loading an EURUSD trade outcome or
oracle field for the exact rule.

## Hypothesis

Synchronous gold and silver appreciation can indicate broad USD weakness,
while synchronous depreciation can indicate USD strength. Agreement may
therefore provide a simple causal EURUSD direction at the hindsight oracle's
actual first-hour entry clocks.

## Frozen decision rule

- Use only locked Regime 1 Neutral decision points at 00:00, 00:15, 00:30,
  and 00:45 UTC.
- For each entry, use the metals M5 bar starting five minutes before entry.
  That bar is complete exactly at entry.
- Calculate each metal's midpoint-close return over 60 minutes.
- Require the return-end and return-start M5 timestamps to exist exactly.
- Convert each return to its sign.
- If both signs are nonzero and positive, trade EURUSD LONG.
- If both signs are nonzero and negative, trade EURUSD SHORT.
- If signs disagree, either sign is zero, or an endpoint is missing, stay
  in cash.
- There is no return-magnitude threshold, fitting, branch selection, clock
  selection, or daily quota.

## Outcome-blind census

| Window | Source points | Candidates | Active days | LONG |
|---|---:|---:|---:|---:|
| 2019-2022 development | 1,532 | 1,074 | 370 | 48.51% |
| 2023 validation | 296 | 207 | 72 | 61.35% |
| 2024 validation | 264 | 178 | 64 | 39.89% |
| 2025 pseudo-OOS | 320 | 194 | 76 | 54.64% |
| 2026 H1 pseudo-OOS | 156 | 111 | 39 | 54.05% |
| Total | 2,568 | 1,764 | 621 | 50.17% |

The rule averages 2.748 candidates per Neutral date. Candidate-count
distribution across the 642 dates is 21/65/132/261/163 for zero through four
candidates. Frequency is descriptive and is not an admission gate.

## Execution

- executable EURUSD bid/ask entry at the selected clock;
- 4-pip stop and 6-pip target;
- 12-hour maximum hold;
- 0.7-pip minimum spread;
- 0.1-pip adverse slippage per execution side;
- stop first when stop and target share an M5 bar;
- 0.25 portfolio R per ticket and at most 1.0 new portfolio R per day;
- up to four concurrent first-hour positions.

## Admission

Development requires at least 100 trades, positive net R, and PF above 1.00.

Each forward window requires its frozen minimum count, 40-60% wins, a
1.35-1.75 payoff ratio, positive net R, and ticket and daily PF above 1.00.
Minimum counts are 20 in each full year and ten in 2026 H1.

Forward overall PF must reach 1.15 with a 45-55% win rate. The ledger must
remain positive under an extra half-pip stress and after removing the best 5%
of winners. Daily portfolio drawdown cannot exceed 20R.

The latest six months require at least ten trades, positive net R, and ticket
and daily PF above 1.00. Exact oracle precision must reach 25%, and same-side
15-minute precision 35%.

## Prohibitions

The economic side mapping cannot be reversed after outcomes. No return
threshold, XAU/XAG ratio, volatility, spread, clock, year, weekday, event, or
regime subgroup may be added. A favorable isolated window cannot activate the
rule.

## Evidence status

Existing history is adaptive research. Even a full historical pass remains
research-only and requires at least 100 new observations and six post-lock
calendar months from 2026-07-29. No broker action is authorized.
