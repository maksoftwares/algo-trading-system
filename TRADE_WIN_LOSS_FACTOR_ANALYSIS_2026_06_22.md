# Demo Trade Win/Loss Factor Analysis

**Scope:** all realized demo trades on record, `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`, 2026‑06‑01 → 2026‑06‑19.
**Method:** deduped to unique fills, joined each trade to M5/H1/D1 bars at its entry (broker time auto‑detected as **UTC+4 / Dubai**, validated 99.9% by entry‑price‑in‑bar), then compared winners vs losers across trend, EMA/MA, volatility, volume, spread, timing, and trade mechanics. Win = `profit_aed > 0`.

## Headline

The book is a **small net loser**: 698 decided trades, **261 wins / 437 losses = 37.4% win rate**, average **−0.08R**, net **−942 AED**. With the fixed 1.5R target, breakeven needs a **40%** win rate — so you're sitting just under the line.

The most important finding for your question: **no single number cleanly separates winners from losers.** Every factor's effect size is small (|Cohen's d| < 0.17). There is no "EMA was X on winners and Y on losers" silver bullet — the edge, where it exists, is weak and only shows up in combination. That is exactly the condition the ML signal‑quality layer is built to exploit, so this validates the project's direction rather than contradicting it.

That said, several **consistent tilts** do appear. Ranked by how much they move the win rate:

## 1. How fast the trade was stopped — the strongest single tell

Losers die quickly; winners survive. Median hold was **13 min for losses vs 23 min for wins**, and win rate climbs sharply with survival time:

| Hold time at entry | Win rate | n |
|---|---|---|
| under ~7 min | 23.4% | 175 |
| ~7–17 min | 29.9% | 174 |
| ~17–35 min | 48.3% | 174 |
| over ~35 min | 48.0% | 175 |

Trades that get run over almost immediately are ~3‑in‑4 losers. This points at **entry quality/timing** (price reversing right after fill) as the core loss driver — not the exit or target.

## 2. Trend alignment (H1 EMA) — modest but consistent

Entering **with** the H1 trend beats fighting it. Price‑vs‑H1‑EMA in the trade direction: top quartile **42.3%** vs most counter‑trend **34.3%**; H1‑EMA slope aligned **41.7%** vs against **36.9%**. Categorically, with‑H1‑trend **39.2%** vs against **35.1%**. The D1 regime signal was noisy and didn't add much — H1 is the useful timeframe here.

## 3. Session — London is the weak window

| Session (UTC+4) | Win rate | n |
|---|---|---|
| Rollover (17–24h) | 41.1% | 158 |
| New York (12–17h) | 40.7% | 182 |
| Asia (00–07h) | 34.9% | 229 |
| London (07–12h) | 32.6% | 129 |

New York and the rollover window carry the book; **London (32.6%) and Asia are the drag.**

## 4. Strategy family — `breakout_retest` is the best; round‑retest variants drag

| Candidate | Win rate | n |
|---|---|---|
| breakout_retest | 46.0% | 113 |
| round_number_retest_v0 | 42.5% | 40 |
| symbol_normalized_round_retest_v0 | 36.2% | 458 |
| swing_breakout_retest_v0 | 32.1% | 28 |
| session_extreme_retest_v0 | 32.0% | 50 |

The `breakout_retest` family (the one the ML layer is scoped to) is clearly the strongest at 46%, while the bulk of volume — the `symbol_normalized_round_retest` variant (458 trades at 36%) — and the swing/session‑extreme variants pull the average below breakeven.

## 5. Volume and volatility — secondary edges

Highest M5 **tick‑volume** quartile wins **42.3%** vs ~34–35% in the quiet/mid quartiles — dead‑tape entries fare worse. Winners also formed in slightly **higher volatility** (M5 ATR ~675 vs ~647 pts) with slightly **wider stops** (~781 vs ~741 pts), i.e. tight stops in quiet conditions get clipped before the move develops.

## What did *not* discriminate
Direction (buy 36.3% vs sell 38.3% — negligible), day of week (flat ~36–38%), planned reward:risk (fixed ~1.5 both sides), and **spread** (constant 50 in the bar data — not analyzable here; real per‑fill spread/slippage would need the fill logs).

## The composite picture
The losing entries cluster as: **counter‑trend, in London/Asia, low‑volume, tight‑stop, round‑retest‑variant** setups that reverse within minutes. The winning subset clusters as: **`breakout_retest`, with the H1 trend, during NY/rollover, in normal‑to‑higher volume/volatility.** Filtering toward that subset is where the win rate moves from ~37% toward and past the 40% breakeven — which is precisely the meta‑label the ML layer would learn.

## Caveats
- Realized trades are keyed by **magic/lane, not the A1/A2/A3 logins** (the export has no login column), so this is segmented by candidate/lane; 761 cross‑lane duplicate fills were removed (2,059 → 712 unique).
- Sample is modest (698 decided over 19 days); per‑bucket win rates carry roughly ±5–8% noise — read the tilts as directional, not precise.
- Indicators are computed from the normalized M5/H1/D1 bars at entry; spread/slippage realism is limited by the bar data (constant spread).
