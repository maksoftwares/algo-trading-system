# A3 Net-Cost Falsification - 2026-06-19

Status: `LOCKED_NEGATIVE_FINDING`

Decision: `XAU_BREAK_RETEST_ENTRY_FALSIFIED_NET_OF_COST_ON_THIS_DATA`

Boundary: analysis-only. No MT5 terminal, profile, chart, preset, order, position, or broker runtime state was touched.

Manifest:

- File: `xau-usd/xauusd-phase1/outputs/reports/A3_NET_COST_FALSIFICATION_MANIFEST_2026_06_19.json`
- SHA256: `1D56960EE04C5DAC02D56B1A194298387C842FCB54D950A2CE05AE09C6C877CE`

## Methodology

- Symbol: `XAUUSD`.
- Source data: Phase 0 Dukascopy M5/H1/D1 bars, 2025-01-02 through 2025-07-01.
- Execution model: one virtual position at a time per candidate; raw deduped book is the primary gate.
- Cost model: measured spread floor from `cost_model_measured.csv`.
- Charged spread: worse of realized bar spread or measured median spread for the UTC hour.
- Stress model: worse of realized bar spread or measured P95 spread for the UTC hour.
- Slippage: `10` points entry slippage and `50` points stop-exit slippage.
- Rejection policy: trades with estimated `cost_R > 0.12` are shown in the cost-guard survivor diagnostics, but that survivor slice is not approval evidence unless pre-registered as an entry rule.
- Acceptance bar: raw deduped net PF `>= 1.25`, raw deduped expectancy `>= +0.10R`, stress PF `>= 1.25`, stress expectancy `>= +0.10R`, max drawdown `<= 8R`, t-stat `>= 2.0`, worst-day robustness, both up-day and down-day survival.

## Result Table

| Candidate | Trades | Cost rejects | Raw PF | Raw exp R | Stress PF | Stress exp R | P95 cost R | Max DD R | t-stat | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `B0_RAW_ALL_SESSION` | 885 | 800 | 0.7357 | -0.2069 | 0.6375 | -0.3028 | 0.8280 | 193.3555 | -4.5125 | FAIL |
| `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2` | 490 | 433 | 1.1242 | 0.0778 | 0.9701 | -0.0199 | 0.7595 | 22.5077 | 1.2796 | FAIL |
| `A3_WIDE_STOP_800PT_SOFT_RETEST_V0` | 303 | 150 | 1.1830 | 0.1070 | 1.1273 | 0.0765 | 0.1375 | 10.1525 | 1.4524 | FAIL |

## Finding

The XAU breakout-retest entry family is falsified net-of-cost on this data.

The scalp baseline is decisively negative. The soft-retest V2 and 800-point wide-stop variants are statistically indistinguishable from zero once realistic costs and stress are applied. The 800-point stop floor is also post-hoc exploratory only, not a pre-registered locked hypothesis.

This is not a stop-width tuning problem. The base entry has no demonstrable raw deduped net edge under the hardened cost model.

## Governance Consequence

- A3 remains paused.
- Do not forward-validate `B0_RAW_ALL_SESSION`, `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`, or `A3_WIDE_STOP_800PT_SOFT_RETEST_V0`.
- Do not resurrect these candidates using the cost-filtered survivor slice.
- Do not re-tune the breakout-retest entry family without a new, separately pre-registered hypothesis and reviewer/owner approval.
- Future XAU entry research must use a genuinely different entry mechanism.

## Source Evidence

- Primary report: `xau-usd/xauusd-phase1/outputs/reports/A3_NET_COST_DEDUPED_REBASELINE_2026_06_19.md`
- Machine-readable report: `xau-usd/xauusd-phase1/outputs/reports/A3_NET_COST_DEDUPED_REBASELINE_2026_06_19.json`
- Per-trade evidence: `xau-usd/xauusd-phase1/outputs/reports/A3_NET_COST_DEDUPED_REBASELINE_TRADES_2026_06_19.csv`
