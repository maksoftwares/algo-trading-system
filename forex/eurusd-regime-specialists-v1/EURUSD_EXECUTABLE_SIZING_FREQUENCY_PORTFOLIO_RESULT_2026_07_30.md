# EURUSD executable-sizing frequency portfolio result

Date: 2026-07-30

Status: **EXECUTABLE_SIZING_PORTFOLIO_REJECTED**

Demo-order authorization: **false**

## Decision

Restoring the protected portfolio's previously broker-tested executable sizes
improved the near-frequency portfolio substantially, but it failed the frozen
second-year winner-concentration gate. It is the strongest near-target
historical benchmark so far, not a deployable portfolio.

| Window | Trades | Trades/weekday | Coverage | Win rate | Payoff | PF | Stressed PF | Best-5%-removed PF | Net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full two years | 447 | 0.856 | 43.30% | 60.18% | 0.997 | 1.507 | 1.401 | 1.055 | +$144.93 |
| First 12 months | 265 | 1.015 | 49.43% | 63.40% | 0.962 | 1.667 | 1.545 | 1.210 | +$98.62 |
| Second 12 months | 182 | 0.697 | 37.16% | 55.49% | 1.071 | 1.336 | 1.246 | 0.872 | +$46.31 |

Maximum closed-trade drawdown was $24.96 and maximum concurrency was two.
The full portfolio passed eleven of twelve frozen gates.

## Failed gate

The second-year PF after removing its largest 5% of winners was 0.872. The
requirement was at least 1.00.

This is not a cosmetic failure. Although second-year PF was 1.336 and stressed
PF was 1.246, its profit did not survive removal of ten large winners. The
recent edge is therefore still too concentrated to treat as stable.

## Sizing boundary

No optimized sizing grid was used:

- protected chop remained at its broker-tested 0.02 lot;
- protected compression remained at 0.01 lot;
- every gated RSI trade remained at 0.01 lot;
- the 0.5-pip stress charge scaled linearly with volume.

No trade or gate decision changed. Raising protected size again, reducing RSI
below the broker minimum, or changing the winner-removal rule after seeing the
result would be a post-result rescue and is prohibited.

## Practical implication

For the average-frequency definition, this is close to the user's requested
goal: 0.856 trades/weekday with full PF 1.507. But frequency weakened to 0.697
in the second year, coverage remained only 37.16%, and concentration failed.

The honest next step for this exact candidate is disarmed prospective
observation. Additional historical selection cannot convert the inspected
two-year result into fresh evidence.

## Reproducibility

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_executable_sizing_frequency_portfolio.py
```

Hashes:

- Frozen config:
  `9128c198ebc128c3da82cfbeda719ffb7c6927470635e61f9f54e7845ed1b6f8`
- Selected combined source:
  `b977310f469648aa7301a9cac5cec1643c6cde92155519eb19246981bf93afa9`
- Protected executable source:
  `3b61273712c75d5aa5cf8ef9d46c71170687ec34fcd9156bfccccf15e8653e43`
- `RESULT.json`:
  `670899b2b5aa47766873d02ebd668d3cf70988009945341bde8400f99c39b4fa`
- `RESULT.md`:
  `22de20228c514ec66310c1221e868a31f087c78b7b021eaf5b433e2bbaba0a5f`
- `EXECUTABLE_SIZING_TRADES.csv`:
  `6dc70442904caff2f71dd0f4bbf5fcd58957d9ec140f6391c49ac7281f988fb0`
