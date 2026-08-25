# V60 Dynamic Capacity Twin Prospective V19

## Purpose

V19 closes one evidence gap left by the sealed V6 executed-trade observer. The
existing observer can measure V60 trades that V6 would retain or veto, but it
cannot measure a later candidate that V6 could accept because an earlier veto
freed portfolio capacity. V19 resolves every causally generated candidate from
the Capital.com XAUUSD tick stream and replays the deployed V60 policy and the
frozen V6 policy as independent, read-only portfolio twins.

V19 is evidence collection only. It cannot send, modify, or close an MT5 order.
It does not change the deployed V60 portfolio, its feeds, its risk settings, or
account 1033030.

## Prospective boundary

Clean evidence starts at `2026-08-26T00:00:00Z`. Candidate outcomes before this
boundary may be used only for resolver and replay parity checks. They cannot be
used in V19 acceptance metrics.

## Frozen policies

### Baseline

The baseline is the deployed V60 canonical portfolio with the deployed
drawdown-protection overlay. ML execution and ML top-ups are excluded.

### Challenger

The challenger is frozen Dynamic V6:

1. Apply the V2 per-source rolling-profit-factor/rank veto.
2. Apply the V57 long weak-follow-through anti-chase veto.
3. Preserve every other V60 entry, capacity, risk, drawdown, guardian,
   profit-protection, source-exit, and cost rule.
4. Recompute source health from the challenger path. A vetoed outcome cannot
   update later challenger health.

No threshold, source, regime, sizing, exit, or protection search is permitted
inside V19.

## Causal candidate resolution

For each append-only candidate fact at or after the boundary:

1. Use only the first Capital.com tick at or after its scheduled entry and
   within that source's frozen maximum entry delay.
2. Reject entry when spread, risk, source identity, or schema fails the frozen
   V60 rule.
3. Set the executable entry to ask for longs and bid for shorts.
4. Resolve the first executable stop or target hit. If neither is hit, use the
   frozen source horizon where one exists.
5. A candidate with no complete exit window remains unresolved. It must never
   be imputed or silently dropped.
6. Use the frozen 0.01-lot/one-ounce economics, observed bid/ask spread,
   `$0.30` ticket cost, `$0.35` per 24 hours holding cost, and separately report
   the locked `0.05R` stress slippage.
7. Consume only completed UTC tick days for economic metrics. The currently
   open day is inventory only.

Every consumed candidate prefix, tick file, decision row, and generated outcome
must be SHA-256 identified. Mutation, truncation, duplicate candidate IDs,
non-monotonic ticks, or missing causal decision coverage fails closed.

## Portfolio replay

V19 must use the same tick-runtime replay implementation and V6 scenario code
as the locked historical experiment. It may add only a prospective warm-start
adapter that seeds each source's pre-boundary closed count and trailing 20
outcomes from the already frozen warm-start artifact.

The baseline and challenger must receive the same resolved candidate facts and
five-second quote cycles. They must maintain isolated positions, capacity,
daily-entry counts, drawdown state, protection state, and health state.

Replacement-capacity trades are candidates accepted by V6 but rejected by V60.
They must be reported separately from common accepted trades and V6 vetoes.

## Fixed identities

- Deployed V60 config SHA-256:
  `739024be8beef82253f708bd98e5707666a395439526b7aff3251a77523e3120`
- Deployed protection overlay SHA-256: recorded in the V19 lock before launch.
- Frozen V6 config SHA-256:
  `369dba6fecbd3c9e851bcd0a8f7652089254677ca42a4f5b2c9a17fd344849d6`
- Frozen V6 scenario SHA-256:
  `6d762645a27330c985a85b0c4612036b904ea61a7bd889d423e5f33c8d4a5c87`
- Shared historical evaluator SHA-256:
  `8be567eb5a0f355a3c47b524838aeb6608f12e6b3d5f3da5a0c9b69dd5ca6dad`
- Frozen prospective warm-start SHA-256:
  `046d5e963489adb7b3b4dceb740be61db8c70d04307076ecb6501315a8e1d8e6`
- Sealed V6 prospective contract SHA-256:
  `23ce7ca7e152e41a3dfa8fa7b0a22d600824eca89bed638556bc45577433c0dc`

The implementation, resolver, runner, and all additional dependencies must be
hashed in a machine-readable contract before the first V19 economic result is
opened.

## Acceptance gates

All gates are comparative against the V60 twin over the same clean interval:

1. At least 90 elapsed calendar days.
2. At least 100 causally resolved candidate facts.
3. At least 20 routing divergences in total.
4. At least 10 resolved V6 vetoes.
5. At least 10 resolved replacement-capacity trades accepted only by V6.
6. Candidate, rank, causal-feature, outcome, and five-second quote coverage are
   each 100% for the scored population.
7. V6 net P/L is strictly higher.
8. V6 profit factor is not lower.
9. V6 closed and sampled-equity drawdown are not higher.
10. V6 trade retention is at least 99% of V60.
11. V6 losing-month burden and worst month are not worse.
12. No completed calendar month has lower V6 P/L than V60.
13. The same comparative gates pass after an additional `$0.10` and `$0.20`
    cost per accepted trade.
14. No open-position accounting error, restart discontinuity, evidence-chain
    break, input mutation, or non-finite metric exists.

The sample floors are necessary but not sufficient. A pass remains a review
candidate and does not authorize demo or live deployment.

## Failure and decision rules

- Any identity, causality, coverage, or accounting failure produces
  `FAILED_CLOSED`.
- Before the sample gates mature, the decision is
  `CONTINUE_PROSPECTIVE_CAPACITY_COLLECTION`.
- If a mature comparative gate fails, the decision is
  `KEEP_DEPLOYED_V60_CAPACITY_TWIN_REJECTS_V6`.
- If every gate passes, the decision is
  `V6_CAPACITY_TWIN_PASSES_REVIEW_REQUIRED`.

`deployment_authorized` and `broker_action_authorized` are always `false`.
