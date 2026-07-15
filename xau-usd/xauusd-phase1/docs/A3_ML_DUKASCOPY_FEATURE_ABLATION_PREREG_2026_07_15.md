# A3 ML Dukascopy Feature Ablation V1 Preregistration

## Question

Do causal Dukascopy XAUUSD bid/ask tick features improve ranking of the already frozen R1 long and R2 short MT5 candidate trades?

This experiment does not create entries. It compares the same fixed logistic model and the same labeled trades with and without eight Dukascopy features.

## Frozen Population

- Training: entries from 2018-07-01 through 2021-12-31.
- Validation: entries from 2022-01-01 through 2024-06-30.
- Families: `r1_box_clean_strict_uptrend` and `r2_pullback_short_h1_confirm`.
- Label: positive realized MT5 Strategy Tester P/L.
- Decision threshold: `0.50`, not tuned after seeing results.
- Model: fixed L2-regularized logistic regression already implemented in the historical training pipeline.

The pre-availability population is 357 training rows and 297 validation rows. Rows without a complete causal feature window are excluded from both arms before fitting; at least 350 training and 290 validation rows must remain for a research pass. The implementation may fit diagnostic models with at least 300/250 rows so a data-gate failure still produces useful measurements, but this does not relax the 350/290 acceptance gate.

## Frozen Dukascopy Features

Every feature uses official Dukascopy `XAU-USD` ticks with timestamps strictly earlier than the MT5 entry:

1. Last spread in basis points.
2. Prior-60-minute p95 spread in basis points.
3. Last spread divided by prior-60-minute median spread.
4. Log one plus prior-5-minute tick count.
5. Log one plus prior-60-minute tick count.
6. Prior-5-minute mid return.
7. Prior-60-minute mid return.
8. Prior-60-minute one-minute realized volatility in basis points.

Five minutes of pre-roll may establish an as-of price at the lookback boundary. No tick at or after the entry timestamp is allowed. Every source hour must match its frozen acquisition manifest and SHA-256.

The shared non-tick baseline features use the existing completed H1/H4 Capital.com plus MT5 bridge bars and the full-history Dukascopy D1 bar-end series. The first attempted run stopped before model fitting because the recent-only MT5 D1 export began in July 2025; replacing that unavailable preflight input with the already validated full-history D1 series does not change the population, model, tick features, or gates.

The second attempted run also stopped before the enhanced model fit when a daily market-reopen entry had only five minutes of prior Dukascopy observations. Such rows receive no imputation: they are causally unavailable and removed from both comparison arms. The exclusion rule was added before any enhanced-model outcome was visible and may not reduce either split below its frozen minimum size.

## Pass Gates

All gates must pass:

- Baseline and enhanced datasets contain exactly the same rows and labels.
- Validation has at least 290 rows.
- Enhanced validation ROC AUC is at least 0.55.
- Enhanced AUC exceeds baseline AUC by at least 0.02.
- The lower bound of a fixed-seed 95% calendar-month block-bootstrap interval for AUC improvement is above zero.
- Enhanced Brier score and log loss do not exceed baseline.
- Neither LONG nor SHORT validation AUC regresses by more than 0.01.
- All execution authorization fields remain false.

Failure is a valid result and closes this feature set. No feature removal, threshold search, split change, or parameter tuning is allowed after the result is observed.

## Boundary

This is research-only evidence. The same historical gold events appear in both broker feeds, so Dukascopy is an independent quote source but not an independent time holdout. Passing does not authorize Python demo predictions, EA consumption, or broker action.
