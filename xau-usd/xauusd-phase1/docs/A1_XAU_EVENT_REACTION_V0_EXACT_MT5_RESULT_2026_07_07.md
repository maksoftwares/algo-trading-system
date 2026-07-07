# A1 XAU Event-Reaction V0 Exact MT5 Result - 2026-07-07

Status: `DIAGNOSTIC_CLUE_LOW_ACTIVITY_NO_DEMO_SPEC`

## Boundary

- Exact MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime chart, preset, order, position, or broker-action state was changed.
- Six cells were predeclared before results in `xau-usd/xauusd-phase1/docs/A1_XAU_EVENT_REACTION_NEW_CLASS_PREREG_2026_07_07.md`.
- Event calendar provenance is official BLS/Fed and frozen in `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_REACTION_CALENDAR_202207_202606_PROVENANCE.md`.

## Implementation

- Added default-off MT5 signal mode `SIGNAL_EVENT_REACTION_M5 = 14`.
- Added calendar loading with tester-local file access and `FILE_COMMON` fallback because MT5 clears tester-agent `MQL5/Files` before launch.
- Added six fixed runner variants:
  - `event_impulse_nfp_rr2`
  - `event_fade_nfp_rr2`
  - `event_impulse_cpi_rr2`
  - `event_fade_cpi_rr2`
  - `event_impulse_fomc_rr2`
  - `event_fade_fomc_rr2`
- Compile evidence: `C:\MT5A1M5MomentumBacktest\Logs\compile_A1XauM5MomentumContinuationExecutor_variants_20260701.log`, `0 errors, 0 warnings`.

## Exact MT5 Result

Report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_EVENT_REACTION_V0_202207_202606.md`

Period: `2022-07-01 -> 2026-06-30`
Tester currency: `USD`
Total calendar weeks: `210`

| Variant | Trades | WR | Net USD | PF | Active weeks | Positive active weeks | Positive all weeks | Worst week |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `event_impulse_nfp_rr2` | 17 | 47.06% | 46.71 | 1.46 | 8.10% | 47.06% | 3.81% | -17.80 |
| `event_fade_nfp_rr2` | 23 | 30.43% | -15.71 | 0.80 | 10.95% | 30.43% | 3.33% | -8.73 |
| `event_impulse_cpi_rr2` | 18 | 38.89% | 22.75 | 1.19 | 8.57% | 38.89% | 3.33% | -16.58 |
| `event_fade_cpi_rr2` | 28 | 46.43% | 40.73 | 1.45 | 13.33% | 46.43% | 6.19% | -15.04 |
| `event_impulse_fomc_rr2` | 16 | 56.25% | 68.52 | 1.81 | 7.62% | 56.25% | 4.29% | -15.40 |
| `event_fade_fomc_rr2` | 9 | 33.33% | 5.64 | 1.16 | 4.29% | 33.33% | 1.43% | -12.77 |

## Verdict

`event_impulse_fomc_rr2` is the best quality clue: WR `56.25%`, PF `1.81`, net `+68.52 USD`, and both long/short directions positive in the runner summary.

It is not demo-ready and does not solve the owner goal. Activity is too sparse: best active-week coverage is only `13.33%`, and the best FOMC impulse clue covers only `7.62%` of calendar weeks. This branch can be used only as a small scheduled add-on clue for future composition/red-week rescue analysis, not as a standalone strategy.

Next useful action is not event-threshold tuning. The clean next test is a preregistered composition audit: whether the profitable event cells touch or improve current baseline red weeks without worsening already-green weeks.
