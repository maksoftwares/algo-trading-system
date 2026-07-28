# EURUSD Regime 1 Neutral causal verdict

Date: 2026-07-27

Decision: `NO_CAUSAL_NEUTRAL_EXPERT_ADMITTED`

## Objective

Approximate the 2,615 Regime 1 Neutral hindsight-oracle trades using only information available at the decision timestamp, while preserving approximately 1.50R payoff and rejecting outcome-dependent parameter repair.

The oracle is a comparison benchmark only in the first six campaigns. A
separately locked seventh campaign uses historical oracle membership as a
purged supervised label, but forbids oracle rows at inference. An eighth
controlled campaign adds synchronized completed DXY and Treasury M5
features to that model. The oracle never generates a causal feature or
execution decision.

## Causal campaigns tested

| Campaign | Evaluation scope | Trades | Win rate | Payoff | PF | Net |
|---|---|---:|---:|---:|---:|---:|
| Four fixed rule families, forced combination | 2019–2026 H1 | 4,348 | 31.21% | 1.424 | 0.646 | -1,092.88R |
| Regularized EURUSD bar classifier | 2023–2026 H1 walk-forward | 1,019 | 32.97% | 1.438 | 0.707 | -206.15R |
| Regularized EURUSD + GBPUSD/USDJPY classifier | 2023–2026 H1 walk-forward | 1,042 | 33.40% | 1.441 | 0.722 | -198.08R |
| Constrained nonlinear cross-pair classifier | 2023–2026 H1 walk-forward | 22 | 13.64% | 1.439 | 0.227 | -15.05R |
| Raw EURUSD tick-microstructure classifier, fixed 4-pip risk | 2023–2026 H1 walk-forward | 103 | 35.92% | 1.439 | 0.807 | -13.08R |
| Raw tick-microstructure classifier, volatility-scaled risk | 2023–2026 H1 walk-forward | 779 | 35.30% | 1.449 | 0.791 | -106.94R |
| Purged direct Neutral-oracle imitation classifier | 2023–2026 H1 walk-forward | 1,246 | 31.54% | 1.420 | 0.654 | -306.20R |
| Synchronous DXY/Treasury oracle-imitation extension | 2023–2026 H1 walk-forward | 638 | 30.56% | 1.439 | 0.633 | -166.43R |
| Exchange-traded Euro FX/UUP participation | 2019–2026 H1 | 227 | 31.72% | 1.439 | 0.668 | -52.70R |
| Official OCC FXE customer call/put flow | 2024 H2–2026 H1 | 78 | 38.46% | 1.439 | 0.899 | -4.95R |
| Public DTCC OTC EUR/USD option flow | 2025 Sep–2026 H1 | 66 | 24.24% | 1.439 | 0.460 | -27.65R |
| Matched OTC option premium skew | 2025 Q4–2026 H1 | 48 | 35.42% | 1.439 | 0.789 | -6.70R |
| Four-session 30-minute opening drive | 2019–2026 H1 | 593 | 32.04% | 1.432 | 0.675 | -134.20R |
| Midnight dual-side pairs | 2019–2026 H1 | 2,620 | 31.56% | 1.433 | 0.661 | -625.38R |
| Four-clock paired side ranker | 2021–2026 H1 | 1,732 | 33.26% | 1.432 | 0.714 | -341.10R |

None passed all locked chronological admission gates. Consequently, none is
an admitted strategy or eligible for demo/live use.

## Fixed-rule family result

| Family | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Rolling one-hour sweep fade | 3,186 | 31.98% | 1.430 | 0.672 | -730.83R |
| Asia-range sweep fade | 352 | 29.26% | 1.436 | 0.594 | -103.88R |
| EMA-anchor reversion | 3,566 | 32.00% | 1.433 | 0.674 | -809.50R |
| Micro-breakout continuation | 2,498 | 27.98% | 1.430 | 0.556 | -824.95R |

The forced one-position combination matched 715 oracle trades within the same direction, UTC date, and 60-minute tolerance. That is 16.44% precision and 27.34% oracle recall, with a five-minute median timing difference. Timing similarity did not produce economic edge.

## Walk-forward controls

The learned campaigns used:

