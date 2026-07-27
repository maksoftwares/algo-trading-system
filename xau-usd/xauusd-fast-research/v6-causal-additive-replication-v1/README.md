# V6 Causal Additive Replication V1

This quarantined research lane tests one mechanism taken from the external
`regime-teacher-eas-v1` handoff without accepting its postselected family.

The experiment:

1. Rebuilds the full 576-member V6 candidate pool.
2. Selects seven members for each calendar year using only Capital outcomes
   closed before that year.
3. Assigns trades by entry year, resolves duplicate signals by prior rank, and
   applies a continuous two-position Capital-clock lock.
4. Adds conservative slippage, fee, and holding-cost stress.
5. Routes the resulting trades beside immutable V60 under the inherited
   shared-account limits.
6. Recomputes closed and M5 floating-equity results.

Run from this directory:

```powershell
python run_experiment.py
python -m pytest -q
```

All history through 2026-06-30 is development evidence. A pass is only a
historical candidate for a new prospective lane. It never authorizes Python,
EA, demo, live, or broker execution.

## Frozen Outcome

The preregistered experiment **failed and is quarantined**.

- 213 V6 trades were accepted beside the 2,194-trade V60 ledger.
- Stress net P&L increased by $303.59.
- Combined stress PF fell from 1.649 to 1.570.
- Combined closed drawdown rose from $276.87 to $347.03.
- M5 floating drawdown rose from $335.34 to $426.89.
- The candidate failed the five-largest-winners-removed check in every required
  window and breached conservative shared add-on overlap/risk limits.
- 209 of 213 accepted trades were long.

The exact V1 specification must not be translated to MT5 or deployed.
