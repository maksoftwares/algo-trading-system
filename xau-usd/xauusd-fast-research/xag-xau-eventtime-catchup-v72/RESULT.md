# V72 Terminal Development Result

V72 established a fully checksummed raw Dukascopy XAGUSD/XAUUSD event-time
pipeline and selected candidate density without opening outcomes. The locked
policy used a one-second XAG horizon, 4.0 bps minimum XAG move, 2.5 bps minimum
directional innovation, 0.50 maximum signed XAU response ratio, and five XAG
quotes. Calibration produced 17 candidates over 21 eligible weekdays
(`0.809524/day`) with five longs and twelve shorts.

Contract SHA-256: `1f95f6442f037aa71b7c33886aa56722cefbab5d485c1285dd10127a1003cc90`.

Development resolved 693 trades over 745 eligible full weekdays
(`0.930201/day`), with 315 longs and 378 shorts. Base/stress net was USD
`-491.63/-542.61`; base/stress PF was `0.2973/0.2646`; first/second-half stress
PF was `0.2293/0.2892`. Positive-day share was `22.01%`, no month was positive,
top-five-winner-removed stress net was USD `-561.59`, stressed closed DD was USD
`543.21`, and bootstrap p-value was `1.0`.

Decision: `V72_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. The July 2024-June 2026 exam archive was not acquired because the
development failure made that network work unnecessary. No V72 threshold,
horizon, direction, response rule, quota, stop, target, hold, cost, or gate may
be changed on these outcomes.