- completed M5 features and cross-asset state lagged to the latest available observation no later than completion-hour minus one hour;
- exact-timestamp completed GBPUSD/USDJPY M5 bars where applicable;
- source-hashed raw EURUSD ticks aggregated only through signal completion;
- no forward fill for missing tick or cross-pair buckets;
- future target/stop paths only as historical supervised labels;
- a purge requiring every training label exit strictly before its inference refit;
- model fitting on 2019–2020;
- threshold selection only on 2021–2022;
- annual frozen-threshold refits for 2023, 2024, 2025, and 2026;
- exact bid/ask execution, 0.70-pip minimum spread, 0.10-pip adverse slippage per side, and stop-first ambiguous bars.

Every campaign was preregistered and SHA-256 locked before its own outcome pass. All archive history had been inspected in earlier research, so these controls reduce adaptive overfitting but cannot turn the archive into pristine out-of-sample evidence.

## Best causal boundary

The closest isolated result was the fixed-risk tick model in 2023:

- 63 trades;
- 42.86% wins;
- 1.439 payoff;
- PF 1.079;
- +2.92R.

It did not persist:

| Window | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 2023 | 63 | 42.86% | 1.079 | +2.92R |
| 2024 | 16 | 12.50% | 0.206 | -11.40R |
| 2025 | 14 | 35.71% | 0.799 | -1.85R |
| 2026 H1 | 10 | 30.00% | 0.617 | -2.75R |

The volatility-scaled lifecycle increased usable frequency but remained negative in every forward window:

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2023 | 264 | 36.74% | 1.452 | 0.844 | -26.52R |
| 2024 | 178 | 33.15% | 1.462 | 0.725 | -33.23R |
| 2025 | 235 | 37.02% | 1.441 | 0.847 | -22.82R |
| 2026 H1 | 102 | 31.37% | 1.437 | 0.657 | -24.38R |

## Frozen July prospective diagnostic

The rejected volatility-scaled model was subsequently frozen at its
development-selected 0.375 threshold before bulk acquisition of July
EURUSD, GBPUSD, and USDJPY ticks. A single refit used only labels completed
before 2026-07-01, followed by untouched inference through
2026-07-27 02:59 UTC.

| Trades | Win rate | Payoff | PF | Net | Frequency |
|---:|---:|---:|---:|---:|---:|
| 19 | 31.58% | 1.459 | 0.673 | -4.317R | 1.00/active weekday |

The preregistered evidence gate requires at least 100 completed trades and
60 calendar days; the available slice has 19 trades and 27 days. It
therefore remains an accumulating, non-promotional diagnostic. Its metric
gate also failed, and it does not rescue the historical model.

## Direct oracle-imitation boundary

A separately locked classifier was trained on exact historical Neutral
oracle membership rather than generic target-first outcomes. It used causal
five-minute bar, cross-asset, time-cycle, and tick features, a 12-hour label
purge, 2019-2022 development, and annual expanding refits for 2023-2026 H1.

The model achieved 23.03% exact-match precision, 27.52% exact recall, and
31.30% same-side precision within 15 minutes across the forward windows.
This passed its behavioral-imitation gate. Economics nevertheless failed in
every window: 1,246 trades, 31.54% wins, 1.420 payoff, PF 0.654, and
-306.20R.

All 287 exact oracle matches won, while the 959 accepted nonmembers won only
11.05% and lost -729.55R. The dominant coefficient was the UTC time cycle,
reflecting that 2,482 of 2,615 Neutral oracle rows occur in the first UTC
hour because the hindsight generator scans from midnight. The model learned
that construction artifact but could not identify the future-winning
direction.

## Synchronous cross-asset boundary

A final controlled extension added 18 exact-timestamp, completed M5
DOLLARIDXUSD and USTBONDTRUSD features to the direct imitation model.
Source rows required both symbols and were never forward-filled. The
525,099-row source was hash-pinned, and 266 independently produced overlap
rows reproduced with maximum absolute error 0.0.

The extension achieved 24.76% exact precision and 36.68% same-side
precision within 15 minutes, but only 15.15% exact recall. Economics failed
in every window: 638 trades, 30.56% wins, 1.439 payoff, PF 0.633, and
-166.43R. Compared with the prior imitation baseline, exact precision rose
only 1.73 percentage points while PF fell by 0.0209.

All 158 exact oracle members won +233.08R, while the 480 accepted
nonmembers won only 7.71% and lost -399.50R. The UTC time-cycle coefficient
remained dominant; the explicit DXY/Treasury joint-direction coefficient
was essentially zero. Synchronized quoted cross-asset behavior did not
provide the missing causal direction.

