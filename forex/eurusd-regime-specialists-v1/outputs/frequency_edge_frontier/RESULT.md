# EURUSD frequency/edge frontier diagnostic

Status: **RETROSPECTIVE DIAGNOSTIC -- NO DEMO ADMISSION**

The highest-frequency rule satisfying the diagnostic full-period and
both-half stressed-edge checks used a global trailing window of
30 completed shadow trades and PF >= 1.05. It was selected
after inspecting history and is therefore forward-only.

| Metric | Result |
|---|---:|
| Combined trades | 447 |
| Combined trades/weekday | 0.8563 |
| Combined weekday coverage | 43.30% |
| Combined PF | 1.4867 |
| Combined PF after +0.5 pip | 1.3745 |
| Combined net at fixed 0.01 lot | $111.40 |
| Second-12-month PF | 1.2781 |
| Second-12 best-5%-removed PF | 0.9378 |
| Projected frequency including daily learner | 0.8695 |

The average-frequency floor is reached, but the desired 1.0/day,
65% weekday coverage, recent concentration test, prospective parity,
and soak are not. Demo-order authorization remains false.
