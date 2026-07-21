# V91 Shared-Portfolio Precommitment

Only unchanged V91 policies passing all five standalone stages may be tested
beside byte-identical V59/V60 in one timestamp-ordered shared-account audit.

Admission requires every item below:

- no V59/V60 trade is removed, changed, delayed, or used to tune V91;
- one shared XAU position at a time unless same-direction risk is explicitly
  aggregated and opposing exposure rejected;
- aggregate entry risk cannot exceed the frozen V60 account-risk budget;
- V60 daily-loss, rolling-drawdown, spread, stale-input, and emergency controls
  remain authoritative;
- maximum two V91 entries per UTC date and one per London/New York slot;
- V91 remains profitable after removing its registered top winners;
- combined stress PF is at least `1.50` in Development 2, Confirmation, and Final;
- each modern combined window is net profitable;
- combined frequency is at least `2.00` trades per source weekday separately in
  Development 2, Confirmation, and Final;
- buffered raw floating drawdown does not exceed V60's `$449.77` hard cap at
  the registered account-risk calibration;
- V91 absolute daily P&L correlation with V59/V60 does not exceed `0.50`.

Failure of any shared gate retires V91 without changing V59/V60. Passing does
not authorize model training, EA consumption, demo/live trading, or broker action.
