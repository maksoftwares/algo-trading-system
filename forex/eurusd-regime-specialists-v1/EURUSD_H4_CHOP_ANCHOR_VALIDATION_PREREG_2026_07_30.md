# EURUSD H4 chop anchor validation preregistration

Frozen 2026-07-30 before running the validation implementation.

## Claim being tested

The unchanged `H4_CHOP_ASIA_LONDON_SHORT_CONTROL` is a positive historical anchor robust enough to retain for prospective confirmation. This is not a claim of untouched out-of-sample performance: the strategy and the archived history were already inspected.

The rule, classifier, side, clock, stop, target, and maximum hold are inherited byte-for-byte from `config/frozen_neutral_h4_quiet_state_transfer_v1.json`. No strategy parameter may change in this test.

## Corrected test

Profitability and robustness are tested directly. A forced 50% win rate or 1.5 payoff ratio is not a gate because those shapes do not independently create expectancy.

The replay must:

- reproduce the prior 349-trade anchor ledger;
- pass strict M5 bid/ask OHLC and timestamp integrity checks;
- remain profitable in every frozen chronological block and the latest 12 months;
- survive 5- and 15-minute entry delays, +0.5 and +1.0 pip round-trip costs, and a conservative 0.5-pip charge for every 21:00 UTC rollover crossed;
- retain PF at least 1 after removing the best 5% of winners;
- meet the frozen 20,000-sample circular five-trade block-bootstrap lower-bound gates.

All thresholds, seed, windows, and scenarios are in `config/frozen_h4_chop_anchor_validation_v1.json`.

## Interpretation

Passing means only `HISTORICAL_ANCHOR_VALIDATED_PROSPECTIVE_CONFIRMATION_REQUIRED`. It does not authorize broker, demo, or live activity. Failing a statistical gate does not erase positive historical PnL; it means the evidence is not strong enough to call the anchor validated.
