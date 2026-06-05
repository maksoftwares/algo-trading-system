# WR50 Experimental Lane Rules

Document date: 2026-06-04

## Non-Negotiable Rules

1. WR50 EAs are demo-experiment only.
2. WR50 EAs do not authorize canonical Phase 2.
3. WR50 EAs do not modify existing observed EAs.
4. WR50 EAs must use unique magic numbers and comments.
5. WR50 EAs must use minimum/fixed lot only.
6. WR50 EAs must use hard SL/TP on every trade.
7. WR50 EAs must be evaluated only after minimum sample size.
8. WR50 EAs must be retired or revised as new versions if gates fail.
9. WR50 EAs cannot be moved to live without a separate formal review.
10. WR50 EAs cannot override measured-cost suspension of canonical breakout_retest.

## Canonical Boundary

The current canonical state is preserved:

```text
Phase 1 dry-run acceptance: PASS
Canonical Phase 2 paper-mode implementation: NO-GO
Canonical broker-side execution: NO-GO
Live trading / real capital: ABSOLUTE NO-GO
breakout_retest family: COST_SUSPENDED_CANONICAL
Experimental demo executor lane: QUARANTINE / REVIEW ONLY
Phase 0R replacement / cost-aware research: GO
```

WR50 results are research evidence only. They cannot be used as independent diversification evidence, canonical Phase 2 readiness evidence, or live trading authorization.

## Prohibited Mechanics

The WR50 lane forbids:

```text
martingale
grid
averaging down
recovery mode
doubling after loss
moving stop loss farther away
no-stop-loss trades
hedge-and-pray logic
```

The first v0 EAs must send a broker-side pending order with hard SL and TP, then let broker-side SL/TP close the position. No trailing, breakeven, or position modification is part of v0.

## Attribution

Every order/deal/position must include:

```text
unique magic number
short EA comment
full CSV ledger row
experiment id
run id
strategy family
ea version
reason code
```

Attribution must be available at source. It cannot be reconstructed later from incomplete broker history.

