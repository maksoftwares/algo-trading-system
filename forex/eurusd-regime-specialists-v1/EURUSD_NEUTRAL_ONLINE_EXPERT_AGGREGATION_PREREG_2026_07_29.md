# EURUSD Neutral online expert aggregation preregistration

Date: `2026-07-29`

Status: `FROZEN_BEFORE_COMBINED_OUTCOME`

This audit asks whether eight already-frozen causal Neutral specialists contain
complementary, persistent information that a past-results-only allocator can
use. The expert set is fixed by mechanism diversity: price opening drive,
multi-session reversal, macro timing, consensus-confirmed events, listed
futures participation, official OCC customer flow, precious-metals consensus,
and symmetric RSI.

This is not pristine historical OOS. Individual component summaries were
already inspected before the meta-policy was designed. The combined selection,
however, has not been calculated, and every simulated decision must use only
component trades whose exits are strictly earlier than that decision.

The primary policy uses a 126-calendar-day exponential half-life. An expert
must have at least 12 lifetime closed observations, at least 8 effective
weighted observations, and a positive weighted mean R. At each entry clock the
highest-scoring eligible expert may trade, subject to one trade per UTC day and
one open position. Otherwise the portfolio stays in cash. Fixed 63- and
252-day half-lives are reported as sensitivities and cannot replace the primary
policy after outcomes are seen.

The input ledgers, full-calendar oracle ledger, chronology, selection rule,
cost stress, concentration stress, reporting windows, and gates are fixed in
`config/frozen_neutral_online_expert_aggregation.json`. The evaluation-only
oracle cannot affect a decision.

Even a historical pass cannot authorize demo or broker trading. It would
permit only a separately locked prospective version. A failure closes this
exact allocator without deleting experts or selecting a favorable half-life.
