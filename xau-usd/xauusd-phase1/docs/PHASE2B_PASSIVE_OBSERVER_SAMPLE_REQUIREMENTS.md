# Phase 2B Passive Observer Sample Requirements

Status: ACTIVE REQUIREMENTS

Phase 2B is a passive, non-execution lane. Its purpose is to observe real-time would-signals and projected cost feasibility so a future cost-aware candidate can be drafted without weakening the canonical Phase 2 block.

## Authority Boundary

| Field | Required value |
| --- | --- |
| Broker-side action | Forbidden |
| Experimental demo order logs as Phase 2 evidence | Forbidden |
| Canonical Phase 2 authorization | Forbidden |
| Live trading authorization | Forbidden |
| Valid output | Research evidence for a new locked Phase 0R hypothesis |

## Minimum Sample

| Requirement | Target | Reason |
| --- | ---: | --- |
| Active market days | >= 20 | Avoid one-session or one-news-cycle bias. |
| Unique family events preferred | >= 300 | Enough events for cost_R distribution review. |
| Unique family events minimum | >= 100 | Allowed only with an explicit low-sample warning. |
| Cost_R coverage | 100% | Every would-signal must have projected cost. |
| Stale ticks | Excluded or flagged | Prevent stale market data from creating fake cost feasibility. |
| Weekend and rollover rows | Identified | Thin-liquidity rows must not blend into normal session reads. |
| Spread buckets | Reported | Required to detect median/P95 cost fragility. |
| Stop-distance buckets | Reported | Required to detect tight-stop cost failure. |
| Session and hour buckets | Reported | Required to find timing-dependent cost viability. |

## Required Reports

```text
PHASE2B_COST_FEASIBILITY_REPORT.md
PHASE2B_STOP_DISTANCE_SURVIVAL_REPORT.md
PHASE2B_SPREAD_REGIME_SURVIVAL_REPORT.md
PHASE2B_SESSION_COST_REPORT.md
PHASE2B_HOUR_OF_DAY_COST_REPORT.md
PHASE2B_CANDIDATE_FEASIBILITY_DECISION.md
```

## Decision Rule

Phase 2B can identify a cost-feasible subset. That subset must then become a new hypothesis, be SHA256-locked, and pass Phase 0 plus measured-cost revalidation. Phase 2B cannot unsuspend `breakout_retest_v1.0`.