## Deterministic UTC-open vote boundary

An outcome-blind source audit found that scheduled CPI, payroll, and FOMC
timing was incompatible with the target cluster: none of the 1,123 Neutral
oracle trades in the calendar-covered period occurred within two hours
after one of 126 available scheduled events. No local EUR FX futures,
executed-flow, or order-book archive was available.

A separately locked deterministic rule therefore tested one 00:00 UTC
Neutral entry from completed 60-minute EURUSD, EURGBP, and EURJPY returns
plus a bounded prior-session DXY return. Three of four votes had to agree.
The outcome-blind census contained 314 trades, evenly split between long
and short.

| Window | Trades | Win rate | PF | Net | Exact precision | 15m precision |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 39 | 43.59% | 1.112 | +2.53R | 43.59% | 64.10% |
| 2024 | 33 | 21.21% | 0.387 | -16.33R | 21.21% | 30.30% |
| 2025 | 40 | 27.50% | 0.546 | -13.50R | 27.50% | 57.50% |
| 2026 H1 | 23 | 30.43% | 0.629 | -6.10R | 30.43% | 47.83% |
| Overall | 135 | 31.11% | 0.650 | -33.40R | 31.11% | 51.11% |

All 42 forward exact members won +61.95R, while all 93 nonmembers lost
-95.35R. This identity follows from the hindsight generator: because it
begins each date at 00:00 and keeps the first target-first paths, any
winning midnight side becomes an exact member and any absent side loses.
The causal rule's economic win rate therefore equals its exact precision.
At a 1.439 realized payoff, its 31.11% precision remains far below the
roughly 41% break-even requirement.

The 2023 slice was a near miss but failed the 45% win-rate floor and became
negative under the extra-half-pip stress. The following three windows
collapsed. The pre-open EUR-cross/DXY vote route is closed without
post-outcome repair.

## Official CFTC participant-flow boundary

A genuinely different campaign used official CFTC Traders in Financial
Futures positions for CME Euro FX. Report dates were lagged eight calendar
days, and rows affected by the 2018-2019 and 2025 federal shutdowns and the
2023 ION interruption were excluded before calculating weekly changes.

Leveraged-money and asset-manager net-position changes voted directly;
dealer inventory change voted inversely. The simple majority selected only
the first Neutral midnight opening within five days of conservative
availability. The outcome-blind census contained 241 trades, split 126
long and 115 short.

| Window | Trades | Win rate | PF | Net | Exact precision | 15m precision |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 28 | 35.71% | 0.799 | -3.70R | 35.71% | 50.00% |
| 2024 | 31 | 32.26% | 0.685 | -6.78R | 32.26% | 41.94% |
| 2025 | 28 | 46.43% | 1.247 | +3.80R | 46.43% | 64.29% |
| 2026 H1 | 15 | 13.33% | 0.221 | -10.38R | 13.33% | 26.67% |
| Overall | 102 | 34.31% | 0.752 | -17.05R | 34.31% | 48.04% |

The 2025 window passed every annual economic gate, including extra-cost
stress, but the effect did not persist. Development was negative, 2023 and
2024 failed, and 2026 H1 collapsed to two wins in fifteen trades.

All four preregistered vote-strength groups were negative over full
history. Across the forward period, all 35 exact members won while all 67
nonmembers lost. Weekly aggregate positioning improved precision by 3.20
percentage points versus the prior pre-open price vote, but remained below
the approximately 41% break-even boundary. The route is closed without
participant or direction selection.

## Official CFTC options-equivalent boundary

A paired-source extension subtracted futures-only participant net
positions from same-date futures-and-options-combined positions to isolate
delta-adjusted aggregate options exposure. All 22 official annual archives
were hash-pinned, and the same conservative CFTC availability and
publication-interruption controls were applied.

The options-derived directions differed from futures-only flow on 112 of
241 candidate dates, or 46.47%, establishing genuine behavioral novelty
before outcomes.

| Window | Trades | Win rate | PF | Net | Exact precision | 15m precision |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 28 | 39.29% | 0.931 | -1.20R | 39.29% | 60.71% |
| 2024 | 31 | 22.58% | 0.420 | -14.28R | 22.58% | 32.26% |
| 2025 | 28 | 39.29% | 0.931 | -1.20R | 39.29% | 64.29% |
| 2026 H1 | 15 | 40.00% | 0.959 | -0.38R | 40.00% | 53.33% |
| Overall | 102 | 34.31% | 0.752 | -17.05R | 34.31% | 51.96% |

