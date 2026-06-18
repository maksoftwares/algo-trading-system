# Final Review — Commit `d5dd2de` / A3 Runtime, Profit-Lock, Signal Quality, and Governance

**Repository:** `maksoftwares/algo-trading-system`
**Commit reviewed:** `d5dd2de` on `main`
**Review date:** 2026-06-18
**Scope:** A3 XAUUSD demo behavior, repeated SL losses, A3 lane decisions, profit-lock manager, signal-quality improvements, and static/governance test failures.

---

## 0. Review caveat

This is a static review of the committed GitHub artifacts and source. I did **not** independently clone and run the repo locally in this environment. The GitHub connector shows **no workflow runs** for the reviewed commit, so I could not map the reported `399 passed / 6 failed` to exact CI logs from GitHub Actions. The test-failure triage below is therefore based on committed source/artifacts and should be turned into a repo-side `PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md` with the exact local pytest output. fileciteturn80file0

---

## 1. Executive verdict

```text
A3 account 1033669 may continue demo-only observation/execution: CONDITIONAL GO
Plain A3 lane 933200 stopped: CORRECT / KEEP STOPPED
Improved A3 lane 933300 active: CONDITIONAL GO, monitor per-magic evidence
Tier1 compat lane 933400 active: CONDITIONAL GO, monitor per-magic evidence
Profit-lock manager: CONDITIONALLY SAFE, useful as a limited SL-protection manager
Further runtime changes: NO-GO until fresh A3 per-magic evidence is collected
Live / real capital: ABSOLUTE NO-GO
Immediate rollback: NO, unless 933300/933400 keep producing loss clusters
```

The strongest conclusion is that **stopping the plain A3 lane `933200` was correct**. The historical diagnosis shows A3’s losses were concentrated in the unfiltered plain lane taking trades that A2 deliberately blocked, with tighter stops and heavier cost-in-R. fileciteturn62file0

However, the current A3 account evidence described in the review request — **22 closed XAUUSD trades, 21 losses, 1 tiny win** — is severe. Before more runtime changes, the repo needs a fresh, committed, per-magic A3 evidence packet that attributes those losses among `933200`, `933300`, and `933400`.

---

## 2. Must-fix blockers first

### Blocker 1 — Exact 6 test failures are not committed as a triage artifact

The user reports:

```text
phase1 suite: 399 passed, 6 failed
```

but the commit has no GitHub workflow run visible for `d5dd2de`, so the exact failures are not independently reviewable from CI. fileciteturn80file0

**Required fix:** add a committed artifact:

```text
xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md
```

It should include:

```text
pytest command used
full failing test names
failure tracebacks or summaries
classification: EXPECTED_GOVERNANCE_UPDATE / REAL_CODE_DEFECT / STALE_ARTIFACT
owner decision for each failure
fix commit/hash
```

Until that exists, do not treat the suite as clean.

---

### Blocker 2 — `status_summary.md/json` are stale or internally inconsistent with the reviewed commit

At commit `d5dd2de`, `status_summary.md` says:

```text
Commit: bf6fbff3c8eaddb7bb33509b1c606ab37d8542ee
Branch: codex/a3-repair-lane-2026-06-13
```

not `d5dd2de` / `main`. fileciteturn76file0

`status_summary.json` repeats the same branch/commit values under `repo.branch`, `repo.commit`, and `repo.main_remote_commit`. fileciteturn77file0

**Required fix:** regenerate:

```text
status_summary.json
status_summary.md
status.html
agent.md runtime-status section
```

from the actual latest `main` commit. This is not a trading-risk issue by itself, but it is a review/governance issue. The compact status artifacts were added specifically because `status.html` is too large to reliably audit; they must be current.

---

### Blocker 3 — Fresh A3 direct-history report for the 22-trade loss window is missing from reviewable committed artifacts

The prompt says:

```text
A3 account 1033669 had 22 closed XAUUSD trades in the reviewed window: 21 losses, 1 tiny win.
```

But the committed report I could inspect, `A3_FAILURE_DIAGNOSIS_2026_06_17.md`, describes an earlier/fresh-at-that-time state:

