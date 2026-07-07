# A1 XAU Owner Goal Frontier Exhaustion Audit

Date: 2026-07-06

## Verdict

Status: `NO_DEMO_READY_OWNER_GOAL_STRATEGY_FOUND`

Deadline update: the 2026-07-07 12:20 Dubai push was missed. See `A1_XAU_1220_DEADLINE_GOAL_AUDIT_2026_07_07.md`.

The ordered GOLD/XAUUSD owner-goal plan has not produced a candidate that satisfies the required intersection:

- signal-level WR `>= 50%`;
- realized average win / average loss `>= 2.0`;
- market-day activity `>= 90%` worth showing, with `100%` as the owner target;
- added owner condition: about `90%` positive closed-P&L weeks.

No demo spec should be drafted from the current evidence. The current frontier is useful research evidence, but the owner must either relax one corner of the target or approve a new research cycle with a materially different strategy class.

## Best Current Exact Frontier

Best exact-ledger full-window frontier remains `A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606`.

| Signals | WR% | W/L | Active% | PF | Net USD | Max DD | Last12 WR/W-L/Active | +0.30/ticket W/L | Exit-time positive weeks% | Worst exit week |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1583.72 | 52.86 / 2.2118 / 80.84 | 1.9029 | 54.81 | -878.18 |

This clears raw WR/W-L by a razor-thin margin, but fails activity, slippage stress, and the later weekly-positive requirement.

## Ordered Plan Audit

| Step | Required action | Current evidence | Result |
| --- | --- | --- | --- |
| Step 1 split-entry family | One preregistered 27-cell exact-MT5 grid, then freeze family | `A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_FRONTIER_2026_07_05.md`: `27/27` cells and `81/81` components complete | `NO_SURVIVOR`; best above-50% WR payoff is `f33_r30_be_1r`, WR `50.42%`, W/L `1.5626`, active `61.07%` |
| Step 2 macro traffic-light gate | Design on 2016-2021, freeze, exam on 2022-2026 | `A1_XAU_M5_EXTERNAL_MACRO_TRAFFIC_LIGHT_GATE_DIAGNOSTIC_2026_07_05.md`: 12 gates x 6 families, lag-safe rule | `REJECT_NO_EXTERNAL_MACRO_GATE_OWNER_SHAPE`; high-WR rows collapse payoff, 2R rows remain low-WR |
| Step 3 portfolio layer | Compose 2-4 non-overlapping exact sources with causal priority/dedupe | `A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_2026_07_05.md`: 3599 legal exact-ledger portfolios | `REJECT_NO_STEP3_OWNER_PORTFOLIO`; best WR row is WR `50.02%`, W/L `1.3227`, active `86.58%`; best activity row misses WR badly |
| Step 4 new family | One separate family, design 2016-2021, exam only if design gate passes | `A1_XAU_M5_DAILY_EXTREME_RECLAIM_PREREG_EXACT_PROBE_2026_07_05.md`: exact-MT5 daily-extreme reclaim design | `REJECT_DESIGN_NO_CORE_OR_NEAR_FRONTIER`; best design row WR `27.93%`, W/L `2.0529`, PF `0.7955`, so exam was killed by preregistered rule |

## Best Frontier Rows By Corner

