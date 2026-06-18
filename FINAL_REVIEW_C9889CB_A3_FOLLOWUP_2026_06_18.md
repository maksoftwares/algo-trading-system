# Final Review — Commit `c9889cb` / A3 Follow-Up Evidence and Runtime Decision

**Repository:** `maksoftwares/algo-trading-system`
**Commit:** `c9889cb2e7585be8c64cdea6800fb05726af3f52`
**Reviewed against:** `d5dd2de6508a812424b12eb248b6409fcf689968`
**Review date:** 2026-06-18
**Scope:** A3 account `1033669`, follow-up evidence packet, six Phase 1 test failures, A3 lane governance, duplicate-family risk, profit-lock manager, and next runtime decision.

---

## 1. Executive verdict

```text
Commit c9889cb as an evidence/reporting follow-up:     CONDITIONAL GO
A3 broker-action runtime as currently configured:     NO-GO
Magic 933200 plain lane:                               KEEP STOPPED
Magic 933300 improved lane:                            PAUSE BROKER ACTION NOW
Magic 933400 Tier1 compat lane:                        PAUSE / RETURN TO DRY-RUN
Profit-lock manager:                                   KEEP ATTACHED ONLY IN DRY-RUN, OR DETACH
Further A3 signal changes:                             SHADOW-FIRST ONLY
Emergency risk-reducing pause:                         GO
New risk-increasing/runtime feature deployment:        NO-GO
Canonical Phase 2 / live / real capital:               ABSOLUTE NO-GO
```

The new evidence packet is sufficient to make a stronger decision than the prior review. It does **not** support keeping both active entry lanes trading.

The key evidence is:

```text
A3 closed XAUUSD trades: 23
Wins / losses:         1 / 22
Net PnL:               -758.79 AED
Duplicate events:      5
Profit-lock actions:   0
```

Per magic:

```text
933200: 14 trades, 0 wins, 14 losses, -510.44 AED, stopped
933300:  8 trades, 1 tiny win, 7 losses, -156.04 AED, still active
933400:  1 trade, 0 wins, 1 loss,       -92.31 AED, still active
```

The improved lane has already crossed the previously proposed emergency pause condition of five consecutive losses: it has **seven consecutive losses**. The Tier1 compatibility lane has only one trade, but that trade was a same-minute, same-direction duplicate with the failed plain lane and lost `-92.31 AED`. It has not earned broker-action continuation.

---

## 2. Review boundary

This is a static review of committed GitHub artifacts and source. The commit has no associated GitHub Actions workflow run. The local pytest output is committed, which is useful, but it is not independent CI evidence.

The diff from `d5dd2de` to `c9889cb` contains:

- review documents;
- direct-history and attribution reports;
- test-output and failure-triage artifacts;
- status-summary changes;
- `agent.md` changes;
- two Python report-generation scripts.

It does **not** contain:

- MQL5 entry-EA changes;
- MQL5 exit-manager changes;
- `.set` or profile changes;
- chart changes;
- order or position changes;
- MT5 runtime deployment changes.

Therefore the expected answer is confirmed:

```text
Commit c9889cb changed no runtime trading behavior.
It is evidence/reporting-only.
```

---

## 3. Did the follow-up fully close the prior review blockers?

### 3.1 Closure matrix

| Prior blocker | Status in `c9889cb` | Review |
|---|---|---|
| Exact six pytest failures unavailable | **Evidence closed** | Full local pytest output and named triage are committed. |
| Status summaries stale versus old branch | **Partially closed** | Branch is now `main`, and A3 evidence is included. Commit field still references `d5dd2de`, not `c9889cb`. |
| `status.html` needed refresh | **Not closed** | `status.html` has the same Git blob SHA in `d5dd2de` and `c9889cb`; it was not changed by this commit. |
| Fresh A3 direct history missing | **Closed** | Direct broker-history export is committed. |
| Per-magic attribution missing | **Closed** | `933200`, `933300`, and `933400` are separately attributed. |
| Duplicate-family evidence missing | **Closed** | Five same-minute/same-direction duplicate events are listed. |
| Profit-lock status/action evidence missing | **Closed** | Manager startup and zero-action status are documented. |
| Safety-audit taxonomy too broad | **Not fixed** | It is triaged, but code/tests remain failing. |
| Acceptance/status taxonomy drift | **Not fixed** | Three tests still fail on `PENDING` versus `FAIL`. |
| EURUSD lot contract drift | **Not fixed** | Source/test contract remains unresolved. |
| Stale Phase 2 preflight artifact | **Not fixed** | The stale artifact remains a failing test. |
| Per-magic hard pause rules | **Not implemented** | The new evidence shows they are needed immediately. |

