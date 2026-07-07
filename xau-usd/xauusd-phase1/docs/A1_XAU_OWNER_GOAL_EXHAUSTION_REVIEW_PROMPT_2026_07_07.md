# A1 XAU Owner-Goal Exhaustion Review Prompt

Date: 2026-07-07

Use this prompt only if we decide to spend the daily reviewer token. The goal is not to re-review every failed grid; the goal is to challenge the exhaustion conclusion and identify a genuinely different next direction.

---

Please review the current A1 XAU/GOLD owner-goal research state and answer with a decision-quality plan.

## Context

We are trying to reach a demo-testable GOLD/XAUUSD strategy using exact MT5 Strategy Tester evidence, not Python-only backtests.

Current owner target:

- WR near or above `50%`;
- realized average win / average loss near or above `2.0`;
- activity near or above `90%`;
- positive closed-P&L weeks in the `70-80%` territory, after the original `90%` positive-week target was relaxed.

The 2026-07-07 12:20 Dubai deadline was missed. No demo-ready strategy was found.

## Best Achieved

| Frontier | Positive weeks | Activity | WR / W-L | Read |
|---|---:|---:|---|---|
| Current exact baseline F67-H16 no-f33 | `54.81%` | `86.39%` | `50.23% / 2.0002` | profitable but weekly-unstable |
| Best causal weekly-state rescue | `58.10%` | `87.63%` | `50.99% / 1.7767` | improves weeks, breaks payoff/activity |
| Weekly-state + V14 weekly-damage add-on | `59.52%` | `90.03%` | `50.00% / 1.7708` | best serious weekly/activity frontier |
| Weekly-state + V15B prior-day add-on | `59.05%` | `90.41%` | `49.17% / 1.8148` | activity ok, still not weekly target |
| Weekly-state + V16 Asian-range add-on | `57.14%` | `96.84%` | `44.35% / 1.9636` | activity solved, weekly worsened |
| Best simple risk-off diagnostic pair | `60.58%` | diagnostic | `51.79% / 1.3591` | smoother only because payoff collapses |

Best serious frontier remains about `59.52%` positive weeks and `90.03%` activity, with W/L only `1.7708`.

## Evidence Already Closed

The following paths have already failed or been frozen:

- split-entry TP1/runner/BE grid;
- macro traffic-light gates;
- exact-ledger Step 3 portfolio recomposition;
- daily-extreme reclaim design;
- H4/D1 stop caps, early-adverse exits, and partial ladders;
- smooth second-book fixed sizing over the current exact archive;
- current-week closed-P&L and previous-red-week state gates;
- non-causal current-pool red-week oracle;
- weekly-damage H1 V14/V14B;
- prior-day level M5 V15/V15B;
- Asian-range M5 V16;
- simple source/hour/weekday/direction risk-off blocks.

Important upper-bound result:

- current-pool red-week oracle reached only `65.24%` positive weeks and `88.59%` activity even with future knowledge;
- it flipped `24` baseline red weeks, but `33` flips are needed for `70%`;
- therefore the current exact trade pool lacks enough correctly timed red-week rescue trades.

Important red-week anatomy:

- `51/94` red weeks are frequency-frontier dominated;
- `43/94` red weeks are H4/D1 dominated;
- `22/24` large red weeks below `-100 USD` are H4/D1 dominated.

So the problem is split:

1. broad small/medium leaks from the frequency book;
2. large tail weeks from the H4/D1 engine.

## Key Artifacts

- `xau-usd/xauusd-phase1/docs/A1_XAU_1220_DEADLINE_GOAL_AUDIT_2026_07_07.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_OWNER_GOAL_FRONTIER_EXHAUSTION_AUDIT_2026_07_06.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_POST_V16_RISK_OFF_PREMISE_AUDIT_2026_07_07.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_WEEKLY90_PROGRESS_STATUS_2026_07_06.md`
- `status_summary.md`

## Questions For Reviewer

1. Is the conclusion sound that the current A1 XAU family is exhausted for the `70-80%` positive-week owner target under the current WR/W-L/activity constraints?

2. If you disagree, what specific exact-MT5 test should be run next?
   - It must not be another hour/source mask over the current pool.
   - It must not be another H4/D1 stop-cap/partial-ladder tweak.
   - It must not be another broad activity filler like prior-day levels or Asian range.
   - It must include a falsifiable preregistered decision rule.

3. If you agree the family is exhausted, which target should be relaxed first?
   - W/L after stress?
   - WR?
   - activity?
   - positive-week target?
   - or should this family be retired for the owner goal?

4. What genuinely different strategy class is most worth trying next for GOLD?
   - It must plausibly win during baseline red weeks.
   - It must address either frequency-book leaks or H4/D1 tail weeks without deleting the edge.
   - It must be implementable in exact MT5 Strategy Tester.

5. Should we spend effort on a hedge/overlay concept, or is that likely to become another overfit state machine?

6. What minimum evidence should be required before any next candidate can become demo-forward?
   - Suggested floor: exact MT5 only, `>=65%` positive weeks as a watchlist threshold, `>=70%` for serious review, no W/L collapse below `~1.8`, and no severe red-week worsening.

## Requested Output

Please return:

- verdict: `EXHAUSTION_CONFIRMED`, `EXHAUSTION_REJECTED_WITH_NEXT_TEST`, or `TARGET_RELAXATION_REQUIRED`;
- the exact next test, if any;
- whether reviewer token should be spent on further details now or saved;
- the top three overfitting risks in the proposed next action;
- any missing evidence that must be collected before another MT5 run.
