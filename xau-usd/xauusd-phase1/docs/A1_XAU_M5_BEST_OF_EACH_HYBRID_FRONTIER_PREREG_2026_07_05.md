# A1 XAU Best-Of-Each Hybrid Frontier Preregistration

Generated: 2026-07-05

## Purpose

The owner asked whether the best useful parts can be combined because each branch solved one part of the target:

- frequency / win rate: Step 3 best frequency frontier;
- payoff: high-payout split and high-payout ORREV composition;
- core WR plus 2R shape: H4/D1 long-only compression clue;
- high hit rate: profit-lock / TP1-heavy split corner.

This diagnostic combines those exact-MT5 evidence streams at signal level to see whether a hybrid book can reach the owner target.

## Boundary

- Offline exact-MT5 ledger composition only.
- No MT5 launch, no runtime attach, no charts, no presets, no orders, and no broker state mutation.
- Inputs are already-realized exact MT5 Strategy Tester trade CSVs and exact MT5 signal ledgers.
- Same-direction entries from different components within five minutes are deduped; earlier/source-priority signal wins.
- This diagnostic is not a demo spec. Any survivor would need reviewer reconstruction and then exact MT5/runtime specification work.

## Fixed Component Pool

1. `freq_step3_frontier`: Step 3 best frequent portfolio kept signals.
2. `hp_v13_orrev`: Step 3 high-payout V13 + ORREV composition.
3. `split_compromise_f33_r30_be_1r`: Step 1 compromise cell.
4. `split_high_wr_f67_r20_be_tp1`: Step 1 high-WR cell.
5. `split_high_payout_f33_r30_be_never`: Step 1 high-payout cell.
6. `h4_d1_long_best_box2_atr80`: H4/D1 long-only frequency stress winner.
7. `h4_d1_long_broad_box3_atr60`: H4/D1 high-WR broad variant.
8. `rr2_lock080_010`: profit-lock high-WR / low-payoff corner.
9. `orrev_london_firm_stop15`: opening-range reversal activity / 2R corner.

## Decision Rules

- `OWNER_GOAL_HIT`: WR >= 50%, realized avg win/loss >= 2.0, active weekday coverage >= 90%, positive net.
- `CORE_SHAPE_FREQUENCY_GAP`: WR >= 50%, realized avg win/loss >= 2.0, positive net, but active coverage < 90%.
- `NEAR_OWNER_FRONTIER`: WR >= 48%, realized avg win/loss >= 1.8, active weekday coverage >= 70%, PF >= 1.30, positive net.
- Otherwise reject.
