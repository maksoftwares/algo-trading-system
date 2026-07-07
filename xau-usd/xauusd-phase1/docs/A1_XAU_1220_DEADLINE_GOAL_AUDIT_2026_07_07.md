# A1 XAU 12:20 Deadline Goal Audit

Date: 2026-07-07

## Verdict

Status: `DEADLINE_MISSED_NO_DEMO_READY_OWNER_GOAL_STRATEGY`

The requested 12:20 Dubai deadline has passed without a demo-ready strategy that satisfies the current owner goal.

No demo spec should be drafted from the current evidence.

## Current Owner Target

The active target evolved into:

- WR near or above `50%`;
- realized average win / average loss near or above `2.0`;
- activity near or above `90%`;
- positive closed-P&L weeks in the `70-80%` territory, after the original `90%` weekly target was relaxed.

## Best Achieved Before / Around Deadline

| Frontier | Positive weeks | Activity | WR / W-L | Read |
|---|---:|---:|---|---|
| Current exact baseline F67-H16 no-f33 | `54.81%` | `86.39%` | `50.23% / 2.0002` | profitable but weekly-unstable |
| Best causal weekly-state rescue | `58.10%` | `87.63%` | `50.99% / 1.7767` | improves weeks, breaks payoff/activity |
| Weekly-state + V14 weekly-damage add-on | `59.52%` | `90.03%` | `50.00% / 1.7708` | best real weekly/activity frontier |
| Weekly-state + V15B prior-day add-on | `59.05%` | `90.41%` | `49.17% / 1.8148` | activity ok, still not weekly target |
| Weekly-state + V16 Asian-range add-on | `57.14%` | `96.84%` | `44.35% / 1.9636` | activity solved, weekly worsened |
| Best simple risk-off diagnostic pair | `60.58%` | diagnostic | `51.79% / 1.3591` | smoother only because payoff collapses |

Best serious frontier remains about `59.52%` positive weeks with about `90.03%` activity. That is still far below even the relaxed `70-80%` weekly target.

## What Was Closed During The Deadline Push

| Branch | Evidence | Decision |
|---|---|---|
| Weekly-damage H1 V14/V14B | exact MT5 Strategy Tester, `2022.07.01 -> 2026.06.30` | frozen; best combo `59.52%` positive weeks |
| Prior-day level M5 V15/V15B | exact MT5 Strategy Tester, `2022.07.01 -> 2026.06.30` | frozen; active but standalone weak |
| Asian-range M5 V16 | exact MT5 Strategy Tester, `2022.07.01 -> 2026.06.30` | frozen; high activity but worsened weekly score |
| Simple source/hour/weekday risk-off blocks | exact reconstructed exit-time ledger diagnostic | no implementation; best weekly smoother breaks W/L |

## Why This Is Not Just One More Iteration Away

The red-week anatomy splits into two different problems:

- `51/94` red weeks are frequency-frontier dominated.
- `43/94` red weeks are H4/D1 dominated.
- `22/24` large red weeks below `-100 USD` are H4/D1 dominated.

The current pool is insufficient even under non-causal help:

- the red-week oracle over the current pool topped at `65.24%` positive weeks;
- it was still `9` flipped weeks short of `70%`;
- and it failed before enforcing true causality or `90%` activity.

The V16 run also proved that simply buying activity does not solve the issue: activity rose to `96.84%`, but positive weeks fell to `57.14%` in the weekly-state combo.

## Remaining Valid Directions

Only three directions remain defensible:

1. **New strategy class**: not another gate over current A1 ledgers, not another H4/D1 stop tweak, not another level/range activity filler.
2. **Target relaxation**: accept that `55-60%` positive weeks is the current achievable territory for this family, or relax W/L/activity constraints.
3. **Reviewer challenge**: spend the daily reviewer token only if asking the reviewer to challenge this conclusion and propose a truly different premise.

## No-Reviewer-Spend Read

Do not spend the reviewer token merely to review another failed grid. A useful review prompt should ask whether the evidence justifies declaring the current A1 XAU family exhausted for the weekly-positive owner target, and what genuinely different source class should be tried next.
