# CODEX WORK ORDER — A3 (1033669) two-lane breakout A/B, LIVE demo (2026-06-16)

Owner: Ali (mohdalikhans97.com@gmail.com), 2026-06-16. **Demo only.** Account A3 `1033669`,
Capital.ComMena-Demo, AED, XAUUSD only.

## Owner decision (recorded)
1. **Drop the two round-retest lanes** on A3 (they are the verified −1,382 drag). Stop placing round
   orders.
2. **Run only the two breakout lanes** live, each magic-tagged and measured separately, so A3 is a
   clean A/B: does the improved breakout beat plain breakout?

This is an owner-authorized live demo deployment that overrides the "observer-only this week" stance.

## Why this design
Verified deduped real-fill evidence: breakout core **+1,059** (robust — survives best-2-days-removed
at +506) is the only durable edge; round family **−1,382** is the drag. So we keep the winner, remove
the loser, and A3 runs a head-to-head of the breakout against an improved version of itself.

| Lane | Magic | Strategy | Role |
|---|---|---|---|
| A | **933200** | plain breakout entry (proven edge) | Control — the known edge (mirrors A2's signals) |
| B | **933300** | breakout + improvements (treatment) | The test: does adding the guards beat plain breakout? |

Lane B "improvements" = the breakout entry PLUS: (a) dynamic trend-alignment guard (skip signals
against the H1/H4 trend), and (b) exit protection — move stop to breakeven at +0.5R **and** take
partial at +1.0R (remainder runs to target). Unproven; this lane is an experiment, not a promotion.

## Round shutdown (do this first)
- **Disarm EA-T1 (933000) and EA-T2 (933100) on A3** — no new round orders. Set non-executing
  (`InpDryRunOnly=true` / disarm preset) or remove from charts.
- Any **currently-open** round position: it already carries a protective stop — let it wind down to
  its existing SL/TP, or flatten at owner discretion. Either way there is no uncapped risk.
- Record **final round P&L at shutdown** per magic, then confirm zero open round positions.

## Build / deploy (the two breakout lanes)
- **Lane A:** deploy the breakout entry on A3 XAUUSD M5, **new magic 933200**, comment
  `A3_BREAKOUT_PLAIN`. Reuse the existing breakout executor logic; **do not modify the
  entry/stop/TP kernel.**
- **Lane B:** build `Account3BreakoutImprovedExecutor.mq5` (or equivalent), **new magic 933300**,
  comment `A3_BREAKOUT_IMPROVED`: the **same** breakout entry kernel (unchanged) + the trend-align
  guard + the BE/partial exit logic above, all as inputs.

## Mandatory guardrails (both lanes)
- XAUUSD only; double scope-lock (`_Symbol`/`InpTargetSymbol`), demo-server marker, login allowlist
  = `1033669` only, magic-band check, kill-switch file. **Committed defaults non-executing**
  (`InpDryRunOnly=true`, `InpBrokerActionAllowed=false`); arming only via local owner preset.
- Fixed **0.01 lot**, **max 1 open position per magic**, min seconds between orders.
- A1 (`1025742`) and A2 (`1033030`) **untouched** — prove with `git status` and process checks.

## Measurement (the whole point)
- Per **magic**, daily: trades, win rate, net PnL, deduped where the two lanes co-fire, plus MFE/MAE.
- The single question that matters: **Lane B vs Lane A — do the improvements (trend guard + BE/partial
  exits) net better than plain breakout?** Report the net, not just give-back counts.
- Watch the curve-fit cost flagged in the plan: winners' avg adverse excursion is **0.46R**, just under
  the 0.5R breakeven trigger, so Lane B **will clip some winners** — the verdict must be losers-saved
  minus winners-clipped.
- Feed both lanes into the nightly deduped real-fill scan and the weekly tracker.

## Reporting
`A3_BREAKOUT_AB_DEPLOYMENT_REPORT_2026_06_16.md`: (1) round shutdown confirmation — EA-T1/EA-T2
disarmed, final round P&L, zero open round positions; (2) startup rows per breakout magic (login
1033669, armed flags, scope-lock pass, zero pre-existing orders on 933200/933300); (3) the build diff
for Lane B proving **only** the guard + exit were added and the entry kernel is byte-for-byte the
breakout kernel; (4) the per-magic measurement template. Raw terminal/log evidence appended. Confirm
A1/A2 unchanged.

## Boundaries
Demo only. Round lanes (933000/933100) disabled on A3. No change to A1, A2, or the breakout
entry/stop/TP kernel. EA-T3 band reframed: 933200 = plain breakout, 933300 = breakout-improved.
