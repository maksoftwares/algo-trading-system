# INDEPENDENT REVIEW — A1 XAU M5 MOMENTUM LOSS-AVOIDANCE REPAIR
Date: 2026-07-02 | Reviewer: Independent (Claude) | Offline/review only; nothing here touches runtime.
All numbers recomputed from `a1_momentum_variants_two_year_2024_07_2026_06_h1h4_diag_usd_20260701/..._h1_h4_aligned_both_trades.csv` (1,120 trades). ATR/stop filters verified INDEPENDENTLY via trade-geometry reconstruction (SL exits: stop=|entry−SL|; TP exits: stop=dist/1.5; ATR=stop/2.5 above the 350pt floor) — not by trusting the unmounted signal log.

## VERDICT: APPROVE_FOR_EXACT_MT5_RERUN

## 1. Verification — everything reproduces
Base: n=1,120, WR 44.38%, net +1,292.94, PF 1.27, ex-top-5 +1,071.56, 18/24 months, balance DD 7.45% — all match.
Repair combo (ATR>1.5 + block 09/10): n=867, WR 47.52%, net +1,619.82, PF 1.41, ex-top-5 +1,398.44 — match to the cent, including the ATR filter through my independent reconstruction (941/+1,384.96/PF 1.31 for ATR-only).
Minor discrepancies (immaterial): (a) I count 20/24 positive months for the combo, not 21/24 — 2025-08 is −0.34 USD and was presumably rounded positive; (b) `profit_aed` column is USD (correctly disclosed); (c) hold≤15m cluster (106, PF 0.57) confirmed.

## 2. Overfit challenge — the repair passes, with one weak link
- **Both halves**: combo improves H1 (PF 1.19→1.31) and H2 (1.31→1.47). Confirmed.
- **All 8 quarters**: base is positive 8/8 (a stronger fact than 18/24 months); combo raises PF in 7/8 quarters, never flips one negative. This is the single best robustness fact in the packet.
- **ATR threshold is structural, not mined**: sweeping 1.0→2.5 gives smooth monotone WR/PF gains (47.5→48.9 WR, 1.41→1.46 PF) with no spike at 1.5. Below 1.4 the filter is inert (stop-floor censoring: stop=max(2.5·ATR,350pt) makes ATR≤1.4 indistinguishable). 1.5 is a defensible frequency-preserving choice.
- **Redundancy note**: because of the same floor formula, "stop>400pt" ⟺ "ATR>1.6". Their stop-filter and ATR-filter rows are one filter wearing two hats. Correctly, only one entered the combo.
- **Hour block**: hour 10 is negative in BOTH halves (−27/−133). Hour 09 is the weak link: ~0 in H1, −98 in H2 — one-half evidence only. Market-structure defense (server 09–10 Dubai = 05–06 UTC pre-London lull; momentum initiated in thin post-Asia chop fails when London flow arrives) is plausible and consistent with A1's realized morning weakness, but 09 rests on a story plus one half. Mitigation: the rerun list includes a block-10-only variant — if it matches the combo, drop 09 and keep the simpler rule.
- **Concentration**: best combo day = 7% of net; no month, day, or top-winner dependence. Removed trades = 253 (23%) — retention is healthy.
- **Statistics**: WR 47.52% vs the 40% breakeven of the 1.5R bracket (realized win/loss ratio 1.56): z≈4.5 even before month-consistency evidence. After accounting for ~7 variants × ~7 filter rows of selection, this survives.

## 3. Trade-level ≠ tester-level (the caveat is real and quantified)
Guard log shows 1,144 `own_position_exists`, 209 `cooldown_active`, 176 `daily_trade_cap_reached` blocks. Removing 253 trades re-opens those slots: the rerun will admit DIFFERENT trades, not just the kept 867. Direction of that effect is unknown — this is exactly why the exact rerun is mandatory and why the pass gates below include an n-sanity band, not just PF.

