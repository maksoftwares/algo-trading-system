# FX Multi-Pair Portfolio V1

Status: **`NO_DEPLOYABLE_FX_EDGE_FOUND_STOP`** — research only. This package
carries **no** demo authority, no live authority, no chart attachment, no preset
and no broker-action file. It does not touch any MT5 runtime, terminal, profile
or the XAUUSD lane.

**Read [`FINDINGS.md`](FINDINGS.md) first.** Six hypothesis classes were tested
against the goal of a profitable, higher-frequency Forex system; all six were
rejected, and the rejections are recorded in [`REJECTIONS.md`](REJECTIONS.md)
with the evidence that closed each one. The headline: the strongest in-sample
effect (positive in 6 of 6 design years) reversed sign in both out-of-sample
windows and loses even at zero spread markup.

What *is* delivered is a tested substrate for evaluating FX hypotheses quickly,
plus a quantified explanation of why the existing Forex lane never passed.

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
python -m pytest tests -q
```

`build_bars.py` and `acquire_fred_fx.py` write to the cache; the rest only read
it and write into `outputs/`.

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

Assumed, **not measured** — no FX broker spread exists anywhere in this repo.
Effective spreads of 12 / 18 / 14 points for EURUSD / GBPUSD / USDJPY, plus 2
points entry and 2 points stop slippage. See `FINDINGS.md` §"Cost-model caveat".
Measuring the demo account's true spread and swap is the recommended first
follow-up, because it is the only thing that could revive the carry rejection.

## What not to retry

`REJECTIONS.md` closes: bar-geometry breakout/channel/fade families on majors,
the inherited EURUSD RSI/Bollinger fade at retail cost, intraday
momentum/reversion conditioning, the Tokyo-hour USD drift, and price-only
cross-sectional momentum and value. Another EURUSD parameter search is not a
next step.
