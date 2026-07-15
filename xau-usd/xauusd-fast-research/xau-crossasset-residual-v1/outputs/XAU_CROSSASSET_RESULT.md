# XAUUSD Cross-Asset Residual Directional Specialists V1

**DIRECTIONAL CROSS-ASSET SPECIALIST RESEARCH**  
**OFFICIAL DUKASCOPY BID/ASK TICKS**  
**ONE FROZEN CAUSAL OLS MODEL**  
**LONG AND SHORT SPECIALISTS SCORED INDEPENDENTLY**  
**NO PARAMETER OPTIMIZATION**  
**NO ROUTER TRAINING**  
**NOT MT5 PARITY EVIDENCE**  
**NOT FORWARD-SHADOW EVIDENCE**  
**NOT DEPLOYMENT AUTHORIZATION**  

Classification: `XAU_CROSSASSET_RESIDUAL_V1_NO_DIRECTIONAL_SURVIVOR`

## Stage A directional results

- `XAU_NEGATIVE_RESIDUAL_LONG_SPECIALIST`: trades 2038, PF 0.6091, expectancy -0.154R, net -313.8R; FAIL (baseline_profit_factor|baseline_expectancy_R|stress_profit_factor|stress_expectancy_R|broker_profit_factor|maximum_closed_drawdown_R|baseline_net_R|stress_net_R|broker_net_R|broker_expectancy_R).
- `XAU_POSITIVE_RESIDUAL_SHORT_SPECIALIST`: trades 1974, PF 0.5895, expectancy -0.1588R, net -313.6R; FAIL (baseline_profit_factor|baseline_expectancy_R|stress_profit_factor|stress_expectancy_R|broker_profit_factor|maximum_closed_drawdown_R|baseline_net_R|stress_net_R|broker_net_R|broker_expectancy_R).
- `COMBINED_BIDIRECTIONAL_DIAGNOSTIC`: trades 4012, PF 0.5996, expectancy -0.1564R, net -627.3R; FAIL (baseline_profit_factor|baseline_expectancy_R|stress_profit_factor|stress_expectancy_R|broker_profit_factor|maximum_closed_drawdown_R|baseline_net_R|stress_net_R|broker_net_R|broker_expectancy_R).

Stage B was not acquired because neither direction independently survived Stage A.

No deployment or trading authorization is granted.
