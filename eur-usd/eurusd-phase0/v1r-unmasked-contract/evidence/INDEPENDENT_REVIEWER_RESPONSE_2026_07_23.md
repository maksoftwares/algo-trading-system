## 1. VERDICT

`REPAIR_THEN_ONE_TEST`

The predeclared immediate kill gates were passed, so killing the family now because the one-year window looks weak would introduce a new post-hoc rule. That does **not** mean the edge is established. The unmasked result remains economically fragile:

- Full-period MT5 PF: `1.11`
- Full-period primary-stress PF: `1.0229`
- Full-period severe-stress PF: `0.9461`
- Last-12-month PF: `1.0167`
- Last-12-month primary-stress PF: `0.9291`
- Last-12-month net after primary stress: `-USD 13.14`
- Last-12-month observed win-rate margin above break-even: approximately `0.41` percentage points

The family is entitled to **one** predeclared causal entry test—the immediate next-bar reclaim—only after the corrected unmasked baseline is rebuilt and frozen.

The present packet is not yet sufficient to authorize that run because the source-to-binary chain is not closed:

- `ARTIFACT_MANIFEST.json` hashes the EX5 and compiler log but does not hash the `ForexMeanReversionScout.mq5` source used to produce that EX5.
- The compiler log identifies only a mutable terminal-local source path.
- The executed INI contains inputs absent from the committed source, so the packet does not prove which inputs were active and which were silently ignored.
- The current audit's “exact common outcome” comparison checks exit time and net P&L, not the complete trade/order/deal geometry.
- The baseline target is calculated from the pre-request Ask and requested stop, not guaranteed to be re-anchored to the accepted fill.

Therefore:

1. repair and freeze a source-bound corrected baseline;
2. require canonical parity with the 1,145-trade unmasked benchmark;
3. run only the frozen immediate next-bar reclaim;
4. kill the family if the repair parity or reclaim gates fail.

No chart, demo, live, shadow, or broker-runtime action is authorized.

---

## 2. CONFIDENCE

`MEDIUM`

Confidence is high on the governance decision and low promotion readiness, but only medium overall because the packet does not bind the compiled EX5 to an immutable source snapshot and several required execution fields are missing.

### Evidence supporting the decision

- The exact unmasked ledger contains `1,145` trades, `USD 77.26` net, PF `1.11`, payoff ratio `0.8186`, and maximum MT5 floating-equity drawdown `USD 27.56`.
- The last 12 months contain `312` trades but only `USD 2.98` net and PF `1.0167`; primary stress makes that period negative.
- The episode-mutex branch is correctly disallowed by the preregistered rule: repeat trades are `45.15%`, but repeat-entry PF is not below `0.90` in two of 2023–2025.
- The committed source uses completed-bar shift `1` for ATR, Bollinger Bands, RSI, OHLC, and shifts `1..6` for the swing low.
- The source rejects stops above `700` points rather than truncating them.
- The source does not initialize the new-signal-bar latch in `OnInit()`, so the first tick can evaluate the previously completed bar.
- `CTrade::Buy()` returning `true` proves only successful request-structure checking, not necessarily an executed deal. The result code and deal must be checked separately.
- MT5 `Model=0` / “Every tick” with `99%` history quality is not proof that the entire run used native real ticks; MT5 may generate ticks where native tick data are unavailable.

### Exact evidence reviewed

Repository: `maksoftwares/algo-trading-system`  
PR: `#5`  
Exact commit: `464b1b8733ddd7c98c9bcf27a73622e1527de12c`

Primary reviewed paths included:

- `eur-usd/eurusd-phase0/unmasked-audit-v1/REVIEWER_DECISION_REQUEST_2026_07_23.md`
- `eur-usd/eurusd-phase0/unmasked-audit-v1/outputs/audit/EURUSD_V1_UNMASKED_AUDIT_RESULT.json`
- `eur-usd/eurusd-phase0/unmasked-audit-v1/outputs/audit/EURUSD_V1_UNMASKED_RECENT_WINDOWS.json`
- `eur-usd/eurusd-phase0/unmasked-audit-v1/outputs/locked/ARTIFACT_MANIFEST.json`
- `eur-usd/eurusd-phase0/unmasked-audit-v1/outputs/locked/compile_ForexMeanReversionScout.log`
- `forex-research/mt5/Experts/ForexMeanReversionScout.mq5`
- the exact V1 and unmasked tester INIs
- the V1 and unmasked presets
- signal, order, trade, startup, episode, multiplicity, and audit-builder artifacts
- the audit and recent-window tests

Relevant official MQL5 references:

- Timeseries index zero is the current unfinished bar:  
  https://www.mql5.com/en/docs/series
- `CTrade::Buy()` success does not by itself prove deal execution:  
  https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade/ctradebuy
- “Every tick” may contain generated ticks; real-tick testing is a distinct mode:  
  https://www.mql5.com/en/docs/runtime/testing

---

## 3. QUESTION_ANSWERS

### A. Strategy-family verdict

**1. `CONTINUE_ONE_TEST`.**  
The family may continue to one reclaim test **only after contract and evidence repair**. The predeclared immediate kill gates passed. The weak one-year result is a major warning and a stringent falsification burden, but it is not one of the already frozen immediate kill rules.

**2. `NOT_APPLICABLE`.**  
No predeclared immediate kill rule has been triggered. Creating a new kill rule after seeing the one-year deterioration would be post-hoc governance. The family can still be killed by repair-parity failure or by failure of the reclaim gates below.

**3. `YES`.**  
Before the reclaim test, no other entry, exit, stop, session, trend, volatility, RSI, Bollinger, ATR, body-fraction, sizing, target, cooldown, rollover, spread, or management change may be performance-tested. Source binding, startup-latch repair, leverage alignment, logging, and analytics corrections are evidence/contract repairs, not alpha variants, and they must reproduce the baseline.

**4. `YES`.**  
Failure of the reclaim experiment ends this EURUSD RSI/Bollinger close-fade family. It does not authorize another entry filter, session mask, stop variant, target sweep, or regime rescue. A Bollinger-middle-band exit test is allowed only if reclaim **passes** the continuation gates and is not classified as a failed reclaim.

### B. Corrected baseline

**5. `NEW_ID_REQUIRED`.**  
The actual executed contract used `InpMinBodyFraction=0.40`, while the published frozen V1 preset states `0.0`. The unmasked baseline also requires a startup-latch correction and a new source/EX5 identity. Those are not annotations to immutable V1; they define a new baseline.

