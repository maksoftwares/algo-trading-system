# Final Review — Commit `ab95b3def4888921dae4861fb9398cdaf26ea4c0`
## A3 XAUUSD Signal-Quality Repair Plan for Codex

**Repository:** `maksoftwares/algo-trading-system`  
**Commit reviewed:** `ab95b3def4888921dae4861fb9398cdaf26ea4c0`  
**Review date:** 2026-06-18  
**Account:** A3 `1033669`  
**Symbol:** `XAUUSD`  
**Boundary:** Repo-only and shadow-only. No broker action, no profile arming, no live attach, no order/position changes.

---

# 1. Executive verdict

```text
Commit ab95b3de safety/governance work:      GO
A3 current paused state:                     KEEP
Signal-quality repair completed:             NO
Proceed to shadow research implementation:   GO
Reactivate 933200:                           NO-GO
Reactivate 933300:                           NO-GO
Reactivate 933400:                           NO-GO
Promote round-retest family:                 NO-GO
Combine breakout and round lanes:            NO-GO
Live / real capital:                         ABSOLUTE NO-GO
```

`ab95b3de` successfully hardens the pause, introduces two-tier kill semantics, adds an arming audit, improves status semantics, and locks an implementation contract/provenance bundle. It does **not** improve the A3 entry logic. That is correctly reflected in the repo: A3 remains paused and `shadow_candidate_performance_status` remains unevaluated.

The next task is not to reactivate an old lane. It is to build a controlled shadow experiment that measures the full **frequency-versus-quality curve** for the breakout-retest family.

---

# 2. Important review findings about `ab95b3de`

## 2.1 What is strong

- Emergency pause is fail-closed, idempotent, hash-audited, and verify-only capable.
- A3 stays at zero exposure.
- Two-tier kill semantics preserve dry-run telemetry while blocking execution.
- Source safety and arming audits exist.
- The hypothesis and implementation-contract files are SHA256 locked.
- P1/P2 work is explicitly repo-only.
- Phase 1 local suite reports `425 passed`.
- No A3 execution lane was reactivated.

## 2.2 What still needs correction before P3

### A. `status_summary` is one commit and one test count behind

At this commit, the status summary still names `e3e3e7a` as the repo commit and still reports `415 passed`, while the P1/P2 implementation report says `425 passed`.

Regenerate:

```text
status_summary.json
status_summary.md
status.html
agent.md
```

Update:

```text
next_allowed_transition = P3 repo-only tick engine / filter sweep / shadow observer build
```

Remove superseded next-evidence items that have already been closed.

### B. Arming audit does not cover executable scripts

`audit_phase1_arming.py` scans:

```text
.set .ini .chr .args .env .json
```

It does not scan:

```text
.py .ps1 .bat .cmd .yaml .yml .toml .cfg
```

Yet committed Python attachment scripts can contain:

```text
InpDryRunOnly=false
InpBrokerActionAllowed=true
```

Add a policy-governed script audit. Do not apply a blanket literal ban because historical owner-authorized attachment utilities exist. Require per-script policy:

```text
default mode must be verify/dry-run
--apply must be explicit
owner packet path/hash required
review hash required
zero-exposure check required
profile backup required
current A3 pause must be acknowledged
```

### C. The locked implementation contract is under-specified

The canonical build plan says the contract should resolve:

```text
first-retest definition
signal timestamp
entry-tick eligibility
EMA/ATR seeding
warm-up
timezone mapping
weekend/gap behavior
restart recovery
tick freshness
rounding
holding duration
gap exit pricing
```

The committed contract does not yet resolve those details.

Do not edit the locked contract. Add and hash-lock:

```text
docs/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md
outputs/manifests/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.sha256.json
```

The addendum may clarify implementation seams but may not alter a locked threshold.

### D. The one-week contract language is not the promotion minimum

The implementation contract says the minimum forward window is one trading week. The locked hypothesis requires at least:

```text
100 closed virtual trades
20 active market days
4 calendar weeks
25 long and 25 short trades
3 weeks with at least 15 trades
```

Clarify in the addendum:

```text
one week = implementation-validation minimum only
full locked minimum = performance/promotion evidence
```

### E. No independent CI is visible for this commit

Local tests are useful, but before any shadow-terminal attachment require a green CI run tied to the exact source commit.

