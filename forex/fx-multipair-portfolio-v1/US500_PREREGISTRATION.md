# US500 System — Preregistration

Status: `PREREGISTERED_BEFORE_LONG_HISTORY`
Written 2026-07-31, before any multi-year US500 result was inspected.

## 0. Why US500 and not BTC

The user offered BTC or SP500. The measured range/cost screen decided it
(`outputs/INSTRUMENT_SCREEN.json`, live Capital.com demo, 21 days):

| Symbol | Spread | Median daily range | Ratio |
|---|---:|---:|---:|
| US30 | 20 pts | 4,951 | 141.5x |
| XAUUSD | 30 pts | 6,398 | 121.9x |
| **US500** | **6 pts** | 777 | **74.0x** |
| EURUSD | 7 pts | 454 | 37.1x |
| ETHUSD | 175 pts | 6,062 | 19.8x |
| **BTCUSD** | **5,000 pts ($500)** | 140,195 | **16.0x** |

BTCUSD is the worst instrument on the account — worse than EURUSD, where eleven
hypothesis classes already failed on cost alone. Its 2.18% daily range cannot
outrun a $500 spread. Nine years of BTC tick history does not fix a cost
structure. **US500 is selected on measured evidence, not preference.**

## 1. Primary hypothesis (H1) — the overnight effect

> In equity indices, returns accrue overnight (previous close → open) rather
> than intraday (open → close). A long-only overnight position therefore earns
> most of the index's return with materially less exposure time, and the
> improvement survives realistic cost.

This is a published, long-documented anomaly, not a pattern mined from this
data. It is stated here **before** the long history is inspected so the test is
confirmatory rather than exploratory.

Orientation on 285 days of broker data (2025-06 → 2026-07) is consistent:
overnight +3.631 pts/day (58.9% win, t = +1.70) vs intraday +1.503 (53.7%,
t = +0.59); overnight captured 71% of the move. That window is a bull market
and proves nothing on its own — hence this preregistration.

**H1 is rejected unless**, on 2016–2026:

- overnight mean return > intraday mean return in the pooled sample;
- overnight Sharpe exceeds buy-and-hold Sharpe net of cost;
- overnight is positive in at least 7 of 10 calendar years;
- it survives the 2018, 2020 and 2022 drawdown years without a loss exceeding
  the buy-and-hold loss in the same year.

## 2. Secondary hypotheses

**H2 — opening range breakout.** Break of the first 30 minutes of the US cash
session, in the direction of the break, exit at session close.

**H3 — turn-of-month.** Long from the last trading day of the month through the
third trading day of the next.

Both are documented equity-index effects. Neither may be tuned beyond the single
parameter named.

## 3. Cost model (measured, not assumed)

From `outputs/BROKER_SPREAD_TICKS.json` and the broker M5 build: US500 spread is
**5 points median, 6 at p95** (`point = 0.1`), i.e. **0.5 index points**, with
zero negative-spread bars over 82,632 bars. Round trip modelled as spread + 2
points entry slippage + 2 points stop slippage = **0.9 index points**.

Cost stress at **2x** is mandatory before promotion.

`contract_size = 1`, so one index point is $1.00 per 1.0 lot and $0.01 per 0.01
lot. Minimum lot 0.01.

## 4. Data and partitions

Two independent sources, deliberately:

- **Broker** — Capital.com demo ticks via read-only MT5, 2025-06 → 2026-07,
  82,632 M5 bars. The venue that would actually be traded.
- **Dukascopy** — `USA500.IDX-USD` from 2016-01, downloading now.

| Partition | Window | Use |
|---|---|---|
| Design | 2016-01 .. 2022-12 | choose parameters |
| Validation | 2023-01 .. 2025-05 | accept or reject |
| Broker exam | 2025-06 .. 2026-07 | venue check, run once |

A candidate must hold on **both** sources. The Forex lane's costliest lesson was
that a candidate tuned on one venue need not transfer to another.

## 5. Target metrics (the "same as forex" bar)

Matching the standard the EURUSD V2 candidate met:

- profit factor >= 1.40 on the pooled sample;
- >= 0.5 trades per trading day;
- >= 55% of active months positive;
- PF >= 1.20 after removing the best 5% of trading days;
- PF >= 1.15 under 2x cost stress;
- max closed-trade drawdown <= 15% of the modelled account;
- positive in validation *and* broker exam, not just design.

## 6. Discipline

No per-year or per-weekday tuning. The broker sample already shows a tempting
weekday split in overnight returns (Mon +15.4, Tue −5.5, Wed +11.5 pts on
n ≈ 57 each); that is explicitly **forbidden** as a selection axis — it is the
same shape as the Tokyo-hour effect that reversed sign out of sample in the FX
lane after being positive in 6 of 6 design years.

Every rejection is recorded in `US500_REJECTIONS.md`. Expect realised results
below backtest: this repo's measured selection-leak ladder is PF 1.99 → 1.45 →
0.82.
