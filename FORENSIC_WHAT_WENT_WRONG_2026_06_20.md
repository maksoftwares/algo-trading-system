# Forensic: "Did our changes break a working system?" — 2026-06-20

Owner's claim: *since we started making changes, trade count dropped, profitability dropped, we took more losing trades, and our best strategy performs badly once moved to other accounts. We must have broken something.*

I tested every part of this against the actual A1 broker fills (June 1–19, deduped, real PnL). Verdict: **the causality is mostly backwards — but there is a real self-inflicted mistake underneath, and it is not the one the owner suspects.**

---

## 1. Trades did NOT drop then we lost. Volume EXPLODED, *then* we lost.

| Week | Trades | Net PnL | Avg/trade | Win rate |
| --- | ---: | ---: | ---: | ---: |
| Wk1 Jun 1–7 | 179 | **+44.77** | +0.25 | 39.1% |
| Wk2 Jun 8–14 | 601 | **−2,327.71** | −3.87 | 33.8% |
| Wk3 Jun 15–21 | 467 | −858.82 | −1.84 | 33.0% |

Week 1 was ~breakeven. Then trade volume **tripled** in Week 2 and the book lost −2,327. Daily counts went 19→34→51→…→**148→173→142** on Jun 10–12. The volume *drop* only happens at the very end (Jun 18: 85, Jun 19: 11) — that is the guardrails finally working. **The restrictions came after the damage and reduced it; they did not cause it.**

## 2. What flooded the book: a known-losing lane, run at scale.

| Candidate | Wk1 | Wk2 | Wk3 | Total |
| --- | ---: | ---: | ---: | ---: |
| `symbol_normalized_round_retest_v0` (round) | 64 / −309 | **380 / −1,413** | 151 / −394 | 595 / **−2,116** |
| `breakout_retest` (the good one) | 66 / **+400** | 160 / −605 | 159 / −152 | 385 / −357 |

The round-family ramped from ~12 trades/day to **53–115 trades/day on Jun 9–12** and lost −1,413 in Week 2 alone. This is the single biggest hole. We were running a lane we already knew was weak, at high volume, into a turning market. **That is the real mistake — over-trading an unvalidated/losing lane at scale.** It is exactly what later got quarantined, but the quarantine came on Jun 17, after the hole was dug.

## 3. The acute losses were market events that hit every lane at once.

On **Jun 12**, both unrelated families lost massively on the same day: round −523, breakout −684. Two independent strategies blowing up together = a gold market/volatility event, not a config bug. The same is true of **Jun 17**. The evening breakout core (our best slice) was **positive every single day except Jun 12 (−189) and Jun 17 (−208)** — those two regime days are ~−397 of its drawdown; remove them and it never had a problem. We didn't break it on those days; the market moved against breakout entries and stopped them out.

## 4. "Best strategy fails on other accounts" — it's the calendar, not the account.

The cleanest refutation is on A1 itself:

- A1 `breakout_retest`: **Wk1 +400 → Wk2 −605 → Wk3 −152.**

The same breakout strategy went negative **on A1 too** after Jun 11. It didn't keep working on A1 and fail on A2 — it stopped working *everywhere at the same time*. The reason A2 looks worse is timing:

- **A2's first trade was Jun 10** — it launched directly into the Jun 12 / Jun 17 bad regime and **never traded the profitable Jun 1–9 window** that made A1's record look great.
- A2 is also **not an identical execution** (separate terminal, its own session gate that blocks trades A1 takes), so it was never the "same strategy" anyway.

So comparing A1's Jun 1–11 glory to A2's Jun 10+ record is apples-to-oranges: different calendar window, different gating. A2's −55 is a measurement confound, not proof the clean account is worse.

## 5. What we actually did wrong (owning it honestly)

1. **Ran a broad portfolio of un-validated lanes — including a known loser (round-family) — at scale.** When the regime turned Jun 9–12, the losing lanes flooded the book and produced most of the −2,327.
2. **Scaled trade volume UP during an unproven, deteriorating period** instead of staying small until an edge was confirmed.
3. **Stood up new accounts (A2 Jun 10, A3 multi-lane Jun 16) at the worst possible time**, then judged "the edge" by those bad-window samples.
4. **The guardrails were reactive and late** — cost gate, round quarantine, A3 pause, profit guardian all landed Jun 16–18, *after* the blow-up, not before.

## 6. What we did NOT do wrong

- The gates/dedup/quarantine/pause **did not cause the losses** — they came after and cut the bleeding (Jun 18–19 volume and losses both fell).
- Isolating the one good lane and cutting the rest (the current next-week plan) is the correct response, not the error.

## 7. Bottom line

The system didn't get broken by over-restriction. It bled because we were **running too many un-edged lanes, at too much volume, into a regime turn**, and the cleanup came late. The "best strategy fails on other accounts" feeling is mostly the calendar: the good window (Jun 1–11) predates the other accounts, and the same lane cooled on A1 at the exact same time. The fix is what we're already doing — isolate the one slice with any evidence, keep size tiny, prove it forward — plus the lesson: **don't scale un-validated lanes, and don't judge an edge on a window the account didn't trade.**
