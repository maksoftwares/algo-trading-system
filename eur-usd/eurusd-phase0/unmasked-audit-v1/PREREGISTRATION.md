# EURUSD V1 Unmasked Audit Preregistration

Frozen before the audit result was inspected.

Post-run audit amendment: the original text said all non-hour inputs remained
unchanged but did not enumerate `InpMinBodyFraction`. Inspection of the exact
V1 and unmasked INIs showed that both used `0.40`, while the earlier published
V1 preset incorrectly said `0.0`. The explicit `0.40` wording below documents
the actual unchanged input; it was not selected or modified after seeing the
unmasked result.

## Candidate

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1_UNMASKED_AUDIT`

This is a research-only attribution run. It is not a promotion candidate,
deployment artifact, demo strategy, live strategy, or independent holdout.

## Single authorized change

Relative to frozen
`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1`, change only:

```text
InpBlockedEntryHoursCsv=6,7,10,13
```

to:

```text
InpBlockedEntryHoursCsv=
```

The EA source, compiled logic, EURUSD symbol, M5 execution chart, M30 signal
timeframe, long-only direction, RSI/Bollinger entry, stop construction,
minimum completed-bar body fraction `0.40`, 700-point stop rejection, 0.8R
target, 0.01 lot, spread guard, position mutex, daily cap, tester model,
account currency/deposit, date range, and broker history remain unchanged.

No reclaim, trend, cooldown, episode mutex, stop, target, threshold, indicator,
lot, or replacement session rule may be tested in this experiment.

## Frozen evidence boundary

- Tester window: `2022.07.01` through `2026.07.02`.
- All data through `2026.07.02` are retrospective development evidence.
- Tester: isolated `C:\MT5A1M5MomentumBacktest`.
- Model: MT5 Strategy Tester `Model=0`, every tick.
- Deposit/currency/leverage: USD 1,000 / USD / 1:200.
- Local tester agent only; remote and cloud agents disabled.
- No live/demo chart, order, position, account, or runtime may be touched.

## Required evidence

1. Exact MT5 report, tester INI, source, EX5, compile log, and hashes.
2. Signal, order-attempt, and filled-trade ledgers.
3. Matched comparison against frozen V1.
4. Outcomes added by removing the mask.
5. Counterfactual reconstruction of the old mask from the unmasked ledger,
   explicitly labelled non-causal because newly admitted positions can block or
   displace later entries.
6. Calendar-year, month, and fixed six-hour broker-time buckets.
7. Episode sequence using the frozen definition: an episode begins with the
   first qualifying oversold signal and ends at the first completed M30 close
   above that bar's current M30 Bollinger middle band.
8. Price P/L and swap cost decomposition from MT5 deals.
9. Trial/multiplicity inventory.

## Predeclared decision gates

The family is killed immediately if the unmasked run has any of:

- full-period MT5 profit factor below `1.05`;
- combined 0.5-pip round-trip cost-stress PF below `0.95`;
- fewer than two positive full calendar years among 2023, 2024, and 2025;
- positive net result entirely dependent on hours 6, 7, 10, and 13.

Passing these gates only authorizes the reviewer-defined diagnostic branch. It
does not establish an edge or authorize runtime use.

If the implementation audit discovers a source/input/preset contract mismatch,
the branch decision may be calculated but no intervention may run until the
actual V1 contract is corrected and frozen.

## Diagnostic branch rule

After the result exists, the episode-mutex intervention is eligible only if:

- entry sequence two or higher represents at least 20% of filled trades; and
- repeat-entry PF is below 0.90 in at least two of 2023, 2024, and 2025.

Otherwise the reviewer-defined immediate next-bar reclaim is the sole eligible
entry intervention. Both must not be run and compared.
