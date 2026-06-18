# Final Review — Commit `b7ea982` / A3 Emergency Pause and Repair Implementation Plan

**Repository:** `maksoftwares/algo-trading-system`  
**Commit reviewed:** `b7ea9823ff6c6a78c05a01034498eaeeaccc2d98`  
**Base commit:** `c9889cb2e7585be8c64cdea6800fb05726af3f52`  
**Review date:** 2026-06-18  
**Scope:** A3 account `1033669`, emergency pause, remaining Phase 1 failures, A3 signal-quality research, account-wide duplicate-family prevention, containment, reactivation gates, and status/report schema.

---

## 1. Executive verdict

```text
Commit b7ea982:                                  GO
Emergency A3 pause:                              PASS / KEEP ACTIVE
933200 plain lane:                               KEEP STOPPED
933300 improved lane:                            KEEP PAUSED
933400 Tier1 compatibility lane:                 KEEP PAUSED
Profit-lock manager:                             KEEP DRY-RUN / DISARMED
Further A3 broker-action changes:                NO-GO
Shadow-only A3 repair research:                  GO
Test/governance cleanup:                         GO
Canonical Phase 2:                               NO-GO
Live / real capital:                             ABSOLUTE NO-GO
```

The emergency pause was the correct response to the A3 loss cluster.

The committed evidence shows:

- no A3 XAUUSD positions before the maintenance operation;
- no A3 pending orders before the operation;
- no A3 XAUUSD positions or orders after the operation;
- no trade closed by the pause;
- no order sent by the pause;
- `933200` remained stopped;
- `933300` was changed to dry-run / broker-action-off;
- `933400` was changed to dry-run / broker-action-off;
- the profit-lock manager was changed to dry-run / manage-action-off;
- the terminal profile was backed up before editing;
- the terminal was closed before profile changes and relaunched afterward;
- startup logs confirmed the paused inputs.

The pause must remain in force until a new, pre-registered shadow candidate completes the reactivation gates in this document.

---

## 2. What `b7ea982` changed

The commit adds or updates:

- the prior `c9889cb` final review;
- the A3 pause application script;
- the A3 pause evidence report;
- direct-history and per-magic reports after the pause;
- project status summary JSON/Markdown;
- the large status dashboard;
- `agent.md`;
- post-pause pytest output;
- updated test-failure triage;
- report/status generator changes.

It does **not** change:

- A3 MQL5 entry logic;
- A3 MQL5 signal rules;
- A3 MQL5 exit logic;
- canonical Phase 2 authorization;
- live or real-capital authorization.

The runtime change was limited to chart input/profile state in the A3 portable demo terminal.

---

## 3. Review of the pause implementation

## 3.1 Correct behavior

The script correctly targets only:

```text
Account3BreakoutImprovedExecutor
Account3BreakoutTier1CompatExecutor
Account3ProfitLockExitManager
```

It requires the plain `933200` chart to already be stopped.

It updates:

```text
933300:
  InpDryRunOnly=true
  InpBrokerActionAllowed=false

933400:
  InpDryRunOnly=true
  InpBrokerActionAllowed=false

Profit-lock manager:
  InpDryRunOnly=true
  InpManageActionAllowed=false
```

It backs up the full profile before writing.

It captures before/after broker exposure and startup-log evidence.

## 3.2 Script hardening required before reuse

The current run was safe because exposure was zero. The reusable script still needs additional fail-closed behavior.

### Required fix A — abort on open exposure

The script currently records a failing before-exposure check but does not abort before editing the profile.

Before any future pause operation:

```text
IF before_broker.status != PASS
THEN abort before closing/editing the terminal.
```

Only an explicit separate `--allow-open-exposure` recovery mode may override this, and that mode must:

- leave the exit manager armed until positions close, or
- have a separately approved position-management procedure.

Default behavior must remain fail-closed.

### Required fix B — verify terminal fully stopped

After graceful close/forced stop:

```text
verify no process exists with the target executable path
before backup/profile write.
```

Return failure if the process remains alive.

### Required fix C — hash all non-target charts

Capture SHA256 for every chart before and after.

Pass only if:

```text
all non-target chart hashes are unchanged
and only the expected input keys changed in target charts.
```

### Required fix D — idempotence

