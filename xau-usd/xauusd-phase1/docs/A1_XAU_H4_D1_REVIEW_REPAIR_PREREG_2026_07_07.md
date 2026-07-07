# A1 XAU H4/D1 Review Repair Preregistration

Date: 2026-07-07

## Scope

Run exactly two exact-MT5 repair probes against the current research frontier `F67-H16 no-f33`.

The probes apply only to the H4/D1 long components:

- `h4_d1_long_best_box2_atr80`
- `h4_d1_long_broad_box3_atr60`

The frequency layer remains unchanged. No TP/SL, source priority, session/hour mask, or frequency-source setting is changed.

## Baseline

Baseline artifact:

- `outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`

Baseline headline:

- Signals: `3751`
- WR: `50.23%`
- W/L: `2.0002`
- Active weekdays: `86.39%`
- PF: `2.0336`
- Net: `22294.46 USD`
- Stress `-$0.30/ticket` W/L: `1.9029`
- Exit-time positive weeks: `54.81%`
- Recent 3M net: `-1226.32 USD`
- May 2026 net: `-1055.98 USD`

## Test 1: H4/D1 Supportive-State Guard

Hypothesis: the H4/D1 long engine loses too much when daily trend support is absent. A fixed D1 supportive-state guard can improve Q2 2026 and weekly loss shape without deleting the profit engine.

Exact EA rule:

- Apply only when `InpSignalMode = SIGNAL_D1_COMPRESSION_H4_EXPANSION`.
- Apply only to long signals.
- Allow entry only when:
  - `D1 close[1] > D1 EMA20[1]`
  - `D1 EMA20[1] >= D1 EMA20[6]`

Tester inputs:

- `InpH4D1SupportiveStateGuardEnabled=true`
- `InpH4D1SupportiveEmaPeriod=20`
- `InpH4D1SupportiveSlopeLagBars=5`

## Test 2: H4/D1 Weekly Loss Governor

Hypothesis: the H4/D1 source should trade normally until the component is in a confirmed bad week. After closed H4/D1 component PnL breaches a fixed weekly loss threshold, further H4/D1 entries are blocked until the next broker week.

Exact EA rule:

- Apply only when `InpSignalMode = SIGNAL_D1_COMPRESSION_H4_EXPANSION`.
- Track closed PnL for the current broker week using only already closed deals for the current symbol and magic number.
- If closed weekly H4/D1 PnL is `<= -150 USD`, block further H4/D1 entries until the next broker week.

Tester inputs:

- `InpH4D1WeeklyLossGovernorEnabled=true`
- `InpH4D1WeeklyLossLimitUsd=150.00`

## Recomposition

For each test:

1. Run exact MT5 Strategy Tester for both H4/D1 components.
2. Remove the baseline H4/D1 rows and the previously removed `step1_f33_r30_be_never` source from `A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv`.
3. Add the two replacement H4/D1 exact-MT5 ledgers.
4. Dedupe using the existing signal-composition function.
5. Score full-window metrics, stress `-$0.30/ticket`, last-12, recent 3M, May 2026, weekly shape, source contributions, and guard block counts.

## Pass/Fail

PASS requires all of:

- WR `>= 50.0%`
- W/L `>= 2.0`
- Active weekdays `>= 84.0%`
- Stress `-$0.30/ticket` W/L `>= 1.90`
- Recent 3M net improves by at least `750 USD` versus baseline
- May 2026 improves by at least `500 USD` versus baseline
- Positive weeks improves by at least `3 percentage points`
- Full net remains `>= 17500 USD`
- Worst week improves by at least `20%`

If both tests fail, freeze this repair path and move to a preregistered new red-week source class.
