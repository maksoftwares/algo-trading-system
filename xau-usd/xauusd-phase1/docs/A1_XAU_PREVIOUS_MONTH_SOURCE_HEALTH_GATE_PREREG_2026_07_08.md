# A1 XAU Previous-Month Source Health Gate Preregistration

Date: 2026-07-08

## Goal

Test whether monthly consistency improves if the portfolio pauses a source group for the next
calendar month after that source group had poor closed performance in the previous month.

This follows the failed current-month firewall: current-month stops often triggered too late to
flip the month, so this pass tests a slower but fully causal source-health rule.

## Boundary

- Use existing exact-MT5 ledgers only:
  - `A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv`
- No MT5 launch.
- No chart, preset, profile, order, position, or broker/runtime state changes.
- No demo claim from this diagnostic.

## Causal Rule

For a candidate entry in month `M`, inspect only the selected source group's closed performance in
previous completed months. If the rule triggers, skip only that source group's entries during month
`M`; all other source groups keep trading.

The source group state uses trade close month, not entry month.

## Source Groups

- `h4_core`: `h4_d1_long_best_box2_atr80`, `h4_d1_long_broad_box3_atr60`
- `frequency`: `freq_step3_frontier`
- `short_hedge`: `short_hedge_v2_breakdown_retest`, never gated in this pass

## Fixed Grid

Run these fixed rules only:

- H4 previous-1-month net gates: pause `h4_core` if previous-month H4 net `< -$1`, `< -$25`,
  `< -$50`, `< -$75`, `< -$100`, `< -$150`, or `< -$200`.
- H4 previous-1-month loss-count gates: pause `h4_core` if previous-month H4 losses are
  `>= 1`, `>= 2`, `>= 3`, `>= 4`, `>= 5`, `>= 8`, or `>= 10`.
- H4 previous-2-month net gates: pause `h4_core` if trailing two-month H4 net `< -$25`,
  `< -$50`, or `< -$100`.
- Frequency previous-1-month net gates: pause `frequency` if previous-month frequency net
  `< -$75`, `< -$100`, `< -$150`, or `< -$200`.
- Frequency previous-2-month net gates: pause `frequency` if trailing two-month frequency net
  `< -$25`, `< -$50`, or `< -$100`.

No month names, hours, directions, extra thresholds, or source groups may be added after looking
at the output.

## Metrics

Report:

- signals, WR, W/L, PF, net;
- stressed W/L and stressed net at `$0.30` per ticket;
- max closed drawdown ordered by trade close time;
- active weekday percentage;
- positive and negative closing months;
- positive calendar-week percentage;
- worst month, best month, worst week;
- blocked signal counts by source group.

## Decision Rules

- `SOURCE_HEALTH_REVIEW_CANDIDATE`: positive closing months `>= 32`, net `>= 19000`, WR
  `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, active weekdays `>= 84%`, and max drawdown
  improves by at least `10%` versus the ungated long+V2 book.
- `SOURCE_HEALTH_WATCHLIST`: positive closing months improve by at least `2` while preserving
  net `>= 19000`, WR `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, and active weekdays
  `>= 84%`.
- `MONTHLY_IMPROVES_CORE_BREAKS`: positive months improve, but the core/net/activity constraints
  break.
- `REJECT_NO_MONTHLY_REPAIR`: no useful monthly repair.

Any passing row remains research-only until implemented as an exact-MT5 combined rule and reviewed.