A second execution against an already-paused profile should:

- make zero profile changes;
- report `ALREADY_PAUSED`;
- not produce misleading `changed_only_expected_pause_targets=PASS` wording.

### Required tests

Create:

```text
tests/test_apply_a3_emergency_pause.py
```

Cover:

1. expected three target charts only;
2. plain lane already stopped;
3. missing target fails;
4. open position/order aborts;
5. non-target hash unchanged;
6. already-paused idempotence;
7. startup log mismatch fails;
8. backup required;
9. terminal-not-stopped fails;
10. no launch mode is clearly reported.

---

## 4. Must-fix blockers

## Blocker 1 — Phase 1 suite remains red

Current result:

```text
399 passed
6 failed
```

Do not claim Phase 1 test closure until all six pass.

## Blocker 2 — safety audit taxonomy is wrong for the current repository shape

The canonical dry-run shell and passive observers must remain strictly broker-action-free.

The repository also contains separately governed experimental demo executors and a stop-only manager.

The audit must distinguish these domains rather than:

- scanning everything as canonical, or
- broadly ignoring files by name.

## Blocker 3 — status summary still mixes historical authorization with current runtime

`status_summary.json` contains a Tier1 lane object that says:

```text
dry_run=false
broker_action_allowed=true
```

while the effective runtime state is:

```text
A3_ENTRY_LANES_PAUSED
dry_run=true
broker_action_allowed=false
```

This is confusing even though the later fields state the pause.

Split:

```text
historical_owner_authorization
current_runtime_state
effective_runtime_authorization
```

Current runtime must be the prominent field.

## Blocker 4 — account-wide family duplicate prevention does not yet exist for A3

The evidence contains five same-minute/same-direction duplicate events.

The current A3 base limits exposure by exact magic. It does not enforce one account-wide breakout-family claim across `933200`, `933300`, and `933400`.

No A3 entry lane may be reactivated before the family mutex passes tests and shadow evidence.

## Blocker 5 — no locked A3 signal-quality repair hypothesis yet

Do not modify `933300` or `933400` in place.

Author and hash-lock a new hypothesis before implementing the repair observer.

## Blocker 6 — no runtime containment contract for reactivation

A daily breaker and per-lane suspension rules are required before demo broker action can resume.

They are containment, not the source of edge.

---

## 5. Ordered implementation plan

## Stage 0 — freeze runtime

Keep:

```text
933200: dry-run / broker-action-off
933300: dry-run / broker-action-off
933400: dry-run / broker-action-off
profit-lock: dry-run / manage-action-off
```

No new A3 chart, order, source deploy, or profile change during Stages 1–4.

---

## Stage 1 — make the test suite green

### 1.1 Split canonical safety from experimental-governance safety

Change:

```text
scripts/audit_phase1_safety.py
```

Add:

```python
audit_canonical_phase1_sources(root)
audit_experimental_demo_sources(root)
audit_phase1_tree(root)  # aggregate actual violations only
```

### Canonical policy

Explicitly include the canonical dry-run shell, canonical Phase 1 includes, and passive observer sources.

For canonical files, forbid:

```text
OrderSend
OrderSendAsync
CTrade
trade.Buy
trade.Sell
TRADE_ACTION_DEAL
TRADE_ACTION_SLTP
position modification/close actions
```

### Experimental policy

Use an explicit per-file action policy, not a blanket filename skip.

Example:

```text
Phase2ExperimentalDemoExecutor.mq5
  allowed: TRADE_ACTION_DEAL
  required: demo-server block, login allowlist, kill switch,
            authorization token, cost-suspension acknowledgement,
            broker-action default false

Phase2ExperimentalDemoRepairExecutor.mq5
  allowed: TRADE_ACTION_DEAL
  required: same guard family

Phase2WeaknessBreakoutRetestExecutor.mq5
  allowed: TRADE_ACTION_DEAL
  required: same guard family

A3BreakoutExecutorBase.mqh
  allowed: TRADE_ACTION_DEAL and TRADE_ACTION_SLTP
  required: demo-server block, login 1033669 allowlist, kill switch,
            dry-run default true, broker-action default false,
            exact-magic lock

Account3ProfitLockExitManager.mq5
  allowed: TRADE_ACTION_SLTP only
  forbidden: TRADE_ACTION_DEAL
  required: account 1033669, XAUUSD, managed-magic allowlist,
            hard exclusion of 933300, kill switch,
            dry-run default true, manage-action default false
```

