# Phase 2 Actual Demo Cost Reconciliation

Overall status: PASS
Resolution status: RESOLVED_FOR_ACTUAL_DEMO_COST_REVIEW
Generated at UTC: 2026-06-08T06:14:49Z

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
| actual_unique_sample_available | PASS | unique_closed=20; broker-inclusive closed_pnl_aed=31.46 |
| actual_unique_broker_inclusive_pnl_available | PASS | unique_closed_pnl_aed=31.46; unique_pf=1.12; used as outcome context, not as the cost-resolution gate |
| breakout_retest_actual_sample_available | PASS | breakout_closed=9; breakout_closed_pnl_aed=-36.15; breakout_pf=0.64; negative or weak outcome here is win-rate/setup evidence, not cost_R evidence |
| p2weakness_order_log_present | PASS | source=C:\MT5PortableP2WeaknessDemo\MQL5\Files\p2weakness_br_v1_order_log_xauusd.csv |
| p2weakness_executed_cost_r_below_floor | PASS | order_send_ok=1; executed_cost_r_max=0.0472; threshold<=0.15 |
| p2weakness_signal_cost_r_below_floor | PASS | cost_observations=8; signal_cost_r_max=0.1332; threshold<=0.15 |

## Actual Broker Trades

| View | Closed | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---|---|---|---|---|---|
| Raw broker trades | 34 | 16 | 18 | 47.06% | 134.41 | 1.3 | 36.86 | -25.3 |
| Duplicate-hidden unique trades | 20 | 8 | 12 | 40.00% | 31.46 | 1.12 | 36.86 | -21.95 |
| Breakout-retest unique trades | 9 | 2 | 7 | 22.22% | -36.15 | 0.64 | 32.05 | -14.32 |

## Unique Trades By Candidate

| Candidate | Closed | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---|---|---|---|---|---|
| symbol_normalized_round_retest_v0 | 10 | 6 | 4 | 60.00% | 71.28 | 1.45 | 38.46 | -39.88 |
| swing_breakout_retest_v0 | 1 | 0 | 1 | 0.00% | -3.67 | 0.0 | 0.0 | -3.67 |
| breakout_retest | 9 | 2 | 7 | 22.22% | -36.15 | 0.64 | 32.05 | -14.32 |

## P2WEAKNESS BR V1 Cost Log

| Metric | Value |
|---|---|
| Rows | 8 |
| OrderSend OK | 1 |
| Guard blocks | 7 |
| Cost observations | 8 |
| Signal cost R min | 0.04 |
| Signal cost R mean | 0.0832 |
| Signal cost R max | 0.1332 |
| Executed cost R mean | 0.0472 |
| Executed cost R max | 0.0472 |

## Result

Cost is no longer treated as the current practical blocker for the actual demo/wider-stop evidence lane. The next research question is whether the observed positive PnL survives larger sample size, duplicate cleanup, session filtering, and formal cost-aware hypothesis locking.
