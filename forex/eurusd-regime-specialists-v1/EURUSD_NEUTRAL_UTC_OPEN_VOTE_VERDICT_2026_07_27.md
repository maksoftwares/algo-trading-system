# EURUSD Regime 1 Neutral UTC-open vote verdict

Date: 2026-07-27

Decision: `REJECTED_NEUTRAL_UTC_OPEN_VOTE_V1`

## Question tested

Can a transparent, deterministic pre-open cross-market vote identify the
future-winning EURUSD direction at the Neutral hindsight oracle's dominant
00:00 UTC entry cluster?

This campaign deliberately avoided machine learning and post-outcome
selection. It tested one entry per eligible UTC date using only information
completed before the entry.

## Source-feasibility audit

Two possible information routes were audited before freezing the rule:

- The available official BLS and Federal Reserve calendars contained 126
  scheduled CPI, payroll, and FOMC events from July 2022 through June 2026,
  but not point-in-time consensus forecasts or release surprises.
- In the same interval, 1,053 of 1,123 Neutral oracle trades occurred in
  hour 00 UTC, and none occurred within 15, 30, 60, or 120 minutes after
  one of those scheduled events. Scheduled-event timing was therefore
  rejected outcome-blind as incompatible with the target behavior.
- No local EUR FX futures, executed-flow, or order-book archive was found.
  The available futures archive was COMEX gold, not EUR currency futures.

The remaining distinct causal hypothesis was a UTC-open cross-market vote.
The four hash-pinned inputs were EURUSD, EURGBP, EURJPY, and DXY M5 data.

## Frozen rule

At 00:00 UTC on an eligible Neutral date:

1. EURUSD, EURGBP, and EURJPY each vote from the sign of their exact,
   completed 60-minute mid-price return ending at 23:55.
2. Because DXY is normally closed at that time, its inverse vote uses the
   latest completed contiguous 60-minute DXY return ending no later than
   23:55 and no more than 240 minutes old.
3. All four returns must be valid and nonzero.
4. Three or four agreeing votes enter one EURUSD trade in that direction.
   A two-two tie remains cash.
5. Only one entry and one open position are allowed per UTC date.

Execution used fixed 4-pip risk, a 1.50R target, a 12-hour maximum hold,
exact bid/ask prices, a 0.70-pip minimum spread, 0.10-pip adverse slippage
per side, and stop-first resolution for ambiguous M5 bars.

The configuration, preregistration, parent contract, and four source files
were SHA-256 locked before the outcome pass. The rule contains no fitted
coefficient or selected probability threshold.

## Outcome-blind census

Before inspecting target, stop, P&L, or oracle-side outcomes:

- 655 Neutral 00:00 candidates existed;
- 464 had four valid nonzero votes;
- 314 passed three-of-four agreement;
- 157 were long and 157 were short;
- annual trade counts were 53, 49, 36, 41, 39, 33, 40, and 23 from 2019
  through 2026 H1.

The frozen capacity gate passed.

## Development result

| Window | Trades | Win rate | Payoff | PF | Net | Max DD | Extra 0.5-pip net |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019-2022 | 179 | 24.58% | 1.439 | 0.469 | -73.48R | 75.85R | -95.85R |

Development failed the win-rate, PF, expectancy, drawdown, and cost-stress
requirements. Per the frozen contract, no return horizon, vote combination,
freshness limit, or entry time was repaired.

## Chronological forward result

| Window | Trades | Win rate | Payoff | PF | Net | Exact precision | Exact recall | 15m precision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 39 | 43.59% | 1.439 | 1.112 | +2.53R | 43.59% | 5.67% | 64.10% |
| 2024 | 33 | 21.21% | 1.439 | 0.387 | -16.33R | 21.21% | 2.66% | 30.30% |
| 2025 | 40 | 27.50% | 1.439 | 0.546 | -13.50R | 27.50% | 3.44% | 57.50% |
| 2026 H1 | 23 | 30.43% | 1.437 | 0.629 | -6.10R | 30.43% | 4.38% | 47.83% |
| Overall | 135 | 31.11% | 1.439 | 0.650 | -33.40R | 31.11% | 4.03% | 51.11% |

Every forward window failed at least one economic gate. The superficially
positive 2023 slice still missed the 45% win-rate floor and became
-2.35R under the frozen extra-half-pip stress. It then collapsed in 2024,
2025, and 2026 H1.

The latest six-month result is therefore 23 trades, 30.43% wins, 1.437
payoff, PF 0.629, -6.10R net, and 10.98R maximum drawdown. At the frozen
0.25 portfolio-R allocation, net performance was -1.53 portfolio-R.

## Structural failure anatomy

| Forward group | Trades | Wins | Win rate | Net |
|---|---:|---:|---:|---:|
| Exact oracle members | 42 | 42 | 100.00% | +61.95R |
| Nonmembers | 93 | 0 | 0.00% | -95.35R |

This split is not a surprising model discovery. It follows from the
oracle's construction. The hindsight oracle starts scanning each UTC date
at midnight and retains the first four future target-first paths. At 00:00,
any selected side that subsequently wins must therefore become an exact
oracle member; a selected side absent from the oracle must lose.

Consequently, the causal strategy's economic win rate is exactly its
same-entry, same-side oracle precision. The vote selected the future-winning
side on 31.11% of forward dates. With realized payoff near 1.439 and the
observed execution loss, break-even requires about 41.3% wins. Behavioral
similarity within 15 minutes did not supply the missing direction.

## Robustness

Across all history, the rule produced 314 trades, 27.39% wins, PF 0.543,
and -106.88R, with 114.13R maximum drawdown. Adding another half pip round
trip reduced net to -146.13R and PF to 0.443. Removing the largest 5% of
winners reduced net to -130.48R and PF to 0.442.

## Verdict

The deterministic UTC-open vote does not solve Regime 1. It passes the
frozen behavioral-imitation gate but fails development, every chronological
economic window, and robustness.

Post-outcome changes to the vote threshold, return horizon, DXY freshness,
entry minute, or observed losing dates would be retrospective overfitting.
This exact pre-open EUR-cross/DXY vote route is closed without retuning.

The next legitimate Regime 1 campaign needs genuinely new direction
information: point-in-time macroeconomic consensus surprises, EUR futures
or multi-venue executed-flow/order-book imbalance, or a prospectively
collected untouched sample. Until such evidence passes, Regime 1 remains
`CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow python run_neutral_utc_open_vote.py
```
