# INDEPENDENT DEEP-DIVE — A1 XAU M5 MOMENTUM: WHERE THE LOSSES LIVE
Date: 2026-07-02 | Reviewer: Independent (Claude) | Offline only; no runtime recommendations herein.
Methods: all headline numbers recomputed from rerun trade CSVs; per-trade entry features joined from the
exported `_signals.csv` (916/916 matched); post-entry paths reconstructed from broker-matched capital.com
M5 bid/ask bars (available 2024-07→2025-06 = first half only) with a simulator validated against tester
outcomes at 99.3% sign agreement, corr 0.992, net 403 vs 423 USD. Conservative intrabar rules (adverse
extreme processed first; management can never act in its own trigger bar).

## VERDICT: PROMOTE (h1_h4_atr_gt1p5_no_09_10 → frozen forward-demo spec, owner approval pending)
…and formally ADOPT "PF 1.35–1.45 at 46–48% WR" as the target. The >50% WR goal should be retired for
this edge — §6 shows precisely what it costs and why. NEED_MORE_BACKTEST applies only to the two
follow-on levers (§5: OOS window, max2_concurrent, RR extension), not to the candidate itself.

## 1. Independent verification (all match Codex to the cent)
| Variant | n | WR% | Net USD | PF | ex-top-5 | pos. months* | t/weekday | DD(bal)% |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| control h1_h4_aligned_both | 1120 | 44.38 | 1292.94 | 1.267 | 1071.56 | 18/24 | 2.15 | 7.45 |
| h1_h4_atr_gt1p5 | 971 | 45.62 | 1331.54 | 1.295 | 1110.16 | 19/24 | 1.87 | 7.53 |
| h1_h4_no_09_10 | 1053 | 45.30 | 1470.84 | 1.329 | 1249.46 | 18/24 | 2.02 | 7.22 |
| **h1_h4_atr_gt1p5_no_09_10** | **916** | **46.72** | **1524.56** | **1.366** | **1303.18** | **19/24*** | 1.76 | 6.95 |
| h1_h4_atr_gt1p5_no_10_only | 940 | 46.38 | 1480.71 | 1.345 | 1259.33 | 19/24 | 1.81 | 7.02 |
| explore_entry_quality | 835 | 45.99 | 1192.50 | 1.310 | 971.12 | 20/24 | 1.61 | 6.93 |
| explore_max2_concurrent | 893 | 47.14 | 1650.71 | 1.427 | 1418.33 | 22/24 | 1.72 | 7.88 |
*I count 19/24 for the candidate vs the report's 20/24 (exit-month bucketing; one ~zero month). Immaterial.
Candidate frequency: 1.76/weekday; ≥1 trade on 60.3% of weekdays, ≥2 on 45.5%. Gate check: all 7 reviewer gates PASS — confirmed.

## 2. Winner-vs-loser factor table (the central negative result)
Mean entry-feature values, winners vs losers (916 trades):
| Feature | Winners | Losers | Separation |
|---|--:|--:|---|
| ATR | 3.47 | 3.40 | none |
| body_fraction | 0.77 | 0.78 | none |
| close_location | 0.680 | 0.678 | none |
| |3-bar move| ATR | 1.97 | 1.99 | none |
| break_distance ATR | 0.77 | 0.79 | none |
| est. cost_R | 0.035 | 0.036 | none |
| spread pts | 27.7 | 27.5 | none |
| **hold minutes** | **272** | **166** | **large — but post-hoc** |
Bucketed splits (absmove, body_fraction, break_distance, cost_R) are non-monotone noise; ATR is gently
monotone (1.5–2.0 bucket PF 1.13 vs 3.5–5.0 PF 1.53); hold-time is the only strong axis: ≤15m PF 0.59,
15–60m PF 1.05 (n=331!), 1–3h PF 1.57, >8h PF 3.54.
Plain English: **at the moment of entry, future winners and losers look identical on every measurable
candle/impulse/cost feature. The outcome is decided by what the market does next, not by entry anatomy.**
This is why `explore_entry_quality` failed in the exact tester and why further entry filtering is a dead end.