### 3.2 Overall blocker verdict

The packet fully closes the **evidence gap**, but not the **code/governance gap**.

Correct characterization:

```text
Evidence packet:                  materially complete
Test suite:                       not clean
Status dashboard:                not fully refreshed
Runtime performance:             failed
Further broker-action changes:    blocked
```

---

## 4. A3 evidence quality

### 4.1 Direct-history methodology

The new generator:

1. initializes the A3 portable terminal;
2. reads direct broker deals for account `1033669`;
3. filters to `XAUUSD` and magics `933200`, `933300`, and `933400`;
4. groups deals by position ID;
5. requires both entry and exit deals;
6. includes profit, commission, swap, and fee in net PnL;
7. reads current open positions and orders;
8. reads chart profile inputs for current runtime-state attribution.

This is sufficient for the immediate A3 lane decision.

### 4.2 Limitation

The report status `PASS` means the report was generated successfully. It must **not** be interpreted as a passing trading result.

The current fields are semantically misleading:

```text
A3_DIRECT_HISTORY status = PASS
A3_PER_MAGIC_ATTRIBUTION status = PASS
A3_REVIEW_FOLLOWUP_STATUS status = PASS
status_summary A3 review follow-up = PASS
```

The trading result is plainly a failure.

Recommended schema:

```json
{
  "artifact_integrity_status": "PASS",
  "runtime_performance_status": "FAIL",
  "runtime_authorization_recommendation": "PAUSE_ACTIVE_ENTRY_LANES"
}
```

Do not use one `PASS` field for both artifact generation and strategy health.

---

## 5. A3 account findings

### 5.1 Account-level result

Window:

```text
2026-06-16 00:00:00 UTC through 2026-06-18 report generation
```

Result:

```text
Closed trades: 23
Wins:           1
Losses:         22
Win rate:       4.35%
Net PnL:        -758.79 AED
Account balance at report: 3237.98 AED
Starting operational balance referenced: approximately 4000 AED
```

This is not normal small-sample noise that should be ignored while collecting data. It is a severe loss cluster requiring containment.

### 5.2 Duplicate-family result

Five same-minute, same-direction events were detected:

```text
933200 + 933400: 1 duplicate event
933200 + 933300: 4 duplicate events
Combined PnL across paired positions: -334.23 AED
```

This does not mean all `-334.23 AED` was avoidable, because one trade per event might still have been taken. It does prove that account risk was repeatedly doubled by correlated same-family entries.

The current A3 base applies an exposure cap only by exact magic. It does not prevent another A3 breakout-family magic from opening the same symbol/direction signal.

This is a real design gap and more important than any of the six static-test failures.

---

## 6. Per-lane recommendation

## 6.1 Magic `933200` — A3 plain

### Evidence

```text
Closed trades:        14
Wins / losses:        0 / 14
Net PnL:              -510.44 AED
Profit factor:        0.00
Consecutive losses:   14
Current dry-run:      true
Broker action:        false
```

### Verdict

```text
KEEP STOPPED
```

Stopping it was correct.

Do not reactivate this exact lane. Any future replacement must be a new version/hypothesis with a new magic and shadow-first evidence.

---

## 6.2 Magic `933300` — A3 improved

### Evidence

```text
Closed trades:        8
Wins / losses:        1 / 7
Win rate:             12.50%
Net PnL:              -156.04 AED
Profit factor:        effectively zero
Consecutive losses:   7
Current dry-run:      false
Broker action:        true
```

The one win was only `+0.26 AED`, while average loss was `-22.33 AED`.

