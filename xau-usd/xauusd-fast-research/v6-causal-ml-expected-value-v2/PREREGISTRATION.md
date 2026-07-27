# Preregistration

## Hypothesis

V1's binary classifier improved ordinary V6 trade quality but could not
distinguish small wins from large wins. Predicting capped expected R should
retain economically useful trades while refusing to let rare tail winners
dominate the training target.

## Frozen Change

Only the model objective and selection rule change:

- model: shallow `HistGradientBoostingRegressor`;
- target: stressed net R clipped to `[-1.25, +3.00]`;
- annual training rows: outcomes closed before target-year start minus 48 hours;
- decision: retain only predictions strictly above `0.00R`;
- sample weighting: equal total weight per UTC scan day.

Features, source data, V6 nominations, V60, costs, routing, windows, and account
limits are inherited unchanged from the source-hashed V1 and V6 packages.

There is one model and one threshold. No target-year result may change V2.

## Model Gates

- Mean annual target AUC using expected-R score must be at least 0.55.
- Mean annual Spearman rank correlation with uncapped stressed R must be at
  least 0.05.
- At least three of five annual rank correlations must be above zero.

## Portfolio Gates

Every required window must:

- contain at least 10 accepted V2 trades;
- have V2 V6 PF no worse than raw V6;
- have V2 V6 closed drawdown no worse than raw V6;
- remain profitable after removing its five largest winners;
- add positive stress P&L to V60;
- leave combined PF and closed drawdown no worse than V60 alone.

Full-history combined PF, closed drawdown, M5 floating drawdown, add-on count,
and add-on risk must also be no worse than or within immutable V60 limits.

## Interpretation

A failure quarantines V2. A historical pass still requires genuinely new
prospective evidence and MT5 parity before any execution decision.
