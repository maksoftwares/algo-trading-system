# PLAN: TESTING FOUR NEW STRATEGY FAMILIES — PLAIN ENGLISH
Date: 2026-07-04 | For: Ali (owner) | Author: Claude (reviewer)
Purpose: a readable master plan for trying four new kinds of algo trading and finding which works
best for us. Codex will later get a technical version of each phase, one at a time.

---

## THE GROUND RULES (why we won't fool ourselves this time)

These four rules apply to everything below. They exist because every painful lesson in this project
came from breaking one of them.

**Rule 1 — Write the rule down BEFORE testing it.** Every strategy idea gets written as an exact
rule (entry, exit, stop, sessions) and hash-locked BEFORE we run any backtest. If the test fails, we
do not "adjust and retry" — that idea is dead, and a genuinely different idea needs a new write-up.
Maximum ONE pre-declared refinement pass per family, ever.

**Rule 2 — Use the fresh data honestly.** We have gold and FX price history from 2016 that has never
been touched. The split:
- 2016–2021 = the LEARNING years. We may look at this freely, explore, form ideas.
- 2022–2026 = the EXAM years. Each frozen rule gets tested here ONCE. No peeking during design.
- Live demo = the FINAL exam. Nothing counts as real until it makes money on fresh demo data.

**Rule 3 — Kill fast, kill cheap.** Each family gets a fixed research budget (below). If it doesn't
show life within its budget, it dies and we move on. No resurrections without brand-new evidence.
Finding out an idea is bad in two weeks is a SUCCESS — it cost us nothing.

**Rule 4 — Nothing touches the running tests.** The XAU forward lanes on demo keep running
untouched. This plan is research-only until a candidate earns its own owner-approved demo lane.

---

## THE FOUR FAMILIES, IN TESTING ORDER