---

# 3. Most likely root cause of the bad A3 trades

The evidence supports this ranking.

## 3.1 Leading cause — direction/regime mismatch

A3 repeatedly accepted breakout signals that opposed the prevailing directional context.

However, do not overstate this as conclusively proven for the A3 breakout family:

- Across the broad sample, H1 with-trend behavior is much better than H1 against-trend behavior.
- The split is especially strong in the round family.
- The breakout-family H1 improvement is positive but more modest.
- A3-specific examples show counter-trend failures, but the improved lane later also lost heavily.

Conclusion:

```text
Moderate H1 trend control is the leading repair hypothesis,
not an established production rule.
```

## 3.2 Secondary cause — permissive retest quality

The current family can accept a technically valid retest that is structurally weak:

- deep penetration;
- weak confirmation body;
- poor close location;
- multiple retests;
- delayed confirmation;
- temporary hold followed by immediate failure.

A light retest-quality filter should be tested beside the trend filters.

## 3.3 Amplifier — duplicate family exposure

Same-minute, same-direction A3 lanes duplicated the same underlying idea. This doubled losses but did not create the original bad signal.

Treat duplicate prevention separately from signal quality.

## 3.4 Contributing cause — session/timing

The early A3 plain loss cluster occurred outside the A2-style window, and evening evidence has been stronger.

But an evening-only gate may remove roughly three quarters of opportunities. Do not make it the first signal repair if frequency preservation is a core objective.

Use session as a **reporting and stratification dimension** during the sweep.

## 3.5 Contributing cause — stop/cost geometry

The A3 plain lane had tighter risk distance and heavier cost in R than A2.

Keep the existing stop floor and `cost_R <= 0.15R` as baseline safety invariants.

Do not treat a wider stop as an entry-quality fix.

## 3.6 Separate issue — exit give-back

Historical path evidence shows a meaningful minority of losing XAUUSD trades first became profitable.

This proves that exit management deserves a separate shadow study. It does not explain the majority of losses and should not be mixed into the initial entry-filter experiment.

---

# 4. Which family should be repaired?

## Decision

```text
Repair breakout-retest.
Do not promote round-retest.
Do not combine the families.
```

Evidence direction:

```text
Breakout core:
  positive PnL
  PF materially above 1
  near-48% win rate
  survives deduped analysis

Round family:
  materially negative PnL
  PF below 1
  dominant historical drag
```

Combining the families would:

- reintroduce the round-family drag;
- make attribution harder;
- recreate duplicate exposure;
- weaken the clean experiment.

Round-level proximity may be logged as context in the future, but it must not become an entry rule in this V1/V2 repair round.

---

# 5. Anti-overfit requirement before adding new filters

The current locked V1 contains:

```text
A3_SQ_MTF_ONLY_V1
A3_SQ_RETEST_ONLY_V1
A3_SQ_COMBINED_V1
```

New `F_*` filters are not covered by that hypothesis.

Before coding them, create:

```text
docs/A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_xx.md
outputs/manifests/A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1.sha256.json
```

The diagnostic sweep is:

```text
hypothesis-generation only
not promotion evidence
not broker-action authorization
```

If an `F_*` diagnostic wins:

1. stop using the discovery window;
2. create a new locked `A3_SIGNAL_QUALITY_V2_<candidate>.md`;
3. start a completely fresh forward-validation window;
4. do not reuse diagnostic-window results as V2 pass evidence.

This discovery/validation split is mandatory.

---

# 6. Exact shadow filter sweep

Every candidate starts from the same raw `breakout_retest` would-signal event.

Log all raw signals across every Dubai session bucket. Do not hide rejected signals.

## 6.1 Baselines

### `B0_RAW_ALL_SESSION`

```text
Current raw breakout-retest would-signal
No new trend filter
No new retest filter
All sessions logged
Current stop-floor and cost calculations
```

Purpose: frequency reference.

### `B1_EVENING_BASELINE`

```text
B0 plus Dubai 16:00–19:59
```

Purpose: apples-to-apples reference for locked V1, whose session is already fixed.

## 6.2 Frequency-preserving diagnostic filters

### `F_LOOSE_CT_VETO`

Block only a strongly counter-trend H1 signal.

