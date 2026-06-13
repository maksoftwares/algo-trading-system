# Plan — "End Each Evening Session (16:00-19:59 Dubai) Positive" (2026-06-13)

Your "Evening" time bucket already = 16:00-19:59 Dubai (the `time_bucket` field in
`PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` is recorded in Dubai/local terminal time — confirmed
against `PHASE2_DEMO_XAUUSD_LAST_7D_TIME_BUCKET_PATTERN.md`). So this is the exact 4-hour
window you described. 10 trading evenings of data exist (Jun 1-5, 8-12), kept (deduped)
trades only:

| Date | n | WR | Total PnL | BUY PnL (n) | SELL PnL (n) |
|---|---:|---:|---:|---:|---:|
| Jun 1 | 7 | 42.9% | -45.70 | -56.95 (4) | +11.25 (3) |
| Jun 2 | 2 | 100% | +71.23 | 0 (0) | +71.23 (2) |
| Jun 3 | 11 | 54.5% | +152.51 | +3.13 (2) | +149.38 (9) |
| Jun 4 | 3 | 100% | +85.96 | +39.44 (2) | +46.52 (1) |
| Jun 5 | 15 | 53.3% | +131.81 | -64.17 (7) | +195.98 (8) |
| Jun 8 | 10 | 30.0% | -42.28 | -65.73 (6) | +23.45 (4) |
| Jun 9 | 28 | 35.7% | +72.82 | -318.79 (12) | +391.61 (16) |
| Jun 10 | 41 | 41.5% | +236.31 | -188.96 (19) | +425.27 (22) |
| Jun 11 | 53 | 26.4% | -489.67 | -262.69 (22) | -226.98 (31) |
| Jun 12 | 24 | 16.7% | -377.00 | -14.14 (11) | -362.86 (13) |
| **10-day total** | | | **-204.01** | | |

6 of 10 evenings were already positive. 4 were negative (Jun 1, 8, 11, 12).

---

## Finding 1 — Most evenings have ONE dominant profitable direction; the other side is the loss

Look at the BUY/SELL split: on Jun 3, 5, 9, 10, SELL was strongly profitable while BUY was
flat-to-losing on the same evening, same symbol set. On Jun 12, BUY was nearly flat (-14)
while SELL was the disaster (-363). **If the losing-direction trades on these 5 evenings
had simply not been taken, every one of Jun 3/5/9/10/12 improves — Jun 9 goes from +73 to
+392, Jun 10 from +236 to +425, Jun 12 from -377 to -14.** This is the clearest, highest-
leverage finding here: the portfolio isn't failing to find the trend — about half its
trades each evening are fighting it.

## Finding 2 — Our own EAs' first-hour direction does NOT reliably predict the evening's winning side

I checked whether "which direction did our EAs fire first (16:00-16:59)" predicts which
direction wins the rest of the evening: **3 matches, 3 mismatches, 2 ties out of 8 days
with first-hour trades** — no better than a coin flip. Jun 9 and Jun 12 are the costliest
mismatches: on Jun 9 the first hour leaned BUY (4 vs 1) but SELL was the winning side all
evening; on Jun 12 the first hour leaned SELL (3 vs 1) and SELL was the catastrophic side.

**This means "ride the direction our EAs are already trading" is not a viable early-warning
signal** — by construction, several of these EAs (round-family especially) fade impulses,
so their first signals can point the wrong way. An early-direction read needs to come from
the **market itself** (price momentum), not from "what our EAs did first."

## Finding 3 — A simple portfolio-wide "stop digging" threshold turns -204 into +220 over 10 evenings

Simulated: once cumulative evening-session PnL (summed across all kept trades, all
families) drops to or below a threshold, block all new entries for the rest of that
evening (resets next day).

| Stand-down threshold | 10-day evening total | Jun 9 | Jun 10 | Jun 11 | Jun 12 |
|---|---:|---:|---:|---:|---:|
| (none / actual) | -204.01 | +72.82 | +236.31 | -489.67 | -377.00 |
| -50 | +88.82 | -63.23 | -76.85 | -54.34 | -50.19 |
| -75 | +27.01 | -81.60 | -76.85 | -83.85 | -84.22 |
| -100 | -103.94 | -127.45 | -119.50 | -106.46 | -104.06 |
| -150 | +79.82 | -174.48 | **+236.31** | -162.89 | -172.65 |
| **-200** | **+220.21** | **+72.82** | **+236.31** | -240.12 | -202.33 |

