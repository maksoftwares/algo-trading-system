# XAUUSD V60 Challenger Goal Result

Date: 2026-08-25

Decision: **keep V60 deployed; collect dynamic V6 forward evidence read-only**.

August is now an explicit acceptance objective, but not a standalone optimization
target. A challenger must improve August P/L, profit factor, and drawdown while
also preserving the nominal long-run edge, every calendar year, the final
3/6/12-month windows, at least 99% of trades, and causal forward validity.

## Best research challenger

`v60-dynamic-followthrough-union-v6` combines the validated V2 source-health
veto with one tightly bounded V57 weak-followthrough anti-chase veto. Its state
is path-dependent: only retained trades enter future challenger source health;
vetoed outcomes do not leak into later decisions. Missing information retains
the baseline trade.

| Metric | Deployed V60 | Dynamic V6 | Change |
|---|---:|---:|---:|
| Closed trades | 1,390 | 1,377 | -13 |
| Net P/L | $3,603.57 | $3,681.34 | +$77.78 |
| Profit factor | 1.7107 | 1.7377 | +0.0270 |
| Win rate | 48.49% | 48.87% | +0.39 pp |
| Closed drawdown | $223.28 | $217.46 | -$5.82 |
| Floating-equity drawdown | $238.28 | $238.28 | $0.00 |
| Trades per weekday | 0.970 | 0.961 | -0.009 |

The full five-second runtime replay covers 2021-01-01 through 2026-06-30. All
nominal preservation gates pass. Dynamic V6 vetoes 13 baseline executions: 12
from V2 and one additional weak-followthrough V57 trade. Their baseline-runtime
PF is 0.028. Trade retention is 99.065%.

| Year | V60 P/L | Dynamic V6 P/L | Change |
|---|---:|---:|---:|
| 2021 | $165.93 | $173.92 | +$7.99 |
| 2022 | $57.12 | $63.45 | +$6.33 |
| 2023 | $341.96 | $351.59 | +$9.63 |
| 2024 | $731.53 | $742.66 | +$11.14 |
| 2025 | $1,167.09 | $1,184.19 | +$17.10 |
| 2026 through June | $1,139.94 | $1,165.53 | +$25.59 |

The final three months remain unchanged. The final six months improve by $25.59
and the final 12 months improve from $1,711.59 to $1,754.28.

## Robustness

The V2 component reproduced exactly. Maturity thresholds of 40, 50, and 60
all pass every original gate. Stricter health and rank thresholds remain
profitable in every year but have too few vetoes for the locked cohort gate.
A 30-trade health window, looser health threshold, and looser rank threshold
each fail at least one risk or annual-stability gate; none replaces V2.

### Independent-feed diagnostic

The exact V60 runtime intervals were also repriced on independent Dukascopy
bid/ask ticks. Quotes no more than five seconds after each Capital runtime entry
and exit were accepted; 1,366 of 1,390 trades (98.27%) had common coverage, and
all 12 V2 vetoes were covered. The remaining 24 rows are explicitly retained as
uncovered instead of being filled using a wider or hindsight-selected window.

| Metric | V60 on Dukascopy timing | V2 on Dukascopy timing | Change |
|---|---:|---:|---:|
| Closed trades | 1,366 | 1,354 | -12 |
| Net spread-only P/L | $4,330.78 | $4,369.58 | +$38.80 |
| Profit factor | 2.0013 | 2.0203 | +0.0190 |
| Win rate | 50.59% | 50.89% | +0.30 pp |
| Closed drawdown | $180.66 | $180.66 | $0.00 |

The veto cohort lost $38.80 at PF 0.0841 on Dukascopy, with 10 losses and two
wins. Capital and Dukascopy agreed on the veto outcome sign for 11 of 12 trades
(91.67%); all-trade P/L correlation was 0.9792. The V2 P/L change was
nonnegative in every covered calendar year. Every raw hour used is captured in
a 2,111-file SHA-256 manifest, and each trade records its exact source file and
row. The result is not driven by the five-second allowance: at 250 ms, all nine
covered vetoes still lose $30.67; at two seconds, all 11 covered vetoes lose
$39.48. A descriptive one-sided Fisher test against the other covered,
degraded-health ranked cohort gives p=0.0256, but remains post-selection.

This supports the cross-broker price-path mechanism, but it is not an
independent strategy replay: Capital produced the entry and exit timestamps,
the policy was historically selected, and commission, swap, and independent
Dukascopy stop triggering are absent. It therefore does not authorize V2.

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

The exact replay independently reconstructed all 30 exposed broker lifecycles
with 100% execution-detail and active-tick coverage. It evaluated 8,359,662
recorded quotes, reconciled final P/L exactly to -$19.19, and measured $95.85 of
XAU-only floating-equity drawdown. V2 is identical in this exposed interval
because it vetoed zero trades. This validates the replay machinery on genuine
broker records but is not prospective evidence of improvement.

