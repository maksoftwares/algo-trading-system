# INDEPENDENT REVIEW — RR2.0 LONG-ONLY DEMO PROMOTION & RR2.5 REJECTION
Date: 2026-07-02 | Reviewer: Independent (Claude) | Offline/review only. All numbers recomputed from raw trade CSVs.

## VERDICT: APPROVE_WITH_CHANGES
Keep RR2.0 long-only active on A1 demo. The RR2.5 rejection was correct. Five changes are required
(§5) — one of them (the shared kill-switch interaction, C1) genuinely threatens forward-test validity.

## 1. Recomputed metrics (all match Codex to the cent)
| Run | Window | n | WR% | Net USD | PF | ex-top-5 | pos.months | pos.qtrs | worst mo. | bestday% | DD%(bal) |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **4-yr RR2 long-only** | 22.07–26.06 | **798** | **41.35** | **+1744.60** | **1.501** | +1466 (top-10: +1293) | 34/44 | 14/16 | −33.42 | 7.8 | 6.84 |
| RR2 long-only (cur) | 24.07–26.06 | 586 | 41.81 | +1465.17 | 1.529 | +1187.34 | 19/24 | 7/8 | −33.42 | 9.3 | 8.60 |
| RR2 long-only (OOS) | 22.07–24.06 | 212 | 40.09 | +279.43 | 1.393 | +160.38 | 15/20 | 7/8 | −12.60 | 16.0 | 4.58 |
| RR2 short-only (OOS) | 22.07–24.06 | 118 | 27.97 | −104.13 | 0.775 | −186.88 | 7/19 | 3/8 | −53.27 | — | 15.83 |
| RR2.5 long-only (cur) | 24.07–26.06 | 515 | 36.89 | +1495.00 | 1.566 | +1181.58 | 18/24 | 6/8 | **−129.01** | 9.1 | 6.55 |
| RR2.5 long-only (OOS) | 22.07–24.06 | 196 | 33.16 | +199.83 | 1.267 | +63.86 | 12/20 | 7/8 | −20.40 | 22.0 | 5.09 |
Minor: my month counts differ ±1 from Codex on two rows (exit-month bucketing); immaterial.
Spec SHA256 independently recomputed: `5566…52b9` — MATCHES the promotion report. EA's new inputs
(`InpMinAtrAbsoluteForEntry`, `InpBlockedEntryHoursCsv`) verified in source: default-off, server-hour
semantics match the tester, ATR floor applied pre-guard with logging. Chart inputs in the attachment
report match the spec line-by-line (DirectionMode=1=LONG_ONLY, RR=2.00 — not 2.5 — confirmed).

## 2. Was RR2.5 rejection correct? YES
RR2.5 wins only on current-window PF (1.566 vs 1.529 — noise). It loses OOS on every stability axis:
PF 1.27 vs 1.39, ex-top-5 +64 vs +160, months 12/20 vs 15/20, WR 33.2 vs 40.1, and its current-window
worst month is −129 vs −33. Caveat for the record: with ~200 OOS trades the RR2.0-vs-2.5 difference is
not statistically decisive — but for choosing ONE lane to forward-test, RR2.0 dominates on robustness
and frequency. Correct call, correctly reasoned.

## 3. Was the promotion justified? YES — as a forward TEST, not as validation
Strengths (verified): 14/16 positive quarters over four years; survives top-10 removal; best day 7.8%
of net; DD < 7%; worst month −33 USD; and the bull-beta objection is weaker than it looks (§4.2).
But the honest label matters — see C2.

