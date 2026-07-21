# V89 Shared-Portfolio Precommitment

Only unchanged policies that pass all five V89 stages may be added to the
byte-identical V59/V60 portfolio. The shared-account audit must use the original
V59 trades, V60 price reconstruction and controls, and V89 side-correct stressed
economics.

Every required modern window must satisfy all of the following:

- combined frequency at least `2.0` accepted trades per calendar weekday;
- positive stressed net P&L and stressed profit factor at least `1.20`;
- no accepted V59/V60 trade removed, resized, delayed, or relabeled;
- maximum two V89 entries per UTC date and one per London/New York slot;
- V89 top winners removed remains profitable;
- shared floating-equity drawdown, after the V60 `1.25` capital buffer, remains at
  or below the locked USD `449.7675` hard limit;
- original exposure, concurrency, daily suspension, and drawdown controls remain
  active; and
- V89 absolute daily P&L correlation with V59/V60 does not exceed `0.50`.

Passing standalone V89 economics does not authorize admission. Failure of any
shared gate retires V89 as an additive sleeve without changing V59/V60.