The audit should fail if:

- a new broker-action file is not in the policy;
- an allowed file uses an unauthorized trade action;
- a required scope guard disappears;
- a passive file gains any broker action.

### 1.2 Keep acceptance semantics

Do **not** change `FAIL` into `PENDING` to make tests pass.

The three acceptance/status tests should return to `PENDING` automatically when the false-positive safety failure is removed.

Keep:

```text
FAIL    = actual broken safety/log/runtime gate
PENDING = incomplete wall-clock/evidence gate
PASS    = complete
```

### 1.3 Resolve EURUSD fixed-lot contract

Current source default:

```text
InpEURUSDFixedLot = 0.01
```

Current test expects:

```text
InpEURUSDFixedLot = 0.05
```

Recommended decision:

```text
Keep source at the safer 0.01 default.
Update the static test and governance docs to 0.01.
```

Before doing that, search all committed presets and owner packets. If an explicit owner-approved `0.05` contract exists, resolve the conflict in an owner decision record rather than silently editing the test.

The source, tests, presets, README, deployment docs, and status reports must all agree.

### 1.4 Regenerate stale preflight

After safety taxonomy is fixed:

```text
regenerate PHASE2_DEMO_PREFLIGHT.json
regenerate matching Markdown
run transition artifact verifier
commit both artifacts
```

### 1.5 Required tests

Add:

```text
tests/test_phase1_safety_domains.py
tests/test_a3_broker_action_policy.py
tests/test_profit_lock_action_scope.py
```

Verify:

- passive files fail if broker-action code is injected;
- profit-lock fails if `TRADE_ACTION_DEAL` appears;
- A3 base fails if demo/login/kill/default locks disappear;
- unknown broker-action source fails;
- acceptance incomplete-soak fixture returns `PENDING`;
- stale runtime fixture returns `PENDING` or `WARN` as specified, not `PASS`;
- real safety violation returns `FAIL`.

Exit criterion:

```text
405 passed, 0 failed
```

The exact total may increase with new tests, but failures must be zero.

---

## Stage 2 — fix status/report schema

Move to:

```text
project_status_summary_v2
```

Required A3 fields:

```json
{
  "artifact_integrity_status": "PASS",
  "runtime_performance_status": "FAIL",
  "historical_owner_authorization": {
    "933400_demo_broker_action": "APPROVED_2026_06_17"
  },
  "current_runtime_state": {
    "933200": "PAUSED",
    "933300": "PAUSED",
    "933400": "PAUSED",
    "profit_lock": "DRY_RUN_DISARMED",
    "verified_at_utc": "...",
    "open_positions": 0,
    "pending_orders": 0
  },
  "effective_runtime_authorization": "A3_ENTRY_LANES_PAUSED",
  "test_suite_status": {
    "passed": 399,
    "failed": 6,
    "status": "FAIL"
  },
  "family_mutex_status": "NOT_IMPLEMENTED",
  "containment_status": "NOT_IMPLEMENTED",
  "shadow_hypothesis_status": "NOT_REGISTERED",
  "reactivation_gate_status": "BLOCKED"
}
```

Also include:

```text
evidence_window_start_utc
evidence_window_end_utc
runtime_snapshot_at_utc
artifact_generation_base_commit
artifact_commit_or_release_id
source_runtime_parity_status
next_allowed_transition
```

Update:

```text
scripts/generate_project_status_summary.py
scripts/generate_project_status_page.py
status_summary.json
status_summary.md
status.html
tests/test_phase1_status_summary.py
```

---

## Stage 3 — pre-register A3 signal-quality hypotheses

Create:

```text
docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_xx.md
outputs/manifests/A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json
```

Do not inspect forward results and then change the rules.

### 3.1 Baseline invariants

All candidates use:

```text
Symbol: XAUUSD
Decision timeframe: M5
Entry family: breakout-retest
Reward target: 1.50R
Stop floor:
  max(raw stop,
      broker stops level + 5 points,
      3 x current spread,
      300 XAU points)
Measured spread cap: 75 points
Post-floor estimated cost_R: <= 0.15R
Session:
  Dubai 16:00–19:59 using TimeGMT()+240 minutes
One virtual family position at a time
No real OrderSend
```