| Corner | Candidate / report | WR% | W/L | Active% | Stress / weekly note | Decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Best raw all-around | F67-H16 no-f33 composition | 50.23 | 2.0002 | 86.39 | +0.30/ticket W/L `1.9029`; exit-week positive `54.81%` | research frontier only |
| Best exact replay near-miss | LH3/10/13/14 exact replay | 50.09 | 1.9859 | 86.39 | +0.30/ticket W/L `1.8887` | misses W/L and activity |
| Best Step 1 above-50 WR payoff | `f33_r30_be_1r` | 50.42 | 1.5626 | 61.07 | exact split-grid cell | payoff too low |
| Best Step 1 W/L | `f33_r30_be_never` | 38.77 | 2.4908 | 60.50 | exact split-grid cell | WR/activity too low |
| Best Step 3 WR-preserving portfolio | `step1_f67_r20_be_tp1 + v8 + orrev_london_firm_stop15` | 50.02 | 1.3227 | 86.58 | +0.30/ticket W/L `1.2249` | payoff too low |
| Best broad activity/payoff combo | companion combo activity row | 46.40 | 2.1050 | 90.99 | +0.30/ticket W/L `1.9954` | WR too low |
| Best smooth second-book 90% activity blend | `baseline + causal_top01 x0.5` | 54.21 | 1.5950 | 90.22 | positive calendar weeks `54.29%`; +0.30/ticket W/L `1.4897` | weekly unchanged and payoff diluted |
| Best standalone smooth weekly book | causal coverage residual book | 67.78 | 0.6794 | 52.64 | positive calendar weeks `61.90%`; June 2026 `+35.04` | activity and W/L unusable |
| Best causal weekly-state rescue | `baseline + causal_top01 current-week drawdown x5` | 50.99 | 1.7767 | 87.63 | positive calendar weeks `58.10%`; +0.30/ticket W/L `1.6997` | no 70% weekly hit, activity/payoff fail |
| Non-causal red-week oracle upper bound | current-pool add-on only in known baseline red weeks | 51.18 | 1.4359 | 88.59 | positive calendar weeks `65.24%`; +0.30/ticket W/L `1.3916` | non-causal and still below target |
| Weekly-damage H1 V14 source | best baseline hybrid `v14 reversal rr2 move10` | 48.85 hybrid | 2.0072 hybrid | 89.36 | positive calendar weeks `56.73%`; red weeks touched/flipped/worsened `63/14/24` | freezes source; not enough repair |
| Weekly-damage H1 V14B direction split | best standalone quality `rr2 move10 long-only` | 39.73 | 2.2024 | 10.93 | positive calendar weeks `20.67%`; combo with weekly-state best tops at `59.52%` | profitable but sparse; no weekly bridge |
| Prior-day level M5 V15B direction split | best baseline hybrid `reversal rr15 short-only` | 48.35 hybrid | 2.0146 hybrid | 89.26 | positive calendar weeks `57.69%`; red weeks touched/flipped/worsened `81/12/36` | active but standalone negative; no weekly bridge |
| Asian-range M5 V16 source | best baseline hybrid `00-06 continuation rr2` | 43.49 hybrid | 2.1118 hybrid | 96.84 | positive calendar weeks `56.73%`; red weeks touched/flipped/worsened `94/15/52` | activity solved, weekly consistency worsened |
| Post-V16 simple risk-off diagnostic | best pair `block H4/D1 + block 08:00` | 51.79 | 1.3591 | diagnostic only | positive calendar weeks `60.58%`; worst week `-138.61` | smooths by deleting edge/payoff |
| Best H4/D1 standalone sparse edge | `long_box2_atr80_range150_body035` | 57.56 | 2.2812 | 19.56 | strong but sparse, pre-2022 robustness fail | frequency gap |
| Best geometry-v2 repair row | `cap9000` recomposition | 50.19 | 1.9709 | 86.48 | exit worst week improves to `-635.21`, but +0.30/ticket W/L `1.8716` | reject core/stress |
| Best H4/D1 partial-ladder row | `p33_t2_run4_be` recomposition | 50.08 | 1.9213 | 85.71 | positive weeks `57.21%`, June 2026 `+164.14`, but +0.30/ticket W/L `1.8106` | reject core/stress |

## Weekly-Positive Condition

The later owner condition says roughly 90% of weeks should end positive.

The stricter exit-time anatomy reconstructed final signal `exit_time` from exact MT5 source CSVs with no missing source CSVs, no fallback rows, and no profit-match failures.

| Book | Positive weeks% | Worst week | Rolling 4w positive% | June 2026 |
| --- | ---: | ---: | ---: | ---: |
| F67-H16 no-f33 baseline | 54.81 | -878.18 | 63.41 | -599.56 |
| Geometry v2 best raw weekly row, `cap9000` | 54.33 | -635.21 | 63.90 | -166.91 |
| Early-adverse best damage row, `cap6000_eae240_r060` | 52.88 | -215.85 | 64.39 | 188.78 |
| Partial-ladder best raw weekly row, `p33_t2_run4_be` | 57.21 | -867.90 | 67.32 | 164.14 |
| Smooth second-book best 90% activity blend, `baseline + causal_top01 x0.5` | 54.29 | -826.66 | 62.32 | -541.52 |
| Standalone smooth weekly ceiling, causal coverage book | 61.90 | -67.06 | 73.43 | 35.04 |
| Causal weekly-state rescue, `current-week drawdown <= -25 + causal_top01 x5` | 58.10 | -879.28 | 63.29 | -219.96 |
| Non-causal red-week oracle upper bound, current pool | 65.24 | -880.38 | 57.00 | -42.26 |
| Weekly-damage H1 V14 best baseline hybrid | 56.73 | -878.18 | not promoted | not promoted |
| Weekly-state best + V14 best add-on | 59.52 | -879.28 | not promoted | not promoted |
| Prior-day level M5 V15B best baseline hybrid | 57.69 | -853.06 | not promoted | not promoted |
| Weekly-state best + V15B best add-on | 59.05 | not promoted | not promoted | not promoted |
| Asian-range M5 V16 best baseline hybrid | 56.73 | -826.50 | not promoted | not promoted |
| Weekly-state best + V16 best add-on | 57.14 | -827.60 | not promoted | not promoted |

Damage-control geometry improves drawdown and some bad weeks, but it breaks WR/W-L and stress. It does not move the book toward 90% positive weeks.

The exact partial-ladder subset requested by review was also tested after adding position-ID deal logging to the EA. It produced a small weekly-shape improvement, but only by lowering realized W/L below the owner core and below stress. It is not demo-ready and does not rescue the H4/D1 family.

The later `70-80%` weekly target was tested against the current exact archive through a smooth second-book diagnostic: reconstructed causal residual packages, top causal coverage candidates, all 42 loaded exact-MT5 individual variants, and fixed second-book sizing sweeps from `0.5x` to `10x`. The best row that reached 90% activity still had only `54.29%` positive calendar weeks and W/L `1.5950`; the best standalone weekly smoother reached only `61.90%` positive weeks and failed activity/payoff. This closes weighting the current A1 archive as a practical path to the relaxed weekly target.