## 3. Top 5 loss causes (path-anatomy, H1-half reconstruction, 226 SL exits)
1. **Dead-on-arrival reversals (37.6% of losers)**: price never reaches even +0.25R. No pre-entry feature
   separates them (§2); a second-bar-hold confirmation was simulated and REJECTED — it skips 20% of
   trades, keeps WR flat (45.6%), and cuts net 422→342. These losses are the irreducible base rate of
   M5 breakout entries. My prior review floated this idea; the test kills it and I withdraw it.
2. **Mid-flight failures (35.4%)**: reach +0.25→0.75R then stop out. The mirror fact: 47% of WINNERS
   endure ≥0.5R adverse excursion (18% nearly touch the stop before hitting TP). Loser paths and winner
   paths overlap so heavily that early-exit rules cannot separate them either — see §6.
3. **Givebacks (27.0%)**: reach ≥+0.75R (14.6% reach ≥+1.0R) then round-trip to the stop. Painful but
   NOT fixable at a profit: every protection scheme tested converts more winner-value than it saves (§6).
4. **Hour 09–10 chop** (now removed by the candidate): confirmed structural — the only two hours negative
   in both halves; blocking them is worth ~+230 USD and −6% trades. Residual weak hours (03, 22, 11) are
   one-half artifacts with n≤51 — do NOT block them (mining).
5. **Low-ATR entries** (now floored at 1.5): the 1.5–2.0 ATR band is still the weakest kept region
   (PF 1.13, n=192). A 2.0 floor would add ~+0.7pp WR and +0.05 PF but costs 21% of trades — poor trade
   given the frequency requirement; not recommended.

## 4. Exit management — tested and REJECTED with numbers (H1-half sim, same 414 trades)
| Overlay | WR% | Net USD | PF | vs no-mgmt net 403 |
|---|--:|--:|--:|--:|
| none (replicates tester) | 45.4 | 403 | 1.27 | — |
| BE at +0.5R | 26.8 | 211 | 1.24 | **−48%** |
| BE at +0.75R | 34.8 | 283 | 1.26 | −30% |
| BE at +1.0R | 38.4 | 314 | 1.25 | −22% |
| Lock +0.5R @ +1.0R | 53.4 | 228 | 1.18 | −43% |
| Lock +0.25R @ +0.75R | **60.1** | 198 | 1.18 | **−51%** |
| Partial 50% @ +0.75R + BE | 60.1 | 222 | 1.20 | −45% |
| Time-stop 60m if losing | 30.2 | 159 | 1.15 | −61% |
Every overlay trades expectancy for win-rate optics. Cause: XAUUSD M5 noise routinely retraces through
entry (47% of winners see ≥0.5R heat); protection sells the strategy's best asset — room to survive.
This closes the "can profit protection turn losers into winners" question: it turns WINNERS into
breakevens. The 1.5R fixed bracket with no management is, so far, the best exit for this entry.

## 5. What actually has headroom (ranked by expected value)
1. **OOS window test of the frozen candidate — 2022-07→2024-06** (same rules, zero changes). The single
   most valuable missing evidence: every result so far lives in one two-year window that was also used
   for selection. Broker M5 data exists back to 2016. Pre-registered OOS gates (lower bar, set now):
   net > 0, PF ≥ 1.15, ex-top-5 > 0, no month < −15% of period net.
