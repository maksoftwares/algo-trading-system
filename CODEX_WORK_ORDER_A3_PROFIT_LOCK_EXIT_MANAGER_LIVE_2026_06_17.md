# CODEX WORK ORDER — Live profit-lock exit-manager on A3 (1033669), 2026-06-17

Owner: Ali. **Demo only.** Owner decision: deploy the dynamic profit-lock as a **live broker-action
trader on A3 `1033669`** (not shadow). **A2 `1033030` stays untouched as the clean control.** Reviewer
recommended conservative-first; owner approved live on A3.

## Design (non-negotiables)
- **Separate exit-manager EA** — `Account3ProfitLockExitManager.mq5`. It **modifies stops on existing
  positions only**; it does **not** open trades and does **not** edit any entry EA or kernel.
- **Scope locks:** XAUUSD only, demo-server marker, login allowlist = `1033669`, kill-switch file,
  managed-magic allowlist. Refuse init otherwise.
- **Managed magics (allowlist):** start with **933200 (plain) + 933400 (compat)** — lanes with no internal
  exit logic. Exclude **933300 (improved)** unless its internal breakeven/partial stay disabled (avoid two
  things moving the same SL). Configurable input `InpManagedMagicsCsv`.
- **Committed defaults non-executing** (`InpDryRunOnly=true`, `InpManageActionAllowed=false`); owner arms
  via a **local** preset only (like the compat lane). No armed preset committed.

## The rule (conservative rung first)
```text
For each managed open position:
  R          = |entry - original_SL|              (risk distance, fixed at entry)
  unreal_R   = (price - entry)/R   (long)  |  (entry - price)/R  (short)
  ARM at unreal_R >= +1.25R  ->  floor = entry +/- 0.80*R
  Move SL toward profit only: long SL = max(curr_SL, floor); short SL = min(curr_SL, floor)
  NEVER widen risk (SL only ratchets toward profit), NEVER move TP (keep +1.50R)
  Respect SYMBOL_TRADE_STOPS_LEVEL (defer if floor too close to price)
  Idempotent: only modify when it improves the SL
```
Implement the lock as an **SL ratchet** (let the broker close at the floor) — no market-close race.
Lower rungs (`+1.00R→+0.50R`, `+0.75R→+0.25R`) are **inputs, default OFF**; do not enable the +0.75/+0.25
rung now (highest winner-clip risk; winners' avg adverse excursion is 0.47R).

## Step 0 — Quick reconciliation BEFORE arming (analysis, not a shadow week)
Re-run the path replay for the **+1.25R→+0.80R rung only**, on the **deduped** universe, and reconcile vs
the prior `REJECTED` BE/partial result (raw vs deduped basis; trigger depth). Arm **only if** the rung is
net-positive deduped and survives best-day-removed. If it flips negative deduped, that is the signal to
hold — report it, do not arm. (This is hours of analysis, not the shadow you declined.)

## Step 1 — Build + compile
`Account3ProfitLockExitManager.mq5` (+ safe preset `…safe_xauusd.set`). MetaEditor compile **0/0**.
Add static tests: scope locks present, managed-magic allowlist enforced, never-widen invariant, committed
defaults non-executing, TP never modified.

## Step 2 — Arm + attach (owner-gated)
- Profile backup of the A3 terminal first.
- Owner local armed preset (`InpDryRunOnly=false`, `InpManageActionAllowed=true`), kill switch present.
- Startup-log proof: login `1033669`, XAUUSD, managed magics, dry_run/action flags, scope-lock PASS.
- Confirm it only ever modifies SLs on the allowlisted magics; **A2 and all non-allowlisted positions
  untouched**; entry EAs (933200/933300/933400) and their inputs unchanged.
- Report: `A3_PROFIT_LOCK_EXIT_MANAGER_ATTACHMENT_2026_06_17.md` (commit it — not gitignored).

## Step 3 — Measurement (A3-with-lock vs A2-without)
Daily: per managed magic, log each `ARMED` and `LOCK_EXIT` event with the unreal_R at arm, exit_R, and the
**counterfactual** (would the unmanaged trade have hit TP or SL?). Net = profit locked vs **TP-R given up**.
Compare A3 (lock) against A2 (no lock, same breakout strategy) as the control.

## Keep / disarm rule (pre-registered)
Keep it live only if, over the forward fortnight on deduped data, **locked profit saved > winner-R clipped**,
it survives best-day-removed, and it holds across up and down days. If it clips more than it saves, **disarm**
(reversible via the SL-only design + profile backup). Re-check after the first down/range week.

## Boundaries
- Do **not** touch A2 `1033030` or any non-allowlisted position.
- Do **not** edit entry EAs/kernels; the manager only ratchets SLs.
- Do **not** enable the +0.75/+0.25 rung yet; do **not** modify TP or widen any stop.
- Do **not** change canonical Phase 2/3; demo only; no live/real capital.
