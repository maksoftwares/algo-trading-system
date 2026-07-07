# A1 XAU Anti-Overfit Decision Matrix

Date: 2026-07-07

## Verdict

Status: `CURRENT_FAMILY_OVERFIT_RISK_HIGH_NO_DEMO_SPEC`

Answer to the owner question: we are not overfit in the most dangerous sense because no mined variant has been promoted to demo. We are, however, now in high overfit-risk territory if we continue tuning the same A1 XAU trade pool.

The current evidence says the next valid action is not another source/hour/weekday/threshold mask over the same ledgers. It must be one of:

1. reviewer challenge to the exhaustion conclusion;
2. a genuinely different preregistered exact-MT5 strategy class;
3. explicit target relaxation;
4. retirement of the current A1 XAU family for the owner weekly target.

## Why The Risk Is High

| Evidence | Read |
|---|---|
| Best exact baseline is only `54.81%` positive weeks | Good raw WR/W-L, but weekly shape is unstable. |
| Best serious weekly/activity frontier is `59.52%` positive weeks / `90.03%` activity / W-L `1.7708` | Weekly/activity improved only by breaking payoff. |
| Best smoother diagnostic reaches `60.58%` positive weeks only with W-L `1.3591` | Smoothing comes from deleting edge, not from finding a better source. |
| Current-pool non-causal oracle tops at `65.24%` positive weeks and `88.59%` activity | Even hindsight selection over the existing pool cannot reach `70%`. |
| `33` baseline red weeks must flip to reach `70%`, but current-pool hindsight still misses | The problem is not just a missing causal classifier. |
| V16 solved activity at `96.84%` but weekly score fell to `57.14%` in combo | More trades are not the same as better week distribution. |

The practical conclusion is that the current pool lacks enough correctly timed red-week rescue trades. More selection pressure on the same data would mostly search noise.

## Decision Matrix

| Direction | Decision | Why | Next Evidence Gate |
|---|---|---|---|
| More current-family tuning | `STOP` | Same archive already failed exact grids, weekly-state gates, smooth second-book sizing, V14-V16 source classes, and simple risk-off blocks. | Only reopen if reviewer gives a specific exact-MT5 test that is not another mask over current trades. |
| Reviewer challenge | `BEST_NEXT_REVIEW_USE` | Conserves work and directly tests whether the exhaustion conclusion is sound. | Use `A1_XAU_OWNER_GOAL_EXHAUSTION_REVIEW_PROMPT_2026_07_07.md`; require `EXHAUSTION_REJECTED_WITH_NEXT_TEST` before another current-adjacent run. |
| New strategy class | `VALID_IF_PREREGISTERED` | Needed because the current pool lacks enough red-week rescue timing. | Must define why it should win during baseline red weeks, exact MT5 implementation scope, and a hard kill rule before results are known. |
| Hedge or overlay | `HIGH_RISK_NEEDS_REVIEW` | Could become a state-machine fitted to known red weeks. | Require standalone hedge logic, independent trigger, separate PnL accounting, and no use of known red-week labels. |
| Target relaxation | `VALID_OWNER_CHOICE` | Current best family is around `55-60%` positive weeks, not `70-80%`. | Owner must choose which corner to relax: weekly-positive target, W-L/stress, WR, or activity. |
| Demo spec | `BLOCKED` | No candidate satisfies owner shape with exact MT5 evidence. | Needs exact MT5 candidate with credible weekly shape, no W-L collapse, robustness review, and owner approval. |

## Red Lines Before Another MT5 Run

- No post-hoc hour/source/weekday mask over the same exact ledger pool.
- No V14-V16 micro-tuning after the class freeze.
- No H4/D1 stop-cap, partial-ladder, or simple risk-off retry without a materially different premise.
- No demo spec from a diagnostic-only row.
- No reviewer token spent merely to validate another failed grid.

## Minimum Gate For A New Candidate

A new branch should be worth an exact MT5 run only if it is preregistered with:

- a different causal source of edge than the current A1 family;
- a reason it should specifically help baseline red weeks;
- fixed parameters or a design/exam split before full-window scoring;
- exact-MT5 Strategy Tester as headline evidence;
- weekly-positive, WR, W-L, activity, worst-week, and stress W-L reported together;
- a watchlist floor around `>=65%` positive weeks without W-L below about `1.8`;
- a serious-review floor around `>=70%` positive weeks without breaking activity or payoff.

## Recommended Next Move

Do not code another current-family iteration.

Use the prepared reviewer prompt if the daily review token is available and the owner wants an external challenge now. If the token must be saved, prepare only a preregistered one-page design for a genuinely new strategy class; do not run it until the premise passes the anti-overfit gate.
