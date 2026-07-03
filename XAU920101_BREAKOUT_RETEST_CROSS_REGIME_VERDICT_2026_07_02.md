# CROSS-REGIME STRESS VERDICT — XAU 920101 BREAKOUT-RETEST FAMILY (incl. shorts-revise)
Date: 2026-07-02 | Reviewer: Independent (Claude) | All numbers recomputed from trade CSVs.
Sources: `outputs/reports/mt5_backtests/xau_920101_breakout_retest_{q2_2026_20260701153851, q2_2026_faststop_repair_20260701165204, q2_2026_profit_protection_20260701190731, q1_2026_short_revise_20260701200732}/`

## VERDICT: REJECT (do not build the shorts-led/morning variant; do not forward-test any variant of this family)

## 1. What was tested
My prior REVISE conditions required: an edge that survives top-5 removal, >=2/3 positive months,
and a cross-regime (earlier-quarter) backtest. Codex ran the full 21-variant family on Q1 2026.
That is exactly the right test — credit where due. The result refutes the family.

## 2. The two "winners" are mirror images, each dead out-of-sample
| Variant | Q2 2026 | Q1 2026 |
|---|---|---|
| repair_24h_h1_faststop_min800_lock100_050 (Q2 winner) | +633, PF 1.49, n=68 (ex-top5 −138) | +18, PF 1.01, n=100, ex-top5 −613, 1/3 months |
| server_20_05_h1_smart (Q1 winner) | +27, PF 1.02, n=95, ex-top5 −717, 1/3 months | +928, PF 1.89, n=64, ex-top5 +204, 3/3 months |

Each quarter's best variant is ~flat in the other quarter and deeply negative ex-top-5. With 21
variants per quarter, one variant at PF ~1.5–1.9 per quarter is what selection alone produces.

## 3. The shorts-revise hypothesis is directly refuted by Q1
- Q1 direction split flips: LONGS +834 / SHORTS +94 in the Q1 winner; shorts net-negative in 17/21
  Q1 variants (e.g. current_24h variants: shorts −515…−559, longs +690…+742).
- All `revise_short_*` Q1 variants are negative or trivially small-n (best: +224 on n=7).
- Conclusion: Q2's "shorts work, longs broken" was the FALLING regime expressing itself through the
  strategy, not a structural edge. A fixed-direction cut is regime-fitting.
- My earlier suggestion to explore a shorts+morning pocket is hereby WITHDRAWN on this evidence.

## 4. Nothing in the family passes the robustness bar in both quarters
No variant of 21 achieves, in BOTH Q1 and Q2: net>0 ex-top-5 AND >=2/3 positive months. Zero.
The committed-default protection config (lock125_080): Q2 net-negative, Q1 +567 but ex-top5 −350.
The realized demo book agrees: A3 breakout PF 0.53; 920401/920301 round-retest lanes −1,892 AED in June alone.

## 5. Constructive path (what could re-open this family)
Only a NEW pre-registered hypothesis, not another parameter sweep:
1. Direction chosen BY a regime signal (H1/D1 trend state), not fixed — note h1_d1_24h_smart
   already approximates this and lost in both quarters (Q1 −299, PF 0.88), so the bar is high;
2. Tested frozen on >=4 quarters spanning 2024–2025 (data exists — the A1 momentum two-year run
   proves the tester can do it) BEFORE any current-quarter fit;
3. Pass ex-top-5 + month-consistency in >=3 of 4 quarters.
Absent that, this family is research-archive material.

## 6. Portfolio consequence (recommendation, owner decision)
- Keep A3 breakout lanes PAUSED (they are). Do not un-pause on any Q1/Q2 variant result.
- The live A1 round-retest lanes 920401 (PF 0.88, −992 June) and 920301 (PF 0.90, −900 June) are
  the same family expressing the same non-edge with 918 June trades. SUBTRACTION recommendation
  stands: pause them; they fund nothing and dominate fast-stop losses (428 sub-15-min losing trades).
- Forward-test capacity should go to the ONE candidate with cross-month robustness inside its test
  window: A1 M5 momentum directional_session_htf_both, per its frozen spec (with the two-year
  filtered-variant condition attached).
