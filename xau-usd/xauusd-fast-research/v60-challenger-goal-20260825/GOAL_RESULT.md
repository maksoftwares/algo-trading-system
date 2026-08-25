# XAUUSD V60 Challenger Goal Result

Date: 2026-08-25

Decision: **keep V60 deployed; collect V2 forward evidence read-only**.

## Best validated historical challenger

`v60-mature-source-health-rank-veto-v2` applies one causal rule to every mature
specialist: after at least 50 earlier source executions, veto only a candidate
whose latest-20 executed source PF is below 1.0 and whose pre-existing causal ML
rank is below 0.10. Missing information retains the baseline trade.

| Metric | Deployed V60 | V2 challenger | Change |
|---|---:|---:|---:|
| Closed trades | 1,390 | 1,378 | -12 |
| Net P/L | $3,603.57 | $3,655.75 | +$52.19 |
| Profit factor | 1.7107 | 1.7289 | +0.0181 |
| Win rate | 48.49% | 48.84% | +0.35 pp |
| Closed drawdown | $223.28 | $217.46 | -$5.82 |
| Floating-equity drawdown | $238.28 | $238.28 | $0.00 |
| Trades per weekday | 0.970 | 0.962 | -0.008 |

The full five-second runtime replay covers 2021-01-01 through 2026-06-30. V2
passed baseline identity, P/L, PF, both drawdowns, trade retention, frequency,
every calendar year, recent-window, cohort-size, and veto-cohort gates. All 12
candidate endpoints were losers; under the actual V60 runtime exits, the cohort
contains 11 losses and one small winner, with PF 0.0411 and net -$52.19.

| Year | V60 P/L | V2 P/L | Change |
|---|---:|---:|---:|
| 2021 | $165.93 | $173.92 | +$7.99 |
| 2022 | $57.12 | $63.45 | +$6.33 |
| 2023 | $341.96 | $351.59 | +$9.63 |
| 2024 | $731.53 | $742.66 | +$11.14 |
| 2025 | $1,167.09 | $1,184.19 | +$17.10 |
| 2026 through June | $1,139.94 | $1,139.94 | $0.00 |

Final 3- and 6-month replay results are unchanged. The final 12 months improve
from $1,711.59 on 310 trades to $1,728.69 on 307 trades.

## Robustness

The nominated result reproduced exactly. Maturity thresholds of 40, 50, and 60
all pass every original gate. Stricter health and rank thresholds remain
profitable in every year but have too few vetoes for the locked cohort gate.
A 30-trade health window, looser health threshold, and looser rank threshold
each fail at least one risk or annual-stability gate; none replaces V2.

Among 255 mature, degraded-health, causally ranked baseline executions, the 12
V2 selections are distributed across 11 entry dates, three specialists, and
five calendar years. The other 243 trades have PF 1.8727. Descriptive
post-selection diagnostics give Fisher p 0.00445 and source-year-conditioned
permutation p 0.00113. These strengthen the mechanism but are not untouched
deployment proof.

An exact path-dependent execution-cost replay adds the same surcharge to every
candidate in V60 and V2. The replay population already models a mean opening
cost of $0.572 per candidate. V2 passes every comparative gate with another
$0.10 per trade (about 17% above that existing mean): net $3,552.44 versus
$3,468.49, PF 1.6955 versus 1.6760, closed drawdown $215.15 versus $220.41, and
equity drawdown $232.80 versus $242.13. At another $0.20, V2 remains $39.48
ahead overall but fails the locked annual/recent-window gate: 2026 and the final
six months are $6.91 worse. V2 therefore has a measurable but limited
execution-cost buffer.

There is no valid unchanged earlier-era replay. V60 price candidates extend to
2010, but the frozen causal-rank ledger starts in 2021 and requires 200 earlier
training rows. Lowering that requirement or rebuilding the ranker after seeing
the outcome would create a different experiment, not independent validation.

