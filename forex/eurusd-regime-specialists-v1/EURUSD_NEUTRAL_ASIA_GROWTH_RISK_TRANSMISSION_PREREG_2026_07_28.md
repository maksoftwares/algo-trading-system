# EURUSD Neutral Asia Growth/Risk Transmission Preregistration

Date frozen: 2026-07-28
Family: `N48_NEUTRAL_ASIA_GROWTH_RISK_TRANSMISSION`

## Rationale and information status

The external growth/risk consensus alone did not generalize. In the untouched 2023 confirmation, the Asia expert was nearly flat at PF 0.98 while the Europe expert failed at PF 0.35. N48 therefore does not claim to be a pre-2022 idea: 2022 and 2023 are disclosed development years.

The new causal hypothesis is that an external risk signal should be traded only when transmission is already visible in EURUSD before entry. This is a new one-rule family, not a direction reversal or a repair of N47.

## Frozen expert

Only `ASIA_HANDOFF_0300` at 03:00 UTC is owned.

The external signal is unchanged:

- LONG when the completed prior 60-minute SPX and copper returns are positive and USD/CNH is negative;
- SHORT for the exact inverse;
- cash otherwise.

The additional transmission confirmation uses exactly the three completed EURUSD M5 bars from 02:45 through 02:59:59 UTC:

- LONG requires the mid close of the final bar to be strictly above the mid open of the first bar;
- SHORT requires it to be strictly below;
- opposite or zero displacement means cash.

Entry remains the 03:00 EURUSD M5 open. The entry bar cannot affect either signal.

All stop, target, hold, spread, slippage, stop-first, one-position, source-integrity, and missing-data rules are inherited unchanged from N46. There is no frequency quota.

## Chronological firewall

1. Hash-lock this exact family before inspecting the new EURUSD-alignment subgroup.
2. Run an outcome-blind candidate census.
3. If capacity passes, evaluate only 2022 and 2023 as development, requiring both years and the combined portfolio to pass the frozen gates.
4. If development fails, do not open 2024–2026.
5. If development passes, hash-lock it before opening 2024 confirmation.
6. If 2024 passes and is separately locked, evaluate 2025 and 2026 H1 exactly once.

The small sample is accepted as low-frequency research, but even a final historical pass would require prospective shadow evidence before demo authorization. Broker action is false.
