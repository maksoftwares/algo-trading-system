# CODEX WORK ORDER — A1 daily +100 profit-floor guardian (LIVE demo), 2026-06-18

Owner: Ali. **Demo only.** Account **A1 `1025742`** (standard demo terminal). Owner decision: deploy a
**live broker-action** account-level daily profit-floor guardian. On floor trigger it **halts new entries
AND closes all open A1 positions** ("true lock"). This is an owner-authorized live demo deployment.

## Owner-acknowledged expectations (state in the report, do not re-litigate)
- This **caps the bleed; it does not make A1 profitable** (sim over June 1–18: −2,796 → ≈ −1,991).
- The fixed +100 floor **clips some recovery days** (e.g. a day that dipped through +100 then would have
  run to +325 gets locked at ~+100). Accepted.
- "Close all" **closes the protected breakout core (chart03/06) too** on a trigger day. Accepted by owner.
- Locked result ≈ +100 **minus closing slippage** (market closes on a reversing tape).

## Design (non-negotiables)
- **Separate guardian EA** — `Account1DailyProfitFloorGuardian.mq5`. It **never opens trades**; it only
  monitors account P&L and, on trigger, **closes** open A1 positions (`TRADE_ACTION_DEAL`, close-only) and
  raises an entry-halt. Do **not** edit any A1 entry EA.
- **Account-level, all symbols.** A1 trades XAU/EUR/GBP/JPY; the floor is account-wide, so the guardian is
  **not** symbol-locked — but it is hard-locked to **login 1025742** and **demo server** only. Refuse init otherwise.
- **Committed defaults non-executing** (`InpDryRunOnly=true`, `InpCloseActionAllowed=false`): in dry-run it
  logs `WOULD_ARM` / `WOULD_LOCK` / `WOULD_CLOSE` and changes nothing. Owner arms via a **local** preset only.
- Master **kill switch** for the guardian itself; reversible by removing the guardian + the halt flag.

## Floor logic (equity-based, Dubai day)
```text
day_start_equity = AccountInfoDouble(ACCOUNT_EQUITY) captured at first tick of each Dubai day (persisted)
day_pnl          = equity_now - day_start_equity          # includes floating — true "are we up +100 now"
FLOOR            = +100 AED   (InpDailyFloorAed, owner-set)

ARM when day_pnl >= FLOOR      (latched for the day)
TRIGGER when armed AND day_pnl <= FLOOR     # fell back down to the floor
On TRIGGER:
   1. close ALL open A1 positions (close-only DEAL, scoped to login 1025742)
   2. raise entry-halt for the rest of the Dubai day (see below)
   3. log LOCKED with locked_realized, positions_closed, slippage
Above the floor it runs free (no cap) — only the downward cross to +100 triggers.
Reset ARM / TRIGGER / day_start_equity at the next Dubai-day boundary.
```
- **Dubai day** via the repo's established offset (`TimeGMT()+240`). Persist `{date, day_start_equity, armed,
  locked}` to a state file; on restart mid-day, restore it (if `locked` today → stay locked).

## Entry-halt mechanism (don't edit entry EAs)
Primary: after a lock, run a **keep-flat guard** — close any A1 position that appears for the rest of the
Dubai day (guarantees the lock with no dependency on the entry EAs). Secondary (to avoid open/close churn +
spread bleed): if the A1 entry EAs honor a kill/halt file, **write that halt file** so they stop entering;
Codex must first **verify** how the A1 entry EAs read their kill switch (entry-time vs init) and prefer the
flag-halt, with keep-flat as the hard backstop. Remove the halt flag at the next Dubai day.

## Optional (the data-favored complement — default OFF)
Add `InpDailyLossStopEnabled=false`, `InpDailyLossStopAed=-150`. When enabled, the same close-all+halt fires
if `day_pnl <= InpDailyLossStopAed`. The sim showed a daily loss stop was ~2× more valuable than the profit
floor (the −2,456 June-12 day is 88% of A1's loss). **Leave it OFF** per owner's current ask; it's wired and
available to flip on later.

## Safety
- Hard login-lock `1025742`; demo-server marker; guardian kill switch; close-only (never opens, never widens).
- `InpDailyFloorAed` and the loss-stop are owner inputs; the +100 is owner-chosen (not fitted).
- Idempotent + fail-closed: if it cannot confirm a close succeeded, retry then alert; never assume.
- Reversible: removing the guardian + halt flag restores normal A1; it makes no permanent config edits.

## Measurement / logging
Per Dubai day: `day_start_equity`, intraday peak day_pnl, armed time, trigger time, positions closed,
locked_realized, and the **counterfactual** (what the day would have closed with no guardian) so we can
score whether the floor helped. Append-only event log + daily summary.

## Tests
Scope-lock (login/demo) enforced; never opens a position; close-only DEAL; arm/trigger math on synthetic
equity paths (incl. dip-through-floor, run-above-then-return, never-reach-100, gap-through-floor); Dubai-day
reset; restart restores locked/armed state; keep-flat closes a re-opened position; committed defaults
non-executing; loss-stop fires only when enabled.

## Attach (owner-gated) + report
Profile backup → 0/0 compile → owner local armed preset → startup-log proof (login 1025742, dry_run/close
flags, kill switch) → confirm guardian opens nothing at attach. Commit
`A1_DAILY_PROFIT_FLOOR_GUARDIAN_ATTACHMENT_2026_06_18.md` (not gitignored). **A2 and A3 untouched.**

## Boundaries
Demo only. A1 `1025742` only. Do not edit A1 entry EAs, A2, or A3. The guardian only closes A1 positions and
halts A1 entries on its own daily-floor logic. No canonical Phase 2/3 change; no live/real capital.
