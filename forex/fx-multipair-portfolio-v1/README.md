# FX Multi-Pair Portfolio V1

Status: **`NO_DEPLOYABLE_FX_EDGE_FOUND_STOP`** — research only. This package
carries **no** demo authority, no live authority, no chart attachment, no preset
and no broker-action file. It does not touch any MT5 runtime, terminal, profile
or the XAUUSD lane.

**Read [`FINDINGS.md`](FINDINGS.md) first.** Ten hypothesis classes were tested
against the goal of a profitable, higher-frequency Forex system; all ten were
rejected, and each is recorded in [`REJECTIONS.md`](REJECTIONS.md) with the
evidence that closed it. Majors and crosses are both closed.

Read **R8** and **R9** for the two near-misses that would have shipped: an edge at
4.8x measured cost that vanished entirely on replication, and GBPJPY Donchian at
design PF 1.483 that fell to 0.908 out-of-sample *after* passing a parameter
plateau test.

The result reduces to one measured inequality: **the bid-ask spread is wider than
the entire predictable component of FX returns.** EURUSD trades at a fixed 0.70
pips on this account. The most significant predictor found anywhere here — short
term mean reversion in signed tick flow, t = −9.3 / −7.8 / −6.3 across three
pairs using real order-book depth — is worth **1.6 points**. And carry, the only
income needing no signal, nets ≈+0.5%/yr against a 68.6% historical drawdown.

**The closing finding answers the question behind the goal.** Ranking every
tradeable symbol on the account by `median daily range / round-trip cost` — the
ratio all ten rejections reduce to — puts **XAUUSD first at 211.7x**, with nothing
above it and the best FX major (AUDUSD) at 33.7x, **6.3x worse**. Gold does not
work because of a better mechanism; it works because it is the most tradeable
instrument available here. That also gives a screening rule: measure range/cost
*before* searching for a strategy, and treat anything below ~50x as unlikely to
support one at retail cost.

What *is* delivered: a tested substrate for evaluating FX hypotheses quickly,
measured broker costs replacing a decade of assumption, an instrument-ranking
rule, and a quantified explanation of why the existing Forex lane never passed.

## Layout

```
src/fxdata.py       tick decode + M5 bid/ask bars + higher-TF derivation
src/engine.py       bid/ask execution engine (costs, slippage, JPY conversion)
src/indicators.py   RSI/ATR/Bollinger + decision->execution bar mapping
src/strategies.py   the three preregistered families
src/report.py       shared metrics, cost model, data partitions
tests/              engine and indicator contract tests
outputs/            every result JSON/CSV referenced by the writeups
```

## Environment

```bash
uv venv --python 3.14 forex/fx-multipair-portfolio-v1/.venv
uv pip install --python forex/fx-multipair-portfolio-v1/.venv/Scripts/python.exe numpy pandas pyarrow pytest
```

Bar cache and long-history panel live outside the repo at
`D:\AlgoTradingData\research\fx-multipair-portfolio-v1`.

## Reproducing

Run from `forex/fx-multipair-portfolio-v1` with `.venv\Scripts\python.exe`.

```bash
python build_bars.py                 # 264k tick files -> M5 bid/ask cache (~97s, 14 workers)
python verify_bars.py                # integrity + coverage -> BAR_INTEGRITY.json
python calibrate_reference.py        # inherited EURUSD rule + spread stress -> R2
python run_design_search.py          # 3 families x 48 params x 3 pairs -> R1
python run_edge_census.py            # 49-bucket intraday census -> R3
python run_tokyo_holdout_test.py     # the holdout test that killed R4
python acquire_fred_fx.py            # 27.5y daily panel, 7 majors
python run_premia_census.py          # cross-sectional premia + carry -> R5, R6
python build_micro_features.py       # order-book depth features (~453s)
python run_micro_census.py           # microstructure vs measured cost -> R7
python run_vol_conditioned_census.py # 300-cell vol-conditioned search -> R8
python run_vol_replication_test.py   # replication that rejected R8
python build_crosses.py              # synthetic EURGBP/EURJPY/GBPJPY bid/ask bars
python run_cross_search.py           # R1 grid + momentum on crosses -> R9
python validate_gbpjpy_donchian.py   # full discipline on the one survivor
python run_spread_dislocation_test.py # fixed-spread structural advantage -> R10
```

