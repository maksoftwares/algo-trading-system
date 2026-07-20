# Capital R5 Causal Outcome Resolver V38 Preregistration

## Purpose

V35 emits frozen R5 transition component candidate facts but intentionally does
not create prospective component outcomes. V38 closes only that engineering gap.
It converts an immutable V35 candidate fact into either one frozen-semantics
Capital bid/ask outcome or one terminal rejection. It does not alter candidate
generation, discover parameters, summarize profitability, train a model, or
authorize execution.

## Frozen identity

- Forward boundary: `2026-07-20T00:00:00Z`.
- Components: `23925`, `24877`, `24995`, and `25048`.
- Candidate identity and geometry come only from V35.
- The V35 contract SHA-256 and rule-dependency SHA-256 in the configuration must
  match the locked V35 artifacts.
- All 799 historical V9 candidates have `signal_time == scheduled_entry_time`.
  V38 requires the same invariant; no timing correction or rescheduling is
  permitted.
- Execution configuration is loaded from V9 and must match V35's frozen V9
  dependency.

## Causal resolution

For each component, candidates are processed by scheduled entry time and
candidate ID. A later candidate cannot be finalized while an earlier candidate
for the same component is unresolved.

The first Capital quote at or after the scheduled entry is used, subject to the
frozen 20-minute entry gap. Long entry uses ask and short entry uses bid. Stops
use the first observed executable quote on crossing. Targets use the locked
target price on the first crossing. A no-hit exit uses the first executable quote
at or after the fixed horizon, subject to the frozen 72-hour horizon gap. Spread,
risk ceiling, ticket cost, holding cost, and stress slippage are copied from V9.

An observed stop or target may be resolved when its crossing quote is present.
No-hit outcomes remain pending until a valid horizon quote exists. A missing
entry or horizon becomes terminal only after the quote ledger has advanced past
the complete allowed gap. Each outcome records its causal knowledge time and the
hash of the exact quote slice supporting it.

The frozen component overlap and maximum four trades per component UTC day are
applied in candidate order. Rejections are immutable labels as well as executed
outcomes.

## Data integrity

- V35 candidate bytes already consumed by V38 form a locked prefix. Truncation
  or mutation fails closed.
- V38 resolution bytes already emitted form a separately locked prefix.
  Truncation or mutation of a prior label also fails closed.
- Candidate IDs, timestamps, geometry, direction, rule-dependency hash, and the
  absence of outcome fields are validated before resolution.
- Capital CSV input must match account `1033669`, server
  `Capital.ComMena-Demo`, symbol `XAUUSD`, and schema
  `xau_prospective_tick_v1`.
- Every consumed quote row must say `dry_run=true`; trade permission, broker
  action, and Python execution must all be false.
- Timestamp agreement, positive bid, ask not below bid, and the spread field are
  checked before duplicate milliseconds use the already frozen keep-last source
  order.
- A stable byte prefix is read from a file that may still be appending; partial
  trailing rows are excluded.

## Outcome boundary

V38 may record individual prospective component labels. It may not calculate or
publish aggregate R5 economics before the locked validation boundary, change a
threshold after seeing an outcome, or admit the sleeve. Validation and
confirmation each require 20 complete forward weekdays under a separately
locked evaluator.

## Authority

V38 imports no MT5 package and calls no broker API. It writes only its local
resolution ledger, source-prefix state, and status. Model training, Python
prediction, EA consumption, demo trading, live trading, and broker action remain
false.
