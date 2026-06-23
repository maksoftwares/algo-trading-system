# A3 ML Replay Promotion Policy V1

Status: LOCKED_RESEARCH_POLICY
Decision source: reviewer decision `ALLOW_FUTURE_PROMOTION_WITH_CONDITIONS`
Created: 2026-06-22

## Scope

This policy covers Strategy Tester replay evidence imported through C56 and analyzed through C57.

Current replay source:

- Source type: `strategy_tester_replay`
- Current label status: `REPLAY_OBSERVER_ONLY`
- Replay lane: `A3_Account3BreakoutTier1CompatExecutor_XAUUSD_M5`
- Account: A3 / `1033669`

## Current Decision

No replay row is promoted now.

All imported replay rows remain:

- `source_type=strategy_tester_replay`
- `label_status=REPLAY_OBSERVER_ONLY`
- `candidate_trainable=false`

Replay may be used only as quarantined research evidence unless a separate human-signed promotion review approves a narrower research tier.

## Permanent Exclusions

Replay rows must never supply execution labels.

Replay rows must never supply:

- `y_win`
- `y_net_R`
- MAE/MFE execution outcomes
- fill quality
- slippage adequacy
- broker execution proof

Replay rows must never count toward C03 gates:

- market setup groups
- active weeks
- regime diversity
- feature budget
- minority labels
- slippage readiness

Replay rows must never enter live out-of-sample validation.

Replay rows must never authorize:

- model training
- Python demo predictions
- EA consumption
- broker action
- live trading

## Future Research Tier

The only future tier that may be considered is:

```text
REPLAY_PROMOTION_CANDIDATE
```

This status is defined but must not be assigned to any row until a separate promotion review explicitly approves it.

`REPLAY_PROMOTION_CANDIDATE` means:

- research-only
- non-gating
- non-label-bearing
- not execution evidence
- excluded from C03
- excluded from slippage adequacy
- excluded from live out-of-sample validation
- separate or down-weighted in any research experiment

## Promotion Preconditions

Before any replay row can move from `REPLAY_OBSERVER_ONLY` to `REPLAY_PROMOTION_CANDIDATE`, all conditions must pass:

1. Source integrity and A3 ML tests are green.
2. C03 remains live-only and no replay row can move any C03 gate.
3. Exact cross-source overlaps are removed, with live data authoritative.
4. Fuzzy/date-direction overlaps are resolved through a documented `market_setup_group_id` dedup pass.
5. Replay-vs-live feature distribution and drift comparison is reviewed.
6. Replay-vs-live regime/session coverage comparison is reviewed.
7. A human-signed promotion decision names the exact subset, allowed use, weighting, validation treatment, and rollback rule.
8. Any model experiment touching replay is validated against live-only out-of-sample evidence.

## Current Replay Analysis Reference

C57 found:

- Replay signal rows: `23124`
- Would-signal rows: `1269`
- Exact live setup overlap: `14`
- Date-direction live overlap: `215`
- Replay active weeks: `17.14`
- Direction balance: `LONG=598`, `SHORT=671`

These values support research planning only. They do not improve C03 readiness.

## Required Future Reports

Before any promotion review, Codex must produce:

- cross-source exact and fuzzy dedup report
- replay-vs-live feature distribution report
- replay-vs-live regime/session coverage report
- trainable-label exclusion test
- C03 replay-exclusion test
- human promotion decision template

## Authorization State

This policy authorizes no runtime action.

Current authorization must remain:

- training authorized: false
- Python demo predictions authorized: false
- EA consumption authorized: false
- broker action authorized: false

## Next Allowed Work

Allowed:

- research reports
- dedup reports
- representativeness reports
- policy tests
- reviewer decision templates

Not allowed:

- assigning `REPLAY_PROMOTION_CANDIDATE`
- model training
- Python demo predictions
- EA handoff publication
- broker action