Completed-bar definition:

```text
h1_slope_points =
    (H1 EMA20[1] - H1 EMA20[4]) / _Point

LONG blocked only when h1_slope_points <= -50
SHORT blocked only when h1_slope_points >= +50

Neutral/weak slope is kept.
Unavailable H1 data is DATA_UNAVAILABLE, not silently kept.
```

Expected frequency hypothesis:

```text
70–90% of B0
```

This is an estimate, not a gate.

### `F_H1_ALIGN`

```text
LONG:
  H1 close[1] > H1 EMA20[1]
  AND H1 EMA20[1] > H1 EMA20[4]

SHORT:
  H1 close[1] < H1 EMA20[1]
  AND H1 EMA20[1] < H1 EMA20[4]
```

No minimum magnitude beyond correct sign.

Expected frequency hypothesis:

```text
50–70% of B0
```

### `F_H1_M15_ALIGN`

Require `F_H1_ALIGN` plus:

```text
LONG:
  M15 close[1] > M15 EMA20[1]
  AND M15 EMA20[1] > M15 EMA20[4]

SHORT:
  M15 close[1] < M15 EMA20[1]
  AND M15 EMA20[1] < M15 EMA20[4]
```

Expected frequency hypothesis:

```text
35–55% of B0
```

### `F_RETEST_LIGHT`

Keep the baseline break requirement and add only moderate structure:

```text
Break close beyond level >= 0.30 × M5 ATR14

Retest occurs within 1–10 completed M5 bars after the break

No completed M5 candle closes through the invalid side of the level
between break and confirmation

Confirmation candle body/range >= 0.40

LONG close location:
  (close-low)/(high-low) >= 0.65

SHORT close location:
  (close-low)/(high-low) <= 0.35

Confirmation closes on the breakout side of the level
```

Do not add the strict penetration and wick limits in this diagnostic.

Expected frequency hypothesis:

```text
45–70% of B0
```

### `F_LOOSE_CT_PLUS_RETEST_LIGHT`

Apply:

```text
F_LOOSE_CT_VETO
+
F_RETEST_LIGHT
```

Expected frequency hypothesis:

```text
35–55% of B0
```

## 6.3 Locked V1 candidates

Implement the locked rules byte-for-byte:

```text
A3_SQ_MTF_ONLY_V1
A3_SQ_RETEST_ONLY_V1
A3_SQ_COMBINED_V1
```

`A3_SQ_COMBINED_V1` is the only currently promotion-eligible V1 candidate.

Do not relax it to obtain more trades.

---

# 7. Exact shadow-only test to build next

Build one isolated, passive MQL5 observer that evaluates every candidate against the same base signal.

## 7.1 Files to add

```text
xau-usd/xauusd-phase1/
  docs/
    A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md
    A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_xx.md

  outputs/manifests/
    A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.sha256.json
    A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1.sha256.json

  mt5/Include/
    A3VirtualExecution.mqh
    A3SignalQualityFilters.mqh
    A3SignalQualityPolicy.mqh

  mt5/Experts/
    Account3SignalQualityShadowObserver.mq5

  mt5/Presets/
    Account3SignalQualityShadowObserver.safe_xauusd.set

  scripts/
    reproduce_a3_signal_quality.py
    replay_a3_virtual_execution.py
    generate_a3_signal_quality_sweep_report.py
    generate_a3_loss_attribution_report.py
    generate_a3_parity_report.py
    verify_a3_shadow_artifacts.py
```

## 7.2 Observer safety

Hard requirements:

```text
InpDryRunOnly=true
no OrderSend
no OrderSendAsync
no CTrade
no TRADE_ACTION_DEAL
no TRADE_ACTION_SLTP
no position/order modification
account 1033669 only
Capital.ComMena-Demo only
XAUUSD only
isolated observer terminal
```

No attachment to the A3 trading terminal in the first implementation commits.

## 7.3 Shared signal identity

Every raw base event receives:

```text
signal_id =
  account + symbol + base_family + direction +
  break_bar_time + retest_bar_time + confirmation_bar_time + level_price
```

Every candidate row references the same `signal_id`.

This enables paired comparison:

```text
candidate kept this signal
candidate blocked this signal
candidate outcome under fixed control exit
```

