# What works, what doesn't — settled on live demo results

Date: 2026-08-01
Source: account 1025742 @ Capital.ComMena-Demo, **2,190 real closed trades**,
2026-06-01 → 2026-07-21. Not backtest.

## The table that decides everything

| Symbol | Trades | Win% | PF | Net AED | Net USD |
|---|---:|---:|---:|---:|---:|
| **XAUUSD** | 1,412 | 38.7% | **1.040** | **+989.95** | **+269.56** |
| BTCUSD | 64 | 34.4% | 0.686 | −83.76 | −22.81 |
| USDJPY | 29 | 24.1% | 0.686 | −20.29 | −5.52 |
| EURUSD | 382 | 36.6% | 0.703 | −899.21 | −244.85 |
| GBPUSD | 303 | 29.7% | **0.573** | **−1,578.44** | −429.80 |
| **TOTAL** | 2,190 | 36.8% | 0.950 | **−1,591.75** | **−433.42** |

**Gold is the only symbol with PF above 1.** Everything else is between 0.573 and
0.703 — not marginal, decisively losing.

## The single action worth taking

| | Trades | PF | Net AED | Net USD |
|---|---:|---:|---:|---:|
| Everything, as currently run | 2,190 | 0.950 | −1,591.75 | −433.42 |
| **XAUUSD only** | 1,412 | **1.040** | **+989.95** | **+269.56** |
| Everything except XAUUSD | 778 | 0.634 | −2,581.70 | −702.98 |

**Turning off EURUSD, GBPUSD, USDJPY and BTCUSD converts a 433 USD loss into a
270 USD profit** — a 703 USD swing, with no new research and no new code.

## This confirms every research finding independently

The live results match what the research said, symbol by symbol:

| Research finding | Live confirmation |
|---|---|
| FX majors: 11 hypothesis classes rejected, spread wider than the predictable component | EURUSD PF 0.703, GBPUSD 0.573, USDJPY 0.686 |
| BTCUSD rejected on cost before testing (16.0x range/cost, $500 spread) | BTCUSD PF 0.686 |
| Gold is the only measured edge in the repository | XAUUSD PF 1.040, the only one above 1 |
| US500: five independent searches, no edge | never deployed — correctly |

Research and live money agree. That is the strongest form of confirmation
available, and it was reached from two completely independent directions.

## What to switch off

**Instruments:** EURUSD, GBPUSD, USDJPY, BTCUSD. All four are live-confirmed
losers on 778 trades.

**Research lanes:** FX multi-pair (11 rejections), US500 (12 rejections plus a
14,400-attempt search whose survivors were indistinguishable from noise). Both
are closed with evidence; neither should absorb further effort.

## What to keep

**XAUUSD** — the only instrument earning its spread.

**Balanced long/short risk construction** — cut backtest drawdown roughly
fivefold at equal profit factor. Worth applying to gold, where there is an edge
to protect.

**The instrument screen** (`screen_instruments.py`) — range/cost ratio, measured
from live broker ticks. It rejected BTCUSD in minutes and the live result
vindicated it. Run it before any new instrument.

**The execution engine and data foundations** — 28 contract tests, honest
bid/ask and full 24h path modelling. This is what caught the 96.5pp overnight
bias and the inverted hold-time bug.

**The null benchmark** — one extra command that prevented shipping a
14,400-attempt false positive.

## Caveats on the gold number, stated plainly

XAUUSD's PF 1.040 is **thin**, and the sample is ~7 weeks, not 12 months:

- 2026-06: 1,321 trades, 39.6% wins, **+1,384.17 AED**
- 2026-07: 91 trades, 26.4% wins, **−394.22 AED**

Maximum drawdown was 2,354 AED against a total profit of 990 AED — the drawdown
exceeds the profit. July's win rate fell to 26.4% on a much smaller trade count.
Gold is the best of what exists here; it is not yet proven robust.
