# EURUSD Neutral midnight dual-side pairs verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_MIDNIGHT_PAIRS_V1`

## What was tested

This campaign tested the remaining simple way to guarantee four causal
Regime 1 trades without predicting direction: retain independent long and
short tickets at both 00:00 and 00:05 UTC on every Neutral-owned weekday.

The rule was preregistered and SHA-256 locked before the first historical
outcome pass. It used:

- the regime state available by the prior day at 23:00 UTC;
- exactly four tickets on every eligible day;
- a 4-pip stop and 6-pip target;
- a 12-hour maximum hold;
- executable bid/ask prices, a 0.7-pip spread floor, and 0.1 pip of adverse
  slippage per execution side;
- stop-first same-bar treatment;
- independent hedge-mode tickets with no loser deletion, OCO cancellation,
  or future-based direction choice;
- 0.25 portfolio R per ticket.

The outcome-blind census contained 655 eligible Neutral dates, 1,310 paired
timestamps, and 2,620 tickets. All 655 dates had exactly four candidates and
all four were executed.

## Result

| Window | Tickets | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019-2020 development | 888 | 31.08% | 1.439 | 0.649 | -220.20R |
| 2021-2022 development | 696 | 32.18% | 1.439 | 0.683 | -153.40R |
| 2023-2024 validation | 560 | 32.50% | 1.412 | 0.680 | -126.33R |
| 2025-H1 2026 pseudo-OOS | 476 | 30.46% | 1.439 | 0.630 | -125.45R |
| Overall | 2,620 | 31.56% | 1.433 | 0.661 | -625.38R |

No chronological window was profitable. The overall individual-ticket win
rate missed the requested 45%-55% band by 13.44 percentage points. Realized
payoff stayed close to the requested 1.5, confirming again that direction
and path selection—not the exit multiple—are the binding problem.

## Why pairing failed

There can be at most one winning ticket in a same-timestamp long/short pair:
the losing side's 4-pip stop lies inside the winning side's 6-pip target
path.

| Pair outcome | Pairs | Raw pair result |
|---|---:|---:|
| One target and one stop | 827 | approximately +0.45R |
| No target winner | 483 | approximately -2.05R |
| Two winners | 0 | not geometrically possible |

The pair success rate was 63.13%, but its winners were too small relative to
double-stop failures. Pair PF was only 0.373 and pair expectancy was
-0.477R. At this realized geometry, roughly 82% of pairs would need one
winner merely to break even; the observed rate was about 19 percentage
points lower.

At the daily portfolio level, 301 of 655 dates were positive:

- 45.95% positive days;
- daily PF 0.302;
- -156.34 portfolio R;
- 157.24R maximum drawdown.

Removing the best 5% of ticket winners worsened net result to -818.63R.
Adding another 0.5 pip of round-trip cost reduced ticket PF to 0.540 and net
result to -952.88R. Every frozen admission gate failed except the exact
four-ticket frequency gate.

## Last six months

From 2026-01-01 through 2026-06-30:

| View | Observations | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Individual tickets | 156 | 27.56% | 1.439 | 0.547 | -52.43R |
| Paired timestamps | 78 | 55.13% | 0.219 | 0.269 | -52.43R |
| Daily 0.25R portfolio | 39 | 38.46% | 0.327 | 0.204 | -13.11R |

The strategy delivered exactly four tickets on each of its 39 eligible
Neutral dates, but only 1.21 tickets per all 129 active weekdays because
Regime 1 did not own every date.

## Oracle resemblance

The rule matched 827 of 2,620 tickets exactly and matched 1,231 within 15
minutes on the same side:

- exact precision 31.56%, exact recall 31.63%;
- 15-minute precision 46.98%, 15-minute recall 47.07%.

The 827 exact members are exactly the 827 winning tickets. This is expected:
the retrospective oracle retains target-first paths and deletes failures.
Time proximity to the oracle therefore rose to nearly 47% without creating
economic edge.

## Verdict

The no-direction, dual-side route is closed. It solved the requested
four-trade frequency mechanically but made the underlying selection problem
worse by paying for every losing direction. It is research-only, requires a
hedge-mode account, and is not eligible for demo or live use.

The next legitimate campaign must select the winning side causally before
entry or use genuinely new decision-time information. Retuning the two
timestamps, stop, target, or hold after this result would be overfitting and
is prohibited.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow python run_neutral_midnight_pairs.py census
uv run --with pandas --with numpy --with pyarrow python run_neutral_midnight_pairs.py backtest
```