Broker measurement needs the MT5 module, which requires Python 3.12 (the
`copy_ticks_*` calls fail to marshal on 3.14). Use the `.venv312` interpreter:

```bash
python measure_broker_costs.py         # symbol specs + real swap rates
python measure_broker_spread_ticks.py  # real spread from broker tick history
python evaluate_carry_sleeve.py        # the one positive-expectancy position set
python rank_instrument_tradeability.py # range/cost ranking across instruments
python -m pytest tests -q
```

`build_bars.py`, `build_micro_features.py` and `acquire_fred_fx.py` write to the
cache; everything else only reads it and writes into `outputs/`.

The broker scripts are **read-only**: `initialize`, `account_info`,
`symbol_info`, `symbol_info_tick`, `symbol_select`, `copy_ticks_range` only —
the same surface the existing `capital-multisymbol-prospective-v1` collector
uses. They send no order, change no setting, and refuse to report on a non-demo
account. `pull_broker_bars.py` is retained to document that this terminal
rejects `copy_rates_*` outright ("Call failed"), so broker bar history is not
available from it.

## Engine contract

The properties that make the numbers trustworthy, each pinned by a test:

- a signal names the M5 bar whose **open** is the fill, and no earlier bar can
  affect it (`test_fill_uses_the_named_bar_open_not_earlier_bars`);
- longs pay the ask and are stopped/targeted on the **bid** path, shorts mirror;
- stop exits slip adversely; targets get no mirror-image improvement;
- a bar spanning both levels resolves to the **stop**, and is counted;
- position size and every level are computed at the entry bar in entry order —
  never in exit order, which is the look-ahead that cost an earlier lane a
  claimed PF 2.03;
- JPY-quoted pairs convert the quote currency at the prevailing rate.

## Cost model

**Measured**, from real broker tick history (`outputs/BROKER_SPREAD_TICKS.json`).
Spreads are *fixed* — p25 = median = p95 at every hour except the 21:00 UTC
rollover:

| AUDUSD | EURUSD | USDJPY | GBPUSD | USDCHF | USDCAD | USDMXN | USDZAR |
|---|---|---|---|---|---|---|---|
| 0.60 | 0.70 | 1.20 | 1.30 | 1.40 | 2.00 | 21.2 | 50.0 |

`src/report.py` exposes both models: `COSTS` is the assumed one used by R1–R6 and
kept verbatim so those runs stay reproducible, and `MEASURED_SPREAD_POINTS` /
`measured_costs()` are the real figures used from R7 onward. Real EURUSD cost is
~30% *below* what R1–R6 assumed, so those rejections ran against a pessimistic
model and stand regardless.

Swap is skimmed **asymmetrically** — near-fair on one side of each pair, punitive
on the other (GBPJPY long ~96% pass-through, EURUSD long ~0%).

## What not to retry

`REJECTIONS.md` closes ten classes: bar-geometry breakout/channel/fade families
on majors, the inherited EURUSD RSI/Bollinger fade, intraday momentum/reversion
conditioning, the Tokyo-hour USD drift, price-only cross-sectional momentum and
value, carry (both on interbank rates and on measured broker swap), tick
microstructure/order flow, volatility-conditioned microstructure, and the
synthetic crosses including their one surviving candidate, and the fixed-spread
structural advantage.

Before writing up any future candidate — here or in the XAU lane — apply the R8
and R9 checks, because both near-misses passed everything short of a holdout:

1. **Count the cells searched** and compare the hit rate against chance. R8's 8
   hits from 300 cells were *fewer* than the ~15 expected at 5%.
2. **Distrust scattered parameters and flipped signs.** R8's winning volatility
   quintiles were Q2/Q3/Q4/Q5 with no monotone pattern.
3. **Do not trust a parameter plateau.** R9's GBPJPY Donchian had a genuinely broad
   plateau in-sample and still fell from PF 1.483 to 0.908 out-of-sample.
4. **Re-run the identical measurement on untouched data.** This is the only check
   that caught either one.
