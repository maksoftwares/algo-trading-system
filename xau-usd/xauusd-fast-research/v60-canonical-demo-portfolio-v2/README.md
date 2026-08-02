# V60 Canonical Demo Portfolio V2

This additive deployment package binds the frozen V59/V60 XAUUSD portfolio to
demo account `1033030`. It contains the five Core specialists plus the four
canonical add-on sleeves. The frozen research packages and their ledgers are
not modified.

Complete-machine recovery is documented in `RECOVERY_RUNBOOK.md`. The Git tag
`v60-demo-recovery-20260730`, SHA-256 recovery manifest, pinned Python
environment, exact six-chart profile, EA sources, model bundle, and replay
evidence are sufficient to reconstruct the current demo deployment after local
machine loss. Broker credentials remain owner-managed and are never committed.

The base configuration remains the exact deterministic portfolio and has no ML
authority. The separately hashed V4 overlay enables one bounded portable-model
top-up after a deterministic baseline order has filled. The model can never
skip, delay, or reduce that baseline order. Any model, feature, state, artifact,
or risk-control failure produces baseline-only behavior. No ML shadow path is
enabled.

The separately hash-bound drawdown-protection V1 overlay does not alter signal
generation. It protects an open portfolio episode after aggregate profit reaches
`1.5R`, exits that episode if profit returns to `0.5R`, prevents simultaneous
same-direction R4/V25 exposure, blocks add-ons from 20% drawdown, and limits
Core concurrency from 22% drawdown. ML top-ups remain blocked from 10%
drawdown. A failed protection close reports
`FAILED_CLOSED` and is escalated to the supervisor.

Demo broker action is enabled for exact account `1033030` after the feed,
profile, account, historical-parity, currency-conversion, guardian-halt, and
broker `order_check` gates passed. Live trading remains unauthorized. Runtime files live beneath
`C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2`.

The feed runner emits a 30-second process heartbeat while bounded slow-feed
cycles are in progress. The executor still fails closed after 180 seconds
without a heartbeat or when one feed cycle exceeds 20 minutes. Actionable fast
feeds and add-ons run before the slow R5 transition refresh so their candidates
are available to the executor without waiting for that refresh to finish.

R5 transition collection, causal resolution, and routing remain active as
read-only research feeds. R5 is deliberately absent from the executor source
set after V43-V46 failed sealed causal confirmation, so no R5 candidate can
reach demo broker action.

The locked V40 causal resolver is also transported into the active account as
the required `CORE_OUTCOMES` feed. It records append-only, individually resolved
R1 pullback, R2, R3, and R4 candidate labels from Capital bid/ask quotes. It
publishes no aggregate economics and has no broker API or execution authority.

The owner waived minimum-balance eligibility for this demo account on
2026-07-22. The executor does not impose a minimum balance and reports the
waiver explicitly in `status.json`. This is permission to collect prospective
demo evidence only: it does not change the historical evidence result or
authorize a live account. The exact demo login, server, MT5 trade mode, fixed
lot, spread, position, daily-entry, drawdown, emergency-close, and guardian
halt controls remain enforced.

The demo uses the smaller of each explicit USD cap and its activation-equity
fraction. There is no minimum-balance gate. At the current fixed 0.01-lot
account size, concurrent initial risk is capped at 6%, the closed-drawdown
suspension is capped at $225, and hard closed/equity stops are capped at 25%.
The fixed-lot portfolio also has aggregate initial-risk and same-direction-risk
caps, and every Core candidate has a $45 initial-risk ceiling. Broker margin
requirements remain unavoidable. Startup verifies this equity-scaled mode
and the exact-source historical parity artifact, and chart preflight requires
every safety input to coexist on its intended chart rather than accepting
settings scattered across the profile.

V57 has one additional deterministic replay guard. After an accepted V57 trade
closes with negative realized net P/L, another V57 trade in the same direction
must wait 120 minutes. Opposite-direction trades and every other source remain
eligible. The guard pairs MT5 deals by position ID, includes commission, swap,
and fees, and fails closed for V57 if deal history is unavailable.