The lane has already exceeded the prior proposed pause trigger of five consecutive losses.

### Why its current mitigations are insufficient

The active trend guard:

```text
blocks if H1 OR H4 is explicitly opposite;
allows a trade when one or both timeframes are neutral.
```

That is a permissive trend filter, not strong multi-timeframe alignment.

Its partial-profit feature is functionally unavailable at a fixed `0.01` lot when broker minimum/step is `0.01`. The source explicitly skips partial closing when it cannot leave the minimum runner. Therefore "partial enabled" does not mean partial exits are actually protecting these trades.

Breakeven can help only after a trade reaches the configured favorable-R threshold. It cannot repair low-quality entries that go directly to SL.

### Verdict

```text
PAUSE BROKER ACTION NOW
RETURN TO SHADOW / DRY-RUN
```

Do not leave `933300` active merely to obtain a larger sample. The evidence already triggered the predeclared emergency criterion.

---

## 6.3 Magic `933400` — A3 Tier1 compatibility

### Evidence

```text
Closed trades:        1
Wins / losses:        0 / 1
Net PnL:              -92.31 AED
Current dry-run:      false
Broker action:        true
```

Its only trade:

- co-fired with `933200`;
- had the same direction and same entry minute;
- produced a combined duplicate-event loss of `-184.95 AED`.

The lane has useful design protections:

- A2-style session gate;
- XAU stop-distance floor;
- separate magic/comment/log namespace;
- fixed `0.01` lot;
- demo account and symbol scope.

However:

- trend guard is shadow-only, not active;
- owner authorization skipped the reviewer's observer-first recommendation;
- the first executed trade does not provide positive validation;
- cross-lane duplicate prevention was absent.

### Verdict

```text
PAUSE BROKER ACTION
RETURN TO THE OBSERVER/DRY-RUN STEP THAT WAS ORIGINALLY RECOMMENDED
```

This is not a statistical rejection based on one trade. It is a governance and risk-containment decision: the lane has not earned continued execution while the account is producing a 22-loss cluster.

---

## 7. Profit-lock manager review

### 7.1 Technical safety

The manager is narrowly scoped:

- account allowlist `1033669`;
- demo-server marker;
- symbol `XAUUSD`;
- managed magics `933200,933400`;
- hard exclusion of `933300`;
- kill-switch support;
- only `TRADE_ACTION_SLTP`;
- never widens an SL;
- checks broker stop/freeze distances;
- preserves the existing TP;
- does not open trades.

Technically, the design is reasonably safe for its narrow purpose.

### 7.2 Evidence and usefulness

Current result:

```text
Managed closed trades in window: 15
Open managed positions:          0
SL moves sent:                   0
SL moves failed:                 0
Dry-run would-move rows:         0
```

The manager did not act because no managed trade reached `+1.25R`.

It cannot solve the current problem:

```text
The primary A3 failure is low-quality entries going to SL.
The manager only helps trades that first reach substantial profit.
```

The dynamic-profit-lock proposal originally recommended a shadow-first forward test. The manager was later armed before such forward evidence existed.

### Recommendation

If `933300` and `933400` are paused as recommended:

```text
Set InpManageActionAllowed=false and InpDryRunOnly=true,
or detach the manager after preserving logs.
```

It may remain attached in dry-run to generate evidence, but it should not remain armed when there are no active managed entry lanes and no open managed positions.

If `933400` is later reauthorized, the manager may be rearmed under a new owner packet after shadow validation.

Do not add `933300` to the manager while `933300` retains internal breakeven management. Multiple independent SL managers on one magic would create race and attribution risk.

---

## 8. Six Phase 1 test failures

## 8.1 Failure classification

| Failure | Classification | Actual EA code defect? | Required before more A3 deployment? |
|---|---|---:|---:|
| Acceptance expected `PENDING`, got `FAIL` | Stale test / acceptance taxonomy | No | Yes, before claiming clean governance |
| Stale-runtime acceptance expected `PENDING`, got `FAIL` | Stale test / acceptance taxonomy | No | Yes |
| Safety audit finds broker-action terms | Governance taxonomy too broad | Not by itself | Yes |
| Status-summary acceptance expected `PENDING`, got `FAIL` | Derived stale test contract | No | Yes |
| EURUSD fixed lot expected `0.05`, source uses `0.01` | Real source/test contract drift | Unresolved | Resolve before next global executor release |
| Phase 2 preflight JSON stale | Stale artifact | No | Regenerate before Phase 2 claims |