```text
57 closed positions
20 wins / 37 losses
35.09% win rate
-99.62 AED closed net PnL
```

and specifically identifies the plain lane as the main loss source. fileciteturn62file0

**Required fix:** commit a fresh report for the exact 22-trade window:

```text
A3_DIRECT_HISTORY_1033669_2026_06_18.md
A3_DIRECT_HISTORY_1033669_2026_06_18.csv
A3_PER_MAGIC_ATTRIBUTION_2026_06_18.md
```

Minimum per-magic fields:

```text
magic
lane_name
closed_trades
wins
losses
win_rate
net_pnl_AED
profit_factor
avg_win
avg_loss
max_loss
consecutive_losses
open_positions
broker_action_allowed_now
```

Without this, the decision on `933300` and `933400` is conditional rather than fully evidence-backed.

---

### Blocker 4 — Broker-action artifacts need explicit test-domain separation

The repo now contains broker-action/demo-management artifacts, including `Account3ProfitLockExitManager.mq5`, which uses `OrderSend` for `TRADE_ACTION_SLTP` stop modification. fileciteturn70file0

This is not inherently wrong because it is a demo-only management EA with account/symbol/magic guards, but it will break any old static test that assumes **all Phase 1 files must contain no broker-action terms**.

**Required fix:** update the test taxonomy:

```text
1. Phase1 dry-run shell / passive observers: no OrderSend, no CTrade, no broker action.
2. Owner-authorized experimental demo executors: broker-action allowed only in allowlisted files.
3. A3 profit-lock manager: SLTP modification allowed only for allowlisted magics and account 1033669.
4. Canonical Phase 2 / live: still NO-GO.
```

Do not simply delete or weaken the safety tests. Scope them.

---

### Blocker 5 — A3 per-magic kill conditions must be explicit before additional runtime changes

Because the latest user-provided A3 outcome is extremely weak — 21 losses out of 22 trades — the next runtime change should not be another signal tweak. First define hard per-magic stop conditions.

Recommended emergency thresholds for A3 demo-only lanes:

```text
If a lane records 5 consecutive closed losses after the latest mitigation: pause that lane.
If a lane records PF < 0.80 after 20 fresh closed trades: pause that lane.
If account-level A3 daily closed loss exceeds a chosen AED cap: pause all new A3 entries.
If a lane produces repeated same-family duplicates not blocked by the mutex: pause that family.
```

These are not strategy improvements; they are containment rules.

---

## 3. A3 current behavior and diagnosis

### 3.1 Known A3 lane map

| Lane | Magic | Current intended state | Notes |
|---|---:|---|---|
| A3 plain | `933200` | **Stopped** | `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`; correct action. |
| A3 improved | `933300` | Active demo | Trend guard, breakeven, partial enabled. Not managed by profit-lock manager. |
| A3 Tier1 compat | `933400` | Active demo | A2-style session gate, XAU stop floor, trend guard shadow-only. |
| A3 profit-lock manager | manager EA | Armed demo manager | Does not open trades; modifies SL only for selected magics after trigger. |

The agent handoff says the A3 Tier1 compat lane is on account `1033669`, symbol `XAUUSD`, magic `933400`, fixed `0.01`, dry-run false, broker-action true, and demo-only; it also states this is not canonical Phase 2 or live/real-capital authorization. fileciteturn60file0

### 3.2 Why A3 has produced repeated SL losses

The root cause is not that MT5 or the broker is broken. The committed A3 diagnosis says A3 failed because it took trades that A2 deliberately filtered out. fileciteturn62file0

The two largest differences were:

```text
1. A2 has an active session gate; A3 plain did not.
2. A2 applies a wider XAUUSD execution stop-distance floor; A3 plain used raw observer risk.
```

The report states that A3 plain also had trend guard and exit protection disabled, and that the A3 improved lane saw the same would-signals but blocked them through trend/cost checks. fileciteturn62file0

Concrete evidence from the diagnosis:

