# A1 XAU M5 Regime Specialist Secondary Campaign Preregistration

Date: `2026-07-13`

Status: `FROZEN_BEFORE_SECONDARY_MT5_EXECUTION`

## Purpose

The primary five-year M5 campaign tested four signal families in each tradable
Router V1 regime. Only R2/DOWNTREND produced a screen survivor. This secondary
campaign is a bounded search for R1/UPTREND, R3/COMPRESSION, and R4/CHOP only.

It does not alter a threshold, stop, target, direction, session, or result mask
of any primary candidate. Each row is a different pre-existing M5 event family.
R2 is excluded because its survivors move directly to untouched ten-year
confirmation.

## Frozen common contract

- Symbol/timeframe: `XAUUSD / M5`
- Window: `2021-07-01` through `2026-07-01`
- MT5 model: every tick, native report quality required `>=98%`
- Deposit/currency: `$1,000 USD`
- Size: fixed `0.01 lot`
- One same-magic position maximum
- Maximum eight trades per day; ten-minute cooldown
- Fixed target: `1.50R`
- Maximum spread: `75 points`
- Maximum estimated cost: `0.15R`
- Router ownership is fail-closed and SHOCK is never tradable

## Frozen candidates

### R1 / UPTREND

1. H1 trend pullback with M5 confirmation (`signal mode 20`, confirmation `M5`)
2. M5 opening-range continuation long (`mode 4`)
3. M5 prior-day breakout continuation long (`mode 13`, continuation)
4. M5 downside sweep/reclaim long (`mode 3`)

### R3 / COMPRESSION

1. M5 break-and-run release (`mode 0`)
2. M5 EMA reaction (`mode 1`)
3. M5 opening-range release (`mode 4`)
4. M5 EMA trend release (`mode 5`)

### R4 / CHOP

1. M5 bearish resistance sweep/reclaim (`mode 16`)
2. M5 bearish lower-high rejection (`mode 17`)
3. M5 bearish failed-support retest (`mode 15`)
4. M5 local compression release (`mode 2`)

## Frozen five-year screen gates

- Trades `>=100`
- Profit factor `>=1.20`
- Win rate `>=35%`
- Net profit `>0`
- MT5 relative equity drawdown `<=20%`
- History quality `>=98%`

A survivor is authorized only for untouched ten-year confirmation. It is not
demo/live or deployment authorization. If a regime again has no survivor, the
result is recorded honestly; no threshold repair is permitted in this phase.
