# V100 Program-Stop Brainstorming

## Decision

V100 ended with `V100_DISCOVERY_FAIL_PROGRAM_STOP`. There is no V101. The
frozen V59/V60 baseline remains unchanged, but the program has not proven two
combined trades per weekday.

Discovery ran all 1,000 locked attempts `131001-132000`. No policy advanced,
so Confirmation, Final, and the shared-account audit remain sealed.

## What failed

The failure was specifically frequency, not basic Discovery profitability:

- `0/1000` policies passed minimum trades (`448`).
- `0/1000` policies passed minimum add-on frequency (`0.86/day`).
- `1000/1000` passed minimum PF and average stress R.
- `996/1000` passed FDR and top-winner removal.
- `983/1000` passed all four half-year segments and worst-segment PF.
- Only `58/1000` passed positive-month share.
- `948/1000` passed the `35R` closed-drawdown cap.

The fastest locked policy was attempt `131881`:

| Metric | Discovery result |
|---|---:|
| Pool | MIXED_60 |
| UTC window | 08:00-16:00 |
| Health rule | 20 completed events, PF >= 0.9, 5-day cooldown |
| Trades | 331 |
| Trades/weekday | 0.635 |
| Stress PF | 20.678 |
| Average stress R | 3.112 |
| Closed drawdown | 8.499R |
| Positive months | 66.7% |
| Profitable half-year segments | 4/4 |
| Worst segment PF | 11.819 |

It passed every locked economic/stability gate but missed both trade-count
gates. V59 produced `1.142/day` in Development-2, so the best theoretical
combined rate was only `1.777/day`. The gap was about `0.223/day`, or 117
additional trades over the 521-weekday Discovery window.

The very large PF and average R are not deployment evidence. The health state
is outcome-conditioned, its sentinel markouts overlap and cluster, and the
underlying history was already exposed in earlier research. It needs an
independent causal audit and prospective replication.

## Post-Outcome Diagnostic

The following diagnostic was deliberately run only after the terminal result.
It is useful for mechanism analysis but is not admissible strategy evidence.

Removing the health circuit while retaining the fixed scheduler showed that
raw event capacity exists:

| Pool/window | Trades/day | Stress PF | Avg R | Positive months | Drawdown | Worst segment PF |
|---|---:|---:|---:|---:|---:|---:|
| MIXED_60, 08:00-16:00 | 1.415 | 2.532 | 1.231 | 50.0% | 94.927R | 2.139 |
| MIXED_60, 12:00-20:00 | 1.390 | 2.456 | 1.179 | 54.2% | 90.462R | 2.169 |
| BREAK_60, 12:00-20:00 | 0.887 | 2.830 | 1.464 | 58.3% | 51.622R | 2.126 |
| BREAK_60, 08:00-16:00 | 0.889 | 2.944 | 1.485 | 54.2% | 54.270R | 2.311 |

The closest raw near-miss is `BREAK_60, 12:00-20:00`. Its `0.887/day` would
raise the Development-2 combined rate to about `2.029/day`, but its `51.622R`
drawdown exceeds the `35R` cap by 47.5%. The health circuit solved drawdown by
discarding too much opportunity. This is the core engineering/research problem.

## Weak Points To Audit

1. **Binary health control.** A sleeve is fully on or fully off. The fastest
   locked policy kept only 331 of 737 scheduled MIXED_60 trades in its UTC
   window, a 55% reduction.
2. **Overlapping sentinel evidence.** A five-minute episode rule does not make
   60-minute markouts independent. Rolling PF can be dominated by one extended
   move and overstate effective sample size.
3. **Repeated historical exposure.** V19/V21 and later work already exposed the
   same periods. Strong Discovery figures cannot be treated as pristine.
4. **Frequency measured without a material-risk floor.** A future design must
   not manufacture frequency by submitting economically negligible trades.
5. **Standalone before portfolio.** The near-miss is attractive alone, but its
   correlation, floating drawdown, and overlap with V59/V60 are not proven.
6. **Execution parity.** Fixed-horizon Dukascopy markouts still require exact
   tick/MT5 parity, spread spikes, slippage, commission, swap, and rejection
   stress before any forward authority.

## Brainstorming Directions

These are hypotheses, not authorization to implement another version.

1. **Two-tier admission instead of binary abstention.** Keep a materially sized
   baseline lane from the raw BREAK_60 schedule and permit a second entry only
   during strong health. The baseline must still satisfy a declared minimum
   risk per counted trade.
2. **Causal risk scaling.** Preserve candidate count while reducing risk during
   weak health rather than deleting every trade. Frequency should count only
   trades above a locked material-risk threshold so scaling cannot game the
   target.
3. **Portfolio-aware daily selection.** Choose at most two candidates by
   incremental account risk, direction, existing V59 exposure, and expected
   diversification. Optimize the shared account directly instead of proving a
   sleeve alone and combining it later.
4. **Independent second lane.** Search for a mechanism whose losses occur on
   different days from BREAK_60. A genuinely diversifying lane may reduce
   portfolio drawdown while restoring the missing `0.223/day`.
5. **State features independent of recent trade outcomes.** Test causal
   volatility, session, spread, and trend-state controls so the router is not
   driven by highly overlapping realized markouts.
6. **Fresh evaluation boundary.** Any new program needs a new preregistration,
   explicit contamination statement, nested walk-forward development, and an
   untouched prospective period. It must not be named or treated as V101.

## Recommended Next Discussion

Before more code, define three items precisely:

- the minimum initial risk required for a trade to count toward frequency;
- whether the `35R` standalone cap or the frozen dollar account cap is the
  primary design constraint; and
- the fresh data boundary that will remain untouched for the next program.

Then compare only three architecture proposals on paper: two-tier admission,
material-risk scaling, and portfolio-aware diversification. Select one based on
causality, expected frequency recovery, drawdown mechanism, and testability.