```text
A3 plain closed trades: 6
Wins: 0
Losses: 6
Net PnL: -96.39 AED
```

Those trades occurred in afternoon, night, and morning; none were in the A2-style Dubai evening execution window. fileciteturn62file0

The A2-versus-A3 guard comparison is especially important: several A3 losing signals were seen by A2 but blocked by `server_hour_session_gate`. fileciteturn62file0

### 3.3 Stop-distance / cost-R issue

The A3 diagnosis reports:

```text
A2 executed orders: avg stop distance ~958 points, avg cost_R ~0.063R
A3 plain orders:   avg stop distance ~421 points, avg cost_R ~0.133R
```

That means the same 50–75 point spread consumes roughly twice as much risk budget in A3 plain. fileciteturn62file0

This explains the repeated SL pattern: tight stops + high cost_R + weak session/trend filtering make normal XAUUSD noise enough to stop out the lane.

---

## 4. Was stopping plain lane `933200` correct?

Yes. This was correct and should remain in force.

Reasons:

```text
1. It caused the largest identified A3 loss cluster.
2. It lacked A2’s session gate.
3. It lacked the A2-style XAU stop floor.
4. It had trend guard and exit protection disabled.
5. The improved lane reportedly blocked the same bad signals.
6. Continuing it would dilute the evidence for 933300/933400.
```

Recommendation:

```text
Keep 933200 dry-run / broker-action-off through the full forward week.
Do not reactivate 933200 unless a new hypothesis and owner packet are produced.
If legacy 933200 positions still exist, the profit-lock manager may manage them until closed; no new 933200 entries.
```

---

## 5. Should `933300` and `933400` remain active?

### 5.1 `933300` improved lane

**Verdict:** conditional GO, but only with fresh per-magic monitoring.

Reason to keep active for now:

```text
A3 improved is the lane that historically blocked the bad A3 plain signals using trend/cost checks.
```

The A3 diagnosis says the improved lane saw the same would-signals and blocked afternoon shorts, morning longs, and a night long through `TREND_AGAINST_SIGNAL` or `COST_R_CAP_BLOCK`. fileciteturn62file0

Risk:

```text
If the fresh 22-trade / 21-loss window includes 933300 losses, then the committed diagnosis is stale and 933300 must be re-evaluated immediately.
```

Action:

```text
Keep 933300 active only until a fresh A3_PER_MAGIC_ATTRIBUTION report is generated.
If 933300 has >=5 consecutive fresh losses or PF <0.80 after 20 fresh trades, pause it.
```

### 5.2 `933400` Tier1 compat lane

**Verdict:** conditional GO, but it is still validation, not proof.

Why it is safer than 933200:

```text
1. Separate magic/comment/log namespace.
2. A2-style session gate.
3. A2-style XAU stop floor.
4. Account 1033669 scoped.
5. Fixed 0.01 lot.
6. Demo-only owner authorization.
```

The A3 Tier1 pre-attachment review confirmed the source-level build was correct and safe repo-side: the breakout kernel was unchanged, the session gate and stop floor were implemented around the kernel, trend guard was shadow-only, and committed defaults were non-executing. fileciteturn75file0

However, the same review recommended observer/dry-run first, not immediate broker action; owner later explicitly approved broker-action demo attachment. That governance override is now documented in the status summary and agent handoff. fileciteturn77file0 fileciteturn60file0

Action:

```text
Keep 933400 active only as owner-authorized demo validation.
Do not treat 933400 as canonical or live-ready.
Collect one full forward-week per-magic report.
If 933400 produces a similar SL cluster, revert it to dry-run and keep only observer evidence.
```

---

## 6. Profit-lock manager review

### 6.1 What it does

`Account3ProfitLockExitManager.mq5` is not an entry EA. It does not open new trades. It scans positions on a timer and, if a managed position reaches a configured unrealized-R trigger, it modifies the position SL to lock profit. fileciteturn70file0

Current defaults:

```text
Managed magics: 933200,933400
Excluded magic: 933300
Primary trigger: +1.25R
Primary lock: +0.80R
Dry-run default: true
Manage action default: false
```

