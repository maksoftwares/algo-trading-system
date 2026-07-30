# EURUSD prospective multi-symbol collector v1

This package collects new, untouched EURUSD and cross-pair observations for the
next causal strategy-development stage. It is an observer, not a trading
strategy.

The collector:

- runs only in MetaTrader 5 Strategy Tester or on a demo account;
- must be attached to the exact configured EURUSD symbol on M5;
- contains no trade library, order function, or position-management path;
- starts with a latch and never backfills the bar that existed at startup;
- captures only the just-completed native M5 interval;
- uses `CopyTicksRange` independently for every configured symbol;
- records missing symbols and missing ticks instead of forward-filling them;
- writes raw quote aggregates, environment metadata, and heartbeats to the
  terminal Common Files directory;
- treats Strategy Tester output as smoke-test evidence only; and
- refuses live observations before the frozen forward boundary
  `2026.08.01 00:00` UTC.

The default source list is:

`EURUSD,EURGBP,EURJPY,GBPUSD,USDJPY,GBPJPY,DOLLARIDXUSD,USTBONDTRUSD`

The last two names are optional broker feeds. A broker using suffixes or
different index names must receive an edited, frozen preset before collection.
Unavailable sources remain explicit `SYMBOL_UNAVAILABLE` rows.

## Files written

The safe preset writes three CSV files under the MT5 Common Files directory:

- `EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv`
- `EURUSD_PROSPECTIVE_M5_ENVIRONMENT_V1.csv`
- `EURUSD_PROSPECTIVE_M5_HEARTBEAT_V1.csv`

The feature ledger has one row per source symbol and completed EURUSD M5
interval. It records first/last timestamps, bid and ask OHLC, quote counts, and
spread statistics. It does not create outcome labels or trade decisions.

## Operating boundary

This component does not improve the current backtest and does not prove a
daily-frequency edge. It creates the first genuinely untouched evidence that
can support or reject a future specialist. The validated H4 strategy remains a
separate protected sleeve.

See `PROSPECTIVE_DATA_PROTOCOL.md` for the frozen evidence and admission rules.

## Unattended demo-shadow operations

`scripts/run_live_forward_cycle.ps1` verifies the deployed expert, preset, and
terminal configuration by SHA-256, restarts only the exact collector terminal
when necessary, audits data freshness, and runs the forward learner without any
order path. Daily raw-ledger snapshots are checksum-verified, made read-only,
and the decision ledger is append-only.

`scripts/install_live_operations_tasks.ps1` installs two limited interactive
Windows tasks:

- `Codex-EURUSD-Prospective-Health` every five minutes; and
- `Codex-EURUSD-Forward-Learner` at 18:10 Dubai / 14:10 UTC daily.

The terminal configuration continues to enforce `AllowLiveTrading=0` and
`AllowDllImport=0`. See `LIVE_OPERATIONS_DEPLOYMENT_2026_07_30.md` for the
verified deployment receipt.

## Forward residual-regime campaign

`run_forward_residual_regime_specialist.py` evaluates one forward-only,
20:00 UTC opportunity on weekdays not owned by the protected M15 portfolio or
the frozen daily learner. It separates those opportunities into five causal
cross-pair regimes and allows each regime-side to learn only from its own prior
resolved observations.

The campaign was frozen before the August evidence floor with zero eligible
feature rows. It has no order path and cannot authorize demo trading.
`scripts/run_forward_residual_cycle.ps1` runs the append-only evaluator after
the six-hour outcome window, and `scripts/install_forward_residual_task.ps1`
installs the limited daily 06:15 Dubai / 02:15 UTC task. See
`EURUSD_FORWARD_RESIDUAL_REGIME_PROTOCOL.md` for the admission boundary and
`EURUSD_FORWARD_RESIDUAL_REGIME_DEPLOYMENT_2026_07_30.md` for the verified
prestart deployment receipt.

## Pre-outcome residual signal publication

`run_forward_residual_live_signal_publisher.py` publishes the frozen residual
decision from 20:01 through 20:10 UTC, before its six-hour outcome exists. It
uses only completed prospective bars and prior terminal residual outcomes.
Missing context or a late start becomes immutable cash; historical backfill and
manual as-of clocks are prohibited.

`scripts/install_forward_residual_live_signal_task.ps1` installs the limited
00:03 Dubai / 20:03 UTC task. The publisher has no order path. See
`EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_PROTOCOL.md` for the contract and
`EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_DEPLOYMENT_2026_07_30.md` for the
prestart deployment receipt.

## Read-only MT5 execution receipts

`run_forward_residual_mt5_shadow_bridge.py` reads the immutable pre-outcome
signal and captures the actual bid/ask from the exact Capital.com demo terminal
within two minutes. It records a 0.01-lot would-enter receipt with the frozen
8/12-pip geometry. Late signals become permanent cash.

The bridge has no order-check, order-send, or position-mutation path.
`scripts/install_forward_residual_mt5_shadow_task.ps1` installs the limited
00:04 Dubai / 20:04 UTC task. See
`EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_PROTOCOL.md` and
`EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_DEPLOYMENT_2026_07_30.md`.

## Raw-tick live outcomes and selection parity

`run_forward_residual_live_outcome_adjudicator.py` preserves and hashes raw
broker ticks from the captured MT5 quote, resolves the frozen stop/target/hold
path, and compares the pre-outcome selection with the later terminal research
decision. Ambiguous entry ticks and missing paths are invalid, never imputed.
Friday 20:00 receipts are non-evaluable cash because the hold crosses the
weekly close.

`scripts/install_forward_residual_live_outcome_task.ps1` installs the limited
06:20 Dubai / 02:20 UTC task. See
`EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_PROTOCOL.md` and
`EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_DEPLOYMENT_2026_07_30.md`.
