# CODEX WORK ORDER — Activate the Solo Breakout (Tier-1 "Best EA") on its own account + take over MT5 terminal management (2026-06-14)

## 0. Read this first — target and assumption check

**Goal in one line:** the proven money-maker — `breakout_retest` on XAUUSD — has been
running *diluted* inside the multi-EA account A1 and its profit got swallowed by the losers
sitting next to it. Run it **clean, on its own account**, so its edge lands as real account
PnL.

**Target terminal/account (the one currently configured to run ONE EA only):**
- Account: **A2 demo, login `1033030`, `Capital.ComMena-Demo`, AED.**
- Terminal (portable root): **`C:\MT5PortableTier1BestEA`** (the "Tier-1 Best EA" lane).
- EA: `Phase2ExperimentalDemoExecutor.mq5` configured as candidate `breakout_retest`,
  symbol XAUUSD only, magic **920101**.

> **ASSUMPTION CHECK (do this before anything else):** This work order assumes the
> single-EA terminal is account `1033030` / `C:\MT5PortableTier1BestEA`. If the solo-EA
> terminal you actually observe is a different login or path, **STOP and confirm with the
> owner** before any attach/arm action. Do not deploy to A1 (`1025742`) or A3 (`1033669`).

## 1. Owner authorization

Owner: **Ali (mohdalikhans97.com@gmail.com)**, dated **2026-06-14**. Demo capital only.

This authorizes:
- Verifying the live state of the three terminals/accounts (read-only inspection).
- Attaching / confirming `breakout_retest` (XAUUSD M5, magic 920101) on the A2 terminal
  (`1033030`) using the existing owner-authorized **local** preset, and arming broker action
  on **demo** so the EA actually trades on its own account.

This does **NOT** authorize:
- Any change to A1 (`1025742`) or A3 (`1033669`) — their EAs, presets, magics, attachments.
- Any change to `breakout_retest` entry / stop / take-profit / session logic. The winner is
  **frozen** — isolate it, do not "improve" it in this work order.
- Adding any non-XAUUSD symbol to this lane (FX breakout loses money — see §3).
- Deploying the chop-filter or the evening sizing-ladder (those remain **shadow-only**, §7).
- Committing any execution-enabled preset to the repo (arming is via local/private `.set`).

## 2. Why we are doing this (findings to carry over — full context)

From two weeks of broker data (2026-06-01 → 06-13) plus source review:

1. **`breakout_retest` on XAUUSD is the single best performer.** Magic 920101, 91 closed
   trades (one per signal), **+837 AED**, ~46% win rate. Its edge is concentrated in the
   active **evening** session: 26 trades, **62% win rate, +641 AED**, mostly take-profit
   exits, not stop-outs.

2. **It has been running inside the kitchen-sink account A1 (`1025742`)**, shoulder-to-
   shoulder with the losing strategies (round-retest family, session-extreme, and the EA's
   own FX trades). In that shared account the winner was **cancelled out**: A1's two-week net
   was **−1,919 AED** despite the gold breakout making +837. The edge never showed up as
   account profit because it shared a pot with the bleeders.

3. **The same `breakout_retest` EA loses on FX.** EUR/GBP/JPY breakout = **−1,680 AED** over
   261 trades (wrong market for a momentum-breakout entry). **This lane must stay XAUUSD-only.**

4. **The isolated terminal to fix this already exists but appears not to be live.** The
   `C:\MT5PortableTier1BestEA` lane (A2, `1033030`) was created 2026-06-12 — source deployed,
   compiled (0 errors), launch started — but its own report shows **"charts attached by
   Codex: False"**, and there is **no A2 trade ledger** in the repo. So as far as the records
   show, the clean breakout deployment was staged but **never switched on**. Activating it is
   the highest-value, lowest-effort action available.

5. **Session profile of the gold breakout (context only — deploy AS-IS, do not retune here):**
   Evening 16:00–20:00 = +641 (62% WR, best); Night 20:00–06:00 = +194 (43%); Morning
   06:00–12:00 = +55 (39%); **Afternoon 12:00–16:00 = −53 (27%, the only losing session).**
   Whether to adjust the session gate is a *separate* shadow study (§7), not part of this
   activation.

6. **Account roles after this work order:** A1 (`1025742`) = legacy/kitchen-sink control,
   untouched; **A2 (`1033030`) = the isolated proven edge — solo `breakout_retest` XAUUSD**;
   A3 (`1033669`) = round-retest repair lane (EA-T1 + EA-T2), untouched.

## 3. Global boundaries (repeat in every report)

- Demo only. No live/real account. Canonical Phase 2 status unchanged.
- A2 (`1033030`) only. A1 (`1025742`) and A3 (`1033669`) untouched — paste `git status` /
  process checks proving no modification to them.
- XAUUSD only on this lane. The qualified-symbols / account-login allowlist must restrict to
  XAUUSD and login `1033030`. Do not widen.
- Committed source defaults stay non-executing (`InpDryRunOnly=true`,
  `InpBrokerActionAllowed=false`). Arming happens only via the **local, uncommitted** owner
  preset in the A2 terminal.
