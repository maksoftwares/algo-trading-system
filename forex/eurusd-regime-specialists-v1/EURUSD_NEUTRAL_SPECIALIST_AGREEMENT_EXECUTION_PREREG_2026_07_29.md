# EURUSD Neutral specialist-agreement execution preregistration

Date: `2026-07-29`

Status: `FROZEN_AFTER_CENSUS_PASS_BEFORE_PRICE_PATH_OUTCOME`

The signal-only census passed all capacity gates with 214 routed candidates,
108 LONG and 106 SHORT, across every chronological window. This file freezes
the one execution authorized by that result before EURUSD M5 paths are loaded.

Each routed agreement enters at its exact archived M5 open with a four-pip
stop, six-pip target, 12-hour maximum hold, 0.7-pip retail spread floor,
0.1-pip adverse slippage per side, and stop-first same-bar handling. Only one
position may be open. A missing entry bar or any overlap with the inherited
suspect-data interval forces cash. A path is admitted only if the exact
12-hour final M5 clock exists, preventing outcome-dependent use of truncated
paths. Extra 0.5-pip round-trip cost, best-5%
winner removal, both sides, every chronological window, drawdown, and
evaluation-only Neutral-oracle resemblance are mandatory reports.

The candidate file, EURUSD bid/ask source, manifest, oracle, execution,
quarantine, windows, and gates are hash-bound in
`config/frozen_neutral_specialist_agreement_execution.json`. No parameter,
direction, expert combination, clock, or favorable window may be selected
after outcomes are opened.

This remains retrospective causal research because the component summaries
were previously inspected. Even a pass cannot authorize demo or broker action;
it would require a separate prospective freeze.
