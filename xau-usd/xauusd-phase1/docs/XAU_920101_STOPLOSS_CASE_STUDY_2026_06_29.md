# XAU 920101 Stop-Loss Case Study - 2026-06-29

Scope: read-only analysis of the recent A1/A2 XAUUSD `breakout_retest` trade under `A1/A2_XAU_920101_EVENING_H1_ONLY_TREND_V2_20260629`. No runtime change is made by this note.

## Trade Summary

| Field | A1 | A2 |
|---|---:|---:|
| Account | `1025742` | `1033030` |
| Order / deal | `4311724` / `3972040` | `4311725` / `3972041` |
| Time broker / Dubai | `2026.06.29 12:20:01` / `16:19:56` | `2026.06.29 12:20:01` / `16:19:56` |
| Direction | SHORT | SHORT |
| Fill | `4043.30` | `4043.27` |
| SL | `4048.94` | `4049.06` |
| TP | `4035.29` | `4035.41` |
| Stop distance | `546.11` planned points / `564` observed initial points | `546.11` planned points |
| Cost estimate | `0.0916R` | `0.0916R` |
| Guard result | `pass` | `pass` |

## Evidence Sources

- A1 order log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_order_log.csv`
- A2 order log: `C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_order_log.csv`
- A1 signal log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_signal_log.csv`
- Position path observer: `C:\MT5PortablePositionPathObserver\MQL5\Files\position_path_log_20260629.csv`

## What Happened

The trade was directionally correct later, but the stop was hit before the move continued.

| Path metric | Value |
|---|---:|
| First observed position path row | `12:20:10` broker |
| Best unrealized point | `12:29:50`, ask `4038.30` |
| Best unrealized result | `+18.36 AED`, `+0.8865R` |
| Close detected | `13:00:20`, ask `4049.81` |
| Worst observed result at close | `-21.16 AED`, about `-1.02R` realized / `-1.15R` path from fill |
| First signal sample above SL | `13:05:00`, ask `4051.06` |
| First signal sample below TP | `13:55:00`, ask `4032.27` |

The market first moved in our favor to nearly `+0.89R`, then bounced hard enough to stop the short, then resumed downward and later traded through the original TP area. In plain English: the direction was not the main problem; timing and trade management were.

## Root Causes

1. **Late/chased market entry after the planned signal level.**  
   The signal row had planned short entry `4047.39`, but the actual A1 fill was `4043.30`, about `409` points lower. That is roughly `0.75R` beyond the planned signal entry. The EA entered after a large part of the breakout impulse had already happened.

2. **No profit protection after meaningful favorable movement.**  
   The trade reached about `+0.89R`, but the current management allowed it to round-trip into a full stop. A break-even move, partial profit, or MFE-based exit rule would have reduced or avoided this loss on this specific trade.

3. **Stop was not wide enough for the snapback.**  
   The stop sat at `4048.94`; the post-entry bounce reached at least `4051.06` in the later signal sample. A wider structure stop may have survived and later reached TP, but widening stops blindly can damage expectancy and must be tested.

4. **H1 trend filter did not fail.**  
   The trade passed the H1-only filter and the position path observer showed H1 slope bearish during the trade. The H1 trend direction was aligned with the eventual selloff. This was an entry/management failure, not a simple trend-filter failure.

## Fixes To Test Before Any Runtime Change

| Proposed fix | Would it have helped this trade? | Risk |
|---|---|---|
| Chase-distance guard: block if market fill is more than `0.30R-0.50R` beyond planned entry | Yes, this trade was about `0.75R` chased | May block strong breakout winners |
| Break-even at `+0.75R` or `+0.80R` | Likely yes; trade reached `+0.8865R` | Can cut winners before TP |
| Partial profit at `+0.75R`, runner to TP | Yes, would have banked some profit | More complex attribution |
| MFE giveback exit: after `+0.75R`, close if trade falls back below `+0.20R` | Likely yes | Needs careful replay/backtest |
| Wider structure stop above snapback high | Would have survived this case | Increases loss size and cost sensitivity |
| Wait-for-pullback re-entry after breakout impulse | Could avoid selling the low | May reduce frequency |

## Recommended Next Experiment

Do not change live/demo runtime immediately. Run an offline replay on all A1/A2 `920101` evening trades with three shadow management variants:

1. `CHASE_GUARD_050R`: skip entries whose actual fill is more than `0.50R` beyond planned entry.
2. `BE_AFTER_080R`: move stop to break-even after `+0.80R`.
3. `PARTIAL_075R_BE`: take 50% at `+0.75R`, move remainder to break-even, keep original TP.

Promotion rule: only deploy if a rule improves realized/deduped PnL, reduces full-stop losses, and does not destroy the already-small trade count.

## Verdict

This loss should be classified as `VALID_DIRECTION_BUT_POOR_ENTRY_MANAGEMENT`. The short idea was eventually right, but the EA entered after a stretched breakout impulse and had no mechanism to protect a nearly `+0.89R` favorable move.
