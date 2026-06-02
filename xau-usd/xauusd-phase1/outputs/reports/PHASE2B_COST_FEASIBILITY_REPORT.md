# Phase 2B Cost Feasibility Report

Overall status: REVIEW_READY_LOW_SAMPLE

This report reads passive paper-observer logs only. It does not read experimental demo order logs and does not authorize canonical Phase 2, paper-mode execution, demo execution as Phase 2 evidence, or live trading.

## Summary

| Field | Value |
| --- | --- |
| Overall status | REVIEW_READY_LOW_SAMPLE |
| Passive log path | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\paper_observer\passive_cost_observer_log.csv |
| Rows | 269 |
| Unique family events | 154 |
| Active market days | 3 |
| Cost_R coverage | 100.00% |
| Median cost_R | 0.1379 |
| Median net edge_R | 0.3737 |
| Mean cost_R | 0.1972 |
| Mean net edge_R | 0.3144 |

## Cost Gate Counts

| Cost gate | Rows |
| --- | --- |
| COST_BLOCK | 54 |
| COST_OK_ACCEPTABLE | 28 |
| COST_OK_STRONG | 146 |
| COST_WARN | 41 |

## Sample Requirements

| Requirement | Target | Observed | Status |
| --- | --- | --- | --- |
| Active market days | >= 20 | 3 | PENDING |
| Unique family events preferred | >= 300 | 154 | PENDING |
| Unique family events minimum | >= 100 | 154 | PASS |
| Cost_R coverage | 100% | 100.00% | PASS |

## Decision

See `PHASE2B_CANDIDATE_FEASIBILITY_DECISION.md` for the candidate-level passive read.