A follow-up weekly-state rescue diagnostic tested causal gates using current-week closed baseline P&L, previous red-week state, and baseline risk-off rules. It tested `760` rows; no row reached `70%` positive weeks and no row reached `90%` activity. Best row reached only `58.10%` positive calendar weeks with W/L `1.7767`. A non-causal oracle check then selected current-pool add-ons only during known future baseline red weeks; even that topped out at `65.24%` positive weeks and `88.59%` activity. This shows the current second-book pool itself lacks enough red-week rescue power, not merely a better causal classifier.

Gap quantification: baseline is `114/210` positive calendar weeks. Reaching `70%` requires `147/210`, so `33` current red weeks must flip; reaching `80%` requires `168/210`, so `54` must flip. The easiest 33 flips require only `353.53 USD` total rescue in hindsight, but the current-pool oracle still failed to flip enough weeks. The next source must therefore have different timing/coverage in baseline red weeks, not just larger sizing of current trades.

The built-in `InpSignalMode` inventory does not offer an obvious untouched shortcut. Modes `0-11` have all been touched by this owner-goal program or earlier exact-MT5 probes. The tempting weekly-level H4 rejection mode was already exact-tested and failed: `171` trades, WR `31.58%`, W/L `1.9852`, PF `0.9162`, net `-164.30`.

The new exact-MT5 weekly-damage H1 source (`SIGNAL_WEEKLY_DAMAGE_H1`, V14/V14B) also failed the relaxed weekly target. V14's best baseline hybrid reached only `56.73%` positive weeks and worsened more baseline red weeks than it flipped (`24` worsened vs `14` flipped). The V14B direction split found a profitable long-only standalone row (`146` trades, WR `39.73%`, W/L `2.2024`, PF `1.4516`, net `+435.11 USD`), but it was too sparse and lifted the weekly-state best combo only to `59.52%` positive weeks. This source class is frozen.

The subsequent exact-MT5 prior-day level and Asian-range M5 sources tested whether naturally active level/range trades could repair the activity and weekly gaps. They did not. V15B's best baseline hybrid reached only `57.69%` positive weeks and came from a standalone-negative short-only row; its best weekly-state combo reached `59.05%`. V16's best row was active (`96.84%` active weekdays) and standalone-positive (`2658` trades, PF `1.0596`, net `+904.53 USD`), but it flipped only `15` baseline red weeks while worsening `52`, so the weekly-state combo fell to `57.14%` positive weeks. These source classes are frozen.

The post-V16 risk-off premise audit also failed to find a simple implementation path. Red-week anatomy splits into two different failure types: `51/94` red weeks are frequency-frontier dominated, while `43/94` are H4/D1 dominated and `22/24` large red weeks below `-100 USD` are H4/D1 dominated. Simple blocks can smooth the week table only by breaking the owner shape: the best pair reached `60.58%` positive weeks but W/L collapsed to `1.3591`. This blocks the obvious "just remove a bad hour/source" path.

The 12:20 deadline audit records the practical conclusion: best serious frontier remains the weekly-state + V14 weekly-damage combo at `59.52%` positive weeks and `90.03%` activity, with W/L `1.7708`. That is materially short of the relaxed `70-80%` weekly target.

## Frozen / Do Not Repeat

These branches are closed unless an independent reviewer proposes a materially new idea:

- split-entry TP1 fraction / runner / BE grid;
- broad macro traffic-light gates tested here;
- exact-ledger Step 3 recomposition of the current source pool;
- daily-extreme reclaim as implemented;
- H4/D1 stop-ceiling filters;
- H4/D1 stop-cap-only grids;
- H4/D1 early-adverse close grids;
- H4/D1 partial-ladder subset (`1/3` at `+2R` to `+4R`, `1/2` at `+3R` to `+6R`, BE/no-BE);
- smooth second-book and fixed sizing sweeps of the current A1 exact archive;
- current-week closed-P&L state gates, previous-red-week add-on gates, and current-pool red-week oracle selection;
- weekly-damage H1 V14/V14B source class;
- prior-day level M5 V15/V15B source class;
- Asian-range M5 V16 source class;
- simple post-V16 risk-off blocks over source bucket, weekday, direction, and entry hour;
- weekly overlays as primary repair;
- current fixed-lot partial-ladder tricks that alter exposure.

## Required Owner Choice

The evidence does not support a demo-ready GOLD strategy under all current conditions. The next productive move is an owner/reviewer decision:

1. Relax W/L after stress and pursue the high-WR frequency branch.
2. Relax WR and pursue the 2R high-payout branch.
3. Relax daily/weekly activity and pursue the sparse H4/D1 branch.
4. Approve a new research cycle with a genuinely different strategy class and a new preregistered budget, focused on baseline red-week complementarity.

Until that choice is made, more tuning inside the current family is likely to repeat the same tradeoff.
