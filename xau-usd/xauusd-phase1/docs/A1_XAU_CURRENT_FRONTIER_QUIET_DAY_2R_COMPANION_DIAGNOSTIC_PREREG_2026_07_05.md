# A1 XAU Current Frontier Quiet-Day 2R Companion Diagnostic Prereg - 2026-07-05

Status: `PREREG_DIAGNOSTIC_ONLY`

## Purpose

The current best exact-ledger frontier, `F67-H16 no-F33`, reaches WR `50.23%` and W/L `2.0002`
but only `86.39%` active weekdays. The latest standalone M5 2R sources solved activity but failed
win rate:

- liquidity sweep-reclaim 2R: WR `30.19%`, W/L `2.0650`, active `98.08%`
- HTF/M5 pullback-reclaim 2R: WR `31.09%`, W/L `2.1445`, active `81.84%`

This diagnostic asks one narrow question: can those already-frozen sources help **only** on days
where the current exact frontier has zero signals?

## Boundary

- Offline diagnostic only.
- No MT5 terminal launch, chart/profile/preset edit, order, position, or runtime attach.
- Candidate add-ons are not exact MT5 ledgers. They are bar-level diagnostics and cannot produce
  headline/demo claims.
- If this somehow produces a candidate, it still requires exact MT5 implementation/replay and
  reviewer review before any spec.

## Fixed Inputs

Base:

- `A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`

Frozen add-on sources:

- `A1_XAU_M5_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_2026_07_05_BEST_EXAM_TRADES.csv`
- `A1_XAU_M5_HTF_PULLBACK_RECLAIM_2R_DIAGNOSTIC_2026_07_05_BEST_EXAM_TRADES.csv`

Common evaluation window:

- `2022-07-01 -> 2025-06-30`, because both diagnostic add-on ledgers end there.

## Fixed Composition Rules

1. Keep every base signal in the common window.
2. Compute base active weekdays in the common window.
3. An add-on source may contribute only on weekdays where the base has zero signals.
4. For each add-on source, test two fixed cadences:
   - `first_per_missing_day`: earliest add-on signal on each base-missing weekday.
   - `all_on_missing_day`: all add-on signals on base-missing weekdays.
5. Test the two add-ons individually and together with fixed priority:
   - base first
   - HTF/M5 pullback-reclaim second
   - liquidity sweep-reclaim third
6. For same-timestamp add-on collisions, keep the higher-priority row and publish dropped rows.

## Decision Rule

This diagnostic can only justify exact-MT5 follow-up if a composed common-window row reaches:

- WR `>=50%`
- W/L `>=2.0`
- active weekdays `>=90%`
- last-12 WR `>=48%`
- last-12 W/L `>=1.85`

If not, the branch is rejected. No reviewer token is spent.