On the 47 flipped forward dates, the options source replaced sixteen
futures-only winners with sixteen different winners; fifteen dates lost
under both directions. Both CFTC campaigns therefore finished with exactly
35 forward winners, 34.31% precision, PF 0.752, and -17.05R.

The post-outcome unanimous-short subgroup was positive over full history,
but it was not preregistered as a separate expert. Selecting it now would
be retrospective subgroup overfitting. Free aggregate options-equivalent
flow is closed; legitimate options evidence now requires strike-level
skew/risk reversal or the actual surface.

## Interpretation

At a realized payoff near 1.44, break-even requires approximately 41% wins. The best stable causal variants remained around 33–35%. The 100%-winning Neutral oracle does not reveal a learnable process: it scans both future directions, keeps early target-first paths, and deletes every failure.

Two login-free market-participation extensions did not change that conclusion.
The Euro FX/UUP futures-volume confirmation lost in development and every
forward year. Official OCC FXE customer call/put flow came closer, but its
fixed full rule still lost money; the isolated profitable final quarter had
only eight trades and cannot be selected retrospectively.

Transaction-level public OTC data removed the remaining options-history
access blocker but did not remove the directional problem. Aggregate
standalone call/put notional-plus-premium flow failed all three windows.
A separately locked matched OTM premium-skew surface was slightly positive
in development, then failed both chronological forward quarters. Neither
rule may be reversed, repaired, or narrowed after observing these results.

A separately locked session-opening-drive geometry also failed. Its PF
improved monotonically from 0.480 in 2019-2020 to 0.921 in 2025-2026 H1,
but no window reached profitability and the latest six months remained
below break-even at PF 0.957. The planned post-lock watchlist was cancelled
with zero observations rather than using future data to rescue a rejected
historical rule.

A separately locked hedge-mode campaign then removed direction prediction
entirely by retaining long and short tickets at both 00:00 and 00:05 UTC.
It achieved exactly four executions on all 655 eligible Neutral dates, but
failed every economic window: 2,620 tickets, 31.56% wins, 1.433 payoff,
PF 0.661, and -625.38R. The 827 one-winner pairs earned about +0.45R each,
while 483 no-winner pairs lost about -2.05R each. Mechanical frequency did
not solve the missing directional edge.

A final paired-learning campaign directly modeled LONG versus SHORT instead
of independent rare-event membership. Sixteen fixed decision-time feature
contrasts fed a purged L2 ranker at four fixed first-hour clocks. It
delivered exactly four trades on every evaluation Neutral date, but
conditional winning-side accuracy remained only 52.60%. All five windows
failed; 1,732 trades returned 33.26% wins, 1.432 payoff, PF 0.714, and
-341.10R. The direct ranking formulation is also closed.

The evidence does not support claiming that Regime 1 has been solved. Further retrospective threshold, hour, feature, or model search on this archive would increase overfitting rather than improve causal evidence.

## Next legitimate evidence

Progress now requires at least one source not adaptively exhausted here:

1. a prospectively collected, untouched EURUSD tick period;
2. event-time macroeconomic surprise data known at release;
3. genuine executed-flow or multi-venue order-book imbalance rather than
   quoted Dukascopy volume; synchronized DXY/Treasury quoted M5 behavior has
   now also failed, and weekly aggregate CFTC Euro FX positioning has also
   failed, including its free options-equivalent extension;
4. an explicit relaxation of the requested frequency/payoff objective.

Until then, Regime 1 remains `CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_causal.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_walkforward.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair_nonlinear.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_microstructure.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_volatility.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_prospective.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_oracle_imitation.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_synchronous_crossasset.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_utc_open_vote.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_cot_flow.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_cot_options_flow.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_futures_participation.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_occ_fxe_flow.py
uv run --with pandas --with numpy --with pyarrow python download_neutral_dtcc_fx_options.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_dtcc_fx_options.py
uv run --with pandas --with numpy --with pyarrow python build_neutral_dtcc_skew_source.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_dtcc_skew.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_opening_drive.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_midnight_pairs.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_four_clock_ranker.py
```
