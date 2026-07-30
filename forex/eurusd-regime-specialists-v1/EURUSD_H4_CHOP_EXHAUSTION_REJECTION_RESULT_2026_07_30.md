# EURUSD H4 chop exhaustion-rejection result

Date: 2026-07-30

Status: **DEVELOPMENT_REJECTED_VALIDATION_UNOPENED**

Demo-order authorization: **false**

## Decision

The frozen later-session H4 chop failed-auction rule had enough capacity but
negative development expectancy. Locked 2022H2-2026H1 validation remained
unopened.

| Scope | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Full development | 321 | 43.61% | 1.157 | 0.895 | -15.95 |
| Early 2017-2019 | 172 | 43.02% | 1.103 | 0.833 | -13.60 |
| Middle 2020-2022H1 | 149 | 44.30% | 1.216 | 0.967 | -2.35 |
| Long | 155 | 41.94% | 1.254 | 0.906 | -6.78 |
| Short | 166 | 45.18% | 1.074 | 0.885 | -9.17 |

The extra 0.5-pip result was PF 0.848 and -23.71R. Best-5%-removed PF was
0.727 and maximum closed-trade drawdown was 28.25R. Both directions were
negative, so deleting a side cannot repair the family.

The result is useful because it separates capacity from edge: H4 chop supplied
many later-session failed-auction signals, but a fixed 1.5R fade did not
monetize them. The envelope, clock, side, body, stop, target, and hold are
retired together without outcome-based adjustment.

## Next evidence target

The original four-trade active-day diagnostic contains a different clue:
days with exactly four independently generated RSI/Bollinger opportunities
had PF 1.444 across 496 trades, but the final daily count was selected with
hindsight. The next legitimate test is whether that high-opportunity day can
be forecast at 00:00 UTC using only completed prior-day information, followed
by locked walk-forward economics.

## Reproducibility

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_h4_chop_exhaustion_rejection.py
```

Hashes:

- Frozen config:
  `deee7c0c6b7f476096a626ae9a874d538b4e804c2a454858d873ea0519afe2b5`
- Source data:
  `8281d96ccbc3488f98586894fe58f6988eaa5376601a0bfaec874fd9f08f1f45`
- `RESULT.json`:
  `b93629bad617aa0e327272364f099bdff2ac6098b0e9dd9cde6d4c4c246904bd`
- `RESULT.md`:
  `5032738393bc51f49cefdaaa3513912dccbfff911feadd82b46764d93a7f4b2c`
- `VALIDATION_TRADES.csv`:
  `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6`

