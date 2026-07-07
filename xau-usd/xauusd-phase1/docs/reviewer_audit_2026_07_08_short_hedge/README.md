# Short Hedge Review Packet - 2026-07-08

Purpose: make the exact-MT5 short-hedge pass reviewable from GitHub even though the normal `outputs/reports` tree is ignored.

Read first:

- `A1_XAU_SHORT_HEDGE_EXACT_202207_202606.md`
- `A1_XAU_SHORT_HEDGE_EXACT_202207_202606_RESULTS.csv`
- `A1_XAU_SHORT_HEDGE_EXACT_202207_202606_STANDALONE.csv`

Best candidate:

- `short_hedge_v2_breakdown_retest`
- Standalone: 329 trades, WR 32.83%, W/L 2.8332, PF 1.3846, net +441.42 USD, stress -$0.30/trade PF 1.2823, stress W/L 2.6239, stress net +342.72.
- Combined with `supportive_guard`: 3953 signals, WR 49.00%, W/L 2.1637, PF 2.0934, net +21064.67 USD, stress W/L 2.0390, positive weeks 58.17%.

Raw exact-MT5 evidence copied here:

- `*_short_hedge_v1_break_run_control_*`
- `*_short_hedge_v2_breakdown_retest_*`
- `*_short_hedge_v3_prior_high_sweep_reclaim_*`

Status: research-only review candidate. No demo spec or runtime promotion is approved.
