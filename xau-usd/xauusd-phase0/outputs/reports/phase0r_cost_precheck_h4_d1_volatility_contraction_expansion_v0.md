# Phase 0R Cost Precheck: h4_d1_volatility_contraction_expansion_v0

Overall status: PASS

This precheck only tests structural cost viability under the measured XAUUSD spread environment. It is not a Phase 0R pass, not an edge claim, and not execution authorization.

| Field | Value |
| --- | --- |
| Candidate | `h4_d1_volatility_contraction_expansion_v0` |
| Expected median stop distance | 400.00 points |
| Measured median spread | 50.00 points |
| Measured P95 spread | 75.00 points |
| Measured median cost_R | 0.1250R |
| Measured P95 cost_R | 0.1875R |
| Hard P95 cost_R cap | 0.3000R |
| Preferred stop-budget floor | 375.00 points |
| Result | Candidate clears measured-cost structural precheck. |

## Command Equivalent

```powershell
.\.venv\Scripts\python.exe scripts\phase0r_candidate_cost_precheck.py --candidate h4_d1_volatility_contraction_expansion_v0 --median-stop-points 400
```

## Boundary

The candidate still needs SHA256 registration, implementation, smoke testing, matrix testing, measured-cost revalidation, concentration/frequency audit, and adversarial review before it can be considered beyond research draft status.