The source explicitly excludes `933300` even if it appears in the managed magic CSV. fileciteturn70file0

### 6.2 Safety strengths

The manager has good safety controls:

```text
Account login allowlist: 1033669
Expected server marker: Demo
Target symbol: XAUUSD
Kill-switch file
Magic allowlist
933300 hard exclusion
Only improves stop, never widens risk
Broker stop/freeze-level distance check
Dry-run and manage-action flags
```

The stop-improvement and broker-distance functions prevent moving SL in a worse direction or too close to market. fileciteturn70file0

The actual broker-action call is limited to `TRADE_ACTION_SLTP` for a specific position, not a new trade. fileciteturn70file0

### 6.3 Usefulness

It is useful for one specific pain point:

```text
Trades that go meaningfully green, then reverse to SL.
```

The dynamic profit-lock proposal showed that on 356 covered XAUUSD trades, 22.71% of losers first reached at least +0.75R, 12.66% reached +1.00R, and 3.93% reached +1.25R. It also showed several virtual lock rules improved replay PnL, although they require fresh proof. fileciteturn72file0

### 6.4 Limitations

The manager will **not** fix the current low win-rate problem if trades go straight to SL. It only acts after the trade reaches a profit threshold. The user’s context says it has not acted yet because trades have not reached the trigger, which is consistent with its design.

Also, because it excludes `933300`, A3 evidence becomes asymmetric:

```text
933300 has internal BE/partial behavior.
933400 has external profit-lock behavior.
933200 is stopped but can still be managed if legacy positions exist.
```

This is acceptable, but reports must never compare 933300 and 933400 as if their exit management were identical.

### 6.5 Required profit-lock reporting

Add or refresh:

```text
A3_PROFIT_LOCK_MANAGER_STATUS_2026_06_18.md
A3_PROFIT_LOCK_ACTION_LOG_2026_06_18.csv
A3_PROFIT_LOCK_COVERAGE_BY_MAGIC_2026_06_18.md
```

Required fields:

```text
managed_magic
positions_seen
positions_reaching_0.75R
positions_reaching_1.00R
positions_reaching_1.25R
SL_moves_sent
SL_moves_succeeded
SL_moves_failed
DEFER_STOPS_LEVEL count
avg locked_R
saved_loss_count
winner_clipped_count
```

---

## 7. Signal-quality improvements without relying mainly on daily loss breaker

The goal should be to improve **trade selection**, not merely stop the account after bad trades. Daily loss breaker is necessary as a circuit breaker, but it is not a strategy-quality fix.

### 7.1 Cross-lane duplicate blocking

Current known limitation: the agent handoff says the experimental demo executor blocks same-symbol, same-direction, same-family entries opened during the current M5 bar, but repair lanes use separate magic ranges and can still duplicate parent-family behavior. It also warns to watch for same-second check/send races. fileciteturn60file0

Recommended next design:

```text
Implement an account-level family mutex shared by A3 lanes.
Key = account + symbol + direction + family + M5_bar_time.
Use GlobalVariableSetOnCondition where possible.
Apply before any OrderSend.
TTL = current M5 bar + small safety buffer.
Log DUPLICATE_FAMILY_BLOCK or WOULD_DUPLICATE_FAMILY_EVENT.
```

Do **not** deploy this as a runtime guard until fresh evidence shows residual duplicate losses after the current mitigation.

### 7.2 Trend alignment

The A3 diagnosis indicates trend guard would have blocked multiple bad A3 plain trades. fileciteturn62file0

Recommended approach:

```text
For 933300: keep existing trend guard active.
For 933400: continue shadow trend logging for the forward week.
If shadow trend guard would have blocked losing 933400 trades without materially clipping winners, promote it through a separate owner packet.
```

Avoid changing 933400 trend guard from shadow to active without a forward-week report, because the pre-attachment review confirmed trend guard was intentionally shadow-only for the Tier1 compat lane. fileciteturn75file0

### 7.3 Retest confirmation quality

The repeated SL losses suggest retest quality may be too loose in some lanes.

