# EURUSD V1 Unmasked Audit

Status: `UNMASKED_KILL_GATES_PASS_CONTRACT_REPAIR_REQUIRED`

The exact unmasked run passes the reviewer's four immediate kill gates, but it
does not pass promotion gates, does not establish an edge, and cannot proceed
to an intervention until the discovered V1 contract mismatch is repaired.

## Exact MT5 result

| Candidate | Trades | Win rate | Net USD | PF | Equity DD |
|---|---:|---:|---:|---:|---:|
| Frozen V1 hour mask | 831 | 59.33% | $101.82 | 1.20 | 30.85 (2.95%) |
| V1 unmasked audit | 1145 | 57.55% | $77.26 | 1.11 | 27.56 (2.68%) |

Removing the mask added 314
net trades and reduced MT5 net by
$24.56. The old
hours were economically harmful in this history, but the raw signal remained
positive without them.

## Cost decomposition and stress

| Metric | Net USD | PF |
|---|---:|---:|
| Exact deal ledger | $77.26 | 1.1100 |
| +0.5 pip round trip; negative commission/swap x1.25 | $16.68 | 1.0229 |
| +1.0 pip round trip; negative commission/swap x1.25 | $-40.57 | 0.9461 |

Exact components: price profit
`$90.57`, commission
`$0.00`, swap
`$-13.31`.

## Matched attribution

- Signal stream parity: `true` across `2957` signals.
- Changed attempt decisions: `469`.
- Common entry timestamps: `789`; exact common outcomes: `789`.
- Unmasked-only entries: `356` (`345` in old masked hours and `11` secondary path effects).
- V1-only entries displaced by path: `42`.

Filtering the unmasked filled ledger after the fact produces
`800` trades and
`$114.29`, not V1's
`831` trades and
`$101.82`. This is not a parity failure:
the one-position mutex makes the intervention path-dependent. The exact V1
rerun is the valid causal reconstruction.

## Calendar years

| Year | Trades | Win rate | Net USD | PF |
|---|---:|---:|---:|---:|
| 2022 | 125 | 55.20% | $6.01 | 1.0527 |
| 2023 | 293 | 61.09% | $28.63 | 1.1588 |
| 2024 | 309 | 54.69% | $-2.66 | 0.9840 |
| 2025 | 238 | 58.82% | $33.36 | 1.2274 |
| 2026 | 180 | 56.67% | $11.92 | 1.1251 |

## Six-hour broker-time buckets

| Bucket | Trades | Win rate | Net USD | PF |
|---|---:|---:|---:|---:|
| 00:00-05:59 | 178 | 64.04% | $32.79 | 1.5785 |
| 06:00-11:59 | 463 | 53.56% | $-27.19 | 0.8994 |
| 12:00-17:59 | 435 | 58.85% | $57.26 | 1.1768 |
| 18:00-23:59 | 69 | 59.42% | $14.40 | 1.2798 |

## Episode diagnostic and branch

- Episodes: `2129`.
- Repeat filled entries: `517` / `1145` (`45.15%`).
- Repeat-entry PF: `1.0448`.
- Years 2023-2025 with repeat-entry PF below 0.90: `0`.
- Episode-mutex branch rule: `false`.
- Sole next authorized entry intervention: `IMMEDIATE_NEXT_BAR_RECLAIM`.

## Immediate kill gates

- [x] `unmasked_mt5_pf_at_least_1_05`
- [x] `primary_cost_stress_pf_at_least_0_95`
- [x] `at_least_two_positive_years_2023_2025`
- [x] `positive_net_not_dependent_on_old_blocked_hours`

## Implementation audit caveat

The source uses completed-bar indicator shifts and lows 1-6, rejects stops over
700 points, and is tester-only. Exact V1 and the unmasked run both used
`InpMinBodyFraction=0.40`, while the published V1 preset says `0.0`. The exact
signal-stream attribution is therefore valid, but the earlier written contract
is not. It must be corrected and frozen.

The source also does not explicitly initialize the new-bar latch to suppress
evaluation of the bar completed before tester startup. No startup signal
occurred in this run (the first signal was
`2022.07.01 12:30:00`), so
the issue did not change these results, but it must be resolved in any new
redesign baseline before prospective work.

The report records terminal build 5833 and 99% history quality. The generated
report used account leverage 1:50 even though the INI requested 1:200; fixed-lot
P&L is unaffected, but the provenance discrepancy is retained.

## Decision

Do not promote or deploy. The unmasked candidate survives only the immediate
family kill test. First repair and freeze the actual V1 contract. After that,
the next and only authorized entry experiment is
`IMMEDIATE_NEXT_BAR_RECLAIM`.