## 4. Hidden risks (examined)
**4.1 Selection burn — the OOS window is spent.** Six variants were evaluated on 2022–24 (candidate,
max2, RR2-both, RR2-long, RR2-short, RR2.5-long); the promoted lane is the best of them, and the
direction choice itself was made ON the OOS result. The four-year run re-uses both windows, so NO
untouched historical window remains. Expected best-of-6 inflation on 212 trades is real (a PF ~1.39
best pick plausibly inflates ~0.1–0.2). This doesn't invalidate promotion-to-demo — forward data is
the only clean test left, which is exactly why demo is the right venue — but it caps confidence.
**4.2 Bull-beta / one-regime dependence — partially cleared.** Monthly PnL vs gold-return correlation
is 0.447 (unavoidable for long-only). But in the 11 falling-gold months the lane traded ~⅓ as often
(8 vs 22 trades/mo) and stayed flat (+94 total, 73% of those months positive): it steps aside rather
than bleeding. Pre-melt-up era (22.07–24.09): PF 1.34 on 281 trades. Still true: 80% of 4-yr net came
from 2025Q1–2026Q1, and a multi-year gold BEAR is unrepresented in all windows. Accept as known bound.
**4.3 Shared kill-switch contamination (C1 — the big one).** The momentum EA honors
`experimental_demo_kill_switch.txt` — the SAME file the A1 daily profit-floor guardian writes when the
920101 lanes hit the +50/+100 AED daily floor. Every day the breakout lanes lock in profit, the
momentum lane is silently halted for the rest of the Dubai day. The backtest had no such halts: the
forward sample will be systematically censored (likely on GOOD trend days), biasing the test and making
backtest-vs-forward comparison invalid. This must be fixed or explicitly accounted for (§5).
**4.4 Magic/comment reuse.** 932200 and comment `A1_XAU_M5_MOM` are inherited from the July-1
directional lane on the same chart. Deals cannot be attributed by magic or comment — only by time.
The switch timestamp exists (startup log `2026.07.02 04:46:42 INIT_OK`) but is not pinned in the spec.
**4.5 Low-WR psychology.** At 41% WR, an 8–10 loss streak is EXPECTED within ~100 trades (median max
streak ≈ 8–9). The kill rules are correctly PF-based, not streak-based — do not add a streak kill.
Owner should read this before the first losing week, not after.
**4.6 Frequency reality.** 4-yr average 0.79 trades/weekday (≥1 trade on only 32.5% of days); recent
window ~1.1/day. At those rates, 100 trades ≈ 18–25 weeks — this is a 4–6 month test, not 8 weeks.
Also: this lane alone does NOT meet the "few trades most days" goal; it is one lane of the A1 book.
**4.7 Spread/slippage/swap realism.** Tester used real ticks/spread; demo adds slippage and overnight
swap (RR2 holds longer — more swap-bearing nights). Verify swap appears in forward deal records and is
included in lane P&L (it is, if net = profit+commission+swap+fee per evidence discipline).

## 5. Required changes (the "WITH_CHANGES")
- **C1 (before judging any forward result): resolve the kill-switch collision.** Owner decision, two
  options: (a) give the momentum lane its own kill-switch filename via an owner-approved maintenance
  packet (preferred; one input change), or (b) keep the shared halt but log every halt day and pre-commit
  to excluding halted days from forward-vs-backtest comparison. Until one is done, forward stats are
  not interpretable against the backtest.
- **C2: label the lane's evidence status precisely** in agent.md/status.html: "OOS window consumed by
  direction/RR selection (6 variants); forward demo is the FIRST clean test; a forward PASS = first
  confirmation, not proof." Do not let a future summary call the 4-year run 'OOS-validated'.
- **C3: pin attribution** — write the lane-start timestamp `2026-07-02 04:46:42` into the spec and
  agent.md; export A1 deals for Jul 1–2 and record any magic-932200 fills before that moment as
  PRE-SPEC/EXCLUDED (the Jul-1 directional lane ran ~1 day on the same magic).
- **C4: set duration expectations** — note in the spec that 100 trades ≈ 18–25 weeks at observed rates;
  the "whichever later" rule stands.
- **C5 (free, high value): shadow counterfactuals from signal logs.** The EA logs WOULD_SIGNAL for both
  directions BEFORE the direction/hour guards, so blocked shorts and blocked 09/10 signals are already
  recorded. Codex should build a weekly offline scoreboard of these counterfactuals (would-have
  outcomes vs actual lane) — a parallel control at zero runtime risk, and exactly the evidence needed
  to revisit the short side later without touching runtime.

## 6. Recommendation among the offered options
KEEP RR2.0 active on demo, unchanged in its trading rules — but execute C1 and C3 promptly (C1 may
need one owner-approved maintenance action; it changes safety plumbing, not the strategy). Add the C5
observer. Do NOT revert; do NOT modify entry/exit rules; no further offline RR/threshold sweeps — the
family's research budget on historical windows is spent (every additional backtest variant now only
adds selection debt). The next information arrives from forward fills and the C5 shadow scoreboard.

## 7. For agent.md / status.html (reviewer caveats, verbatim-ready)
1. RR2.0 long-only forward lane: evidence status = SELECTED_ON_ALL_AVAILABLE_HISTORY; forward demo is
   the first uncontaminated test; PASS gates per spec SHA `5566…52b9`.
2. Kill-switch collision between A1 guardian (+50/+100 AED daily floor) and momentum lane must be
   resolved/accounted before forward evaluation (C1).
3. Lane evaluation starts 2026-07-02 04:46:42; earlier magic-932200 fills are PRE-SPEC.
4. Expected duration to 100 trades: 18–25 weeks. Expected max losing streak within test: 8–10 (normal).
5. Falling-gold behavior (backtest): ~⅓ trade rate, ~flat P&L — if the forward lane BLEEDS in a
   falling-gold month, that is out-of-character and grounds for early review even before kill rules fire.
