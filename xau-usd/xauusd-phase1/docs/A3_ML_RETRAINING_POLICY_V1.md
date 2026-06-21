# A3 ML Retraining Policy V1

Status: PRELOCK_CONTRACT

This contract owns new-data minimums, model versioning, no online learning, and replacement rules.

## No Online Learning

No model may update itself after each trade.

No automatic retraining.

No automatic promotion.

No mutable model_latest artifact.

## Retraining Eligibility

Retraining requires:

- at least 250 new resolved unique setup groups;
- at least 4 new active market weeks.

## Every Retrain Requires

- new model version;
- new artifact hash;
- same locked contracts or new contract versions;
- full purged walk-forward validation;
- new threshold selection;
- new forward confirmation;
- reviewer signoff.

The currently approved model remains frozen until the replacement passes.

CONTINUE_EVIDENCE must not trigger threshold relaxation, feature changes, or schedule-driven promotion.
