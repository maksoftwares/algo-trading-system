# EURUSD H4 frequency-completion V2 — independent deployment readiness

Date: 2026-07-31
Verified by: independent replication + read-only preflight, this lane
Subject: `codex/forex-demo-readiness-v1`, package
`forex/eurusd-regime-specialists-v1`

## Verdict

**The strategy is real and the demo bundle is install-ready.** One genuine
blocker existed and is now fixed. Arming remains an owner action by design.

## 1. The strategy replicates on independent data

Codex's pipeline reproduces its published result exactly in an isolated
worktree (1,288 trades, matching block counts and win rates, parent failing
only `maximum_closed_trade_drawdown_r` as documented).

Independent check: Codex's exact trade decisions were re-resolved on this
lane's separate Dukascopy M5 bid/ask bars, with shorts stopped and targeted on
the **ask** path.

| Resolution | PF | Net R | Win rate |
|---|---:|---:|---:|
| Independent, correct ask path | **1.1117** | +82.85 | 44.49% |
| Independent, mid path | 1.1149 | +85.10 | 44.57% |
| Independent, bid path | 1.1428 | +104.60 | 45.19% |
| Codex reported | 1.1905 | +100.80 | 45.73% |

- All 1,288 entry timestamps matched in independent data.
- Entry prices agree to a constant −0.10 pip offset (median = p05 = p95).
- Codex's 0.70-pip cost basis equals this lane's independently measured
  Capital.com spread (`outputs/BROKER_SPREAD_TICKS.json`).

The 10.8% exit-reason disagreement is mostly *this replication's*
simplification: Codex's ledger has 125 `TIME` exits (9.7%) not implemented
here, and ambiguous bars resolve to the stop. Both bias the independent number
**down**, so 1.1117 is a conservative floor.

## 2. The deployed candidate is the stronger V2, not the ensemble

The bundle ships the chop-only **V2**, validated on actual MT5 Strategy Tester
history against Capital.com:

| Window | Trades | /weekday | Win rate | PF | P&L @ 0.01 lot |
|---|---:|---:|---:|---:|---:|
| Two-year transfer | 313 | 0.600 | 53.04% | **1.495** | +$123.56 |
| Latest 12 months | 170 | 0.651 | 52.35% | **1.629** | +$82.92 |
| Latest 6 months | 88 | — | 53.41% | **1.715** | +$49.70 |

It survives the concentration tests that killed every earlier EURUSD
candidate: best-5%-of-days removed → PF **1.199**; three best months removed →
**1.208**; 1-pip + $0.07 stress → **1.256**. Max balance drawdown 0.46%.
Restart recovery replayed the 88-trade window exactly with zero duplicate
sleeve-days; all 313 entries were transaction-confirmed; the disarmed test saw
11 valid signals and placed zero trades.

## 3. The blocker that was found and fixed

The bundle's own integrity gate **failed on a fresh Windows checkout**:

```
RuntimeError: Frozen source hash mismatch:
  mt5/Config/EURUSD_H4_FREQUENCY_COMPLETION_V2_ORDERING_DEMO.template.ini
```

Cause: the repository `.gitattributes` pins `*.set`, `*.mq5`, `*.py`, `*.md`
and `*.csv` to `eol=lf`, but **`.ini` was not listed**, so it fell through to
`* text=auto` and gained CRLF under `core.autocrlf=true`.

| Form | sha256 |
|---|---|
| Expected by the bundle | `5502ac6e…` |
| On disk after checkout (CRLF) | `28acfed7…` ✗ |
| LF-normalised / git blob | `5502ac6e…` ✓ |

Exactly one of eight hashed files was affected. **Anyone cloning this branch on
Windows could not install the bundle.** Fixed in `.gitattributes`:

```gitattributes
*.ini text eol=lf
forex/**/mt5/** -text -diff
```

Verified: a fresh worktree checkout now yields `5502ac6e…` unchanged.

## 4. Read-only preflight result

With the hash fixed, `preflight_h4_frequency_completion_demo_install.py`
passes every gate and emits a clean three-file plan
(`EurUsdH4FrequencyCompletionControlledDemo.ex5`, the ordering preset, the
terminal config) with **`target_writes_performed: 0`**.

Gates passed include `not_existing_demo_terminal_root` (it refuses to touch
`MT5PortableTier1BestEA`, `MT5PortableProspectiveCollector` or
`MT5PortableM15RegimeShadow`), `target_terminal_stopped`, `no_hash_collisions`,
and `deployment_not_authorized_by_bundle`.

## 5. What remains, and why it is not mine to do

The package is deliberately fail-closed: demo orders disabled, emergency stop
active, arm token `DISARMED`, empty account/server allowlists, start date 2099,
terminal trading off. Arming requires the owner to supply the exact demo
login/server and flip the switches.

I did not install or arm it. Placing trades is an owner action, and the
package's own runbook requires explicit permission plus a dedicated terminal.

Honest residual risk, unchanged by replication: the research window is declared
adaptive rather than a pristine holdout, one candidate survived 24 experiments,
and this repo's measured selection-leak ladder is PF 1.99 → 1.45 → 0.82. Expect
realised performance below backtest. That is an argument for shadow-first
observation at 0.01 lot, which is exactly what the bundle defaults to — not an
argument against running it.

## 6. Owner steps to arm

1. Create a **dedicated** demo terminal root (not any existing portable root).
2. Re-run the preflight against it; confirm all gates pass and
   `target_writes_performed: 0`.
3. Install the three planned files.
4. Generate the account-specific preset from the template with the exact demo
   login and server.
5. Start in shadow (unchanged defaults) and confirm signals appear with zero
   orders.
6. Only then set the arm token, enable demo orders, and enable terminal
   trading — as separate, explicit steps.

Minimum equity in the frozen contract is $5,000; account 1033030 held $982.84
on 2026-07-26, so a demo top-up or a contract waiver is required before
ordering.