## 7.4 Candidate independence

Each candidate owns an independent virtual position state.

A position in one candidate must not block another candidate. Within each candidate:

```text
maximum one virtual open position
```

Log both:

```text
raw_signal_retention
executable_virtual_trade_retention
```

---

# 8. Tick-level virtual execution

## 8.1 State machine

```text
IDLE
→ SIGNAL_PENDING
→ VIRTUAL_OPEN
→ VIRTUAL_CLOSED

Alternative:
CANCELLED_NO_FRESH_TICK
INVALID_DATA
RECOVERY_REQUIRED
```

## 8.2 Entry

```text
Decision only from completed bars.

LONG:
  fill at first fresh ask after decision timestamp.

SHORT:
  fill at first fresh bid after decision timestamp.

No historical same-bar fill.

Entry expires when the next M5 bar closes without a fresh eligible tick.
```

## 8.3 Risk

```text
risk_price = max(
  raw signal risk,
  broker stops level + 5 points,
  3 × spread at fill,
  300 XAU points
)

TP = 1.50R
```

## 8.4 Exit

```text
LONG SL/TP evaluated on bid
SHORT SL/TP evaluated on ask
first executable quote crossing the level closes the virtual trade
gap exit uses actual quote, not requested level
```

Do not subtract spread a second time; ask-to-bid execution already embeds it.

## 8.5 Persistence

```text
a3_sq_decisions.csv
a3_sq_virtual_events.csv
a3_sq_virtual_trades.csv
a3_sq_virtual_state.json
```

On restart:

```text
rebuild from append-only events
if state cannot be reconstructed exactly:
  RECOVERY_REQUIRED
  block new virtual signals
```

---

# 9. Separate bad entries from bad exits

Keep the original fixed 1.50R exit for every entry-filter candidate. Do not test entry and exit changes in the same experiment.

For every losing virtual trade, use path order.

## 9.1 Entry failure

```text
BAD_SIGNAL:
  -0.50R is reached before +0.50R
  OR +0.50R is never reached before final SL
```

## 9.2 Mixed path

```text
MIXED:
  +0.50R is reached first
  but maximum favorable excursion remains below +0.75R
  and the trade later loses
```

## 9.3 Exit give-back

```text
BAD_EXIT_GIVEBACK:
  +0.75R is reached before -0.50R
  and the trade later closes at <= 0R
```

## 9.4 Near-target give-back

```text
NEAR_TP_GIVEBACK:
  +1.25R is reached
  TP at +1.50R is not reached
  trade later closes at <= 0R
```

Report:

```text
first_hit_plus_0_50_time
first_hit_minus_0_50_time
max_MFE_R
max_MAE_R
time_to_MFE
time_to_MAE
bars_held
final_R
loss_class
```

Historical evidence suggests most losses are entry failures, while roughly a quarter to a third may be give-backs. Entry quality remains the first project. Exit management becomes a separate Stage-2 experiment after a frequency-preserving entry candidate is identified.

---

# 10. Python parity and replay

Python must be independent.

Do not import the MQL-facing strategy implementation.

## 10.1 Feature parity

Compare:

```text
M5 ATR14
H1 EMA20
M15 EMA20
D1 EMA20/EMA50
completed-bar indexing
session mapping
break/retest/confirmation bars
close location
body/range
spread
stop-floor geometry
cost_R
```

Document:

```text
EMA initialization
Wilder ATR initialization
minimum warm-up
timezone conversion
DST policy
point/digits rounding
missing-data behavior
```

## 10.2 Decision parity

Required:

```text
>=99% across all evaluated decisions
100% on accepted promotion-eligible signals
```

Mismatch classes:

```text
BAR_ALIGNMENT
TIMEZONE
EMA_SEEDING
ATR_SEEDING
ROUNDING
SESSION_BOUNDARY
QUOTE_FRESHNESS
RETEST_INDEX
STATE_RECOVERY
DATA_GAP
UNKNOWN
```

Any `UNKNOWN` affecting an accepted candidate is a NO-GO.

## 10.3 Execution parity

Required:

```text
same signal_id
same first eligible tick
same fill timestamp
same direction
entry/SL/TP within 1 point
same exit event and timestamp
same net R
same MFE/MAE
```

---

# 11. Frequency and quality metrics