### Phase 1 — "Smart Gold": gold trading with a macro tailwind gate
**What it is, plainly:** gold mostly moves because of two things — US interest rates (adjusted for
inflation) and the US dollar. Right now our gold robots are blind to both; they only look at gold's
own candles. This idea adds a simple daily traffic light: when rates and the dollar are pushing
gold's way, the light is green and our existing entry logic may trade; when they push against, the
light is red and we stand aside.
**Why first:** highest expected value. The hard machinery (daily data feeds, the "no cheating with
tomorrow's data" join logic) was already built for the forex lane and just needs pointing at gold.
It upgrades strategies we ALREADY trust instead of starting from zero.
**How we test:** design the traffic light on 2016–2021 gold data. Freeze it. Then one exam run on
2022–2026: does the green-light-only version beat the always-on version of the same entries?
**Pass looks like:** green-light trades clearly better than red-light trades, edge holds in both
halves of the exam window, and the improvement survives our standard stress checks.
**Budget:** ~2 weeks of Codex work. **Kill if:** the light doesn't separate good from bad trades on
the learning years, or fails the exam.

### Phase 2 — "The Slow Book": daily-chart trend following on several markets
**What it is, plainly:** instead of many small trades per day on one market, this makes 1–3 trades
per WEEK across gold, a few big currency pairs, and one stock index. It buys strength, sells
weakness, holds for days to weeks, and sizes positions by volatility. It is boring on purpose.
**Why:** this is the most proven strategy style in the world for small operations — decades of
public evidence. And it earns money in exactly the months our fast gold books go quiet, which
smooths the whole account. Our own data already told us our edges live in letting winners run.
**How we test:** one classic rule (e.g., break of the recent 40-day high/low, volatility-sized stop,
trail the winner), written once, tested across 5–6 markets on the learning years, frozen, then
examined on 2022–2026. The DIVERSIFICATION is the edge — we judge the basket, not each market.
**Pass looks like:** the basket is profitable over both learning and exam years, no single market
carries everything, and drawdowns stay civilized.
**Budget:** ~2 weeks. **Kill if:** the basket only works on gold (then it's not a trend book, it's
a worse version of what we have), or drawdowns are deeper than our existing books.

### Phase 3 — "The News Clock": scheduled-event strategies on gold
**What it is, plainly:** a handful of US announcements (jobs report, inflation numbers, Fed
decisions) move gold violently at KNOWN times. We've never used a calendar. Two testable ideas:
(a) stand aside before the announcement and trade the follow-through after the dust settles;
(b) simply BLOCK our existing bots for 30 minutes around these events and see if their results improve.
**Why third, not first:** the idea is strong but the testing is tricky — spreads explode around news,
so sloppy testing lies to you. We need event-time spread data, not averages. Idea (b) is nearly free
though, and could improve every existing lane.
**How we test:** build the event calendar (public data), first run idea (b) as a pure filter on our
existing books' historical trades, then design idea (a) on learning years, freeze, exam.
**Pass looks like:** (b) removing news-window trades makes existing books better → adopt as hygiene.
(a) post-news follow-through survives realistic event-time costs.
**Budget:** ~2 weeks. **Kill if:** the edge disappears the moment real event spreads are applied.

### Phase 4 — "The Rubber Band": relative-value between related metals/pairs
**What it is, plainly:** gold and silver are cousins. When one runs far ahead of the other, the gap
usually closes. We trade the GAP, not the direction: short the expensive cousin, buy the cheap one,
profit when they re-converge. Same idea possibly for gold priced in dollars vs euros.
**Why last:** it's the most genuinely different (great for diversification, naturally high win rate,
steady) but also the most new machinery: two positions at once, double costs, and gaps sometimes
stop closing for months — the rule for "give up on this gap" matters as much as the entry.
**How we test:** measure on learning years how far apart the cousins drift and how reliably they
snap back after costs. Freeze thresholds. Exam on 2022–2026 with both legs' real spreads counted.
**Pass looks like:** steady small profits, high win rate, shallow drawdowns, AND low correlation
with all our other books (that's the whole point).
**Budget:** ~2–3 weeks. **Kill if:** after real two-leg costs the snap-back edge is too thin, or the
2022–2026 regime broke the gold/silver relationship.

---

## HOW WE PICK THE WINNER — ONE SCORECARD FOR ALL

Every family that passes its exam gets scored on the SAME card, on the SAME time window:
1. Profit factor and profit per trade (after realistic costs)
2. How bad the worst losing stretch was
3. Does it still make money if we delete its luckiest trades?
4. Is it still working in the most recent 12 months? (your recency rule — as a gate)
5. How many trades per week does it give us?
6. NEW: how uncorrelated is it with the books we already run? (a mediocre strategy that zigs when
   gold zags can be worth more to the account than a good strategy that duplicates what we have)
The best one or two go to a frozen forward-demo spec, exactly like the XAU lanes did — small size,
kill rules, no touching. The rest stay on the shelf with their evidence written down.

## TIMELINE, REALISTICALLY
- Weeks 1–2: Phase 1 (Smart Gold). Weeks 3–4: Phase 2 (Slow Book). Weeks 5–6: Phase 3 (News Clock).
  Weeks 7–9: Phase 4 (Rubber Band). Verdicts land as we go — a fast kill frees the schedule.
- Around week 10: scorecard comparison, pick 1–2 winners, write forward specs, owner decision.
- Meanwhile: the existing XAU demo lanes keep accumulating their own forward evidence in parallel —
  by the time this plan finishes, they'll be near their own pass/fail verdicts too.
- Expectations set honestly: out of four families, finding ONE real keeper would be a very good
  outcome. Two would be exceptional. Zero is possible and would still leave us smarter and with the
  news-hygiene filter (Phase 3b) as a free consolation prize.

## WHAT I NEED FROM YOU (OWNER DECISIONS)
1. Approve the order above (or reorder — Phase 2 and 3 can swap freely).
2. Confirm research budgets: a family that fails its budget dies without appeal.
3. Agree that during these 9–10 weeks we do NOT add unplanned experiments to this plan — new ideas
   go into a parking-lot list for the next cycle.