2. **max2_concurrent → decision track.** Best headline of the rerun (PF 1.43, 22/24 months, ex-top-5
   +1,418) and it was PRE-registered in my last review before results existed — it has already survived
   one honest hurdle. My stress recompute: positive 7/8 quarters (worst 2024Q4 −18), H1 PF 1.31 / H2 1.50,
   best day 7.5% of net, DD 7.88% (higher than candidate's 6.95% — expected, exposure doubles in bursts).
   Needs: risk framing (max concurrent margin, worst-case 2×stop day), then the same OOS window run.
3. **RR extension probe (diagnostic).** H1-half sim, same entries, no management: RR 1.0 → WR 53.4%,
   net 222; RR 1.5 → 45.4%, 403; RR 2.0 → 39.4%, 516; RR 2.5 → 35.0%, 654; RR 3.0 → 31.4%, 726. The
   curve is MONOTONE UP in net/PF: this is a trend-continuation edge that monetizes tails, not hit-rate.
   Worth two exact-tester variants (RR 2.0, 2.5) on the full window. Warning attached: WR in the low-30s
   and longer holds are psychologically brutal and DD profile changes; this is a different animal to trade.
4. NOT recommended: further entry filters (§2), exit management (§4), second-bar confirmation (§3.1),
   day-of-week blocks (Mon/Tue look good — no structure, refuses pre-registration), blocking hours 03/22/11
   (one-half artifacts), ATR floor 2.0 (frequency cost), Sunday block (n=15, cosmetic).

## 6. Direct answers to the owner's questions
- **Why still <50% WR?** Because the payoff is asymmetric (1.5R): breakeven WR is 40%, and the edge
  expresses as winners running further, not winning more often. The RR curve (§5.3) proves the edge's
  natural shape: net INCREASES as WR decreases. 46.7% at 1.5R is healthy, not deficient.
- **Easiest losses to avoid?** Already avoided: hours 09/10 + ATR≤1.5 (the candidate). Nothing else
  separable remains at entry — proven by feature table, by the exact entry_quality run, and by the
  confirmation-bar sim.
- **Which losses must be tolerated?** All three remaining classes (§3.1–3.3). Avoiding givebacks or
  mid-flight failures with stops/locks destroys 22–51% of net because winner paths overlap loser paths.
- **Can protection turn losers into winners?** It converts ~27% of losers into ~breakeven — and converts
  far more winner-value into breakeven at the same time. Net effect always negative in this system (§4).
- **>50% WR without killing frequency?** Yes, mechanically: RR 1.0 gives 53.4% WR at IDENTICAL frequency
  — and −45% net. Or Lock@0.75R gives 60% WR at −51% net. Both are win-rate cosmetics priced in real money.
- **Best realistic target?** Higher PF at 46–48% WR. Formally: PF ≥ 1.35, 19+/24 months, DD < 8%,
  ~1.7–1.8 trades/weekday — which is exactly what the candidate already delivers.
- **Exact next MT5 variants** — see §7.

## 7. Exact variant list for Codex (pre-registered; no optimizer; decision set vs exploration labeled)
Window A = 2024.07.01–2026.06.30 (current), Window B = 2022.07.01–2024.06.30 (OOS, new).
1. `oos_h1_h4_atr15_no0910_2022_2024` — candidate frozen, Window B. DECISION. Gates: net>0, PF≥1.15, ex-top5>0.
2. `oos_max2_concurrent_2022_2024` — max2 variant, Window B. DECISION for max2 promotion. Same gates + DD≤10%.
3. `rr_2p0_h1_h4_atr15_no0910` — Window A, InpRiskReward=2.0. EXPLORATION. Interesting if net≥1524 and DD≤1.5× candidate.
4. `rr_2p5_h1_h4_atr15_no0910` — Window A, InpRiskReward=2.5. EXPLORATION, same bar.
5. (conditional) if 1 AND 2 pass: `oos_rr_2p0` on Window B before any RR adoption.
Rules: 1–2 decide promotion strength; 3–5 cannot be adopted from Window A alone (selection re-entry).
No other variants in this pass. Especially: no threshold nudging on ATR/hours — that door is closed.

## 8. Warnings (overfit, bias, missing data)
- **Single-window selection bias remains the biggest open risk**: ATR floor, hour blocks, and the H1/H4
  alignment itself were all chosen on Window A. §7.1 is the antidote; until it runs, treat the candidate
  as strong-diagnostic, not proven.
- Path simulations (§4, §5.3) cover H1-half only (bars end 2025-06-30) at M5 granularity with
  conservative assumptions; treat magnitudes as estimates, directions as reliable. The capital.com bars
  post-2025-07 should be exported to extend this capability (ask Codex to refresh the phase0 bar archive).
- The 09/10-hour "server time" in this tester aligns with the bar file's raw timestamps, not Dubai+4 —
  hour semantics are internally consistent but the wall-clock interpretation in prior prose ("pre-London
  lull") should be re-verified against the actual data clock before being quoted as market structure.
- `profit_aed` still means USD in these runs (known); positive-month counts differ by ±1 with bucketing
  convention; `explore` variants carry no promotion rights from Window A.
- Sunday rows (n=15) exist in the trade set — confirm the tester's weekend session handling matches the
  demo broker's before forward comparison.
