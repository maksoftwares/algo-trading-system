# EURUSD Neutral precious-metals consensus verdict

## Verdict

`REJECTED_NEUTRAL_PRECIOUS_METALS_CONSENSUS_V1`

The hash-locked XAUUSD/XAGUSD consensus rule is closed without reversing its
economic mapping, adding a magnitude threshold, selecting clocks, or filtering
years after outcome inspection.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019-2022 development | 1,074 | 28.96% | 1.439 | 0.587 | -323.38R |
| 2023 validation | 207 | 38.65% | 1.438 | 0.906 | -12.28R |
| 2024 validation | 178 | 28.09% | 1.439 | 0.562 | -57.45R |
| 2025 pseudo-OOS | 194 | 34.02% | 1.439 | 0.742 | -33.85R |
| 2026 H1 pseudo-OOS | 111 | 27.93% | 1.440 | 0.558 | -36.25R |
| Forward total | 690 | 32.90% | 1.439 | 0.705 | -139.83R |

No historical window was profitable. The requested latest six months also
failed decisively: 111 trades, 27.93% wins, 1.440 payoff, PF 0.558, and
-36.25R. At the daily portfolio level they returned PF 0.433 and -9.06
portfolio R.

## Diagnosis

The first-hour metal agreement selected the correct side in 227 of the 436
forward clocks where exactly one EURUSD side reached target first, or 52.06%.
This is slightly above chance but economically insufficient because 254 of the
690 selected clocks were no-winner cases. The resulting unconditional trade
win rate was only 32.90%, well below the roughly 41.0% break-even rate implied
by the realized 1.439 payoff.

The latest six months did not show improvement: conditional direction accuracy
was 49.21%, below chance, and unconditional wins fell to 27.93%.

## Robustness and oracle resemblance

- extra-half-pip stress: PF 0.575 and -226.08R;
- best 5% of winners removed: PF 0.597 and -191.48R;
- forward daily portfolio PF: 0.595;
- forward daily portfolio drawdown: 35.46 portfolio R;
- exact oracle matches: 111 of 690, or 16.09% precision;
- same-side 15-minute oracle matches: 258 of 690, or 37.39% precision.

The tolerant oracle-resemblance gate passed, but the exact-match gate, every
economic gate, and the drawdown gate failed. Entry resemblance without outcome
edge is not deployable evidence.

## Data and integrity

The no-authentication Dukascopy Jetta endpoint supplied the missing XAGUSD
hours; existing local raw history supplied XAUUSD. The normalized compact
source contains 40,481 M5 rows and reproduced byte-for-byte from cache.

Source SHA-256:

`64fbf4e9e0a77b37e738db48a256c230873fce29a532b87c8ed55148c728982f`

Source-manifest SHA-256:

`b2a14d3cf81a156016bcef642e063892d31751edefb84546f6612a25490aac83`

The outcome-blind census and all implementation artifacts were hash-locked
before EURUSD outcomes were loaded. The exact result is deterministic:

`outputs/neutral_precious_metals_consensus/RESULT.json`

Result SHA-256:

`604f9c36cc8c5f29e97151472d122d04a53a90ebf522428e491b9d8963099da5`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
