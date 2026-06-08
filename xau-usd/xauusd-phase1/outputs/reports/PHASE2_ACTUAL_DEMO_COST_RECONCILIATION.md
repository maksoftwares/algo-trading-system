# Phase 2 Actual Demo Cost Reconciliation

Overall status: PASS
Resolution status: RESOLVED_FOR_ACTUAL_DEMO_COST_REVIEW
Generated at UTC: 2026-06-08T08:15:36Z

Actual demo cost reconciliation is RESOLVED for the current demo/wider-stop evidence lane: direct MT5 broker-inclusive outcomes are available and P2WEAKNESS_BR_V1 cost_R is below the +0.15R floor. The canonical old tight-stop Phase 0 revalidation remains unchanged as historical FAIL.

## Boundary

- This resolves the current actual-demo cost concern only.
- It does not change `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` or `MEASURED_COST_ASSUMPTION_DELTA.md` to PASS.
- It does not authorize live capital.
- It does not make experimental demo fills canonical Phase 2 evidence.
- Any canonical promotion still needs a new locked cost-aware hypothesis or corrected cost bug plus fresh revalidation.

## Why The Old Gate And Actual Demo Differ

| Measure | Old Phase 0 ledger | Actual demo / P2 weakness lane |
|---|---|---|
| Stop-distance profile | Median stop 109.79 points | Observed P2 weakness executed stop 1060.26 points; signal stops 375.36-1060.26 points |
| Spread stress | P95 passive spread 75 points | Executed spread 50.00 points; signal spread 50-75 points |
| Cost in R | Median all-in cost 0.6904R; measured net -0.6150R | Executed cost max 0.0472R; signal cost max 0.1332R |
| Interpretation | Cost fatal for old tight-stop historical ledger | Current demo/wider-stop execution profile is not showing fatal cost_R |

## Checks

| Check | Status | Evidence |
|---|---|---|
| actual_broker_csv_present | PASS | source=C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv |
| actual_unique_sample_available | PASS | unique_closed=204; broker-inclusive closed_pnl_aed=-69.06 |
| actual_unique_broker_inclusive_pnl_available | PASS | unique_closed_pnl_aed=-69.06; unique_pf=0.97; used as outcome context, not as the cost-resolution gate |
| breakout_retest_actual_sample_available | PASS | breakout_closed=77; breakout_closed_pnl_aed=358.83; breakout_pf=1.65; negative or weak outcome here is win-rate/setup evidence, not cost_R evidence |
| p2weakness_order_log_present | PASS | source=C:\MT5PortableP2WeaknessDemo\MQL5\Files\p2weakness_br_v1_order_log_xauusd.csv |
| p2weakness_executed_cost_r_below_floor | PASS | order_send_ok=1; executed_cost_r_max=0.0472; threshold<=0.15 |
| p2weakness_signal_cost_r_below_floor | PASS | cost_observations=11; signal_cost_r_max=0.1332; threshold<=0.15 |

## Actual Broker Trades

| View | Closed | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---|---|---|---|---|---|
| Raw broker trades | 353 | 140 | 213 | 39.66% | 96.36 | 1.02 | 30.41 | -19.53 |
| Duplicate-hidden unique trades | 204 | 78 | 126 | 38.24% | -69.06 | 0.97 | 28.4 | -18.13 |
| Breakout-retest unique trades | 77 | 34 | 43 | 44.16% | 358.83 | 1.65 | 26.89 | -12.92 |

## Unique Trades By Candidate

| Candidate | Closed | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---|---|---|---|---|---|
| breakout_retest | 77 | 34 | 43 | 44.16% | 358.83 | 1.65 | 26.89 | -12.92 |
| swing_breakout_retest_v0 | 9 | 3 | 6 | 33.33% | 56.7 | 5.0 | 23.62 | -2.36 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 2 | 0.00% | -74.0 | 0.0 | 0.0 | -37.0 |
| session_extreme_retest_v0 | 39 | 12 | 27 | 30.77% | -81.73 | 0.76 | 21.21 | -12.45 |
| symbol_normalized_round_retest_v0 | 77 | 29 | 48 | 37.66% | -328.86 | 0.75 | 33.65 | -27.18 |

## P2WEAKNESS BR V1 Cost Log

| Metric | Value |
|---|---|
| Rows | 11 |
| OrderSend OK | 1 |
| Guard blocks | 10 |
| Cost observations | 11 |
| Signal cost R min | 0.04 |
| Signal cost R mean | 0.08 |
| Signal cost R max | 0.1332 |
| Executed cost R mean | 0.0472 |
| Executed cost R max | 0.0472 |

## Result

Cost is no longer treated as the current practical blocker for the actual demo/wider-stop evidence lane. The next research question is whether the observed positive PnL survives larger sample size, duplicate cleanup, session filtering, and formal cost-aware hypothesis locking.
