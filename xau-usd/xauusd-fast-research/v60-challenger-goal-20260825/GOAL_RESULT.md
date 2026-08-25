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
every calendar year, recent-window, cohort-size, and veto-cohort gates. Its 12
vetoes were all endpoint losers.

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

The directly live-responsive virtual-health V3 is rejected. Although it adds
$28.61 overall and lowers both drawdowns, it hurts 2025 by $12.23, hurts 2026 by
$7.11, worsens recent windows, and its veto cohort PF is 1.046.

## Real demo evidence

The exposed pre-boundary audit contains 28 resolved XAUUSD broker executions
since 2026-07-21 with combined P/L of -$11.06. V2 would have vetoed none, so no
recent broker improvement is claimed. V57's causal virtual source health is
currently degraded (recent-20 PF 0.814 and net -$28.13), but using that signal as
a veto failed the long replay gates in V3.

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
100 scored executed candidates, 10 resolved veto opportunities, veto PF below
0.8, and positive avoided broker P/L before review. Passing those gates still
does not auto-authorize deployment.

The runtime supervisor is healthy on demo account 1033030. It supervises six
workers, both execution feeds pass, and both V1 and V2 observers explicitly
report `broker_action_authorized=false` and `deployment_authorized=false`.

The deployed portfolio currently loads the existing ML top-up overlay, but it
has filled zero top-ups. V2 itself is not deployed.
