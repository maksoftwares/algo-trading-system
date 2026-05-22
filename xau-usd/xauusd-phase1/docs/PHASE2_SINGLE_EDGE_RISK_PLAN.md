# Phase 2 Single-Edge Risk Plan

Last updated: 2026-05-22

This plan reflects Review #3: `swing_breakout_retest_v0` is same-family with `breakout_retest`, so the v1 portfolio is a single-edge breakout-retest family with two timeframe flavors. It must not be treated as diversified.

## Approved Edge Family

| Expert | Status | Diversification treatment |
| --- | --- | --- |
| `breakout_retest` | Approved future expert | Primary expression of the breakout-retest family. |
| `swing_breakout_retest_v0` | Approved future expert candidate | Same-family variant; useful for telemetry, not independent diversification. |

Rejected experts and rejected research candidates remain rejected unless a new versioned hypothesis is written, hash-locked, and rerun through Phase 0.

## Capital Principle

Because the system currently has one edge family, all future capital decisions must be more conservative than a multi-expert portfolio plan.

Phase 2 remains paper-mode only. No live capital is authorized by this document.

## Draft Step Ladder

| Stage | Authorization condition | Risk posture |
| --- | --- | --- |
| Phase 2 paper | Phase 1 acceptance PASS, measured-cost gates PASS, owner approval PASS | Paper-only, measure cost and drift. |
| Live micro pilot | Separate future approval after paper evidence | Lower than the original 0.25% per trade assumption. |
| Step 1 | Paper/live review shows cost-adjusted expectancy >= +0.10R and drift acceptable | Small fixed risk, no compounding. |
| Step 2 | Additional review period passes without concentration or drift breach | Modest increase only after written review. |
| Stop | Cost, drawdown, drift, logic, or execution trigger fires | Suspend the family and return to research. |

## Risk Constraints To Preserve

| Constraint | Rule |
| --- | --- |
| Edge-family exposure | Treat both approved variants as one correlated family. |
| Sizing | No portfolio-diversification uplift until a genuinely independent expert passes Phase 0. |
| Compounding | Disabled through paper and any future micro pilot. |
| Recovery behavior | No martingale, grid, averaging down, or loss recovery. |
| Live execution | Not authorized until a later phase. |
| Cost floor | Suspend if measured net expectancy falls below +0.10R. |

## Drift And Review Triggers

Immediate review is required if any trigger fires:

| Trigger | Rule |
| --- | --- |
| Cost drift | Measured cost exceeds the level that keeps net expectancy >= +0.10R. |
| Trade-count drift | Observed frequency materially departs from Phase 0 expectation. |
| PF drift | Rolling PF falls below the pre-defined warning band. |
| Drawdown | Daily, weekly, monthly, or rolling drawdown reaches warning state. |
| Concentration | A small number of trades explain too much PnL. |
| Execution quality | Spread, slippage proxy, stale tick, or broker-state warnings increase. |
| Logic mismatch | Paper observations show behavior outside the locked hypothesis. |

## Required Review Output

Every formal review must end with exactly one state:

```text
CONTINUE
CONTINUE_WITH_REDUCED_RISK
SUSPEND
RETIRE
RESEARCH_REPLACEMENT
```

No review may rewrite the original hypothesis to fit observed results.
