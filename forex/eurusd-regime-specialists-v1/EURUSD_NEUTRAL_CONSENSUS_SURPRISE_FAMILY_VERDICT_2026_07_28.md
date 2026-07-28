# EURUSD Neutral consensus-surprise family verdict

## Verdict

`REJECTED_NEUTRAL_CONSENSUS_SURPRISE_FAMILY_V1`

Both preregistered variants passed their outcome-blind capacity census, and
both failed the frozen profitability and oracle-resemblance gates. The exact
family is closed without selecting its favorable 2024 or 2026 H1 blocks.

No demo or live action is authorized.

## Outcome-blind census

The reconciled source contained 262 CPI, PPI, and NFP rows. Forty-two equal
actual/forecast observations stayed in cash, leaving 220 directional release
surprises.

| Variant | Candidates | Active dates | Development | 2023 | 2024 | 2025 | 2026 H1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Macro surprise carry | 404 | 101 | 248 | 60 | 36 | 44 | 16 |
| Price agreement | 212 | 97 | 125 | 33 | 17 | 25 | 12 |

Both variants passed the total, development, every-forward-window, recent,
both-side, and all-family capacity gates. Therefore the single locked
backtest was permitted for both.

## Full-history result

| Variant | Trades | Win rate | Payoff | PF | Net ticket R | Fixed 0.01 lot |
|---|---:|---:|---:|---:|---:|---:|
| Macro surprise carry | 404 | 34.41% | 1.439 | 0.755 | -66.60R | -$26.64 |
| Price agreement | 212 | 34.91% | 1.439 | 0.772 | -32.30R | -$12.92 |

The desired payoff shape survived execution, but the side selector did not.
At a 1.439 realized payoff, break-even requires approximately 41.00% wins.
The two rules missed that level by 6.59 and 6.10 percentage points.

The price filter reduced activity by 47.52% but did not materially improve
win rate or PF. Its LONG slice passed at PF 1.151, while its 140 SHORT trades
returned PF 0.617. That is diagnostic only: deleting the losing side after
inspection is prohibited.

## Chronological windows

### Macro surprise carry

| Window | Trades | Win rate | PF | Net ticket R |
|---|---:|---:|---:|---:|
| 2019-2022 development | 248 | 33.87% | 0.737 | -44.20R |
| 2023 | 60 | 25.00% | 0.480 | -24.00R |
| 2024 | 36 | 47.22% | 1.288 | +5.60R |
| 2025 | 44 | 27.27% | 0.540 | -15.10R |
| 2026 H1 | 16 | 68.75% | 3.166 | +11.10R |

### Macro surprise with price agreement

| Window | Trades | Win rate | PF | Net ticket R |
|---|---:|---:|---:|---:|
| 2019-2022 development | 125 | 36.00% | 0.809 | -15.63R |
| 2023 | 33 | 27.27% | 0.540 | -11.33R |
| 2024 | 17 | 47.06% | 1.279 | +2.57R |
| 2025 | 25 | 20.00% | 0.360 | -13.13R |
| 2026 H1 | 12 | 58.33% | 2.015 | +5.20R |

Development, 2023, and 2025 lost for both variants. The profitable 2024 and
2026 H1 blocks do not define a causal activation rule and cannot be selected
after returns are known.

## Requested last six months

The January-June 2026 slice was profitable for both rules, but it contained
only four active dates:

| Date | Carry tickets / wins / net | Agreement tickets / wins / net |
|---|---:|---:|
| 2026-01-12 | 4 / 3 / +3.40R | 2 / 1 / +0.45R |
| 2026-02-02 | 4 / 3 / +3.40R | 3 / 2 / +1.93R |
| 2026-03-20 | 4 / 2 / +0.90R | 3 / 1 / -0.58R |
| 2026-06-12 | 4 / 3 / +3.40R | 4 / 3 / +3.40R |

The carry rule's 16 tickets equal +2.775 portfolio R after the frozen
0.25R-per-ticket weighting and +$4.44 at fixed 0.01 lot. The agreement rule's
12 tickets equal +1.300 portfolio R and +$2.08. Under the extra 0.5-pip
round-trip stress, they remained positive at +9.10 and +3.70 ticket R.

These are four clustered release states rather than 16 or 12 independent
trading days. They are useful as a prospective hypothesis signal, not as demo
evidence against three losing historical blocks.

## Robustness and oracle resemblance

| Diagnostic | Carry | Price agreement | Required |
|---|---:|---:|---:|
| Best-5%-removed PF | 0.641 | 0.657 | >= 1.000 |
| Extra-0.5-pip PF | 0.616 | 0.629 | >= 1.000 |
| Exact oracle precision | 20.54% | 17.92% | >= 40.00% |
| Same-side 15-minute precision | 37.13% | 45.75% | >= 45.00% |

Price agreement barely cleared the tolerant resemblance gate, but failed
profitability, exact resemblance, both-side, every-window, winner-removal, and
cost-stress gates. Carry failed both resemblance gates and the same economic
gates.

## Interpretation and next boundary

The consensus surprise is not a stable 72-hour direction selector for the
Neutral oracle's midnight clocks. The favorable recent block does suggest
that a genuinely different, prospectively captured event-time hypothesis may
be worth defining, but N39 itself may not be repaired or activated only in
2026.

The historical consensus field was retrieved post-event, so even a passing
result would have required prospective pre-release forecast capture before
demo consideration.

## Integrity

- Census SHA-256:
  `f06d9051dd7669b9d88f1631e1cc36ed3baaca4020f4ce364bc60b0d181a93e5`
- Candidate manifest SHA-256:
  `41c0ee369272da53887be14f18672fc0c77bbd643873ded3c8cb57f75214dfad`
- Result SHA-256:
  `afaa058b6676a27ba966a0d2f46db801586f4fa64c64cfa6706e4f89ecc80959`
- Trade ledger SHA-256:
  `433e38aadb4467fd131c1e535e28deb66583809a2ad8e0b0339888d81c3ea8d5`
- Daily portfolio SHA-256:
  `6d7e65a013da0d94e2e881a6df3c28e39683a92ab5380619fcd9eb10215e3dc2`
- Oracle matches SHA-256:
  `b2bb01d526a3b2a443c601a88ae3bab79b2f7c1639cace2d6d8818ee920610a4`