## August robustness objective

Dynamic V6 specifically addresses the concentrated August failure pattern. Its
V57 anti-chase side requires a bottom-decile causal rank, ATR ratio at least
1.20, proximity to the prior 24-hour high, positive 24-hour return, and a
4-hour/24-hour return ratio below 0.70. This describes a weak late-stage chase,
not every strong V57 long.

| Metric through August 25 | Deployed V60 | Dynamic V6 | Change |
|---|---:|---:|---:|
| Trades | 24 | 21 | -3 |
| Net P/L | -$24.87 | +$17.50 | +$42.38 |
| Profit factor | 0.8346 | 1.1621 | +0.3275 |
| Win rate | 41.67% | 47.62% | +5.95 pp |
| Closed drawdown | $86.59 | $56.69 | -$29.90 |

This August result is exposed and therefore cannot prove the rule. What makes
V6 worth forwarding is that the exact dynamic replay also improves all six
calendar years, the final 6/12-month windows, long-run P/L/PF, and closed
drawdown while retaining more than 99% of trades. On same-timing Dukascopy
quotes, the combined delta is +$61.49 and no covered calendar year is harmed.

Nominal historical-to-runtime parity is exact: the prospective policy produces
the same 13 veto IDs, 1,377 trades, and $3,681.34 P/L as full dynamic V6, with
zero replacement-capacity trades. Stress behavior is now separated. At +$0.10,
the full dynamic replay admits 22 replacement-capacity trades; at +$0.20 it
admits 11. Those trades cannot be validated by the read-only observer.

On the conservative veto-only common path, +$0.10 still improves net by $73.78,
PF to 1.7034, closed drawdown to $206.71, and equity drawdown from $242.13 to
$228.43, but retains only 98.843% of trades and therefore fails the locked
retention/frequency gates. At +$0.20 it improves net by $68.19, closed drawdown
to $208.49, and equity drawdown from $244.02 to $230.22, but retains 98.697% and
harms 2021 by $1.08. The fixed-lifecycle reconstruction matches V60's equity
drawdown exactly in every scenario. These limitations and the lack of clean
forward outcomes keep deployment locked.

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

V60 remains the only broker-action policy. Dynamic V6 is supervised read-only from the
locked evidence boundary `2026-08-26T00:00:00Z`, with 332 hash-locked replay
outcomes used only to establish source maturity. It requires at least 90 days,
100 scored and resolved baseline executions, 10 resolved veto opportunities,
complete causal-rank and feature coverage, at least 99% trade retention, veto PF below 0.8,
and positive avoided broker P/L before review. Across the entire resolved
forward portfolio, V6 must also have net P/L and PF no worse than V60 and
closed-trade drawdown no higher.

The clean observer writes each score decision, execution decision, and broker
outcome to a hash-linked evidence chain. Any later change to an immutable event
fails collection closed. The chain was initialized and verified empty before
the prospective boundary. Its exact prospective contract hash
`86cb376fdd545c2652edab395cb96bb1598a14784a35d2a3bd367380bce3d0b4`
is required by the supervisor and written into every immutable score and
execution decision. A reconstructed veto can count only if its score and
execution decision are immutably recorded within 120 seconds of scheduled entry
and strictly before the actual broker exit; a late decision is retained by V6
in every P/L, equity, and exact-replay calculation. The observer runner is
hash-locked, records actual score-completion time, and uses a 30-second pause
between cycles. A second hash-linked series records XAU-only V60 and hypothetical
V6 equity marks after each completed cycle. At least 5,000
marks are required, V6 sampled equity drawdown cannot be worse, and the final review must reconstruct
exact between-sample drawdown from the stored ticks. Passing every gate still
does not auto-authorize deployment.

The exact replay implementation is now hash-locked. Prospective evidence also
freezes every broker entry's time, side, volume, volume-weighted price, and entry
cost. The replay handles overlapping trades, marks longs to bid and shorts to
ask on every recorded tick, reconciles final broker P/L, and hashes each closed
daily tick file it uses. It also handles multiple entry fills and partial exits
at their actual times and volumes. With no post-boundary trades yet, its status is
`NOT_READY_NO_RESOLVED_TRADES`, as expected.

The runtime supervisor is healthy on demo account 1033030. It supervises eight
workers, both execution feeds pass, and all research observers explicitly
report `broker_action_authorized=false` and `deployment_authorized=false`.
The deployed V60 processes remain `19888, 4888`, and MT5 remains `24168`;
adding V6 changed neither broker action nor strategy/risk parameters.

The deployed portfolio currently loads the existing ML top-up overlay, but it
has filled zero top-ups. V2, anti-chase, and dynamic V6 are not deployed.
