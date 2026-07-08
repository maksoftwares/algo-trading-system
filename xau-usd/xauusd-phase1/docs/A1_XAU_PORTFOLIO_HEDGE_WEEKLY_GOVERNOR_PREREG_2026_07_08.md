# A1 XAU Portfolio Hedge Weekly Governor Preregistration

Date: 2026-07-08

## Goal

After the standalone XAU short WR50/RR2 search was falsified, test whether the current best
long book plus the V2 short hedge can be improved by portfolio-level weekly risk governance.

This is a smoothing diagnostic, not a new entry-signal hunt.

## Boundary

- Use only existing exact-MT5 ledgers:
  - `A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv`
  - `A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv`
- No MT5 launch.
- No chart, preset, profile, order, position, or broker/runtime state changes.
- No demo claim from this diagnostic.

## Causal Rule

For each candidate entry, use only trades that have already closed before the candidate entry time.
The weekly closed PnL bucket is the broker week containing the trade close time. The gate decision
is made for the broker week containing the candidate entry time.

If a weekly gate is active:

- `loss_stop`: skip new entries for the rest of the week once closed weekly PnL is less than or
  equal to `-loss_stop`.
- `profit_lock`: skip new entries for the rest of the week once closed weekly PnL is greater than
  or equal to `profit_lock`.
- `bracket`: apply both rules.

## Fixed Grid

Run these fixed rules only:

- baseline supportive guard, no hedge;
- supportive guard plus V2 short hedge, no weekly gate;
- loss stops: `$25`, `$50`, `$75`, `$100`, `$150`, `$200`;
- profit locks: `$25`, `$50`, `$75`, `$100`, `$150`, `$200`;
- brackets:
  - loss `$50`, profit `$50`, `$75`, `$100`, `$150`;
  - loss `$75`, profit `$50`, `$75`, `$100`, `$150`;
  - loss `$100`, profit `$50`, `$75`, `$100`, `$150`.

No thresholds may be added after looking at the output.

## Metrics

Report for every row:

- signals, WR, W/L, PF, net, max closed drawdown;
- stressed W/L and stressed net at `$0.30` per ticket;
- active weekday percentage;
- positive calendar-week percentage;
- positive active-week percentage;
- worst week, rolling 4-week positive percentage;
- June 2026 net;
- recent Q2 2026 net;
- blocked signal count.

## Decision Rules

- `PORTFOLIO_GOVERNOR_REVIEW_CANDIDATE`: positive calendar weeks `>= 65%`, active weekdays
  `>= 85%`, WR `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, net `>= 17000`, and June 2026
  improves versus ungated long-plus-short.
- `SMOOTHING_WATCHLIST`: positive calendar weeks improve by at least `3pp` versus ungated
  long-plus-short while preserving WR `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, and net
  `>= 17000`.
- `WEEKLY_IMPROVES_CORE_BREAKS`: weekly shape improves, but core WR/W-L/stress/net breaks.
- `REJECT_NO_WEEKLY_REPAIR`: no useful weekly repair.

Any row that passes still needs a real exact-MT5 combined-EA implementation and reviewer review
before any demo-spec discussion.