### 8.2 Are any confirmed A3 code defects?

The six failures do **not** prove an A3 entry/exit code defect.

However, independent of those tests, the evidence reveals a real A3 design defect:

```text
Cross-lane same-family duplicate blocking is not effective across
933200 / 933300 / 933400.
```

The current A3 base counts exposure by exact magic only. It is not an account-wide family mutex.

### 8.3 What must be fixed before further A3 runtime changes?

An emergency pause is risk-reducing and should happen immediately; it should not wait for tests.

Before any reactivation or risk-increasing runtime change:

1. scope the Phase 1 safety audit by artifact domain;
2. reconcile `FAIL` versus `PENDING` acceptance taxonomy;
3. make the full Phase 1 test suite pass;
4. regenerate the stale Phase 2 preflight artifact;
5. resolve and document the EURUSD lot contract drift;
6. implement and test an atomic A3 family mutex;
7. produce a new shadow-only signal-quality hypothesis and evidence packet.

---

## 9. Status and governance artifacts

### 9.1 What improved

- `status_summary.md/json` now use branch `main`;
- A3 direct-history metrics are included;
- `agent.md` accurately lists the new packet and per-magic results;
- the six test failures are named and captured.

### 9.2 Remaining misleading/stale items

#### `status.html`

`status.html` has the same Git blob SHA in `d5dd2de` and `c9889cb`.

Therefore the response statement that `status.html` was regenerated/updated is not supported by the committed diff.

**Fix:** regenerate and commit `status.html`, or remove the claim.

#### Commit field in compact summaries

`status_summary.md/json` identify commit `d5dd2de`, while the packet is committed in `c9889cb`.

A file cannot trivially contain the final hash of the commit that contains it without an amend/rebuild cycle. Fix the schema rather than creating an endless one-commit lag:

```text
evidence_base_commit: d5dd2de...
artifact_commit: populated by CI/release metadata, or omitted
```

Do not label the base commit simply as `Commit`.

#### A3 `PASS` semantics

The packet reports `PASS` for successful evidence generation while runtime performance is catastrophic.

Split artifact integrity from trading status.

Recommended:

```text
artifact_integrity_status = PASS
runtime_performance_status = FAIL
lane_authorization_status = PAUSE_REQUIRED
```

#### Test triage

`PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md` is accurate as a triage, but it remains `REVIEW_REQUIRED`. It is not a closure artifact until the fixes are implemented and pytest is green.

---

## 10. Signal-quality improvements — shadow-first plan

Do not patch the active executors in place. Create new versioned shadow candidates.

## 10.1 Cross-lane atomic family mutex — highest priority

Required behavior:

```text
Key:
account + symbol + family + direction + M5 bar timestamp

All A3 breakout lanes use the same key.

Claim:
atomic GlobalVariableSetOnCondition immediately before OrderSend.

Priority:
one deterministic lane owner, preferably the most restrictive approved version.

Release:
release on failed order send;
retain through the bar after successful send;
do not allow same-family co-fire.
```

Add tests for:

- same second;
- same M5 bar;
- two terminals/processes;
- order-send failure;
- restart;
- opposite directions;
- stale lock expiry.

The simplest and safest near-term policy is even stronger:

```text
Only one A3 breakout-family lane may be broker-action enabled at a time.
```

## 10.2 Stronger trend alignment

Current improved logic blocks an explicitly opposite H1 or H4 trend, but allows neutral states.

Shadow-test a new rule:

```text
H1 trend must equal signal direction
AND H4 trend must equal signal direction
AND D1 bias must not oppose
AND M15/H1 EMA slope must not oppose
```

Use the existing trend-guarded observer evidence. Do not invent thresholds from these 23 trades.