- Do not edit `breakout_retest` entry/stop/TP/session logic, magic 920101, or guard logic.
- Confirm the account equity guard (Account Equity Guardian / risk guard) and the kill-switch
  file mechanism are present and functional on this terminal before/after arming.

## 4. Tasks

### T1 — Inventory and verify current state (read-only, before any change)
1. Enumerate all running MT5 terminals/processes and, for each, the login, server, and the
   EA(s) + symbols attached. Produce a table: terminal path → login → EA(s) → symbol(s) →
   armed? (dry-run / broker-action flags from startup logs).
2. Explicitly confirm: A1 (`1025742`) = many EAs; A3 (`1033669`) = exactly two
   (`Account3RoundRetestGuardedExecutor` 933000 + `Account3RoundRetestStructuredExecutor`
   933100); and the **single-EA** terminal = `1033030` / `C:\MT5PortableTier1BestEA`.
3. For A2: report whether `breakout_retest` is currently attached and trading, the last
   trade/heartbeat timestamp (if any), and the current value of `InpDryRunOnly` /
   `InpBrokerActionAllowed`. **This answers "is the best EA actually running separately?" —
   state it plainly.**

### T2 — Activate the solo breakout on A2 (only if T1 confirms it is not already live)
1. Apply the existing owner-authorized local preset
   `Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set`
   (or recreate an identical local preset if absent), changing **only** the arming flags:
   `InpDryRunOnly=false`, `InpBrokerActionAllowed=true`. All strategy parameters (entry, stop,
   TP, session gate, magic 920101, lot) stay exactly as the frozen breakout config.
2. Confirm `InpTargetSymbol`/qualified-symbols = XAUUSD only and the account-login allowlist =
   `1033030` only. Confirm the server marker check still requires the demo marker and refuses
   live/real.
3. Attach `breakout_retest` to **XAUUSD M5** on the A2 terminal and confirm via startup-log
   rows: account login `1033030`, demo server, symbol XAUUSD, magic 920101,
   `InpDryRunOnly=false`, `InpBrokerActionAllowed=true`, and an `ATTACHED`/ready status (not
   `INIT_FAILED`). Do not place manual test orders — let it run on its own cadence.
4. Confirm the account equity guard is armed for A2 and the kill-switch file mechanism halts
   this EA if present.

### T3 — Confirm scope and isolation
- Paste `git status` and process/terminal checks proving A1 and A3 are unchanged and that no
  execution-enabled preset was committed.
- Confirm no orders/positions on magic 920101 / account `1033030` existed before this attach
  (record the pre-attach baseline).

### T4 — Take over ongoing terminal management
- Stand up monitoring for A2: heartbeat lane, a per-session PnL ledger (Morning/Afternoon/
  Evening/Night, Dubai), and an entry in the existing weekly review packet covering all three
  accounts (A1 control, A2 solo breakout, A3 repair).
- Maintain the freeze discipline: nothing on any account changes mid-week; changes land in
  owner-authorized weekend maintenance windows with a packet.
- Keep a clear kill/pause procedure documented (kill-switch file + flipping the local preset's
  `InpBrokerActionAllowed` back to false and re-attaching stops new orders; open positions are
  managed manually).

## 5. Reporting

Write `TIER1_BREAKOUT_SOLO_ACTIVATION_REPORT_2026_06_14.md` with **raw command/terminal output**
for every check (same standard as the A3 arm-and-attach and T0/T12 reverify reports — actual
logs, file paths, timestamps in UTC and Dubai, not summaries). Include:
- The T1 terminal inventory table and the plain-language answer to "was the best EA already
  running separately, yes/no."
- Before/after of the two arming flags only, with a diff against the frozen preset proving no
  other parameter changed.
- The startup-log evidence of the live A2 attach.
- A short "How to pause/stop" section.

## 6. Acceptance criteria
- A2 (`1033030`) is confirmed running `breakout_retest` XAUUSD M5, magic 920101, armed on
  demo, isolated (no other EA on that terminal), with equity guard + kill switch functional.
- A1 and A3 provably unchanged.
- Report delivered with raw evidence. No committed execution-enabled preset.

## 7. Out of scope / explicitly NOT now (future shadow research only)
- **Chop-filter (W5):** breakout's one real weakness is two-sided chop evenings (e.g., the
  06-12 chop session, −179 on gold). A chop/pause gate is a future *shadow* study — do not
  wire it into the live entry now.
- **Evening sizing-ladder (W7):** scaling 1.5×/2× in the proven evening window is a future
  *shadow* study behind a multi-week evidence bar — do not change lot sizing now.
- **Session-gate retune:** the session breakdown in §2.5 is context, not an instruction; any
  change to which sessions trade is a separate pre-registered shadow study, not part of this
  activation.
- Any change to A3's round-retest lanes or A1.

---

*Prepared from the 2026-06-14 analysis session. Demo only. The single instruction that matters:
run the EA we already know works, on its own account, unchanged — and confirm it is actually
trading.*
