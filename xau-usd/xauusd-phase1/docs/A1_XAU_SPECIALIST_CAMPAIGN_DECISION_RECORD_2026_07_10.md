# A1 XAU Specialist Campaign Decision Record

Date: `2026-07-10`

Status: `NO_QUALIFIED_STANDALONE_SPECIALIST_NO_PORTFOLIO_TEST_AUTHORIZED`

This is the append-only decision record for the current specialist campaign. It does
not promote any source. The incumbent R1 box remains a comparison control only; R1,
R2, and R3 currently have no admitted owner under the hard contract.

Integrity resolution: the first mode-22/23/24 implementations used elapsed seconds for
some bar-count windows. They were replaced by distinct completed-M15 cursors/counters,
inclusive final-bar evaluation, reset/rearm clearing, 116 preservation tests, and an
isolated 0-error/0-warning compile. All five required exact cells were rerun from the
corrected EA (`347BCE9646E89F91900B809966EFB168873217C97BB542EC2CAEB469408FB4A6`).
The trade counts and admission decisions were unchanged, so the three kills below are
now final and conforming. No mode-25 history was launched with the defect.

Authoritative contract: [A1_XAU_SPECIALIST_ADMISSION_REGIME_AND_DRAWDOWN_CONTRACT_2026_07_10.md](A1_XAU_SPECIALIST_ADMISSION_REGIME_AND_DRAWDOWN_CONTRACT_2026_07_10.md).

## Hard admission and drawdown contract

- Exact MT5 and completed bars only; one preregistered cell per family, with no grid,
  post-result sibling, or hour/session/day/month/previous-PnL mask.
- Standalone alpha: at least 100 trades, three owned-regime episodes, three exposure
  years and three profitable years, WR `>= 50%`, realized W/L `>= 2.00`, PF `>= 2.00`,
  stress PF `>= 1.75` after `-$0.30/ticket`, positive stressed net, and positive
  pre-recent net.
- Robustness: top-ten-winners-removed and top-three-entry-days-removed net positive,
  best-month share `<= 30%`, and no owned episode above `50%` of positive net.
- Ownership/execution: `100%` native-state authorization, incumbent overlap below
  `20%` unless replacement superiority was preregistered, exact send/trade/ledger
  reconciliation, every failure explained, no open-at-end position, and zero forbidden
  guard blocks.
- Standalone risk: MT5 balance and equity DD relative each `<= 20%`, net/maximal-equity
  DD `>= 2.00`, and maximal-equity DD `<= 2.0x` closed-ledger DD.
- Final runtime target, if anything later qualifies: `0.50%` initial risk/trade,
  `1.00%` aggregate specialist risk, and `2.00%` aggregate portfolio open risk.
- A strong recent era cannot cover a failed older era. A strong portfolio cannot hide
  a failed component.

## Exact evidence completed

Money values reflect each candidate's frozen tester deposit/sizing. Compare alpha and
DD ratios within a row; do not compare dollar net across differently sized families.
`BalDD` and `EqDD` are MT5 relative drawdowns.