**-200 is the sweet spot in this sample**: it never touches Jun 9 or Jun 10 (both stay
fully intact at +73 and +236, because neither evening ever dropped that far), while it cuts
Jun 11's loss roughly in half (-490 → -240) and Jun 12's by almost half (-377 → -202).
Tighter thresholds (-50/-75/-100) "save" more on the bad days but also chop off Jun 9/10's
late-evening recoveries before they happened — those days dipped early and rallied later,
and a tight stop would have locked in the dip.

**Honest framing of your goal**: a PnL-threshold stand-down alone gets the 10-day evening
total from -204 to +220, but it does NOT make every evening green — Jun 1, 8, 11, 12 stay
negative (just smaller). Getting *every* evening positive requires Finding 1's directional
fix as well, which needs new data (below).

---

## The Plan

### Step 1 (now, no new data needed) — Live evening-session ledger
Add a running "Evening session PnL" counter to the position-path observer / weekly packet:
resets at 16:00 Dubai, sums realized + floating PnL across the portfolio in real time. Pure
observability, zero trading-logic change. This gives you the live number to watch tonight.

### Step 2 (now, no new data needed) — Portfolio-level evening stand-down guard
A session-scoped sibling to G4: if cumulative evening-session PnL (all kept trades, all
magics combined) falls to **≤ -200 AED**, block new entries portfolio-wide until 20:00
Dubai (resets next evening). Backtest above: -204 → +220 over 10 evenings, without
touching either big winning evening. Recommend: shadow-log this for 3-5 evenings (does it
fire, and was the post-trigger PnL actually negative — i.e. would it have helped?) before
arming as a real block.

### Step 3 (needs fresh M5 bars — data gap, flagged previously) — Build a market-based "session bias" signal
Compute the same momentum measure G1 uses (`ret12_atr` on M5, i.e. 1-hour price momentum)
for XAUUSD/EURUSD/GBPUSD at 16:00 Dubai (session open). This is an EXTERNAL read of "which
way is the market actually moving right now" — independent of what our EAs signal (Finding
2 showed our EAs' own first moves aren't reliable for this). Requires refreshing the M5 bar
export through today (the same gap noted for G1 backtesting).

### Step 4 — Validate the bias signal against these 10 evenings
Once Step 3's data exists: does "momentum direction at 16:00" match the evening's actual
winning direction (SELL on Jun 3/5/9/10, BUY-leaning on Jun 12, etc.) better than the ~50%
hit rate of "EA's own first move"? Target: meaningfully above 50% (say ≥65%) over enough
days before trusting it.

### Step 5 (only if Step 4 validates) — Directional gate, shadow first
If the bias signal validates, log (don't yet block) what "skip entries against the 16:00
bias direction" would have done each evening. Given Finding 1, this is where the larger
upside is — e.g. Jun 9/10/12 nearly double in this scenario. But this changes which trades
get taken, not just how many, so it goes through the same shadow → A3-style guarded trial →
owner-authorization process as G1, not a quick patch.

---

## On "flip the direction" specifically

I'd separate two different ideas that can both feel like "flipping":

- **Skip the losing side** (Finding 1: don't take the BUY signals on a SELL-dominant
  evening) — this is supported by the data above and is what Step 5 targets. It requires
  knowing the dominant direction *before* it's obvious, which is Steps 3-4.
- **Reverse the signal** (take SELL when the EA says BUY) — this is a different bet
  entirely, untested, and risky: a wrong BUY signal being skipped doesn't mean the opposite
  SELL would have won at that exact entry/level. I'd recommend NOT pursuing this without its
  own dedicated backtest — it's a new strategy, not a filter on the existing ones.

---

## Recommended order for next week

1. Step 1 + Step 2 are cheap, evidence-backed, and don't wait on anything — these can go in
   the same maintenance window as T0/A3 (additive, no conflict with the approved work
   order).
2. Refresh the M5 bar export (Step 3's prerequisite) — this also unblocks the previously-
   flagged G1 backtest gap, so it serves two purposes.
3. Steps 4-5 are next week's research output, not this week's runtime change — they need
   the refreshed data and a few more evenings to validate against.

This plan doesn't change or delay T0/A3. Steps 1-2 can be added to the same Codex batch as
a low-priority addendum if you'd like; Step 3 (bar refresh) is worth prioritizing since it
unblocks two open items at once.
