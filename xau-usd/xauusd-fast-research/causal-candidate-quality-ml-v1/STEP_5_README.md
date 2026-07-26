# Step 5 Locked Shared-Account Portfolio Evaluation

> **Account-currency correction:** Step 5.1 found that demo account `1033030`
> is denominated in AED, not USD. Step 5's account-specific risk and drawdown
> percentages are therefore superseded for that account. See
> `STEP_5_1_README.md`; the corrected fixed-0.01-lot portfolio fails and is not
> authorized for MT5 attachment.

Step 5 evaluates the canonical mechanical candidate families together on one
fixed 0.01-lot account. ML remains offline. The result is historical research,
not permission to alter MT5 or trade.

## Result

The locked decision is
`STEP_5_HISTORICAL_PORTFOLIO_GATE_PASS_RESEARCH_ONLY`. All 18 preregistered
checks passed for the primary `NINE_ALL_CANDIDATES_GOVERNED` policy.

| Window | Trades | Trades/weekday | Net USD | PF | Floating DD USD |
|---|---:|---:|---:|---:|---:|
| 3M | 77 | 1.185 | 338.07 | 1.590 | 95.43 |
| 6M | 154 | 1.194 | 1,075.42 | 1.862 | 146.59 |
| 1Y | 360 | 1.379 | 1,345.08 | 1.574 | 146.59 |
| 2Y | 766 | 1.467 | 1,890.24 | 1.503 | 230.76 |
| 5Y | 1,413 | 1.084 | 2,489.57 | 1.454 | 275.00 |
| 10Y | 1,989 | 0.763 | 2,934.68 | 1.425 | 275.00 |
| Full 2010-2026 | 2,089 | 0.485 | 3,161.40 | 1.438 | 275.00 |

The maximum full-history floating drawdown is 7.53% of the USD 3,654.45
starting account. No hard stop fired and every account-governor invariant held.
The primary policy accepted 2,089 candidates and rejected the rest for explicit
episode, broker, overlap, position, risk, or daily-entry reasons.

Important limitations:

- The one-trade-per-weekday target is achieved over the latest five, two, and
  one years, but not over ten years or full history.
- Only 13 of 20 six-month blocks were profitable, exactly the locked 65% gate.
- Recent profit is concentrated in V57, V7, V8, and R2. R1 was nearly flat over
  one year and negative over six months; V25 was negative over one year.
- All history was already exposed during research. This result is not an
  untouched confirmation test.
- Floating drawdown is a conservative bid/ask M5 envelope, not an exact
  tick-level liquidation simulation.
- Passing Step 5 does not authorize ML, MT5, shadow, demo, or live execution.

Lock the execution and risk contract before opening combined outcomes:

```powershell
uv run --no-project --with-requirements requirements-step5.txt python lock_step_5_contract.py
```

Run the evaluation:

```powershell
uv run --no-project --with-requirements requirements-step5.txt python run_step_5.py
```

Verify all artifacts and reproduce the primary account decisions:

```powershell
uv run --no-project --with-requirements requirements-step5.txt python verify_step_5.py
```
