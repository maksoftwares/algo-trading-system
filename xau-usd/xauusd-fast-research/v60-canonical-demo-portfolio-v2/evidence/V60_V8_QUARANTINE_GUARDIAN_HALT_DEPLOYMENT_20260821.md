# V60 V8 Quarantine And Guardian Halt-Only Deployment

Date: 2026-08-21

## Authorization and scope

- Target: Capital.com demo account `1033030`, server `Capital.ComMena-Demo`.
- Symbol: `XAUUSD`.
- Live-account authority remains false.
- No minimum-balance requirement was added.
- No Forex or US500 runtime, state, position, or chart was changed.

## Deployed changes

1. `V8_RETEST_HEALTH` remains registered and observable but is excluded from
   deterministic execution and ML top-ups.
2. The `-100 AED` V60 daily-loss guardian still halts new entries for the rest
   of the Dubai day, but no longer force-closes existing positions for that
   trigger. Source stops, targets, portfolio protection, and hard stops remain
   active.
3. Other guardian triggers retain their prior close-position behavior.
4. The absolute `$420` strategy hard stop was not lowered. The no-V8 ten-year
   raw replay has `$257.96` maximum closed drawdown, and its existing 1.5x
   safety-headroom check requires at least `$386.95`. Shared multi-asset stress
   has not justified a tighter number.

## Exact runtime replay

Period: 2021-01 through 2026-07. Values are fixed `0.01` lot USD-equivalent
historical diagnostics, not profit guarantees.

| Metric | Previous runtime | Deployed policy | Change |
|---|---:|---:|---:|
| Accepted trades | 1,584 | 1,390 | -194 |
| Net P/L | $2,628.49 | $3,603.57 | +$975.08 |
| Profit factor | 1.4897 | 1.7107 | +0.2210 |
| Win rate | 46.53% | 48.49% | +1.96 pp |
| Maximum equity drawdown | $218.55 | $238.28 | +$19.73 |
| Maximum closed drawdown | $203.68 | $223.28 | +$19.60 |
| Trades per eligible weekday | 1.105 | 0.970 | -0.135 |

The deployed replay ended flat, produced no suspension deadlock, recorded 51
guardian locks, and rejected 152 V8 candidates with
`SOURCE_EXECUTION_QUARANTINED`.

## Why the guardian changed

The prior daily-loss action force-closed 91 positions across 52 historical
locks. Those forced exits totaled `-$500.61`; their original source exits would
have totaled `+$610.97`. This does not prove every future recovery should be
held, but it shows the daily guardian was overriding independently tested trade
exits in a materially harmful way. It now stops new risk while preserving the
existing source-managed positions.

## This-week ML diagnostic

Week: 2026-08-17 through 2026-08-21.

| Path | Trades | Wins | Net P/L | Profit factor | Status |
|---|---:|---:|---:|---:|---|
| Actual deterministic execution | 7 | 1 | -$39.95 | 0.287 | Observed |
| Deployed ML top-up behavior | 7 | 1 | -$39.95 | 0.287 | No top-ups fired |
| Post-hoc rank veto at 0.30 | 3 | 1 | -$6.74 | 0.705 | Research only |

The post-hoc veto would have rejected four scored V57 losses totaling about
`$33.21`, while retaining the V57 winner, the V7 loss, and the unscored R1
pullback loss. The threshold was inspected after outcomes and there are only 20
prospective scores in total. It is therefore useful evidence for a separately
preregistered veto experiment, not authorization to deploy an ML filter.

## Verification

- Portfolio and add-on tests: `35 passed`.
- Guardian scope tests: `4 passed`.
- Tick-runtime replay tests: `17 passed`.
- Repository and live-terminal recovery verification: `PASS` across `162`
  manifest files.
- Guardian compile: `0 errors, 0 warnings`.
- Deployed guardian source SHA-256:
  `86cb6fb2bc05f26876e884d89f20534e5754a54bc4f037215c9b9349fefc42eb`.
- Deployed guardian EX5 SHA-256:
  `841574c609942a30039a6f3737f970cb3cb516a73ef33af86d5cb42a1bf9da6c`.
- Deployment parity artifact SHA-256:
  `7c36cea133d95d2b77a4ce984c64e5aacab296b2273f4b705b6895430498d664`.
- Base config SHA-256:
  `ccc8e6ed662afd9ce0f4118865495979e26fa3178edbd5729edca4060823fd09`.

After restart, runtime status reported account `1033030`,
`ACTIVE_DEMO_BROKER_ACTION`, healthy feed and broker long/short checks, eight
execution sources, nine registered sources, V8 quarantined, and
`InpDailyLossStopClosePositions=false`. The existing daily halt was preserved;
it must not be manually cleared and will reset on the next Dubai trading day.

Rollback backup:

`C:\MT5PortableTier1BestEA\MQL5\Files\v60_canonical_demo_v2\deployment_backup_20260821_154700`
