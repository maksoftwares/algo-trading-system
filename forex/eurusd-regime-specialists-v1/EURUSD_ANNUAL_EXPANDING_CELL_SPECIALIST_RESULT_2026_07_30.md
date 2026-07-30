# EURUSD annual expanding-cell specialist result

Date: 2026-07-30

Status: **DEVELOPMENT_REJECTED_VALIDATION_UNOPENED**

Demo-order authorization: **false**

## Decision

The fixed annual-refit cell specialist supplied useful frequency and narrowly
cleared aggregate development PF, but its edge did not transfer consistently
between development years. The locked 2024-2026H1 validation remained
unopened.

| Development scope | Trades | Trades/weekday | Win rate | Payoff | PF | Stressed PF | Net R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022-2023 | 72 | 0.1385 | 48.61% | 1.225 | 1.158 | 1.079 | +5.81 |
| 2022 | 36 | 0.1385 | 38.89% | 1.053 | 0.670 | 0.628 | -7.31 |
| 2023 | 36 | 0.1385 | 58.33% | 1.360 | 1.905 | 1.766 | +13.12 |

The full development result passed the frozen trade-count, frequency, PF,
stressed-PF, and drawdown gates. It failed two non-negotiable robustness
gates:

- 2022 PF had to exceed 1.00 but was 0.670;
- best-5%-of-winners-removed PF had to be at least 1.00 but was 0.995.

The 0.5-pip stressed result earned only +3.02R, and fixed 0.01-lot stressed
P&L was -$1.48 after applying the additional per-trade cost convention.

## What the annual refit revealed

Ten cells were selected at each January boundary, but only four were shared
between the 2022 and 2023 lists. The selection was dominated by neutral-auction
cells: eight of ten in 2022 and six of ten in 2023.

This is causal drift adaptation, not stable edge. The annual refit changed the
cell list, but it could not prevent a full losing year. The profitable 2023
block masked the negative 2022 block in the aggregate result, which is exactly
why the each-year gate was frozen before execution.

No threshold, minimum-trade, cell-dimension, owner, seed, hour, or refit-period
repair is permitted for this exact family.

## Capacity implication

This family demonstrated that approximately 0.14 additional trades per
weekday are available from a distinct time-cell mechanism. It did not
demonstrate that those trades have stable positive expectancy. It therefore
adds zero admissible trades to the protected portfolio and does not reduce the
416-trade central frequency shortfall.

## Reproducibility

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_annual_expanding_cell_specialist.py
```

Hashes:

- Frozen config:
  `e9d58ea081086a9f905d46efd440c397c90d80b03e896c31c26b5de322aef327`
- Opportunity ledger:
  `d422d6dc6521fc21ff9695462d662f2ff1d753144b363ca66ca160aed4e5368f`
- `RESULT.json`:
  `cfd186119ce1a563c3b09d3a537a43ad8d9a721a3217002508b00a2263f03670`
- `RESULT.md`:
  `eecfd50eaf1f80edafddb91754f359c9507e40f299516d30257adfd5229c7089`
- `TRADES.csv`:
  `3f349379f11b5b84f45b5a28be841404a9557a192a2ae40ad17479935c3b8459`
- `ANNUAL_SELECTED_CELLS.csv`:
  `0e1d0f9e022feb1bc31fd21bf4f932b59f87a22f3ef699c0ac0313492ee702ec`
