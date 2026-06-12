# Entry-Failure Forensics — Why "Good" Entries Die (2026-06-12)

Research question (owner's words): *why do we enter the wrong trade — it looks like it
should be entered, and in the end it fails?*

Method: every closed XAUUSD broker trade June 1 → June 12 09:15 UTC (n=728) was joined to
the exported M5 bars at its entry bar. For each trade we measured the market's state at
the moment of entry, then asked which entry-time conditions separate winners from losers.
Entry-time conditions for tonight's 138 path-observed trades (slopes, ATR, spread,
stacking) were analyzed the same way. Demo evidence only; all numbers recomputed from raw
files.

---

## 1. The finding: trades die when they fight the last hour's impulse

Define **impulse alignment** = (trade direction) × (price change over the 12 M5 bars
before entry) ÷ ATR14. Positive = entering in the direction the market just moved;
negative = entering against it.

| Entry position vs last-hour move | n | Win rate | Avg PnL | Total PnL AED |
|---|---:|---:|---:|---:|
| **Hard against** (fighting a ≥1.5-ATR move) | 163 | **28.8%** | −8.6 | **−1,405.6** |
| Mild against (0.5–1.5 ATR) | 117 | 40.2% | −1.5 | −174.8 |
| Fresh / flat (<0.5 ATR either way) | 159 | 40.9% | +7.7 | +1,231.0 |
| Mild with | 115 | 45.2% | +1.5 | +170.8 |
| **Extended with** (riding a ≥1.5-ATR move) | 174 | **48.9%** | +10.8 | **+1,872.0** |

The relationship is **monotonic across all five buckets** — a 20-point win-rate staircase
from 28.8% to 48.9%. One dimension, measured at entry, explains the bulk of the
win/lose split. For contrast: raw volatility of the prior hour (any direction) shows NO
effect (WR 39–43% flat across quiet/normal/violent hours). It is not volatility that
kills — it is *fighting* the move.

## 2. The mechanism — why the EA thinks it "should" enter

The retest trigger requires: a level nearby + one confirmation candle. After a violent
hourly move INTO a level, both conditions are satisfied almost automatically:

1. Price has just rallied/dropped to a round number or swing level → **a level is nearby
   by construction** (for round numbers, always — `ceil()` guarantees it).
2. The first pause produces an opposite-colored M5 candle → **"confirmation."**
3. The EA reads pause-at-level as rejection-of-level and steps in front of the train.

Then the path data completes the anatomy (from 52k ten-second snapshots): the trade
typically goes **green first** — losers' median MFE is +0.68R, half exceed +0.5R — because
the move genuinely pauses. That is the "it was working!" phase. Then the dominant impulse
resumes and runs through the stop. The trade was never a rejection; it was a rest stop.