| Candidate | Exact era | Trades | WR% | W/L | PF | Stress PF | Net USD | Top10-rem USD | Top3-day-rem USD | Best month% | Closed DD USD | BalDD% | EqDD% | Exact decision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Incumbent R1 box, clean/unmasked | 2022-07 to 2026-06 | 181 | 62.98 | 2.2565 | 3.8394 | 3.8096 | 10,560.49 | 7,631.18 | 8,144.34 | 25.31 | 866.37 | 19.54 | 32.31 | `R1_BOX_CLEAN_REJECT` |
| Incumbent R1 box, clean/unmasked | 2016-01 to 2021-12 | 204 | 48.04 | 2.0114 | 1.8596 | 1.8248 | 2,160.81 | 1,164.48 | 1,408.33 | 50.32 | 546.60 | 29.87 | 38.86 | `R1_BOX_CLEAN_REJECT` |
| R1 long-expansion replacement | 2022-07 to 2026-06 | 139 | 67.63 | 2.0312 | 4.2430 | 4.2158 | 10,142.72 | 7,063.79 | 7,215.73 | 25.23 | 856.09 | 15.98 | 28.85 | `R1_LONG_EXPANSION_REPLACEMENT_REJECT` |
| R1 long-expansion replacement | 2016-01 to 2021-12 | 166 | 47.59 | 1.7932 | 1.6283 | 1.6044 | 1,719.22 | 668.90 | 935.29 | 68.22 | 956.31 | 31.41 | 39.61 | `R1_LONG_EXPANSION_REPLACEMENT_REJECT` |
| R2 mode 22 prior-D1-low first retest | 2022-07 to 2026-06 | 0 | 0.00 | — | — | — | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 | `R2_PDL_FIRST_RETEST_NO_CORE_PASS` |
| Raw R3 H4 compression release | 2022-07 to 2026-06 | 18 | 55.56 | 2.1485 | 2.6856 | 2.6696 | 992.16 | -588.61 | 426.58 | 19.12 | 217.46 | 2.07 | 2.81 | `R3_COMPRESSION_RELEASE_TRANSITION_V1_NO_SURVIVOR` |
| R1 mode 23 prior-D1-high first retest | 2022-07 to 2026-06 | 1 | 0.00 | 0.0000 | 0.0000 | 0.0000 | -31.60 | -31.60 | 0.00 | — | 31.60 | 0.32 | 0.33 | `R1_PDH_FIRST_RETEST_REJECT` |
| R1 mode 23 prior-D1-high first retest | 2016-01 to 2021-12 | 0 | 0.00 | — | — | — | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 | `R1_PDH_FIRST_RETEST_REJECT` |
| R2 mode 24 mature-downtrend second continuation | 2016-01 to 2021-12 | 0 | 0.00 | — | — | — | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 | `R2_LHF_SECOND_CONTINUATION_REJECT` |
| R2 mode 24 mature-downtrend second continuation | 2022-07 to 2026-06 | 2 | 0.00 | 0.0000 | 0.0000 | 0.0000 | -98.60 | -98.60 | 0.00 | — | 98.60 | 0.99 | 1.29 | `R2_LHF_SECOND_CONTINUATION_REJECT` |
| R3 mode 25 compression acceptance / first pullback | 2016-01 to 2021-12 | 0 | 0.00 | — | — | — | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 | `R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_NO_SURVIVOR` |
| R3 mode 25 compression acceptance / first pullback | 2022-07 to 2026-06 | 1 | 0.00 | 0.0000 | 0.0000 | 0.0000 | -49.29 | -49.29 | 0.00 | — | 49.29 | 0.49 | 1.23 | `R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_NO_SURVIVOR` |
| R1 mode 26 mature-uptrend second continuation | 2016-01 to 2021-12 | 1 | 100.00 | — | — | — | 57.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 0.74 | `R1_HLF_SECOND_CONTINUATION_REJECT` |
| R1 mode 26 mature-uptrend second continuation | 2022-07 to 2026-06 | 0 | 0.00 | — | — | — | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 | `R1_HLF_SECOND_CONTINUATION_REJECT` |
| R3 mode 28 inside-compression H1 boundary / first M15 sweep-reclaim | 2016-01 to 2021-12 | 38 | 28.95 | 2.1366 | 0.8705 | 0.8516 | -70.20 | -521.80 | -253.90 | — | 295.50 | 2.90 | 3.30 | `R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_REJECT` |
| R3 mode 28 inside-compression H1 boundary / first M15 sweep-reclaim | 2022-07 to 2026-06 | 35 | 31.43 | 1.9403 | 0.8893 | 0.8696 | -53.70 | -465.30 | -228.90 | — | 191.80 | 1.90 | 1.95 | `R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_REJECT` |

### Decision details and no-retune rulings

1. **Incumbent/control R1 box — rejected as a qualified specialist.** The current era
   passed all reported alpha and concentration checks, but equity DD was `32.31%`,
   equity/closed DD was `2.0007`, and three fully described `market closed` sends broke
   its preregistered zero-failure gate. Prehistory independently failed WR (`48.04%`),
   PF (`1.8596`), best-month concentration (`50.32%`), balance DD (`29.87%`), and
   equity DD (`38.86%`). Keep only as a benchmark; no calendar, previous-PnL, stop, or
   management retune. Evidence: [aggregate MD](../outputs/reports/A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710.md),
   [aggregate JSON](../outputs/reports/A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710.json).

