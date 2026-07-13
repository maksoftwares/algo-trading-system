# A1 XAU Specialist Admission, Regime, and Drawdown Contract

Date: `2026-07-10`

Status: `LOCKED_BEFORE_NEW_SPECIALIST_RESULTS`

## Objective

Build a research-only XAUUSD portfolio in which every trading source is independently profitable, belongs to a causally defined market state, and controls mark-to-market equity drawdown. A combined portfolio may improve a qualified component, but it may never conceal a failed component.

This contract governs the clean R1 requalification and every subsequent R2, compression/transition, overlap, and portfolio test. It does not authorize demo or live deployment.

## Evidence boundary

- Promotion evidence must come from exact MT5 Strategy Tester runs using completed-bar inputs.
- Python and ledger recomposition are diagnostic only.
- The candidate, thresholds, risk rules, test windows, and pass/kill rules must be preregistered before the exact run.
- One candidate is allowed per research family. A failed run does not authorize a sibling threshold, calendar mask, or management repair.
- No hour, session, weekday, month, previous-period PnL, outcome-derived, or post-result mask is admissible.
- No parameter grid is admissible for specialist promotion.
- Costs, fixed risk/size, stop, target, and execution assumptions must be declared before the run.
- All raw HTML, tester configuration, trade, order, signal, management, and deal artifacts must be retained.

## Canonical causal regime contract

Regime is represented by three orthogonal dimensions. A single mutually exclusive label is retained only as a compatibility projection.

### Direction

- `UP`: completed D1 fast EMA is above slow EMA, its completed-bar slope is non-negative over the frozen lag, persistence is satisfied, and completed H4 confirms when required.
- `DOWN`: completed D1 fast EMA is below slow EMA, its completed-bar slope is non-positive over the frozen lag, persistence is satisfied, and completed H4 confirms when required.
- `NEUTRAL`: neither directional state is established.

### Volatility

- `SHOCK`: the frozen completed-H1 range/ATR or completed-D1 ATR-percentile shock rule is met.
- `COMPRESSED`: the frozen completed-D1 ATR-percentile and multi-day range/median compression rules are met.
- `NORMAL`: neither shock nor compression is present.

### Phase

- `ESTABLISHED`: the directional persistence rule is satisfied and no new compression-release transition is active.
- `TRANSITION`: direction is not yet established after a directional change, or a setup recorded in completed compression has broken its frozen range and is still within its preregistered transition lifetime.

Shock is an overriding risk condition, not a direction. Compression may coexist with direction. Transition is explicit and may not be silently forced into chop or trend.

The compatibility projection is:

1. `shock` if volatility is `SHOCK`;
2. `transition` if phase is `TRANSITION`;
3. `uptrend` if direction is `UP`;
4. `downtrend` if direction is `DOWN`;
5. `compression` if volatility is `COMPRESSED`;
6. `chop` otherwise.

## Mandatory regime telemetry

Every candidate decision must log:

- regime dimensions and compatibility label at setup, entry, maximum adverse excursion, and exit;
- the completed-bar timestamps used by the classifier;
- setup identifier and setup-state timestamp;
- state changes while a position is open;
- authorization result and exact block reason;
- specialist owner and conflict-owner decision;
- entry risk in money and R, aggregate same-direction open risk, and aggregate portfolio open risk.

Executed entries must have zero future-bar inputs and zero out-of-contract authorizations. Blocked attempts may occur in non-owned states and must remain in the ledger.

## Initial specialist ownership

| Specialist | Setup ownership | Executed-entry ownership | Initial action outside ownership |
| --- | --- | --- | --- |
| R1 trend long | established `UP` | `UP`, non-shock | block |
| R2 trend short | established `DOWN` | `DOWN`, non-shock | block |
| R3 compression release | completed `COMPRESSED` setup | registered `TRANSITION`, non-shock | block |
| Chop | none until a separate family qualifies | none | cash |
| Shock | none until a separate event family qualifies | none | cash and block new entries |
| Unknown/ambiguous | none | none | cash |

Handling a state successfully may mean staying flat. Three specialists are not required to manufacture trades in every state.

## Standalone admission gates

All gates are evaluated per source before any combined test.

### Alpha and sample