Add a shadow-only quality report first:

```text
A3_RETEST_QUALITY_SHADOW_REPORT.md
```

Candidate features to measure:

```text
break distance in ATR
retest depth
retest close relative to level
confirmation candle body/wick quality
opposing wick size
distance from level at entry
bars since break
level reuse count
signal age
```

Potential future filters, after evidence:

```text
Minimum breakout displacement.
Retest must close back on correct side of level.
Confirmation candle must close in direction with body >= X% of ATR.
Reject if immediate opposite wick exceeds a threshold.
Reject reused levels within N bars.
```

Do not deploy these directly; shadow them first.

### 7.4 Session filtering

A2’s session gate was the largest known difference versus A3 plain. A3 Tier1 compat is designed with A2-style session gate. fileciteturn75file0

Recommended rule:

```text
933400 keeps the A2-style session gate.
933300 should be analyzed under the same session gate as a shadow overlay.
If 933300 losses are mostly outside the A2/Tier1 window, create a new session-gated copy or pause outside-window trading.
```

Do not implement a broad afternoon ban. Earlier round-family analysis already concluded that afternoon weakness was mostly a round-family problem, not proof that all afternoon XAUUSD should be blocked. fileciteturn57file0

### 7.5 Daily loss breaker

A daily loss breaker is necessary, but optional in the sense that it should not be the main quality improvement.

Recommended A3 breaker:

```text
Stage A: observer/logging only.
Stage B: write A3_KILL.txt to block new entries after threshold.
Stage C: optional close-all only after separate owner approval.
```

Suggested thresholds for demo:

```text
Per-lane: 5 consecutive losses = pause lane.
A3 account group: daily closed loss > configured AED cap = block new entries.
Open risk: max 1 open position per lane, max 2 open A3 positions across 933300/933400.
```

Do not rely on this to make a bad signal good. Use it to prevent a bad day from becoming worse.

---

## 8. Static/governance test failures — expected vs must-fix

Because exact failing test names are not committed, this section classifies likely failures based on committed source and artifacts.

### 8.1 Likely expected due to new broker-action artifacts

These are expected **if** old tests still assume every Phase 1 file is dry-run only:

```text
1. Safety audit detects OrderSend in Account3ProfitLockExitManager.mq5.
2. Safety audit detects broker-action flags in A3 Tier1 attachment/status artifacts.
3. Report policy detects owner-authorized demo broker action in status_summary.
4. Static tests detect active A3 933400 broker-action status.
```

These should not be waived silently. They should be fixed by scoping the tests:

```text
Phase1 dry-run/passive files: strict no broker action.
Owner-authorized demo broker-action files: allowed only in explicit allowlist.
Profit-lock manager: allowed only for SLTP modification, not entries.
Canonical Phase 2/live: still blocked.
```

### 8.2 Must-fix code/report issues

These are not acceptable as “expected” failures:

```text
1. status_summary commit/branch mismatch versus reviewed main commit.
2. agent.md or status files claiming reports that are absent or not committed.
3. Missing fresh A3 direct-history/per-magic attribution for the 22-trade loss window.
4. Any test that fails because 933300/933400 state is not consistently documented.
5. Any test that fails because magic 933400 is not in the registry/manifest.
6. Any test that fails because live/real-capital authorization is ambiguous.
```

### 8.3 Required triage artifact

Before another runtime change, add:

```text
PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md
```

Template:

```text
| Test | Failure summary | Classification | Fix |
| --- | --- | --- | --- |
| test_name | ... | EXPECTED_GOVERNANCE_UPDATE | scope allowlist |
| test_name | ... | STALE_ARTIFACT | regenerate report |
| test_name | ... | REAL_CODE_DEFECT | code fix |
```

---

## 9. Runtime risk concerns

### 9.1 A3 is now a live demo experiment with multiple active behaviors

A3 has at least:

```text
933300 improved
933400 Tier1 compat
profit-lock manager
possibly legacy/disabled 933200 state
```

This is acceptable only if every trade is attributable by magic/comment and every report is per-magic.