2. **R1 long-expansion replacement — killed.** The current era passed alpha but failed
   equity DD (`28.85%`), equity/closed DD (`2.0093`), and its zero-send-failure gate
   with two described `market closed` failures. Prehistory failed WR (`47.59%`), W/L
   (`1.7932`), PF (`1.6283`), stress PF (`1.6044`), best-month share (`68.22%`), balance
   DD (`31.41%`), equity DD (`39.61%`), and net/equity DD (`1.2913`). It cannot replace
   or supplement R1; no retune. Evidence: [aggregate MD](../outputs/reports/A1_XAU_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_EXACT_20260710.md),
   [aggregate JSON](../outputs/reports/A1_XAU_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_EXACT_20260710.json).

3. **R2 mode 22 prior-D1-low first retest — killed.** It produced zero executions.
   All 12 logged attempts were blocked: five by `r2_pdl_stop_h1_atr_exceeded` and seven
   by the strict router (three chop, two compression, one uptrend, one shock). With no
   alpha sample, no older-era extension or threshold repair is authorized. Evidence:
   [exact MD](../outputs/reports/A1_XAU_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_EXACT_20260710.json).

4. **Raw R3 H4 compression release — killed.** The headline shape came from only 18
   trades. Long had 12 trades / PF `4.0522`; short had six trades / WR `33.33%` / PF
   `1.1402`. Removing the ten winners left `-$588.61`. Of 107 would-signals, 85 were
   blocked by the one-position rule and four by risk overshoot. Low equity DD does not
   cure sample, direction, or concentration failure. No raw-H4 threshold or
   direction-only rescue. Evidence: [exact MD](../outputs/reports/A1_XAU_R3_COMPRESSION_RELEASE_TRANSITION_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R3_COMPRESSION_RELEASE_TRANSITION_V1_EXACT_20260710.json).

5. **R1 mode 23 prior-D1-high first retest — killed.** Primary produced one executed
   loss (`-$31.60`); prehistory produced zero executions. Primary native-R1 purity was
   `100%`, but incidence was effectively absent and every alpha gate failed. The exact
   attrition record confirms only two would-signals per era before later guards. No
   cost-cap, stop-cap, retest, or candle-threshold repair. Evidence: [exact MD](../outputs/reports/A1_XAU_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_V1_EXACT_20260710.json).

6. **R2 mode 24 mature-downtrend second continuation — killed.** The event machine
   found 120 native setups and 57 mature-downtrend episodes in prehistory, but only
   three would-signals; two exceeded the frozen one-H1-ATR stop limit and one exceeded
   the cost/R limit, leaving zero executions. The primary era found 82 setups and 32
   episodes, but only five would-signals; three exceeded the stop limit and the two
   executions both lost, for `-$98.60` net. Setup/entry purity and the executed-risk
   cap were correct (`$49.55` maximum), but incidence and alpha were absent. No pivot,
   window, stop, cost, or maturity-threshold sibling is authorized. Evidence:
   [exact MD](../outputs/reports/A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_EXACT_20260710.json).

7. **R3 mode 25 compression acceptance / first pullback — killed.** Corrected
   completed-bar counters found 519 registered compression events and 83 H1
   acceptances in prehistory, but only three would-signals and zero executions. The
   primary era found 179 registrations, 25 acceptances, one would-signal, and one
   executed loss (`-$49.29`). Event integrity and the hard risk lane passed; the one
   execution risked `$48.98`. Dominant terminal outcomes were established-trend
   handoff (`265/110`), expiry (`144/36`), shock (`59/17`), and failed first touch
   (`38/13`). This is incidence failure, not a drawdown repair opportunity. No
   acceptance, pullback-window, direction, or boundary-threshold sibling is
   authorized. Evidence:
   [exact MD](../outputs/reports/A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710.json).

8. **R1 mode 26 mature-uptrend second continuation — killed.** The conforming
   completed-bar state machine registered 203/234 native setups and consumed every
   setup exactly once, but produced only 6/10 would-signals. Prehistory executed one
   winner for `+$57.00`; four other attempts exceeded the frozen one-H1-ATR stop and
   one failed the cost/R limit. In the primary era all ten attempts exceeded the
   frozen stop limit, leaving zero executions. Setup purity was `100%`, lifecycle
   integrity passed, and the one execution had calculated initial risk of `$28.50`.
   This is decisive incidence/geometry failure, not a drawdown repair opportunity;
   no pivot, maturity, stop, cost, or window sibling is authorized. Evidence:
   [exact MD](../outputs/reports/A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_EXACT_20260710.json).