Log broker-server hour in parallel and verify it maps to the pre-registered Dubai window.

### 3.2 Primary promotion candidate — `A3_SQ_COMBINED_V1`

This is the **only promotion-eligible** candidate in this research round.

It combines the strict MTF rule and strict retest rule below.

### 3.3 Diagnostic ablation A — `A3_SQ_MTF_ONLY_V1`

Use the baseline entry/retest logic plus strict MTF alignment.

Long requires all:

```text
D1 close[1] > D1 EMA20[1] > D1 EMA50[1]

H1 EMA20[1] - H1 EMA20[4] >= +50 XAU points

M15 EMA20[1] - M15 EMA20[4] >= +50 XAU points
```

Short requires all mirrored:

```text
D1 close[1] < D1 EMA20[1] < D1 EMA50[1]

H1 EMA20[1] - H1 EMA20[4] <= -50 XAU points

M15 EMA20[1] - M15 EMA20[4] <= -50 XAU points
```

Rules:

```text
completed bars only
any unavailable indicator = block
MIXED D1 bias = block
neutral slope = block
no per-direction exceptions
```

### 3.4 Diagnostic ablation B — `A3_SQ_RETEST_ONLY_V1`

Use baseline session/cost logic plus:

```text
Break close beyond level >= 0.30 x M5 ATR14

First retest only

Retest occurs 1–5 completed M5 bars after break

Retest penetration beyond level <= 0.15 x M5 ATR14

Retest closes back on breakout side by >= 0.05 x M5 ATR14

Confirmation candle body/range >= 0.60

Long confirmation close location:
  (close-low)/(high-low) >= 0.80

Short confirmation close location:
  (close-low)/(high-low) <= 0.20

Opposite wick <= 0.25 x candle range

Long confirmation close > retest high

Short confirmation close < retest low

Invalidating close through the level before confirmation = reject
```

### 3.5 Multiplicity rule

```text
A3_SQ_COMBINED_V1 is primary.
MTF_ONLY and RETEST_ONLY are explanatory diagnostics.
Do not promote an ablation if the primary fails.
Do not change thresholds during the forward window.
```

### 3.6 Priority order

```text
1. Family mutex engineering
2. Combined MTF + retest primary shadow candidate
3. MTF-only diagnostic
4. Retest-only diagnostic
5. Session stratification reporting
6. Cost/stop reporting
```

Session and cost are baseline safety invariants, not parameters to optimize in this round.

Do not repurpose the existing weak-family impulse-veto thresholds for the breakout family without a new, separately locked hypothesis.

---

## Stage 4 — implement the shadow-only research lane

Create a new source; do not edit the paused executors.

Suggested files:

```text
mt5/Experts/Account3SignalQualityShadowObserver.mq5
mt5/Include/A3SignalQualityPolicy.mqh
mt5/Include/A3FamilyMutex.mqh
mt5/Presets/Account3SignalQualityShadowObserver.safe_xauusd.set
docs/A3_SIGNAL_QUALITY_SHADOW_OBSERVER.md
```

Requirements:

```text
InpDryRunOnly=true hard lock
no OrderSend
no CTrade
no SL/TP modification
demo server only
account 1033669 only
XAUUSD only
separate logs
hypothesis hash/version in every row
all candidate decisions logged on the same underlying signal
```

### Tick-level virtual execution

Avoid using the quarantined bar replay as promotion evidence.

Implement an in-terminal virtual position state machine:

```text
virtual long entry = observed ask on first eligible tick after signal
virtual short entry = observed bid on first eligible tick after signal
SL/TP use baseline post-floor geometry
evaluate on every tick
close on first actual tick crossing SL or TP
include measured spread
log virtual fill, MFE, MAE, exit, net R, and costs
one virtual position per candidate
```

This is still shadow evidence, but it avoids same-bar OHLC sequencing ambiguity.

---

## Stage 5 — implement the account-wide A3 family mutex

## 5.1 Scope

Key dimensions:

```text
account login
symbol
family
direction
M5 bar start UTC
```

Example:

