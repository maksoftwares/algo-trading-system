# A1/A2 XAU 920101 Evening Core Forward V0 Spec - 2026-06-20

Status: `RELOCKED_AFTER_REVIEW`

Boundary: this is an offline forward-test specification only. It does not authorize or perform any MT5 terminal, EA, preset, chart, order, position, profile, or broker setting change. A3 remains paused.

## Source Evidence

Primary reconciliation report:

`xau-usd/xauusd-phase1/outputs/reports/XAU_920101_EVENING_CORE_RECONCILIATION_2026_06_20.md`

The profitable core is attributed to the A1 standard experimental demo export, not to the A2 direct Tier-1 account history.

| Evidence slice | Account/source | Rows | Wins | Losses | Win rate | PnL AED | PF |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `920101` / `XAUUSD` / Dubai evening | A1 `1025742` primary export | 27 | 18 | 9 | 66.67% | 701.86 | 3.7477 |
| breakout_retest / XAUUSD / Dubai evening | A2 `1033030` direct history | 12 | 4 | 8 | 33.33% | -55.09 | 0.8100 |

The A1 core remains positive after removing the top 3 winning trades, but it is still the best selected cell from many tested cells and is therefore only eligible for a small forward test, not validation or scaling. The A2 clean account is negative over its direct history, so the forward test must run both accounts in parallel and require both-account confirmation before any promotion.