**6. `APPROVE`.**  
Use:

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT`

`V1R` means contract-repaired. Frozen V1 and the existing unmasked audit remain immutable historical evidence.

**7. `YES`, with two mandatory provenance additions.**  
The corrected baseline must contain:

- no blocked-hour mask;
- `InpMinBodyFraction=0.40`;
- the fail-closed startup latch;
- every other **active** V1 trading input and trading semantic unchanged;
- an explicitly verified effective leverage;
- a source-to-EX5 identity chain.

Legacy INI keys that are not declared by the candidate-specific source must be removed rather than silently retained. If the terminal-local source proves that any such key was active, its executed value must be frozen and parity must be demonstrated.

**8. `YES`.**  
Because neither exact run produced a startup signal or startup trade, the corrected baseline must reproduce:

- `2,957` canonical raw signal rows;
- `2,957` canonical decision/attempt rows;
- `1,145` filled trades;
- `659` wins and `486` losses;
- `USD 77.26` net;
- gross profit `USD 779.61`;
- gross loss `USD 702.35`;
- ledger PF `779.61 / 702.35 = 1.1100021357...`;
- the same entry and exit sequence;
- the same MT5 maximum floating-equity drawdown, subject only to exact report serialization.

A mismatch is not excused by calling the startup change “performance-neutral.”

**9. `ZERO_UNEXPLAINED_DIFFERENCES`.**  
After canonicalization, permitted differences are limited to:

- candidate/run ID;
- magic number;
- source and EX5 file names/hashes;
- output file names;
- compiler timestamp;
- order/deal ticket identifiers when MT5 regenerates them;
- one additional startup-latch initialization event.

No tolerance is allowed for:

- row counts;
- signal-bar timestamps;
- decision timestamps;
- action or guard reason;
- direction;
- volume;
- bid/ask strings;
- requested SL/TP strings;
- entry/exit timestamps;
- entry/exit prices to symbol digits;
- per-trade commission, swap, and P&L to the reported cent;
- aggregate P&L to the cent.

Indicator and price fields must match exactly at their frozen logged precision. Any non-identity difference is unexplained until causally reconciled.

**10. `YES`.**  
Any trade difference, order-decision difference, signal difference, or unexplained floating-drawdown difference after startup repair requires `STOP` before reclaim coding or execution.

**11. `YES`, as part of the corrected baseline run.**  
The corrected INI should request `1:50`, and the resulting MT5 report must record `1:50`. A separate 1:200 performance variant is not authorized. If the environment still overrides the requested value, the effective leverage, margin per 0.01 lot, free-margin minimum, and absence of margin rejection/stop-out effects must be documented before continuing.

**12. `YES`.**  
The corrected baseline must use a candidate-specific MQ5 source and candidate-specific EX5. The old V1 source, preset, EX5, report, and hashes remain untouched.

### C. Startup and execution semantics

**13. `APPROVE`.**  
On initialization:

1. read the current native M30 bar-open timestamp;
2. store it as the last-seen signal-bar timestamp;
3. clear any pending reclaim state;
4. do not evaluate the previously completed M30 bar;
5. wait until the native M30 timestamp changes.

**14. `YES`.**  
Even if initialization occurs exactly at a native M30 transition, fail closed and wait for the following transition. This sacrifices one possible setup but prevents ambiguous retroactive processing.

**15. `YES`.**  
Log separately:

- setup-bar open time;
- setup-bar close time;
- signal-detection/decision tick time;
- confirmation-bar open and close time;
- first executable tick time;
- trade-request time;
- server result time where available;
- deal fill time;
- position-open time;
- position-close/exit time.

Do not overload one `timestamp_broker` field to represent all of these events.

**16. `YES`.**  
A failed first order request consumes the setup exactly as the baseline consumes a completed-bar opportunity. There is no retry during the same M30 bar and no carry-forward.

However, request acceptance and fill status must be distinguished:

- `CTrade::Buy()==true` is not sufficient to label a fill;
- `ResultRetcode`, `ResultDeal`, and the resulting deal/position must be reconciled;
- the setup is consumed whether the result is filled, rejected, market-closed, invalid-stops, or another terminal/server failure;
- the daily **entry** count increments only for a confirmed filled entry, not for a request that produced no deal.

**17. `YES`.**  
The one-owned-position restriction remains unchanged: at most one open EURUSD position owned by the candidate's magic number. A pending reclaim setup is not an open position, but it is also limited to one pending setup.

### D. Immediate next-bar reclaim contract

**18. `APPROVE`, with exact temporal wording.**

- A raw setup is defined on completed M30 bar `t`.
- It is detected on the first executable tick after bar `t` completes, which is the first tick of bar `t+1`.
- No entry is attempted then.
- At the first executable tick after `t+1` completes—the first tick of `t+2`—the EA evaluates completed bar `t+1`.
- Confirmation passes only when `Close(t+1) > LowerBand(t+1)`.
- A passing confirmation allows one immediate entry attempt on that same first executable tick of `t+2`.
- A failing confirmation permanently expires setup `t`.
- There is no later confirmation window.

“Next bar” means the next available native M30 bar in the broker series. The code must verify adjacency by stored bar-open timestamps/indexes. Reinitialization clears the pending setup.

**19. `YES`.**  
`Close(t+1) == LowerBand(t+1)` fails. Confirmation is strictly greater-than.

**20. `NO`.**  
Bar `t+1` does not need to satisfy RSI, body fraction, candle color, close-below-band, or any original setup condition. Its only confirmation condition is:

`Close(t+1) > LowerBand(t+1)`

The Bollinger Band is calculated from completed `t+1` data using the same period, deviation, applied price, and symbol/timeframe as the baseline.

**21. `REPLACE_WITH_NEWEST_RAW_SETUP`, without queuing.**  
Processing order at the first tick of `t+2` is:

1. evaluate the old pending setup's confirmation on `t+1`;
2. if confirmation passes, attempt the old setup once and do not create a second pending setup from `t+1`;
3. if confirmation fails, expire the old setup;
4. after expiration, independently evaluate `t+1` as a new raw setup;
5. if `t+1` is a raw setup, it becomes the sole pending setup for confirmation by `t+2`;
6. otherwise return to idle.

No array, queue, or multiple simultaneous pending setups is allowed.

**22. `EXPIRE_IMMEDIATELY`.**  
If an owned position is open at the first executable tick of `t+2`, log `CONFIRMATION_BLOCKED_OWN_POSITION`, expire the setup, and do not wait for the position to close.

**23. `NO_RETRY`.**  
The first attempted request during `t+2` consumes the confirmed setup. Preserve baseline one-attempt semantics.

**24. `THE_SIX_BARS_ENDING_AT t+1`.**  
At the first tick of `t+2`, the swing low uses the most recent six completed M30 bars:

`t-4, t-3, t-2, t-1, t, t+1`

Equivalently, shifts `1..6` at the entry-decision tick. This preserves the baseline rule of using the latest six completed bars relative to the entry attempt.

**25. `t+1`.**  
ATR is the completed ATR(14) value for confirmation bar `t+1`, read with shift `1` at the first tick of `t+2`.

**26. `NO` to the statement that this is guaranteed by the current baseline implementation.**  
The reviewed source calculates the requested long geometry before the order:

- requested SL from current pre-request Ask, ATR, floor, and recent low;
- requested TP as `Ask + 0.8 * (Ask - requested_SL)`.

It then sends SL and TP with the market order. It does not re-anchor TP after receiving `ResultPrice()`.

To preserve one-change attribution, the reclaim experiment must retain that **quote-based requested geometry**. It must log:

- pre-request Ask;
- requested SL and TP;
- accepted fill;
- actual position SL and TP;
- realized initial reward/risk ratio.

Changing to fill-anchored 0.8R would be a separate execution/exit intervention and is not permitted in the reclaim run.

**27. `REJECT_THE_TRADE`.**  
Preserve actual baseline behavior. If the final required stop distance exceeds `700` points, log `stop_ceiling_exceeded`, consume the setup, and place no order. Do not truncate to 700 points.

**28. `YES`.**  
The reclaim experiment cannot introduce:

- a multi-bar confirmation window;
- close-above-band buffers;
- alternative bands;
- alternative RSI thresholds;
- another RSI test on `t+1`;
- candle-color requirements;
- body-fraction requirements on `t+1`;
- a minimum reclaim distance;
- a trend filter;
- a volatility filter;
- a new cooldown;
- a replacement hour/session mask;
- different stop or target geometry;
- fill-anchored target repair;
- a market-close time filter.

**29. `YES`.**  
Log every:

- raw setup;
- setup rejection;
- pending-state creation;
- pending-state replacement;
- confirmation pass/fail;
- equality failure;
- restart discard;
- adjacency failure;
- position block;
- spread block;
- daily-cap block;
- stop-ceiling block;
- terminal/account block;
- request attempt;
- request result;
- order;
- deal;
- position-open event;
- SL/TP state;
- management event;
- exit.

Filled trades alone are insufficient.

### E. Acceptance and kill gates

**30. `YES`.**  
The reclaim base-PF requirement is an absolute improvement of at least `0.10` over the **unrounded corrected baseline ledger PF**.

Using the present ledger:

`PF_baseline = 779.61 / 702.35 = 1.1100021357...`

Therefore:

`PF_reclaim >= PF_baseline + 0.10 = 1.2100021357...`

Display threshold: `>= 1.2100`.

**31. `NO`.**  
Reaching `1.20` alone is not sufficient because it would improve the current baseline by only about `0.09`. The operative formula is:

`PF_reclaim >= max(1.20, PF_baseline + 0.10)`

which is approximately `1.2100`.

**32. `YES`.**  
Minimum full-period filled trade count: `400`.

**33. `YES`.**  
Minimum full-period primary-stress PF: `1.15`.

**34. `YES`.**  
Under severe stress:

- unrounded PF must be `>=1.00`; and
- net P&L must be strictly `>USD 0.00`.

A rounded displayed PF of `1.00` with zero or negative unrounded net fails.

**35. `YES`.**  
Using realized exit timestamps:

- last 12 months `[2025-07-02, 2026-07-02)`: PF `>=1.22`;
- last 6 months `[2026-01-02, 2026-07-02)`: PF `>=1.20`.

These boundaries and the exclusive endpoint must not be changed after the result.

**36. `YES`.**  
Calendar years 2023, 2024, and 2025 must each have strictly positive net P&L after swap and commission. Annual assignment must use realized exit time for P&L attribution.

**37. `YES`.**  
At least two of 2023, 2024, and 2025 must have PF `>=1.15`.

**38. `YES`, for final historical admission.**  
Average winner / absolute average loser must be `>=0.90`.

The sole exception is the predeclared conditional basis-exit route: reclaim may authorize that exit test when all core continuation gates pass and payoff ratio remains below `0.90`. That is not acceptance of the reclaim candidate; it is authorization for the one final mechanism-aligned exit test.

**39. `YES`.**  
MT5 maximum floating-equity drawdown must be:

`<= min(USD 33.94, the locked account-level cap)`

If the account cap is lower, the lower cap controls. Closed-trade reconstructed drawdown is not a substitute.

**40. `MANDATORY CONCENTRATION GATES`.**

All use net trade results after commission and swap:

1. Remove the ten largest winning trades:
   - remaining net P&L `>0`;
   - remaining PF `>=1.05`.
2. The ten largest winners contribute no more than `35%` of full gross profit.
3. The ten largest losses contribute no more than `30%` of full gross loss.
4. Remove the best calendar month by net P&L:
   - remaining PF `>=1.15`.
5. No single calendar month contributes more than `25%` of full gross profit.
6. Use the frozen broker/tester-time entry buckets:
   - `00:00–05:59`
   - `06:00–11:59`
   - `12:00–17:59`
   - `18:00–23:59`
7. Remove the best six-hour entry bucket:
   - remaining PF `>=1.10`.
8. No one six-hour entry bucket contributes more than `50%` of total positive net P&L.
9. The session analysis is a robustness test only and may not be converted into excluded hours.

Calendar month uses exit time. Entry-session buckets use the first request/entry-decision time. Both time bases must be explicit.

**41. `MANDATORY ROLLING GATES`.**

Sort filled trades by exit time, tie-breaking by exit-deal ID. Calculate overlapping full windows starting every ten trades. Do not include partial windows.

| Window | Positive-net window share | Median PF | Minimum PF |
|---|---:|---:|---:|
| 100 trades | `>=65%` | `>=1.15` | `>=0.60` |
| 150 trades | `>=75%` | `>=1.20` | `>=0.75` |
| 250 trades | `>=90%` | `>=1.25` | `>=0.90` |

A window is positive only when its unrounded net is greater than zero.

**42. `PARTLY YES`, with stage separation.**

- Weekly block bootstrap: mandatory for reclaim continuation.
- Volatility and trend regime coverage: mandatory for reclaim continuation.
- DSR: mandatory before any historical-admission or prospective-freeze claim, but currently **not assessable** because historical trial preservation is incomplete.

The incomplete DSR does not block the single predeclared reclaim falsification run. It does block promotion or a claim that multiplicity-adjusted significance has passed.

**43. `NO`, not every gate belongs to the same stage. Gates within each stage are conjunctive.**

Decision hierarchy:

1. **Repair authorization gates — all conjunctive and fatal.**
   - immutable source-to-EX5 binding;
   - canonical input schema;
   - leverage and symbol provenance;
   - corrected baseline parity;
   - no unexplained ledger difference.
   - Failure status: `STOP_REPAIR`, no reclaim.

2. **Reclaim core gates — all conjunctive and fatal.**
   - PF improvement;
   - trade count;
   - primary and severe stress;
   - recent windows;
   - annual results;
   - drawdown;
   - concentration;
   - rolling windows;
   - weekly bootstrap;
   - regime coverage.
   - Failure status: `KILL_FAMILY`.

3. **Final historical-admission gates.**
   - full PF `>=1.30`;
   - payoff ratio `>=0.90`;
   - complete evidence;
   - DSR assessable and passed;
   - all core gates remain passed.
   - Passing does not authorize demo/live; it authorizes freezing for prospective tester validation.

4. **Conditional basis-exit route.**
   - allowed only if every reclaim core gate passes;
   - reclaim PF is at least `1.2100`;
   - the only remaining substantive deficiencies are final PF below `1.30` and/or payoff ratio below `0.90`;
   - no stress, recent, annual, concentration, rolling, bootstrap, regime, evidence, or drawdown gate may have failed.

**44. `KILL`.**  
If reclaim improves full PF but fails a recent-window or stress gate, the family is killed. The corrected baseline remains an immutable research benchmark, not an active candidate. `REJECT_RECLAIM_KEEP_BASELINE` is not authorization for another test.

**45. `YES`, conditionally.**  
The Bollinger-middle-band exit test remains potentially authorized only when reclaim:

- passes source/evidence/parity gates;
- has at least `400` trades;
- has PF `>=1.2100`;
- has primary-stress PF `>=1.15`;
- has severe-stress PF `>=1.00` and positive net;
- passes the 12- and 6-month gates;
- makes 2023, 2024, and 2025 all positive;
- has at least two of those years at PF `>=1.15`;
- remains within `USD 33.94` and the account cap;
- passes all concentration gates;
- passes all rolling gates;
- passes the weekly block-bootstrap gate;
- passes regime-coverage gates;
- has no unexplained execution or parity defect;
- fails final historical admission only because full PF is below `1.30` and/or payoff ratio is below `0.90`.

The basis-exit rule must then be preregistered as the only allowed exit change. If reclaim fails recent or stress gates, no exit test is authorized.

### F. Evidence completeness

**46. `MISSING BEFORE CONTRACT REPAIR`.**

The manifest does not yet close these items:

1. Exact MQ5 source snapshot used to compile `ForexMeanReversionScout.ex5`.
2. SHA256 of that exact source in the locked manifest.
3. Hashes of every nonstandard include or generated dependency.
4. Clean compile procedure proving the EX5 was generated from the locked source:
   - delete/rename prior EX5;
   - compiler executable path and version/build;
   - command line;
   - source path;
   - output path;
   - source hash;
   - output EX5 hash.
5. A compiled-input schema dump showing which INI keys are declared, their types, defaults, and executed values.
6. Reconciliation of executed INI keys absent from the committed source.
7. Reconciliation of source inputs omitted from the executed INI and therefore taken from defaults.
8. Exact symbol specification:
   - digits and point;
   - contract size;
   - tick size;
   - tick value profit/loss;
   - volume min/max/step;
   - stops level;
   - freeze level;
   - spread mode;
   - trade mode;
   - margin calculation mode;
   - swap mode and long swap;
   - account currency and conversion path.
9. Effective leverage proof and minimum free-margin/margin-level evidence.
10. Server-time to UTC/DST mapping.
11. Native-real-tick coverage or an explicit statement that `Model=0` contains simulated ticks.
12. Full canonical order/deal/position reconciliation, not only exit-time/net matching.
13. Actual accepted SL and TP per position.
14. Stop-component attribution and stop-cap activation counts.
15. Corrected annual/month analytics using exit time; the existing annual/month builder groups by entry time while recent windows use exit time.
16. A corrected definition of “filled”: actual deal reconciliation, not `ORDER_SEND_OK` alone.
17. A complete source review proving the tester-only guard, completed-bar shifts, stop rejection, target basis, and setup-consumption behavior in the source actually bound to the EX5.

**47. `REQUIRED AFTER REPAIR, BEFORE RECLAIM`.**

1. Frozen V1R candidate-specific MQ5 source.
2. Frozen V1R EX5.
3. Source, include, compiler-log, and EX5 hashes.
4. Compiler version/build and clean compile evidence.
5. Canonical V1R preset and tester INI with no unknown keys.
6. INI leverage `50` and report leverage `1:50`.
7. Exact symbol specification snapshot.
8. V1R MT5 report and all canonical logs.
9. Canonical parity report against the 1,145-trade unmasked benchmark.
10. Full signal, state, attempt, request, order, deal, position, management, and trade parity.
11. Proof of `2,957` signals, `2,957` decision rows, and `1,145` trades.
12. Exact reproduction of `USD 77.26` net and ledger PF `1.1100021357...`.
13. Stop-component and stop-cap telemetry.
14. Requested-versus-actual fill/SL/TP telemetry.
15. Corrected exit-time year/month reports.
16. Fixed session, rolling, bootstrap, and regime-analysis code frozen before reclaim output exists.
17. Frozen reclaim source specification and state-machine tests.
18. Trial registry updated to include V1R repair as a non-alpha contract repair.
19. A clean output directory and proof stale logs/reports were removed before the run.
20. A new checkout-stable manifest covering every file above.
21. Tests for startup, reinitialization, equality failure, pending replacement, no retry, stop ceiling, open-position expiration, and bar adjacency.
22. No demo/live/chart attachment.

**48. `REQUIRED AFTER RECLAIM, BEFORE FINAL VERDICT`.**

1. Reclaim source, EX5, preset, INI, compiler log, report, and manifest.
2. Baseline-to-reclaim matched raw-setup diff.
3. Pending-state, confirmation, expiration, replacement, and block ledger.
4. Request/order/deal/position/trade reconciliation.
5. Requested and actual fill/SL/TP geometry.
6. Realized initial R and payoff geometry.
7. Stop-component attribution and cap activations.
8. Failed-attempt inventory preserving market-close and invalid-stop outcomes.
9. Full base and stress metrics.
10. Exact 6- and 12-month exit-time windows.
11. Exit-time calendar-year and month buckets.
12. Fixed entry-session buckets.
13. Largest-winner/loss concentration analysis.
14. Best-month and best-session deletion analysis.
15. Rolling 100/150/250-trade analysis.
16. Weekly block-bootstrap output.
17. Volatility and slow-trend regime coverage.
18. MAE and MFE per trade.
19. Holding bars and minutes.
20. Rollover crossings and swap attribution.
21. MT5 floating-equity drawdown and equity curve.
22. Daily end-of-day balance/equity return stream.
23. Updated multiplicity inventory including the repair and reclaim.
24. DSR output only if a defensible trial count exists; otherwise `NOT_ASSESSABLE`.
25. One complete machine-generated pass/fail table with no discretionary overrides.

**49. `YES_FOR_CURRENT_DECISION_ONLY; NO_FOR_EXPERIMENT_AUTHORIZATION`.**  
The listed artifact classes are enough to determine `REPAIR_THEN_ONE_TEST`. They are not currently complete enough to authorize the reclaim run because source identity, symbol specification, accepted SL/TP, and several telemetry fields are absent or unbound.

**50. `FATAL BEFORE THE EXPERIMENT`.**

| Missing field | Fatal before reclaim? | Required treatment |
|---|---|---|
| Symbol specification | `YES` | Needed to validate points, pip value, margin, stops, and stress cost |
| Bid/Ask at decision and actual fill | `YES` | Decision quote and deal fill must be separate |
| Requested versus actual SL/TP | `YES` | Required to verify unchanged stop/target contract |
| Stop-component attribution | `YES` | Must identify ATR, floor, swing-low winner, and final distance |
| Stop-cap activation | `YES` | Must reconcile every rejection over 700 points |
| MAE/MFE | `NO` before run; `YES` before final verdict | Diagnostic/final evidence |
| Holding bars/minutes | `NO` before run; `YES` before final verdict | Exit/rollover diagnosis |
| Rollover crossings | `NO` before run; `YES` before final verdict | Swap and operational diagnosis |
| Daily return stream | `NO` before run; `YES` before admission | Required for DSR and time-series risk analysis |

**51. `YES`, telemetry may be added without intentionally changing trading behavior, but a rerun is mandatory.**  
Any telemetry change alters the source and EX5 identity. Therefore:

- rebuild the corrected baseline;
- rerun it;
- prove canonical parity;
- stop if telemetry changes timing or outcomes.

Analytics-only changes outside the EA do not require a new MT5 run if they consume the same immutable raw artifacts and are themselves hashed/tested.

**52. `ALL_CANONICAL_LEDGERS_REQUIRED`.**  
Byte-identical trade-ledger parity alone is insufficient. Require canonical exact parity for:

- raw signals;
- setup state;
- guard decisions;
- attempts;
- requests;
- order results;
- deals;
- positions;
- management events;
- exits;
- trade ledger.

Raw byte identity is not required where candidate ID, magic, filenames, or ticket IDs differ. Canonical field-level equality is required.

**53. `YES`.**  
The 33 preserved JSON reports and 114 result rows document known multiplicity. They do not prove that every informal, deleted, failed, manual, or unrecorded trial was retained.

**54. `DSR_NOT_ASSESSABLE`.**  
Do not choose a favorable “conservative” trial count without evidence. Treatment:

- for the single reclaim falsification test: DSR is informational/unavailable and does not block running the test;
- for historical admission or prospective freeze: unavailable DSR is a blocking failure;
- a DSR pass may be claimed only after a defensible complete trial inventory or independently justified upper bound is frozen.

**55. `NO` before the single relative reclaim falsification test; `YES` before promotion.**  
The corrected baseline and reclaim may be compared on the same locked MT5 `Model=0` history. The result must be labelled simulator-specific.

Before any historical-admission, prospective, demo, or execution claim, provide:

- real-tick mode rerun or quantified native-tick coverage;
- spread/tick provenance;
- comparison of generated-tick and real-tick outcomes;
- explanation of any trade-path differences.

`99%` history quality does not by itself satisfy this requirement.

### G. Governance and prospective validation

**56. `CONFIRMED`.**

- All data through `2026-07-02` remains retrospective development data.
- Data after `2026-07-02` and before final source, EX5, preset, INI, and history hashes are frozen is quarantined.
- No result is prospective until all final identities and inputs are frozen before observing its outcomes.
- Prospective validation requires at least `250` trades and `12` completed calendar months, whichever occurs later.
- No EURUSD demo or live trading is authorized during retrospective research.
- No chart attachment is authorized.
- XAUUSD performance, diversification, or portfolio PF cannot rescue a failed EURUSD standalone result.
- Historical admission does not itself authorize broker action.

---

## 4. FROZEN_CORRECTED_BASELINE_CONTRACT

### Field/value table

| Field | Frozen value |
|---|---|
| Candidate ID | `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT` |
| Role | Corrected immutable unmasked development baseline |
| Parent evidence | Existing 1,145-trade unmasked audit |
| Frozen V1 treatment | Remains immutable; no overwrite |
| Source file | Candidate-specific `EurUsdM30RsiBbCloseFadeLongV1R.mq5` |
| EX5 file | Candidate-specific `EurUsdM30RsiBbCloseFadeLongV1R.ex5` |
| Source basis | Copy of the exact reviewed committed strategy source, with only startup-latch and non-behavioral telemetry/source-binding repairs |
| Tester-only guard | Mandatory `MQL_TESTER` fail-closed guard |
| Runtime authorization | Tester only; no chart/demo/live/shadow/broker action |
| Symbol | `EURUSD` |
| Execution chart | `M5` |
| Signal timeframe | Native `M30` |
| Direction | Long only |
| Test period | `2022-07-01` inclusive to `2026-07-02` exclusive |
| Broker/server | `Capital.ComMena-Demo` |
| Terminal build | `5833`, or exact rerun build recorded and frozen |
| Tester model | `Model=0`, Every tick |
| Starting deposit | `USD 1,000` |
| Account currency | `USD` |
| INI leverage | `50` |
| Required report leverage | `1:50` |
| Agents | Local only; remote/cloud disabled |
| Fixed lot | `0.01` |
| Risk-normalized sizing | Disabled |
| Magic | `26723003` |
| Run ID | `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT` |
| Signal mode | Bollinger close fade |
| Bollinger applied price | Close |
| Bollinger period | `20` |
| Bollinger deviation | `2.0` |
| Bollinger shift | `0` |
| RSI period | `14` |
| RSI filter | Enabled |
| Long RSI threshold | `RSI <= 35.0` |
| Minimum band distance | `0.0 ATR` |
| Body fraction formula | `abs(close-open) / max(high-low, point)` |
| Minimum body fraction | `>=0.40` |
| Raw long setup | Completed M30 close `<=` completed M30 lower band, RSI `<=35`, body fraction `>=0.40` |
| Candle-color requirement | None |
| Close-location requirement | None |
| Three-bar-move requirement | None |
| Trend filter | None |
| Volatility filter | None beyond existing indicator geometry |
| Blocked hours | Empty / none |
| Cooldown | `0` minutes |
| Maximum spread | `100` points |
| Spread source | Current `SYMBOL_SPREAD`; also log `(Ask-Bid)/Point` and reconcile |
| Maximum entries per broker day | `20` confirmed filled entries |
| Owned open positions | Maximum `1` by symbol and candidate magic |
| Entry timing | First executable tick after a new native M30 bar is detected |
| Startup behavior | Store current M30 open time in `OnInit`; do not evaluate until the next transition |
| Completed-bar shift | `1` |
| ATR period | `14` |
| ATR source | Completed M30 shift `1` |
| Swing-low window | Six completed M30 bars, shifts `1..6` |
| Stop ATR component | `1.4 * ATR(14)` |
| Stop floor | `30` points |
| Long requested SL | `min(recent_low_1_to_6, decision_ask - max(1.4*ATR, 30 points))` |
| Stop ceiling | `700` points |
| Stop-ceiling behavior | Reject and consume setup; do not truncate |
| Risk/reward input | `0.80` |
| Requested TP basis | Pre-request decision Ask and requested SL |
| Long requested TP | `decision_ask + 0.8 * (decision_ask - requested_SL)` |
| Post-fill TP re-anchoring | None; prohibited in baseline/reclaim attribution |
| Deviation | `30` points |
| First failed request | Consumes setup |
| Retry | None |
| Daily count on failed request | No increment unless an actual entry deal exists |
| Order result classification | Request result, retcode, order, deal, and position logged separately |
| Trailing | None |
| Partial close | None |
| Split entry | None |
| Profit protection | None |
| Portfolio guard | None |
| ML/discretion | None |
| Unknown legacy INI keys | Prohibited; canonical INI may contain only declared inputs |
| Startup log | Candidate-specific |
| Signal/state log | Candidate-specific |
| Request/order/deal log | Candidate-specific |
| Position/exit log | Candidate-specific |
| Management log | Candidate-specific, expected empty absent management |
| Output cleanup | Delete stale candidate outputs before each exact run |
| Compile requirement | Clean compile, zero errors, zero warnings |
| Source binding | Source/include/compiler/EX5 hashes in one manifest |
| Parity requirement | Canonical exact reproduction of 2,957 signals, 2,957 decisions, 1,145 trades, and USD 77.26 |
| Baseline status after parity | Research benchmark only; not promoted |

### Baseline implementation invariants

1. `OnInit()` cannot generate a signal.
2. Shift zero cannot be used for signal, ATR, Bands, RSI, OHLC, or swing-low decisions.
3. Each native M30 transition is processed at most once.
4. A qualifying bar produces at most one request attempt.
5. Every guard decision is logged.
6. A `CTrade` method return is not equated with a fill.
7. The actual position and exit deals reconcile to the trade ledger.
8. Stop-cap rejection is preserved in the attempt ledger.
9. No legacy hour mask is reintroduced.
10. Baseline parity is judged before any reclaim code is compiled.

---

## 5. FROZEN_RECLAIM_CONTRACT

### Field/value table

| Field | Frozen value |
|---|---|
| Candidate ID | `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_IMMEDIATE_NEXT_BAR_RECLAIM_V1` |
| Parent baseline | `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT` |
| Only alpha change | Delay entry and require immediate next completed-bar reclaim |
| Inherited fields | Every baseline field except entry state transition |
| Raw setup bar | Completed M30 bar `t` satisfying the corrected baseline raw setup |
| Raw setup detection | First executable tick of `t+1` |
| Pending setups | Maximum one |
| Confirmation bar | Immediate next native completed M30 bar `t+1` |
| Confirmation rule | `Close(t+1) > LowerBand(t+1)` |
| Equality | Fails |
| Confirmation RSI | Not evaluated |
| Confirmation body fraction | Not evaluated |
| Confirmation candle color | Not evaluated |
| Confirmation buffer | None |
| Confirmation window | One bar only |
| Entry time | First executable tick of `t+2` |
| Adjacency check | Stored setup bar must equal series shift `2` at the `t+2` decision tick |
| Restart behavior | Clear pending state; no retroactive confirmation/entry |
| New raw setup on failed confirmation bar | Old expires; `t+1` becomes the sole new pending setup |
| Queue | Prohibited |
| Open position at entry tick | Confirmed setup expires immediately |
| Guard failure at entry tick | Confirmed setup expires immediately |
| Failed request | Consumes setup; no retry |
| ATR for delayed stop | Completed `t+1`, shift `1` at entry tick |
| Swing low | Latest six completed bars ending at `t+1`, shifts `1..6` |
| Stop ceiling | Reject if `>700` points |
| Target | Preserve baseline quote-based requested 0.8R |
| Fill re-anchoring | Prohibited in this experiment |
| Additional filters | Prohibited |
| Output requirements | Full raw setup, state, confirmation, guard, request, order, deal, position, and exit logs |

### State-transition table

| Current state | Event | Condition | Required action | Next state |
|---|---|---|---|---|
| `BOOTSTRAP` | `OnInit` | Current M30 open time available | Store current M30 open time, clear pending setup, log initialization, evaluate nothing | `IDLE` |
| `BOOTSTRAP` | `OnInit` | M30 time unavailable | Fail initialization or remain fail-closed; no signal | `STOPPED` or `BOOTSTRAP` |
| `IDLE` | Native M30 transition | Completed bar `b` is not a raw setup | Log no setup where diagnostic logging is enabled | `IDLE` |
| `IDLE` | Native M30 transition | Completed bar `b` is a raw setup | Store bar ID/time and required raw values; log `RAW_SETUP_PENDING` | `WAIT_CONFIRM` |
| `WAIT_CONFIRM` | Reinitialization | Any | Log pending discard; clear it; do not reconstruct from history | `IDLE` |
| `WAIT_CONFIRM` | Next native M30 transition | Stored setup is not exactly series shift `2` | Log adjacency failure and expire; optionally evaluate the latest completed bar as a fresh raw setup only | `IDLE` or `WAIT_CONFIRM` |
| `WAIT_CONFIRM` | Next native M30 transition | `Close(t+1) > LowerBand(t+1)` | Log confirmation pass; evaluate all unchanged execution guards on the same tick | `EXECUTE_ONCE` |
| `WAIT_CONFIRM` | Next native M30 transition | `Close(t+1) <= LowerBand(t+1)` and `t+1` is not a raw setup | Log confirmation failure and old-setup expiration | `IDLE` |
| `WAIT_CONFIRM` | Next native M30 transition | `Close(t+1) <= LowerBand(t+1)` and `t+1` is a raw setup | Log old expiration and new pending setup; replace, do not queue | `WAIT_CONFIRM` |
| `EXECUTE_ONCE` | Same first tick of `t+2` | Owned position exists | Log block and expire | `IDLE` |
| `EXECUTE_ONCE` | Same first tick of `t+2` | Spread/daily cap/trading/stop/lots guard fails | Log exact block and expire | `IDLE` |
| `EXECUTE_ONCE` | Same first tick of `t+2` | All guards pass | Calculate stop from `t+1` ATR and six bars ending `t+1`; send one request; log request/result/deal | `IDLE` |
| `EXECUTE_ONCE` | Request returns no deal | Any retcode | Consume setup; no retry | `IDLE` |
| `EXECUTE_ONCE` | Entry deal confirmed | Valid position | Reconcile actual fill and actual SL/TP; increment filled-entry count | `IDLE` |

### Reclaim invariants

1. One pending setup maximum.
2. One confirmation bar maximum.
3. One request maximum.
4. No bar-zero indicator reads.
5. No pending state survives reinitialization.
6. No wait after a position or operational guard block.
7. No target, stop, session, or cost-rule change.
8. Consecutive oversold bars can replace the expired pending setup but never create a queue.
9. Confirmation and raw-setup evaluation are separately logged.
10. The baseline and reclaim must share the same locked history and tester environment.

---

## 6. PASS_FAIL_GATES

### Metric formulas

For trade-level net outcome `P_i`, including price P&L, commission, and swap:

`GrossProfit = Σ max(P_i, 0)`

`GrossLoss = -Σ min(P_i, 0)`

`PF = GrossProfit / GrossLoss`

`PayoffRatio = mean(P_i | P_i > 0) / abs(mean(P_i | P_i < 0))`

All gates use unrounded calculations. Rounding is for display only.

### Cost-stress formula

Derive pip value from the frozen MT5 symbol specification and actual trade volume. Do not hard-code `USD 0.10` until the symbol specification proves it.

For negative cost `c < 0`:

`stressed_cost(c) = 1.25 * c`

For nonnegative cost:

`stressed_cost(c) = c`

For each trade:

`PrimaryStress_i = PriceProfit_i - value_of_0.5_round_trip_pip_i + stressed_commission_i + stressed_swap_i`

`SevereStress_i = PriceProfit_i - value_of_1.0_round_trip_pip_i + stressed_commission_i + stressed_swap_i`

If an added execution charge turns a small winner into a loser, it must be reclassified as a loss in PF.

### Stage 0 — contract-repair gates

All are fatal and conjunctive:

| Gate | Pass condition |
|---|---|
| Candidate identity | New V1R ID and candidate-specific source/EX5 |
| Source binding | Source, includes, compiler, and EX5 hashes all frozen |
| Compile | `0` errors and `0` warnings |
| Input schema | No unknown or silently ignored INI keys |
| Leverage | INI and report both `1:50` |
| Symbol provenance | Complete specification frozen |
| Startup | Fail-closed latch verified |
| Signal parity | Exactly `2,957` canonical signal rows |
| Decision parity | Exactly `2,957` canonical attempt/decision rows |
| Trade parity | Exactly `1,145` trades |
| Win/loss parity | `659 / 486` |
| Net parity | Exactly `USD 77.26` |
| Gross parity | `USD 779.61 / USD 702.35` |
| PF parity | `1.1100021357...` from ledger |
| Ledger parity | Zero unexplained differences across all canonical ledgers |
| Safety boundary | Tester only; no broker runtime |

Any failure: `STOP_REPAIR`. No reclaim run.

### Stage 1 — reclaim core continuation gates

All are fatal and conjunctive:

| Gate | Threshold |
|---|---:|
| Full-period PF | `>= PF_baseline + 0.10`, approximately `>=1.2100` |
| Full-period trades | `>=400` |
| Primary-stress PF | `>=1.15` |
| Severe-stress PF | `>=1.00` unrounded |
| Severe-stress net | `>USD 0.00` |
| Last-12-month PF | `>=1.22` |
| Last-6-month PF | `>=1.20` |
| 2023 net | `>0` |
| 2024 net | `>0` |
| 2025 net | `>0` |
| Years with PF `>=1.15` | At least `2` of 2023–2025 |
| MT5 floating-equity DD | `<=min(USD 33.94, locked account cap)` |
| Top-winner removal | Net `>0`, PF `>=1.05` |
| Top-10 winner concentration | `<=35%` of gross profit |
| Top-10 loss concentration | `<=30%` of gross loss |
| Best-month removal PF | `>=1.15` |
| Single-month gross-profit share | `<=25%` |
| Best-session removal PF | `>=1.10` |
| Single-session positive-net share | `<=50%` |
| Rolling-window gates | All thresholds below |
| Weekly block bootstrap | Lower confidence bound `>0` |
| Volatility/trend coverage | All minimum counts below |
| Evidence reconciliation | Zero unexplained differences |

Failure of any Stage 1 gate: `KILL_FAMILY`.

### Rolling gates

Sort by exit time and use starts `0, 10, 20, ...` while a complete window fits.

| Window | Positive share | Median PF | Minimum PF |
|---|---:|---:|---:|
| 100 | `>=65%` | `>=1.15` | `>=0.60` |
| 150 | `>=75%` | `>=1.20` | `>=0.75` |
| 250 | `>=90%` | `>=1.25` | `>=0.90` |

### Weekly block-bootstrap gate

Freeze before running:

- aggregate net P&L by ISO week using realized exit time;
- include zero-trade weeks as zero;
- use circular moving blocks of `4` consecutive weeks;
- `100,000` resamples;
- random seed `20260723`;
- statistic: mean weekly net P&L;
- pass when the one-sided 95% lower bound, the fifth percentile, is strictly `>0`.

### Regime-coverage gates

Freeze regime thresholds from all completed D1 bars in the development interval before scoring reclaim outcomes.

1. Volatility state:
   - completed D1 `ATR(14)/Close`;
   - split into three fixed terciles;
   - minimum `50` reclaim trades in each tercile.

2. Slow-trend state:
   - completed D1 close above versus below completed D1 SMA(200);
   - minimum `75` reclaim trades in each state.

Regime buckets are diagnostics/gates, not entry filters.

### Stage 2 — final historical admission

All Stage 1 gates must remain passed, plus:

| Gate | Threshold |
|---|---:|
| Full-period PF | `>=1.30` |
| Payoff ratio | `>=0.90` |
| DSR | `>=0.95`, only with defensible complete multiplicity input |
| Evidence | Complete and source-bound |
| Prospective status | Not yet claimed |

Passing Stage 2 authorizes freezing one candidate for prospective tester validation. It does not authorize demo/live trading.

### Conditional Bollinger-basis exit route

This route is available only when:

- every Stage 0 and Stage 1 gate passes;
- reclaim PF is at least `1.2100`;
- no recent, stress, annual, concentration, rolling, bootstrap, regime, drawdown, or evidence gate fails;
- final admission is prevented only by:
  - PF below `1.30`; and/or
  - payoff ratio below `0.90`.

The exit test must be one preregistered change. No fixed-R sweep is allowed.

### Prospective boundary

After final source/EX5/preset/INI/history hashes are frozen:

- all data through `2026-07-02` is development;
- intervening data is quarantined;
- prospective requirement is at least `250` trades and `12` completed calendar months, whichever is later;
- no parameter/code change resets or preserves the old prospective label—the clock restarts.

---

## 7. MISSING_EVIDENCE

### Before repair

| Missing evidence | Status | Required disposition |
|---|---|---|
| Exact source used for locked EX5 | Missing from manifest | `REPAIR`; fatal |
| Source-to-EX5 compile chain | Incomplete | `REPAIR`; fatal |
| Compiled input schema | Missing | `REPAIR`; fatal |
| Unknown/ignored INI-key reconciliation | Missing | `REPAIR`; fatal |
| Exact symbol specification | Missing | `REPAIR`; fatal |
| Effective leverage alignment | Conflicting | `REPAIR`; fatal |
| Actual fill/SL/TP reconciliation | Incomplete | `REPAIR`; fatal |
| Stop-component attribution | Missing | `REPAIR`; fatal |
| Stop-cap activation report | Incomplete | `REPAIR`; fatal |
| Full canonical outcome diff | Current comparison too narrow | `REPAIR`; fatal |
| Fill definition by deal | Current episode logic uses `ORDER_SEND_OK` | `REPAIR`; fatal |
| Exit-time annual/month report | Current full audit uses entry time | `REPAIR`; required |
| Native-real-tick coverage | Not established | Annotate before test; required before promotion |
| Server UTC/DST mapping | Missing | Required before session portability claim |
| Complete informal-trial inventory | Not provable | DSR remains not assessable |

### After repair, before intervention

| Required artifact/analysis | Pass requirement |
|---|---|
| V1R source and EX5 | Unique, immutable, hashed |
| Clean compiler evidence | Zero errors/warnings; exact compiler identity |
| Canonical preset/INI | Declared inputs only |
| Effective leverage | `1:50` in INI and report |
| Symbol specification | Complete |
| Baseline MT5 report | Exact frozen run |
| Startup/signal/state/order/deal/trade logs | Complete |
| Baseline parity | Zero unexplained differences |
| Stop and target telemetry | Requested and actual |
| Corrected analytics | Exit-time years/months; fixed sessions |
| Reclaim preregistration | Exact state machine and gates |
| State-machine tests | All edge cases covered |
| Trial registry | Repair entry added |
| Manifest | Covers every artifact |
| Runtime boundary | Tester only |

### After intervention

| Required artifact/analysis | Purpose |
|---|---|
| Reclaim source/EX5/compile hashes | Identity |
| MT5 report and all ledgers | Reconciliation |
| Baseline/reclaim matched diff | Causal attribution |
| Setup/confirmation/expiration ledger | State-machine proof |
| Request/order/deal/position reconciliation | Execution proof |
| Requested/actual SL/TP and fill | Geometry proof |
| Stop component/cap report | Stop-contract proof |
| Base/primary/severe metrics | Cost robustness |
| 6/12-month reports | Recent robustness |
| Exit-time annual/month results | Temporal breadth |
| Fixed session buckets | Session concentration |
| Top winners/losses | Tail concentration |
| Rolling windows | Local stability |
| Weekly block bootstrap | Dependence-aware expectancy |
| Regime coverage | Breadth |
| MAE/MFE | Entry/exit diagnosis |
| Holding time/rollover | Swap and operational diagnosis |
| Daily equity returns | DSR/risk analysis |
| Updated multiplicity inventory | Selection-risk accounting |
| Machine-generated gate table | Final decision |
| Reviewer verdict | `LOCK_FOR_PROSPECTIVE`, `AUTHORIZE_BASIS_EXIT`, or `KILL_FAMILY` |

---

## 8. INVALID_TESTS

Any of the following invalidates the bounded program:

1. Testing another excluded-hour mask.
2. Deleting or suppressing hours `6,7,10,13` from the unmasked baseline.
3. Testing both episode mutex and reclaim and choosing the better result.
4. Changing RSI, Bollinger period/deviation, ATR period/multiple, body fraction, band distance, stop floor, stop ceiling, or RR.
5. Adding a trend, session, volatility, candle-color, close-location, or multi-bar filter.
6. Allowing a multi-bar reclaim window.
7. Testing equality as both pass and fail.
8. Testing reclaim buffers such as one point, one pip, or ATR fractions.
9. Replacing the pending-setup rule after seeing results.
10. Using bars ending at `t` and bars ending at `t+1` as competing stop variants.
11. Using ATR from `t` and `t+1` as competing variants.
12. Changing quote-based TP to fill-based TP during the reclaim experiment.
13. Sweeping fixed targets or Bollinger-basis exit variants.
14. Truncating stops at 700 points instead of rejecting.
15. Retrying failed requests during `t+2`.
16. Waiting for an open position to close before executing an old confirmation.
17. Adding market-close or rollover time exclusions before reclaim.
18. Removing the three historical failed attempts.
19. Treating `CTrade::Buy()==true` as proof of a fill without deal reconciliation.
20. Incrementing filled-entry counts for requests with no deal.
21. Reusing the V1 ID after changing body fraction, startup behavior, source, or EX5.
22. Retaining unknown INI keys without proving whether they are active.
23. Compiling over an existing EX5 without a clean-output proof.
24. Hashing the EX5 and compiler log while omitting the source.
25. Accepting only trade-ledger parity while signal/order/deal ledgers differ.
26. Calling exit-time/net equality an “exact full outcome” match.
27. Mixing entry-time and exit-time calendar attribution after seeing which is better.
28. Changing rolling-window stride, bootstrap block length, seed, or regime definitions after results.
29. Calling `Model=0` and `99%` proof of complete native real-tick history.
30. Guessing a DSR trial count that produces a pass.
31. Treating any part of 2022–2026 as an untouched holdout.
32. Using data accrued before final hashes as prospective.
33. Using XAUUSD portfolio results to rescue EURUSD.
34. Increasing lot size to improve dollar P&L.
35. Attaching the EA to a chart or placing demo/live orders.
36. Authorizing a basis-exit test after reclaim fails a stress or recent-window gate.
37. Running another rescue test after reclaim or basis exit fails.
38. Promoting from retrospective history alone.

---

## 9. NEXT_SINGLE_ACTION

Create and freeze the candidate-specific corrected baseline:

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT`

Bind its exact MQ5 source to its clean-compiled EX5, align the INI and report to effective leverage `1:50`, add only the fail-closed startup latch and required non-behavioral telemetry, and rerun the exact MT5 baseline to prove zero-unexplained canonical parity with all `1,145` trades and `USD 77.26`.

Do not code or run the reclaim candidate until that parity gate passes.