```text
A3MUX_1033669_XAUUSD_BR_BUY_20260618_1455
```

Keep the key below the MT5 global-variable name limit.

## 5.2 Family mapping

```text
933200 -> BR
933300 -> BR
933400 -> BR
future A3 signal-quality lane -> BR
```

## 5.3 Claim protocol

Before any future `OrderSend`:

1. compute current M5 bar start;
2. scan current positions, pending orders, and account history from bar start for same account/symbol/family/direction;
3. create the global-variable slot if absent;
4. atomically claim `0 -> owner_magic` with `GlobalVariableSetOnCondition`;
5. write claim log before sending;
6. call `OrderSend` only after successful claim.

## 5.4 Release and expiry

Safest policy:

```text
Successful or accepted order:
  retain claim through the end of the M5 bar plus 60 seconds.

Failed order:
  retain claim through bar expiry.
  Do not allow another lane to "rescue" the same signal in the same bar.

New bar:
  owner may delete its prior-bar claim.

Startup:
  reconstruct current-bar lock from positions, orders, and history.

Stale lock:
  delete only if encoded bar timestamp is older than 15 minutes
  and no matching current-bar exposure/history exists.
```

Do not immediately release after a successful send.

## 5.5 Cross-terminal boundary

MT5 terminal Global Variables coordinate EAs within the same terminal data directory.

If A3 lanes ever run across different terminal directories, this mutex is insufficient.

In that case, require:

- one broker-action arbiter terminal, or
- a separately reviewed OS/file-lock service.

Do not claim cross-terminal safety from a terminal-local GlobalVariable.

## 5.6 Priority policy

Near-term rule:

```text
Only one A3 breakout-family lane may be broker-action enabled at a time.
```

The mutex is a defense against mistakes/races, not permission to run several correlated lanes simultaneously.

## 5.7 Tests

Create:

```text
tests/test_a3_family_mutex_contract.py
tests/test_a3_family_mutex_scenarios.py
```

Cover:

1. same account/symbol/family/direction/bar -> one winner;
2. opposite direction -> separate keys;
3. different symbol -> separate keys;
4. different account -> separate keys;
5. different M5 bar -> separate keys;
6. same-second two-lane race;
7. order failure retains lock;
8. successful send retains lock through bar;
9. stale cleanup after 15 minutes;
10. restart reconstruction from positions/orders/history;
11. unknown magic fails closed;
12. manager does not claim entry mutex;
13. no duplicate virtual trades in shadow logs.

---

## Stage 6 — shadow reactivation evidence

`933300` and `933400` remain paused for the entire shadow period.

Prefer a new future magic such as:

```text
933500 = A3_BREAKOUT_SQ_V1
```

Do not overwrite the historical identities of `933300` or `933400`.

### 6.1 Minimum sample

Primary candidate must accumulate:

```text
>= 100 closed virtual trades
>= 20 active market days
>= 4 calendar weeks
>= 25 long and >= 25 short trades,
unless a one-sided hypothesis was pre-registered
>= 3 distinct weeks with at least 15 trades
```

### 6.2 Performance gates

All must pass:

```text
Win rate >= 50%

Profit factor >= 1.30 after measured spread/cost

Net expectancy >= +0.15R per trade

P95 cost_R <= 0.15R

No accepted trade cost_R > 0.15R

Max consecutive losses <= 8 in the full shadow sample

Max drawdown <= 8R

Largest single trade contribution <= 10% of net PnL

Top 5 trades contribution <= 40% of net PnL

No single day contributes > 30% of positive net PnL

At least 3 of 4 weekly buckets have PF >= 1.0

Session compliance = 100%

Duplicate family entries = 0

Unknown/missing indicator decisions = blocked and separately reported
```

### 6.3 Parity gates

Before broker action:

```text
MQL5 observer decision must match an independent Python reproduction
on >= 99% of evaluated completed-bar decisions.

All mismatches must be classified.

No unresolved lookahead/data-timestamp mismatch.

Virtual entry/SL/TP calculations must match a second implementation
within one symbol point.
```

### 6.4 Reactivation sequence

