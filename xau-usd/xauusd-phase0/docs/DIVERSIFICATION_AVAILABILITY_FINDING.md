# Diversification Availability Finding

Last updated: 2026-05-25

## Finding

As of 2026-05-25, the project has tested a broad set of non-level, intermarket, macro-regime, AI-style macro-composite, nominal-rate, yield-curve, corporate-credit, futures-positioning, options-implied-volatility, equity-risk implied-volatility, financial-conditions, breakeven-inflation, volatility-regime, and higher-timeframe XAUUSD candidates under the locked Phase 0 research lane. Twenty-one H4/D1/W1 candidates plus additional H1 intermarket and volatility-regime candidates were registered, SHA256-locked, smoke-tested, and run through the real 9-cell matrix without tuning. Zero produced the required PF >= 1.30 survival rate in at least 7 of 9 cells.

The current evidence supports this operating conclusion:

```text
The project has one approved edge family inside the current XAUUSD research scope:
level-and-pullback / breakout-retest.
```

Same-family variants may be useful for observation, cost study, and future comparison, but they do not provide portfolio diversification.

## Evidence Set

| # | Candidate | Decision cadence | PF >= 1.30 cells | First-pass status |
| ---: | --- | --- | ---: | --- |
| 1 | `d1_momentum_h4_pullback_v0` | H4/D1 | 3/9 | REJECTED_FIRST_PASS |
| 2 | `d1_volatility_expansion_reversal_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 3 | `d1_compression_h4_expansion_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 4 | `d1_multi_day_exhaustion_reversion_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 5 | `h4_d1_momentum_expansion_continuation_v0` | H4/D1 | 3/9 | REJECTED_FIRST_PASS |
| 6 | `h4_inside_bar_d1_momentum_breakout_v0` | H4/D1 | 2/9 | REJECTED_FIRST_PASS |
| 7 | `w1_d1_momentum_continuation_v0` | W1/D1 | 3/9 | REJECTED_FIRST_PASS |
| 8 | `weekly_open_reversion_v0` | W1/M15 | 0/9 | REJECTED_FIRST_PASS |
| 9 | `d1_inside_day_breakout_v0` | H4/D1 | 3/9 | REJECTED_FIRST_PASS |
| 10 | `d1_outside_day_followthrough_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 11 | `d1_w1_momentum_h4_pullback_v0` | H4/D1 with W1 state | 3/9 | REJECTED_FIRST_PASS |
| 12 | `h4_walk_forward_knn_momentum_state_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 13 | `h4_real_yield_proxy_momentum_v0` | H4/D1 with FRED real-yield/dollar state | 3/9 | REJECTED_FIRST_PASS |
| 14 | `cot_gold_positioning_reversal_v0` | H4 with official CFTC gold COT positioning | 0/9 | REJECTED_FIRST_PASS |
| 15 | `h4_gvz_volatility_panic_reversal_v0` | H4 with FRED GVZ gold-options implied volatility | 0/9 | REJECTED_FIRST_PASS |
| 16 | `h4_vix_risk_off_reversal_v0` | H4 with FRED VIX equity-risk implied volatility | 3/9 | REJECTED_FIRST_PASS |
| 17 | `h4_financial_conditions_stress_reversal_v0` | H4 with FRED NFCI/ANFCI financial conditions | 0/9 | REJECTED_FIRST_PASS |
| 18 | `h4_breakeven_inflation_momentum_v0` | H4 with FRED T5YIE/T10YIE breakeven inflation momentum | 0/9 | REJECTED_FIRST_PASS |
| 19 | `h4_treasury_curve_stress_momentum_v0` | H4 with FRED DGS2/DGS10/T10Y2Y Treasury curve stress | 3/9 | REJECTED_FIRST_PASS |
| 20 | `h4_credit_spread_stress_momentum_v0` | H4 with FRED BAA10Y/AAA10Y corporate credit spread stress | 0/9 | REJECTED_FIRST_PASS |
| 21 | `h4_macro_composite_risk_state_v0` | H4 with fixed AI-style FRED macro/risk vote | 6/9 | REJECTED_FIRST_PASS |

Additional H1 intermarket and volatility-regime diversification attempts:

| # | Candidate | Input Family | PF >= 1.30 cells | First-pass status |
| ---: | --- | --- | ---: | --- |
| 1 | `gold_fx_proxy_divergence_v0` | EURUSD/USDJPY proxy | 0/9 | REJECTED_FIRST_PASS |
| 2 | `xau_xag_relative_value_v0` | XAGUSD relative value | 0/9 | REJECTED_FIRST_PASS |
| 3 | `xau_xag_fx_composite_reversion_v0` | XAGUSD plus EURUSD/USDJPY proxy | 0/9 | REJECTED_FIRST_PASS |
| 4 | `xag_lead_xau_followthrough_v0` | XAGUSD lead-lag continuation | 0/9 | REJECTED_FIRST_PASS |
| 5 | `h1_volatility_squeeze_breakout_v0` | H1 volatility-compression expansion | 3/9 | REJECTED_FIRST_PASS |

Supporting artifacts:

- `docs/CANDIDATE_RESEARCH_BACKLOG.md`
- `outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md`
- `outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md`
- Per-candidate `*_FIRST_PASS.md` files in `docs/`

## Gate-Bias Check

The frequency-normalized concentration audit did not rescue or reclassify any rejected candidate. It found review-context normalized ratios, but no candidate crossed the pre-review context thresholds in a way that invalidated the original rejection.

This means the current single-family state is not being treated as an artifact of an obvious low-frequency concentration-gate bias.

## Operational Consequence

The Phase 2 operating frame is single-edge:

```text
Execution-eligible first paper stream: breakout_retest only
Same-family variants: observer-only unless separately authorized later
Diversification uplift: none
Compounding: disabled through paper and any future micro pilot
Measured-cost floor: suspend if net expectancy after measured cost falls below +0.15R
```

The controlling operational document is:

- `xau-usd/xauusd-phase1/docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md`

## Conditions To Reopen Diversification Research

The project may reopen diversification research only under one of these conditions:

1. A new data class is added, such as real-yield, DXY, Treasury-rate, futures-volume, options, or news-calendar data.
2. A new broker or venue data source materially changes the available microstructure evidence.
3. A new author proposes a mechanically distinct hypothesis family and pre-registers it before any result-producing run.
4. A future review explicitly asks for a new versioned candidate class and accepts the opportunity cost.

Any reopened idea must use a new versioned hypothesis, a new SHA256 registration, and the forward-looking gates in `docs/HYPOTHESIS_LOCKING.md`.

## Prohibited Interpretation

This finding must not be used to:

- tune rejected v0 hypotheses in place
- lower gates for old results
- count same-family candidates as diversified portfolio legs
- authorize Phase 2 or live trading before the measured-cost and soak gates pass
