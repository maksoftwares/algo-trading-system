# V90 Shared-Portfolio Precommitment

Only unchanged V90 policies that pass all five standalone stages may be tested
beside byte-identical V59/V60. V59 trades, V60 price reconstruction and controls,
and V90 side-correct stressed outcomes must be combined by timestamp in one
shared-account simulation.

V90 admission requires every item below:

- no V59/V60 trade is removed, changed, delayed, or used to tune V90;
- one shared XAU position at a time unless the simulator explicitly aggregates
  same-direction risk and rejects opposing exposure;
- aggregate entry risk cannot exceed the frozen V60 account risk budget;
- V60 daily loss, rolling drawdown, spread, stale-input, and emergency controls
  remain authoritative;
- maximum two V90 entries per UTC date and one per London/New York slot;
- V90 remains profitable after removing its registered top winners;
- combined stress PF is at least `1.50` in development 2, confirmation, and final;
- each modern combined window is net profitable;
- combined trade frequency is at least `2.00` per source weekday in development
  2, confirmation, and final;
- buffered raw floating drawdown does not exceed the frozen V60 hard cap of
  `$449.77` at the registered account-risk calibration;
- V90 absolute daily P&L correlation with V59/V60 does not exceed `0.50`.

Passing standalone V90 economics does not authorize admission. Failure of any
shared gate retires V90 as an additive sleeve without changing V59/V60. No model,
EA, demo, or live authority follows from this research.