1. shadow candidate passes;
2. independent reviewer signs off;
3. owner approves exact version/hash;
4. compile proof 0 errors / 0 warnings;
5. profile backup;
6. zero A3 exposure baseline;
7. attach one new lane only;
8. fixed 0.01 lot;
9. broker action initially limited to a micro demo pilot;
10. first-order and first-day reconciliation;
11. no other A3 breakout lane active.

---

## Stage 7 — containment before any reactivation

Containment is mandatory.

## 7.1 Account-wide exposure

```text
Max open A3 breakout-family positions: 1
Max pending A3 breakout-family orders: 0 for market-entry design
Max new A3 breakout-family entries per M5 bar: 1
Max broker-action A3 breakout-family lanes: 1
```

## 7.2 Per-trade risk

```text
Initial monetary risk <= 0.50% of day-start equity.

If broker minimum lot makes risk exceed the cap:
  block the trade.
```

## 7.3 Daily limits

Use Dubai day boundaries.

```text
Max new entries per day: 2

Soft daily lock:
  2 closed losses in the same Dubai day
  OR daily family PnL <= -1.5R
  OR equity drawdown <= -1.5% from day-start equity

Action:
  block new entries until next Dubai day.
```

## 7.4 Hard review locks

```text
4 consecutive closed losses:
  block new entries and require manual owner reset.

Weekly family PnL <= -4R
OR weekly equity drawdown <= -4%:
  block until review.

Any duplicate-family broker entry:
  immediate manual-review lock.

Any unauthorized magic/account/symbol:
  immediate kill-switch lock.
```

## 7.5 Reset semantics

Soft daily lock:

```text
auto-reset at 00:00 Dubai only if:
  no open A3 position,
  no pending A3 order,
  kill file absent,
  prior day ledger closed successfully.
```

Hard lock:

```text
must survive terminal restart;
requires a versioned manual reset file;
reset file contains account, date, reason, owner, and approved commit/hash;
reset action is logged.
```

A daily breaker is necessary before reactivation, but it does not replace signal-quality gates.

---

## 6. Status/report changes still required

The three-way split is correct:

```text
artifact_integrity_status
runtime_performance_status
runtime_authorization_status
```

Add:

```text
historical_owner_authorization
current_runtime_state
effective_runtime_authorization
runtime_snapshot_at_utc
evidence_window_start_utc
evidence_window_end_utc
test_suite_status
open_positions
pending_orders
family_mutex_status
containment_status
shadow_hypothesis_status
reactivation_gate_status
source_runtime_parity_status
next_allowed_transition
```

Fix the current contradiction where the Tier1 static lane object still presents:

```text
dry_run=false
broker_action_allowed=true
```

while the effective runtime state is paused.

Rename repository identity fields:

```text
artifact_generation_base_commit
```

Do not call it simply `commit` when the artifact is committed one revision later.

---

## 7. Files likely to change

### Test/governance cleanup

```text
xau-usd/xauusd-phase1/scripts/audit_phase1_safety.py
xau-usd/xauusd-phase1/scripts/generate_phase1_acceptance_report.py
xau-usd/xauusd-phase1/scripts/generate_phase1_status_summary.py
xau-usd/xauusd-phase1/scripts/generate_phase2_demo_preflight.py
xau-usd/xauusd-phase1/scripts/verify_phase2_transition_artifacts.py
xau-usd/xauusd-phase1/tests/test_phase1_static.py
xau-usd/xauusd-phase1/tests/test_phase1_acceptance_report.py
xau-usd/xauusd-phase1/tests/test_phase1_status_summary.py
xau-usd/xauusd-phase1/tests/test_phase2_experimental_demo_executor.py
xau-usd/xauusd-phase1/tests/test_phase2_transition_artifacts.py
```

### Pause script hardening

```text
xau-usd/xauusd-phase1/scripts/apply_a3_emergency_pause.py
xau-usd/xauusd-phase1/tests/test_apply_a3_emergency_pause.py
```

### Status schema

```text
xau-usd/xauusd-phase1/scripts/generate_project_status_summary.py
xau-usd/xauusd-phase1/scripts/generate_project_status_page.py
status_summary.json
status_summary.md
status.html
agent.md
```

### Shadow repair

