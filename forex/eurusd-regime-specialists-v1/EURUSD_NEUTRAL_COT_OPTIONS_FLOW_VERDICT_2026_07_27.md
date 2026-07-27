# EURUSD Regime 1 Neutral CFTC options-equivalent flow verdict

Date: 2026-07-27

Decision: `REJECTED_NEUTRAL_COT_OPTIONS_FLOW_V1`

## Question tested

Can delta-adjusted aggregate EUR options exposure select the
future-winning direction at the Neutral oracle's midnight cluster better
than futures-only CFTC participant flow?

This campaign used paired official CFTC Traders in Financial Futures
futures-only and futures-and-options-combined reports for CME Euro FX.
Each participant's futures-only net was subtracted from its combined net
to isolate options-equivalent directional exposure.

## Official source and causal controls

The [CFTC historical archive](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm)
provides both TFF formats by year. The
[CFTC report description](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)
explains that combined options positions are delta-adjusted.

Twenty-two annual archives—eleven futures-only and eleven combined—were
downloaded from the official source and independently SHA-256 pinned.
Only exact same-date rows were paired.

Report dates were lagged eight calendar days to 00:00 UTC. Rows affected
by the 2018-2019 and 2025 federal shutdowns and the 2023 ION interruption
were excluded before weekly changes were calculated, following the
[CFTC historical special announcements](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm).

## Frozen rule

For each participant and paired report:

```text
options-equivalent net
  = combined long - combined short
  - futures-only long + futures-only short
```

Weekly changes from leveraged funds and asset managers voted directly in
EURUSD orientation. Dealer-intermediary change voted inversely. A simple
two-of-three majority fixed direction, and only the first Neutral 00:00 UTC
opening within five days of conservative availability could trade.

Execution used fixed 4-pip risk, a 1.50R target, a 12-hour maximum hold,
exact bid/ask prices, a 0.70-pip minimum spread, 0.10-pip adverse slippage
per side, and stop-first resolution of ambiguous M5 bars.

## Outcome-blind census

Before inspecting target, stop, P&L, or oracle membership:

- 519 paired reports remained;
- 518 had three valid nonzero options-flow votes;
- 655 Neutral midnight candidates existed;
- 241 paired reports found an eligible first Neutral opening;
- 122 trades were long and 119 were short;
- 112 of 241 directions, or 46.47%, differed from the rejected
  futures-only flow rule on identical dates;
- annual counts were 30, 41, 35, 33, 28, 31, 28, and 15 from 2019 through
  2026 H1.

The frozen capacity, balance, and source-novelty requirements passed.

## Development result

| Window | Trades | Win rate | Payoff | PF | Net | Max DD | Extra 0.5-pip net |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019-2022 | 139 | 33.09% | 1.439 | 0.712 | -27.48R | 29.03R | -44.85R |

Development failed the win-rate, PF, expectancy, and cost-stress gates.
No participant, sign, lag, freshness rule, or vote subset was changed.

## Chronological forward result

| Window | Trades | Win rate | Payoff | PF | Net | Exact precision | Exact recall | 15m precision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 28 | 39.29% | 1.439 | 0.931 | -1.20R | 39.29% | 3.67% | 60.71% |
| 2024 | 31 | 22.58% | 1.439 | 0.420 | -14.28R | 22.58% | 2.66% | 32.26% |
| 2025 | 28 | 39.29% | 1.439 | 0.931 | -1.20R | 39.29% | 3.44% | 64.29% |
| 2026 H1 | 15 | 40.00% | 1.439 | 0.959 | -0.38R | 40.00% | 3.75% | 53.33% |
| Overall | 102 | 34.31% | 1.439 | 0.752 | -17.05R | 34.31% | 3.36% | 51.96% |

No forward window passed. The latest six-month result was close to
cost-free break-even but still failed every economic threshold: 15 trades,
40.00% wins, PF 0.959, -0.38R net, and 5.13R maximum drawdown. The extra
half-pip stress result was -2.25R. At the frozen 0.25 portfolio-R
allocation, net performance was -0.09 portfolio-R.

## Paired substitution anatomy

The options rule traded exactly the same dates as the futures-only CFTC
rule but changed 112 directions.

| Period | Flipped dates | Futures-only winners | Options winners | Futures-only-only wins | Options-only wins | Neither won |
|---|---:|---:|---:|---:|---:|---:|
| Development | 65 | 21 | 19 | 21 | 19 | 25 |
| Forward | 47 | 16 | 16 | 16 | 16 | 15 |

On the 47 flipped forward dates, the options signal replaced sixteen
futures-only winners with sixteen different winners and left fifteen dates
wrong in both directions. It therefore added different correct calls but
no net directional accuracy.

Both campaigns finished the forward period with exactly 35 winners,
34.31% precision, PF 0.752, and -17.05R. The options source merely
redistributed those outcomes across years: it removed the futures rule's
positive 2025 slice while improving 2026 H1 from 13.33% to 40.00%.

Across the options campaign, all 35 exact oracle members won +51.63R while
all 67 nonmembers lost -68.68R. The strategy remained below the
approximately 41.0% break-even precision boundary.

## Post-outcome subgroup warning

| Frozen vote group | Trades | Win rate | Net |
|---|---:|---:|---:|
| Unanimous short, sum -3 | 32 | 46.88% | +4.70R |
| Majority short, sum -1 | 87 | 28.74% | -26.68R |
| Majority long, sum +1 | 92 | 31.52% | -21.80R |
| Unanimous long, sum +3 | 30 | 40.00% | -0.75R |

The unanimous-short subgroup is visible only after the outcome pass. It
was not preregistered as an independent expert, and selecting it now would
be retrospective overfitting. It cannot rescue or authorize a new claim
on the same archive.

## Robustness

Across all history, the rule produced 241 trades, 33.61% wins, PF 0.729,
and -44.53R, with 47.93R maximum drawdown. Adding another half pip round
trip reduced net to -74.65R and PF to 0.594. Removing the largest 5% of
winners reduced net to -63.70R and PF to 0.612.

## Verdict

Free aggregate CFTC options-equivalent exposure does not solve Regime 1.
It is behaviorally distinct from futures-only positioning, but it does not
increase forward precision or PF.

Post-outcome unanimous-vote selection, participant removal, direction
inversion, shorter lag, or conditioning on a favorable year is prohibited.
This exact aggregate options-delta route is closed without retuning.

The remaining options evidence must be more granular: strike-level
risk-reversal/skew or the actual options surface, which is not contained in
the free CFTC aggregate. Until a genuinely new source passes, Regime 1
remains `CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_cot_options_flow.py
```
