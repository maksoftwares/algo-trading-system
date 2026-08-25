# V60 Dynamic Health-Margin Union V7 Preregistration

## Change from V6

V6 passed nominal and +$0.10 stress gates. At +$0.20, every aggregate, drawdown,
recent-window, and five of six annual gates improved, but 2021 was $3.57 worse because
V2 vetoed a winner when stressed source PF sat just below 1.00.

V7 changes one value: the dynamic V2 source-health veto now requires prior rolling PF
strictly below 0.90 instead of 1.00. The rank threshold, 20-trade lookback, 50-trade
maturity, anti-chase rule, data, costs, and all acceptance gates are unchanged.

The 0.90 margin is intended to require material degradation and reduce state changes
caused by small cost perturbations. It is recomputed causally from each scenario's own
closed outcomes.

## Selection disclosure

This margin was nominated after V6's stressed 2021 result was known. It is post-hoc
and cannot establish deployability. V7 may only be nominated for clean prospective
observation if every locked retrospective gate passes.

## Authorization

Broker action, runtime changes, demo deployment, and live deployment are prohibited.
