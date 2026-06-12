# Repo Review 13 — "Selective Duplicate Stacking" Proposal: Verdict (2026-06-12)

Reviewer role: senior quant + risk reviewer.
Independent verification performed against `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
(1,184 rows through 2026-06-12 13:15). Demo evidence only.

---

## Verdict: NO — keep the hard family mutex. The proposal misreads what a duplicate is.

The recommendation is unchanged after checking your numbers, and the check produced three
results that decide the question:

### 1. Duplicates are photocopies, not trades (measured, not asserted)
Across all 557 kept-vs-duplicate pairs in the broker history: **PnL correlation 0.989,
same-sign rate 96.4%.** A duplicate has no outcome of its own — it inherits its primary's
outcome at a one-second offset. Therefore "profitable duplicate EAs" cannot exist as a
category. What exists is: *profitable primary signals that happened to be photocopied.*
The only real question a duplicate ever poses is a **sizing** question on the primary
stream — and sizing decisions belong to an explicit sizing policy with caps and evidence,
not to whichever clones happen to co-fire.

### 2. The ranking table is an artifact of label order
Your table and my same-day snapshot disagree wildly for the same EAs — you show
`round_number_retest_v0` duplicates at −863.60/363 and `swing` at **+81.01**; the current
CSV shows −396.33/305 and **−81.46**. Sign flips and 2× swings for identical underlying
trades, because "which clone is marked duplicate" depends on dedup priority and export
timing. A policy written on top of a label that flips with sort order is built on sand.
(This also explains the apparent paradox of `symbol_normalized` duplicates at 52% WR while
the EA's unique view sits at ~34% — different arbitrary subsets of the same clone stream.)

### 3. The evening decomposition reverses the conclusion
XAUUSD evening 16:00–19:59, full period, duplicate-hidden:

| Slice | n | Net AED | WR |
|---|---:|---:|---:|
| breakout_retest | 16 | **+530.0** | 68.8% (PF 5.91) |
| round family | 61 | **−318.1** | 36.1% |
| All dedup evening | 81 | +192.6 | — |
| RAW evening (with duplicates) | 219 | +1,856 | 45.2% |

The raw +1,856/+2,089 number is the breakout evening edge **doubled by its swing clone**,
minus round-family churn. "Evening stacking is profitable" is true only because the thing
being stacked (breakout) is profitable; the round family *loses in the evening even in this
favorable sample*. A selective-stacking policy derived from the raw table would have you
stack round-family evening trades — the −318 slice.

One more honesty check: the "profitable duplicate" lanes are 1–2-day phenomena.
`session_extreme_repair_v1`: +396 of its +385 total came on June 10 alone (June 11: −111).
`p2weakness`: +282 of +562 on June 11. These are regime days, not distributions.

---

## Answers to the ten questions

**1. Which duplicate EAs should remain blocked?** All of them — the mutex stays universal
within families. Not because duplicates are "bad trades" but because they are not trades;
they are uncontrolled position sizing that bypasses every cap and corrupts attribution.

**2. Which should be allowed conditionally?** None *via duplication*. The legitimate
mechanism for "more exposure where the edge is" already exists in your roadmap: a
**per-cell size multiplier on the kept primary stream** (0.5×/1×/1.5×/2×, one step per
week, rolling-evidence-driven — greenfield spec §C4). A 2× lot on breakout-evening kept
trades is mathematically identical to allowing one duplicate, except it is visible to the
risk engine, capped, attributable, and reversible.

**3. Should XAUUSD evening allow controlled stacking?** The *edge* deserves more size
eventually — it is the most consistent finding across every review (now 69–71% WR, PF ~6,
n≈16–21 dedup). But via the sizing ladder, only after the locked week confirms it, and
only on `breakout_retest` — not as a session-wide stacking permission that the round
family would ride.

**4. Max stack size?** 1 per family-direction (the mutex), plus the account-level cap of
≤2 same-symbol-same-direction positions across ALL families (Guardian R5 spec). Exposure
beyond that is a sizing decision, never a stacking decision.

**5. Rules by symbol/session?** Sizing multipliers: yes, per cell — that is the whole
point of cell-based allocation. Duplication policy: uniform OFF everywhere. Two knobs, two
jobs; don't merge them.

**6. Avoiding overfitting from this sample?**
- Score at family level only — clone-split rankings are mirror artifacts (proven above).
- Minimum n ≥ 30 broker-joined unique trades per cell before any cell rule.
- Windows must span both regimes (the up-trend week AND June 12's reversal day).
- Pre-registered hypotheses only — this proposal arrived post-hoc from a ranked table of 10 EAs, which is multiplicity selection by construction.
- One promotion per week, max one step.

**7. Shadow-only policy for Codex (this is the testable next step):**
`CELL_SIZING_SHADOW_v1` — analysis-only, no EA changes:
- For each KEPT primary trade, log hypothetical PnL at 1× and 2× per (family × symbol × session) cell.
- For each `WOULD_DUPLICATE_FAMILY_EVENT` block (post-mutex), log the PnL the suppressed duplicate would have inherited (= primary's PnL) so the weekly report shows exactly what the mutex "cost" or saved — answering this same question continuously with clean data.
- Weekly output: per-cell table — kept PnL, 2×-hypothetical PnL, drawdown at 2×, account-cap breaches that 2× would have caused. Pre-registered pass bar for promoting any single cell to 1.5×: n ≥ 30, PF ≥ 1.3 net of cost, positive in ≥ 3 of 4 weeks, max-DD at 2× within the daily-loss budget.

**8. Evidence threshold before touching demo EAs:** ≥ 4 weeks of post-mutex data, the §7
bar met on broker-joined trades only, the locked week scored first, and an owner-signed
packet naming exactly one cell and one size step. Replay/observer-only evidence does not
qualify (calibration is quarantined).

**9. p2weakness / repair lanes — promote, monitor, or experimental?** **Monitor, all
three.** Each is small-n with day-concentrated profits, and two of them
(`*_repair_v1`) are the SHORT-only lanes whose construction Review 8 showed was overfit —
their good days arrived exactly when the regime finally matched their hard-coded bias.
That is the trap working as intended. Bar for promotion: n ≥ 30 broker-joined unique
trades, positive across ≥ 2 regime-distinct weeks, PF ≥ 1.3 — same bar as everything else.
No special lane privileges in either direction.

**10. Risks of reading profitable duplicates as edge?** (a) **Pseudo-replication** — the
same signal counted 2–5× inflates apparent n and confidence while adding zero information;
(b) **leverage masquerading as alpha** — stacking amplifies whatever sign the week had,
and this week had a generous evening regime; (c) **selection after the fact** — ranking 10
EAs and keeping the top half guarantees a "finding" in any random data; (d) **label
instability** — the ranked quantity literally changes sign under a different dedup
priority; (e) **regime concentration** — the standout lanes earned their totals in 1–2
sessions. Any one of these alone would disqualify the table as a policy basis; it has all
five.

---

## Boundary compliance
- No runtime change recommended now; the locked week proceeds uncontaminated — these
findings (from pre-lock data) become formally testable *through* it.
- The only new artifact requested is shadow/analysis-only (§7).
- The mutex deployed in the approved A3 window stays exactly as is; its weekly
`WOULD_DUPLICATE` ledger is the ongoing, clean-data answer to this very question.

The constructive core of your finding survives review: **XAUUSD evening breakout exposure
is the project's best asset and deserves to grow.** Grow it with a number you control
(size, ladder, caps) — not with an accident you tolerate (clone co-firing).