## 10.3 Stronger retest confirmation

Pre-register a new retest-quality hypothesis. Candidate conditions:

- first retest only;
- confirmation candle closes beyond the broken level;
- confirmation close in directional top/bottom quartile;
- minimum body-to-range ratio;
- maximum opposite wick;
- maximum retest penetration in ATR;
- maximum bars between break, retest, and confirmation;
- entry only after confirmation high/low is actually broken.

Test these as a new version, not as ad-hoc rescue filters.

## 10.4 Session filtering

`933300` has no active session gate. Its losing trades occurred across broad hours.

`933400` has a 12–15 server-hour gate, but the first trade inside that gate lost. Therefore session filtering is useful but insufficient.

Shadow-test:

- A2-compatible session;
- session + active trend alignment;
- session + stronger retest confirmation.

Do not conclude from one `933400` trade that the 12–15 gate is invalid.

## 10.5 Cost and stop quality

Keep:

- XAU minimum stop floor;
- spread cap;
- cost-R cap.

But signal quality must be improved before further execution. Wider stops cannot rescue entries with no directional edge.

---

## 11. Is a daily loss breaker necessary?

It is **necessary as containment**, but it is not the main strategy fix.

A breaker:

- does not improve expectancy;
- does not turn bad entries into good entries;
- prevents a failed configuration from compounding losses during discovery.

Before any A3 broker-action reactivation, pre-register:

```text
Per-lane:
- consecutive-loss pause;
- maximum daily -R;
- maximum daily closed loss.

Account:
- maximum A3 daily closed loss;
- maximum A3 open family exposure;
- block new entries after trigger;
- manual reset or next-day reset rule.
```

Do not optimize the threshold on the current 23 trades. Choose a conservative operational bound, document it before the next forward window, and treat it as a kill switch rather than an edge filter.

---

## 12. Next safest action

Execute a risk-reducing maintenance window:

```text
1. Keep 933200 dry-run=true / broker_action=false.
2. Set 933300 dry-run=true / broker_action=false.
3. Set 933400 dry-run=true / broker_action=false.
4. Set profit-lock manager manage_action=false and dry_run=true,
   or detach it after confirming no managed open positions.
5. Back up the A3 profile before the change.
6. Reconcile chart inputs after restart.
7. Confirm zero open A3 positions/orders.
8. Commit an A3 pause-applied report.
```

Then, repo-side only:

```text
9. Fix the six-test taxonomy/contracts and obtain a green suite.
10. Implement a shadow-only account-wide family mutex.
11. Author a versioned signal-quality hypothesis.
12. Run broker-joined shadow evidence.
13. Permit only one A3 entry lane to return to demo broker action
    after a separate review and owner authorization.
```

---

## 13. Final go/no-go table

| Item | Verdict |
|---|---|
| Accept `c9889cb` evidence packet | **CONDITIONAL GO** |
| Treat prior blockers as fully closed | **NO** |
| Keep `933200` stopped | **GO** |
| Keep `933300` broker-action active | **NO-GO** |
| Keep `933400` broker-action active | **NO-GO** |
| Keep profit-lock manager armed | **NO-GO** |
| Keep profit-lock manager attached dry-run | **GO** |
| Emergency A3 pause maintenance | **GO** |
| Signal-quality research shadow-only | **GO** |
| Daily loss breaker as containment | **REQUIRED BEFORE REACTIVATION** |
| Further risk-increasing runtime changes | **NO-GO** |
| Canonical Phase 2 | **NO-GO** |
| Live / real capital | **ABSOLUTE NO-GO** |

---

## 14. Bottom line

The follow-up packet did its job: it converted uncertainty into evidence.

That evidence does **not** justify continued broker action.

The safest and most defensible conclusion is:

```text
933200 stays stopped.
933300 is paused because it has seven consecutive losses and near-zero PF.
933400 returns to dry-run because its only trade was a duplicate loss and
observer-first validation was skipped.
The profit-lock manager is disarmed because it cannot fix entries that never
reach its +1.25R trigger.
Signal improvements proceed shadow-first, with an account-wide family mutex
as the first engineering fix.
```
