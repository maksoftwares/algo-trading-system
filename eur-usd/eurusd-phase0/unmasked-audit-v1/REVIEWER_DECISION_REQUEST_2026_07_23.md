# Independent Reviewer Decision Request — EURUSD V1 Unmasked Audit

## Your role

Act as a skeptical independent systematic-trading reviewer. Do not optimize the
strategy, invent filters, or choose parameters from this development history.
Audit the evidence, resolve the contract ambiguities below, and return an
executable next-step decision.

We need direct answers, not general suggestions. If evidence is insufficient,
state exactly which artifact or field is missing and whether that omission
requires `STOP`, `REPAIR`, `RETEST`, or `KILL`.

## Research boundary

- Instrument: EURUSD
- Direction: long only
- Signal timeframe: M30
- Execution/test timeframe: M5 with M30 completed-bar indicators
- Data status: all data from 2022-07-01 through 2026-07-02 is retrospective
  development evidence
- Test environment: exact MT5 Strategy Tester, every-tick mode, 99% history
  quality, Capital.ComMena-Demo build 5833
- Fixed size: 0.01 lot
- Starting balance: USD 1,000
- No demo, live, broker-runtime, portfolio, or XAUUSD decision is authorized
- Frozen V1 must remain immutable
- Do not treat exact hashes or MT5 reproduction as proof of alpha