### 9.2 Profit-lock cannot protect straight-to-SL trades

If A3 trades are losing without reaching +1.25R, the manager will not act. That is expected and not a bug.

### 9.3 Owner override needs continuous clarity

The A3 Tier1 pre-attachment review recommended observer/dry-run first. fileciteturn75file0 Owner later authorized demo broker-action, and `status_summary.json` records that override. fileciteturn77file0

Keep this explicit in every A3 report:

```text
Owner overrode observer-first recommendation for demo broker-action only.
This is not canonical Phase 2.
This is not live/real capital.
```

### 9.4 Main direct push is a governance smell

The user states the commit was pushed directly to `main`, no PR. That is not an automatic rollback reason, but it should trigger a post-merge review artifact and a freeze on further runtime changes until the six test failures are triaged.

---

## 10. Recommended next actions

### Immediate — before any more runtime changes

```text
1. Generate and commit PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md.
2. Regenerate status_summary.json / status_summary.md / status.html from d5dd2de/main.
3. Commit fresh A3 direct-history and per-magic attribution for the 22-trade window.
4. Confirm 933200 has broker-action off and no new 933200 orders after stop time.
5. Confirm 933300 and 933400 open positions, closed PnL, and consecutive-loss counts.
6. Confirm profit-lock startup/action logs and whether it has seen or modified any position.
7. Do not deploy more signal filters yet.
```

### Next evidence packet

Create:

```text
A3_FORWARD_EVIDENCE_PACKET_2026_06_18.md
A3_PER_MAGIC_ATTRIBUTION_2026_06_18.csv
A3_PROFIT_LOCK_COVERAGE_2026_06_18.md
A3_DUPLICATE_FAMILY_EVENTS_2026_06_18.md
A3_SESSION_TREND_SHADOW_REPORT_2026_06_18.md
A3_RETEST_QUALITY_SHADOW_REPORT_2026_06_18.md
```

### Runtime policy for the next 24–48h

```text
933200: keep stopped.
933300: keep active only if per-magic evidence does not show ongoing severe loss cluster.
933400: keep active only as owner-authorized demo validation.
No new EAs.
No new runtime filters.
No live/real capital.
```

### Runtime pause triggers

```text
Pause 933300 if it records 5 consecutive fresh closed losses or PF <0.80 after 20 fresh trades.
Pause 933400 under the same condition.
Pause all A3 new entries if A3 daily closed loss exceeds the configured AED cap.
Pause all A3 new entries if duplicate-family entries recur after mutex evidence.
```

---

## 11. Final go / no-go table

| Item | Verdict |
|---|---|
| Plain lane `933200` stopped | **GO / correct** |
| Keep `933200` stopped | **YES** |
| Improved lane `933300` active | **Conditional GO** |
| Tier1 compat lane `933400` active | **Conditional GO** |
| Profit-lock manager attached/armed | **Conditional GO** |
| Rely on profit-lock to fix low win rate | **NO** |
| Add more runtime signal filters now | **NO-GO** |
| Add shadow reports for trend/session/retest quality | **GO** |
| Add daily breaker as emergency circuit | **GO, but not as main fix** |
| Treat 399/6 test state as acceptable | **NO — triage required** |
| Immediate rollback | **NO, unless 933300/933400 continue loss cluster** |
| Canonical Phase 2 / live capital | **ABSOLUTE NO-GO** |

---

## 12. Bottom line

Stopping `933200` was the right move. The evidence says A3 plain was the failed control lane: it traded outside the A2-style gate, used tighter stops, had heavier cost_R, and lacked the active protections that the improved/Tier1 lanes are supposed to provide.

`933300` and `933400` can remain active **only as tightly monitored demo experiments**, not as canonical evidence. The next improvement should not be another runtime tweak. The next improvement should be **clean attribution**:

```text
Which magic is still losing?
Which sessions are losing?
Which trades are duplicates?
Which trades are trend-against?
Which retests are low quality?
Did profit-lock ever get a chance to act?
```

Once that evidence is committed, signal-quality changes can be proposed as shadow-first policies, not ad hoc patches.