## 11.1 Per candidate

```text
raw base signals
accepted signals
signal retention %
opened virtual trades
trade retention %
closed trades
session buckets
direction counts
win rate
PF after executable bid/ask costs
net expectancy R
net R
max drawdown R
max consecutive losses
P50/P95 cost_R
largest trade contribution
top-five contribution
best-day contribution
weekly PF
regime coverage
bad-signal loss share
give-back loss share
```

## 11.2 Frequency floor

For any frequency-preserving future V2 candidate:

```text
signal retention >= 40% of B0
virtual-trade retention >= 35% of B0
>=100 closed trades
median weekly trades >= 40% of B0 median weekly trades
```

A candidate that improves PF by blocking nearly everything fails the project objective.

## 11.3 Diagnostic eligibility for V2 registration

A diagnostic may be selected for a new V2 hypothesis only if, in the discovery window:

```text
signal retention >= 40%
closed virtual trades >= 100
PF >= 1.20
expectancy >= +0.10R
PF improvement vs B0 >= +0.15
OR expectancy improvement vs B0 >= +0.05R

blocked bucket expectancy is worse than kept bucket
bad-signal loss share improves by >=20% relative
no concentration breach
evidence includes both rising and falling regimes
```

These are **V2 registration eligibility** gates, not broker-action gates.

After V2 is locked, start a new fresh validation window.

## 11.4 Final reactivation gates

For locked V1, use all existing locked gates, including `WR >= 50%`.

For a future V2, decide the win-rate objective before locking. Recommendation:

```text
hard WR floor >=45%
target WR >=50%
PF >=1.30
expectancy >=+0.15R
```

Reason: the profitable breakout core historically operated near 48% win rate. A mandatory 50% gate may reject a valid 1.5R-payoff edge. If the owner insists on a strict 50% objective, write that into V2 before the fresh test.

All final gates also require:

```text
>=100 trades
>=20 active market days
>=4 calendar weeks
>=25 long and >=25 short
>=3 weeks with >=15 trades
frequency floor
P95 cost_R <=0.15
no trade cost_R >0.15
max consecutive losses <=8
max drawdown <=8R
concentration gates
session compliance
zero duplicate family events
>=99% decision parity
100% accepted-signal parity
```

---

# 12. Required reports

```text
A3_SIGNAL_QUALITY_IMPLEMENTATION_CONTRACT_ADDENDUM_01.md
A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_LOCK.md
A3_SIGNAL_QUALITY_BUILD_REPORT.md
A3_SIGNAL_QUALITY_OBSERVER_SAFETY_REPORT.md
A3_VIRTUAL_EXECUTION_TEST_REPORT.md
A3_SIGNAL_QUALITY_PARITY_REPORT.md
A3_SIGNAL_QUALITY_SWEEP_REPORT.md
A3_LOSS_ATTRIBUTION_REPORT.md
A3_SHADOW_FORWARD_REPORT.md
A3_DATA_MANIFEST.json
A3_SHADOW_ARTIFACT_MANIFEST.json
```

The sweep report must show, for every candidate:

```text
quality
frequency
regime
session
direction
concentration
entry-failure versus exit-give-back split
```

---

# 13. One task per commit

## Commit SQ-00 — status and audit cleanup

```text
Regenerate status artifacts.
Extend arming audit to executable deployment scripts.
Add policy tests.
No strategy code.
```

## Commit SQ-01 — implementation addendum

```text
Add and hash-lock V1 implementation addendum.
Resolve indexing, seeding, tick, restart and data-split semantics.
No strategy code.
```

## Commit SQ-02 — diagnostic sweep registration

```text
Pre-register B0/B1/F_* definitions and discovery-window rules.
Hash-lock the document.
No strategy code.
```

## Commit SQ-03 — virtual execution engine

```text
Add A3VirtualExecution.mqh.
Add deterministic state-machine tests.
No filter logic.
```

## Commit SQ-04 — filter library

```text
Add A3SignalQualityFilters.mqh.
Implement locked V1 and pre-registered diagnostics.
Add fixture tests.
No observer attachment.
```

## Commit SQ-05 — shadow observer

```text
Add Account3SignalQualityShadowObserver.mq5.
Add safe preset.
Add passive-source safety tests.
No MT5 attachment.
```

