# Two-Week Trade Weakness & Fix Audit — Profit-Preservation Review (2026-06-14)

**Question answered:** (1) list every weakness in the last two weeks of trades, (2) check
whether each is fixed to the best of what the data teaches, and (3) verify the fixes cut
losses **without** killing the profit we were actually capable of making.

**Data:** `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` — 1,510 closed trades, 2026-06-01 → 2026-06-13,
account A1 (`1025742`), recomputed independently with pandas. Veto analysis uses
`PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv` (per-signal `impulse_alignment` + realized outcome).
Recomputed totals (raw **−1,919**, dedup **−2,132**) reconcile with the existing forensics
(−1,964 / −2,157) within partial-day rounding, so the ledger and method are trusted.

---

## Bottom line

The fixes are **correctly aimed**. Every loss-cutting rule (impulse veto, streak/daily
brakes, cost caps, clone retirement, mutex de-duplication) is scoped to the **losing**
round/session families. The one genuinely profitable thing in the data — `breakout_retest`
on **XAUUSD in the evening (+641 AED, 62% win)** — is frozen and untouched. So the profit
engine is preserved *by construction*.

Two honest qualifications:

1. The **brakes** (G3/G4) are the only fix that touches winners. On this sample they net
   **+881 AED**, but they get there by halting trading during bad runs, which forgoes
   ~+5,316 of winners to dodge ~−6,197 of losers. Net-positive here, thin margin, worth
   monitoring — they are *insurance*, not alpha.
2. The biggest **unaddressed loss sits on the winning family**: `breakout_retest`'s
   EUR/GBP trades at 0.05 lot. A3 does not touch this (breakout is frozen, correctly), so
   this weakness is still live on A1/A2 and is the highest-value remaining fix for
   "minimise losses without hurting profit."

The "profit we had before" was **mostly an illusion**: 47% of trades were duplicate clones,
and the two lanes that produced the headline gains evaporate on a one-trade-per-signal
basis. The fixes remove that illusion; they do not remove real edge.

---

## 1. Where the "profit" actually came from

Cumulative **raw** PnL peaked at **+1,640 AED on Jun 10**. The **de-duplicated** reality at
that same moment was **−452**. The good-feeling number was duplication stacked on a losing
kernel.

| Lane | Raw PnL | De-dup PnL | What it really was |
|---|---:|---:|---|
| `p2weakness_br_v1` | **+548** (n=10) | **−14** | gain was clone co-fires; vanishes deduped |
| `session_extreme..._repair_v1` | **+385** (n=20) | n/a (all duplicate) | overfit SHORT-only; luck when regime matched |
| `breakout_retest` XAUUSD evening | — | **+641** (n=26, 62% WR) | **the one real, repeatable edge** |
| round family (both clones) | −2,666 | **−1,711** | the loss engine |

De-duplication (the mutex fix) only changes the *total* by +213 AED, but it removes the
**+1,640 → −452 peak illusion**. Expect headline good-days to look smaller and calmer after
the fix — that is correct, not a regression.

---

## 2. Weakness ledger (data-confirmed)

| # | Weakness | Evidence (this dataset) | Severity |
|---|---|---|---|
| W1 | **Duplicate clones** — same signal traded 2× under different magics | 714 / 1,510 trades (47%) are duplicates; largest same-second cluster = 6; 64 clusters ≥3 | High |
| W2 | **Round-family counter-trend churn** — direction from one M5 candle + always-present round levels | round family −1,711 dedup, loses in **all four** time buckets (−343/−772/−238/−357) | High |
| W3 | **Uncapped stacking** — no position cap | **max 42 concurrent open positions** on a ~4.5k account | High |
| W4 | **No armed daily stop / flatten** — the −42% day ran to completion | Jun 12 −1,185 dedup (−2,623 raw) in a single day | High |
| W5 | **Session-extreme family** — counter-trend + server-vs-Dubai time-base bug | session family −300 dedup, 28% WR | Med |
| W6 | **Overfit repair lanes** — calendar+direction rules, no market-state check | `*_repair_v1` positive only when regime matched hard-coded side | Med |
| W7 | **EUR/GBP breakout drag at 0.05 lot** — on the *winning* family | breakout all-symbol +0 vs XAUUSD-evening +641; Jun 12 breakout −531 was mostly EUR/GBP | **Med–High (unaddressed)** |
| W8 | **Cost/spread churn** — ~60 round signals/day, max spread paid | round 17-min median holds, all-bucket losses | Med |

---

## 3. Fix coverage — is each weakness handled?