```text
xau-usd/xauusd-phase1/docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_xx.md
xau-usd/xauusd-phase1/mt5/Experts/Account3SignalQualityShadowObserver.mq5
xau-usd/xauusd-phase1/mt5/Include/A3SignalQualityPolicy.mqh
xau-usd/xauusd-phase1/mt5/Include/A3FamilyMutex.mqh
xau-usd/xauusd-phase1/mt5/Presets/Account3SignalQualityShadowObserver.safe_xauusd.set
xau-usd/xauusd-phase1/scripts/generate_a3_signal_quality_shadow_report.py
xau-usd/xauusd-phase1/outputs/reports/A3_SIGNAL_QUALITY_SHADOW_REPORT.md
xau-usd/xauusd-phase1/outputs/reports/A3_SIGNAL_QUALITY_SHADOW_ROWS.csv
```

### Containment

```text
xau-usd/xauusd-phase1/mt5/Include/A3ContainmentPolicy.mqh
xau-usd/xauusd-phase1/docs/A3_CONTAINMENT_POLICY.md
xau-usd/xauusd-phase1/tests/test_a3_containment_contract.py
```

---

## 8. Required reports

Before any A3 reactivation:

```text
PHASE1_TEST_CLOSURE_AFTER_A3_PAUSE.md
A3_EMERGENCY_PAUSE_SCRIPT_TEST_REPORT.md
A3_STATUS_SCHEMA_V2_REPORT.md
A3_SIGNAL_QUALITY_HYPOTHESIS_LOCK.md
A3_SIGNAL_QUALITY_SHADOW_REPORT.md
A3_SIGNAL_QUALITY_PARITY_REPORT.md
A3_FAMILY_MUTEX_TEST_REPORT.md
A3_FAMILY_MUTEX_SHADOW_REPORT.md
A3_CONTAINMENT_TEST_REPORT.md
A3_REACTIVATION_READINESS_REPORT.md
```

Final readiness states:

```text
PASS
FAIL
PENDING
```

No ambiguous `CONDITIONAL` field may authorize runtime by itself.

---

## 9. What Codex should do first

Exact first task:

```text
Do not touch MT5 runtime.

Fix audit_phase1_safety.py into canonical and experimental policy domains.

Add the new safety-domain tests.

Run the full Phase 1 suite.

Then resolve the EURUSD lot contract and regenerate Phase2 preflight.

Do not start the shadow EA until the full test suite is green.
```

Second task:

```text
Fix status_summary schema contradiction and add current runtime fields.
```

Third task:

```text
Write and SHA256-lock A3_SIGNAL_QUALITY_HYPOTHESES_V1.
```

Only then implement the shadow observer, family mutex, and containment modules.

---

## 10. Explicitly out of scope

Until all reactivation gates pass:

```text
No reactivation of 933200
No reactivation of 933300
No reactivation of 933400
No new A3 broker-action lane
No changes to A1 or A2
No changes to protected A1 breakout-core charts
No live or real-capital trading
No lot increase
No averaging down
No grid
No martingale
No threshold tuning after forward results
No profit-lock rearming
No adding 933300 to the external profit-lock manager
No using the quarantined bar replay as promotion evidence
No multiple A3 breakout lanes broker-action-enabled simultaneously
No daily breaker presented as proof of edge
```

---

## 11. Final decision table

| Item | Verdict |
|---|---|
| Accept `b7ea982` pause implementation | **GO** |
| Keep A3 pause active | **GO** |
| Reactivate `933300` now | **NO-GO** |
| Reactivate `933400` now | **NO-GO** |
| Keep profit-lock armed | **NO-GO** |
| Keep profit-lock attached dry-run | **GO** |
| Fix remaining tests | **GO / FIRST PRIORITY** |
| Implement family mutex shadow contract | **GO after green tests** |
| Implement signal-quality observer | **GO after locked hypothesis** |
| Add containment before reactivation | **REQUIRED** |
| Canonical Phase 2 | **NO-GO** |
| Live / real capital | **ABSOLUTE NO-GO** |

---

## 12. Bottom line

`b7ea982` successfully contains the immediate risk.

The next phase is not another runtime tweak. It is:

```text
green the governance tests
fix status truthfulness
lock one primary signal-quality hypothesis
build a tick-level shadow observer
prove zero duplicate-family entries
add containment
then consider one new versioned A3 lane only
```

`933300` and `933400` should remain paused until the full evidence package passes.
