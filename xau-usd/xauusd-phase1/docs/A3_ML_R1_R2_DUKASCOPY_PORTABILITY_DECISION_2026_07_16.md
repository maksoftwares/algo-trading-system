# A3 ML R1/R2 Dukascopy Portability Decision

Date: 2026-07-16

## Decision

The preregistered exam classification is `PORTABILITY_FAIL`.

- The R1/R2 pair does not advance to demo execution.
- R2 is rejected as a qualified alpha specialist in its current form.
- R1 remains a research baseline only and advances to a structural robustness audit. It does not advance directly to account-level execution.
- No signal threshold, regime threshold, stop, target, or gate may be tuned against these Dukascopy outcomes under the same version.
- Python demo predictions, EA consumption, strategy promotion, and broker action remain disabled.

The frozen result is identified by:

- inventory JSON SHA256: `7b9401496ec67bf55ef1aac223e856c71f3e73bb73889bd43aeee32cff51b2d1`
- portability JSON SHA256: `5bda423ed76a1c146e4f88b581bfaafe0ec85fb9593524a41e42eaf66d33e3a1f`
- selected-label CSV SHA256: `618cbdc4dc9bdc1e7b49366370b70d5015a18ccc44a7e82827e9cd70025f8fee`

## Data Integrity

- Source period: 2016-07 through 2026-06.
- Valid Dukascopy Bid/Ask months: 120/120.
- Missing months: 0.
- Invalid months: 0.
- Raw candidates: 1,053.
- Resolved raw labels: 1,053.
- Selected trades after frozen execution controls: 936.
- Candidate IDs are unique and every selected trade starts at or after its causal decision time.

## Economic Evidence

Across the full source period, the selected pair produced 936 trades, USD 10,327.63 stress net, PF 2.195, 42.84% winners, and USD 1,131.39 closed-trade drawdown. Frequency was approximately 0.371 trades per trading day. These aggregate figures do not override the failed frozen gates.

Historical backcast, 2016-07 through 2024-06:

| Scope | Trades | Stress net | PF | Closed DD | DD/net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Portfolio | 801 | USD 1,714.38 | 1.294 | USD 1,131.39 | 0.660 |
| R1 | 196 | USD 1,572.96 | 1.499 | USD 934.64 | 0.594 |
| R2 | 605 | USD 141.42 | 1.053 | USD 362.52 | 2.563 |

Recent cross-feed window, 2024-07 through 2026-06:

| Scope | Trades | Stress net | PF | Closed DD | DD/net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Portfolio | 135 | USD 8,613.25 | 4.057 | USD 701.79 | 0.081 |
| R1 | 114 | USD 8,547.74 | 4.249 | USD 701.79 | 0.082 |
| R2 | 21 | USD 65.51 | 1.351 | USD 90.32 | 1.379 |

The recent two-year window contributes about 83% of full-period pair profit. This is positive evidence for R1 during the recent gold trend, but it is also a major recency and regime-concentration warning.

## Failed Gates

1. `drawdown_to_net_each_window`: the historical portfolio DD/net ratio was 0.660 versus the frozen maximum 0.500.
2. `episode_concentration`: R1's best overlapping exposure episode contributed 38.78% of R1 net, above the 35% limit. R2's best episode contributed 99.04% of R2 net.
3. `top_three_episodes_removed_net_positive`: R2 becomes USD 269.79 net negative after removing its three best winning episodes.
4. `reference_timestamp_delta`: the preregistered UTC+4 conversion produced median nearest-entry deltas of 240 minutes for R1 and 180 minutes for R2, above the 60-minute limit.

The pair passed the frozen portfolio PF, specialist PF, specialist positive-net, positive-year, positive-six-month, and reference-count-ratio gates.

## Episode Findings

R1's largest winning exposure episode ran from 2025-08-26 through 2025-10-15, contained 28 overlapping trades, and earned approximately USD 3,924.70. Its second-largest ran from 2025-12-11 through 2026-01-28 and earned approximately USD 3,238.63 from 19 trades. R1 remains positive after removing its three best episodes, but its result is too concentrated for promotion.

R2's largest winning episode ran from 2022-05-09 through 2022-05-19, contained 22 trades, and earned approximately USD 204.94. That single episode is approximately equal to R2's entire ten-year stress net. R2 therefore has no sufficiently distributed edge under the frozen exam.

## Timestamp Diagnostic

Repository documents state that historical MT5 tester timestamps lack a frozen historical UTC-offset mapping. The exam used the preregistered current-runtime UTC+4 interpretation. A post-exam sensitivity diagnostic, which is not allowed to change the verdict, found that treating the old tester timestamps as UTC-like broker wall-clock values reduces the nearest-entry median to less than one minute for both specialists.

This ambiguity must be corrected in a future source contract with an independently established historical broker-time mapping. It cannot rescue this exam because the drawdown and episode-concentration failures remain independently decisive.

## Next Iteration

Iteration 2 will audit R1 episode robustness and shared floating-equity behavior without changing the frozen signal rules. It will measure overlapping stop risk, floating drawdown, margin use, cost stress, and risk-capped variants as portfolio engineering diagnostics. In parallel, R2 will not be counted as qualified coverage, and later specialist research must target genuinely different compression, chop, and shock-recovery opportunities rather than loosen R1/R2 entries.

The six-stage path remains: independent validation, structural robustness, shared-account risk, orthogonal specialists, ML ranking in shadow mode, and demo qualification. A failed stage can create a redesign cycle, so six is a disciplined minimum rather than a guaranteed maximum.
