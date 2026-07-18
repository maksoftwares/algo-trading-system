# XAUUSD Corrected Event V4 Historical Replication

Decision: `NO_CORRECTED_EVENT_V4_HISTORICAL_SURVIVOR`
Policies evaluated: **8**
Events in stage: **241**
Signals in stage: **303**
Executed outcomes: **279**
Stops / targets / timeouts: **160 / 81 / 38**
Survivors: **0**

| Policy | Trades / events | PF | Avg R | DD R | Top 3 removed R | Year + | Holm q | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `EVENT_FOMC_IMPULSE_RR2` | 32 / 43 | 1.704 | 0.323 | 8.139 | 4.633 | 66.7% | 0.7314 | FAIL |
| `EVENT_NFP_FADE_RR2` | 30 / 66 | 1.209 | 0.133 | 9.438 | -1.664 | 66.7% | 1.0000 | FAIL |
| `EVENT_CPI_FADE_RR2` | 37 / 66 | 0.927 | -0.055 | 8.329 | -7.638 | 50.0% | 1.0000 | FAIL |
| `EVENT_PPI_FADE_RR2` | 39 / 66 | 0.861 | -0.106 | 10.014 | -9.717 | 33.3% | 1.0000 | FAIL |
| `EVENT_PPI_IMPULSE_RR2` | 51 / 66 | 0.819 | -0.130 | 12.066 | -12.265 | 16.7% | 1.0000 | FAIL |
| `EVENT_FOMC_FADE_RR2` | 20 / 43 | 0.682 | -0.258 | 5.686 | -10.796 | 33.3% | 1.0000 | FAIL |
| `EVENT_CPI_IMPULSE_RR2` | 40 / 66 | 0.512 | -0.383 | 16.109 | -21.037 | 0.0% | 1.0000 | FAIL |
| `EVENT_NFP_IMPULSE_RR2` | 30 / 66 | 0.196 | -0.547 | 16.426 | -19.269 | 0.0% | 1.0000 | FAIL |

Stop and target ordering was resolved from verified raw Dukascopy ticks.
Only this stage was labeled; later-stage outcomes remain unmaterialized.
Related confirmation is not represented as a pristine blind exam.
No result grants model, EA, demo, live, broker, paid-data, or Databento authority.