Current runtime identity check:

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_RULE_IDENTITY_RECONCILIATION_2026_06_20.md`

That check currently reports `MISMATCH_REQUIRES_MAINTENANCE_REPORT`: the active A2 XAU breakout chart is found, while the inspected A1 standard profile does not currently show an active `Phase2ExperimentalDemoExecutor` XAU chart for account `1025742`. This spec therefore requires a future owner-approved maintenance report before runtime.

## Hypothesis

If A1 and A2 both run the exact same `breakout_retest` XAUUSD lane represented by derived magic `920101`, with broker-action restricted to the Dubai evening window, then the combined forward book will remain net-positive on new demo data while avoiding the concentrated losses created by weaker symbols, sessions, duplicate families, and A3 repair lanes.

A1 is the in-sample promising account. A2 is the clean independent check. A promotion cannot be based on A1 alone.

## Exact Runtime Scope If Later Approved

No runtime change is authorized by this document. If the owner separately approves a maintenance window, the forward test must use exactly this scope:

| Field | Locked value |
| --- | --- |
| Accounts | A1 standard demo `1025742` and A2 clean Tier-1 demo `1033030` |
| Server | `Capital.ComMena-Demo` only |
| Symbol | `XAUUSD` only |
| Candidate | `breakout_retest` only |
| Magic | `920101` only |
| Lot | `0.01` fixed |
| Broker-action window | Dubai `16:00:00` through `19:59:59` only |
| Blocked windows | Dubai morning, afternoon, and night |
| Duplicate rule | one same-family XAU breakout trade per duplicate event |
| Daily profit lock | stop new entries after each account reaches `+100 AED` Dubai-day PnL |
| Daily loss stop | stop new entries after each account reaches `-100 AED` Dubai-day PnL |
| Round-family lanes | broker-action disabled |
| A3 repair lane | paused / observer-only |
| A2 clean account | active parallel confirmation, not merely a passive control |
| Canonical Phase 2 | unchanged; this is not a PASS |
| Live/real capital | not authorized |

## Rule-Identity Gate

The forward test must not start until an owner-approved maintenance report proves the A1 and A2 chart rules are identical.

Required proof:

- A1 has an active `Phase2ExperimentalDemoExecutor` XAUUSD chart on account `1025742`.
- A2 has an active `Phase2ExperimentalDemoExecutor` XAUUSD chart on account `1033030`.
- Both accounts use `breakout_retest`, derived magic `920101`, fixed lot `0.01`, and Dubai evening-only broker action.
- Both accounts block Dubai morning, afternoon, and night.
- Both accounts log startup, signal, order, and daily-lock evidence.
- Any before/after profile changes are listed in the maintenance report.

## Daily Loss Stop Calibration

Calibration source:

`xau-usd/xauusd-phase1/outputs/reports/XAU_920101_EVENING_CORE_RECONCILIATION_TRADES_2026_06_20.csv`

The historical A1 evening-core sequence did not contain any profitable day that first dipped below `-100 AED`. The only day that would have hit `-100 AED` was 2026-06-12, which ended at `-123.05 AED` after four losses. Therefore `-100 AED` is accepted as the initial demo-only daily loss stop.

The A1 evening-core average win is `+53.18 AED`; average loss is `-28.38 AED`. Therefore:

- `+100 AED` daily profit lock is about `1.9` average wins.
- `-100 AED` daily loss stop is about `3.5` average losses.
- `-150 AED` early cumulative kill is about `5.3` average losses.

These AED values are valid only for `0.01` fixed lot. If lot size changes later, the stop/lock must be re-expressed in R or average-loss units before use.

| Date | Trades | Final PnL AED | Min running PnL AED | Would hit -100 |
| --- | ---: | ---: | ---: | --- |
| 2026-06-02 | 1 | 65.72 | 65.72 | false |
| 2026-06-03 | 4 | 104.44 | -24.51 | false |
| 2026-06-04 | 2 | 84.49 | 37.97 | false |
| 2026-06-05 | 2 | 68.74 | 20.16 | false |
| 2026-06-09 | 3 | 155.27 | -12.86 | false |
| 2026-06-10 | 3 | 28.75 | -81.46 | false |
| 2026-06-11 | 5 | 192.75 | -13.56 | false |
| 2026-06-12 | 4 | -123.05 | -123.05 | true |
| 2026-06-17 | 2 | 76.18 | 35.39 | false |
| 2026-06-18 | 1 | 48.57 | 48.57 | false |

## Forward-Test Window

Start condition: after an explicit owner-approved runtime maintenance report confirms the A1 and A2 profiles both match this shared spec.

Minimum review window:

- First checkpoint: at least 2 trading weeks and at least 20 non-zero closed evening-core trades.
- Decision checkpoint: at least 4 trading weeks and at least 40 non-zero closed evening-core trades.
- Promotion-grade evidence: at least 80-100 non-zero closed evening-core trades.

Do not judge the lane as passed before the decision checkpoint, even if early PnL is positive.

## Continue / Kill Rules

### Early Risk Kill

After at least 10 non-zero closed combined forward trades, stop the forward test and keep both accounts flat if:

- net PnL is below `-150 AED`, and
- PF is below `0.75`.

### Daily Runtime Stop

During any Dubai day, stop new entries on the affected account for the rest of the day if:

- the account's day PnL reaches `+100 AED`, or
- the account's day PnL reaches `-100 AED`.

### Weekly Review Stop

At each weekly review, pause the lane if any of these occur:

- unauthorized account, symbol, magic, lot, session, or candidate appears;
- duplicate same-family stacking reappears;
- A3 places broker-action trades;
- either A1 or A2 is net-negative after the decision checkpoint;
- the combined A1+A2 book is net-negative after the decision checkpoint;
- the lane fails to produce enough sample by the decision checkpoint and the owner declines extension.

## Pass Criteria At Decision Checkpoint

All must hold:

- A1 net PnL > `0 AED`;
- A2 net PnL > `0 AED`;
- combined A1+A2 net PnL > `0 AED`;
- combined PF >= `1.25`;
- combined win rate >= `50%`, or combined PF >= `1.30` with positive net PnL;
- combined result remains positive after removing the top 2 winning trades;
- no single day contributes more than 40% of combined net PnL;
- worst day does not breach the pre-registered `-100 AED` daily stop;
- no unauthorized runtime drift.

## Required Logging For Forward Evidence

Every accepted signal/order row must retain or add:

- account login;
- symbol;
- magic;
- candidate;
- entry time in broker, UTC, and Dubai time;
- direction;
- lot size;
- entry price;
- SL and TP;
- spread at entry;
- estimated stop distance;
- estimated cost_R;
- exit price;
- broker-realized PnL;
- duplicate key / duplicate decision;
- session bucket;
- daily lock state;
- loss-stop state.

If exact cost_R cannot be reconstructed from logs, the pass result is provisional only.

## Forbidden Changes During Test

- No parameter tuning.
- No lot increase.
- No additional symbols.
- No additional broker-action EAs on A1 or A2.
- No A3 reactivation.
- No round-family reactivation.
- No changing the session window after seeing results.
- No moving failed trades to another bucket after the fact.

## Interpretation

This test is designed to answer one question only:

Can the `920101` XAUUSD evening breakout core repeat on new demo data across both the historically positive A1 book and the clean A2 account once known bleeding lanes are removed?

It does not prove canonical Phase 2, does not authorize live trading, and does not rescue the broader XAU retest family.