| Weakness | Fix | In live A3 code? | Status |
|---|---|---|---|
| W1 duplication | Atomic GV mutex claimed before `OrderSend` + startup self-test | **Yes** (verified in source) | **Fixed** |
| W2 counter-trend round | Impulse veto (EA-T1) + M15-structure filter (EA-T2); clones retired to observer | **Yes** | **Fixed** (see §4 — veto is the strong one) |
| W3 stacking | `InpMaxOpenPositionsPerMagic = 1` | Yes (per magic) | **Fixed on A3**; ⚠ T1+T2 run together → up to 2× correlated; A1 control still uncapped by design |
| W4 daily stop / flatten | G4 entry-stop (−150/day) deployed; Guardian Stage B flatten **not armed wk 1** | Entry-stop yes; flatten no | **Partial** — only per-trade SL + entry-block protect open risk now |
| W5 session family | Retired (not on A3); time-base bug fix is source-only | Not deployed | **Mitigated by retirement**; code bug still in retired source |
| W6 overfit repair lanes | Excluded from A3 entirely | n/a (not deployed) | **Fixed by exclusion** |
| W7 EUR/GBP lot drag | — (breakout frozen; A5 lot-size proposal declined) | No | **Unaddressed** |
| W8 cost/spread | `InpMaxEstimatedCostR=0.15`, spread cap 75pts, min-60s, 0.01 lot | Yes | **Fixed** |

---

## 4. Profit-preservation — do the fixes block the upside? (the crux)

### 4a. The impulse veto is surgical — it cuts losers, not winners
Round family, de-duplicated, split by the −1.5 veto decision:

| Veto −1.5 | Trades | PnL | Win rate |
|---|---:|---:|---:|
| **BLOCK** (vetoed) | 103 | **−1,490** | **23%** |
| **KEEP** (traded) | 314 | −64 | 39% |

The blocked set is overwhelmingly losers (23% WR, −1,490). The kept set is essentially
unchanged. **The veto removes loss, not profit.** Threshold sensitivity:

| Threshold | Blocked PnL (avoided) | Kept PnL |
|---|---:|---:|
| −1.0 | −1,966 | **+413** |
| −1.5 (chosen) | −1,490 | −64 |
| −2.0 | −1,039 | −514 |

Note the chosen −1.5 is the *conservative* end — it blocks **fewer** trades than −1.0, which
would have turned the kept round family **positive (+413)**. So the live risk is the veto
being slightly too lenient, **not** too aggressive. (Caveat: both thresholds were fitted on
this same June window; treat −1.0's edge as a forward hypothesis, not a settled win.)

### 4b. Scoping the veto to round-only is provably right
Apply the same impulse signal to breakout and it carries **no information**: breakout
counter-impulse trades win **34%**, identical to breakout overall (**34%**). Forcing the veto
onto breakout would forgo **+126 AED** (at −1.0) for zero discrimination. The design applies
the veto exactly where it separates winners from losers and nowhere else. ✓

### 4c. The brakes (G3/G4) are blunt insurance — the one fix that costs some upside
Round family, de-duplicated, streak + daily-stop simulation:

- Without brakes: **−1,711**  → With brakes: **−830** (improvement **+881**)
- They block 317 trades: **203 losers (−6,197 avoided)** and **114 winners (+5,316 forgone)**.

So the brakes **do** sacrifice real winners — they just sacrifice fewer than the losses they
prevent, netting +881 on this sample. That margin is thin, and in a calmer/mean-reverting
regime the post-streak winners could outweigh the avoided losses. Keep the brakes (they cap
tail risk like Jun 11–12), but treat them as loss-limiters to monitor, not profit-neutral.
*(First-order reconstruction: SL inferred from exit comments, entry-order accumulation;
matches the deep-dive's independent estimate.)*

### 4d. Net
| View | PnL | Note |
|---|---:|---|
| Raw (all, with duplication) | −1,919 | the rollercoaster |
| De-dup (mutex fix applied) | −2,132 | the honest baseline |
| — breakout (kept, **untouched**) | −11 all-symbol / **+641 XAUUSD-evening** | the preserved edge |
| — round + session (fixed/retired) | −2,033 | what the fixes target |

The fixes subtract from the **−2,033 loss engine** and leave the **+641 edge** alone. That is
the definition of "minimise losses without hurting profit." The only profit they remove is
the duplication/overfit illusion.

---

## 5. Residual weaknesses & recommendations (priority order)

1. **EUR/GBP breakout lot-size (W7) — highest-value open item.** It is a loss on the
   *winning* family and nothing in A3 touches it. Re-open the 0.05→0.01 (or session-gated)
   EUR/GBP proposal with the Jun-12 −531 evidence. This is the cleanest remaining
   "cut a loss that doesn't cost edge" move.
2. **Arm the automated flatten (W4).** Today, open-position risk is held only by each
   trade's SL + the G4 entry-block. The mechanism that would have stopped the −42% day is
   still not live on A3. Close the Guardian Stage-B drill and arm it.
3. **Cross-EA exposure (W3 residual).** EA-T1 and EA-T2 use separate mutex namespaces, so
   on a shared round signal both can open — up to 2× correlated 0.01 positions. Either add
   an account-level position cap or accept and document it. (Also: arming both at once
   muddies which repair worked — the plan had held EA-T2 for Phase B.)
4. **Revisit veto −1.5 vs −1.0** once A3 has out-of-sample data — the data hints −1.0 cuts
   materially more loss, but it is in-sample today.

## 6. Caveats
- Demo data only (AED, 0.01 lot); conclusions are about logic/expectancy, not live fills.
- The −1.5 and −1.0 thresholds were fitted on this June window; forward results will shrink.
- The brakes counterfactual is a first-order reconstruction, consistent with the prior
  deep-dive but not a tick-exact replay.
