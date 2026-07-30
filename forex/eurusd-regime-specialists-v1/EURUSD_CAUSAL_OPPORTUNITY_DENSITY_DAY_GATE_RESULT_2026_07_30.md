# EURUSD causal opportunity-density day gate result

Date: 2026-07-30

Status: **DEVELOPMENT_REJECTED_VALIDATION_UNOPENED**

Demo-order authorization: **false**

## Decision

The fixed midnight classifier could not causally recover the hindsight
exact-four-opportunity effect. It improved precision relative to the rare
target base rate, but activated too few dates and its accepted trades lost.
Locked 2024-2026H1 validation remained unopened.

| Development 2022-2023 metric | Result |
|---|---:|
| Weekdays | 520 |
| Actual exact-four dates | 28 |
| Target base rate | 5.38% |
| Activated dates | 9 |
| Correct exact-four dates | 1 |
| Precision | 11.11% |
| Recall | 3.57% |
| Trades | 9 |
| Trades per weekday | 0.0173 |
| Win rate | 33.33% |
| Payoff | 1.478 |
| Profit factor | 0.739 |
| Stressed PF | 0.686 |
| Net R | -1.58 |
| Best-5%-removed PF | 0.492 |

The classifier selected two dates in 2022 but neither contained a trade. In
2023 it activated seven dates and produced nine trades at the same negative
aggregate economics.

No threshold relaxation is permitted. Lowering the fixed 0.50 threshold after
seeing this sparse result would be a retrospective capacity rescue and would
not establish that the exact-four state is predictable. The historical PF
1.444 density bucket remains a hindsight artifact because its final same-day
count is not known at midnight or at the earlier entries.

## Reproducibility

```powershell
uv run --offline --with pandas --with numpy --with pyarrow --with scikit-learn python run_causal_opportunity_density_day_gate.py
```

Hashes:

- Frozen config:
  `4f991a16eedd06ea2eca15d22a35ca33fc7f08f28c19ee2459ebe9df52653c09`
- Market source:
  `8281d96ccbc3488f98586894fe58f6988eaa5376601a0bfaec874fd9f08f1f45`
- Opportunity ledger:
  `d422d6dc6521fc21ff9695462d662f2ff1d753144b363ca66ca160aed4e5368f`
- `RESULT.json`:
  `a840f3837c6ea3544753272a82cf53dae3226edd80a81db4c7fba73406faf16c`
- `RESULT.md`:
  `5f28ac9b8e902094efbfb78d43a3f23359712abe4f87c7af83c080fa39e544e2`
- `DAY_DECISIONS.csv`:
  `a6944c92b497d4a050d18857cf8600f2263be14ef18afecde2a7df7db70048a5`
- `TRADES.csv`:
  `d140bec8f1174ea67f4e16a685f17a989f5921bc16226a05bd3ea2ee742cebf6`

