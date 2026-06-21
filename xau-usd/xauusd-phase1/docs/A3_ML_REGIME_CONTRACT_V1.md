# A3 ML Regime Contract V1

Status: PRELOCK_CONTRACT

This contract owns deterministic RISING, FALLING, MIXED, and UNKNOWN definitions.

## Input Bars

Use completed D1 bars only.

No current incomplete D1 bar may be used.

## Score

```text
d1_trend_score =
  (EMA20_D1[1] - EMA20_D1[6]) / ATR14_D1[1]
```

If required D1 bars, EMA values, or ATR14_D1[1] are unavailable, zero, negative, stale, or not causally available, regime is UNKNOWN.

## Regime Labels

RISING:

```text
close_D1[1] > EMA20_D1[1]
and d1_trend_score >= +0.25
```

FALLING:

```text
close_D1[1] < EMA20_D1[1]
and d1_trend_score <= -0.25
```

MIXED:

```text
all other valid states
```

UNKNOWN:

```text
unavailable, invalid, stale, or non-causal data
```

UNKNOWN does not satisfy regime coverage.

For MATURE_MODEL, "all regimes" means RISING, FALLING, and MIXED are represented. UNKNOWN is reported but does not count toward coverage.
