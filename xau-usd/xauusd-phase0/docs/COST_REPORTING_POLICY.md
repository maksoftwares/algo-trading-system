# Cost Reporting Policy

Last updated: 2026-05-22

## Reporting Principle

Review #2 reframes `breakout_retest` as a high-frequency, modest-edge strategy. Reporting must therefore lead with normalized edge and cost metrics, not compounding dollar outcomes.

Primary review surfaces must use fixed-notional, no-compounding metrics first.

## Forbidden Headline Metrics

Do not headline:

- Compounding total dollar PnL.
- Exponential ending equity.
- Any dollar result that assumes unlimited scaling, broker capacity, or perfect reinvestment.

Compounding output may remain as a secondary diagnostic only if it is labelled:

```text
compounding simulation output, not operational target
```

## Primary Metrics

Headline reports should lead with:

- Trade count.
- Win rate.
- Profit factor.
- Average R per trade.
- Median R per trade.
- Gross expectancy in R.
- All-in cost in R.
- Net expectancy in R.
- Cost-edge consumption percentage.
- Max drawdown percentage or fixed-notional drawdown.
- Fixed-notional no-compounding PnL.

## Secondary Diagnostic Metrics

Secondary diagnostics may include:

- Compounding total PnL.
- Compounding max drawdown in dollars.
- Broker/cost-model cell comparisons.
- Concentration metrics.
- Decile and multisymbol summaries.

These must not be presented as operational targets.

## Fixed-Notional Calculation

Default fixed risk per trade:

```text
starting_equity_usd * phase0_risk_per_trade_pct
```

For the current Phase 0 configuration:

```text
10000 * 0.005 = 50 USD fixed risk per trade
```

Fixed-notional PnL:

```text
fixed_trade_pnl = trade_r_multiple * fixed_risk_usd
fixed_total_pnl = sum(fixed_trade_pnl)
```

No later trade may increase its risk because prior trades made money.

## Cost-In-R Calculation

For each trade:

```text
risk_price = abs(entry_price - stop_loss)
entry_spread_R = spread_price / risk_price
entry_slippage_R = abs(entry_slippage_price) / risk_price
exit_slippage_R = abs(exit_slippage_price) / risk_price
commission_R = commission_money / actual_risk_money
all_in_cost_R = entry_spread_R + entry_slippage_R + exit_slippage_R + commission_R
net_expectancy_R = mean(r_multiple)
gross_expectancy_R = mean(r_multiple + all_in_cost_R)
cost_edge_consumption_pct = all_in_cost_R / gross_expectancy_R
```

Current generated reports using configured cost assumptions must be labelled as assumed-cost baselines until measured spread logger data is integrated.

## Cost Flags

| Cost-edge consumption | Flag |
| ---: | --- |
| <= 40% | GREEN |
| > 40% and <= 60% | YELLOW |
| > 60% and <= 80% | ORANGE |
| > 80% | RED |

## Report Regeneration Requirements

After any cost-reporting change, regenerate:

- `outputs/reports/FIXED_NOTIONAL_REPORT.md`
- `outputs/reports/FIXED_NOTIONAL_SUMMARY.csv`
- `outputs/manifests/FIXED_NOTIONAL_REPORT_MANIFEST.json`
- `outputs/reports/MEASURED_COST_MODEL.md`
- `outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md`
- `outputs/reports/PHASE0_REAL_ARTIFACT_VERIFICATION.md`
- Phase 0 review bundle

Commands:

```powershell
.\.venv\Scripts\phase0.exe generate-fixed-notional-report --expert breakout_retest
.\.venv\Scripts\phase0.exe generate-measured-cost-model --input-dir C:\MT5PortableGoldMission\MQL5\Files
.\.venv\Scripts\phase0.exe generate-measured-cost-revalidation --expert breakout_retest
```

## Acceptance Gates Using Measured Costs

Before Phase 2 authorization:

- Passive spread logger data must be analyzed.
- Measured median and P95 cost model must be produced.
- `breakout_retest` must be revalidated under measured P95 costs.
- Phase 2 readiness must fail or remain pending if measured cost evidence is absent.