- at least `100` executed trades;
- at least three independently identified owned-regime episodes;
- at least three calendar years with exposure and three profitable calendar-year buckets;
- win rate at least `50%`;
- realized average-win/average-loss at least `2.00`;
- profit factor at least `2.00`;
- stressed profit factor at least `1.75` after the preregistered per-ticket cost stress;
- stressed net profit positive;
- pre-recent-window net profit positive.

Rare-event families require a separate preregistered event-count contract. Their gate may not be relaxed after results are known.

### Robustness and concentration

- net profit remains positive after removing the ten largest winning trades;
- net profit remains positive after removing the three best entry days;
- the best month contributes no more than `30%` of total positive net;
- no single regime episode contributes more than `50%` of total positive net;
- no component is admitted from one recent episode alone.

### Regime purity and independence

- `100%` of executed entries are authorized by the specialist's owned setup/entry contract;
- the specialist is profitable inside its owned state, not merely in an independently assigned different state;
- same-event, same-direction overlap with an incumbent is below `20%`, unless a preregistered replacement test proves superior net, PF, and equity drawdown;
- a relabeled incumbent is not counted as a new specialist.

### Execution integrity

- exact MT5 successful-order, executed-trade, and normalized-ledger counts reconcile;
- every `ORDER_SEND_FAIL` is listed with timestamp, retcode, description, and same-timestamp execution outcome;
- zero unexplained failures, missing tester files, or open-at-end positions;
- no forbidden calendar/session/previous-PnL guard fires.

### Drawdown and capital efficiency

All reports must show closed-ledger DD, MT5 balance DD maximal/relative, and MT5 equity DD maximal/relative.

- standalone MT5 equity drawdown relative no more than `20%`;
- standalone MT5 balance drawdown relative no more than `20%`;
- net profit / maximum MT5 equity drawdown at least `2.00`;
- maximum MT5 equity drawdown may not exceed `2.0x` closed-ledger drawdown without an explicit floating-risk failure;
- a candidate passing alpha but failing these gates is `ALPHA_ONLY_RISK_REPAIR_REQUIRED`, not qualified.

## Risk-layer rules

Alpha is first tested without previous-PnL governors. Only after alpha passes may one separately preregistered structural risk layer be tested.

Permitted risk layers:

- risk-normalized position sizing;
- a fixed per-specialist aggregate open-risk ceiling;
- a fixed portfolio aggregate open-risk ceiling;
- a same-event conflict mutex;
- shock entry stand-down.

Forbidden risk repairs:

- hour/session/day/month masks;
- previous-day, previous-week, or previous-month profit gates;
- loss-streak or outcome-derived alpha filters;
- threshold siblings chosen after viewing the result.

The target runtime risk budget, if a final portfolio qualifies, is no more than `0.50%` initial risk per position, `1.00%` aggregate risk per specialist, and `2.00%` aggregate portfolio open risk. Exact MT5 must verify the broker minimum-lot behavior before any forward use.

## Portfolio admission gates

Only standalone-qualified components may enter the combined exact-MT5 test.

- win rate at least `50%`;
- average-win/average-loss at least `2.00`;
- profit factor at least `2.50`;
- stressed profit factor at least `2.00` and stressed net positive;
- each added specialist contributes positive stressed net and at least `10%` incremental net versus the frozen prior portfolio;
- no specialist is negative in its owned regime;
- top-ten-winners-removed and top-three-days-removed net remain positive;
- best-month share no more than `30%`;
- exact combined MT5 balance and equity DD are both no more than `115%` of the frozen control and equity DD relative is no more than `20%`;
- net profit / maximum equity DD at least `3.00`;
- positive owned-regime episodes and positive months do not decline after adding a specialist.

## Test sequence and kill discipline

1. Clean, unmasked R1 exact requalification.
2. One durable, scale-normalized R2 family exact test.
3. Exact R1+R2 with fixed source ownership and risk accounting.
4. One compression-release/transition family exact test.
5. Pairwise overlap and replacement audit.
6. One exact three-specialist portfolio test.
7. Forward shadow only after every gate above passes.

Immediate kill conditions are any core alpha failure, profit primarily earned outside the owned regime, forbidden mask dependency, concentration failure, unexplained execution mismatch, recent-single-episode dependence, or portfolio equity-DD breach. After a kill, that family is frozen; the result does not authorize a threshold sibling or combined test.

