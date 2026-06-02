# Phase 0R Lower-Cost Candidate Spec

Overall status: ACTIVE_RESEARCH_SPEC

Phase 0R exists because the breakout-retest family passed historical Phase 0 but failed measured-cost survivability. The replacement search must start with measured cost, not bolt it on after historical optimism.

## Required Candidate Rules

1. Candidate must not be same-family level/retest unless explicitly marked same-family.
2. Candidate should operate on H1/H4/D1/W1 or use wider stops.
3. Candidate must include expected median stop distance.
4. Candidate must include expected cost_R under measured median and P95 spread.
5. Candidate must be pre-rejected if measured P95 cost_R is structurally too high.
6. Candidate must use the measured 50/75 point spread model from the start.
7. Candidate must use fixed-notional R reporting from the start.
8. Candidate must not optimize after first failure.
9. Candidate must not claim diversification unless the mechanic family and decision timeframe are genuinely different.

## Measured-Cost Precheck

Measured spread references:

```text
Measured median spread: 50 points
Measured P95 spread: 75 points
```

Precheck rule:

```text
If expected median stop distance < 250 points:
    candidate is cost-fragile and requires explicit written justification.

If expected P95 cost_R > 0.30R:
    candidate is not eligible for canonical execution research.
```

Preferred profile:

```text
median stop distance >= 375-500+ points
expected holding time > 4h
decision timeframe H1/H4/D1/W1
mechanic independent from M5 level/retest continuation
```

## Preferred Candidate Families

| Priority | Family | Reason |
| --- | --- | --- |
| 1 | D1 compression -> H4 expansion | Wider invalidation and lower sensitivity to retail spread. |
| 2 | H4 trend continuation after D1 volatility contraction | Better cost budget and longer holding period. |
| 3 | H4 reversal after macro-volatility shock with wide stop | Independent trigger class if macro proxy is reliable. |
| 4 | D1/H4 gold volatility-regime continuation | Regime-based, not local level/retest. |
| 5 | Options-skew / CVOL-informed H4 reversal | Potentially independent, but requires licensed CME history. |
| 6 | Weekly-level rejection with H4 confirmation | Wide invalidation and low turnover. |

## Avoid For Now

- more M5 retest variants
- more same-family round-number retests
- more same-bar swing-level breakout variants
- tight-stop scalps
- strategy filters added to failed `breakout_retest` v1.0
- same-family variants claimed as diversification

## Command

Use the precheck helper before registering any new candidate:

```powershell
python scripts\phase0r_candidate_cost_precheck.py --candidate <name> --median-stop-points <points>
```

The precheck is not a full Phase 0 pass. It only determines whether the candidate is structurally worth researching under the measured spread environment.
