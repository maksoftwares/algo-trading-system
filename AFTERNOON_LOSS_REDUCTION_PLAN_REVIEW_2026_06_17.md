# Review — Afternoon Loss Reduction Plan (2026-06-17)

Reviewer: Claude. Scope: **XAUUSD, demo only.** Critical review of the proposed Afternoon Loss
Reduction Plan. **Boundary: review only; no runtime/EA/preset change authorized here.**

## Headline verdict

**The methodology is excellent; the premise is 86% already-solved.** Before building a seven-filter
afternoon stack, look at what the afternoon loss actually *is*: on the 586-signal deduped real-fill
evidence, afternoon is **−523**, and **−452 of that (86%) is the round family** — which A3 has already
dropped and which the loss-avoidance review recommends quarantining fleet-wide. **Remove round and the
entire afternoon problem shrinks to ≈ −28 to −71 over ~25 signals — basically flat.** That residual is
too small and too noisy to justify most of the proposed filters; fitting rules to ~25 trades is exactly
where curve-fitting lives.

### Afternoon −523, by family (deduped, verified)

| Family | Signals | Win% | PnL | Share of afternoon loss |
|---|---:|---:|---:|---:|
| **round_family** | 55 | 27% | **−452.13** | **86%** |
| breakout_core | 11 | 27% | −53.09 | 10% |
| session_extreme | 16 | 31% | −17.81 | 3% |
| **Afternoon, round removed** | **~25** | — | **≈ −28 to −71** | residual |

So the single highest-value "afternoon" action is the **round quarantine you already have** — not a new
afternoon filter layer. The realistic win you predicted ("afternoon: strongly negative → flat") is
**already delivered by dropping round.** Build the rest only if the *round-removed* residual stays
materially negative across regimes on a larger sample — and right now it doesn't look like it will.

## What's strong (keep this)

The framework is disciplined and matches everything we've validated: shadow-first, kept-vs-blocked,
protect evening/night, promote only proven rules, no parameter tuning, forward-demo confirmation, and a
humble expected outcome. The decision rule is sound. None of the criticism below is about the *process*
— it's about *which filters* and *in what order*, given the family split.

## Filter-by-filter assessment

