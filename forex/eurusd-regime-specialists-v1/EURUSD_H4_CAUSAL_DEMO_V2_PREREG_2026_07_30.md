# EURUSD causal demo V2 preregistration

The previous M15 expansion failed because its extra trades were mostly
unconfirmed first breaks. This experiment tests two causal explanations fixed
before reading their outcomes:

1. persistence: enter only after the immediately following completed M15 close
   remains beyond the same Asia-range boundary;
2. break/retest/rejection: after the first qualifying M15 break, enter only
   when one of the next four completed M15 bars touches the boundary and closes
   beyond it;
3. direction symmetry: apply the same immediate, persistence, and retest rules
   to upside breaks as independent long experts.

The protected H60 short is the only control. There is no future-H60 label,
post-result minute filter, threshold interpolation, or year selection.

Each side/regime expert must be positive after 0.5 pip extra cost, in every
chronological block, in the latest 12 months, and after removing the best 5%
of winners. The fixed rule selects the highest-frequency passing variant for
each side and regime.

The combined portfolio accepts at most one EURUSD position at a time at fixed
0.01 research lot. Historical demo gates retain the original target of at
least one trade per observed FX day plus PF 1.30, PF 1.15 after 0.5 pip,
positive recent windows, 45%-55% win rate, 1.35-1.75 payoff, concentration,
drawdown, delay, and bootstrap requirements.

This is inspected historical development. Even a full pass cannot authorize
orders: exact MT5 parity and a prospective demo observation period remain
mandatory.