9. **R3 mode 28 inside-compression H1 boundary / first M15 sweep-reclaim —
   killed.** The final conforming run had a clean causal lifecycle: prehistory
   registered and consumed `7,089/7,089` scalar events with 136 would-signals, while
   primary registered and consumed `1,880/1,880` with 43 would-signals. Both windows
   had zero lifecycle, context, H1-decision, counter, retrospective-entry, native
   setup/signal, or execution-reconciliation violations; setup and entry purity were
   `100%`, and maximum calculated initial risk was `$36.70/$37.10`. That clean
   implementation exposed a clear alpha rejection rather than an audit failure.
   Prehistory produced 38 trades, WR `28.95%`, PF `0.8705`, stress PF `0.8516`, and
   `-$70.20` net. Primary produced 35 trades, WR `31.43%`, PF `0.8893`, stress PF
   `0.8696`, and `-$53.70` net. PF was below `0.90` and net was negative in both eras;
   winner-removal robustness was also negative in both. No H1 lookback, sweep,
   reclaim, candle, stop, direction, session, or other threshold retune or sibling is
   authorized. Evidence:
   [exact MD](../outputs/reports/A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_EXACT_20260710.md),
   [exact JSON](../outputs/reports/A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_EXACT_20260710.json).

No killed result may be combined into a portfolio or revived by a mask. New work must
be a preregistered causal family with a distinct event definition.

## Pending frozen append-only modes

These are specifications/scaffolds, not results. Historical execution remains locked
until implementation/readiness review; no metric or success claim exists yet.

| Mode | Frozen family | Status | Frozen tester-input SHA256 | Exact windows | Risk lane |
| ---: | --- | --- | --- | --- | --- |
| 24 | R2 mature-downtrend second continuation: H1 leg, first M15 lower high, first second break | `EXACT_COMPLETE_REJECTED_COUNTER_CONFORMING` | `d86bbb02074ff4cfdc6464a7c00e3f5792c2ecb6e8181e9a6837f36f85b2f12c` | 2016-2021 and 2022-2026, identical cell | $50/$10k, zero overshoot, one position |
| 25 | R3 completed-D1 compression, H1 acceptance, first M15 pullback | `EXACT_COMPLETE_REJECTED` | `ca53d3b0e4b19df61b45c110943452178f3b45b547ff154860b517d2c02bfc5f` | 2016-2021 and 2022-2026, identical cell | $50/$10k, zero overshoot, one position |
| 26 | R1 mature-uptrend second continuation: H1 leg, first M15 higher low, first second break | `EXACT_COMPLETE_REJECTED` | `9fb023f1b492f9acec4d68c3880bcacdc757e0460ae33db9b9789f9d6f213418` | 2016-2021 and 2022-2026, identical cell | $50/$10k, zero overshoot, one position |
| 27 | R2 mature-downtrend repeated M15 impulse / first M5 continuation | `PREREGISTERED_RUNNER_LOCKED_NOT_IMPLEMENTED_NOT_RUN` | `58621fea70c35ecda9eabbb18877158aff660482b93041bf50e2eb03ff18d3c4` | 2016-2021 and 2022-2026, identical cell | $50/$10k, zero overshoot, one position |
| 28 | R3 inside-compression repeated H1 boundary / first M15 sweep-reclaim | `EXACT_COMPLETE_REJECTED` | `bb8f93fc783b0c08f6a08340310f3197fd9402f1556ccbdb2c890adb95ea47b3` | 2016-2021 and 2022-2026, identical cell | $50/$10k, zero overshoot, one position |

Specifications: [mode 24](A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_PREREG_2026_07_10.md),
[mode 25](A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_PREREG_2026_07_10.md),
[mode 26](A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_PREREG_2026_07_10.md),
[mode 27](A1_XAU_R2_M15_IMPULSE_M5_CONTINUATION_SHORT_V1_PREREG_2026_07_10.md),
[mode 28](A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_PREREG_2026_07_10.md).

## Append-only future exact result template

Append a new subsection below without rewriting prior decisions:

