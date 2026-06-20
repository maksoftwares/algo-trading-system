# A1/A2 920101 Rule Identity Reconciliation - 2026-06-20

Status: `MISMATCH_REQUIRES_MAINTENANCE_REPORT`

Boundary: read-only/offline profile inspection only. No MT5 terminal, EA, preset, chart, order, position, profile, or broker setting was changed. A3 remains paused.

## Why This Report Exists

Claude's 2026-06-20 review correctly flags that the profitable `920101` evening core should not be forward-tested as "the same rule" on A1 and A2 until the active chart configurations are proven identical.

This report compares current chart-profile evidence for:

- A1 standard demo account `1025742`.
- A2 clean Tier-1 account `1033030`.
- Candidate `breakout_retest`.
- Derived magic `920101`.
- Target symbol `XAUUSD`.

## Key Finding

The historical `+701.86 AED` A1 evening core is real broker-fill evidence from the A1 primary export, but the currently inspected A1 standard profile does **not** contain an active `Phase2ExperimentalDemoExecutor` chart for `XAUUSD` / account `1025742`. A2 does contain the clean XAU breakout executor.

Therefore the next-week forward test is not ready for runtime. Before any broker-action change, an owner-approved maintenance report must prove the A1 and A2 runtime rules are identical, or explicitly document the before/after changes that make them identical.

## Current Profile Evidence

### A1 Standard Demo Profile

Inspected profile:

`C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default`

Detected `Phase2ExperimentalDemoExecutor` charts for A1:

| Chart | Symbol | Candidate | Target symbol | Account allowlist | Broker action | Session gate | Server hours | Lot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chart01.chr` | `EURUSD` | `breakout_retest` | `EURUSD` | `1025742` | `true` | `true` | `12 -> 1` | `0.01` |
| `chart02.chr` | `GBPUSD` | `breakout_retest` | `GBPUSD` | `1025742` | `true` | `true` | `12 -> 1` | `0.01` |

No current chart was found in the inspected A1 profile with all of:

- `name=Phase2ExperimentalDemoExecutor`
- `InpAllowedAccountLoginsCsv=1025742`
- `InpTargetSymbol=XAUUSD`

Important: older project handoff text says A1 XAU `breakout_retest` once existed on `chart03.chr`; the current profile inspection does not confirm that state.

### A2 Clean Tier-1 Profile

Inspected profile:

`C:\MT5PortableTier1BestEA\MQL5\Profiles\Charts\Default`

Detected A2 XAU breakout chart:

| Chart | Symbol | Candidate | Target symbol | Account allowlist | Broker action | Session gate | Server hours | Lot | Max open positions | Max cost R | Max spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `chart02.chr` | `XAUUSD` | `breakout_retest` | `XAUUSD` | `1033030` | `true` | `true` | `12 -> 15` | `0.01` | 1 | 0.30 | 75.0 |

## Known Configuration Difference

The current A1 executor charts that do exist use server hours `12 -> 1`, interpreted in prior reports as Dubai `16:00 -> 05:59`. The A2 clean XAU chart uses server hours `12 -> 15`, interpreted as Dubai evening-only.

If A1 XAU is restored with `12 -> 1`, it would not be the same rule as A2. The forward spec must therefore require a shared rule for both accounts before the test starts.

## Required Shared Rule Before Forward Test

Both accounts must be explicitly confirmed as:

| Field | Required shared value |
| --- | --- |
| Candidate | `breakout_retest` |
| Symbol | `XAUUSD` |
| Derived magic | `920101` |
| Lot | `0.01` fixed |
| Broker action | enabled only after owner-approved maintenance |
| Session gate | enabled |
| Broker-action window | Dubai `16:00:00` through `19:59:59` only |
| Blocked windows | Dubai morning, afternoon, and night |
| Duplicate/family mutex | enabled according to current approved code |
| Daily profit lock | `+100 AED` per account/day |
| Daily loss stop | `-100 AED` per account/day |
| Canonical Phase 2 | unchanged, not approved |
| A3 | paused |

## Decision

Do not start the next-week forward test from the current evidence alone.

Required before runtime:

1. Owner-approved maintenance packet.
2. Before/after chart-profile report for A1 and A2.
3. Startup-log proof for both accounts.
4. Confirmation that the A1 XAU `920101` chart exists and matches A2's shared rule.
5. Confirmation that A2 remains clean and runs the same shared XAU evening rule.

After that, the forward test may be scored on both accounts in parallel. Promotion requires both accounts and the combined book to be positive.