## Commit SQ-06 — Python parity

```text
Add independent Python feature/decision/execution implementation.
Add parity tests and mismatch taxonomy.
```

## Commit SQ-07 — reporting and loss attribution

```text
Add sweep, parity, frequency and signal-vs-exit reports.
No attachment.
```

## Commit SQ-08 — deterministic offline integration

```text
Run MQL5/Python fixtures and captured-tick replay.
Produce build/parity reports.
Fix implementation defects without changing thresholds.
```

## Commit SQ-09 — isolated shadow attachment packet

Only after SQ-00 through SQ-08 pass:

```text
owner-approved observer-only attachment
isolated terminal
no broker-action surface
startup hash verification
forward_start_utc recorded
```

## Commit SQ-10 — discovery conclusion

After discovery minimum is met:

```text
select no candidate
OR select one diagnostic for a new V2 registration
```

Do not promote from the discovery window.

---

# 14. Exact NO-GO conditions

A3 remains paused if any one is true:

```text
933200, 933300 or 933400 proposed for reactivation
round family proposed for promotion or combination
status summary is stale or contradictory
arming audit does not cover executable deployment scripts
CI is not green
implementation addendum is missing or hash-invalid
diagnostic sweep is not pre-registered
threshold changes after forward start
observer contains broker-action code
virtual state cannot recover deterministically
parity <99%
accepted-signal parity <100%
UNKNOWN mismatch affects an accepted signal
signal retention <40%
trade retention <35%
sample minimum not reached
only one market regime is represented
PF or expectancy gate fails
cost_R gate fails
concentration gate fails
bad-signal share is not materially improved
duplicate-family event occurs
A3 has any open position or order at preflight
profit-lock is armed
more than one A3 lane is proposed
reviewer or owner exact-hash approval is missing
```

---

# 15. Minimum evidence before reactivation can be discussed

```text
1. Current pause verification PASS.
2. Source safety audit PASS.
3. Expanded arming/deployment audit PASS.
4. Full test suite and CI PASS.
5. Locked hypothesis and implementation addendum.
6. Locked diagnostic sweep.
7. Shadow observer source and 0/0 compile proof.
8. Safe preset and isolated attachment report.
9. Raw bars/ticks manifest with hashes.
10. Tick-level virtual execution test report.
11. Independent Python parity report.
12. Full minimum sample across up and down regimes.
13. Frequency floor PASS.
14. All PF/expectancy/cost/concentration gates PASS.
15. Bad-signal loss share materially reduced.
16. Zero duplicate-family events.
17. New locked V2 if a diagnostic was selected.
18. Fresh V2 validation window, separate from discovery.
19. Family mutex and containment built/tested.
20. Zero-exposure preflight.
21. Profit-lock dry-run/disarmed.
22. Independent reviewer signoff.
23. Owner approval of exact source, binary, hypothesis and contract hashes.
24. One-lane, fixed-0.01-lot micro-pilot plan with hard end date.
```

---

# 16. Explicitly out of scope

```text
No reactivation of 933200.
No reactivation of 933300.
No reactivation of 933400.
No round-family promotion.
No combined breakout/round executor.
No A1 or A2 changes.
No broker action.
No live or real capital.
No preset arming.
No profit-lock deployment change.
No lot increase.
No grid, martingale, averaging or recovery.
No threshold tuning after forward start.
No historical discovery data counted as V2 validation.
No daily loss breaker presented as an entry-quality fix.
```

---

# 17. Codex first instruction

```text
Do not touch MT5 runtime.

First commit:
  regenerate status artifacts and extend the arming audit to executable
  deployment scripts with explicit policies.

Second commit:
  write and lock the implementation addendum.

Third commit:
  pre-register and hash-lock the diagnostic filter sweep.

Only then begin A3VirtualExecution.mqh.
```

---

# 18. Bottom line

The best current route is:

```text
breakout-retest base
+
moderate H1 direction control
+
light retest quality
+
fixed original exit
+
tick-level virtual evidence
```

Do not assume the strict locked V1 will preserve frequency. Run it honestly, but use the pre-registered diagnostics to find the quality-frequency frontier. If a diagnostic wins, create a new locked V2 and validate it on fresh data.

A3 remains paused throughout.
