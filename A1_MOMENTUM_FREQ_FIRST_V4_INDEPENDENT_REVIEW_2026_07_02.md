# INDEPENDENT REVIEW — FREQUENCY-FIRST V4 (freq_h1_h4_long_rr0p7_v4_combo_rank1)
Date: 2026-07-02 | Reviewer: Independent (Claude) | Offline/review only. All numbers recomputed from raw CSVs.

## VERDICT: ACCEPT_AS_DEMO_TEST_WORTHY (with conditions) — this satisfies guard #1 of the readiness note.
Owner approval (guard #2) and the conditions in §4 are still required before any attach.

## 1. Verification — everything reproduces
Four-year (2022.07–2026.06): n=1,132, WR 65.90%, net +1,042.07, PF 1.449, top-10-removed +899.51,
36/47 positive months, balance DD 5.6%, best day 5.4% of net, 383 active days, 2.96 trades/active day.
Halves: 2022–24 PF 1.404 (WR 65.0%), 2024–26 PF 1.471 (WR 66.7%). All match Codex.
Realized win/loss ratio 0.750 → breakeven WR 57.1%. Observed 65.9% = +8.8pp margin, raw z≈6.2 on 1,132 trades.

## 2. What makes this candidate stronger than I expected
- **The edge exists BEFORE the hour mask.** The all-hours base (long RR0.7 + cost≤0.05R) is itself
  positive: n=1,751, WR 62.7%, PF 1.20 (+827 USD), z≈4.9 vs breakeven. The 10-hour mask refines an
  existing edge; it does not manufacture one. This is the single most important robustness fact.
- **7 of 10 blocked hours are independently negative in BOTH halves** (2,9,10,11,12,17,23) — same
  standard the 09/10 block passed earlier. Only 13/19/21 are mixed-evidence passengers (21 has no
  trades at all — it's a no-op).
- Codex pre-empted my standard objection with a mask-neighborhood robustness pass (nearby top-ranked
  masks rerun on all three windows) — the right test, run before I asked.
- Concentration is clean: best day 5.4%, top-10 removal keeps +900, DD 5.6% (lower than the RR2 lane's 6.8%).
- Falling-gold months: +172 net across 13 months, 77% positive — steps aside/keeps edge, same healthy
  pattern as RR2 long-only.
- The forward gates in the readiness note are appropriately strict for once: WR≥55% (not 50 — leaves
  margin over the 57.1% breakeven... see §4-C3), kill at WR<50%@80 trades, PF floor, activity floor.

## 3. What the owner must understand before choosing it
- **The WR optics have a price.** Same four years: V4 makes +1,042 USD; the sparse RR2 lane makes
  +1,745. Per trade: +0.92 vs +2.19 USD (≈+0.12R vs +0.23R). V4 buys 66% WR and 3-trades-per-active-day
  at ~40% less total profit. That may be the right buy — losing streaks are shorter, DD lower, and an
  equity curve you can live with is worth real money — but it is a purchase, not a free upgrade.
- **"Frequency-first" is bursty, not constant**: 63% of weekdays have ZERO trades (383 active days of
  ~1,043). On active days you get ~3 trades; most days you get none. If the objective is "trades most
  days", V4 does not deliver that either — no long-only H1/H4-gated system can.
- **Cost sensitivity is 3–4x the RR2 lane.** Average win is $4.51 on 0.01 lots; median spread (~$0.28)
  is already ~6% of it. Demo slippage will bite RR0.7 much harder than RR2.0 — this is exactly what the
  forward test must measure, and why tester results may degrade live. Expect some WR shrinkage.
- **All four years of history are burned.** ~216 tester variants in this wave (V0–V13, portfolio/mask/
  target/cost searches) used both windows including the former OOS. Raw z≈6.2 survives any reasonable
  multiplicity penalty (max-z for ~1,000 independent tries ≈3.7), and the base-without-mask fact (§2)
  is the strongest antidote — but there is NO untouched historical window left for ANY momentum variant.
  Forward demo data is the only clean evidence from here on. This must be written into agent.md.
- Even in-sample, 42% of active days are losers and losing streaks of 7 active days occurred. At 66%
  WR people forget this; write it next to the chart.

## 4. Conditions attached to acceptance (C1–C4)
- **C1 — kill-switch collision (inherited, still open):** the momentum EA honors
  `experimental_demo_kill_switch.txt`, which the A1 guardian writes on +50/+100 AED days from the
  920101 lanes. Whichever momentum lane runs forward, this censors its sample. Resolve (own filename)
  or pre-commit to annotating/excluding halted days before the forward clock starts.
- **C2 — replace vs parallel:** recommendation = PARALLEL with a NEW magic (e.g. 932300), not
  replacement. The RR2 forward test started today 04:46; killing it after ~12 hours wastes the only
  clean test in flight, and the two lanes answer different questions (expectancy-first vs WR-first).
  Exposure of two correlated 0.01 lanes is acceptable on demo. If the owner insists on one lane,
  supersession per the readiness note is procedurally fine — pin the switch timestamp.
- **C3 — one gate fix:** the pass bar "WR ≥ 55%" is only −2.1pp from the 57.1% realized breakeven; a
  55–57% outcome would "pass" while losing money. Change to: WR ≥ 58% AND PF ≥ 1.25 AND net > 0 —
  net/PF conditions already exist; raising the WR floor to 58% makes the gates internally consistent.
- **C4 — freeze the search.** No V14. No new masks, targets, cost caps, or portfolio recombinations on
  2022–2026 data — every additional variant now only adds selection debt to a fully burned dataset.
  The next information arrives from forward fills only. (Research budget can go to the C5 shadow
  scoreboard from the RR2 review, which covers both lanes for free.)

## 5. Context for the owner's original question (68% WR at 1:2)
V4 is the honest version of that portfolio: 65.9% WR at 0.75:1 realized — the market charged ~1.3R of
payoff to move WR from 41% to 66%. The advertised 68% at 2:1 (+1.04R/trade) remains ~9x V4's
expectancy (+0.12R/trade) and is not supported by anything in four years of this system's data. The
WR/payoff exchange rate held exactly; Codex found the best seat on the curve rather than a way off it.