## 4. Exact MT5 rerun list for Codex (pre-registered, no optimizer)
Two-year window 2024.07.01–2026.06.30, every-tick, USD, same EA, new inputs `InpMinAtrAbsoluteForEntry` and `InpBlockedEntryHoursCsv` (default-off):
1. `h1_h4_aligned_both` — control re-run (must reproduce 1,120/+1,292.94).
2. `h1_h4_atr_gt1p5`.
3. `h1_h4_no_09_10`.
4. `h1_h4_atr_gt1p5_no_09_10` — the candidate.
5. `h1_h4_atr_gt1p5_no_10_only` — tests whether 09 pulls weight.
6. EXPLORATION TIER (label diagnostic, separate): candidate + entry-quality tightening using EXISTING inputs — `InpMinBodyFraction` 0.45→0.55, `InpLongCloseLocation` 0.72→0.78 (short 0.28→0.22), plus one new input `InpMaxThreeBarMoveAtr=4.0` (exhaustion cap; currently n=40 evidence — treat as hypothesis, not finding).
7. FREQUENCY TIER (label diagnostic, separate): candidate + `InpOnePositionPerMagic=false` capped at 2 concurrent (new input). Evidence hint: entries ≤60min after a prior entry run WR 54.9%/PF 1.86 — burst continuation is the EA's best regime and 1,144 signals were blocked by the one-position rule.
Rules: run 1–5 as the decision set; 6–7 are exploration and CANNOT be promoted from this pass (they'd need their own OOS confirmation) — that's how we avoid re-entering the best-of-N trap.

## 5. Pass/fail gates for the rerun (variant 4 vs variant 1, set now)
PASS requires ALL: net ≥ control net; PF ≥ 1.35; WR ≥ 46.5%; n within 867±15% (sequencing sanity); ex-top-5 > 0; ≥18/24 positive months; equity DD ≤ control DD.
If variant 5 is within noise of variant 4 (net within ±10%, PF within ±0.05) → adopt 5 (block 10 only).
FAIL any gate → REVISE (report divergence between trade-level and tester-level; no threshold re-tuning in the same pass).

## 6. Win rate >50% — honest answer plus concrete levers
Blunt part first: at a fixed 1.5R bracket, WR>50% is the wrong target. Breakeven is 40%; 47.5% with ratio 1.56 is a real expectancy edge (PF 1.41, DD 8%). Filters that chase WR>50% on this dataset cost money: ATR>2.5 → WR 48.9% but net −186 vs combo and n falls to 568; skip-after-same-day-loss → WR 48.1%, net −320 vs combo. I also tested and REJECT as mining-bait: day-of-week filters (Mon/Tue look good — no structure, one-sample), anti-burst spacing filters (bursts are the BEST trades), ATR ceilings (no exhaustion signal in stop geometry).
Levers that could legitimately raise WR (in priority order):
1. **Entry-quality tightening on already-logged features** (tier 6): body_fraction, close_location, three-bar band [0.7, 4.0]. These are pre-entry, already inputs, and mechanistically select cleaner breaks. Realistic gain: +1–2pp WR at −10–20% n.
2. **Second-bar hold confirmation** (small new code): require the NEXT M5 bar to not close back inside the broken range before entering. Directly attacks the ≤15m fast-stop cluster (106 trades, PF 0.57) with a pre-entry rule. Cost: later entries, slightly worse average entry price; must be exact-tested. This is the single most promising WR idea because it's causally aimed at the diagnosed failure mode.
3. **Export the tester signal logs into the repo** (`a1_xau_m5_momentum_signal_log.csv` lives only in `C:\MT5A1M5MomentumBacktest`). With per-signal body_fraction/close_location/break_distance joined to outcomes, the next review can test entry-quality thresholds offline BEFORE burning tester runs — and the ML feature_budget work (0/6) gets 6 candidate features for free.
4. If the owner insists on the >50% optic: lowering RR to ~1.2 raises WR mechanically (same edge, different split). Register it as a separate strategy variant, never as a "fix".

## 7. Frequency
Combo: 1.66 trades/weekday average, but distribution matters: ≥1 trade on only 59.7% of weekdays, ≥2 on 44.7%, ≥3 on 27.1%. The owner's "a few trades most days" is NOT met — 40% of weekdays are flat. That is the H1+H4 alignment doing its job (6,463+1,109 signals blocked): frequency is the price of the only filter that made the two-year number positive. n=867 over 24 months is statistically adequate for evaluation. The one frequency lever with supporting evidence is tier 7 (2 concurrent positions in bursts); softening H4 (slope-only) is possible but expect PF dilution toward the h1-only variant (PF 1.19). Do not buy frequency with hour-unblocking or ATR-floor drops — that's repurchasing the diagnosed losses.

## 8. Demo-readiness path (boundary respected — no runtime action now)
1. Codex runs §4; gates §5 decide.
2. If PASS: draft frozen forward-demo spec for `A1_XAU_M5_MOMENTUM_H1H4_ATR15_NO_09_10_V0` (or NO_10 variant), cloning the structure of `A1_MOMENTUM_FROZEN_FORWARD_TEST_SPEC_2026_07_02.md`: SHA256-locked EA+set, dedicated magic, 0.01 lot, 8 weeks or n≥60, kill switch, pre-registered PASS PF≥1.30 / ex-top-5>0 / no-day>25% / ≥2 months positive; FAIL PF<0.8@n≥40 or 10 consecutive losses.
3. Owner decision (queued, not urgent): the currently attached momentum lane runs `directional_session_htf_both`, whose two-year record is PF 1.19, 12/24 months, DD 24.6% — clearly inferior to this candidate's diagnostic. If §4 confirms, relock the lane to the new rule via a fresh spec + attach packet. Until then, leave runtime untouched.
4. Explicitly NOT approved: scaling, live capital, ML label consumption, or treating tier 6/7 exploration results as promotable.

## 9. Summary of arithmetic/data concerns
- 21/24 combo positive months should read 20/24 (2025-08 = −0.34). Cosmetic.
- `short_only` row used a smaller data footprint (113,501 bars) — fine since it FAILed, but the runner should pin identical footprints for comparability.
- Signal-log features referenced by the analysis are not in the repo — export them (see §6.3).
- Trade CSVs still name the column `profit_aed` in a USD run — rename per-run or add a `currency` column; this WILL bite someone eventually.