Candidate under review:

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1_UNMASKED_AUDIT`

## What changed since your prior review

Your requested unmasked audit is complete. The sole trading change was:

```text
InpBlockedEntryHoursCsv: "6,7,10,13" -> ""
```

The actual V1 and unmasked runs both used
`InpMinBodyFraction=0.40`. Signal-stream parity is exact.

### Full-period unmasked result

| Metric | Result |
|---|---:|
| Trades | 1,145 |
| Wins / losses | 659 / 486 |
| Win rate | 57.55% |
| Net P&L | +USD 77.26 |
| MT5 PF | 1.11 |
| Expected payoff | +USD 0.07/trade |
| Average winner / loser | 0.8186 |
| MT5 maximal equity DD | USD 27.56 / 2.68% |
| Price profit | +USD 90.57 |
| Commission | USD 0.00 |
| Swap | -USD 13.31 |

Primary stress, defined as 0.5 pip round-trip adverse execution plus 1.25 times
negative commission/swap, produces +USD 16.68 and PF 1.0229. Severe 1.0-pip
stress produces -USD 40.57 and PF 0.9461.

The unmasked run passes your four immediate kill gates:

- PF 1.11 is at least 1.05;
- primary stress PF 1.0229 is at least 0.95;
- 2023 and 2025 are positive full years;
- profitability does not depend entirely on the previously blocked hours.

Passing those gates does not establish an edge or promotion authority.

### Recent-window deterioration

Trades are assigned by realized exit time. The tester endpoint
`2026-07-02` is exclusive.

| Period | Trades | W / L | Win rate | Net | PF | Avg/trade | Closed-trade DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3 months | 89 | 50 / 39 | 56.18% | +USD 6.00 | 1.1491 | +USD 0.0674 | USD 6.75 |
| 6 months | 180 | 102 / 78 | 56.67% | +USD 11.92 | 1.1251 | +USD 0.0662 | USD 10.44 |
| 1 year | 312 | 172 / 140 | 55.13% | +USD 2.98 | 1.0167 | +USD 0.0096 | USD 19.42 |

| Period | Primary-stress net / PF | Severe-stress net / PF |
|---|---:|---:|
| 3 months | +USD 1.36 / 1.0321 | -USD 3.09 / 0.9301 |
| 6 months | +USD 2.59 / 1.0261 | -USD 6.41 / 0.9379 |
| 1 year | -USD 13.14 / 0.9291 | -USD 28.74 / 0.8505 |

The one-year breakeven win rate is 54.72% versus 55.13% observed, leaving only
about 0.41 percentage points of win-rate margin.

### Matched causal attribution

- 2,957 signals exist in both V1 and unmasked runs.
- Full signal-stream parity: exact.
- 2,957 attempt rows exist in each run; 469 attempt decisions changed.
- 789 common entry timestamps have 789 exact common outcomes.
- Unmasked-only entries: 356.
- Of those, 345 occur in the old blocked hours.
- Eleven other unmasked-only trades and 42 V1-only trades arise from the
  one-position path dependency.
- Simple post-hoc removal of old-hour trades does not reconstruct V1.
- Trades in the formerly blocked hours on the unmasked causal path: 345 trades,
  -USD 37.03, PF 0.8414.

### Episode branch result

The preregistered episode definition labels 2,129 episodes and all 2,957
signals.

- Repeat filled entries: 517 of 1,145 trades, or 45.15%.
- Repeat-entry PF: 1.0448.
- Repeat PF by full year:
  - 2023: 1.0912
  - 2024: 1.0295
  - 2025: 0.9565
- Zero years among 2023–2025 have repeat-entry PF below 0.90.

Therefore, your episode-mutex branch rule fails. Under the preregistered branch,
the only eligible alpha intervention is the immediate next-bar reclaim. We
have not run it.

## Blocking contract defects discovered

### 1. Body-fraction mismatch

The published frozen V1 preset states:

```text
InpMinBodyFraction=0.0
```

The exact V1 tester INI and the exact unmasked tester INI both used:

```text
InpMinBodyFraction=0.40
```

The unmasked attribution remains internally valid because the exact V1 and
unmasked runs both used 0.40 and have exact signal parity. However, the written
V1 contract is not identical to the executed V1 contract.

### 2. Startup latch

The shared research EA does not explicitly initialize the new-M30-bar latch
fail-closed. Its first tick can evaluate the previously completed M30 bar. No
startup signal or trade occurred in either exact run; the first unmasked signal
was at `2022-07-01 12:30:00`, so the reported economics were unaffected.

Any corrected baseline should initialize the latch and wait for the next native
M30 bar transition before evaluating a signal.

### 3. Tester leverage discrepancy

The tester INI requested 1:200 leverage, while the MT5 report records 1:50.
Fixed-lot trade P&L is unaffected, but provenance differs.

### 4. Shared-source immutability

The old shared `ForexMeanReversionScout.mq5` source produced the frozen V1
research evidence. We propose copying it to a new candidate-specific research
EA and applying only the startup-latch repair there, preserving V1 unchanged.

## Decisions required from you

Answer every numbered item. Use `YES`, `NO`, or one of the requested verdicts
before explaining.

### A. Strategy-family decision

1. Given full PF 1.11, one-year PF 1.0167, and negative one-year primary-stress
   P&L, is the family still entitled to the single bounded reclaim experiment?
   Answer `CONTINUE_ONE_TEST` or `KILL_NOW`.
2. If `KILL_NOW`, identify the exact kill rule now triggered.
3. If `CONTINUE_ONE_TEST`, confirm that no other entry, exit, stop, session,
   trend, volatility, RSI, Bollinger, ATR, or sizing change may be tested first.
4. Confirm whether failure of the reclaim experiment ends this EURUSD
   mean-reversion family, rather than authorizing another rescue test.

### B. Corrected baseline identity and parity

5. Must the actual executed V1 contract with `InpMinBodyFraction=0.40` receive a
   new immutable baseline ID? Answer `NEW_ID_REQUIRED` or
   `ANNOTATE_EXISTING_ID`.
6. If a new ID is required, approve or replace:
   `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT`.
7. Confirm the corrected baseline must have no hour mask, body fraction 0.40,
   the startup latch repair, and every other actual V1 input unchanged.
8. Is exact reproduction of 1,145 trades and +USD 77.26 required after the
   startup repair, given that no startup signal existed? State the allowed
   numeric/row-level tolerance, if any.
9. Confirm that any trade-ledger difference after a performance-neutral startup
   repair is an automatic stop requiring explanation before intervention.
10. Does the 1:50 report versus 1:200 INI mismatch require rerunning at an
    explicitly verified leverage, or is it an annotated provenance exception
    for this fixed-lot baseline?
11. Confirm the corrected candidate must use its own source and EX5 identity,
    leaving the shared V1 source, preset, report, and hashes untouched.

### C. Startup and execution semantics

12. Approve this startup rule: on initialization, record the current native M30
    bar-open timestamp and do not evaluate a setup until that timestamp changes.
13. If initialization occurs exactly on a native M30 transition, should the EA
    still fail closed until the following transition?
14. Confirm that signal time, decision time, first executable tick, request
    time, fill time, and exit time must remain separately logged.
15. Confirm that a failed order attempt consumes the setup exactly as in the
    baseline, unless you explicitly authorize different behavior.
16. Confirm that the existing one-position restriction remains unchanged.

### D. Immediate next-bar reclaim contract

17. Approve or correct this definition:
    - original setup occurs on completed M30 bar `t`;
    - completed bar `t+1` must close strictly above its own completed-bar lower
      Bollinger Band;
    - enter on the first executable tick of `t+2`;
    - otherwise the setup expires permanently.
18. Does equality (`close == lower_band`) pass or fail? We propose fail because
    the rule says “above.”
19. Must `t+1` independently satisfy the original RSI, close-below-band, candle,
    and body-fraction conditions? We propose no.
20. If a second raw setup appears while the first setup awaits `t+1`, is it
    ignored, does it replace the pending setup, or create a separate pending
    setup? Choose one exact behavior.
21. If another position is open on the first executable tick of `t+2`, does the
    confirmed setup expire, or may it wait? We propose immediate expiration to
    avoid a hidden waiting window.
22. If the first `t+2` order attempt fails, may it retry during `t+2`? We
    propose preserving the baseline attempt/consumption rule.
23. Which completed bars define the unchanged six-bar swing low for the delayed
    entry: bars ending at `t`, or the most recent six completed bars ending at
    `t+1`? This must be explicit before coding.
24. Which completed bar supplies ATR for the unchanged stop calculation: `t` or
    `t+1`?
25. Is the 0.8R target calculated from the actual accepted fill and the final
    accepted stop, exactly as in the baseline?
26. If the required stop distance exceeds the 700-point ceiling, must the
    reclaim candidate preserve the actual baseline behavior or reject the
    trade? Do not let us choose after seeing performance.
27. Confirm no multi-bar reclaim waiting window, alternate threshold, candle
    color rule, extra RSI rule, or tuned buffer is permitted.
28. Confirm we must record all raw setups, confirmations, expirations, blocked
    position states, attempts, order results, deals, and exits—not just filled
    trades.

### E. Exact experiment gates

29. Is the reclaim experiment’s required base-PF improvement an absolute
    increase of at least 0.10 over the corrected unmasked PF (approximately
    1.11 to at least 1.21), or must it independently reach full PF 1.20?
30. Confirm the minimum full-period trade count is 400.
31. Confirm the minimum full-period primary-stress PF is 1.15.
32. Confirm whether the severe-stress requirements are PF at least 1.00 and
    positive net.
33. Confirm required recent gates: last-12-month PF 1.22 and last-6-month PF
    1.20, or provide corrected thresholds.
34. Confirm required annual results: 2023, 2024, and 2025 all positive, with at
    least two years having PF at least 1.15.
35. Confirm payoff ratio must be at least 0.90.
36. Confirm MT5 maximum floating-equity drawdown must not exceed USD 33.94.
37. Confirm concentration, rolling-window, weekly block-bootstrap, DSR, and
    regime-coverage gates that are mandatory for historical admission.
38. State whether every gate is conjunctive. If not, provide the exact
    decision hierarchy and identify which failures are fatal.
39. State the minimum result that authorizes the conditional Bollinger-basis
    exit experiment, and whether that exit test remains allowed given the now
    observed weak one-year result.
40. If the reclaim improves full PF but fails recent or stress gates, is the
    required verdict `KILL`, `REJECT_RECLAIM_KEEP_BASELINE`, or another exact
    status?

### F. Evidence completeness

41. Review `outputs/locked/ARTIFACT_MANIFEST.json` and list every required
    artifact still missing before contract repair.
42. List every artifact required after contract repair but before the reclaim
    run.
43. List every artifact required after the reclaim run before a decision.
44. Are the exact MT5 report, source, EX5, compiler log, preset/INI, signal log,
    attempt/order log, trade ledger, startup log, M30 bar export, matched diffs,
    episode labels, cost decomposition, year/month/session buckets, trial
    inventory, and hash manifest sufficient for the current decision?
45. Which missing fields are fatal now: symbol specification, bid/ask at signal
    and fill, requested versus actual SL/TP, stop-component attribution,
    cap activation, MAE/MFE, holding bars, rollover crossing, or daily return
    stream?
46. May any missing diagnostic be added without changing trading logic, or must
    the baseline be rerun whenever telemetry changes?
47. Is byte-identical trade-ledger parity sufficient, or must signal, attempt,
    order, deal, and management ledgers also be byte-identical?
48. Confirm that the preserved 33 local JSON reports and 114 flattened result
    rows are evidence of known multiplicity, not proof that every historical
    informal trial was retained.
49. Given incomplete historical trial preservation, is DSR an automatic fail,
    informational only, or computable with a conservative assumed trial count?
50. Do we need exact native-tick or real-tick coverage beyond the reported
    every-tick mode and 99% history quality before running the single
    falsification experiment?

### G. Research governance and prospective boundary

51. Confirm all data through 2026-07-02 remains development data.
52. Define the quarantine start timestamp for data accrued after 2026-07-02 but
    before final source/EX5/input hashes are frozen.
53. Confirm no result may be described as prospective until the final champion
    identity is frozen.
54. Confirm the prospective requirement remains 250 trades and 12 completed
    calendar months, whichever occurs later.
55. Confirm no EURUSD demo/live attachment or order placement is permitted
    during retrospective research.
56. Confirm XAUUSD performance, diversification, or portfolio effects may not
    rescue a failed standalone EURUSD result.

## Required response format

Return exactly these sections:

1. `VERDICT`: one of `KILL_NOW`, `REPAIR_THEN_ONE_TEST`, or `REPAIR_ONLY`.
2. `CONFIDENCE`: `LOW`, `MEDIUM`, or `HIGH`, with the main uncertainty.
3. `QUESTION_ANSWERS`: numbered answers 1–56.
4. `FROZEN_CORRECTED_BASELINE_CONTRACT`: a complete field/value table.
5. `FROZEN_RECLAIM_CONTRACT`: a complete state-transition and field/value
   table, or `NOT_AUTHORIZED`.
6. `PASS_FAIL_GATES`: exact formulas, thresholds, hierarchy, and fatal gates.
7. `MISSING_EVIDENCE`: grouped into before repair, before intervention, and
   after intervention.
8. `INVALID_TESTS`: explicit actions that would invalidate the program.
9. `NEXT_SINGLE_ACTION`: one action only.

Do not provide multiple strategy variants for us to choose from. Resolve each
ambiguity before authorizing code or another MT5 performance run.

## Evidence map

- `README.md`
- `PREREGISTRATION.md`
- `outputs/audit/EURUSD_V1_UNMASKED_AUDIT_RESULT.md`
- `outputs/audit/EURUSD_V1_UNMASKED_AUDIT_RESULT.json`
- `outputs/audit/EURUSD_V1_UNMASKED_RECENT_WINDOWS.md`
- `outputs/audit/EURUSD_V1_UNMASKED_RECENT_WINDOWS.csv`
- `outputs/audit/EURUSD_V1_UNMASKED_RECENT_WINDOWS.json`
- `outputs/audit/MATCHED_SIGNAL_ATTEMPT_DIFF.csv`
- `outputs/audit/MATCHED_TRADE_DIFF.csv`
- `outputs/audit/TRADES_ADDED_BY_UNMASKING.csv`
- `outputs/audit/UNMASKED_TRADE_LEDGER_ENRICHED.csv`
- `evidence/TRIAL_REGISTRY.csv`
- `evidence/MULTIPLICITY_NOTE.md`
- `evidence/PRIOR_REPORT_INVENTORY.csv`
- `evidence/PRIOR_TRIAL_RESULT_INVENTORY.csv`
- `outputs/locked/ARTIFACT_MANIFEST.json`

The exact MT5 report, source, EX5, compiler log, tester INI, logs, and M30 bar
telemetry are under `outputs/mt5`, `outputs/bar_audit`, `outputs/locked`, and
`mt5/Experts`.