| Filter | Likely to help? | Curve-fit / regime risk | Verdict |
|---|:--:|:--:|---|
| **Duplicate family mutex** | Yes (modest) | Low | **Keep** — already owner-approved & implemented (`WOULD_DUPLICATE_FAMILY_EVENT`). But the key `family+symbol+dir+bar` **misses cross-family** stacking (breakout+round same bar); drop `family` from the key for exposure control. Note: once round is quarantined, its afternoon value shrinks |
| **Trend alignment** | Maybe (small set) | **High (regime)** | **Shadow only, and not afternoon-specific.** Use **H1/H4** to match the live improved lane, not M15+H1 (M15 is noisier and a new knob). Both tracked days were up → can't separate "counter-trend loses" from "shorts lose"; needs a **down-day**. Only ~11 afternoon breakout trades exist to act on |
| **EA-specific afternoon permission** | Looks clean, isn't | **High (selection)** | **Drop as written.** "Permit EAs with positive afternoon expectancy" = ranking on tiny per-EA per-session samples = data-snooping. It also collapses to "drop round in afternoon," which the round quarantine already does. *Respectfully, this is not one of the clean ones* |
| **Clean retest score** | Unknown | **High** | **Defer.** "Cleaner structure" is a subjective, tunable definition — the classic hindsight filter. With ~25 residual trades there's nothing safe to fit it to |
| **Impulse exhaustion block** | Maybe | **High (tunable)** | **Defer.** "Large move" is a threshold to be tuned; needs a *pre-registered* definition and a real sample. (EA-T1 already has an impulse veto whose value isn't established.) |
| **Stricter afternoon spread/cost cap** | Weak | Medium-High | **Defer.** A session-specific cost knob on top of a cost signal we already found fragile (June-10-driven, threshold unstable, different universe). Afternoon's problem is round/direction, not cost |
| **MFE protection (BE/partial @ +0.5R/+0.75R)** | No | n/a | **Drop — already disproven.** Prior logged-path replay: Partial+BE *reduced* PnL by 134 AED, dragged 21 winners, saved 0 losers; BE-only saved 0, improved 0 (`REJECTED_FOR_DEPLOYMENT`). Partial can't leave a runner at 0.01 lot, and winners' avg adverse excursion (0.46R) sits under a 0.5R trigger, so BE clips winners. Don't re-test without a materially different, pre-registered case |

## Answers to your review questions

**Which filters most likely to help?** In order: (1) **round quarantine** (not on your list, but it *is*
the afternoon fix — 86%); (2) **duplicate mutex** with a cross-family key (modest, mechanism-clean);
(3) **trend alignment** as a *general* H1/H4 shadow (already running on the improved lane), pending a
down-day. The rest add little once round is gone.

**Which risk curve-fitting?** Clean-retest score, impulse-exhaustion, stricter afternoon cost cap, and —
counter to your vote — **EA-specific afternoon permission** (selection on small samples). MFE/BE/partial
isn't curve-fit so much as **already empirically rejected**.

**Exact pass/fail metrics?** Keep your decision rule and add: **net-R = losers-saved − winners-clipped**
(not loss-count); **survives best-1–2-days-removed**; **protected-cluster audit** (evening/night
breakout_core = 79 signals / +1,027 must be untouched); **minimum ~30 affected signals** per filter;
and for trend alignment specifically, **≥1 non-up regime** in the window. A filter that "helps afternoon"
by removing a handful of trades on an up-week is noise.

**How to design the shadow backtest?** Replay on **deduped real broker fills, one universe** (don't mix
the 586 family set with the 704/906 cost set). For each filter, log a would-block flag per signal; then
report kept-n/PnL, blocked-n/PnL, winners-clipped, net-R, best-day-removed net, and the protected-cluster
delta — per session. Then run it **forward, shadow-only, on live ticks** before any guard goes active.

**How to avoid blocking good trades?** Protected-cluster audit (never touch evening/night breakout_core);
judge by **net**, not loser-count; apply every rule to winners as well as losers; and require the net to
survive best-day removal and hold forward. The live A/B (plain vs improved) is already this instrument.

**Filter, reduce, or fully disable afternoon?** **None of those as a session rule — fix the cause.**
Don't blanket-disable afternoon (blunt; it would also kill the ~11 breakout and any future good trades).
**Reduce by removing round** (done on A3), then re-measure. The residual is small enough that the right
answer is "leave it and keep tracking," not "build a filter stack."

**Recommended implementation order:**
1. **Measure round-removed afternoon first** (done here: ≈ −28 to −71). Free, and it reframes the whole plan.
2. **Round quarantine** — the actual afternoon fix (already live on A3; the fleet-wide extension is the lever).
3. **Duplicate mutex** with a cross-family key — general exposure control, small afternoon benefit.
4. **Stop and re-measure.** If round-removed afternoon stays materially negative across ≥1 non-up regime on ≥~30 signals, *then* revisit (4a) H1/H4 trend alignment shadow. Otherwise leave afternoon alone.
5. **Do not** build clean-retest / impulse / afternoon-cost-cap / EA-permission / MFE layers on the current ~25-signal residual.

## On your vote

You picked **trend alignment + duplicate mutex + EA-specific afternoon permission.** Mutex — agreed.
Trend alignment — agreed *as a general H1/H4 shadow*, not an afternoon-specific M15+H1 rule, and it needs
a down-day. **EA-specific afternoon permission — I'd swap it out:** it sounds principled but it's
selection bias on small per-EA samples, and it reduces to "drop round in afternoon," which you've already
done. Replace it with **"measure round-removed afternoon first"** — cheaper, and it tells you whether any
of this is even needed.

## Do-not-do
- Don't build the 7-filter stack before removing round and re-measuring — you'd be fitting to ~25 trades.
- Don't re-test MFE/BE/partial — already rejected, and partial can't work at 0.01 lot.
- Don't use M15 in the trend filter, or make a separate afternoon trend rule — reuse the H1/H4 shadow.
- Don't promote any direction/trend filter on up-day-only evidence.
- Don't touch evening/night breakout_core (79 signals / +1,027).
- Don't edit running EAs; shadow-first, owner-approved runtime only.

**Boundary:** review only. Demo only. No MT5 runtime, EA, preset, chart, order, or account change is
authorized by this document.
