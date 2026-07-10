# A1 XAUUSD Extended-Horizon Risk Review Prompt

Date: `2026-07-11`

Status: `INDEPENDENT_REVIEW_REQUIRED_NO_GO`

Branch: `codex/xau-router-entry-hold-audit`

## Prompt to give the independent reviewer

You are the independent quantitative-strategy, MT5 execution, and portfolio-risk
reviewer for this repository. Inspect the GitHub branch
`codex/xau-router-entry-hold-audit` directly. Do not rely only on the summary below:
read the governing documents, source, tests, evidence manifests, and concise result
artifacts. Challenge the methodology and calculations. The requested output is a
decision and a minimum defensible next experiment, not a broad list of possible
optimizations.

The program objective is a stable XAUUSD portfolio whose specialists have positive
standalone expectancy in their own admissible regimes and whose integrated floating
equity drawdown is controlled. No demo or live deployment is authorized. All history
through `2026-06-30` is development data, not an untouched holdout.

### Governing context to inspect

1. `docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md`
2. `docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md`
3. `docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1_PREREG_2026_07_10.md`
4. `docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1_EXECUTION_SPEC_2026_07_10.md`
5. This review prompt and every code/test/evidence file added on the review branch.

### Facts that must remain separated

- The five-year exact-MT5 development window is `2021-07-01` through
  `2026-06-30`: 750 portfolio trades, 48.53% WR, 2.6411 W/L, 2.4905 PF,
  `+$9,306.92` net, `+$9,081.92` at the preregistered `-$0.30/trade` stress,
  and `$889.69` reconstructed maximum closed-equity drawdown.
- The ten-year exact-MT5 development window is `2016-07-01` through
  `2026-06-30`: 1,371 kept portfolio trades after three frozen ownership
  collisions, 46.17% WR, 2.5538 W/L, 2.1905 PF, `+$11,321.16` net,
  `+$10,909.86` stress net, and `$889.69` reconstructed maximum closed-equity
  drawdown.
- The ten-year portfolio has 87/109 positive rolling 12-month windows, but its
  worst rolling 12 months is `-$542.43`; calendar 2021 is `-$451.07` with PF
  0.6054.
- H4 supplies `+$8,159.08`, approximately 72% of ten-year net. Its native MT5
  maximum relative equity drawdown is 39.49%. Its maximum monetary equity
  drawdown is `$1,733.37` (21.25% at that drawdown point). These are native
  source-account figures, not integrated portfolio figures.
- R1 pullback: 830 ten-year trades, 44.34% WR, PF 1.72, `+$2,183.21`, 14.17%
  maximum relative MT5 equity drawdown.
- R2 continuation: 58 ten-year trades, 56.90% WR, PF 2.80, `+$577.52`, 6.99%
  maximum relative MT5 equity drawdown. Its attractive risk statistics are based
  on a sparse sample.
- R2 pullback: 179 ten-year trades, 42.46% WR, PF 1.58, `+$428.62`, 11.24%
  maximum relative MT5 equity drawdown.
- H4 attempted three orders while the market was closed (`10018`) at
  `2024-10-29 21:00`, `2025-03-19 21:00`, and `2025-03-27 21:00`. They appear
  in both overlapping horizon reports but are three unique incidents. Any order
  failure is currently a hard execution NO-GO.
- The `$889.69` portfolio figure is reconstructed closed-equity drawdown under
  the frozen five-minute ownership rule. It is not a claim about simultaneous
  floating portfolio equity. No integrated MT5 portfolio equity test exists yet.
- The historical sources retain legacy selection/containment rules solely to
  reproduce the frozen control: an H4 previous-month P/L gate, directional
  server-session gates on R1 and R2 pullback, and a source-local R2 continuation
  daily-loss stop. The current master direction does not admit these rules for a
  future production portfolio.
- Exact fee-native replays found zero native `DEAL_FEE` for all 1,356 frozen
  entry/exit deals, while preserving the original source commits, accepted orders,
  and completed deals. The separate stress deduction remains conservative.
- The final entry/hold exporter rerun completed twice with identical causal hashes,
  all eight required runtime assertions passing, 678/678 scheduled rows complete,
  and zero orders/deals. It is evidence generation only, not strategy admission.

### Evidence entry points

- `outputs/reports/A1_XAU_EXTENDED_HORIZON_EXACT_20260711/`
- `outputs/reports/A1_XAU_FEE_NATIVE_REPLAYS_EXACT_20260710/`
- `outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_INPUTS_20260710/`
- `outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_EXACT_20260711_FINAL/manifest.json`
- `scripts/run_a1_xau_extended_horizon_exact.py`
- `scripts/run_a1_xau_fee_native_replays_exact.py`
- `scripts/run_a1_xau_router_entry_hold_path_exact.py`
- `mt5/Experts/A1XauRouterEntryHoldPathExporter.mq5`
- The matching `tests/test_a1_xau_*.py` files.

Large causal and tick-path outputs are intentionally not committed to GitHub. Their
hashes, assertions, configs, concise reports, and deterministic generators are
committed. State explicitly if you require a particular large artifact to be
transferred by another channel before reaching a conclusion.