The directly live-responsive virtual-health V3 is rejected. Although it adds
$28.61 overall and lowers both drawdowns, it hurts 2025 by $12.23, hurts 2026 by
$7.11, and worsens recent windows. Its 16 decisions include only 14 common-path
baseline executions, so it remains rejected regardless of cohort PF.

## Real demo evidence

The exposed pre-boundary audit now covers all nine source ledgers and reconciles
to 30 resolved XAUUSD broker executions since 2026-07-21: 12 wins, 18 losses,
PF 0.8967, and combined P/L of -$19.19. V2 would have vetoed none, so no recent
broker improvement is claimed. V57's causal virtual source health is currently
degraded (recent-20 PF 0.814 and net -$28.13), but using that signal as a veto
failed the long replay gates in V3.

The first V2 observer configuration read only the shared add-on ledger despite
targeting every source. That coverage defect was fixed before the clean evidence
boundary: the observer now hash-locks the deployed source configuration, merges
all core and add-on ledgers, normalizes source/time fields, rejects ambiguous or
duplicate candidates, and reports per-source ledger coverage.

A second pre-boundary audit found that the deployed top-up scorer intentionally
does not rank R1, V25, or V8, while historical V2 can act on those sources. V2
now has a separate observer-only rank path using the same frozen model. It scores
all sources chronologically, batches simultaneous candidates against the same
strictly earlier reference, and cannot affect an order. All 45 exposed
candidates scored successfully against 1,676 frozen historical reference scores;
all 30 executed broker candidates are now evaluable. On the 23 candidates also
ranked by the deployed top-up path, raw model scores match exactly; mean rank
difference is 0.0010 and maximum difference is 0.0026 because the observer
correctly expands with all-source scores.

A fixed post-hoc rank-only audit was also run because three recent V57 losses had
bottom-decile scores but source PF above 1.0. It is rejected: although net P/L
improves by $72.33, PF rises to 1.7655, and equity drawdown falls by $6.05, it
removes 58 trades, excludes a profitable cohort with PF 1.14, hurts 2023 by
$47.23, and hurts 2024 by $21.87. Loosening V2 to fit the recent losses would
discard established edge.

New candidates now persist their recent-20 source health for future research.
This field is observability only and cannot affect an order.

## Runtime improvement

R4 previously reparsed about 2.15 GB of CSV ticks each cycle, taking roughly
117.5-122 seconds and consuming 3.7-6.5 GB. Verified per-file tick and bar caches
now reproduce the exact immutable dataset while warm R4 cycles take about
1.2-1.4 seconds and the feed process uses about 0.21-0.23 GB. Feed polling is
five seconds instead of 60 seconds.

Immutable parity evidence:

- 8,574,972 unique ticks and 6,630 M5 bars
- tick SHA-256 `0d037b4f4d3241056249d096113bb5974ab9d8f9be24d3111122f2708dcc41f1`
- bar SHA-256 `fac126f813397683096146add174b0cbbde7732d63c97462c8d9f0c641e8915b`

## Forward state

V60 remains the only broker-action policy. V2 is supervised read-only from the
locked evidence boundary `2026-08-26T00:00:00Z`, with 332 hash-locked replay
outcomes used only to establish source maturity. It requires at least 90 days,
100 scored and resolved baseline executions, 10 resolved veto opportunities,
complete causal-rank coverage, at least 95% trade retention, veto PF below 0.8,
and positive avoided broker P/L before review. Across the entire resolved
forward portfolio, V2 must also have net P/L and PF no worse than V60 and
closed-trade drawdown no higher.

The clean observer writes each score decision, execution decision, and broker
outcome to a hash-linked evidence chain. Any later change to an immutable event
fails collection closed. The chain was initialized and verified empty before
the prospective boundary. Passing every gate still does not auto-authorize
deployment.

The runtime supervisor is healthy on demo account 1033030. It supervises six
workers, both execution feeds pass, and both V1 and V2 observers explicitly
report `broker_action_authorized=false` and `deployment_authorized=false`.

The deployed portfolio currently loads the existing ML top-up overlay, but it
has filled zero top-ups. V2 itself is not deployed.