This also unifies the two contradictory days:
- **June 11 (trend day):** losers were counter-trend SELLs into the rally — *hard_against* entries.
- **June 12 (reversal day):** losers were "trend-confirmed" entries — but M15/H1 slopes lag, so what the slopes called with-trend was *hard_against the fresh reversal impulse*. (Tonight's slope-based cut showed with-trend 0/10, counter-trend 50% — inverted only if you use lagging slopes; consistent if you use the last-hour impulse.)

**The unified failure law: entries fail when they fight the freshest impulse, and the
candle-color trigger systematically manufactures exactly those entries at the worst
moments. Lagging trend measures (D1 bias, slow EMAs) mislabel turns; the 60-minute
impulse measure does not lag enough to be fooled in either regime observed so far.**

## 3. Per-family dose-response — who needs the cure

| Bucket | Round family (n=546) | Breakout family (n=101) |
|---|---|---|
| hard_against | **23.7% WR, −12.7/trade (n=118)** | 50.0% WR, +13.5 (n=28) |
| mild_against | 34.5%, −8.8 | 50.0%, +13.0 |
| fresh/flat | 38.3%, +2.7 | 38.9%, +12.0 |
| mild_with | 44.0%, −1.3 | 52.9%, +6.6 |
| extended_with | **50.7%, +10.4 (n=142)** | 40.0%, +6.9 |

Two different diseases:
- **Round family**: extreme gradient. 38% of its trades are *against*-bucket entries, and they are catastrophic (23.7% WR). Its mechanism is not uniformly broken — it is broken specifically as an impulse-fader. Notably, the same EA riding momentum (`extended_with`) wins 50.7%.
- **Breakout family**: flat gradient — its swing-structure anchor already filters entry timing; even its counter-impulse fades win 50%. **It does not need this rule, and applying it would delete profitable trades.** This is why the winner wins, stated quantitatively.

## 4. Solutions, per mechanism

| # | Mechanism | Solution | Scope | Mode |
|---|---|---|---|---|
| S1 | Fading violent impulses (the −1,406 bucket) | **Impulse veto:** block entry when `direction_sign × (close[1]−close[13])/ATR14 < −1.5`. Twelve closed M5 bars, one ATR — trivially computable in MQL5 at signal time. | Round family + session_extreme ONLY (not breakout — §3) | **SHADOW first** |
| S2 | Pause-at-level misread as rejection | Broken-structure requirement (Fix Plan L3.2): a level is tradeable only after a confirmed M15 swing break in the trade direction — converts "pause" into "structure event." Complementary to S1: S1 is the cheap proxy, S2 the structural cure. | Round family kernel | SHADOW |
| S3 | Green-then-die anatomy (median loser MFE +0.68R) | Regime-conditional exit research (already pre-registered): use the SAME impulse measure as the regime tag — e.g., in against-impulse or post-impulse-flip states, tighter targets may dominate 1.5R. Do not deploy any exit change until ≥3 weeks of path data; June 1–7 replay showed the opposite in trend weeks. | Exit research lane | RESEARCH only |
| S4 | Lagging slope vetoes mislabel turns | In the trend-guarded observer, log `impulse_alignment` alongside the slope columns; score BOTH veto definitions on the same signals; let the scoreboard pick. | Observer column add | SHADOW |

## 5. Codex implementation spec (shadow-only — nothing touches runtime behavior)

1. **Add two columns everywhere signals/entries are logged** (trend-guarded observer,
   shadow-fix observer, path observer FIRST_SEEN rows, executor signal log):
   - `ret12_atr = (close[1] − close[13]) / ATR14` (signed, M5, computed at signal/entry time)
   - `impulse_alignment = direction_sign × ret12_atr`
2. **Pre-register thresholds** {−1.0, −1.5, −2.0} in a dated hypothesis file before next
   week's data: "blocking round-family + session-extreme entries with
   `impulse_alignment < T` improves family net expectancy with kept-share ≥ 60%."
3. **Weekly scoreboard** (extend the existing outcome-resolution pipeline,
   broker-joined rows only): per family × threshold — kept n/WR/net R vs blocked n/WR/net
   R, and the **dose-response table (§1 format) must remain monotonic** in each fresh
   week. A rule whose gradient flips week-to-week is regime noise; a rule whose gradient
   holds is a law.
4. **Promotion bar** (unchanged ladder): one fresh forward week minimum, blocked bucket
   clearly negative, kept bucket ≥ baseline, monotonicity intact, owner packet. Apply to
   round/session lanes only; breakout stays frozen.
5. **Do not** apply S1 to breakout_retest, do not tune thresholds mid-week, do not deploy
   S3 exits from this analysis.

## 6. Caveats — read before celebrating

- June 1–12 was trend-dominant; `extended_with` at 48.9% may be partly regime payment.
  The *against*-side finding (28.8%) is the robust leg — it held on June 11 AND tonight's
  reversal independently. The veto blocks the bad side; it does not bet on the good side.
- This is one pre-declared dimension (move maturity), but several cuts were examined
  tonight — the locked-week and following week serve as the honest out-of-sample test.
- n per family-bucket is 18–174; the round-family hard_against cell (n=118, 23.7%) is the
  statistically strongest single cell and the one the veto targets.
- All demo evidence; nothing here authorizes runtime changes outside the ladder.

## One-line answer to the owner's question

The EAs enter trades that "should work" because their trigger mistakes a pause in a
violent move for a rejection of it — the trade then goes briefly green as the move rests
(+0.68R median), and dies when the move resumes; the cure is to forbid the weak lanes
from fading any ≥1.5-ATR hourly impulse (shadow-test now), and to require a real structure
break before a level counts — which is precisely the ingredient the profitable EA already
has and the losing ones lack.
