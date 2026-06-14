# CODEX FOLLOW-UP — A2 session-gate timezone check + equity-guardian options (2026-06-14)

Authority: follow-up to `CODEX_WORK_ORDER_TIER1_BREAKOUT_SOLO_ACTIVATION_2026_06_14.md`
and `TIER1_BREAKOUT_SOLO_ACTIVATION_REPORT_2026_06_14.md`. Owner: Ali, 2026-06-14.

**Boundaries:** Demo only. A2 (`1033030` / `C:\MT5PortableTier1BestEA`) only; A1 (`1025742`)
and A3 (`1033669`) untouched. **This is diagnostic + options only — do NOT change the live
preset, hours, or attach any EA. Report findings and recommended changes for owner approval.**

Context to check against (from analysis): the gold breakout edge is the **evening, Dubai
16:00–20:00** (+641 AED, 62% win). The **afternoon, Dubai 12:00–16:00, is the only losing
session** (−53 AED, 27% win). The A2 preset sets `InpTradeSessionStartHour=12`,
`InpTradeSessionEndHour=15`, and the EA evaluates the gate using `TimeCurrent()` (broker
server time). This repo has a prior server-vs-Dubai timezone defect (session-extreme L5.2),
so this must be confirmed explicitly, not assumed.

## TA — Confirm the session gate equals the Dubai evening
1. Determine the broker server UTC offset on the A2 terminal (e.g., compare `TimeCurrent()`
   vs `TimeGMT()` live, or from the terminal/server clock). State it plainly.
2. Compute the exact **Dubai** clock window that `12:00–15:00` server time corresponds to.
3. List **every** A2 trade (account `1033030`, magic `920101`) with entry timestamp in
   server, UTC, and Dubai. State how many fall inside Dubai 16:00–20:00 (evening, the edge)
   vs inside Dubai 12:00–16:00 (afternoon, the loser).
4. Verdict: is the gate trading the evening edge, yes/no? If it is drifting off the evening,
   give the corrected `InpTradeSessionStartHour`/`EndHour` (in the EA's server-time reference)
   that would map to **Dubai 16:00–20:00** — as a recommendation only, do not apply it.

## TB — Equity-guardian options memo for A2
A2 currently has no account-level downside protection (only per-trade SL + the entry-blocking
kill switch). Lay out the concrete options to add an account-level loss/equity stop, each with
what it protects against, its cost/tradeoff, and whether it breaks the "one EA, one chart"
lane:
1. Attach `AccountEquityGuardianShadow.mq5` as a second chart/EA on A2 (note its R1 flatten /
   R2 giveback / weekly-breaker thresholds and any kill-drill prerequisite).
2. Any account-level guard the `Phase2ExperimentalDemoExecutor` already supports via inputs
   (daily realized-loss entry stop, equity floor, max positions) — state which inputs exist
   and what values would apply, since this needs no second EA.
3. An external watchdog/script that flattens/halts A2 on an equity threshold.

End with a one-line recommendation. **Attach nothing and change nothing** — owner decides.

## Reporting
Write `TIER1_SESSION_AND_GUARDIAN_FOLLOWUP_REPORT_2026_06_14.md` with raw command output for
TA (server offset, the trade-time table, the verdict) and the TB options table. No live
changes; list any recommended change as a proposal pending owner sign-off.