The account is AED-denominated. Every USD drawdown threshold is converted using
the AED peg (`3.6725 AED/USD`) before it is compared with MT5 equity or deal
values.

Closed P/L is reconstructed from complete MT5 position-ID lifecycles. A
position belongs to V60 only when its opening deal has one of the canonical
source magics; all later deals on that position are then counted regardless of
which guardian or operator closes it. The runtime rebuilds both cumulative and
peak closed P/L from history on every cycle and fails closed when MT5 deal
history is unavailable.

The original position-origin deployment observation is recorded in
`evidence/POSITION_ORIGIN_REPAIR_DEMO_DEPLOYMENT_20260729.md`. The later safety
repair comparison is recorded in
`evidence/V60_SAFETY_REPAIR_BEFORE_AFTER_20260730.json`. The repaired
current-capital replay passes without a flat suspension deadlock: 1,619 trades,
USD 2,628.44 net P/L, PF 1.4398, and USD 227.24 maximum lifetime equity
drawdown. This is historical evidence, not a profit guarantee.

The MT5 profile keeps both account guardians and attaches one passive telemetry
collector plus three observer-only event sensors. Each collector/sensor has
per-EA trading disabled. The Python portfolio executor is the only component
authorized to open canonical trades. The daily guardian is loss-only: it has no
daily profit target, can halt after a -100 AED account day, and may close only
the nine canonical V60 magic numbers on XAUUSD.

Run `restore_v60_demo.ps1` once on a new machine to create the dedicated,
version-locked V60 `.venv`; no unrelated research environment is required.
Use `start_portfolio.ps1` after a normal restart. It starts one feed process
and one portfolio process and refuses duplicate launchers. Healthy execution reports
`ACTIVE_DEMO_BROKER_ACTION` in `status.json`; `feed_status.json` must report all
eight required feed groups healthy. `set_terminal_algo_trading.ps1` changes the
terminal-wide Algo Trading state only while that terminal is stopped, and keeps
a backup of `common.ini`.

The launcher supplies
`config/v60_drawdown_protection_v1_overlay.json` and
`config/v60_portable_ml_topup_v4_overlay.json` to the executor. The protection
comparison is recorded in
`evidence/V60_DRAWDOWN_PROTECTION_V1_COMPARISON_20260802.json`. Its latest
six-month replay changes net P/L from USD 474.26 to USD 600.14, PF from 1.4047
to 1.5878, and maximum equity drawdown from USD 198.84 to USD 127.83. Over the
full replay, drawdown falls from USD 227.24 to USD 218.55 while net P/L remains
effectively unchanged. These are exposed-history diagnostics and authorize prospective demo
observation only.

The ML overlay is
bound to the immutable deterministic base config, the exact forty-model 2026
bundle, its implementation lock, and the outcome-free Capital/Dukascopy parity
result. Only confirmed R2, R3, R4, V7, and V57 signals are score-eligible.
Marginal V8 and V25 remain deterministic baseline-only probation sources. A
rank strictly above `0.80` may request one separate
`0.01`-lot top-up after the baseline fill. At most one ML top-up may be open and
at most two may be opened per UTC day; every original account,
direction, source, add-on, position, drawdown, emergency-close, and guardian
control remains in force.

The older `v60-core-demo-executor-v1` package is superseded and must not run at
the same time as this full canonical package.

## V57 post-loss cooldown evidence

`build_v57_post_loss_cooldown_impact.py` replays the V57 cooldown
path-dependently against the frozen V60 fee-stress ledger. Over the final 12
completed months, it changes the result from 363 trades and USD 2,474.8069 net
P/L to 356 trades and USD 2,502.7233 net P/L. Profit factor rises from 1.9467
to 1.9837, win rate rises from 43.8017% to 44.1011%, and comparable
closed-trade drawdown remains USD 208.4144.

