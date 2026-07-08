# A1 XAU Source-Level Monthly Firewall Preregistration

Date: 2026-07-08

## Goal

Improve monthly consistency without destroying the profit engine. The prior weekly governor
improved smoothness but cut too much activity and net profit, so this pass tests only narrow
source-level monthly damage controls.

## Boundary

- Use existing exact-MT5 ledgers only:
  - `A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv`
  - `A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv`
- No MT5 launch.
- No chart, preset, profile, order, position, or broker/runtime state changes.
- No demo claim from this diagnostic.

## Causal Rule

For each candidate entry, use only same-source-group trades already closed before the candidate
entry time. State is tracked by the month containing the entry. A closed trade updates the month
containing its close time.

If a source group is paused for the current month, only entries from that source group are skipped.
All other sources continue trading.

## Source Groups

- `h4_core`: `h4_d1_long_best_box2_atr80`, `h4_d1_long_broad_box3_atr60`
- `frequency`: `freq_step3_frontier`
- `short_hedge`: `short_hedge_v2_breakdown_retest`, never gated in this pass

## Fixed Grid

Run these fixed rules only against the long+V2 combined book:

- H4 loss-count stops: pause `h4_core` after `1`, `2`, or `3` closed H4 losses in the current
  month.
- H4 PnL stops: pause `h4_core` after closed H4 current-month PnL is less than or equal to
  `-$50`, `-$75`, `-$100`, `-$150`, or `-$200`.
- H4 combined stops:
  - loss count `2` or PnL `<= -$100`
  - loss count `2` or PnL `<= -$150`
  - loss count `3` or PnL `<= -$150`
- Frequency PnL stops: pause `frequency` after closed frequency current-month PnL is less than
  or equal to `-$75`, `-$100`, `-$150`, or `-$200`.
- Combined H4/frequency stops:
  - H4 PnL `<= -$100` and frequency PnL `<= -$150`
  - H4 loss count `2` or H4 PnL `<= -$100`, plus frequency PnL `<= -$150`
  - H4 PnL `<= -$150` and frequency PnL `<= -$200`

No thresholds, source groups, month filters, hour filters, or direction filters may be added after
looking at the output.

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

- `MONTHLY_FIREWALL_REVIEW_CANDIDATE`: positive closing months `>= 32`, net `>= 18000`, WR
  `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, active weekdays `>= 84%`, and max drawdown
  improves by at least `15%` versus the ungated long+V2 book.
- `MONTHLY_FIREWALL_WATCHLIST`: positive closing months improve by at least `2` while preserving
  net `>= 19000`, WR `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, and active weekdays `>= 84%`.
- `MONTHLY_IMPROVES_CORE_BREAKS`: positive months improve, but the core/net/activity constraints
  break.
- `REJECT_NO_MONTHLY_REPAIR`: no useful monthly repair.

Any passing row remains research-only until implemented as an exact-MT5 combined rule and reviewed.