## Questions the review must answer

### A. Evidence and methodology

1. Are the historical source-commit pinning, native-position reconciliation,
   fee capture, horizon extension, ownership merge, and deterministic exporter
   sufficient to trust the reported development results? Identify any concrete
   invalidating defect with file/line or artifact evidence.
2. Is 98% MT5 history quality adequate for this decision? What additional data
   integrity checks, broker-history comparisons, spread/slippage scenarios, or
   execution-model checks are mandatory before the next gate?
3. Is the `-$0.30/trade` stress appropriate for this symbol/account, given zero
   observed native fees? Specify a defensible cost model rather than merely asking
   for "more stress."
4. Is the frozen five-minute same-direction ownership rule defensible? Could its
   three ten-year dropped collisions or concurrent opposite-direction exposure
   materially bias portfolio risk or P/L?
5. Do the five- and ten-year reports correctly distinguish native source equity DD,
   reconstructed portfolio closed DD, and the still-unknown integrated floating
   portfolio equity DD? What claims, if any, are overstated?

### B. Drawdown and concentration

6. Should H4 be rejected, quarantined, or retained at a smaller risk budget given
   its 39.49% maximum relative equity DD and approximately 72% profit contribution?
   Give one primary recommendation and quantitative acceptance/rejection gates.
7. Before evaluating allocation, what common initial capital, lot-size or
   percentage-risk convention must be imposed so DD percentages are comparable
   across specialists and the integrated account?
8. Which risk mechanism should be tested first: static source weights, fixed
   fractional risk, volatility targeting, source-level loss limits, portfolio-level
   exposure caps, equity-curve throttling, or another mechanism? Select the minimum
   mechanism that addresses the observed risk without becoming a fitted rescue.
9. What maximum relative floating-equity DD should be the hard program gate?
   Evaluate whether 10% is appropriate and specify any daily, weekly, source, and
   aggregate limits needed to support it.
10. What evidence would demonstrate that a drawdown control is structural rather
    than fitted to the known 2021 or 2025 loss paths?

### C. Execution and rule admissibility

11. For the three closed-session H4 signals, should the repaired policy skip the
    trade permanently or defer it to the next tradable tick? Choose one. Explain
    the causal and execution consequences and the exact equality checks required
    after repair.
12. Is a session-availability preflight sufficient to clear the execution NO-GO,
    or are retry, requote, partial-fill, duplicate-order, and stale-signal policies
    also mandatory in the next harness?
13. Can any current specialist be admitted while its legacy P/L/session/daily-loss
    rule remains? If not, should the next step be a rule-clean standalone rebuild,
    a clean-room replacement, or portfolio-risk research using the frozen sources
    only as non-deployable controls?

### D. Regime coverage and next experiment

14. Does the evidence support the claim that these specialists cover distinct
    regimes, or merely that four selected historical ledgers sum profitably?
    Specify the minimum regime-attribution evidence required per specialist.
15. How should the weak 2016-2019 results and losing 2021 be interpreted relative
    to the much stronger 2024-2026 period? Is there unacceptable recent-period or
    H4 concentration?
16. Is R2 continuation a credible standalone component with only 58 ten-year
    trades? State the minimum sample, confidence interval, or resampling evidence
    you require.
17. Define the single next preregistered experiment. Include fixed inputs, allowed
    code changes, forbidden tuning, MT5 dates, cost scenarios, source and portfolio
    DD metrics, failure policy, and pass/fail thresholds.
18. Should that next experiment be:
    - execution-only repair followed by exact equality replay;
    - an integrated frozen-source MT5 portfolio/equity harness;
    - rule-clean standalone specialist qualification;
    - or another explicitly justified prerequisite?
    Rank these steps and explain dependencies.
19. After development gates pass, what untouched holdout or forward protocol is
    required, and what would constitute a final NO-GO regardless of profitability?

## Required reviewer response format

Return all of the following:

1. `EVIDENCE_VERDICT`: `VALID`, `VALID_WITH_LIMITATIONS`, or `INVALID`.
2. `DEPLOYMENT_VERDICT`: expected to remain `NO_GO` unless you identify evidence
   that changes the governing boundary; explain why.
3. A ranked defect table with severity, evidence citation, consequence, and repair.
4. A specialist decision table: H4, R1 pullback, R2 continuation, and R2 pullback;
   use `REJECT`, `QUARANTINE`, `SHADOW`, or `NEXT_TEST_CANDIDATE`.
5. One recommended drawdown ceiling and one capital/risk-normalization convention.
6. One minimum next experiment with exact preregistered pass/fail gates.
7. A list of questions that truly require owner judgment rather than repository
   evidence. Do not return questions that can be answered by inspecting the repo.
8. Explicitly state what must not be optimized or changed before that experiment.

Do not recommend deployment, parameter searching, new specialists, or retrospective
regime filters merely because the aggregate PF is above 2. The central decision is
how to obtain trustworthy integrated floating-equity drawdown control without
turning known historical losses into tuning labels.