The JSON summary, monthly comparison, and row-level audit are under `reports/`.
The deployment parity artifact applies the same rule and must pass at startup.

## Historical ML comparison

`build_ml_historical_comparison.py` applies the frozen V10/V11 out-of-time
retain/veto decisions to the exact 363 already-routed V60 trades from July 2025
through June 2026. Missing mandatory XAU features cause model abstention and
retain-all, matching the prospective V13 contract.

The script verifies the hashes of the canonical dataset, V11 prediction ledger,
and V60 price ledger before producing a monthly comparison, summary, and
row-level audit under `reports/`. This is a post-routing research overlay. It
does not change MT5, authorize ML, or re-admit candidates that historical
portfolio routing rejected.

## V12 profit-policy portfolio diagnostic

`build_ml_profit_policy_comparison.py` applies the V12 out-of-time profit-policy
decisions to the exact 2,184-row canonical/V60 join and independently replays
the current V57 post-loss cooldown for the raw and ML paths. All source inputs
are SHA-256 bound. Missing V12 predictions cause model abstention and
retain-all.

After the cooldown, the final 12 completed months improve from 356 trades,
USD 2,502.7233, PF 1.9837, and USD 208.4144 closed-trade drawdown to 325
trades, USD 2,565.6581, PF 2.1193, and USD 191.6678 drawdown. The six-month
P/L also improves by USD 24.2434. The latest three months lose USD 43.7844
versus raw, however, and all-history drawdown is USD 4.3442 worse.

This is a positive post-outcome diagnostic, not deployment evidence. V12's
final forward policy retained all because its calibration improvement was
insufficient, and no disjoint prospective confirmation exists. The generated
window, fold, monthly, family, and row-level audit artifacts are under
`reports/`. All ML runtime and trading authorities remain false.

## B3 macro expected-R diagnostic

`build_ml_macro_expected_r_comparison.py` repeats the purged expected-R
evaluation with the completed dollar-index and Treasury state block added to
the original B1/B2 features. It retains the strongly regularized partial-pooling
ridge, limits candidate vetoes to at most 15% in calibration, and optimizes the
threshold for fee-stressed fixed-0.01-lot dollars. Every dataset, split,
feature-contract, implementation, ledger, and runtime-config input is
SHA-256 bound.

The exact cooldown-aware portfolio retains 2,109 of 2,153 all-history trades.
It improves net P/L by USD 86.7893, profit factor by 0.0318, and closed-trade
drawdown by USD 8.1658. The final 12 months improve by USD 66.7226 and the
final six months improve by USD 7.8742. The latest three months are still USD
18.3237 worse than raw.

The package therefore records
`HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` and keeps deployment
eligibility false. The B3 design was formalized after its historical result
was observed, and it has no prospective Capital dollar/bond confirmation.
Predictions, fold decisions, exact windows, and the row audit are under
`reports/`; no runtime or authority changes are made.

## V14 untouched macro confirmation

The historically informed B1/B2/B3 design is now frozen separately under
`causal-canonical-macro-expected-r-prospective-v14`. Its final model was fit
on all 3,024 resolved causal candidates before July 2026 and uses a pooled 5%
veto threshold that retained 95.01% of fit structural weight. That fit statistic
is a construction check, not forward evidence.

V14 begins at `2026-07-27T03:00:00Z`, consumes immutable V13 B1/B2 candidate
facts, and adds only completed free Dukascopy dollar-index and Treasury-bond
features. Missing, stale, incomplete, or delayed features retain the raw V60
trade by model abstention. Contract SHA-256 is
`ed5e6c2d69ac037de878017745d6c366b2a5ffdfab09500a2064bd10d9668d83`.

Validation requires at least 20 eligible weekdays and 40 resolved candidates;
a later disjoint confirmation requires 40 additional weekdays and 120
resolved candidates. Both stages must beat raw V60 P/L without worsening
profit factor or drawdown, retain at least 90% of frequency, and pass a
weekly-block bootstrap lower bound. V14 is research-only and cannot be
consumed by the EA.
