# A3 Breakout Tier1 Compat V1

Status: `BUILT_REPO_SIDE_NOT_ATTACHED`

Boundary: demo-only experimental repair lane. This document and the committed source do not authorize canonical Phase 2, live trading, real capital, or any change to currently running MT5 terminals/EAs.

## Purpose

`A3_BREAKOUT_TIER1_COMPAT_V1` is a new copy built after the A3 failure review. It tests whether A3 plain was losing because it took the unfiltered slice that A2 blocks.

The lane is intentionally separate from:

| Existing lane | Why not edit it |
| --- | --- |
| A2 `breakout_retest` | It is the current clean positive benchmark. Do not disturb it. |
| A3 `a3_breakout_plain` | It remains the unfiltered control lane. |
| A3 `a3_breakout_improved` | It remains the stronger guard/exit experiment. |

## Files

| File | Purpose |
| --- | --- |
| `mt5/Experts/Account3BreakoutTier1CompatExecutor.mq5` | New wrapper, magic `933400`, comment `A3_BREAKOUT_TIER1_COMPAT` |
| `mt5/Include/A3BreakoutExecutorBase.mqh` | Shared A3 base extended with opt-in tier1-compatible controls |
| `mt5/Presets/Account3BreakoutTier1CompatExecutor.safe_xauusd.set` | Committed safe preset, dry-run and broker-action disabled |
| `tests/test_a3_breakout_ab_executors.py` | Static tests for source/preset boundaries |

## What Changed Versus A3 Plain

| Behavior | A3 Plain | A3 Tier1 Compat V1 |
| --- | --- | --- |
| Magic | `933200` | `933400` |
| Comment | `A3_BREAKOUT_PLAIN` | `A3_BREAKOUT_TIER1_COMPAT` |
| Logs | `a3_breakout_plain_*` | `a3_breakout_tier1_compat_*` |
| Breakout kernel | `CPhase1BreakoutRetestObserver` | Same kernel |
| Session gate | Off | On by default, server hour `12` through `15` |
| XAU stop-distance floor | Off | On by default |
| Trend guard | Off | Active guard off; shadow-only trend decision on |
| Breakeven / partial | Off | Off |
| Committed preset | Dry-run only | Dry-run only |

## Why These Rules

The A3 failure review found:

| Finding | Repair decision |
| --- | --- |
| A3 plain took non-evening trades that A2 blocked | Copy A2-style server-hour session gate |
| A3 plain had tighter stops and higher cost_R | Copy A2-style XAU stop-distance floor |
| A3 improved blocked all bad signals so far | Shadow trend guard only; do not hard-block yet |
| 0.01 lot makes partial close unable to leave a runner | Keep partial close off |

## Safety Defaults

The committed preset is deliberately non-executing:

```text
InpDryRunOnly=true
InpBrokerActionAllowed=false
InpAllowedAccountLoginsCsv=1033669
InpTargetSymbol=XAUUSD
InpMagicNumber=933400
InpOrderComment=A3_BREAKOUT_TIER1_COMPAT
```

No execution-enabled preset is committed.

## Pre-Attachment Review Result

Claude review file: `A3_TIER1_COMPAT_REVIEW_2026_06_17.md`

Verdict: `PASS_WITH_CONDITIONS`

Interpretation:

| Item | Status |
| --- | --- |
| Repo-side source safety | PASS |
| Breakout kernel unchanged | PASS |
| A2-style session gate | PASS |
| A2-style XAU stop floor | PASS |
| Trend guard shadow-only | PASS |
| Committed preset non-executing | PASS |
| MT5 attachment authorization | NOT AUTHORIZED |
| Broker-action authorization | NOT AUTHORIZED |

Required before any attachment:

1. Separate owner authorization packet approving A3 `933400`.
2. MetaEditor compile proof with 0 errors and 0 warnings.
3. A3 profile backup before attachment.
4. Observer/dry-run attachment first, using a non-executing preset.
5. Startup-log proof for login `1033669`, demo server, magic `933400`, and scope locks.
6. Zero pre-existing `933400` orders/positions baseline.
7. Reconciliation report after attach and kill-switch proof.

## PnL Framing

The current evidence supports a repair direction, not a forecast.

| Estimate | Evidence quality | Result | Correct interpretation |
| --- | --- | ---: | --- |
| Strict A3 replay | Strong for loss avoidance | 0 allowed trades; `-96.39 AED` avoided | The session gate would have blocked the full A3 plain loss cluster. It proves loss avoidance, not profit. |
| A2 live proxy | Useful but tiny sample | 8 trades, 50.00% win rate, `+104.92 AED` | Closest live proxy because A2 uses the gate/floor copied here; still too small for prediction. |
| XAU evening breakout proxy since 2026-06-01 | Indicative only, regime-exposed | 12 trades, 83.33% win rate, `+478.66 AED` | Real fills, but not a direct replay of this new copy and likely flattered by the recent gold regime. |

Do not promote this lane from these numbers alone. The next valid evidence is forward observer/dry-run behavior in the `12-15` server-hour window.

## Review Questions

Ask the reviewer to confirm:

1. Does the lane copy the correct A2-compatible controls without changing the breakout kernel?
2. Should the session gate remain server hour `12-15`, matching A2, for the first comparison?
3. Is the XAU stop-distance floor parity implemented in the right place?
4. Is trend guard correctly shadow-only, not active blocking?
5. Are magic/comment/logs sufficiently separated from A2, A3 plain, and A3 improved?
6. Are the pass/fail criteria below strict enough before attachment?

## Proposed Pass / Fail Criteria

Before any owner-approved attachment, pre-register:

| Criterion | Proposed bar |
| --- | --- |
| Minimum sample | At least 30 closed evening-window trades |
| Duration | At least one fortnight and at least one non-up gold day-set |
| PnL | Net positive |
| Profit factor | At least 1.20 |
| Win rate | At least 45%, and not worse than A2 on overlapping signals |
| Comparison | Same symbol, same lot, same session window, same breakout kernel |
| Trend shadow | Report losers-saved and winners-clipped before active promotion |

## Do Not Do

- Do not edit A2 to test this.
- Do not edit current A3 plain/improved lanes to test this.
- Do not attach this lane without a separate owner-approved runtime packet.
- Do not commit an execution-enabled preset.
- Do not hard-enable trend guard or breakeven/partial in this first copy.
- Do not call this canonical Phase 2 evidence.