```text
### YYYY-MM-DD — mode NN / family

- Preregistration and frozen-input SHA256:
- Exact artifact MD/JSON:
- Implementation/readiness result:
- 2016-2021: trades, WR, W/L, PF, stress PF/net, concentration, balance/equity DD,
  risk reconciliation, native-state purity:
- 2022-2026: same fields:
- Failed gates:
- Decision: qualified shadow or killed:
- No-retune consequence:
```

## Future exact results

### 2026-07-10 — mode 24 / mature-downtrend second continuation

- Frozen-input SHA256: `d86bbb02074ff4cfdc6464a7c00e3f5792c2ecb6e8181e9a6837f36f85b2f12c`.
- Exact artifact: [MD](../outputs/reports/A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_EXACT_20260710.md), [JSON](../outputs/reports/A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_EXACT_20260710.json).
- Prehistory: zero executions from three would-signals.
- Primary: two executions, zero wins, PF `0`, net `-$98.60`, maximum calculated initial risk `$49.55`, equity DD `1.29%`.
- Final decision: `R2_LHF_SECOND_CONTINUATION_REJECT`; completed-counter replacement runs reproduced both window results and finalized the kill.

### 2026-07-10 — mode 25 / compression acceptance and first pullback

- Frozen-input SHA256: `ca53d3b0e4b19df61b45c110943452178f3b45b547ff154860b517d2c02bfc5f`.
- Exact artifact: [MD](../outputs/reports/A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710.md), [JSON](../outputs/reports/A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710.json).
- Prehistory: zero executions from three would-signals.
- Primary: one executed loss, net `-$49.29`, maximum calculated initial risk `$48.98`, equity DD `1.23%`.
- Decision: `R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_NO_SURVIVOR`; family frozen with no retune.

### 2026-07-10 — mode 26 / mature-uptrend second continuation

- Frozen-input SHA256: `9fb023f1b492f9acec4d68c3880bcacdc757e0460ae33db9b9789f9d6f213418`.
- Exact artifact: [MD](../outputs/reports/A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_EXACT_20260710.md), [JSON](../outputs/reports/A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_EXACT_20260710.json).
- Prehistory: 203 registered setups, six would-signals, one executed winner,
  `+$57.00` net, maximum calculated initial risk `$28.50`, equity DD `0.74%`.
- Primary: 234 registered setups, ten would-signals, zero executions; every attempt
  exceeded the preregistered one-H1-ATR stop limit.
- Decision: `R1_HLF_SECOND_CONTINUATION_REJECT`; family frozen with no retune.

### 2026-07-10 — mode 28 / inside-compression H1 boundary and first M15 sweep-reclaim

- Frozen-input SHA256: `bb8f93fc783b0c08f6a08340310f3197fd9402f1556ccbdb2c890adb95ea47b3`.
- Exact artifact: [MD](../outputs/reports/A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_EXACT_20260710.md), [JSON](../outputs/reports/A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_EXACT_20260710.json).
- Implementation/readiness: conforming completed-D1/H1/M15 lifecycle, `100%` native
  setup and entry purity, exact order/trade/ledger reconciliation, no missing risk
  calculations, no forbidden guard blocks, and no lifecycle violations in either
  window.
- Prehistory: 38 trades, WR `28.95%`, W/L `2.1366`, PF `0.8705`, stress PF `0.8516`,
  stress net `-$81.60`, raw net `-$70.20`, top-ten-winners-removed net `-$521.80`,
  top-three-entry-days-removed net `-$253.90`, balance/equity DD `2.90%/3.30%`, and
  maximum calculated initial risk `$36.70`.
- Primary: 35 trades, WR `31.43%`, W/L `1.9403`, PF `0.8893`, stress PF `0.8696`,
  stress net `-$64.20`, raw and pre-recent net `-$53.70`, top-ten-winners-removed net
  `-$465.30`, top-three-entry-days-removed net `-$228.90`, balance/equity DD
  `1.90%/1.95%`, and maximum calculated initial risk `$37.10`.
- Failed gates: sample, WR, PF, stress PF/net, profitable-year, directional breadth,
  winner-removal robustness, owned-state net, and net/equity-DD efficiency; both eras
  were independently negative with PF below `0.90`.
- Decision: `R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_REJECT` and
  `EXACT_COMPLETE_REJECTED`.
- No-retune consequence: freeze the family with no parameter retune, mask, or sibling
  test and do not admit it to a portfolio.
